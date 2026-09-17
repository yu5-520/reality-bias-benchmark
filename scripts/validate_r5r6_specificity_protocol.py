#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(rel: str):
    with (ROOT / rel).open("r", encoding="utf-8") as f:
        return json.load(f)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def main() -> None:
    mechanism = load_json("configs/first_paper_mechanism_contract_v0.6.json")
    analysis = load_json("configs/first_paper_analysis_contract_v0.5.json")
    measurement = load_json("configs/process_reality_measurement_contract_v0.7.json")
    variables = load_json("configs/experimental_variable_registry_v0.5.json")
    selection = load_json("configs/r5r6_specificity_field_selection_contract_v0.1.json")
    plan_schema = load_json("schemas/r5r6_specificity_plan_v0.1.schema.json")
    comparison_schema = load_json("schemas/r5r6_specificity_comparison_v0.1.schema.json")

    require(mechanism["schema"] == "RB-FIRST-PAPER-MECHANISM-CONTRACT-v0.6", "mechanism_contract_schema_invalid")
    require(analysis["schema"] == "RB-FIRST-PAPER-ANALYSIS-CONTRACT-v0.5", "analysis_contract_schema_invalid")
    require(measurement["schema"] == "RB-PROCESS-REALITY-MEASUREMENT-CONTRACT-v0.7", "measurement_contract_schema_invalid")
    require(variables["schema"] == "RB-EXPERIMENTAL-VARIABLE-REGISTRY-v0.5", "variable_registry_schema_invalid")
    require(selection["schema"] == "RB-R5R6-SPECIFICITY-FIELD-SELECTION-CONTRACT-v0.1", "field_selection_contract_schema_invalid")
    require(plan_schema["$id"] == "RB-R5R6-SPECIFICITY-PLAN-v0.1", "specificity_plan_schema_id_invalid")
    require(comparison_schema["$id"] == "RB-R5R6-SPECIFICITY-COMPARISON-v0.1", "specificity_comparison_schema_id_invalid")

    spec = mechanism["specificity"]
    require(spec["namespace"] == "S", "specificity_namespace_must_be_s")
    require(spec["contrasts"]["PRIMARY_TARGET_SPECIFICITY"] == "S2_MINUS_S1", "primary_specificity_contrast_invalid")
    require(spec["s1_zero_effect_required"] is False, "s1_zero_effect_must_not_be_required")
    require(spec["same_intervention_mechanics_s1_s2_required"] is True, "s1_s2_mechanical_equivalence_required")

    r6 = mechanism["r6"]
    require(r6["role"] == "POST_CONSUMPTION_SYSTEM_INERTIA_READOUT", "r6_role_invalid")
    require(r6["local_response_is_not_inertia"] is True, "local_response_must_not_equal_inertia")
    require(r6["single_scalar_required"] is False, "single_inertia_scalar_must_not_be_required")

    r7 = mechanism["r7"]
    require(r7["namespace"] == "C", "r7_namespace_must_be_c")
    require(r7["s_namespace_aliasing_forbidden"] is True, "s_c_aliasing_must_be_forbidden")
    require(r7["conditions_preserved"] == [
        "C1_ONE_SHOT_FREE_CONTINUATION",
        "C2_PERSISTENT_FIELD_PROPAGATION",
        "C3_ALR_AUTHORITY_LOCALIZED_RECOVERY",
    ], "r7_conditions_changed_unexpectedly")

    analysis_spec = analysis["r5r6_specificity"]
    require(analysis_spec["primary_readout"] == "R6_POST_CONSUMPTION_INERTIA_PROFILE", "specificity_primary_readout_invalid")
    require(analysis_spec["local_activity_volume_is_primary_specificity_endpoint"] is False, "local_activity_must_not_be_primary_specificity_endpoint")
    require(analysis_spec["s1_zero_response_required"] is False, "analysis_s1_zero_response_must_not_be_required")
    require(analysis["integrity"]["no_outcome_aware_s1_selection"] is True, "outcome_aware_s1_selection_must_be_forbidden")

    require(measurement["r5r6_specificity_contrasts"]["PRIMARY_TARGET_SPECIFICITY"]["primary_readout"] == "POST_CONSUMPTION_INERTIA_PROFILE", "measurement_specificity_readout_invalid")
    require(measurement["r7_namespace_guard"]["aliasing_forbidden"] is True, "measurement_namespace_aliasing_must_be_forbidden")
    require(measurement["paid_provider_authorized"] is False, "measurement_contract_must_not_authorize_paid_provider")

    guards = variables["namespace_guards"]
    require(guards["specificity_namespace"] == "S", "variable_registry_specificity_namespace_invalid")
    require(guards["r7_structural_handling_namespace"] == "C", "variable_registry_r7_namespace_invalid")
    require(guards["s_to_c_aliasing_forbidden"] is True, "variable_registry_s_c_aliasing_must_be_forbidden")

    require(selection["selection_timing"]["outcome_aware_target_selection_forbidden"] is True, "field_selection_outcome_awareness_forbidden")
    require(selection["eligible_pool_rules"]["expected_low_effect_control_selection_forbidden"] is True, "low_effect_control_cherrypicking_forbidden")
    require(selection["intervention_equivalence"]["s1_s2_same_to_status_required"] is True, "s1_s2_to_status_must_match")
    require(selection["authorization"]["paid_provider_run"] is False, "field_selection_contract_must_not_authorize_provider")

    for rel in (
        "docs/R_Plan_v4.4.md",
        "theory/theory_contract_v0.8.md",
        "docs/system_behavior_measurement_plan_v4.4.md",
        "docs/R6_inertia_transition_protocol_v0.2.md",
        "docs/R5_R6_specificity_protocol_v0.1.md",
        "docs/first_paper_v4.4_scope.md",
    ):
        require((ROOT / rel).is_file(), f"missing_forward_document:{rel}")

    print("R5R6_SPECIFICITY_PROTOCOL_VALIDATION=PASS")
    print("SPECIFICITY_NAMESPACE=S")
    print("R7_NAMESPACE=C")
    print("PRIMARY_SPECIFICITY_CONTRAST=S2_MINUS_S1")
    print("PRIMARY_READOUT=POST_CONSUMPTION_INERTIA_PROFILE")
    print("PAID_PROVIDER_AUTHORIZED=NO")
    print("PAID_EVALUATOR_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
