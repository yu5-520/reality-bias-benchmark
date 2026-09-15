import unittest

from . import evaluate_reviewer_v2_deepseek as e


class ReviewerV2DeepSeekAdapterTests(unittest.TestCase):
    def test_cost_uses_cache_breakdown(self):
        cfg = {'pricing_snapshot_usd_per_million_tokens': {'peak': {'input_cache_hit': 1, 'input_cache_miss': 2, 'output': 3}}}
        usage = {'prompt_tokens': 15, 'prompt_cache_hit_tokens': 10, 'prompt_cache_miss_tokens': 5, 'completion_tokens': 2}
        self.assertAlmostEqual(e.cost_usd(usage, cfg, 'peak'), (10 + 10 + 6) / 1_000_000)

    def test_cost_falls_back_to_cache_miss(self):
        cfg = {'pricing_snapshot_usd_per_million_tokens': {'peak': {'input_cache_hit': 1, 'input_cache_miss': 2, 'output': 3}}}
        usage = {'prompt_tokens': 10, 'completion_tokens': 2}
        self.assertAlmostEqual(e.cost_usd(usage, cfg, 'peak'), (20 + 6) / 1_000_000)

    def test_target_refs(self):
        self.assertEqual(e.target_ref('R2', {'target_candidate': {'event_ref': 'r:EVENT:0001'}}), 'r:EVENT:0001')
        self.assertEqual(e.target_ref('R4', {'run_id': 'r', 'structural_window': {'structural_round_id': 'round-1'}}), 'round-1')

    def test_r2_record_preserves_uncertainty(self):
        packet = {'evidence_batch_hash': 'b', 'packet_id': 'p', 'packet_hash': 'h', 'target_candidate': {'event_ref': 'r:EVENT:0001', 'effect_scope': 'REALIZED_STRUCTURAL_EFFECT'}}
        final = {
            'epistemic_transition': 'UNCERTAIN', 'goal_relation': 'ORIGINAL_GOAL',
            'goal_focus_transition': 'NO_MATERIAL_SHIFT', 'local_retrospective_outcome': 'NOT_REWORK',
            'authorization_judgment': 'UNCERTAIN', 'rationale': 'insufficient evidence',
            'confidence': 0.4, 'uncertainties': ['source unresolved'], 'evidence_refs': [],
        }
        row = e.make_record('R2', packet, final, 'rid', 'mh', 'ph', {'model': 'm', 'id': 'resp'}, {}, 1, [], None, 'AUTH-REF')
        self.assertEqual(row['epistemic_transition'], 'UNCERTAIN')
        self.assertEqual(row['authorization_judgment'], 'UNCERTAIN')
        self.assertFalse(row['context_expansion_used'])
        self.assertEqual(row['authorization_ref'], 'AUTH-REF')


if __name__ == '__main__':
    unittest.main()
