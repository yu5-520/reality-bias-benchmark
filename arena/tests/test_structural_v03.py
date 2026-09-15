import json
import tempfile
import unittest
from pathlib import Path
from arena.engine import run_arena_once
from arena.providers import ScriptedProvider
from arena.structural_views import build_views
from arena.journal import Journal
from arena.core import stable_hash

ROOT = Path(__file__).resolve().parents[2]

def actions(*xs):
    return {'actions': list(xs)}

def invoke(target):
    return {'type': 'invoke_agent', 'agent_id': target, 'request': 'check'}

FINAL = {'type': 'finalize', 'answer': 'settled'}

class StructuralTests(unittest.TestCase):
    def setUp(self):
        self.domain = json.loads((ROOT/'arena/domains/ecommerce.json').read_text())
        self.config = json.loads((ROOT/'arena/config/arena_v0.3.json').read_text())

    def run_trace(self, script):
        return run_arena_once(self.domain, self.config, ScriptedProvider(script), 'structural-test')

    def test_repeated_feedback_remains_observable(self):
        t = self.run_trace([
            actions(invoke('inventory'), FINAL),
            actions(FINAL),
            actions({'type':'message','to':'ops_lead','content':'new assessment'}),
            actions({'type':'revise_final_state','patch':{'decision':'changed'},'reason':'assessment'}, invoke('inventory')),
            actions({'type':'message','to':'ops_lead','content':'follow-up'}),
            actions(FINAL),
        ])
        self.assertEqual(t['turns'], 6)
        self.assertEqual(t['run_status'], 'RUN_COMPLETE')
        self.assertEqual(t['termination_reason'], 'queue_empty_with_final_state')
        _, view = build_views(t, 'batch')
        self.assertTrue(view['feedback_candidates'])
        self.assertTrue(any(x['evidence_type']=='message_read_into_input' for x in view['relations']))
        self.assertEqual(view['layers']['R4'], 'PENDING_REVIEW')
        self.assertEqual(t['final_state']['state']['decision'], 'changed')

    def test_turn_limit_is_censoring_even_with_final(self):
        self.config['max_turns'] = 2
        t = self.run_trace([actions(FINAL), actions(invoke('inventory'), FINAL)])
        self.assertEqual(t['run_status'], 'BUDGET_CENSORED')
        self.assertTrue(t['remaining_queue'])
        self.assertTrue(t['observation_censored'])

    def test_natural_end_exactly_at_limit(self):
        self.config['max_turns'] = 2
        t = self.run_trace([actions(FINAL), actions(FINAL)])
        self.assertEqual(t['run_status'], 'RUN_COMPLETE')

    def test_invocation_limit_censors(self):
        self.config['max_total_invocations'] = 1
        t = self.run_trace([actions(invoke('inventory'), invoke('inventory'))])
        self.assertEqual(t['run_status'], 'BUDGET_CENSORED')
        self.assertEqual(t['budget_hits'][0]['reason'], 'invocation_budget_exhausted')

    def test_duplicate_wakeups_preserve_all_messages(self):
        t = self.run_trace([actions(invoke('inventory'), invoke('inventory')), actions(FINAL), actions(FINAL)])
        self.assertEqual(t['turns'], 3)
        self.assertEqual(len(t['model_calls'][1]['input_invocation_ids']), 2)
        self.assertEqual(len(t['invocation_ledger']), 2)

    def test_journal_survives_provider_failure(self):
        class Bad:
            def complete_agent(self, *args, **kwargs):
                raise RuntimeError('offline test failure')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'journal.jsonl'
            with Journal(p) as j:
                t = run_arena_once(self.domain, self.config, Bad(), 'failure', recorder=j)
            rows=[json.loads(x) for x in p.read_text().splitlines()]
            self.assertEqual(t['run_status'], 'RUN_FAILED')
            self.assertEqual(rows[0]['record_type'], 'call_started')
            self.assertEqual(rows[-1]['record_type'], 'turn_failed')
            previous = None
            for row in rows:
                digest = row.pop('record_hash')
                self.assertEqual(stable_hash(row), digest)
                self.assertEqual(row['previous_hash'], previous)
                previous = digest

    def test_legacy_snapshot_not_fabricated(self):
        _, view = build_views({'run_id':'legacy','model_calls':[{}]}, 'batch')
        self.assertEqual(view['state_read_evidence'], 'NOT_RECORDED_IN_SOURCE_VERSION')

if __name__ == '__main__':
    unittest.main()
