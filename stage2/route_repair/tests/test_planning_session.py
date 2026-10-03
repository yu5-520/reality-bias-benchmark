import copy
import unittest
from unittest.mock import patch

from stage2.native_v7.software_host_v1 import TASKS
from stage2.route_repair.branch_fields import BranchConstraintError, build_branch_policy
from stage2.route_repair.planning_session import RoutePlanningSession
from stage2.route_repair.tests import test_branch_fields as field_fixtures


class PlanningSessionTests(unittest.TestCase):
    def setUp(self):
        self.fixture=field_fixtures.FieldBranchTests();self.fixture.setUp()
        self.context=self.fixture.ctx
        self.session=RoutePlanningSession(self.context,TASKS['T2'])
        self.policy=build_branch_policy(self.context,original_task=TASKS['T2'],
            branch_id='offline-planning-fixture',semantic_id='unadjudicated-fixture',
            route_refs=['file:source.json','file:plan.json'],
            grants=[{'target_ref':'file:source.json','kind':'JSON_LEAF_REPLACE','pointer':'/status'},
                    {'target_ref':'file:plan.json','kind':'JSON_LEAF_REPLACE','pointer':'/gate'}],
            evidence=self.fixture.policy['source_witnesses'])
        self.ids=[]
        for ref in ['file:source.json','file:plan.json']:
            row=self.session.file(ref)
            self.ids.append(self.session.witness(row['read_id'],0,len(row['text']))['witness_id'])
        self.session.file('file:untouched.py')
        actions=copy.deepcopy(self.fixture.actions)
        for action in actions:action['diagnosis_ids']=['claim-1']
        self.proposal={'schema':'stage2-complete-route-proposal-v1','original_task':copy.deepcopy(TASKS['T2']),
            'graph_hash':self.context.graph['graph_hash'],'archive_sha256':self.context.case['archive_sha256'],
            'parent_checkpoint_hash':'cp','route_refs':['file:source.json','file:plan.json','file:untouched.py'],
            'modify_refs':['file:source.json','file:plan.json'],'preserve_refs':['file:untouched.py'],'verify_refs':[],
            'diagnoses':[{'claim_id':'claim-1','source_ref':'file:source.json','destination_ref':'file:plan.json',
                'status':'CANDIDATE','adoption_status':'UNKNOWN','meaning_before':'source status',
                'meaning_after':'plan gate','authority_effect':'candidate obligation; not adjudicated',
                'limitation':'synthetic fixture; source spans do not establish adoption','witness_ids':self.ids}],
            'unknown_relations':['No semantic adoption demonstrated.'],
            'expected_postconditions':['Existing fixture leaf values changed; other values retained.'],
            'application_actions':actions,'host_answer':None,
            'verification_tasks':[{'verification_id':'v1','operation':'HOST_DEFINED_OFFLINE_CHECK',
                'refs':['file:plan.json'],'depends_on':['a2'],'postcondition':'host must check exact value'}],
            'execution_order':['a1','a2','v1']}
    def tearDown(self):self.fixture.tearDown()
    def compile(self, proposal=None, policy=None):
        return self.session.compile(proposal or self.proposal,trusted_application_policy=policy or self.policy)

    def test_full_catalog_source_binding_and_plan_do_not_write_or_adjudicate(self):
        catalog=self.session.catalog()
        result=self.compile()
        self.assertEqual(catalog['node_count'],len(self.context.graph['nodes']))
        self.assertEqual(result['application_plan']['execution_order'],['a1','a2'])
        self.assertFalse(result['semantic_diagnosis_adjudicated'])
        self.assertFalse(result['verification_tasks_executed'])
        self.assertFalse(result['live_execution_ready'])
        self.assertEqual(result['native_actions_executed'],0)
        self.assertFalse((self.fixture.root/'branch').exists())
        self.assertEqual(result['inspected_source_witnesses']['witness:1']['quote'],self.fixture.files['source.json'])

    def test_fabricated_unread_witness_and_bad_span_rejected(self):
        with self.assertRaisesRegex(BranchConstraintError,'NOT_INSPECTED'):self.session.witness('fake',0,1)
        with self.assertRaisesRegex(BranchConstraintError,'SPAN_REQUIRED'):self.session.witness('read:1',0,9999)
        proposal=copy.deepcopy(self.proposal);proposal['diagnoses'][0]['witness_ids']=['fake']
        with self.assertRaisesRegex(BranchConstraintError,'WITNESS_NOT_INSPECTED'):self.compile(proposal)

    def test_one_endpoint_source_cannot_stand_in_for_other_endpoint(self):
        proposal=copy.deepcopy(self.proposal);proposal['diagnoses'][0]['witness_ids']=[self.ids[0]]
        with self.assertRaisesRegex(BranchConstraintError,'ENDPOINT_WITNESS_REQUIRED'):self.compile(proposal)

    def test_agent_cannot_claim_verified_semantics_or_adoption(self):
        for field,value in [('status','VERIFIED'),('adoption_status','VERIFIED')]:
            proposal=copy.deepcopy(self.proposal);proposal['diagnoses'][0][field]=value
            with self.assertRaises(BranchConstraintError):self.compile(proposal)

    def test_unknown_claim_cannot_justify_action(self):
        proposal=copy.deepcopy(self.proposal);proposal['diagnoses'][0]['status']='UNKNOWN'
        with self.assertRaisesRegex(BranchConstraintError,'UNKNOWN_CLAIM'):self.compile(proposal)

    def test_task_and_parent_and_uninspected_route_rejected(self):
        for field,value in [('graph_hash','wrong'),('parent_checkpoint_hash','wrong'),('original_task',{'id':'T2'})]:
            proposal=copy.deepcopy(self.proposal);proposal[field]=value
            with self.assertRaises(BranchConstraintError):self.compile(proposal)
        self.session.inspected_nodes.remove('file:untouched.py')
        with self.assertRaisesRegex(BranchConstraintError,'NODE_NOT_INSPECTED'):self.compile()

    def test_role_conflict_missing_classification_and_unbound_actions_rejected(self):
        for field,value in [('preserve_refs',[]),('verify_refs',['file:source.json'])]:
            proposal=copy.deepcopy(self.proposal);proposal[field]=value
            with self.assertRaises(BranchConstraintError):self.compile(proposal)
        proposal=copy.deepcopy(self.proposal);proposal['application_actions'][0]['diagnosis_ids']=['fake']
        with self.assertRaisesRegex(BranchConstraintError,'DIAGNOSIS_NOT_BOUND'):self.compile(proposal)

    def test_whole_graph_visibility_does_not_grant_writes(self):
        proposal=copy.deepcopy(self.proposal);proposal['application_actions'][0]['pointer']='/other'
        with self.assertRaisesRegex(BranchConstraintError,'FIELD_OUTSIDE_BRANCH'):self.compile(proposal)
        with self.assertRaisesRegex(BranchConstraintError,'SEPARATE_HOST_APPLICATION_POLICY_REQUIRED'):
            self.session.compile(self.proposal)

    def test_verification_is_not_arbitrary_code_or_self_certified_completion(self):
        proposal=copy.deepcopy(self.proposal);proposal['verification_tasks'][0]['operation']='SHELL'
        with self.assertRaisesRegex(BranchConstraintError,'UNSUPPORTED_VERIFICATION'):self.compile(proposal)
        proposal=copy.deepcopy(self.proposal);proposal['verification_tasks'][0]['depends_on']=['missing']
        with self.assertRaisesRegex(BranchConstraintError,'DEPENDENCY_NOT_ORDERED'):self.compile(proposal)
        proposal=copy.deepcopy(self.proposal);proposal['execution_order']=['v1','a1','a2']
        with self.assertRaisesRegex(BranchConstraintError,'COORDINATED_ORDER'):self.compile(proposal)

    def test_live_origin_is_blocked(self):
        with self.assertRaisesRegex(BranchConstraintError,'LIVE_PLANNING_NOT_READY'):
            RoutePlanningSession(self.context,TASKS['T2'],proposal_origin='LIVE_AGENT')

    def test_native_observation_must_bind_the_requested_object(self):
        native={'observation':{'object_refs':['file:source.json'],
            'source_locator':self.context.locator('checkpoints/cp/application/source.json')},
            'source_text':self.fixture.files['source.json']}
        with patch.object(self.context,'observation_source',return_value=native):
            read=self.session.observation('native-1','file:source.json')
            self.assertEqual(read['text'],native['source_text'])
            with self.assertRaisesRegex(BranchConstraintError,'REF_NOT_BOUND'):
                self.session.observation('native-1','file:plan.json')


if __name__=='__main__':unittest.main()
