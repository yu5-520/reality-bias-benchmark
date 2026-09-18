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
        # v5 migration base
        "theory/theory_contract_v0.11.md",
        "docs/R_Plan_v5.0.md",
        "docs/v5_structural_observability_contract_v0.1.md",
        "schemas/semantic_audit_record_v0.2.schema.json",
        # v5.1 forward layer
        "theory/theory_contract_v0.12.md",
        "theory/change_notes/CN-R-060_semantic_lineage_scoped_repair.md",
        "docs/R_Plan_v5.1.md",
        "docs/first_paper_v5_1_scope.md",
        "docs/paper_structure_theory_engineering_future_v0.1.md",
        "docs/R6_semantic_lineage_repair_anchor_protocol_v1.1.md",
        "docs/R7_semantic_lineage_scoped_recovery_protocol_v1.1.md",
        "docs/R7_process_integrity_engineering_profile_v0.3.md",
        "docs/semantic_lineage_repair_contract_v0.1.md",
        "docs/reporting/process_reality_report_standard_v1_6.md",
        "docs/reporting/process_reality_theory_experiment_report_standard_v1_0.md",
        "docs/reporting/process_reality_engineering_experiment_report_standard_v1_0.md",
        "schemas/semantic_lineage_closure_v0.1.schema.json",
        "schemas/lineage_completeness_gate_v0.1.schema.json",
        "schemas/semantic_repair_packet_v0.1.schema.json",
        "schemas/process_integrity_lineage_record_v0.4.schema.json",
        "schemas/process_integrity_relation_evidence_v0.2.schema.json",
        "configs/r7_process_integrity_engineering_contract_v0.3.json",
        "configs/first_paper_mechanism_contract_v0.9.json",
        "configs/first_paper_analysis_contract_v0.9.json",
        "configs/v5_whole_process_ecommerce_batch001_v0.2.json",
        "configs/v5_whole_process_subject_gate_v0.2.json",
        "docs/v5_fresh_whole_process_design_v0.2.md",
        "configs/r5r6_engineering_package_source_binding_v0.1.json",
        "arena/r5r6_engineering_package.py",
        "arena/tests/test_r5r6_engineering_package.py",
        "docs/reports/2026-09-18/R5-R6_Engineering_Experiment_Report_v1.md",
    ]
    for path in required_files:
        require((ROOT / path).exists(), f"missing required v5/v5.1 file: {path}")

    # Historical freeze remains intact.
    legacy = load_json("manifests/r6d_specificity_preexecution_design_freeze_2026-09-17_v0_1.json")
    require(legacy["design_hash"] == LEGACY_R6D_DESIGN_HASH, "legacy R6-D design hash changed")

    migration = load_json("manifests/process_reality_v5_methodological_migration_2026-09-18.json")
    require(migration["legacy_layer"]["evidence_mutated"] is False, "migration may not mutate historical evidence")
    require(migration["provider_run_authorized"] is False, "migration may not authorize provider run")

    mechanism = load_json("configs/first_paper_mechanism_contract_v0.9.json")
    require(mechanism["theory_layer"]["formation_path_fixed_across_runs"] is False, "dynamic formation guard missing")
    require(mechanism["theory_layer"]["first_structural_support_required_for_engineering"] is False, "first support still mandatory")
    require(mechanism["theory_layer"]["first_pool_entry_required_for_engineering"] is False, "first pool still mandatory")
    require(mechanism["engineering_layer"]["repair_anchor_selection_basis"] == "REPAIR_EFFICIENCY_NOT_CAUSAL_PRIMACY", "Repair Anchor selection boundary missing")
    require(mechanism["engineering_layer"]["locality_definition"] == "LOCAL_BY_SEMANTIC_SCOPE", "semantic-scope locality missing")
    require(mechanism["engineering_layer"]["complete_relevant_semantic_lineage_required"] is True, "complete relevant lineage not required")
    require(mechanism["engineering_layer"]["unrelated_task_semantics_required"] is False, "unrelated semantics incorrectly required")
    require(mechanism["engineering_layer"]["lineage_gap_blocks_automatic_repair"] is True, "LINEAGE_GAP must block repair")
    require(mechanism["engineering_layer"]["repair_agent_may_invent_missing_lineage_as_fact"] is False, "repair agent guessing allowed")

    analysis = load_json("configs/first_paper_analysis_contract_v0.9.json")
    require(analysis["locality"]["by_semantic_scope"] is True, "analysis locality must be semantic")
    require(analysis["locality"]["by_trace_depth"] is False, "analysis locality must not be shallow-trace based")
    require("FIRST_STABLE_POOL_ENTRY" in analysis["optional_mechanism_observables"], "first pool must remain optional mechanism observable")
    require("SEMANTIC_LINEAGE_CLOSURE" in analysis["engineering_analysis_objects"], "semantic lineage closure missing")
    require("LINEAGE_COMPLETENESS_GATE" in analysis["engineering_analysis_objects"], "completeness gate missing")

    engineering = load_json("configs/r7_process_integrity_engineering_contract_v0.3.json")
    require(engineering["locality"]["definition"] == "LOCAL_BY_SEMANTIC_SCOPE", "engineering locality mismatch")
    require(engineering["locality"]["complete_relevant_history_required"] is True, "relevant history completeness missing")
    require(engineering["locality"]["unrelated_semantic_branches_excluded_by_default"] is True, "unrelated branch exclusion missing")
    require(engineering["repair_anchor"]["causal_primacy_required"] is False, "Repair Anchor incorrectly requires causal primacy")
    require("LINEAGE_GAP" in engineering["completeness_gate"]["blocks_automatic_repair_on"], "LINEAGE_GAP not blocking repair")
    require(engineering["completeness_gate"]["repair_agent_may_invent_missing_lineage_as_fact"] is False, "repair guessing guard missing")

    batch = load_json("configs/v5_whole_process_ecommerce_batch001_v0.2.json")
    require(batch["paid_subject_execution_authorized"] is False, "fresh design may not authorize provider")
    require("STRUCTURAL_REPAIR_ANCHOR_CANDIDATES" in batch["engineering_core_outputs"], "Repair Anchor output missing")
    require("CONTENT_ADDRESS_INDEX" in batch["engineering_core_outputs"], "content address output missing")
    require("SEMANTIC_LINEAGE_RECOVERABILITY_STATUS" in batch["engineering_core_outputs"], "lineage recoverability output missing")
    require("FIRST_STRUCTURAL_SUPPORT_CANDIDATE" in batch["optional_mechanism_observables"], "first support not preserved as optional mechanism data")
    require(batch["semantic_boundaries"]["first_node_localization_required_for_engineering"] is False, "first-node engineering dependency remains")
    require(batch["semantic_boundaries"]["repair_anchor_is_semantic_origin"] is False, "Repair Anchor/origin boundary missing")
    require(batch["semantic_boundaries"]["content_address_proves_semantic_use"] is False, "content address/semantic-use boundary missing")

    gate = load_json("configs/v5_whole_process_subject_gate_v0.2.json")
    require(gate["provider_execution_authorized"] is False, "subject gate may not authorize provider")
    require(gate["active_recovery_authorized"] is False, "subject gate may not authorize recovery")

    lineage = load_json("schemas/process_integrity_lineage_record_v0.4.schema.json")
    required_lineage = set(lineage["required"])
    for field in [
        "repair_anchor_ref","target_semantic_id","content_address","trace_root_ref",
        "semantic_lineage_closure_ref","lineage_completeness_status",
        "evidence_supported_affected_closure","repair_closure","preserved_unrelated_refs",
    ]:
        require(field in required_lineage, f"lineage required field missing: {field}")

    closure = load_json("schemas/semantic_lineage_closure_v0.1.schema.json")
    closure_required = set(closure["required"])
    for field in ["source_refs","transformation_refs","pool_state_refs","relevant_descendant_refs","excluded_unrelated_refs","completeness_status"]:
        require(field in closure_required, f"SemanticLineageClosure required field missing: {field}")

    completeness = load_json("schemas/lineage_completeness_gate_v0.1.schema.json")
    statuses = set(completeness["properties"]["status"]["enum"])
    require("LINEAGE_GAP" in statuses, "LINEAGE_GAP enum missing")

    packet = load_json("schemas/semantic_repair_packet_v0.1.schema.json")
    require("semantic_lineage_closure_ref" in packet["required"], "repair packet missing semantic lineage closure")
    require("lineage_completeness_gate_ref" in packet["required"], "repair packet missing completeness gate")
    require("preserved_unrelated_refs" in packet["required"], "repair packet missing unrelated preservation")

    require_tokens("theory/theory_contract_v0.12.md", [
        "Dynamic formation",
        "Structural Repair Anchor",
        "semantic scope",
        "LINEAGE_GAP",
    ])
    require_tokens("docs/R_Plan_v5.1.md", [
        "Repair Anchor -> Content Address -> Semantic Lineage Closure -> Completeness Gate",
        "First support / first pool / first exposure remain optional mechanism observables",
        "Theory Experiment Report",
        "Engineering Experiment Report",
    ])
    require_tokens("docs/R7_semantic_lineage_scoped_recovery_protocol_v1.1.md", [
        "complete relevant semantic history + minimal unrelated context",
        "LINEAGE_GAP",
        "Missing semantic history must not be reconstructed as historical fact",
    ])
    require_tokens("docs/reports/2026-09-18/R5-R6_Engineering_Experiment_Report_v1.md", [
        "COMPLETE_FOR_AUTHORIZED_REPAIR",
        "READY_FOR_SEPARATE_AUTHORIZATION",
        "Repair Anchor != Semantic Origin",
        "R7 READY FOR SEPARATE AUTHORIZATION",
    ])
    require_tokens("README.md", [
        "Process Reality v5.1",
        "Semantic Lineage Closure",
        "LINEAGE_GAP",
        "Theory Experiment Report",
        "Engineering Experiment Report",
    ])

    print("PASS: Process Reality v5.1 semantic-lineage scoped repair layer is synchronized")
    print(f"LEGACY_R6D_DESIGN_HASH={LEGACY_R6D_DESIGN_HASH}")
    print("HISTORICAL_EVIDENCE_MUTATED=NO")
    print("SCIENTIFIC_PROVIDER_RUN_AUTHORIZED=NO")
    print("ACTIVE_RECOVERY_AUTHORIZED=NO")
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
