import json
import tempfile
import unittest
from pathlib import Path

from arena.core import ArenaState
from arena.engine import run_arena_once
from arena.evidence import build_batch
from arena.providers import ScriptedProvider
from arena.topology import participation_metrics
from arena.review_records import REVIEW_RECORD_VERSION, validate_review_record

ROOT = Path(__file__).resolve().parents[2]


class EvidenceV02Tests(unittest.TestCase):
    def setUp(self):
        self.domain = json.loads((ROOT / 'arena/domains/ecommerce.json').read_text())
        self.cfg = json.loads((ROOT / 'arena/config/arena_v0.2.json').read_text())

    def test_terminal_finalize_waits_for_pending_expert(self):
        state = ArenaState(self.domain, self.cfg, 'wait-test')
        state.turns = 1
        state.runtime_view('ops_lead')
        state.apply_actions('ops_lead', {'actions': [
            {'type': 'invoke_agent', 'agent_id': 'inventory', 'request': 'check'},
            {'type': 'finalize', 'answer': 'first'}
        ]})
        self.assertFalse(state.terminated)
        self.assertIn('inventory', state.queue)
        # consume late event, then terminal finalize is still deferred because expert remains queued
        state.turns += 1
        state.queue.popleft()  # ops_lead late-event slot
        state.runtime_view('ops_lead')
        state.apply_actions('ops_lead', {'actions': [{'type': 'finalize', 'answer': 'second'}]})
        self.assertFalse(state.terminated)
        self.assertIn('inventory', state.queue)
        self.assertEqual(state.events[-1]['note'], 'terminal_finalize_deferred_pending_work')

    def test_participation_distinguishes_activation_and_execution(self):
        scripted = [
            {'actions': [{'type': 'invoke_agent', 'agent_id': 'inventory', 'request': 'check'}]},
            {'actions': [{'type': 'message', 'to': 'ops_lead', 'content': 'done'}]},
            {'actions': [{'type': 'finalize', 'answer': 'first'}]},
            {'actions': [{'type': 'finalize', 'answer': 'second'}]},
        ]
        trace = run_arena_once(self.domain, self.cfg, ScriptedProvider(scripted), 'participation', 1)
        p = participation_metrics(trace)
        self.assertGreaterEqual(p['activated_agent_count'], 2)
        self.assertGreaterEqual(p['executed_agent_count'], 2)
        self.assertEqual(p['message_lifecycle_status'], 'RECORDED')
        self.assertIsNotNone(p['unexecuted_invocations'])

    def test_unreviewed_evidence_report_never_emits_bias_zero(self):
        scripted = [
            {'actions': [{'type': 'finalize', 'answer': 'first'}]},
            {'actions': [{'type': 'finalize', 'answer': 'second'}]},
        ]
        trace = run_arena_once(self.domain, self.cfg, ScriptedProvider(scripted), 'batch', 1)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            manifest = p / 'manifest.jsonl'; traces = p / 'traces.jsonl'
            row = {
                'run_id': 'batch', 'domain_id': 'ecommerce', 'trial': 1,
                'domain_hash': 'd', 'task_hash': trace['task_hash'], 'agent_pool_hash': trace['agent_registry_hash'],
                'arena_config_path': 'arena/config/arena_v0.2.json', 'arena_config_version': self.cfg['version'],
                'arena_config_hash': 'a', 'model_config_version': 'm', 'model_config_hash': 'mhash'
            }
            trace.update(domain_hash='d', arena_config_hash='a', model_config_hash='mhash')
            manifest.write_text(json.dumps(row) + '\n')
            traces.write_text(json.dumps(trace) + '\n')
            build_batch(manifest, traces, None, p / 'out', 'test-sha')
            report = (p / 'out/RUN_REPORT.md').read_text()
            self.assertIn('C/P/R: **NOT_ADJUDICATED**', report)
            self.assertNotIn('|C|0', report)

    def test_review_record_interface(self):
        row = {
            'review_record_version': REVIEW_RECORD_VERSION,
            'review_record_id': 'RR-test', 'record_kind': 'independent',
            'evidence_batch_hash': 'h', 'packet_id': 'p', 'event_id': 'e',
            'reviewer': {'id': 'human-1', 'type': 'human'},
            'rubric_version': 'r', 'prompt_version': 'p',
            'bias_labels': ['C'], 'authorization_judgment': 'UNCERTAIN',
            'rationale': 'insufficient provenance', 'confidence': 0.7,
            'uncertainties': ['missing field'], 'created_at': '2026-09-15T00:00:00Z',
            'review_version': '1', 'parent_review_ids': []
        }
        self.assertTrue(validate_review_record(row))


if __name__ == '__main__':
    unittest.main()
