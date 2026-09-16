import copy
import unittest

from arena.branch_comparison_v4 import build_branch_comparison_v4, verify_branch_comparison_v4


class BranchComparisonV4Tests(unittest.TestCase):
    def _measurement(self, condition_id, assignment, run_id, *, jump_count, descendants, depth):
        anchor_events = 7 if assignment == "CONTROL" else 3
        anchor_crossings = 4 if assignment == "CONTROL" else 1
        anchor_depth = 5 if assignment == "CONTROL" else 2
        return {
            "schema": "RB-SYSTEM-TRAJECTORY-MEASUREMENT-v4.0",
            "measurement_id": run_id + ":m",
            "trajectory_id": run_id,
            "parent_state_hash": "same-parent",
            "branch_start_state_hash": "control-start" if assignment == "CONTROL" else "intervention-start",
            "source_trace_hash": run_id + ":trace",
            "source_evidence_batch_hash": "same-evidence",
            "source_version": "R2-ARENA-TRACE-v0.3",
            "termination_status": "RUN_COMPLETE",
            "behavior_event_count": 12 if assignment == "CONTROL" else 10,
            "behavior_event_refs": [],
            "r2": {
                "jump_candidate_count": jump_count,
                "jump_candidate_refs": [],
                "first_jump_candidate_ref": None,
                "first_jump_turn": 3 if jump_count else None,
                "jump_type_counts": {"EPISTEMIC_STATUS_PROMOTION": jump_count},
            },
            "r3": {
                "descendant_event_count": descendants,
                "affected_agent_count": 2 if descendants else 0,
                "operational_boundary_crossing_count": 3 if descendants else 1,
                "first_jump_downstream_operational_crossing_count": 2 if descendants else 0,
                "first_jump_mechanical_penetration_depth_candidate": depth,
                "first_jump_operational_authority_classes_reached": ["I", "SETTLEMENT"] if descendants else [],
                "penetration_status": "NOT_ADJUDICATED",
            },
            "r4": {
                "retrospective_window_count": 1,
                "retrospective_window_refs": [],
                "semantic_r_status": "NOT_ADJUDICATED",
            },
            "r5_mid": {
                "branch_start_anchor_hash": run_id + ":anchor",
                "state_key": "inventory_view",
                "state_status": "fact" if assignment == "CONTROL" else "provisional",
                "anchor_visible_agent_turn_count": 2,
                "anchor_visible_agent_ids": ["ops_lead", "inventory"],
                "potential_downstream_event_count": anchor_events,
                "potential_downstream_relation_count": anchor_events - 1,
                "potential_downstream_affected_agent_count": 2 if anchor_events else 0,
                "potential_downstream_affected_agent_ids": ["ops_lead", "inventory"],
                "potential_downstream_operational_crossing_count": anchor_crossings,
                "potential_downstream_authority_classes_reached": ["I", "SETTLEMENT"] if anchor_crossings else [],
                "mechanical_anchor_reach_depth_candidate": anchor_depth,
                "semantic_reliance_status": "NOT_ADJUDICATED",
                "authority_penetration_status": "NOT_ADJUDICATED",
                "causal_effect_status": "NOT_ADJUDICATED",
            },
            "experimental_variables": [
                {
                    "variable_id": "EPISTEMIC_STATUS_DOWNGRADE",
                    "family": "CONTAINMENT",
                    "stage": "MID",
                    "assignment": assignment,
                    "level": "HIGH_CERTAINTY_STATUS" if assignment == "CONTROL" else "PROVISIONAL",
                }
            ],
            "semantic_status": "NOT_ADJUDICATED",
            "measurement_hash": run_id + ":measurement-hash",
            "pair_id": "PAIR-001",
            "replicate_index": 1,
            "condition_id": condition_id,
            "pair_order_pattern": "CONTROL_FIRST",
            "branch_plan_hash": "same-plan",
            "v4_research_binding_hash": "same-binding",
        }

    def test_structural_delta_is_paired_but_not_causal_or_semantic(self):
        control = self._measurement(
            "CONTROL_CONTINUATION",
            "CONTROL",
            "control-run",
            jump_count=2,
            descendants=8,
            depth=4,
        )
        intervention = self._measurement(
            "STATUS_DOWNGRADE_INTERVENTION",
            "MANIPULATION",
            "intervention-run",
            jump_count=1,
            descendants=3,
            depth=2,
        )
        comparison = build_branch_comparison_v4(control, intervention, comparison_id="PAIR-001:V4STRUCTURAL")
        self.assertTrue(verify_branch_comparison_v4(comparison))
        self.assertEqual(comparison["semantic_status"], "NOT_ADJUDICATED")
        self.assertEqual(comparison["causal_effect_status"], "NOT_ADJUDICATED")
        self.assertEqual(
            comparison["structural_deltas"]["r2"]["jump_candidate_count"]["delta_intervention_minus_control"],
            -1,
        )
        self.assertEqual(
            comparison["structural_deltas"]["r3"]["descendant_event_count"]["delta_intervention_minus_control"],
            -5,
        )
        self.assertEqual(
            comparison["structural_deltas"]["r3"]["first_jump_mechanical_penetration_depth_candidate"]["delta_intervention_minus_control"],
            -2,
        )
        self.assertEqual(
            comparison["structural_deltas"]["r5_mid_branch_anchor"]["potential_downstream_event_count"]["delta_intervention_minus_control"],
            -4,
        )
        self.assertEqual(
            comparison["structural_deltas"]["r5_mid_branch_anchor"]["potential_downstream_operational_crossing_count"]["delta_intervention_minus_control"],
            -3,
        )
        self.assertEqual(
            comparison["structural_deltas"]["r5_mid_branch_anchor"]["mechanical_anchor_reach_depth_candidate"]["delta_intervention_minus_control"],
            -3,
        )

    def test_parent_or_binding_mismatch_fails_closed(self):
        control = self._measurement("CONTROL_CONTINUATION", "CONTROL", "control-run", jump_count=1, descendants=1, depth=1)
        intervention = self._measurement("STATUS_DOWNGRADE_INTERVENTION", "MANIPULATION", "intervention-run", jump_count=1, descendants=1, depth=1)
        bad_parent = copy.deepcopy(intervention)
        bad_parent["parent_state_hash"] = "different-parent"
        with self.assertRaises(ValueError):
            build_branch_comparison_v4(control, bad_parent, comparison_id="bad-parent")
        bad_binding = copy.deepcopy(intervention)
        bad_binding["v4_research_binding_hash"] = "different-binding"
        with self.assertRaises(ValueError):
            build_branch_comparison_v4(control, bad_binding, comparison_id="bad-binding")

    def test_condition_role_cannot_be_swapped(self):
        control = self._measurement("CONTROL_CONTINUATION", "CONTROL", "control-run", jump_count=1, descendants=1, depth=1)
        intervention = self._measurement("STATUS_DOWNGRADE_INTERVENTION", "MANIPULATION", "intervention-run", jump_count=1, descendants=1, depth=1)
        with self.assertRaises(ValueError):
            build_branch_comparison_v4(intervention, control, comparison_id="swapped")


if __name__ == "__main__":
    unittest.main()
