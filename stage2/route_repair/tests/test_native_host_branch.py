import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost, TASKS, SUBJECT_LIMITS
from stage2.r7_checkpoint_v1.common import digest, stable_json_bytes, file_tree_manifest
from stage2.r7_checkpoint_v1.host_adapter import SoftwareHostCheckpointAdapter, ADAPTER_ID
from stage2.route_repair.branch_fields import BranchConstraintError, seal
from stage2.route_repair.native_host_branch import (
    NativeHostAnswerBinding, NoCallProvider, build_host_answer_policy,
)


class SourceFixture:
    def __init__(self, state):
        self.case = {'terminal_checkpoint_hash':'cp', 'archive_sha256':'archive'}
        self.graph = {'graph_hash':'graph'}
        self.members = {
            'checkpoints/cp/native_state.json':stable_json_bytes(state),
            'checkpoints/cp/manifest.json':stable_json_bytes({
                'adapter_id':ADAPTER_ID, 'restore_capability':'FULL_NATIVE',
                'system_id':'X4_MCP', 'checkpoint_hash':'cp', 'native_state_sha256':digest(state)}),
            'natural_A_result.json':stable_json_bytes({'answer':state['answer']}),
        }
    def raw(self, member):
        return self.members[member]
    def locator(self, member):
        return {'member':member, 'member_sha256':digest(self.raw(member))}


class ObserverFixture:
    def __init__(self, out):
        self.out = out
        self.captures = []
    def capture(self, *args, **kwargs):
        self.captures.append((args, kwargs))


class NativeHostBranchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.checkout = self.root/'application'
        self.checkout.mkdir()
        (self.checkout/'preserve.txt').write_text('unchanged')
        host = SoftwareEngineeringHost(task_id='T2', checkout=self.checkout,
            provider=NoCallProvider(), max_turns=1)
        host.max_turns = 64
        host.answer = 'old captured account'
        host.stop_reason = 'finalized'
        host.history = [{'turn':1,'account':'historical old captured account'}]
        self.before = SoftwareHostCheckpointAdapter().save_state(host)
        self.context = SourceFixture(self.before)
        self.policy = build_host_answer_policy(self.context, original_task=TASKS['T2'],
            answer='source-grounded corrected account',
            evidence=[self.context.locator('natural_A_result.json')],
            depends_on=['application_action','verified_route'])
        self.observer = ObserverFixture(self.root/'evidence')
    def tearDown(self):
        self.temp.cleanup()
    def binding(self, policy=None, trusted=None):
        return NativeHostAnswerBinding(self.context, self.checkout, policy or self.policy,
            trusted_policy=self.policy if trusted is None else trusted)
    def apply(self, binding):
        return binding.apply(completed_actions=['application_action','verified_route'], observer=self.observer)
    def reseal(self, policy):
        return seal({k:v for k,v in policy.items() if k!='policy_hash'}, 'policy_hash')

    def test_only_current_answer_changes_and_original_budget_restored(self):
        limits = copy.deepcopy(SUBJECT_LIMITS)
        manifest = file_tree_manifest(self.checkout)
        binding = self.binding()
        self.assertEqual(binding.current(), self.before)
        receipt = self.apply(binding)
        self.assertIsNone(receipt['error'])
        after = binding.current()
        self.assertEqual(after['answer'], self.policy['value'])
        self.assertEqual({k:v for k,v in after.items() if k!='answer'},
                         {k:v for k,v in self.before.items() if k!='answer'})
        self.assertEqual(file_tree_manifest(self.checkout), manifest)
        self.assertEqual(SUBJECT_LIMITS, limits)
        self.assertEqual(receipt['new_provider_calls'],0)
        self.assertEqual(len(self.observer.captures),2)

    def test_uncompleted_dependency_blocks_without_supersession(self):
        binding = self.binding()
        with self.assertRaisesRegex(BranchConstraintError,'DEPENDENCY_NOT_COMPLETE'):
            binding.apply(completed_actions=['application_action'], observer=self.observer)
        self.assertEqual(binding.current(),self.before)
        self.assertFalse(binding.executed)
        self.assertEqual(self.observer.captures,[])

    def test_host_drift_blocks_without_rewriting_history(self):
        binding = self.binding()
        binding.host.history.append({'external':'drift'})
        with self.assertRaisesRegex(BranchConstraintError,'STALE_HOST_STATE'):self.apply(binding)
        self.assertEqual(binding.host.answer,self.before['answer'])

    def test_repeated_supersession_is_rejected(self):
        binding = self.binding();self.apply(binding)
        with self.assertRaisesRegex(BranchConstraintError,'ALREADY_APPLIED'):self.apply(binding)

    def test_resealed_policy_cannot_override_host_authority(self):
        policy=copy.deepcopy(self.policy);policy['value']='unapproved'
        with self.assertRaisesRegex(BranchConstraintError,'TRUSTED_POLICY_MISMATCH'):
            self.binding(self.reseal(policy))

    def test_even_trusted_policy_revalidates_source_and_projected_hash(self):
        policy=copy.deepcopy(self.policy);policy['after_state_hash']='forged'
        policy=self.reseal(policy)
        with self.assertRaisesRegex(BranchConstraintError,'SOURCE_REVALIDATION_FAILED'):
            self.binding(policy,trusted=policy)

    def test_historical_or_private_field_never_supported(self):
        for field in ['/history','/inbox','/queue','/private_memory']:
            policy=copy.deepcopy(self.policy);policy['field_path']=field;policy=self.reseal(policy)
            with self.assertRaisesRegex(BranchConstraintError,'FIELD_NOT_AUTHORIZED'):
                self.binding(policy,trusted=policy)

    def test_original_task_text_cannot_be_replaced(self):
        task=copy.deepcopy(TASKS['T2']);task['user_request']='only edit the answer'
        with self.assertRaisesRegex(BranchConstraintError,'ORIGINAL_TASK_BINDING_MISMATCH'):
            build_host_answer_policy(self.context,original_task=task,answer='new',
                evidence=self.policy['source_witnesses'],depends_on=['a'])

    def test_source_state_drift_and_foreign_adapter_block_before_restore(self):
        changed=copy.deepcopy(self.before);changed['answer']='drift'
        self.context.members['checkpoints/cp/native_state.json']=stable_json_bytes(changed)
        with self.assertRaisesRegex(BranchConstraintError,'STATE_VERSION_MISMATCH'):self.binding()
        self.context.members['checkpoints/cp/native_state.json']=stable_json_bytes(self.before)
        manifest=json.loads(self.context.raw('checkpoints/cp/manifest.json'))
        manifest['system_id']='PRIVATE_PRODUCT'
        self.context.members['checkpoints/cp/manifest.json']=stable_json_bytes(manifest)
        with self.assertRaisesRegex(BranchConstraintError,'FOREIGN_STATE_NOT_WRITABLE'):self.binding()

    def test_native_postcondition_failure_keeps_actual_receipt(self):
        binding=self.binding()
        def incorrect_restore(host,state):host.answer='incorrect native output'
        with patch.object(binding.adapter,'load_state',side_effect=incorrect_restore):
            receipt=self.apply(binding)
        self.assertIn('POSTCONDITION_FAILED',receipt['error']['message'])
        self.assertEqual(receipt['after_hash'],digest(binding.current()))
        self.assertTrue((self.observer.out/'native_host_action_receipt.json').exists())
        self.assertEqual(self.observer.captures[-1][0][1],stable_json_bytes(binding.current()).decode())
        self.assertEqual(binding.current()['history'],self.before['history'])

    def test_offline_provider_is_fail_closed(self):
        with self.assertRaisesRegex(RuntimeError,'PROVIDER_CALL_FORBIDDEN'):
            NoCallProvider().complete_agent([])


if __name__=='__main__':unittest.main()
