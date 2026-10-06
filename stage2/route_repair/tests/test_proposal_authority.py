import copy
import json
import unittest

from stage2.native_v7.software_host_v1 import TASKS
from stage2.route_repair.branch_fields import BranchConstraintError, seal
from stage2.route_repair.proposal_authority import freeze_task_envelope, ProposalAuthorityCompiler
from stage2.route_repair.tests import test_planning_session as fixtures


class ProposalAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.PlanningSessionTests()
        self.f.setUp()
        self.root = self.f.fixture.root
        self.envelope = freeze_task_envelope(self.f.context, TASKS['T2'],
            writable_refs=['file:source.json', 'file:plan.json'], branch_id='automatic-proposal-fixture',
            max_actions=2, max_value_bytes=2048)

    def tearDown(self): self.f.tearDown()

    def compile(self, proposal=None, envelope=None):
        return ProposalAuthorityCompiler(self.f.context, envelope or self.envelope).compile(
            self.f.session, proposal or self.f.proposal)

    def bindings(self):
        t = self.f.proposal['verification_tasks'][0]
        return {'v1': {**t, 'run': lambda root: {'passed': json.loads((root / 'plan.json').read_text())['gate'] == 'pending'}}}

    def test_host_derives_grants_from_proposal_and_dispatches_native_system(self):
        a = self.compile()
        self.assertFalse(self.envelope['replacement_values_prescribed'])
        result = a.system(a.bundle, self.root / 'authorized', verifiers=self.bindings()).execute()
        self.assertEqual(result['native_application_writes'], 2)
        self.assertEqual(result['status'], 'AWAITING_NATIVE_CONTINUATION')
        self.assertFalse(result['repair_success'])

    def test_same_envelope_allows_different_proposed_value_before_freeze(self):
        p = copy.deepcopy(self.f.proposal)
        p['application_actions'][0]['value'] = 'another proposed value'
        a = self.compile(p)
        self.assertEqual(a.bundle['application_plan']['actions'][0]['value'], 'another proposed value')
        self.assertFalse(a.receipt['semantic_claims_grant_extra_permissions'])

    def test_resealed_value_or_dependency_change_rejected_before_copy(self):
        a = self.compile()
        for key, value in [('value', 'forged value'), ('depends_on', ['a2'])]:
            b = a.bundle
            b['proposal']['application_actions'][0][key] = value
            b.pop('bundle_hash')
            with self.assertRaisesRegex(BranchConstraintError, 'HOST_FROZEN_PROPOSAL_MISMATCH'):
                a.system(seal(b, 'bundle_hash'), self.root / 'forged', verifiers=self.bindings())
        self.assertFalse((self.root / 'forged').exists())

    def test_returned_copies_cannot_widen_retained_authorization(self):
        a = self.compile()
        b = a.bundle
        b['application_plan']['policy']['field_grants'].append({'target_ref': 'file:untouched.py'})
        self.assertNotEqual(b, a.bundle)
        with self.assertRaisesRegex(BranchConstraintError, 'FROZEN_PROPOSAL'):
            a.system(b, self.root / 'forged', verifiers=self.bindings())

    def test_visible_object_does_not_enlarge_original_host_envelope(self):
        p = copy.deepcopy(self.f.proposal)
        p['application_actions'][0]['target_ref'] = 'file:untouched.py'
        with self.assertRaisesRegex(BranchConstraintError, 'WRITE_OUTSIDE_TASK_ENVELOPE'): self.compile(p)

    def test_action_and_value_budgets_are_host_owned(self):
        e = freeze_task_envelope(self.f.context, TASKS['T2'], writable_refs=self.envelope['writable_refs'],
            branch_id='small', max_actions=1, max_value_bytes=2048)
        with self.assertRaisesRegex(BranchConstraintError, 'ACTION_BUDGET'): self.compile(envelope=e)
        p = copy.deepcopy(self.f.proposal)
        p['application_actions'][0]['value'] = 'x' * 3000
        with self.assertRaisesRegex(BranchConstraintError, 'VALUE_BUDGET'): self.compile(p)

    def test_unknown_semantic_claim_and_missing_current_witness_block(self):
        p = copy.deepcopy(self.f.proposal)
        p['diagnoses'][0]['status'] = 'UNKNOWN'
        with self.assertRaisesRegex(BranchConstraintError, 'UNKNOWN_CLAIM'): self.compile(p)
        self.f.session.witnesses.clear()
        with self.assertRaisesRegex(BranchConstraintError, 'CURRENT_TARGET_WITNESS'): self.compile()

    def test_unread_fake_witness_cannot_be_inserted_in_session(self):
        self.f.session.witnesses['witness:1']['quote'] = 'invented authority'
        with self.assertRaisesRegex(BranchConstraintError, 'RECOMPILE_DRIFT'): self.compile()

    def test_second_proposal_and_second_dispatch_require_new_host_authorization(self):
        compiler = ProposalAuthorityCompiler(self.f.context, self.envelope)
        a = compiler.compile(self.f.session, self.f.proposal)
        with self.assertRaisesRegex(BranchConstraintError, 'PROPOSAL_ALREADY_FROZEN'):
            compiler.compile(self.f.session, self.f.proposal)
        a.system(a.bundle, self.root / 'authorized', verifiers=self.bindings())
        with self.assertRaisesRegex(BranchConstraintError, 'AUTHORIZATION_ALREADY_DISPATCHED'):
            a.system(a.bundle, self.root / 'second', verifiers=self.bindings())


if __name__ == '__main__': unittest.main()
