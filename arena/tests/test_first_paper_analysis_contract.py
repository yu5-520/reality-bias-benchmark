import copy
import unittest

from arena.branch_comparison_v4 import build_branch_comparison_v4
from arena.first_paper_analysis_contract import (
    analyze_structural_comparisons,
    load_analysis_contract,
    resolve_semantic_endpoint,
    validate_analysis_contract,
)


class FirstPaperAnalysisContractTests(unittest.TestCase):
    def _measurement(self, pair_id, condition_id, assignment, run_id, operational_crossings, order="CONTROL_FIRST"):
        anchor_events = operational_crossings + 3
        return {
            "schema": "RB-SYSTEM-TRAJECTORY-MEASUREMENT-v4.0",
            "measurement_id": run_id + ":m",
            "trajectory_id": run_id,
            "parent_state_hash": "same-parent",
            "branch_start_state_hash": run_id + ":start",
            "source_trace_hash": run_id + ":trace",
            "source_evidence_batch_hash": "same-evidence",
            "source_version": "R2-ARENA-TRACE-v0.3",
            "termination_status": "RUN_COMPLETE",
            "behavior_event_count": anchor_events + 4,
            "behavior_event_refs": [],
            "r2": {
                "jump_candidate_count": 1,
                "jump_candidate_refs": [],
                "first_jump_candidate_ref": None,
                "first_jump_turn": 3,
                "jump_type_counts": {"EPISTEMIC_STATUS_PROMOTION": 1},
            },
            "r3": {
                "descendant_event_count": anchor_events,
                "affected_agent_count": 2,
                "operational_boundary_crossing_count": operational_crossings,
                "first_jump_downstream_operational_crossing_count": operational_crossings,
                "first_jump_mechanical_penetration_depth_candidate": operational_crossings,
                "first_jump_operational_authority_classes_reached": ["I"] if operational_crossings else [],
                "penetration_status": "NOT_ADJUDICATED",
            },
            "r4": {
                "retrospective_window_count": 0,
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
                "potential_downstream_relation_count": max(0, anchor_events - 1),
                "potential_downstream_affected_agent_count": 2,
                "potential_downstream_affected_agent_ids": ["ops_lead", "inventory"],
                "potential_downstream_operational_crossing_count": operational_crossings,
                "potential_downstream_authority_classes_reached": ["I"] if operational_crossings else [],
                "mechanical_anchor_reach_depth_candidate": operational_crossings,
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
            "pair_id": pair_id,
            "replicate_index": int(pair_id.split("-")[-1]),
            "condition_id": condition_id,
            "pair_order_pattern": order,
            "branch_plan_hash": "same-plan",
            "v4_research_binding_hash": "same-binding",
        }

    def _comparison(self, index, control_crossings, intervention_crossings):
        pair_id = f"PAIR-{index}"
        order = "CONTROL_FIRST" if index % 2 else "INTERVENTION_FIRST"
        control = self._measurement(
            pair_id,
            "CONTROL_CONTINUATION",
            "CONTROL",
            pair_id + ":control",
            control_crossings,
            order,
        )
        intervention = self._measurement(
            pair_id,
            "STATUS_DOWNGRADE_INTERVENTION",
            "MANIPULATION",
            pair_id + ":intervention",
            intervention_crossings,
            order,
        )
        return build_branch_comparison_v4(control, intervention, comparison_id=pair_id + ":V4STRUCTURAL")

    def test_contract_is_frozen_before_new_subject_evidence(self):
        contract = load_analysis_contract()
        self.assertTrue(validate_analysis_contract(contract))
        self.assertEqual(contract["status"], "FROZEN_BEFORE_NEW_V4_SUBJECT_EVIDENCE")
        self.assertEqual(
            contract["outcomes"]["primary_confirmatory_structural"]["outcome_id"],
            "R5MID_ANCHOR_DOWNSTREAM_OPERATIONAL_CROSSING_COUNT",
        )
        self.assertEqual(contract["batch_aggregation"]["primary_structural"]["primary_p_value"], "NONE")

    def test_primary_estimator_uses_pair_delta_and_bootstrap_rule(self):
        comparisons = [self._comparison(i, 5, 3) for i in range(1, 9)]
        summary = {
            "planned_pair_count": 10,
            "pair_index": [
                *[
                    {"pair_id": f"PAIR-{i}", "pair_status": "PAIR_COMPARED_STRUCTURALLY_V4"}
                    for i in range(1, 9)
                ],
                {"pair_id": "PAIR-9", "pair_status": "PAIR_NOT_COMPARABLE_NONCOMPLETE_TRACE"},
                {"pair_id": "PAIR-10", "pair_status": "PAIR_NOT_COMPARABLE_NONCOMPLETE_TRACE"},
            ],
        }
        analysis = analyze_structural_comparisons(comparisons, derivation_summary=summary)
        self.assertEqual(analysis["complete_pair_count"], 8)
        self.assertEqual(analysis["censored_pair_count"], 2)
        self.assertEqual(analysis["mean_pair_delta"], -2.0)
        self.assertEqual(analysis["median_pair_delta"], -2.0)
        self.assertEqual(analysis["negative_delta_count"], 8)
        self.assertEqual(analysis["primary_interval_status"], "ESTIMATED")
        self.assertIsNone(analysis["primary_p_value"])
        self.assertEqual(analysis["semantic_status"], "NOT_INCLUDED_IN_STRUCTURAL_ANALYSIS")

    def test_below_minimum_pairs_does_not_invent_interval(self):
        comparisons = [self._comparison(i, 4, 3) for i in range(1, 4)]
        analysis = analyze_structural_comparisons(comparisons)
        self.assertEqual(analysis["primary_interval_status"], "NOT_ESTIMATED_MINIMUM_PAIR_COUNT_NOT_MET")
        self.assertIsNone(analysis["primary_interval"])

    def test_semantic_resolution_preserves_disagreement_until_append_only_adjudication(self):
        packet_id = "packet-1"
        independent_a = {
            "packet_id": packet_id,
            "review_record_id": "review-a",
            "record_kind": "independent",
            "reviewer": {"id": "reviewer-a"},
            "judgments": {"authority_penetration": "YES", "evidence_sufficiency": "SUFFICIENT"},
            "parent_review_ids": [],
        }
        independent_b = {
            "packet_id": packet_id,
            "review_record_id": "review-b",
            "record_kind": "independent",
            "reviewer": {"id": "reviewer-b"},
            "judgments": {"authority_penetration": "NO", "evidence_sufficiency": "SUFFICIENT"},
            "parent_review_ids": [],
        }
        unresolved = resolve_semantic_endpoint([independent_a, independent_b])
        self.assertEqual(unresolved["status"], "DISAGREEMENT_UNRESOLVED")
        self.assertIsNone(unresolved["value"])

        adjudication = {
            "packet_id": packet_id,
            "review_record_id": "review-adjudication",
            "record_kind": "adjudication",
            "reviewer": {"id": "reviewer-c"},
            "judgments": {"authority_penetration": "NO", "evidence_sufficiency": "SUFFICIENT"},
            "parent_review_ids": ["review-a", "review-b"],
        }
        resolved = resolve_semantic_endpoint([independent_a, independent_b, adjudication])
        self.assertEqual(resolved["status"], "RESOLVED_APPEND_ONLY_ADJUDICATION")
        self.assertEqual(resolved["value"], "NO")

    def test_invalid_comparison_cannot_enter_primary_estimate(self):
        comparison = self._comparison(1, 5, 3)
        bad = copy.deepcopy(comparison)
        bad["experimental_variable_id"] = "OTHER_VARIABLE"
        bad.pop("comparison_hash", None)
        from arena.system_behavior import content_hash
        bad["comparison_hash"] = content_hash(bad)
        with self.assertRaises(ValueError):
            analyze_structural_comparisons([bad])


if __name__ == "__main__":
    unittest.main()
