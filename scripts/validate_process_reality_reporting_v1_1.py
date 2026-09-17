#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def load_json(rel: str):
    with (ROOT / rel).open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    standard = ROOT / "docs/reporting/process_reality_report_standard_v1_1.md"
    template_path = "schemas/process_reality_report_template_v1_1.json"
    require(standard.is_file(), "report_standard_v1_1_missing")
    template = load_json(template_path)

    require(template["schema"] == "RB-PROCESS-REALITY-REPORT-TEMPLATE-v1.1", "report_template_schema_invalid")
    require(template["report_standard"] == "RB-PROCESS-REALITY-REPORT-STANDARD-v1.1", "report_standard_binding_invalid")
    require(template["historical_v1_0_reports_remain_valid"] is True, "historical_v1_0_compatibility_required")

    profiles = template["report_profiles"]
    require("r6_system_inertia_factual_report" in profiles, "r6_report_profile_missing")
    require("r5r6_specificity_validation_report" in profiles, "specificity_report_profile_missing")

    spec = template["specificity_requirements"]
    require(spec["namespace"] == "S", "specificity_namespace_invalid")
    require(spec["r7_namespace"] == "C", "r7_namespace_invalid")
    require(spec["s_c_aliasing_forbidden"] is True, "specificity_r7_aliasing_must_be_forbidden")
    require(spec["primary_contrast"] == "S2_MINUS_S1", "specificity_primary_contrast_invalid")
    require(spec["primary_readout"] == "POST_CONSUMPTION_R6_INERTIA_PROFILE", "specificity_primary_readout_invalid")
    require(spec["s1_zero_effect_required"] is False, "s1_zero_effect_must_not_be_required")
    require(spec["outcome_blind_s1_selection_required"] is True, "outcome_blind_s1_required")
    require(spec["s1_s2_mechanical_equivalence_required"] is True, "s1_s2_mechanical_equivalence_required")
    require(spec["specificity_is_not_semantic_cpr_truth"] is True, "specificity_semantic_boundary_required")

    hierarchy = template["reporting_hierarchy"]
    require(hierarchy.index("local_perturbation_response") < hierarchy.index("post_consumption_inertia_profile"), "local_response_must_precede_inertia")
    require(hierarchy.index("post_consumption_inertia_profile") < hierarchy.index("target_specificity_contrast_if_applicable"), "inertia_must_precede_specificity")
    require(hierarchy.index("target_specificity_contrast_if_applicable") < hierarchy.index("terminal_outcome_separate"), "terminal_outcome_must_remain_separate_and_later")

    integrity = template["integrity_constraints"]
    for key in (
        "no_outcome_aware_s1_selection",
        "no_control_cherrypicking_for_expected_low_effect",
        "no_historical_ab_relabel_to_s",
        "no_r7_c_relabel_to_s",
        "no_inertia_absence_inference_from_censoring",
        "no_unvalidated_local_plus_inertia_composite_score",
    ):
        require(integrity[key] is True, f"report_integrity_guard_missing:{key}")

    text = standard.read_text(encoding="utf-8")
    for phrase in (
        "R6 System Inertia Factual Report",
        "R5-R6 Specificity Validation Report",
        "S2 - S1",
        "Matched Factual Field",
        "Immediate perturbation response",
    ):
        require(phrase in text, f"report_standard_phrase_missing:{phrase}")

    print("PROCESS_REALITY_REPORTING_V1_1_VALIDATION=PASS")
    print("R6_FACTUAL_PROFILE=YES")
    print("R5R6_SPECIFICITY_PROFILE=YES")
    print("SPECIFICITY_NAMESPACE=S")
    print("R7_NAMESPACE=C")
    print("PRIMARY_SPECIFICITY_CONTRAST=S2_MINUS_S1")


if __name__ == "__main__":
    main()
