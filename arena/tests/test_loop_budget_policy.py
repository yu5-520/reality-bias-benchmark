import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class LoopBudgetPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / 'arena/config/loop_budget_policy_v0.1.json').read_text(encoding='utf-8'))

    def test_policy_is_not_active(self):
        self.assertEqual(self.policy['status'], 'PLANNED_NOT_ACTIVE')
        self.assertEqual(self.policy['upper_bound_layer']['status'], 'PLANNED_NOT_ACTIVE')
        self.assertFalse(self.policy['upper_bound_layer']['auto_escalation'])

    def test_initial_k_is_strictly_two_then_four(self):
        upper = self.policy['upper_bound_layer']
        self.assertEqual(upper['initial_k_values'], [2, 4])
        self.assertEqual(upper['execution_order'], [2, 4])
        self.assertEqual(upper['max_k_authorized_in_initial_phase'], 4)
        self.assertEqual(upper['beyond_k4']['status'], 'NOT_AUTHORIZED')

    def test_k_counter_is_semantic_blind(self):
        upper = self.policy['upper_bound_layer']
        self.assertTrue(upper['loop_counter_must_be_semantic_blind'])
        self.assertEqual(upper['loop_counter_unit'], 'structural_feedback_round')
        validation = upper['counter_validation']
        self.assertEqual(validation['counter_version'], 'R4-STRUCTURAL-FEEDBACK-ROUND-v0.2')
        self.assertTrue(validation['semantic_blind'])
        self.assertTrue(validation['non_overlapping'])
        self.assertEqual(validation['status'], 'OFFLINE_VALIDATED_RUNTIME_NOT_ACTIVE')
        self.assertEqual(validation['runtime_enforcement_status'], 'NOT_IMPLEMENTED_NOT_ACTIVE')
        rules = self.policy['analysis_rules']
        self.assertTrue(rules['C_P_R_are_deferred_semantic_labels'])
        self.assertTrue(rules['K_is_not_a_bias_label'])
        self.assertTrue(rules['communication_cycle_is_not_authority_loop'])

    def test_frozen_counter_audit_is_registered_without_relabeling_base(self):
        validation = self.policy['upper_bound_layer']['counter_validation']
        self.assertEqual(validation['frozen_trace_audit_run'], 34965261787)
        self.assertEqual(validation['format005_rederive_run'], 34965319939)
        counts = validation['frozen_trace_round_counts']
        self.assertEqual(counts['v0.3.1_microbatch003_run0002_complete_18_turns'], 2)
        self.assertEqual(counts['v0.3.2_format005_censored_32_turns'], 3)
        self.assertIn('no subject behavior was changed', validation['note'].lower())

    def test_k4_requires_qualified_signal_not_raw_accumulation(self):
        gate = self.policy['upper_bound_layer']['k4_gate']
        self.assertTrue(gate['raw_cumulative_event_count_alone_is_insufficient'])
        self.assertGreaterEqual(len(gate['qualified_metrics']), 3)
        self.assertIn('new_bias_events_per_feedback_round', gate['qualified_metrics'])
        self.assertIn('reviewed_propagation_depth', gate['qualified_metrics'])

    def test_base_is_explicitly_required_first(self):
        base = self.policy['base_layer']
        self.assertEqual(base['name'], 'BASE_FIXED_WINDOW')
        self.assertEqual(base['current_turn_horizon'], 32)
        self.assertIn('censor_aware_objective_stats_available', base['required_before_upper_bound'])
        self.assertIn('review_packets_bind_same_evidence_batch_hash', base['required_before_upper_bound'])


if __name__ == '__main__':
    unittest.main()
