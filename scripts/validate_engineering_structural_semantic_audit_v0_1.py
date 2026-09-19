#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCHEMA = "RB-ENGINEERING-STRUCTURAL-SEMANTIC-AUDIT-v0.1"
BUNDLE_SCHEMA = "RB-V5.4-R5R7-ENGINEERING-REPORT-EVIDENCE-BUNDLE-v0.1"
EXPECTED_CASES = {
    "wave-3-56ee79f97f54",
    "wave-4-8b1731b57396",
    "wave-4-cf726639de1d",
    "wave-6-7c7e526e4d91",
}
REQUIRED_LEDGER_DIMENSIONS = {
    "CONTROL_SURFACE",
    "LOCALIZATION",
    "CONTENT_ADDRESSING",
    "INVALIDATION",
    "REOPEN",
    "RECOMPUTE",
    "PRESERVATION",
    "REENTRY",
    "AUTHORITY_RESULT",
    "ENDPOINT_PROCESS_RELATION",
    "HORIZON",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def load(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return json.loads(p.read_text(encoding="utf-8"))


def stable_hash(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            obj,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def hash_without(row: dict[str, Any], key: str) -> str:
    x = copy.deepcopy(row)
    x.pop(key, None)
    return stable_hash(x)


def validate_contracts() -> None:
    cfg = load("configs/v5_4_r5_r7_engineering_structural_semantic_audit_v0.1.json")
    audit_schema = load("schemas/engineering_structural_semantic_audit_v0.1.schema.json")
    bundle_schema = load("schemas/engineering_report_evidence_bundle_v0.1.schema.json")

    require(
        cfg["schema"]
        == "RB-V5.4-R5R7-ENGINEERING-STRUCTURAL-SEMANTIC-AUDIT-CONFIG-v0.1",
        "engineering_config_schema_invalid",
    )
    require(set(cfg["candidate_case_ids"]) == EXPECTED_CASES, "candidate_case_set_invalid")
    require(cfg["expected"]["case_count"] == 4, "expected_case_count_invalid")
    require(cfg["expected"]["lineage_complete_count"] == 4, "lineage_complete_count_invalid")
    require(cfg["expected"]["r7_p_trace_count"] == 4, "r7_p_count_invalid")
    require(cfg["expected"]["r7_s_trace_count"] == 4, "r7_s_count_invalid")
    require(cfg["expected"]["persistent_direct_exposure_count"] == 32, "persistent_exposure_count_invalid")
    require(cfg["expected"]["structured_repair_preserved_unrelated_case_count"] == 4, "preservation_count_invalid")
    require(cfg["expected"]["structural_old_fact_reentry_case_count"] == 1, "reentry_count_invalid")
    require(cfg["expected"]["blind_old_fact_restoration_case_count"] == 0, "blind_restore_count_invalid")
    require(cfg["expected"]["material_divergence_case_count"] == 2, "divergence_count_invalid")
    require(cfg["expected"]["reconvergence_case_count"] == 2, "reconvergence_count_invalid")
    require(cfg["expected"]["fixed_horizon_censored_trace_count"] == 8, "censor_count_invalid")

    ops = cfg["operator_semantics"]
    require(ops["R5_I"]["engineering_role"] == "PROBE_NOT_REPAIR", "r5_role_invalid")
    require(ops["R6"]["engineering_role"] == "REPAIR_READINESS_NOT_REPAIR", "r6_role_invalid")
    require(ops["R7_P"]["engineering_role"] == "EXTERNAL_CORRECTION_NOT_INTERNAL_REPAIR", "r7p_role_invalid")
    require(ops["R7_S"]["engineering_role"] == "STRUCTURAL_REPAIR", "r7s_role_invalid")
    require(ops["R5_I"]["mutates_underlying_shared_state"] is False, "r5_mutation_guard_invalid")
    require(ops["R6"]["mutates_underlying_shared_state"] is False, "r6_mutation_guard_invalid")
    require(ops["R7_P"]["mutates_underlying_shared_state"] is False, "r7p_mutation_guard_invalid")
    require(ops["R7_S"]["mutates_underlying_shared_state"] is True, "r7s_mutation_guard_invalid")

    boundary = cfg["execution_boundary"]
    require(boundary["subject_reruns"] == 0, "subject_rerun_guard_invalid")
    require(boundary["new_provider_calls"] == 0, "provider_guard_invalid")
    require(boundary["new_paid_evaluator_calls"] == 0, "evaluator_guard_invalid")
    require(boundary["raw_evidence_mutated"] is False, "raw_mutation_guard_invalid")
    require(boundary["cpr_adjudicated"] is False, "cpr_guard_invalid")
    require(boundary["intervention_superiority_adjudicated"] is False, "superiority_guard_invalid")

    require(audit_schema["$id"] == AUDIT_SCHEMA, "engineering_audit_schema_id_invalid")
    for field in (
        "engineering_lifecycle",
        "r7_p_route",
        "r7_s_route",
        "repair_scope",
        "engineering_semantic_ledger",
        "p_vs_s_semantic_contrast",
        "engineering_case_class",
    ):
        require(field in audit_schema["properties"], "engineering_audit_schema_missing:" + field)

    require(bundle_schema["$id"] == BUNDLE_SCHEMA, "engineering_bundle_schema_id_invalid")

    contract = (ROOT / "docs/engineering_structural_semantic_audit_contract_v0.1.md").read_text(encoding="utf-8")
    for phrase in (
        "PROBE_NOT_REPAIR",
        "REPAIR_READINESS_NOT_REPAIR",
        "EXTERNAL_CORRECTION_NOT_INTERNAL_REPAIR",
        "STRUCTURAL_REPAIR",
        "same endpoint != same engineering process",
        "structural recomputation != semantic novelty",
        "exact key/status re-entry != blind restoration",
        "NOT_ADJUDICATED",
    ):
        require(phrase in contract, "engineering_contract_phrase_missing:" + phrase)

    standard = (
        ROOT / "docs/reporting/process_reality_engineering_experiment_report_standard_v1_3.md"
    ).read_text(encoding="utf-8")
    for phrase in (
        AUDIT_SCHEMA,
        "R5 probe != R6 repair readiness != R7-P persistent correction != R7-S structural repair",
        "FRESH_EVIDENCE_BASED_AUTHORITY_REGENERATION",
        "BUDGET_CENSORED / turn_budget_exhausted",
    ):
        require(phrase in standard, "engineering_report_standard_phrase_missing:" + phrase)


def validate_route(route: dict[str, Any], arm_id: str) -> None:
    require(route["arm_id"] == arm_id, "route_arm_id_mismatch")
    require(route["complete_route_verified"] is True, "route_not_complete")
    require(route["fixed_horizon_censored"] is True, "route_not_fixed_horizon_censored")
    nodes = route.get("nodes") or []
    require(len(nodes) == 8, "canonical_r7_route_must_have_8_nodes")
    indices = [int(node["route_index"]) for node in nodes]
    require(indices == list(range(8)), "route_indices_must_be_0_to_7")
    require(all(node.get("call_ref") for node in nodes), "route_call_ref_missing")
    require(all(node.get("agent_role") for node in nodes), "route_agent_missing")
    require(
        route["terminal"]["run_status"] == "BUDGET_CENSORED"
        and route["terminal"]["termination_reason"] == "turn_budget_exhausted",
        "route_terminal_not_common_fixed_horizon",
    )
    require(route["terminal"]["terminal_outcome_is_primary"] is False, "terminal_outcome_primary_forbidden")


def validate_audit(row: dict[str, Any]) -> None:
    require(row.get("schema") == AUDIT_SCHEMA, "engineering_audit_schema_invalid")
    require(row["case_id"] in EXPECTED_CASES, "engineering_case_unknown")
    require(
        row["reviewer"]["blind_to_prior_semantic_labels"] is False,
        "engineering_rebinding_review_mode_drift",
    )

    lifecycle = row["engineering_lifecycle"]
    require(lifecycle["R5_I"]["engineering_role"] == "PROBE_NOT_REPAIR", "r5_engineering_role_invalid")
    require(lifecycle["R6"]["engineering_role"] == "REPAIR_READINESS_NOT_REPAIR", "r6_engineering_role_invalid")
    require(lifecycle["R7_P"]["engineering_role"] == "EXTERNAL_CORRECTION_NOT_INTERNAL_REPAIR", "r7p_engineering_role_invalid")
    require(lifecycle["R7_S"]["engineering_role"] == "STRUCTURAL_REPAIR", "r7s_engineering_role_invalid")
    require(lifecycle["R5_I"]["underlying_shared_state_mutation"] is False, "r5_underlying_mutation_forbidden")
    require(lifecycle["R6"]["underlying_shared_state_mutation"] is False, "r6_underlying_mutation_forbidden")
    require(lifecycle["R7_P"]["underlying_shared_state_mutation"] is False, "r7p_underlying_mutation_forbidden")
    require(lifecycle["R7_S"]["underlying_shared_state_mutation"] is True, "r7s_underlying_mutation_required")

    validate_route(row["r7_p_route"], "R7_P_PERSISTENT_SEMANTIC")
    validate_route(row["r7_s_route"], "R7_S_STRUCTURED_LINEAGE_REPAIR")
    require(row["r7_p_route"]["direct_exposure_count"] == 8, "r7p_direct_exposure_count_invalid")
    require(row["r7_s_route"]["direct_exposure_count"] == 0, "r7s_runtime_overlay_forbidden")

    scope = row["repair_scope"]
    require(scope["lineage_completeness_status"] == "COMPLETE_FOR_AUTHORIZED_REPAIR", "lineage_gate_incomplete")
    require(scope["preserved_unrelated_structure"] is True, "unrelated_structure_not_preserved")
    require(scope["allowed_repair_operations"], "allowed_repair_operations_missing")
    require(scope["reopened_model_call_refs"], "reopened_calls_missing")
    require(scope["recomputed_descendant_refs"], "recomputed_descendants_missing")
    require(scope["preserved_unrelated_refs"], "preserved_unrelated_refs_missing")
    require(scope["verification_hash"], "verification_hash_missing")

    dims = {entry["dimension"] for entry in row["engineering_semantic_ledger"]}
    require(REQUIRED_LEDGER_DIMENSIONS <= dims, "engineering_semantic_ledger_incomplete")
    for entry in row["engineering_semantic_ledger"]:
        require(entry.get("structural_fact"), "ledger_structural_fact_missing")
        require(entry.get("engineering_semantic_meaning"), "ledger_meaning_missing")
        require(entry.get("evidence_refs"), "ledger_evidence_refs_missing")

    contrast = row["p_vs_s_semantic_contrast"]
    require(contrast["intervention_mode_semantic_distinction"] == "SUPPORTED", "mode_distinction_invalid")
    require(contrast["intervention_superiority"] == "NOT_ESTABLISHED", "superiority_boundary_invalid")

    if scope["old_lineage_reentry_detected"]:
        require(
            row["engineering_case_class"]
            == "REPAIR_RECONVERGENCE_WITH_FRESH_AUTHORITY_REGENERATION",
            "structural_reentry_requires_fresh_regeneration_class",
        )
        marker = contrast["old_fact_reentry_semantic_interpretation"].upper()
        require(
            "SEMANTICALLY_REDERIVED" in marker or "FRESH" in marker,
            "reentry_semantic_rederivation_marker_missing",
        )

    require(row["audit_hash"] == hash_without(row, "audit_hash"), "engineering_audit_hash_mismatch")


def validate_bundle(bundle: dict[str, Any]) -> None:
    require(bundle.get("schema") == BUNDLE_SCHEMA, "engineering_bundle_schema_invalid")
    require(bundle["status"] == "READY_FOR_ENGINEERING_REPORT_DRAFT", "engineering_report_gate_not_ready")
    require(
        bundle["engineering_report_standard"]
        == "RB-PROCESS-REALITY-ENGINEERING-REPORT-STANDARD-v1.3",
        "engineering_report_standard_binding_invalid",
    )
    require(bundle["report_standard"] == "RB-PROCESS-REALITY-REPORT-STANDARD-v1.8", "report_standard_binding_invalid")
    require(bundle["candidate_case_count"] == 4, "bundle_case_count_invalid")
    require(len(bundle["case_audit_refs"]) == 4, "bundle_case_audit_ref_count_invalid")
    require({row["case_id"] for row in bundle["case_audit_refs"]} == EXPECTED_CASES, "bundle_case_set_invalid")
    require(len(bundle["recommended_report_family"]) == 4, "engineering_report_family_count_invalid")
    require(len(bundle["required_central_visuals"]) >= 4, "engineering_visual_contract_incomplete")
    support = bundle["aggregate_structural_support"]
    require(support["persistent_direct_exposure_count"] == 32, "bundle_persistent_exposure_invalid")
    require(support["persistent_reinjection_count"] == 28, "bundle_reinjection_invalid")
    require(support["structured_repair_preserved_unrelated_case_count"] == 4, "bundle_preservation_invalid")
    require(support["structural_old_fact_reentry_case_count"] == 1, "bundle_reentry_invalid")
    require(support["semantic_blind_restoration_case_count"] == 0, "bundle_blind_restore_invalid")
    require(support["material_divergence_case_count"] == 2, "bundle_divergence_invalid")
    require(support["reconvergence_after_recompute_case_count"] == 2, "bundle_reconvergence_invalid")
    require(support["fixed_horizon_censored_trace_count"] == 8, "bundle_censor_invalid")
    require(bundle["new_provider_calls"] == 0, "bundle_provider_calls_nonzero")
    require(bundle["new_paid_evaluator_calls"] == 0, "bundle_evaluator_calls_nonzero")
    require(bundle["subject_reruns"] == 0, "bundle_subject_reruns_nonzero")
    require(bundle["raw_evidence_mutated"] is False, "bundle_raw_mutated")
    require(bundle["bundle_hash"] == hash_without(bundle, "bundle_hash"), "bundle_hash_mismatch")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit")
    ap.add_argument("--bundle")
    args = ap.parse_args()

    validate_contracts()
    if args.audit:
        validate_audit(load(args.audit))
        print("ENGINEERING_STRUCTURAL_SEMANTIC_AUDIT=PASS")
    if args.bundle:
        validate_bundle(load(args.bundle))
        print("ENGINEERING_REPORT_EVIDENCE_BUNDLE=PASS")

    print("R5_R7_ENGINEERING_STRUCTURAL_SEMANTIC_CONTRACT=PASS")
    print("R5=PROBE_NOT_REPAIR")
    print("R6=REPAIR_READINESS_NOT_REPAIR")
    print("R7_P=EXTERNAL_CORRECTION_NOT_INTERNAL_REPAIR")
    print("R7_S=STRUCTURAL_REPAIR")
    print("SAME_ENDPOINT_NE_SAME_ENGINEERING_PROCESS=YES")
    print("STRUCTURAL_RECOMPUTATION_NE_SEMANTIC_NOVELTY=YES")
    print("CPR=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
