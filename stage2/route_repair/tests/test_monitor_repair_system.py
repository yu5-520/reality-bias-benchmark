import copy
import json
import tempfile
import unittest
from pathlib import Path

from stage2.r7_checkpoint_v1.common import digest
from stage2.monitor_enhancement.evidence_graph import EvidenceGraph
from stage2.monitor_enhancement.snapshot_append import AppendOnlyEvidenceGraph
from stage2.route_repair.branch_fields import BranchConstraintError, seal
from stage2.route_repair.offline_system import OfflineRouteRepairSystem
from stage2.route_repair.recovery_journal import RecoveryJournal
from stage2.route_repair.system_contract import build_system_contract, assess_continuation
from stage2.route_repair.tests import test_planning_session as fixtures


class MonitorRepairSystemTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PlanningSessionTests()
        self.fixture.setUp()
        self.bundle = self.fixture.compile()
        self.root = self.fixture.fixture.root

    def tearDown(self):
        self.fixture.tearDown()

    def system(self, bundle=None, verifier=None, bindings=True):
        task = self.bundle['proposal']['verification_tasks'][0]
        binding = {'operation': task['operation'], 'refs': task['refs'], 'postcondition': task['postcondition'],
                   'run': verifier or (lambda root: {'passed': json.loads((root / 'plan.json').read_text())['gate'] == 'pending'})}
        return OfflineRouteRepairSystem(self.fixture.context, bundle or self.bundle, self.root / 'system',
                                        application_policy=self.fixture.policy,
                                        verifiers={'v1': binding} if bindings else {})

    def test_coordinated_branch_runs_and_retains_pending_effectiveness(self):
        system = self.system()
        result = system.execute()
        self.assertEqual(result['completed_steps'], ['a1', 'a2', 'v1'])
        self.assertEqual(result['native_application_writes'], 2)
        self.assertEqual(result['status'], 'AWAITING_NATIVE_CONTINUATION')
        self.assertFalse(result['repair_success'])
        self.assertEqual((system.executor.root / 'untouched.py').read_text(), 'x=1\n')
        self.assertTrue(result['graph_comparison']['historical_prefix_preserved'])
        assessment = json.loads((system.out / 'continuation_assessment.json').read_text())
        self.assertGreater(assessment['new_sources_verified'], 0)
        self.assertEqual(assessment['status'], 'PENDING_NATIVE_CONTINUATION')
        self.assertEqual(result['live_provider_calls'], 0)
        self.assertFalse(result['branch_promoted'])

    def test_missing_native_verifier_blocks_before_copy_or_write(self):
        with self.assertRaisesRegex(BranchConstraintError, 'CAPABILITY_MISSING'):
            self.system(bindings=False)
        self.assertFalse((self.root / 'system').exists())

    def test_fabricated_source_citation_cannot_be_resealed(self):
        bundle = copy.deepcopy(self.bundle)
        bundle['inspected_source_witnesses']['witness:1']['quote'] = 'fabricated authority'
        bundle.pop('bundle_hash')
        with self.assertRaisesRegex(BranchConstraintError, 'RECOMPILE_DRIFT'):
            self.system(seal(bundle, 'bundle_hash'))
        self.assertFalse((self.root / 'system').exists())

    def test_failed_host_verification_retains_actions_without_success_or_retry(self):
        system = self.system(verifier=lambda root: {'passed': False})
        result = system.execute()
        self.assertEqual(result['status'], 'BLOCKED_WITH_PARTIAL_EVIDENCE')
        self.assertEqual(result['completed_steps'], ['a1', 'a2'])
        self.assertFalse(result['repair_success'])
        with self.assertRaisesRegex(BranchConstraintError, 'ALREADY_EXECUTED'):
            system.execute()

    def test_verifier_cannot_mutate_an_unrelated_object_without_detection(self):
        def mutation(root):
            (root / 'untouched.py').write_text('x=99\n')
            return {'passed': True}
        result = self.system(verifier=mutation).execute()
        self.assertEqual(result['status'], 'BLOCKED_WITH_PARTIAL_EVIDENCE')
        self.assertIn('MUTATED_APPLICATION', result['error']['message'])
        self.assertFalse(result['repair_success'])

    def test_source_drift_blocks_and_retains_a_recovery_journal(self):
        system = self.system()
        (system.executor.root / 'source.json').write_text('{"status":"different"}\n')
        result = system.execute()
        self.assertEqual(result['status'], 'BLOCKED_WITH_PARTIAL_EVIDENCE')
        self.assertEqual(result['native_application_writes'], 0)
        self.assertTrue((system.out / 'recovery_journal').exists())

    def test_contract_watches_old_cp_reentry_and_unrelated_progression(self):
        contract = build_system_contract(self.bundle, self.fixture.context.graph)
        checks = contract['lineage_obligations'][0]['checks']
        self.assertIn('OLD_INFORMATION_AUTHORITY', checks)
        self.assertIn('OLD_TASK_PERMISSION', checks)
        self.assertIn('HISTORICAL_REENTRY', checks)
        self.assertIn('UNRELATED_SEMANTIC_PROGRESSION', checks)
        self.assertFalse(contract['graph_reachability_grants_writes'])


class ContinuationEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PlanningSessionTests()
        self.fixture.setUp()
        self.before = self.fixture.context.graph
        self.contract = build_system_contract(self.fixture.compile(), self.before)
        self.graph = AppendOnlyEvidenceGraph.from_snapshot(self.before)
        self.sources = {}

    def tearDown(self):
        self.fixture.tearDown()

    def add(self, name, sequence, clock='native', kind='NATIVE_CONTINUATION', ref='file:plan.json', content='old version'):
        raw = json.dumps({'content': content}).encode()
        self.sources[name] = raw
        self.graph.add_observation({'schema': 'RB-STAGE2-ENHANCED-OBSERVATION-v1',
            'observation_id': name, 'event_ref': name, 'evidence_ref': 'raw:' + name,
            'object_refs': [ref], 'native_sequence': sequence, 'clock_id': clock, 'event_kind': kind,
            'content_hash': digest(content.encode()),
            'source_locator': {'member': name + '.json', 'member_sha256': digest(raw), 'json_pointer': '/content', 'line': None}})

    def assess(self, exit_id='exit'):
        return assess_continuation(self.contract, self.before, self.graph.snapshot(),
                                   source_reader=lambda row: self.sources[row['observation_id']], exit_observation_id=exit_id)

    def test_activity_after_exit_does_not_establish_success(self):
        self.add('exit', 10, kind='REPAIR_AGENT_EXIT')
        self.add('next', 11)
        result = self.assess()
        self.assertEqual(result['ordered_post_exit_observation_ids'], ['next'])
        self.assertEqual(result['status'], 'PENDING_INDEPENDENT_SEMANTIC_REVIEW')
        self.assertFalse(result['repair_success'])

    def test_other_clock_cannot_be_promoted_to_post_exit_order(self):
        self.add('exit', 10, kind='REPAIR_AGENT_EXIT')
        self.add('next', 1000, clock='other')
        result = self.assess()
        self.assertEqual(result['ordered_post_exit_observation_ids'], [])
        self.assertEqual(result['cross_clock_unordered_observation_ids'], ['next'])
        self.assertEqual(result['status'], 'PENDING_NATIVE_CONTINUATION')

    def test_repair_write_is_not_an_agent_exit(self):
        self.add('exit', 10, kind='ACTION_AFTER')
        with self.assertRaisesRegex(BranchConstraintError, 'EXIT_RECORD_REQUIRED'):
            self.assess()

    def test_literal_historical_version_in_a_new_carrier_is_only_a_clue(self):
        self.graph._observations['obs:0']['content_hash'] = digest(b'old version')
        self.before = self.graph.snapshot()
        payload = {k: v for k, v in self.contract.items() if k != 'contract_hash'}
        payload['source_graph_hash'] = self.before['graph_hash']
        self.contract = seal(payload, 'contract_hash')
        self.add('exit', 10, kind='REPAIR_AGENT_EXIT', content='exit')
        self.add('descendant', 11, ref='file:new-descendant.json')
        result = self.assess()
        self.assertEqual(result['literal_version_reappearance'][0]['object_refs'], ['file:new-descendant.json'])
        self.assertIn('NOT_SEMANTIC_ADOPTION', result['literal_version_reappearance'][0]['classification'])
        self.assertEqual(result['semantic_descendants_status'], 'PENDING_INDEPENDENT_REVIEW')
        self.assertFalse(result['repair_success'])

    def test_mismatched_capture_is_rejected_even_with_a_valid_graph_hash(self):
        self.add('exit', 10, kind='REPAIR_AGENT_EXIT')
        self.sources['exit'] = b'changed'
        with self.assertRaisesRegex(BranchConstraintError, 'SOURCE_HASH_DRIFT'):
            self.assess()

    def test_old_observation_rewrite_cannot_be_hidden_by_rehashing(self):
        self.graph._observations['obs:0']['event_ref'] = 'changed'
        with self.assertRaisesRegex(BranchConstraintError, 'HISTORICAL_PREFIX_DRIFT'):
            self.assess(exit_id=None)


class RecoveryJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.binding = {'bundle_hash': 'bundle', 'contract_hash': 'contract', 'parent_checkpoint_hash': 'parent'}
        self.journal = RecoveryJournal(self.root, self.binding)

    def tearDown(self):
        self.temp.cleanup()

    def test_interruption_after_write_is_reconciled_without_replay(self):
        self.journal.intent('a1', 'file:x', 'before', 'after')
        recovered = RecoveryJournal(self.root, self.binding)
        result = recovered.reconcile(lambda ref: 'after')
        self.assertEqual(result['actions'][0]['decision'], 'EXPECTED_STATE_PRESENT_NO_REPLAY')
        self.assertFalse(result['automatic_replay_enabled'])
        with self.assertRaisesRegex(BranchConstraintError, 'ALREADY_ATTEMPTED'):
            recovered.intent('a1', 'file:x', 'before', 'after')

    def test_before_state_still_requires_a_revalidated_new_plan(self):
        self.journal.intent('a1', 'file:x', 'before', 'after')
        result = self.journal.reconcile(lambda ref: 'before')
        self.assertEqual(result['actions'][0]['decision'], 'BEFORE_STATE_PRESENT_REVALIDATE_BEFORE_NEW_PLAN')

    def test_wrong_output_retains_receipt_and_stops(self):
        self.journal.intent('a1', 'file:x', 'before', 'after')
        self.journal.complete('a1', 'wrong', {'actual': 'wrong'})
        result = self.journal.reconcile(lambda ref: 'wrong')
        self.assertEqual(result['actions'][0]['decision'], 'DIVERGED_OR_FAILED_STOP')
        self.assertEqual(result['actions'][0]['recorded_result']['status'], 'POSTCONDITION_FAILED')

    def test_chain_tampering_and_parent_drift_are_rejected(self):
        self.journal.append('START', {})
        with self.assertRaisesRegex(BranchConstraintError, 'PARENT_DRIFT'):
            RecoveryJournal(self.root, {**self.binding, 'parent_checkpoint_hash': 'other'})
        path = self.root / '000001.json'
        row = json.loads(path.read_text()); row['phase'] = 'fake'
        path.write_text(json.dumps(row))
        with self.assertRaisesRegex(BranchConstraintError, 'SEAL_MISMATCH'):
            RecoveryJournal(self.root, self.binding)

    def test_two_coordinators_cannot_silently_append_over_each_other(self):
        second = RecoveryJournal(self.root, self.binding)
        self.journal.append('START', {})
        with self.assertRaisesRegex(BranchConstraintError, 'STALE_COORDINATOR'):
            second.append('START', {})

    def test_same_object_intermediate_hash_is_not_treated_as_replay_permission(self):
        self.journal.intent('a1', 'file:x', 'before', 'middle')
        self.journal.complete('a1', 'middle', {})
        self.journal.intent('a2', 'file:x', 'middle', 'after')
        result = self.journal.reconcile(lambda ref: 'after')
        self.assertEqual(result['actions'][0]['decision'], 'INTERMEDIATE_VERSION_REQUIRES_RECEIPT_REVIEW')
        self.assertEqual(result['actions'][1]['decision'], 'EXPECTED_STATE_PRESENT_NO_REPLAY')


if __name__ == '__main__':
    unittest.main()
