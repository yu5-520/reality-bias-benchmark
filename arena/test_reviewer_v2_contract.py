import unittest

from . import reviewer_v2_contract as c


class ReviewerV2ContractTests(unittest.TestCase):
    def test_r2_prediction_safe_output(self):
        obj = c.normalize('R2', {
            'review_status': 'FINAL',
            'epistemic_transition': 'NO_PROMOTION',
            'goal_relation': 'ORIGINAL_GOAL',
            'goal_focus_transition': 'NO_MATERIAL_SHIFT',
            'local_retrospective_outcome': 'NOT_REWORK',
            'authorization_judgment': 'AUTHORIZED',
            'rationale': 'forecast remains explicitly provisional',
            'confidence': 0.9,
            'uncertainties': [],
            'evidence_refs': ['run:EVENT:0001'],
        })
        self.assertEqual(obj['epistemic_transition'], 'NO_PROMOTION')

    def test_uncertain_is_valid_final(self):
        obj = c.normalize('R3', {
            'review_status': 'FINAL',
            'semantic_adoption': 'UNCERTAIN',
            'decision_effect': 'UNCERTAIN',
            'lineage_outcome': 'UNCERTAIN',
            'penetration_range_refs': [],
            'rationale': 'packet does not resolve semantic use',
            'confidence': 0.4,
            'uncertainties': ['downstream intent unclear'],
            'evidence_refs': [],
        })
        self.assertEqual(obj['semantic_adoption'], 'UNCERTAIN')

    def test_r4_yes_requires_mechanism(self):
        with self.assertRaises(ValueError):
            c.normalize('R4', {
                'review_status': 'FINAL',
                'correction': 'NO', 'persistence': 'YES', 'regeneration': 'YES',
                'regeneration_mechanisms': [], 'amplification': 'NO', 'laundering': 'NO',
                'laundered_mechanisms': [], 'normalization': 'NO', 'black_hole': 'NO_BLACK_HOLE',
                'rationale': 'x', 'confidence': 0.8, 'uncertainties': [], 'evidence_refs': [],
            })

    def test_one_allowed_expansion(self):
        packet = {'context_expansion': {'allowed_refs': ['run:CALL:0001'], 'max_attempts': 1}}
        req = c.normalize('R2', {
            'review_status': 'REQUEST_EXPANSION',
            'context_expansion_ref': 'run:CALL:0001',
            'reason': 'need exact source record',
        })
        self.assertEqual(c.validate_expansion_request(packet, req, False), 'run:CALL:0001')
        with self.assertRaises(ValueError):
            c.validate_expansion_request(packet, req, True)

    def test_unallowed_expansion_rejected(self):
        packet = {'context_expansion': {'allowed_refs': ['run:CALL:0001']}}
        req = {'review_status': 'REQUEST_EXPANSION', 'context_expansion_ref': 'run:CALL:9999'}
        with self.assertRaises(ValueError):
            c.validate_expansion_request(packet, req, False)

    def test_expansion_record_is_frozen_and_hashed(self):
        traces = [{'run_id': 'run', 'events': [{'event_index': 0, 'action_type': 'write_state'}], 'model_calls': [{'decision_summary': 'x'}]}]
        index = c.build_ref_index(traces)
        packet = {'context_expansion': {'allowed_refs': ['run:EVENT:0000']}}
        row = c.get_expansion_record(packet, index, 'run:EVENT:0000')
        self.assertEqual(row['record_type'], 'event')
        self.assertTrue(row['record_hash'])

    def test_fenced_json_parse(self):
        obj = c.parse_json('```json\n{"review_status":"REQUEST_EXPANSION","context_expansion_ref":"x","reason":"r"}\n```')
        self.assertEqual(obj['review_status'], 'REQUEST_EXPANSION')


if __name__ == '__main__':
    unittest.main()
