import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from arena.core import ArenaState
from arena.engine import run_arena_once
from arena.evaluation import build_evaluator_messages, validate_evaluation
from arena.counterfactual import replay_immediate_containment
from arena.providers import ScriptedProvider

ROOT = Path(__file__).resolve().parents[2]


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.domain = json.loads((ROOT/'arena/domains/ecommerce.json').read_text())
        self.config = json.loads((ROOT/'arena/config/arena_v0.1.json').read_text())
        self.state = ArenaState(self.domain, self.config, 'test')

    def write(self):
        self.state.apply_actions('ops_lead', {'actions': [{'type':'write_state','key':'stock','value':1520,'status':'provisional','basis':'preliminary feed'}]})

    def codes(self, **changes):
        row = dict(event_index=0, bias_mechanisms=['C'], authorized_under_contract=False, confidence=0.8, evidence='Unsupported promotion')
        row.update(changes)
        return {'coded_events':[row]}

    def test_metadata_survives_write_and_snapshot(self):
        self.write()
        view = self.state.runtime_view('ops_lead')
        self.assertEqual(view['shared_state_metadata']['stock']['status'], 'provisional')
        self.state.apply_actions('ops_lead', {'actions':[{'type':'finalize','answer':'initial'}]})
        self.assertEqual(self.state.final_state['state_metadata']['stock']['basis'], 'preliminary feed')

    def test_finalize_requires_observed_late_event_and_stops_response(self):
        self.state.apply_actions('ops_lead', {'actions':[{'type':'finalize'}, {'type':'finalize'}, {'type':'write_state','key':'bad','value':1}]})
        self.assertFalse(self.state.terminated)
        self.assertNotIn('bad', self.state.shared_state)
        self.assertEqual(self.state.queue[0], 'ops_lead')
        self.state.apply_actions('ops_lead', {'actions':[{'type':'finalize'}]})
        self.assertFalse(self.state.terminated)
        self.state.runtime_view('ops_lead')
        self.state.apply_actions('ops_lead', {'actions':[{'type':'finalize'}, {'type':'write_state','key':'bad','value':1}]})
        self.assertTrue(self.state.terminated)
        self.assertNotIn('bad', self.state.shared_state)

    def test_queue_failure_does_not_activate_agent(self):
        self.state.config = {**self.config, 'max_pending_messages':0}
        self.state.apply_actions('ops_lead', {'actions':[{'type':'invoke_agent','agent_id':'inventory'}]})
        self.assertNotIn('inventory', self.state.active_agents)
        self.assertEqual(self.state.total_invocations, 0)
        self.assertFalse(self.state.events[-1]['realized_in_baseline'])

    def test_complete_typed_evaluation_required(self):
        self.write(); trace={'events':self.state.events}
        for evaluation in ({}, {'coded_events':[]}, self.codes(authorized_under_contract='false'), self.codes(confidence=float('nan')), self.codes(evidence=''), self.codes(event_index=True)):
            with self.subTest(evaluation=evaluation), self.assertRaises(ValueError):
                validate_evaluation(trace,evaluation)
        self.assertTrue(validate_evaluation(trace,self.codes()))
        self.assertTrue(validate_evaluation({'events':[]},{'coded_events':[]}))

    def test_replay_keeps_baseline_failures_separate(self):
        self.write()
        trace={'run_id':'test','domain_id':'ecommerce','events':copy.deepcopy(self.state.events)}
        trace['events'][0]['realized_in_baseline']=False
        for row in replay_immediate_containment(trace,self.codes()):
            self.assertEqual(row['realized_event_indices'],[])
            self.assertEqual(row['blocked_event_indices'],[])
            self.assertEqual(row['baseline_unrealized_event_indices'],[0])
        trace['events'][0]['realized_in_baseline']=True
        rows=replay_immediate_containment(trace,self.codes())
        self.assertEqual(rows[0]['realized_event_indices'],[0])
        self.assertEqual(rows[1]['blocked_event_indices'],[0])

    def test_evaluator_receives_actual_turn_inputs_and_messages(self):
        scripted=[{'actions':[{'type':'invoke_agent','agent_id':'inventory','request':'stock?'}]},
                  {'actions':[{'type':'message','to':'ops_lead','content':'preliminary stock'}]},
                  {'actions':[{'type':'finalize'}]}, {'actions':[{'type':'finalize'}]}]
        trace=run_arena_once(self.domain,self.config,ScriptedProvider(scripted),'test')
        payload=json.loads(build_evaluator_messages(self.domain,self.config,trace)[1]['content'])
        self.assertTrue(any(e['action_type']=='message' for e in payload['full_event_trace']))
        self.assertTrue(all(c['messages'] for c in payload['per_turn_inputs']))
        self.assertNotIn('environment_late_event', json.dumps(payload['per_turn_inputs'][0]['messages']))
        self.assertIn('environment_late_event', json.dumps(payload['per_turn_inputs'][-1]['messages']))
        self.assertTrue(trace['late_event_consumed'])

    def test_analysis_excludes_failed_and_authorized_events(self):
        self.write(); base=copy.deepcopy(self.state.events[0])
        events=[]; codes=[]
        for i,(realized,authorized) in enumerate([(False,False),(True,True),(True,False)]):
            e=copy.deepcopy(base); e.update(event_index=i,realized_in_baseline=realized); events.append(e)
            codes.append(self.codes(event_index=i,authorized_under_contract=authorized)['coded_events'][0])
        trace={'run_id':'test','domain_id':'ecommerce','activated_agent_count':1,'events':events}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); (p/'traces').write_text(json.dumps(trace)+'\n')
            (p/'evals').write_text(json.dumps({'run_id':'test','evaluation':{'coded_events':codes}})+'\n')
            subprocess.run([sys.executable,'-m','arena.analyze','--traces',str(p/'traces'),'--evaluations',str(p/'evals'),'--outdir',str(p/'out')],cwd=ROOT,check=True,capture_output=True)
            import csv
            with (p/'out/bias_authority_3x3.csv').open() as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(sum(int(r['event_count']) for r in rows),1)
            with (p/'out/run_level.csv').open() as f:
                self.assertEqual(next(csv.DictReader(f))['first_bias_event_index'],'2')


if __name__ == '__main__':
    unittest.main()
