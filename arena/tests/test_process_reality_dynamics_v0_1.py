import unittest

from arena.process_reality_dynamics_v0_1 import compare_process_reality


class ProcessRealityComparisonTest(unittest.TestCase):
    def test_path_comparison_is_nondirectional(self):
        control = {
            "trajectory_id": "A",
            "path_topology": {"canonical_edge_signatures": ["a", "b"], "ordered_event_signatures": ["x", "y", "z"]},
            "r2_jump_recurrence": {"descendant_rejump_count": 1},
            "r3_inherited_inertia": {"root_reach_depth": 3, "affected_agent_count": 2},
        }
        intervention = {
            "trajectory_id": "B",
            "path_topology": {"canonical_edge_signatures": ["a", "c"], "ordered_event_signatures": ["x", "q", "z"]},
            "r2_jump_recurrence": {"descendant_rejump_count": 2},
            "r3_inherited_inertia": {"root_reach_depth": 4, "affected_agent_count": 3},
        }
        row = compare_process_reality(control, intervention, comparison_id="PAIR")
        self.assertEqual(1, row["shared_path_prefix_event_count"])
        self.assertEqual(["b"], row["control_only_edge_signatures"])
        self.assertEqual(["c"], row["intervention_only_edge_signatures"])
        self.assertFalse(row["terminal_outcome_comparison_is_primary"])
        self.assertEqual("NOT_ADJUDICATED", row["semantic_causal_effect_status"])


if __name__ == "__main__":
    unittest.main()
