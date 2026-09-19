from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit("FAIL: " + message)


def load_json(path: str):
    with (ROOT / path).open("r", encoding="utf-8") as f:
        return json.load(f)


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> None:
    contract = load_json("configs/process_reality_probability_structure_separation_v1.0.json")
    require(contract["status"] == "FORWARD_ACTIVE_V5_3", "forward status must be v5.3")
    require(contract["primary_separation"]["probability_unit"] == "DOMAIN_ENVIRONMENT_TRAJECTORY_POPULATION", "probability unit mismatch")
    require(contract["primary_separation"]["structure_unit"] == "NATURALLY_REALIZED_SOURCE_BOUND_CASE", "structure unit mismatch")

    inv = contract["invariants"]
    for key in (
        "r5_reestimates_domain_probability",
        "r6_requires_new_subject_experiment",
        "r6_requires_fixed_parent_repetition",
        "fixed_parent_repetition_estimates_domain_probability",
        "fixed_parent_nonreproduction_negates_realized_case_structure",
        "exact_output_inequality_is_semantic_effect",
        "case_level_structure_requires_cross_run_frequency",
        "r7_gate_depends_on_fixed_parent_recurrence_frequency",
    ):
        require(inv[key] is False, f"invariant must remain false: {key}")

    fixed_parent = contract["optional_modules"]["fixed_parent_repetition"]
    require(fixed_parent["role"] == "SUPPLEMENTARY_LOCAL_CONDITIONAL_SENSITIVITY_ONLY", "fixed-parent role mismatch")

    manifest = load_json("manifests/v5_cross_domain_probability_structure_reclassification_2026-09-19_v0_1.json")
    require(manifest["frozen_evidence_mutated"] is False, "frozen evidence may not be mutated")
    require(manifest["new_provider_call_authorized"] is False, "correction may not authorize provider call")
    require(manifest["r7_authorized"] is False, "correction may not authorize R7")
    followup = manifest["reclassified_followup"]
    require(followup["workflow_run_id"] == 35423813470, "reclassified workflow mismatch")
    require(followup["forward_role"] == "SUPPLEMENTARY_LOCAL_CONDITIONAL_SENSITIVITY", "follow-up role mismatch")
    require(followup["estimates_domain_probability"] is False, "fixed-parent follow-up may not estimate domain probability")
    require(followup["required_for_r6_entry"] is False, "fixed-parent follow-up may not gate R6")
    require(followup["required_for_r7_entry"] is False, "fixed-parent follow-up may not gate R7")
    require(followup["may_negate_observed_case_structure"] is False, "fixed-parent nonreproduction may not erase case structure")

    wave4 = manifest["wave4_forward_status"]
    require(wave4["carrier_read_adoption_persistence"] == "SUPPORTED_IN_REALIZED_BRANCH", "wave4 realized structure must remain supported")
    require(wave4["r7_status"] == "NOT_AUTHORIZED_PENDING_CASE_LEVEL_LINEAGE_COMPLETENESS_REASSESSMENT", "R7 boundary mismatch")

    required_files = [
        "docs/R_Plan_v5.3.md",
        "theory/theory_contract_v0.14.md",
        "docs/first_paper_v5_3_scope.md",
        "docs/R5_structural_scouting_and_driver_probe_protocol_v1.1.md",
        "docs/R6_structural_support_trace_control_surface_protocol_v1.1.md",
        "docs/cross_domain_case_progression_contract_v0.2.md",
        "docs/v5_whole_process_experiment_protocol_v0.2.md",
        "docs/reporting/process_reality_theory_experiment_report_standard_v1_1.md",
        "docs/cross_domain_probability_structure_interpretation_addendum_v0.1.md",
        "docs/reports/2026-09-19/V5_Cross_Domain_Probability_Structure_Interpretation_Correction_v1.md",
    ]
    for path in required_files:
        require((ROOT / path).exists(), "missing v5.3 file: " + path)

    require("Entering R6 does not require an additional provider run." in text("docs/R_Plan_v5.3.md"), "R6 passive boundary missing")
    require("SUPPLEMENTARY_LOCAL_CONDITIONAL_SENSITIVITY" in text("docs/R_Plan_v5.3.md"), "local sensitivity label missing")
    require("No additional provider run is required merely to enter R6." in text("docs/cross_domain_probability_structure_interpretation_addendum_v0.1.md"), "cross-domain R6 entry boundary missing")
    require("R7 entry depends on completeness/repairability, not fixed-parent recurrence." in text("docs/R6_structural_support_trace_control_surface_protocol_v1.1.md"), "R7 gate boundary missing")

    print("PASS: Process Reality v5.3 probability/structure separation is synchronized")
    print("PROBABILITY_UNIT=DOMAIN_ENVIRONMENT_TRAJECTORY_POPULATION")
    print("STRUCTURE_UNIT=NATURALLY_REALIZED_SOURCE_BOUND_CASE")
    print("R6_REQUIRES_NEW_PROVIDER_RUN=NO")
    print("FIXED_PARENT_ROLE=SUPPLEMENTARY_LOCAL_CONDITIONAL_SENSITIVITY_ONLY")
    print("R7_DEPENDS_ON_FIXED_PARENT_RECURRENCE=NO")
    print("FROZEN_EVIDENCE_MUTATED=NO")


if __name__ == "__main__":
    main()
