import copy
import unittest
from stage2.route_repair.branch_fields import BranchConstraintError
from stage2.route_repair.tests import test_independent_review as fixtures
from scripts.review_stage2_connected_repair import submit, REVIEWER_ID


class ReviewSubmissionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.IndependentReviewTests(); self.fixture.setUp()
        inspected = self.fixture.context(); report = self.fixture.report(inspected)
        report['reviewer_id'] = REVIEWER_ID
        names = {'review_read': 'read', 'review_witness': 'witness', 'review_catalog': 'catalog'}
        self.submission = {'queries': [{'name': names[q['operation']], 'arguments': q['request']}
            for q in inspected._queries], 'report': report}

    def test_replayed_independent_source_queries_validate_without_writes(self):
        result = submit(self.fixture.context(), self.submission)
        self.assertEqual(result['native_write_operations'], 0)
        self.assertFalse(result['semantic_truth_established_by_validator'])
        self.assertEqual(len(result['source_witnesses']), 3)

    def test_report_witness_ids_are_not_accepted_without_actual_source_queries(self):
        forged = copy.deepcopy(self.submission); forged['queries'] = []
        with self.assertRaisesRegex(BranchConstraintError, 'WITNESS_NOT_READ'):
            submit(self.fixture.context(), forged)

    def test_review_write_tool_and_actor_selected_identity_are_rejected(self):
        forged = copy.deepcopy(self.submission); forged['queries'][0]['name'] = 'write_file'
        with self.assertRaisesRegex(BranchConstraintError, 'READ_ONLY_INDEPENDENT_REVIEW_TOOL'):
            submit(self.fixture.context(), forged)
        forged = copy.deepcopy(self.submission); forged['report']['reviewer_id'] = 'repair-role'
        with self.assertRaisesRegex(BranchConstraintError, 'HOST_BINDING_DRIFT'):
            submit(self.fixture.context(), forged)

    def test_missing_actual_exit_blocks_before_reviewer_reads(self):
        context = self.fixture.context(exit_id=None)
        with self.assertRaisesRegex(BranchConstraintError, 'NATIVE_CONTINUATION_REQUIRED'):
            submit(context, self.submission)
        self.assertEqual(context._reads, {})


if __name__ == '__main__': unittest.main()
