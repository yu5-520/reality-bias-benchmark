#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_json(rel: str):
    with (ROOT / rel).open("r", encoding="utf-8") as f:
        return json.load(f)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def require_file(rel: str) -> str:
    p = ROOT / rel
    require(p.is_file(), f"missing_file:{rel}")
    return p.read_text(encoding="utf-8")


def main() -> None:
    plan = require_file("docs/R_Plan_v4.5.md")
    theory = require_file("theory/theory_contract_v0.9.md")
    measurement_plan = require_file("docs/system_behavior_measurement_plan_v4.5.md")
    r6 = require_file("docs/R6_inertia_identification_protocol_v0.3.md")
    spec = require_file("docs/R5_R6_specificity_protocol_v0.3.md")
    r7 = require_file("docs/R7_structural_inertia_control_protocol_v0.4.md")
    alr = require_file("docs/ALR_authority_localized_recovery_contract_v0.3.md")
    eng = require_file("docs/R7_process_integrity_engineering_profile_v0.1.md")
    scope = require_file("docs/first_paper_v4.5_scope.md")
    evidence = require_file("docs/evidence_status_addendum_v0.1.md")
    report_standard = require_file("docs/reporting/process_reality_report_standard_v1_2.md")

    mechanism = load_json("configs/first_paper_mechanism_contract_v0.7.json")
    analysis = load_json("configs/first_paper_analysis_contract_v0.6.json")
    measurement = load_json("configs/process_reality_measurement_contract_v0.8.json")
    variables = load_json("configs/experimental_variable_registry_v0.6.json")
    engineering = load_json("configs/r7_process_integrity_engineering_contract_v0.1.json")
    selection = load_json("configs/r5r6_specificity_field_selection_contract_v0.2.json")
    binding = load_json("configs/r5r6_specificity_exact_source_binding_v0.2.json")
    report_template = load_json("schemas/process_reality_report_template_v1_2.json")
    event_schema = load_json("schemas/process_integrity_event_v0.1.schema.json")
    lineage_schema = load_json("schemas/process_integrity_lineage_record_v0.1.schema.json")

    require(mechanism["schema"] == "RB-FIRST-PAPER-MECHANISM-CONTRACT-v0.7", "mechanism_schema_invalid")
    require(analysis["schema"] == "RB-FIRST-PAPER-ANALYSIS-CONTRACT-v0.6", "analysis_schema_invalid")
    require(measurement["schema"] == "RB-PROCESS-REALITY-MEASUREMENT-CONTRACT-v0.8", "measurement_schema_invalid")
    require(variables["schema"] == "RB-EXPERIMENTAL-VARIABLE-REGISTRY-v0.6", "variable_registry_schema_invalid")
    require(engineering["schema"] == "RB-R7-PROCESS-INTEGRITY-ENGINEERING-CONTRACT-v0.1", "engineering_schema_invalid")
    require(report_template["schema"] == "RB-PROCESS-REALITY-REPORT-TEMPLATE-v1.2", "report_template_schema_invalid")
    require(report_template["report_standard"] == "RB-PROCESS-REALITY-REPORT-STANDARD-v1.2", "report_template_standard_binding_invalid")
    require(event_schema["$id"] == "RB-PROCESS-INTEGRITY-EVENT-v0.1", "event_schema_id_invalid")
    require(lineage_schema["$id"] == "RB-PROCESS-INTEGRITY-LINEAGE-RECORD-v0.1", "lineage_schema_id_invalid")

    require(mechanism["r6"]["role"] == "SYSTEM_INERTIA_IDENTIFICATION", "r6_mechanism_role_invalid")
    require(set(mechanism["r6"]["subroles"]) == {"R6_A", "R6_B", "R6_C", "R6_D"}, "r6_subroles_invalid")
    require(analysis["r6"]["subanalyses"]["R6_C_INTERVENTION_RELATED_INERTIA"]["requires_natural_variability_reference"] is True, "r6_natural_baseline_requirement_missing")
    require(analysis["r6"]["subanalyses"]["R6_B_CARRIER_IDENTIFICATION"]["reachability_is_not_semantic_adoption"] is True, "carrier_semantic_guard_missing")
    require(measurement["censoring"]["censored_equals_zero"] is False, "censoring_guard_missing")

    sconds = mechanism["r6_specificity"]["conditions"]
    require(sconds == [
        "S0_NATURAL_REFERENCE",
        "S1_MATCHED_OR_ORDINARY_FACTUAL_INFORMATION_DOWNGRADE",
        "S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL",
    ], "specificity_conditions_invalid")
    require(mechanism["r6_specificity"]["primary_contrast"] == "S2_MINUS_S1", "specificity_primary_contrast_invalid")
    require(mechanism["r6_specificity"]["s1_zero_effect_required"] is False, "s1_zero_effect_must_not_be_required")
    require(binding["s1"]["target_locator"] == "public_context.products.C.gross_margin_pct", "s1_exact_target_invalid")
    require(binding["s1"]["original_value"] == 35, "s1_exact_value_invalid")
    require(binding["s2"]["target_locator"] == "shared_state.inventory_stockout_assessment_v1.A.preliminary_stock", "s2_exact_target_invalid")
    require(binding["s2"]["original_value"] == 1520, "s2_exact_value_invalid")
    require(binding["s2"]["source_origin_status"] == "preliminary_unreconciled", "s2_source_origin_status_invalid")
    require(binding["s2"]["acquired_status_at_intervention"] == "fact", "s2_acquired_status_invalid")
    require(selection["selection_timing"]["must_complete_before_scientific_s_arm_outputs"] is True, "outcome_blind_selection_guard_missing")

    require(mechanism["r7"]["namespace"] == "C", "r7_namespace_invalid")
    require(mechanism["r7_engineering_implication"]["scientific_result"] is False, "engineering_implication_must_not_be_scientific_result")
    require(engineering["runtime_modes"]["PASSIVE"]["may_modify_agent_prompt"] is False, "passive_prompt_interference_forbidden")
    require(engineering["runtime_modes"]["PASSIVE"]["may_modify_routing"] is False, "passive_routing_interference_forbidden")
    require(engineering["adapter_rule"]["replacement_agent_sdk_required"] is False, "replacement_agent_sdk_must_not_be_required")
    require(engineering["adapter_rule"]["replacement_mcp_or_a2a_protocol_required"] is False, "replacement_protocol_must_not_be_required")
    require(engineering["point_repair_rule"]["silent_overwrite_forbidden"] is True, "silent_overwrite_guard_missing")

    profiles = report_template["report_profiles"]
    for name in ("r6_system_inertia_identification_report", "r6_target_specificity_report", "r7_localized_risk_control_report", "process_integrity_engineering_profile"):
        require(name in profiles, f"report_profile_missing:{name}")

    hierarchy = report_template["reporting_hierarchy"]
    require(hierarchy.index("local_perturbation_response") < hierarchy.index("r6_natural_inertia_baseline"), "report_hierarchy_local_before_baseline_required")
    require(hierarchy.index("r6_natural_inertia_baseline") < hierarchy.index("r6_carrier_and_inheritance_evidence"), "report_hierarchy_baseline_before_carrier_required")
    require(hierarchy.index("r6_carrier_and_inheritance_evidence") < hierarchy.index("r6_post_consumption_intervention_related_inertia"), "report_hierarchy_carrier_before_inertia_required")
    require(hierarchy.index("r6_post_consumption_intervention_related_inertia") < hierarchy.index("r6_target_specificity_if_applicable"), "report_hierarchy_inertia_before_specificity_required")

    required_phrases = {
        "plan": ["R6-A", "R6-B", "R6-C", "R6-D", "Process Integrity Protocol"],
        "theory": ["System Inertia Identification", "REACHABLE_CARRIER", "Process Integrity Protocol"],
        "measurement": ["R6-A Natural Inertia Baseline", "Carrier / Inheritance", "right-censoring"],
        "r6": ["R6-A", "R6-B", "R6-C", "R6-D"],
        "r7": ["risk-bearing", "content/revision", "Process Integrity"],
        "alr": ["R6-identified", "Content-addressed revision identity"],
        "engineering": ["lightweight", "pluggable", "content-addressed", "Point Repair"],
        "scope": ["Four contribution layers", "Localized solution"],
        "evidence": ["Intervention-related inertia transition", "Target specificity", "NOT_ADJUDICATED"],
        "report": ["R6 System Inertia Identification Report", "R7 Localized Risk-Control / Recovery Report"]
    }
    texts = {"plan": plan, "theory": theory, "measurement": measurement_plan, "r6": r6, "r7": r7, "alr": alr, "engineering": eng, "scope": scope, "evidence": evidence, "report": report_standard}
    for key, phrases in required_phrases.items():
        haystack = texts[key].lower()
        for phrase in phrases:
            require(phrase.lower() in haystack, f"missing_phrase:{key}:{phrase}")

    for auth in (
        mechanism["authorization"],
        analysis["authorization"],
        measurement["authorization"],
        variables["authorization"],
        engineering["authorization"],
    ):
        require(auth.get("paid_provider_run", False) is False, "paid_provider_must_not_be_authorized")
        require(auth.get("paid_evaluator_run", False) is False, "paid_evaluator_must_not_be_authorized")

    print("PROCESS_REALITY_V4_5_VALIDATION=PASS")
    print("R6_ROLE=SYSTEM_INERTIA_IDENTIFICATION")
    print("R6_SUBROLES=R6_A,R6_B,R6_C,R6_D")
    print("R6_PRIMARY_SPECIFICITY_CONTRAST=S2_MINUS_S1")
    print("R7_ENGINEERING_PROFILE=PROCESS_INTEGRITY_PROTOCOL")
    print("PASSIVE_NON_INTERFERENCE=YES")
    print("PAID_PROVIDER_AUTHORIZED=NO")
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
