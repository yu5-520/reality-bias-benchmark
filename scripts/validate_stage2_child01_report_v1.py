#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPORT = ROOT / "docs/reports/2026-09-26/StageII_Child01_Native_Heterogeneous_Execution_and_Process_Reality_Report_v1.md"
BUNDLE = ROOT / "configs/stage2_child01_report_evidence_bundle_v1.json"
SCHEMA = ROOT / "schemas/process_reality_report_evidence_bundle_v0.2.schema.json"
STANDARD = ROOT / "docs/reporting/process_reality_report_standard_v1_10.md"
GENERAL = ROOT / "configs/stage2_general_chapter_claim_registry_v1.json"
AUDIT_INDEX = ROOT / "stage2/natural_v7/r6_grade_semantic_audit/audit_index.json"
LEDGERS = ROOT / "stage2/natural_v7/r6_grade_semantic_audit/case_semantic_ledgers.jsonl"

EXPECTED_CASES = {
    "X1-T2","X2-T2","X3-T2","X3-T3","X4-T3","X5-T3","X6-T1","X6-T3","X7-T3"
}
EXPECTED_SYSTEMS = {f"X{i}" for i in range(1,8)}
EXPECTED_METHODS = {f"GC-M{i}" for i in range(1,6)}

def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> None:
    report = REPORT.read_text(encoding="utf-8")
    bundle = load_json(BUNDLE)
    schema = load_json(SCHEMA)
    general = load_json(GENERAL)
    audit = load_json(AUDIT_INDEX)
    ledgers = [json.loads(line) for line in LEDGERS.read_text(encoding="utf-8").splitlines() if line.strip()]
    ledger_by_cell = {row["cell"]: row for row in ledgers}
    audit_by_cell = {row["cell"]: row for row in audit["cells"]}

    require(schema["$id"] == "RB-PROCESS-REALITY-REPORT-EVIDENCE-BUNDLE-v0.2", "stage2 bundle schema id mismatch")
    require(bundle["schema"] == schema["$id"], "bundle schema mismatch")
    require(bundle["reporting_standard"] == "RB-PROCESS-REALITY-REPORT-STANDARD-v1.10", "report standard mismatch")
    require(bundle["report_gate_status"] == "READY_FOR_REPORT_FREEZE", "report bundle not ready")
    require(bundle["experiment_accounting"]["natural_cells"] == 21, "natural cell count mismatch")
    require(bundle["experiment_accounting"]["natural_reruns"] == 0, "natural rerun count must be zero")
    require(bundle["experiment_accounting"]["contrasts_spent_by_report"] == 0, "report may not spend contrast")
    require(bundle["provenance"]["raw_evidence_mutation"] is False, "raw evidence mutation forbidden")
    require(bundle["provenance"]["missing_events_reconstructed"] is False, "missing event reconstruction forbidden")
    require(bundle["provenance"]["new_subject_provider_evaluator_calls_for_report"] == 0, "reporting may not call subject/provider/evaluator")

    method_ids = set(bundle["general_chapter"]["adopted_methodological_ids"])
    require(method_ids == EXPECTED_METHODS, "child report must adopt GC-M1..GC-M5")
    general_ids = {row["id"] for row in general["claims"]}
    require(method_ids <= general_ids, "unknown General Chapter method ID")
    require(set(bundle["general_chapter"]["hypotheses_informed"]) <= general_ids, "unknown General Chapter hypothesis ID")
    require(bundle["general_chapter"]["anti_circularity_acknowledged"] is True, "anti-circularity acknowledgement missing")

    cases = bundle["trajectory_cases"]
    case_ids = {row["case_id"] for row in cases}
    require(case_ids == EXPECTED_CASES, f"selected case set mismatch: {sorted(case_ids ^ EXPECTED_CASES)}")
    require({row["system_id"] for row in cases} == EXPECTED_SYSTEMS, "all seven systems must be represented")
    require(bundle["experiment_accounting"]["selected_source_bound_cases"] == len(cases), "selected case accounting mismatch")

    for case in cases:
        cell = case["case_id"]
        require(cell in audit_by_cell, f"{cell}: absent from audit index")
        require(cell in ledger_by_cell, f"{cell}: absent from semantic ledgers")
        idx = audit_by_cell[cell]
        led = ledger_by_cell[cell]
        require(case["coverage_status"] == idx["coverage_status"], f"{cell}: coverage mismatch")
        require(case["route_material_ref"] == idx["material_ref"], f"{cell}: material ref mismatch")
        require(case["route_representation"] == led["complete_route_accounting"]["route_representation"], f"{cell}: route representation mismatch")
        require(case["complete_recorded_route"] is True, f"{cell}: complete route flag missing")
        require(case["semantic_lineage_overlay_present"] is True, f"{cell}: semantic overlay flag missing")
        manifest = load_json(ROOT / case["raw_manifest_ref"])
        require(manifest["tar_sha256"] == case["archive_sha256"], f"{cell}: raw archive hash mismatch")
        require(manifest["natural_attempts_for_cell"] == 1, f"{cell}: not a single first attempt")
        for node in led["semantic_nodes"]:
            require(node["node_id"] in report, f"{cell}: semantic node absent from report: {node['node_id']}")
        for edge in led["semantic_edges"]:
            require(edge["edge_id"] in report, f"{cell}: semantic edge absent from report: {edge['edge_id']}")

    # Primary complete route figure must visibly carry every recorded route node.
    x3t2 = load_json(ROOT / "stage2/natural_v7/r6_grade_material/X3-T2.json")
    require(len(x3t2["route_skeleton"]) == 32, "X3-T2 route length changed")
    for i in range(1,33):
        require(f"R{i:02d}" in report, f"X3-T2 figure missing route node R{i:02d}")

    x3t3 = load_json(ROOT / "stage2/natural_v7/r6_grade_material/X3-T3.json")
    require(len(x3t3["route_skeleton"]) == 32, "X3-T3 route length changed")
    for i in range(1,33):
        require(f"B{i:02d}" in report, f"X3-T3 figure missing route node B{i:02d}")

    required_report_strings = [
        "Relation to Stage-II General Chapter",
        "General Chapter question / definition → child source-bound evidence → bounded child finding.",
        "A terminal functional state is an endpoint measurement; it is not a substitute for the process lineage that produced it.",
        "Observed process difference is not, by itself, evidence of inferior system quality.",
        "no framework superiority",
        "C3/C4 unspent",
        "RB-PROCESS-REALITY-REPORT-STANDARD-v1.10",
        "RB-PROCESS-REALITY-REPORT-EVIDENCE-BUNDLE-v0.2",
    ]
    for s in required_report_strings:
        require(s in report, f"report missing required text: {s}")

    require("TIME_ALIGNED_ACTUAL_AGENT_ROUTE_WITH_SEMANTIC_LINEAGE_OVERLAY" in STANDARD.read_text(encoding="utf-8"), "v1.10 primary visual rule missing")
    require(any(f["figure_type"] == "TIME_ALIGNED_ACTUAL_AGENT_ROUTE_WITH_SEMANTIC_LINEAGE_OVERLAY" and f["all_recorded_route_nodes_required"] for f in bundle["figure_specs"]), "primary complete-route figure spec missing")

    require(audit["natural_cells"] == 21 and audit["natural_reruns"] == 0 and audit["subject_calls"] == 0, "R6-grade audit accounting changed")
    require(audit["material_accounting"]["runner_route_nodes"] == 482, "route-node accounting changed")
    require(audit["material_accounting"]["passive_native_events"] == 1202, "native-event accounting changed")
    require(audit["material_accounting"]["textual_observer_members"] == 840, "observer-artifact accounting changed")
    require(audit["material_accounting"]["frozen_checkout_file_entries"] == 299, "checkout-file accounting changed")

    print("PASS: Stage-II Child Report 01 is source-bound, route-complete for primary figures, semantically complete for selected cases, and claim-bounded")
    print("NATURAL_CELLS=21")
    print("NATURAL_RERUNS=0")
    print("SELECTED_CASES=9")
    print("NEW_SUBJECT_PROVIDER_EVALUATOR_CALLS=0")
    print("NEW_CONTRASTS=0")

if __name__ == "__main__":
    main()
