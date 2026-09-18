from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_R6D_DESIGN_HASH = "d8783a9c3e0a264c3119ee72e63db9b61d51f0d633ff6dde66068751c31701de"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(f"FAIL: {message}")


def load_json(path: str):
    with (ROOT / path).open("r", encoding="utf-8") as f:
        return json.load(f)


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require_tokens(path: str, tokens: list[str]) -> None:
    body = text(path)
    for token in tokens:
        require(token in body, f"{path} missing {token!r}")


def main() -> None:
    required_files = [
        "theory/theory_contract_v0.11.md",
        "docs/R_Plan_v5.0.md",
        "docs/first_paper_v5_scope.md",
        "docs/v5_concept_mapping.md",
        "docs/v5_structural_observability_contract_v0.1.md",
        "docs/v5_historical_rederivation_protocol_v0.1.md",
        "docs/v5_whole_process_experiment_protocol_v0.1.md",
        "docs/R5_structural_scouting_and_driver_probe_protocol_v1.0.md",
        "docs/R6_structural_support_trace_control_surface_protocol_v1.0.md",
        "docs/R7_localized_recovery_protocol_v1.0.md",
        "docs/reporting/process_reality_report_standard_v1_5.md",
        "schemas/structural_support_record_v0.1.schema.json",
        "schemas/process_integrity_event_v0.3.schema.json",
        "schemas/process_integrity_lineage_record_v0.3.schema.json",
        "schemas/semantic_audit_record_v0.2.schema.json",
        "configs/v5_whole_process_experiment_chain_v0.1.json",
    ]
    for path in required_files:
        require((ROOT / path).exists(), f"missing required v5 file: {path}")

    # Legacy frozen design remains unchanged.
    legacy = load_json("manifests/r6d_specificity_preexecution_design_freeze_2026-09-17_v0_1.json")
    require(legacy["design_hash"] == LEGACY_R6D_DESIGN_HASH, "legacy R6-D design hash changed")

    migration = load_json("manifests/process_reality_v5_methodological_migration_2026-09-18.json")
    require(migration["legacy_layer"]["evidence_mutated"] is False, "migration may not mutate historical evidence")
    require(migration["provider_run_authorized"] is False, "migration may not authorize provider run")

    mechanism = load_json("configs/first_paper_mechanism_contract_v0.8.json")
    require(mechanism["legacy_compatibility"]["jump_is_semantic_origin_by_default"] is False, "legacy Jump/origin guard missing")
    require(mechanism["r5"]["historical_operator_is_r5_definition"] is False, "R5 remains overbound to one-shot operator")
    require(mechanism["r6"]["detection_surface_equals_trace_root_required"] is False, "detection/trace separation missing")
    require(mechanism["r6"]["trace_root_equals_intervention_surface_required"] is False, "trace/intervention separation missing")

    analysis = load_json("configs/first_paper_analysis_contract_v0.8.json")
    require(analysis["r6"]["historical_abcd_modules_default_required_for_new_run"] is False, "old R6 A-D still mandatory")
    require("STRUCTURAL_SUPPORT_CANDIDATE" in analysis["primary_analysis_objects"], "support object missing")
    require("STABLE_SHARED_POOL_ENTRY_CANDIDATE" in analysis["primary_analysis_objects"], "pool object missing")

    scout = load_json("configs/structural_support_scout_v0.1.json")
    candidate_types = {r["candidate_type"] for r in scout["rules"]}
    require("STRUCTURAL_SUPPORT_CANDIDATE" in candidate_types, "support scout rule missing")
    require("STRUCTURAL_EXPOSURE_CANDIDATE" in candidate_types, "exposure scout rule missing")

    measurement = load_json("configs/process_reality_measurement_contract_v1.0.json")
    require(measurement["invariants"]["shared_addressability_is_epistemic_validity"] is False, "pool/truth boundary missing")
    require(measurement["invariants"]["legacy_jump_equals_origin"] is False, "legacy Jump/origin measurement guard missing")

    chain = load_json("configs/v5_whole_process_experiment_chain_v0.1.json")
    require(chain["invariants"]["raw_freeze_before_semantic_audit"] is True, "raw-before-audit invariant missing")
    require(chain["invariants"]["all_event_semantic_judge_required"] is False, "all-event Judge must not be mandatory")
    require(chain["invariants"]["optional_robustness_required_for_every_run"] is False, "optional robustness still mandatory")

    lineage = load_json("schemas/process_integrity_lineage_record_v0.3.schema.json")
    required_lineage = set(lineage["required"])
    for field in [
        "trace_root_ref",
        "structural_support_refs",
        "pool_entry_refs",
        "exposure_anchor_refs",
        "candidate_intervention_surface_refs",
    ]:
        require(field in required_lineage, f"lineage required field missing: {field}")

    semantic = load_json("schemas/semantic_audit_record_v0.2.schema.json")
    roles = set(semantic["properties"]["semantic_role"]["enum"])
    for role in [
        "UNSTABLE_INFORMATION",
        "SEMANTIC_TRANSFORMATION",
        "STRUCTURAL_SUPPORT",
        "STABLE_POOL_ENTRY",
        "DIRECT_POOL_CONSUMPTION",
        "STRUCTURAL_EXPOSURE",
        "DRIVER_RESPONSE",
    ]:
        require(role in roles, f"semantic role missing: {role}")

    report = load_json("schemas/process_reality_report_template_v1_5.json")
    require(report["legacy_compatibility"]["legacy_j0_may_be_auto_relabeled"] is False, "report legacy mapping guard missing")

    require_tokens("theory/theory_contract_v0.11.md", [
        "Unstable Information",
        "Escape Structure",
        "Stable Shared Information Pool",
        "Detection Surface != Trace Root != Intervention Surface",
    ])
    require_tokens("docs/R_Plan_v5.0.md", [
        "Whole-Process Runs",
        "Optional robustness modules",
        "No new R stage is added",
    ])
    require_tokens("docs/reporting/process_reality_report_standard_v1_5.md", [
        "Structural Support",
        "Stable Shared Pool",
        "Structural Exposure",
    ])
    require_tokens("README.md", [
        "Process Reality v5.0",
        "Whole-Process Run",
    ])

    print("PASS: Process Reality v5 methodological migration is synchronized")
    print(f"LEGACY_R6D_DESIGN_HASH={LEGACY_R6D_DESIGN_HASH}")
    print("HISTORICAL_EVIDENCE_MUTATED=NO")
    print("SCIENTIFIC_PROVIDER_RUN_AUTHORIZED=NO")
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
