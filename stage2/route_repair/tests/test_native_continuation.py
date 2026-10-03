import asyncio
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from stage2.r7_checkpoint_v1.common import CheckpointRegistry, digest, file_tree_manifest
from stage2.r7_checkpoint_v1.host_adapter import SoftwareHostCheckpointAdapter
from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost
from stage2.route_repair.branch_fields import BranchConstraintError
from stage2.route_repair.native_continuation import (
    OfflineNativeContinuation, OfflineScript, load_host_parent, MANIFEST_FIELDS,
)


class NativeContinuationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        app = self.root / 'source_application'
        app.mkdir()
        (app / 'a.py').write_text('x=1\n')
        self.host = SoftwareEngineeringHost(task_id='T2', checkout=app, provider=None, max_turns=3)
        self.host.history = [{'turn': 1, 'role': 'release_lead', 'valid': True, 'actions': 0}]
        self.registry = CheckpointRegistry(self.root / 'checkpoints')
        self.manifest = SoftwareHostCheckpointAdapter().capture(system_id='X4_MCP', host=self.host,
            registry=self.registry, application_root=app, group_id='OFFLINE_TEST', run_id='fixture', task_id='T2',
            event_ref='host:turn:0001:post', model_visible_context={'turn': 1}, remaining_horizon=2,
            external_carrier_refs=[{'ref': 'external:immutable', 'sha256': 'fixture'}])
        self.cp = self.manifest['checkpoint_hash']
        self.archive = self.root / 'immutable_archive'
        self.archive.write_bytes(b'frozen fixture archive')
        # No extraction or manifest rewrite.
        self.raw = {'checkpoints/' + self.cp + '/' + str(p.relative_to(self.registry.checkpoint_dir(self.cp))): p.read_bytes()
                    for p in self.registry.checkpoint_dir(self.cp).rglob('*') if p.is_file()}
        self.context = SimpleNamespace(raw=lambda member: self.raw[member],
            ledger={'checkpoints': [{'checkpoint_hash': self.cp, 'boundary': 'AFTER_NATIVE_MODEL_TURN_AT_QUIESCENT_BOUNDARY',
                                    'event_ref': self.manifest['event_ref'], 'model_decision_sequence': 1}]},
            case={'archive_sha256': digest(self.archive.read_bytes())},
            access=SimpleNamespace(archive=SimpleNamespace(name=str(self.archive))))

    def tearDown(self): self.tmp.cleanup()

    def script(self, actions=None):
        return OfflineScript([{'content': json.dumps({'actions': actions or [{'type': 'finalize', 'answer': 'offline fixture'}]})}])

    def branch(self, script=None, out=None, refs=None):
        return OfflineNativeContinuation(self.context, self.cp, out or self.root / 'branch',
            script=script or self.script(), observed_foreign_refs=refs if refs is not None else self.manifest['external_carrier_refs'])

    def update_state(self, **changes):
        prefix = 'checkpoints/' + self.cp + '/'
        state = json.loads(self.raw[prefix + 'native_state.json'])
        state.update(changes)
        self.raw[prefix + 'native_state.json'] = json.dumps(state).encode()
        m = copy.deepcopy(self.manifest)
        m['native_state_sha256'] = digest(state)
        if 'max_turns' in changes: m['remaining_horizon'] = state['max_turns'] - len(state['history'])
        old_cp = self.cp
        self.cp = digest({k: m[k] for k in MANIFEST_FIELDS})
        m['checkpoint_hash'] = self.cp
        m['checkpoint_id'] = f"rbcp:{m['system_id']}:{self.cp[:24]}"
        self.manifest = m
        self.raw[prefix + 'manifest.json'] = json.dumps(m).encode()
        self.raw = {k.replace('checkpoints/' + old_cp + '/', 'checkpoints/' + self.cp + '/'): v for k, v in self.raw.items()}
        self.context.ledger['checkpoints'][0]['checkpoint_hash'] = self.cp

    def test_exact_restore_and_original_numbering_budget_continue(self):
        b = self.branch()
        self.assertEqual(b.adapter.save_state(b.host), SoftwareHostCheckpointAdapter().save_state(self.host))
        r = asyncio.run(b.run())
        self.assertEqual(r['remaining_before'], 2)
        self.assertEqual(r['remaining_after'], 1)
        self.assertEqual(b.host.history[-1]['turn'], 2)
        self.assertEqual(r['provider_calls'], 0)
        self.assertFalse(r['repair_success'])
        self.assertFalse(r['actual_repair_agent_exit_observed'])
        graph = json.loads((b.out / 'full_graph_after.json').read_text())
        kinds = {o['event_kind'] for o in graph['observations']}
        self.assertIn('NATIVE_CLOSURE', kinds)
        self.assertNotIn('REPAIR_AGENT_EXIT', kinds)

    def test_stopped_parent_with_positive_budget_is_not_reopened(self):
        self.update_state(stop_reason='finalized', answer='already done')
        with self.assertRaisesRegex(BranchConstraintError, 'STOPPED_NATIVE_PARENT_NO_REOPEN'): self.branch()
        self.assertFalse((self.root / 'branch').exists())

    def test_zero_budget_and_foreign_carrier_drift_fail_before_copy(self):
        with self.assertRaisesRegex(BranchConstraintError, 'ENVIRONMENT_MISMATCH'): self.branch(refs=[])
        self.update_state(max_turns=1)
        with self.assertRaisesRegex(BranchConstraintError, 'NATIVE_BUDGET_EXHAUSTED'): self.branch()

    def test_hash_drift_and_annotation_only_parent_are_not_restorable(self):
        name = 'checkpoints/' + self.cp + '/application/a.py'
        original = self.raw[name]
        self.raw[name] = b'forged'
        with self.assertRaisesRegex(BranchConstraintError, 'APPLICATION_FILE_HASH_MISMATCH'): self.branch()
        self.raw[name] = original
        self.context.ledger['checkpoints'][0]['event_ref'] = 'structural-only'
        with self.assertRaisesRegex(BranchConstraintError, 'ONLY_HAS_MONITOR_ANNOTATION'): self.branch()

    def test_live_provider_cannot_be_passed_as_offline_script(self):
        with self.assertRaisesRegex(BranchConstraintError, 'LIVE_CONTINUATION_BINDING_DISABLED'):
            self.branch(script=object())

    def test_capture_surrounds_native_write_and_does_not_change_semantics(self):
        script = self.script([{'type': 'write_file', 'path': 'a.py', 'content': 'x=2\n'},
                              {'type': 'finalize', 'answer': 'scripted'}])
        b = self.branch(script)
        r = asyncio.run(b.run())
        self.assertEqual((b.root / 'a.py').read_text(), 'x=2\n')
        self.assertEqual((self.root / 'source_application/a.py').read_text(), 'x=1\n')
        kinds = [o['event_kind'] for o in sorted(b.observer.graph.snapshot()['observations'],
                                                key=lambda o: o['native_sequence'])]
        self.assertLess(kinds.index('NATIVE_ACTION_BEFORE'), kinds.index('NATIVE_ACTION_RESULT'))
        self.assertLess(kinds.index('NATIVE_ACTION_RESULT'), kinds.index('NATIVE_ACTION_AFTER'))
        self.assertTrue(r['history_prefix_preserved'])

    def test_interruption_retains_partial_state_and_never_replays(self):
        b = self.branch(self.script([{'type': 'read_file', 'path': 'a.py'}]))
        with self.assertRaisesRegex(BranchConstraintError, 'SCRIPT_EXHAUSTED'): asyncio.run(b.run())
        r = json.loads((b.out / 'continuation_receipt.json').read_text())
        self.assertEqual(r['status'], 'INTERRUPTED_OR_FAILED_REQUIRES_READ_ONLY_REVIEW')
        self.assertEqual(r['scripted_response_calls'], 1)
        self.assertTrue((b.out / 'continuation_intent.json').exists())
        with self.assertRaisesRegex(BranchConstraintError, 'ALREADY_ATTEMPTED'): asyncio.run(b.run())
        with self.assertRaisesRegex(BranchConstraintError, 'FRESH_CONTINUATION_BRANCH_REQUIRED'): self.branch()

    def test_budget_censor_and_pre_run_drift_are_retained_or_blocked(self):
        self.update_state(max_turns=2)
        b = self.branch(self.script([{'type': 'read_file', 'path': 'a.py'}]))
        r = asyncio.run(b.run())
        self.assertEqual(r['stop_reason'], 'turn_budget')
        self.assertEqual(r['remaining_after'], 0)
        kinds = {o['event_kind'] for o in b.observer.graph.snapshot()['observations']}
        self.assertIn('NATIVE_CENSOR', kinds)
        b2 = self.branch(out=self.root / 'drift')
        b2.host.queue.clear()
        with self.assertRaisesRegex(BranchConstraintError, 'PRE_RUN_DRIFT'): asyncio.run(b2.run())


if __name__ == '__main__': unittest.main()
