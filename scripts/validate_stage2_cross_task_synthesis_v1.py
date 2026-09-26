#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPORT = ROOT / "docs/reports/2026-09-26/StageII_Cross_Task_Cross_Layer_Synthesis_and_Paper_Extraction_v1.md"
BUNDLE = ROOT / "configs/stage2_cross_task_synthesis_evidence_bundle_v1.json"
REGISTRY = ROOT / "configs/stage2_paper_figure_table_registry_v1.json"
SCHEMA = ROOT / "schemas/process_reality_report_evidence_bundle_v0.2.schema.json"
STANDARD = ROOT / "docs/reporting/process_reality_report_standard_v1_10.md"
GENERAL = ROOT / "configs/stage2_general_chapter_claim_registry_v1.json"
AUDIT_INDEX = ROOT / "stage2/natural_v7/r6_grade_semantic_audit/audit_index.json"
LEDGERS = ROOT / "stage2/natural_v7/r6_grade_semantic_audit/case_semantic_ledgers.jsonl"
CROSS_AUDIT = ROOT / "stage2/natural_v7/cross_task_cross_layer_audit.json"

EXPECTED_METHODS = {f"GC-M{i}" for i in range(1,6)}
EXPECTED_SYSTEMS = {f"X{i}" for i in range(1,8)}
EXPECTED_TASKS = {"T1","T2","T3"}
EXPECTED_SELECTED = {
    "X1-T2","X2-T2","X3-T2","X3-T3","X4-T3",
    "X5-T3","X6-T1","X6-T3","X7-T2","X7-T3",
}

def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> None:
    report = REPORT.read_text(encoding="utf-8")
    bundle = load_json(BUNDLE)
    registry = load_json(REGISTRY)
    schema = load_json(SCHEMA)
    general = load_json(GENERAL)
    audit = load_json(AUDIT_INDEX)
    cross = load_json(CROSS_AUDIT)
    ledgers = [json.loads(line) for line in LEDGERS.read_text(encoding="utf-8").splitlines() if line.strip()]
    ledger_by_cell = {row["cell"]: row for row in ledgers}
    audit_by_cell = {row["cell"]: row for row in audit["cells"]}

    require(schema["$id"] == "RB-PROCESS-REALITY-REPORT-EVIDENCE-BUNDLE-v0.2", "bundle schema id mismatch")
    require(bundle["schema"] == schema["$id"], "bundle schema mismatch")
    require(bundle["report_family"] == "STAGE2_SYNTHESIS", "wrong report family")
    require(bundle["reporting_standard"] == "RB-PROCESS-REALITY-REPORT-STANDARD-v1.10", "report standard mismatch")
    require(bundle["report_gate_status"] == "READY_FOR_REPORT_FREEZE", "synthesis bundle not ready")
    require(bundle["experiment_accounting"]["natural_cells"] == 21, "natural cell count mismatch")
    require(bundle["experiment_accounting"]["natural_reruns"] == 0, "natural rerun count must be zero")
    require(bundle["experiment_accounting"]["selected_source_bound_cases"] == 10, "selected case count mismatch")
    require(bundle["experiment_accounting"]["contrasts_spent_by_report"] == 0, "synthesis may not spend contrast")
    require(bundle["provenance"]["raw_evidence_mutation"] is False, "raw evidence mutation forbidden")
    require(bundle["provenance"]["missing_events_reconstructed"] is False, "missing event reconstruction forbidden")
    require(bundle["provenance"]["new_subject_provider_evaluator_calls_for_report"] == 0, "synthesis may not call subject/provider/evaluator")

    method_ids = set(bundle["general_chapter"]["adopted_methodological_ids"])
    require(method_ids == EXPECTED_METHODS, "synthesis must adopt GC-M1..GC-M5")
    general_ids = {row["id"] for row in general["claims"]}
    require(method_ids <= general_ids, "unknown General Chapter method ID")
    require(set(bundle["general_chapter"]["hypotheses_informed"]) <= general_ids, "unknown General Chapter hypothesis ID")
    require(bundle["general_chapter"]["anti_circularity_acknowledged"] is True, "anti-circularity acknowledgement missing")

    require(set(bundle["domain_scope"]["systems"]) == EXPECTED_SYSTEMS, "all seven systems must remain in synthesis scope")
    require(set(bundle["domain_scope"]["task_families"]) == EXPECTED_TASKS, "T1-T3 must remain in synthesis scope")

    selected = {row["case_id"] for row in bundle["trajectory_cases"]}
    require(selected == EXPECTED_SELECTED, f"selected synthesis case set mismatch: {sorted(selected ^ EXPECTED_SELECTED)}")
    for case in bundle["trajectory_cases"]:
        cell = case["case_id"]
        require(cell in ledger_by_cell and cell in audit_by_cell, f"{cell}: missing frozen semantic source")
        led = ledger_by_cell[cell]
        idx = audit_by_cell[cell]
        require(case["coverage_status"] == idx["coverage_status"], f"{cell}: coverage mismatch")
        require(case["route_material_ref"] == idx["material_ref"], f"{cell}: route material mismatch")
        require(case["route_representation"] == led["complete_route_accounting"]["route_representation"], f"{cell}: route representation mismatch")
        manifest = load_json(ROOT / case["raw_manifest_ref"])
        require(manifest["tar_sha256"] == case["archive_sha256"], f"{cell}: raw archive hash mismatch")
        require(manifest["natural_attempts_for_cell"] == 1, f"{cell}: not a frozen first attempt")

    require(audit["natural_cells"] == 21 and audit["natural_reruns"] == 0, "whole-matrix accounting changed")
    require(audit["material_accounting"]["runner_route_nodes"] == 482, "route-node count changed")
    require(audit["material_accounting"]["passive_native_events"] == 1202, "native-event count changed")
    require(audit["material_accounting"]["textual_observer_members"] == 840, "textual observer count changed")
    require(audit["material_accounting"]["frozen_checkout_file_entries"] == 299, "checkout-file count changed")

    by_task = {"T1":{"nodes":0,"edges":0},"T2":{"nodes":0,"edges":0},"T3":{"nodes":0,"edges":0}}
    total_nodes = total_edges = 0
    for row in ledgers:
        n = len(row["semantic_nodes"])
        e = len(row["semantic_edges"])
        by_task[row["task_id"]]["nodes"] += n
        by_task[row["task_id"]]["edges"] += e
        total_nodes += n
        total_edges += e
    require(total_nodes == 70 and total_edges == 46, "semantic total changed")
    require(by_task == {"T1":{"nodes":21,"edges":12},"T2":{"nodes":23,"edges":15},"T3":{"nodes":26,"edges":19}}, f"task semantic counts changed: {by_task}")
    require(bundle["semantic_summary"]["total_semantic_nodes"] == total_nodes, "bundle semantic-node total mismatch")
    require(bundle["semantic_summary"]["total_semantic_edges"] == total_edges, "bundle semantic-edge total mismatch")
    require(bundle["semantic_summary"]["task_semantic_counts"] == by_task, "bundle task semantic counts mismatch")

    require(cross["state"]["natural_matrix"] == "21_OF_21_COMPLETE", "cross-task audit natural matrix changed")
    require(cross["state"]["natural_reruns"] == 0, "cross-task audit rerun count changed")

    # Complete paired source-route requirement for the primary synthesis mechanism figure.
    x3t2 = load_json(ROOT / "stage2/natural_v7/r6_grade_material/X3-T2.json")
    x3t3 = load_json(ROOT / "stage2/natural_v7/r6_grade_material/X3-T3.json")
    require(len(x3t2["route_skeleton"]) == 32 and len(x3t3["route_skeleton"]) == 32, "paired X3 route length changed")
    for i in range(1,33):
        require(f"A{i:02d}" in report, f"X3-T2 source route missing A{i:02d}")
        require(f"B{i:02d}" in report, f"X3-T3 source route missing B{i:02d}")

    fig_specs = {row["figure_id"]: row for row in bundle["figure_specs"]}
    require(fig_specs["FIG-S2SYN-P2"]["figure_type"] == "TIME_ALIGNED_ACTUAL_AGENT_ROUTE_WITH_SEMANTIC_LINEAGE_OVERLAY", "P2 figure type mismatch")
    require(fig_specs["FIG-S2SYN-P2"]["all_recorded_route_nodes_required"] is True, "P2 complete-route requirement missing")

    claim_ids = {row["claim_id"] for row in bundle["claim_registry"]}
    require(claim_ids == {f"S2SYN-C{i}" for i in range(1,9)}, "synthesis claim registry mismatch")

    require(registry["schema"] == "stage2-paper-figure-table-registry-v1", "paper registry schema mismatch")
    require(registry["state"] == "FROZEN_SOURCE_BINDING", "paper registry not frozen")
    require({f["id"] for f in registry["figures"]} == {"FIG-P1","FIG-P2","FIG-P3","FIG-P4"}, "paper figure set mismatch")
    require({t["id"] for t in registry["tables"]} == {"TABLE-P1","TABLE-P2"}, "paper table set mismatch")
    for item in registry["figures"] + registry["tables"]:
        require(set(item["claim_ids"]) <= claim_ids, f"{item['id']}: unknown synthesis claim id")

    required_report_strings = [
        "From Heterogeneous Native Execution to a Paper-Facing Process-Reality Evidence Architecture",
        "source / artifact state",
        "C → P",
        "P → C",
        "C → R",
        "R → P",
        "memory presence ≠ inherited inertia",
        "same endpoint ≠ same process",
        "different process ≠ automatically worse process",
        "Stage I supplies mechanism depth. Stage II supplies cross-system breadth.",
        "C3/C4 should remain reserve evidence",
        "configs/stage2_paper_figure_table_registry_v1.json",
        "TIME_ALIGNED_ACTUAL_AGENT_ROUTE_WITH_SEMANTIC_LINEAGE_OVERLAY",
        "no framework ranking",
    ]
    for s in required_report_strings:
        require(s in report, f"report missing required synthesis text: {s}")

    require("TIME_ALIGNED_ACTUAL_AGENT_ROUTE_WITH_SEMANTIC_LINEAGE_OVERLAY" in STANDARD.read_text(encoding="utf-8"), "report standard route rule missing")

    for child in [
        ROOT / "docs/reports/2026-09-26/StageII_Child01_Native_Heterogeneous_Execution_and_Process_Reality_Report_v1.md",
        ROOT / "docs/reports/2026-09-26/StageII_Child02_T2_Implementation_Process_Expansion_and_Closure_Deferral_Report_v1.md",
        ROOT / "docs/reports/2026-09-26/StageII_Child03_T3_Functional_Cut_Historical_Residue_and_Semantic_Closure_Report_v1.md",
    ]:
        require(child.exists(), f"required frozen child report missing: {child.name}")

    print("PASS: Stage-II cross-task/cross-layer synthesis is source-bound, paper-extraction-bound, route-complete for the paired X3 source figure, and claim-bounded")
    print("NATURAL_CELLS=21")
    print("NATURAL_RERUNS=0")
    print("SEMANTIC_NODES=70")
    print("SEMANTIC_EDGES=46")
    print("PAPER_FIGURES=4")
    print("PAPER_TABLES=2")
    print("NEW_SUBJECT_PROVIDER_EVALUATOR_CALLS=0")
    print("NEW_CONTRASTS=0")

if __name__ == "__main__":
    main()
