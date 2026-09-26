#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPORT = ROOT / "docs/reports/2026-09-26/StageII_Child03_T3_Functional_Cut_Historical_Residue_and_Semantic_Closure_Report_v1.md"
BUNDLE = ROOT / "configs/stage2_child03_t3_report_evidence_bundle_v1.json"
SCHEMA = ROOT / "schemas/process_reality_report_evidence_bundle_v0.2.schema.json"
STANDARD = ROOT / "docs/reporting/process_reality_report_standard_v1_10.md"
GENERAL = ROOT / "configs/stage2_general_chapter_claim_registry_v1.json"
AUDIT_INDEX = ROOT / "stage2/natural_v7/r6_grade_semantic_audit/audit_index.json"
LEDGERS = ROOT / "stage2/natural_v7/r6_grade_semantic_audit/case_semantic_ledgers.jsonl"
T3_AUDIT = ROOT / "stage2/natural_v7/T3_posthoc_audit.json"

EXPECTED_CASES = {f"X{i}-T3" for i in range(1,8)}
EXPECTED_SYSTEMS = {f"X{i}" for i in range(1,8)}
EXPECTED_METHODS = {f"GC-M{i}" for i in range(1,6)}
EXPECTED_HYPOTHESES = {"GC-H1a","GC-H2c","GC-H3a","GC-H3b","GC-H3c"}

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
    t3 = load_json(T3_AUDIT)
    ledgers = [json.loads(line) for line in LEDGERS.read_text(encoding="utf-8").splitlines() if line.strip()]
    ledger_by_cell = {row["cell"]: row for row in ledgers}
    audit_by_cell = {row["cell"]: row for row in audit["cells"]}

    require(schema["$id"] == "RB-PROCESS-REALITY-REPORT-EVIDENCE-BUNDLE-v0.2", "stage2 bundle schema id mismatch")
    require(bundle["schema"] == schema["$id"], "bundle schema mismatch")
    require(bundle["report_family"] == "STAGE2_TASK_PRESSURE", "wrong report family")
    require(bundle["reporting_standard"] == "RB-PROCESS-REALITY-REPORT-STANDARD-v1.10", "report standard mismatch")
    require(bundle["report_gate_status"] == "READY_FOR_REPORT_FREEZE", "report bundle not ready")
    require(bundle["experiment_accounting"]["natural_cells"] == 21, "Stage-II population count mismatch")
    require(bundle["experiment_accounting"]["natural_reruns"] == 0, "natural rerun count must be zero")
    require(bundle["experiment_accounting"]["selected_source_bound_cases"] == 7, "T3 selected case count mismatch")
    require(bundle["experiment_accounting"]["contrasts_spent_by_report"] == 0, "report may not spend contrast")
    require(bundle["provenance"]["raw_evidence_mutation"] is False, "raw evidence mutation forbidden")
    require(bundle["provenance"]["missing_events_reconstructed"] is False, "missing event reconstruction forbidden")
    require(bundle["provenance"]["new_subject_provider_evaluator_calls_for_report"] == 0, "reporting may not call subject/provider/evaluator")

    method_ids = set(bundle["general_chapter"]["adopted_methodological_ids"])
    require(method_ids == EXPECTED_METHODS, "child report must adopt GC-M1..GC-M5")
    require(set(bundle["general_chapter"]["hypotheses_informed"]) == EXPECTED_HYPOTHESES, "unexpected hypothesis binding")
    general_ids = {row["id"] for row in general["claims"]}
    require(method_ids <= general_ids, "unknown General Chapter method ID")
    require(EXPECTED_HYPOTHESES <= general_ids, "unknown General Chapter hypothesis ID")
    require(bundle["general_chapter"]["anti_circularity_acknowledged"] is True, "anti-circularity acknowledgement missing")

    cases = bundle["trajectory_cases"]
    case_ids = {row["case_id"] for row in cases}
    require(case_ids == EXPECTED_CASES, f"T3 case set mismatch: {sorted(case_ids ^ EXPECTED_CASES)}")
    require({row["system_id"] for row in cases} == EXPECTED_SYSTEMS, "all seven systems must be represented")
    require(set(bundle["domain_scope"]["task_families"]) == {"T3"}, "Child 03 must remain T3-scoped")

    total_route = total_native = total_textual = total_checkout = 0
    total_nodes = total_edges = 0
    for case in cases:
        cell = case["case_id"]
        require(cell in audit_by_cell, f"{cell}: absent from audit index")
        require(cell in ledger_by_cell, f"{cell}: absent from semantic ledgers")
        idx = audit_by_cell[cell]
        led = ledger_by_cell[cell]
        require(idx["task_family"] == "legacy_path_retirement", f"{cell}: not T3 legacy_path_retirement")
        require(case["coverage_status"] == idx["coverage_status"], f"{cell}: coverage mismatch")
        require(case["route_material_ref"] == idx["material_ref"], f"{cell}: material ref mismatch")
        require(case["route_representation"] == led["complete_route_accounting"]["route_representation"], f"{cell}: route representation mismatch")
        require(case["complete_recorded_route"] is True, f"{cell}: complete route flag missing")
        require(case["semantic_lineage_overlay_present"] is True, f"{cell}: semantic overlay flag missing")

        manifest = load_json(ROOT / case["raw_manifest_ref"])
        require(manifest["tar_sha256"] == case["archive_sha256"], f"{cell}: raw archive hash mismatch")
        require(manifest["natural_attempts_for_cell"] == 1, f"{cell}: not a single first attempt")

        material = load_json(ROOT / case["route_material_ref"])
        total_route += len(material.get("route_skeleton", []))
        total_native += len(material.get("native_events", []))
        total_textual += len(material.get("textual_observer_members", []))
        total_checkout += len(material.get("checkout_members", []))
        total_nodes += len(led["semantic_nodes"])
        total_edges += len(led["semantic_edges"])

        for node in led["semantic_nodes"]:
            require(node["node_id"] in report, f"{cell}: semantic node absent from report: {node['node_id']}")
        for edge in led["semantic_edges"]:
            require(edge["edge_id"] in report, f"{cell}: semantic edge absent from report: {edge['edge_id']}")

    require(total_route == 162, f"T3 route-node accounting changed: {total_route}")
    require(total_native == 392, f"T3 native-event accounting changed: {total_native}")
    require(total_textual == 536, f"T3 textual-artifact accounting changed: {total_textual}")
    require(total_checkout == 107, f"T3 checkout-file accounting changed: {total_checkout}")
    require(total_nodes == 26, f"T3 semantic-node accounting changed: {total_nodes}")
    require(total_edges == 19, f"T3 semantic-edge accounting changed: {total_edges}")

    structural = bundle["structural_summary"]
    require(structural["runner_route_nodes"] == total_route, "bundle route count mismatch")
    require(structural["passive_native_events"] == total_native, "bundle native-event count mismatch")
    require(structural["textual_observer_members"] == total_textual, "bundle textual count mismatch")
    require(structural["frozen_checkout_file_entries"] == total_checkout, "bundle checkout count mismatch")
    require(bundle["semantic_summary"]["total_semantic_nodes"] == total_nodes, "bundle semantic-node count mismatch")
    require(bundle["semantic_summary"]["total_semantic_edges"] == total_edges, "bundle semantic-edge count mismatch")

    x3 = load_json(ROOT / "stage2/natural_v7/r6_grade_material/X3-T3.json")
    require(len(x3["route_skeleton"]) == 32, "X3-T3 route length changed")
    for i in range(1,33):
        require(f"R{i:02d}" in report, f"X3-T3 primary figure missing route node R{i:02d}")

    require(t3["schema"] == "stage2-v7-t3-posthoc-audit-v1", "T3 posthoc schema changed")
    require(t3["cells"]["X3"]["legacy_compat_state"] == "EMPTY_FILE_REMAINS", "X3 historical residue state changed")
    require(t3["cells"]["X4"]["outcome"] == "FINALIZED_TURN_31", "X4 finalized state changed")
    require(t3["cells"]["X6"]["outcome"] == "FINALIZED_TURN_3", "X6 rapid-closure state changed")
    require(t3["evidence_state"]["natural_reruns"] == 0, "T3 natural rerun accounting changed")

    required_report_strings = [
        "Relation to Stage-II General Chapter",
        "General Chapter question / definition → child source-bound evidence → bounded child finding.",
        "A terminal functional state is an endpoint measurement; it is not a substitute for the process lineage that produced it.",
        "Observed process difference is not, by itself, evidence of inferior system quality.",
        "Functional deactivation is not equivalent to historical-state closure.",
        "no framework superiority",
        "C3/C4 unspent",
        "TIME_ALIGNED_ACTUAL_AGENT_ROUTE_WITH_SEMANTIC_LINEAGE_OVERLAY",
        "RB-PROCESS-REALITY-REPORT-STANDARD-v1.10",
        "RB-PROCESS-REALITY-REPORT-EVIDENCE-BUNDLE-v0.2",
    ]
    for s in required_report_strings:
        require(s in report, f"report missing required text: {s}")

    require("TIME_ALIGNED_ACTUAL_AGENT_ROUTE_WITH_SEMANTIC_LINEAGE_OVERLAY" in STANDARD.read_text(encoding="utf-8"), "v1.10 primary visual rule missing")
    require(any(f["figure_type"] == "TIME_ALIGNED_ACTUAL_AGENT_ROUTE_WITH_SEMANTIC_LINEAGE_OVERLAY" and f["all_recorded_route_nodes_required"] for f in bundle["figure_specs"]), "primary complete-route figure spec missing")

    print("PASS: Stage-II Child Report 03 is source-bound, T3-scoped, route-complete for the primary figure, semantically complete for all seven T3 cells, and claim-bounded")
    print("T3_NATURAL_CELLS=7")
    print("NATURAL_RERUNS=0")
    print("RUNNER_ROUTE_NODES=162")
    print("PASSIVE_NATIVE_EVENTS=392")
    print("TEXTUAL_OBSERVER_ARTIFACTS=536")
    print("SEMANTIC_NODES=26")
    print("SEMANTIC_EDGES=19")
    print("NEW_SUBJECT_PROVIDER_EVALUATOR_CALLS=0")
    print("NEW_CONTRASTS=0")

if __name__ == "__main__":
    main()
