import copy
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from stage2.r7_checkpoint_v1.common import digest
from stage2.monitor_enhancement.evidence_graph import EvidenceGraph
from stage2.monitor_enhancement.snapshot_append import AppendOnlyEvidenceGraph
from stage2.route_repair.branch_fields import BranchConstraintError, seal
from stage2.route_repair.system_contract import assess_continuation, bound_source_text
from stage2.route_repair.independent_review import RepairReviewContext, IndependentReviewerBinding, CHECKS

ROOT = Path(__file__).resolve().parents[3]


class IndependentReviewTests(unittest.TestCase):
    def setUp(self):
        self.sources = {}
        before_builder = EvidenceGraph()
        self.add(before_builder, 'old-source', 'file:source.json', 1, 'NATIVE_READ', 'uncertain source')
        self.add(before_builder, 'old-plan', 'file:plan.json', 2, 'NATIVE_WRITE', 'required inherited gate')
        self.before = before_builder.snapshot()
        self.graph = AppendOnlyEvidenceGraph.from_snapshot(self.before)
        self.add(self.graph, 'exit', 'state:repair', 3, 'REPAIR_AGENT_EXIT', 'repair agent exited')
        self.add(self.graph, 'consumer', 'file:new-plan.json', 4, 'NATIVE_CONTINUATION', 'reconstructed from independent evidence')
        self.add(self.graph, 'close', 'state:subject', 5, 'NATIVE_CLOSURE', 'subject closed with no pending work')
        self.contract = seal({'source_graph_hash': self.before['graph_hash'], 'parent_checkpoint_hash': 'parent',
                              'original_task': {'request': 'broad original task'},
                              'lineage_obligations': [{'semantic_id': 'target', 'watch_refs': ['file:source.json', 'file:plan.json'],
                                                      'checks': list(CHECKS)}]}, 'contract_hash')
        self.rules = json.loads((ROOT / 'configs/r8_dynamic_semantic_audit_contract_v0.4.json').read_text())
        self.lineage = json.loads((ROOT / 'configs/stage2_r6_grade_semantic_audit_rules_v1.json').read_text())

    def add(self, graph, identity, ref, seq, kind, text):
        raw = json.dumps({'content': text}).encode(); self.sources[identity] = raw
        graph.add_observation({'schema': 'RB-STAGE2-ENHANCED-OBSERVATION-v1', 'observation_id': identity,
            'event_ref': identity, 'evidence_ref': 'raw:' + identity, 'object_refs': [ref],
            'clock_id': 'native', 'native_sequence': seq, 'event_kind': kind,
            'source_locator': {'member': identity + '.json', 'member_sha256': digest(raw), 'json_pointer': '/content', 'line': None}})

    def context(self, *, exit_id='exit'):
        after = self.graph.snapshot()
        rows = {r['observation_id']: r for r in self.before['observations']}
        def old_source(identity):
            row = rows[identity]
            return {'observation': row, 'source_text': bound_source_text(row, self.sources[identity])}
        native = SimpleNamespace(graph=self.before, observation_source=old_source)
        assessment = assess_continuation(self.contract, self.before, after,
            source_reader=lambda row: self.sources[row['observation_id']], exit_observation_id=exit_id)
        return RepairReviewContext(native, self.contract, self.before, after, assessment,
            branch_source_reader=lambda row: self.sources[row['observation_id']],
            semantic_rules=self.rules, lineage_rules=self.lineage, repair_actor_id='repair-role')

    def report(self, context):
        witnesses = []
        for identity in ['old-plan', 'consumer', 'close']:
            row = context.read(identity)
            witnesses.append(context.witness(row['read_id'], 0, len(row['text']))['witness_id'])
        return {'schema': 'stage2-post-repair-semantic-review-v1', 'reviewer_id': 'independent-role',
                'criteria_hash': context.catalog()['criteria_hash'], 'closing_observation_id': 'close',
                'closing_witness_id': witnesses[-1], 'visibility_status': 'FULL_RELEVANT_LINEAGE_RECOVERABLE',
                'assessments': [{'semantic_id': 'target', 'check': check, 'status': 'SUPPORTED',
                    'meaning_before': 'required inherited gate', 'meaning_after': 'new evidence reconstruction',
                    'authority_effect': 'fixture reviewer claims old gate no longer constrains the consumer',
                    'independent_support': 'fixture reviewer cites separate reconstruction',
                    'inherited_support': 'fixture reviewer inspects old gate after re-entry',
                    'limitation': 'synthetic reviewer-contract test, not a semantic experiment',
                    'not_established': [], 'witness_ids': witnesses[:2],
                    'path': [{'from_witness_id': witnesses[0], 'to_witness_id': witnesses[1],
                              'relation_type': 'INDEPENDENT_REANCHORING', 'semantic_change': 'fixture review statement'}]}
                    for check in CHECKS]}

    def binding(self, context, transform=None, reviewer_id='independent-role'):
        def review(ctx):
            report = self.report(ctx)
            if transform: transform(report)
            return report
        return IndependentReviewerBinding(reviewer_id, context.catalog()['criteria_hash'], review)

    def test_no_native_continuation_does_not_invoke_a_reviewer(self):
        context = self.context(exit_id=None)
        calls = []
        binding = IndependentReviewerBinding('independent-role', context.catalog()['criteria_hash'], lambda ctx: calls.append(ctx))
        with self.assertRaisesRegex(BranchConstraintError, 'NATIVE_CONTINUATION_REQUIRED'): context.evaluate(binding)
        self.assertEqual(calls, [])
        self.assertFalse(context.pending_receipt()['repair_success'])

    def test_same_repair_actor_cannot_bind_its_own_review(self):
        context = self.context()
        with self.assertRaisesRegex(BranchConstraintError, 'CANNOT_SELF_REVIEW'):
            context.evaluate(self.binding(context, reviewer_id='repair-role'))

    def test_full_read_only_catalog_keeps_criteria_and_omits_plan_labels(self):
        context = self.context(); catalog = context.catalog()
        self.assertEqual(len(catalog['all_observation_ids']), 5)
        self.assertFalse(catalog['source_wording_continuity_required'])
        self.assertEqual(catalog['criteria']['C'], self.rules['C'])
        self.assertEqual(catalog['criteria']['R'], self.rules['R'])
        self.assertEqual(catalog['write_capabilities'], [])
        self.assertFalse(catalog['repair_plan_or_completion_verdict_included'])

    def test_complete_bound_report_is_only_review_support_not_validator_truth(self):
        context = self.context(); result = context.evaluate(self.binding(context))
        self.assertTrue(result['repair_success_supported_by_bound_reviewer'])
        self.assertFalse(result['semantic_truth_established_by_validator'])
        self.assertEqual(result['native_write_operations'], 0)
        self.assertEqual(len(result['report']['assessments']), 6)

    def test_missing_old_cp_or_reentry_check_is_rejected(self):
        context = self.context()
        with self.assertRaisesRegex(BranchConstraintError, 'COVERAGE_MISMATCH'):
            context.evaluate(self.binding(context, lambda report: report['assessments'].pop(2)))

    def test_new_state_alone_cannot_replace_the_before_after_path(self):
        context = self.context()
        def remove_old(report): report['assessments'][0]['witness_ids'] = [report['assessments'][0]['witness_ids'][1]]
        with self.assertRaisesRegex(BranchConstraintError, 'BEFORE_AFTER_WITNESSES_REQUIRED'):
            context.evaluate(self.binding(context, remove_old))

    def test_fabricated_or_unread_citations_are_rejected(self):
        context = self.context()
        with self.assertRaisesRegex(BranchConstraintError, 'SOURCE_NOT_READ'): context.witness('fake', 0, 1)
        def forged(report): report['assessments'][0]['witness_ids'] = ['fake']
        with self.assertRaisesRegex(BranchConstraintError, 'WITNESS_NOT_READ'):
            context.evaluate(self.binding(context, forged))

    def test_visibility_or_read_alone_cannot_support_repair(self):
        for relation in ['MERE_VISIBILITY', 'READ', 'NOT_ESTABLISHED']:
            context = self.context()
            def change(report): report['assessments'][0]['path'][0]['relation_type'] = relation
            with self.assertRaisesRegex(BranchConstraintError, 'CANNOT_SUPPORT_REPAIR'):
                context.evaluate(self.binding(context, change))

    def test_partial_semantic_capture_or_unknown_check_prevents_overall_support(self):
        context = self.context()
        def partial(report): report['visibility_status'] = 'FULL_ROUTE_PARTIAL_SEMANTIC_CAPTURE'
        self.assertFalse(context.evaluate(self.binding(context, partial))['repair_success_supported_by_bound_reviewer'])
        context = self.context()
        def uncertain(report):
            report['assessments'][3]['status'] = 'UNCERTAIN'
            report['assessments'][3]['not_established'] = ['historical adoption unresolved']
        self.assertFalse(context.evaluate(self.binding(context, uncertain))['repair_success_supported_by_bound_reviewer'])

    def test_censored_active_chain_cannot_be_called_repaired(self):
        self.graph._observations['close']['event_kind'] = 'NATIVE_CENSOR'
        context = self.context()
        result = context.evaluate(self.binding(context))
        self.assertFalse(result['repair_success_supported_by_bound_reviewer'])
        self.assertEqual(result['window_boundary'], 'NATIVE_CENSOR')

    def test_target_cannot_be_marked_not_applicable_to_claim_success(self):
        context = self.context()
        def noop(report): report['assessments'][0]['status'] = 'NOT_APPLICABLE'
        self.assertFalse(context.evaluate(self.binding(context, noop))['repair_success_supported_by_bound_reviewer'])

    def test_closure_needs_an_actual_read_witness(self):
        context = self.context()
        def fake_closure(report): report['closing_witness_id'] = 'not-read'
        with self.assertRaisesRegex(BranchConstraintError, 'CLOSURE_SOURCE_NOT_READ'):
            context.evaluate(self.binding(context, fake_closure))


if __name__ == '__main__': unittest.main()
