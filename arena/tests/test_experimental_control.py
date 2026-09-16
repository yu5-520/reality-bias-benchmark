import unittest
from pathlib import Path

from arena.core import ArenaState
from arena.engine import run_arena_once
from arena.experimental_control import (
    apply_state_intervention,
    capture_state,
    decide_commit,
    make_branch_manifest,
    restore_state,
    verify_branch_manifest,
    verify_state_snapshot,
)
from arena.io_utils import load_json
from arena.providers import ScriptedProvider


ROOT = Path(__file__).resolve().parents[2]


class ExperimentalControlTest(unittest.TestCase):
    def setUp(self):
        self.domain = load_json(ROOT / 'arena/domains/ecommerce.json')
        self.config = load_json(ROOT / 'arena/config/arena_v0.3.json')
        self.state = ArenaState(self.domain, self.config, 'experimental-control-test')

    def test_snapshot_roundtrip_preserves_arena_state(self):
        snapshot = capture_state(
            self.state,
            anchor_ref='before-first-agent-call',
            parent_trace_hash='trace:test',
        )
        self.assertTrue(verify_state_snapshot(snapshot))
        restored = restore_state(
            self.domain,
            self.config,
            'experimental-control-test',
            snapshot,
        )
        roundtrip = capture_state(
            restored,
            anchor_ref='before-first-agent-call',
            parent_trace_hash='trace:test',
        )
        self.assertEqual(snapshot['state_hash'], roundtrip['state_hash'])
        self.assertFalse(roundtrip['provider_internal_state_captured'])

    def test_branch_manifest_binds_parent_and_post_intervention_start(self):
        snapshot = capture_state(self.state, anchor_ref='A0', parent_trace_hash='trace:test')
        intervention = {
            'type': 'set_shared_state_status',
            'key': next(iter(snapshot['shared_state_metadata'])),
            'status': 'provisional',
        }
        changed = apply_state_intervention(snapshot, intervention)
        manifest = make_branch_manifest(
            branch_id='B-001',
            parent_trace_hash='trace:test',
            parent_snapshot=snapshot,
            branch_start_snapshot=changed,
            intervention_spec=intervention,
            replicate_index=0,
            model_identity={'model': 'scripted'},
            config_identity={'arena': self.config['version']},
            code_identity={'commit': 'TEST'},
        )
        self.assertTrue(verify_branch_manifest(manifest, snapshot, changed))
        self.assertNotEqual(snapshot['state_hash'], changed['state_hash'])
        self.assertEqual(snapshot['state_hash'], manifest['parent_state_hash'])
        self.assertEqual(changed['state_hash'], manifest['branch_start_state_hash'])
        self.assertTrue(manifest['intervention_applied_before_continuation'])
        self.assertEqual(changed['shared_state_metadata'][intervention['key']]['status'], 'provisional')

    def test_commit_gate_is_fail_closed_and_state_bound(self):
        snapshot = capture_state(self.state, anchor_ref='A0', parent_trace_hash='trace:test')
        policy = {
            'default_decision': 'BLOCK',
            'allowed_action_types': ['write_state'],
            'allowed_authority_classes': ['I'],
            'require_source_refs': True,
            'require_expected_state_hash': True,
        }
        proposal = {
            'action_type': 'write_state',
            'authority_class': 'I',
            'source_refs': ['source:1'],
            'expected_state_hash': snapshot['state_hash'],
        }
        passed = decide_commit(proposal, policy, current_state_hash=snapshot['state_hash'])
        self.assertEqual('PASS', passed['decision'])

        stale = dict(proposal)
        stale['expected_state_hash'] = 'stale'
        blocked = decide_commit(stale, policy, current_state_hash=snapshot['state_hash'])
        self.assertEqual('BLOCK', blocked['decision'])
        self.assertIn('STATE_HASH_MISMATCH', blocked['reasons'])

    def test_engine_continues_from_intervened_state_without_losing_parent_identity(self):
        snapshot = capture_state(self.state, anchor_ref='A0', parent_trace_hash='trace:test')
        key = next(iter(snapshot['shared_state_metadata']))
        intervention = {
            'type': 'set_shared_state_status',
            'key': key,
            'status': 'provisional',
            'result_anchor_ref': 'A0:status-downgraded',
        }
        changed = apply_state_intervention(snapshot, intervention)
        manifest = make_branch_manifest(
            branch_id='B-CONTINUE-001',
            parent_trace_hash='trace:test',
            parent_snapshot=snapshot,
            branch_start_snapshot=changed,
            intervention_spec=intervention,
            replicate_index=1,
            model_identity={'model': 'scripted'},
            config_identity={'arena': self.config['version']},
            code_identity={'commit': 'TEST'},
        )
        scripted = ScriptedProvider([
            {'decision_summary': 'settle', 'actions': [{'type': 'finalize', 'answer': 'Initial plan.'}]},
            {'decision_summary': 'settle after late event', 'actions': [{'type': 'finalize', 'answer': 'Final plan.'}]},
        ])
        anchors = []
        trace = run_arena_once(
            self.domain,
            self.config,
            scripted,
            'branch-run-001',
            logical_seed=1,
            initial_state_snapshot=changed,
            branch_manifest=manifest,
            state_snapshot_callback=anchors.append,
        )
        self.assertEqual('RUN_COMPLETE', trace['run_status'])
        self.assertEqual('B-CONTINUE-001', trace['experimental_branch']['branch_id'])
        self.assertEqual(snapshot['state_hash'], trace['experimental_branch']['parent_state_hash'])
        self.assertEqual(changed['state_hash'], trace['experimental_branch']['branch_start_state_hash'])
        self.assertTrue(trace['experimental_branch']['intervention_applied_before_continuation'])
        self.assertFalse(trace['experimental_branch']['provider_internal_state_replayed'])
        self.assertGreaterEqual(len(anchors), 2)
        self.assertTrue(all(verify_state_snapshot(anchor) for anchor in anchors))


if __name__ == '__main__':
    unittest.main()
