from __future__ import annotations

import copy
import unittest

from arena.core import stable_hash
from arena.r5r6_specificity import (
    S0,
    S1,
    S2,
    SpecificityOneShotRuntimeViewTransform,
    build_field_selection_record,
    build_specificity_plan,
    rotated_condition_order,
    verify_field_selection_record,
    verify_specificity_plan,
)
from arena.r5r6_specificity_preflight import build_preflight


class R5R6SpecificityTests(unittest.TestCase):
    def _selection(self):
        features = {
            "pre_intervention_status_class": "fact",
            "runtime_visibility_boundary": "POST_J0_SHARED_STATE",
            "temporal_distance_from_common_parent": 0,
            "state_or_interface_family": "operational_assessment",
            "actor_or_role_accessibility": "ops_lead_visible",
            "downstream_opportunity_for_inheritance": "available_next_turn",
            "source_evidence_completeness": "complete",
        }
        candidates = [
            {
                "state_key": "matched_b",
                "pre_status": "fact",
                "source_refs": ["E20"],
                "matching_features": {**features, "actor_or_role_accessibility": "ads_visible"},
            },
            {
                "state_key": "matched_a",
                "pre_status": "fact",
                "source_refs": ["E21"],
                "matching_features": copy.deepcopy(features),
            },
            {
                "state_key": "j0_field",
                "pre_status": "fact",
                "source_refs": ["E32"],
                "matching_features": copy.deepcopy(features),
            },
            {
                "state_key": "provisional_field",
                "pre_status": "provisional",
                "source_refs": ["E22"],
                "matching_features": copy.deepcopy(features),
            },
        ]
        return build_field_selection_record(
            source_trace_hash="trace",
            source_evidence_hash="evidence",
            common_parent_state_hash="parent",
            j0_candidate_id="J0-CANDIDATE",
            j0_event_ref="E32",
            j0_state_key="j0_field",
            j0_pre_status="fact",
            j0_matching_features=features,
            candidates=candidates,
        )

    def test_selection_is_outcome_blind_and_excludes_j0(self):
        record = self._selection()
        self.assertTrue(verify_field_selection_record(record))
        self.assertEqual(record["selected_s1_state_key"], "matched_a")
        self.assertNotEqual(record["selected_s1_state_key"], record["selected_j0_state_key"])
        self.assertTrue(record["selector_outcome_blind_attestation"])
        self.assertFalse(record["future_s_arm_outputs_available_to_selector"])
        reasons = {x["state_key"]: x.get("exclusion_reason") for x in record["excluded_pool"]}
        self.assertEqual(reasons["j0_field"], "SELECTED_J0_TARGET_EXCLUDED_FROM_S1_POOL")
        self.assertEqual(reasons["provisional_field"], "PRE_STATUS_NOT_COMPATIBLE_WITH_J0")

    def test_plan_keeps_s_and_c_namespaces_separate(self):
        selection = self._selection()
        bundle = build_specificity_plan(selection_record=selection, j0_source_refs=["E32"], replicates=3)
        self.assertTrue(verify_specificity_plan(bundle))
        plan = bundle["plan"]
        self.assertEqual(plan["conditions"], [S0, S1, S2])
        self.assertEqual(plan["namespace_guard"]["specificity_namespace"], "S")
        self.assertEqual(plan["namespace_guard"]["r7_namespace"], "C")
        self.assertTrue(plan["namespace_guard"]["aliasing_forbidden"])
        self.assertEqual(plan["contrasts"]["primary_target_specificity"], "S2_MINUS_S1")
        self.assertEqual(plan["authorization_status"], "NOT_AUTHORIZED")
        self.assertFalse(plan["paid_evaluator_authorized"])

    def test_s1_s2_use_same_mechanics_but_different_targets(self):
        selection = self._selection()
        bundle = build_specificity_plan(selection_record=selection, j0_source_refs=["E32"])
        s1 = bundle["s1_envelope"]
        s2 = bundle["s2_envelope"]
        self.assertNotEqual(s1["state_key"], s2["state_key"])
        for key in (
            "mechanical_primitive",
            "from_status",
            "to_status",
            "delivery_policy",
            "direct_exposure_limit",
            "persistent_state_mutation",
            "experiment_origin_reinjection_forbidden",
        ):
            self.assertEqual(s1[key], s2[key])
        self.assertNotEqual(s1["research_identity"], s2["research_identity"])

    def test_one_shot_transform_never_mutates_source_and_never_reinjects(self):
        selection = self._selection()
        bundle = build_specificity_plan(selection_record=selection, j0_source_refs=["E32"])
        parent = {
            "shared_state_metadata": {
                "matched_a": {"status": "fact"},
                "j0_field": {"status": "fact"},
            }
        }
        source_hash = stable_hash(parent)
        transform = SpecificityOneShotRuntimeViewTransform(bundle["s2_envelope"])
        view1, delivery1 = transform(actor="ops_lead", turn=9, runtime_view=parent)
        view2, delivery2 = transform(actor="ops_lead", turn=10, runtime_view=parent)
        self.assertIsNotNone(delivery1)
        self.assertIsNone(delivery2)
        self.assertEqual(view1["shared_state_metadata"]["j0_field"]["status"], "unconfirmed")
        self.assertEqual(view2["shared_state_metadata"]["j0_field"]["status"], "fact")
        self.assertEqual(stable_hash(parent), source_hash)
        self.assertEqual(transform.delivered_count, 1)
        self.assertTrue(transform.verify_finished())

    def test_rotated_execution_order_balances_first_position(self):
        orders = [rotated_condition_order(i) for i in (1, 2, 3)]
        self.assertEqual(orders[0], (S0, S1, S2))
        self.assertEqual(orders[1], (S1, S2, S0))
        self.assertEqual(orders[2], (S2, S0, S1))
        self.assertEqual({x[0] for x in orders}, {S0, S1, S2})

    def test_offline_preflight(self):
        bundle = build_preflight()
        summary = bundle["summary"]
        self.assertEqual(summary["scientific_status"], "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE")
        self.assertTrue(summary["source_parent_immutable"])
        self.assertTrue(summary["outcome_blind_selection"])
        self.assertTrue(summary["s1_s2_targets_distinct"])
        self.assertTrue(summary["s1_s2_mechanical_primitive_equal"])
        self.assertEqual(summary["s1_direct_exposures"], 1)
        self.assertEqual(summary["s2_direct_exposures"], 1)
        self.assertEqual(summary["s1_reinjections"], 0)
        self.assertEqual(summary["s2_reinjections"], 0)
        self.assertFalse(summary["paid_api_called"])
        self.assertEqual(summary["semantic_cpr_status"], "NOT_ADJUDICATED")


if __name__ == "__main__":
    unittest.main()
