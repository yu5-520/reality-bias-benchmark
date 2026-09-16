import copy
import json
import tempfile
import unittest
from pathlib import Path

from arena.core import stable_hash
from arena.first_paper_mechanism import (
    build_source_packet, grouped_analysis, aggregate_batches,
    append_reviews, resolve_reviews, sealed, continuation_observations,
)
from arena.tests import test_first_paper_analysis_contract as fixtures


class MechanismTests(unittest.TestCase):
    def packet(self):
        baseline = {'model_calls': [
            {'event_index_start': 0, 'event_index_end': 1, 'messages': [{'content': 'source task evidence'}]},
            {'event_index_start': 1, 'event_index_end': 2, 'messages': [{'content': 'FUTURE SECRET'}]},
        ]}
        bundle = {'plan': {'common_identity': {'source_trace_hash': stable_hash(baseline), 'state_key': 'x', 'parent_state_hash': 'parent'}},
                  'parent_snapshot': {'shared_state': {'x': 'claim'}, 'shared_state_metadata': {'x': {'event_index': 0, 'status': 'fact'}}}}
        return build_source_packet(bundle, baseline)

    def test_source_packet_excludes_future_and_records_missingness(self):
        p = self.packet()
        self.assertNotIn('FUTURE SECRET', json.dumps(p))
        self.assertFalse(p['input_missing'])
        self.assertFalse(p['branch_outcomes_included'])

    def test_parent_weighting_and_no_pseudoreplication_interval(self):
        fixture = fixtures.FirstPaperAnalysisContractTests()
        comparisons = [fixture._comparison(i, 5, 1) for i in range(1, 9)]
        row = fixture._comparison(9, 1, 5)
        row.pop('comparison_hash')
        row['common_parent_state_hash'] = 'second-parent'
        comparisons.append(sealed(row, 'comparison_hash'))
        summary = {'planned_pair_count': 9, 'pair_index': [{'pair_id': r['pair_id'], 'pair_status': 'PAIR_COMPARED_STRUCTURALLY_V4'} for r in comparisons]}
        result = grouped_analysis(comparisons, summary, [])
        self.assertEqual(result['parent_count'], 2)
        self.assertEqual(result['parent_balanced_mean_delta'], 0)
        self.assertIsNone(result['primary_interval'])
        self.assertTrue(all(p['auxiliary_status'] == 'MISSING_NOT_ZERO' for p in result['pairs']))

    def test_incomplete_pairs_preserved(self):
        result = grouped_analysis([], {'planned_pair_count': 1, 'pair_index': [{'pair_id': 'censored', 'pair_status': 'PAIR_NOT_COMPARABLE_NONCOMPLETE_TRACE'}]}, [])
        self.assertEqual(result['planned_pair_count'], 1)
        self.assertIsNone(result['parent_balanced_mean_delta'])
        with self.assertRaises(ValueError):
            grouped_analysis([], {'planned_pair_count': 2, 'pair_index': []}, [])

    def review(self, packet, reviewer, value):
        return sealed({'packet_hash': packet['packet_hash'], 'reviewer_id': reviewer,
                       'independent': True, 'outcome_blind': True, 'evidence_sufficiency': 'SUFFICIENT',
                       'evidence_refs': ['source:producing_call_input'], 'anchor_class': value}, 'review_hash')

    def test_disagreement_stays_unresolved_and_import_is_append_only(self):
        p = self.packet()
        a = self.review(p, 'a', 'SUPPORTED_CALIBRATED')
        b = self.review(p, 'b', 'UNSUPPORTED_OR_OVERSTATED')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'ledger.jsonl'
            append_reviews([p], [a], path)
            prefix = path.read_bytes()
            records = append_reviews([p], [b], path)
            self.assertTrue(path.read_bytes().startswith(prefix))
            self.assertEqual(resolve_reviews(records)[0]['resolutions']['anchor_class'], 'UNRESOLVED')
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                append_reviews([p], [a], path)
            self.assertEqual(before, path.read_bytes())

    def test_unblinded_source_review_rejected(self):
        p = self.packet()
        r = self.review(p, 'a', 'SUPPORTED_CALIBRATED')
        r.pop('review_hash'); r['outcome_blind'] = False; r = sealed(r, 'review_hash')
        with tempfile.TemporaryDirectory() as temp, self.assertRaises(ValueError):
            append_reviews([p], [r], Path(temp) / 'ledger')

    def test_structural_promotion_is_not_semantic_recertification(self):
        event = {'behavior_event_id': 'e', 'turn': 2, 'realization_status': 'REALIZED', 'boundary_id': 'STATE',
                 'structured_diff': {'source_action_type': 'write_state', 'action_key': 'x', 'action_status': 'fact'}}
        trace = {'run_id': 'r', 'run_status': 'RUN_COMPLETE', 'experimental_branch': {'branch_start_turn': 1}}
        anchor = {'pair_id': 'p', 'condition_id': 'CONTROL_CONTINUATION', 'branch_start_anchor': {'state_key': 'x', 'parent_state_hash': 'h'},
                  'potential_downstream_operational_crossing_ids': [], 'anchor_visible_agent_turn_count': 1}
        result = continuation_observations(trace, {'behavior_events': [event]}, {'operational_crossings': []}, anchor)
        self.assertEqual(result['high_certainty_rewrite_candidate_refs'], ['e'])
        self.assertEqual(result['semantic_recertification'], 'NOT_ADJUDICATED')
        self.assertEqual(result['task_completion'], 'NOT_ADJUDICATED')

    def test_duplicate_batches_cannot_inflate_sample_count(self):
        result = grouped_analysis([], {'planned_pair_count': 0, 'pair_index': []}, [])
        result.pop('analysis_hash'); result['source_trace_hash'] = 'source'; result = sealed(result, 'analysis_hash')
        with self.assertRaises(ValueError):
            aggregate_batches([result, result])


if __name__ == '__main__':
    unittest.main()
