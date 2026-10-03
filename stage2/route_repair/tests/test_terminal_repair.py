import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.terminal import FrozenGraphAccess,exact_hash,validate_terminal_decision


class TerminalRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.archive=self.root/'source.tar.gz';self.raw=b'{"content":"observed record"}'
        with tarfile.open(self.archive,'w:gz') as tf:
            m=tarfile.TarInfo('native/raw.json');m.size=len(self.raw);tf.addfile(m,io.BytesIO(self.raw))
        self.sha=exact_hash(self.archive)
        self.observation={'observation_id':'obs:1','object_refs':['file:a.py'],
            'source_locator':{'archive_sha256':self.sha,'member':'native/raw.json',
                'member_sha256':digest(self.raw),'json_pointer':'/content','line':None}}
        self.graph={'nodes':[{'ref':'file:a.py'},{'ref':'state:terminal'}],
            'edges':[],'observations':[self.observation]}
        self.graph['graph_hash']=digest(self.graph)
        self.parent={'checkpoint_hash':'parent:1','restore_capability':'FULL_NATIVE','native_state_sha256':'native:1'}
        self.accesses=[]
    def tearDown(self):
        for a in self.accesses:a.close()
        self.temp.cleanup()
    def access(self,arm='GRAPH',**kwargs):
        a=FrozenGraphAccess(self.graph,self.archive,arm=arm,expected_archive_hash=self.sha,**kwargs)
        self.accesses.append(a);return a
    def decision(self,a):
        r=a.query({'op':'read_member','member':'native/raw.json'})
        return {'decision':'NO_REPAIR_NEEDED','parent_checkpoint_hash':'parent:1',
            'reason':'The inspected evidence supports preservation.','evidence':[{'member':r['member'],'sha256':r['member_sha256']}],'actions':[]}
    def validate(self,d,a):
        return validate_terminal_decision(d,access=a,parent=self.parent,current_files={'a.py':'file:1'},
            authorized_files={'a.py'},preserve_files={'a.py'})
    def test_no_repair_is_supported_without_an_action(self):
        a=self.access();r=self.validate(self.decision(a),a)
        self.assertEqual(r['actions'],[]);self.assertIn('decision_hash',r)
    def test_citation_must_have_been_inspected(self):
        a=self.access();d={'decision':'UNRESOLVED','parent_checkpoint_hash':'parent:1','reason':'Need evidence',
            'evidence':[{'observation_id':'obs:1'}],'actions':[]}
        with self.assertRaisesRegex(ValueError,'not inspected'):self.validate(d,a)
    def test_both_arms_can_read_identical_raw_evidence(self):
        local=self.access('LOCAL');graph=self.access('GRAPH')
        q={'op':'read_member','member':'native/raw.json'}
        self.assertEqual(local.query(q),graph.query(q))
        with self.assertRaisesRegex(ValueError,'not available'):local.query({'op':'node','ref':'file:a.py'})
    def test_observation_source_binds_exact_value(self):
        a=self.access();r=a.query({'op':'observation','observation_id':'obs:1'})
        self.assertEqual(json.loads(r['source_text']),'observed record')
        a.validate_citations([{'observation_id':'obs:1'}])
    def test_graph_navigation_is_paginated_not_truncated(self):
        a=self.access();first=a.query({'op':'list_nodes','limit':1})
        second=a.query({'op':'list_nodes','limit':1,'offset':first['next_offset']})
        self.assertEqual(set(first['items']+second['items']),{'file:a.py','state:terminal'})
    def test_archive_drift_fails_before_access(self):
        with self.assertRaisesRegex(ValueError,'archive hash mismatch'):
            FrozenGraphAccess(self.graph,self.archive,arm='GRAPH',expected_archive_hash='wrong')
    def test_wrong_parent_fails_before_action(self):
        a=self.access();d=self.decision(a);d['parent_checkpoint_hash']='another'
        with self.assertRaisesRegex(ValueError,'wrong repair parent'):self.validate(d,a)
    def test_preserved_file_cannot_be_written_even_if_visible(self):
        a=self.access();d=self.decision(a);d['decision']='REPAIR';d['actions']=[{
            'kind':'file_replace','target_ref':'file:a.py','before_hash':'file:1','content':'replacement',
            'reason':'proposed','evidence':d['evidence']}]
        with self.assertRaisesRegex(ValueError,'outside authorized'):self.validate(d,a)
    def test_process_action_binds_current_native_state(self):
        a=self.access();d=self.decision(a);d['decision']='REPAIR';d['actions']=[{
            'kind':'process_revision','target_ref':'state:terminal','before_hash':'stale',
            'instruction':'verify the account','reason':'proposed','evidence':d['evidence']}]
        with self.assertRaisesRegex(ValueError,'stale process state'):self.validate(d,a)
    def test_noop_cannot_smuggle_actions(self):
        a=self.access();d=self.decision(a);d['actions']=[{'kind':'process_revision'}]
        with self.assertRaisesRegex(ValueError,'non-repair decision has actions'):self.validate(d,a)
    def test_query_budget_is_shared_across_operations(self):
        a=self.access(max_queries=1);a.query({'op':'list_members'})
        with self.assertRaisesRegex(ValueError,'budget exhausted'):a.query({'op':'list_nodes'})
    def test_failed_query_consumes_budget_and_is_retained(self):
        a=self.access(max_queries=1)
        with self.assertRaisesRegex(ValueError,'source member absent'):
            a.query({'op':'read_member','member':'missing'})
        with self.assertRaisesRegex(ValueError,'budget exhausted'):a.query({'op':'list_members'})
        self.assertEqual(a.log[0]['request']['member'],'missing')
    def test_both_agents_receive_shared_terminal_evidence_without_case_verdict(self):
        from stage2.route_repair.terminal_runner import agent_diagnosis
        class Probe:
            maximum=1
            def complete_agent(self,messages,metadata=None):
                self.messages=messages
                return {'content':json.dumps({'decision':'UNRESOLVED','reason':'probe',
                    'parent_checkpoint_hash':'parent:1','evidence':[],'actions':[]})}
        case={'full_id':'G3-X4-T2','preserve_file_refs':['file:a.py'],
              'authorized_file_refs':[],'process_revision_allowed':True,
              'purpose_for_evaluation_only':'EVALUATION_SECRET_VERDICT'}
        initial=[]
        for arm in ['LOCAL','GRAPH']:
            a=self.access(arm);terminal=a.query({'op':'read_member','member':'native/raw.json'})
            provider=Probe();agent_diagnosis(provider,a,self.parent,case,{'a.py':'file:1'},terminal)
            message=provider.messages[1]['content'];obj=json.loads(message)
            initial.append(obj['shared_initial_evidence'])
            self.assertNotIn('EVALUATION_SECRET_VERDICT',message)
        self.assertEqual(initial[0],initial[1]);self.assertEqual(initial[0]['text'],self.raw.decode())

if __name__=='__main__':unittest.main()
