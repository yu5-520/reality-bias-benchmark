from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "stage2/r7_monitor_v1"

SUMMARY = BASE / "summary.json"
SCAN = BASE / "candidate_scan_summary.json"
EVENTS = BASE / "normalized_structural_events.jsonl"
CANDIDATES = BASE / "structural_candidates.jsonl"
PACKAGES = BASE / "monitor_derived_repair_packages.jsonl"
PREFLIGHT = BASE / "parent_reconstruction_preflight.jsonl"
RULES = ROOT / "configs/stage2_r7_structural_monitor_rules_v1.json"
ASSEMBLY = ROOT / "configs/stage2_r7_package_assembly_rules_v1.json"
BOUNDARY = ROOT / "configs/stage2_r7_boundary_contract_v1.json"
FIREWALL = ROOT / "configs/stage2_r7_monitor_input_firewall_v1.json"
SOURCE = ROOT / "configs/stage2_r7_21_path_source_freeze_v1.json"
PACKAGE_SCHEMA = ROOT / "schemas/stage2_r7_monitor_derived_repair_package_v1.schema.json"
REPORT = BASE / "offline_prefix_replay_report_v1.md"
ASSEMBLY_REPORT = BASE / "package_assembly_report_v1.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def require(ok: bool, message: str):
    if not ok:
        raise AssertionError(message)


def main():
    summary = load(SUMMARY)
    scan = load(SCAN)
    rules = load(RULES)
    assembly = load(ASSEMBLY)
    boundary = load(BOUNDARY)
    firewall = load(FIREWALL)
    source = load(SOURCE)
    package_schema = load(PACKAGE_SCHEMA)
    events = load_jsonl(EVENTS)
    candidates = load_jsonl(CANDIDATES)
    packages = load_jsonl(PACKAGES)
    preflight = load_jsonl(PREFLIGHT)

    require(summary["schema"] == "RB-STAGE2-R7-STRUCTURAL-MONITOR-SUMMARY-v1", "summary schema")
    require(summary["status"] == "OFFLINE_PREFIX_REPLAY_AND_PACKAGE_ASSEMBLY_COMPLETE", "summary status")
    require(summary["source_cells"] == 21, "21 source cells")
    require(summary["natural_reruns"] == 0, "natural reruns")
    require(summary["semantic_audit_used_as_input"] is False, "semantic audit input")
    require(summary["cpr_labels_used_as_input"] is False, "CPR input")
    require(summary["future_evidence_used"] is False, "future leakage")
    require(summary["provider_calls"] == 0 and summary["evaluator_calls"] == 0, "offline only")
    require(summary["active_repair_authorized"] is False, "active repair must remain disabled")

    require(len(events) == 1120 == summary["normalized_event_count"], "normalized event count")
    require(len(candidates) == 244 == summary["structural_candidate_count"], "candidate count")
    require(len(packages) == 24 == summary["repair_package_count"], "assembled package count")
    require(len(preflight) == 24, "preflight count")
    require(summary["package_cells"] == 15, "package cell count")
    require(summary["cells_with_candidates"] == 15, "candidate cell count")

    require(rules["status"] == "FROZEN_BEFORE_CANONICAL_PREFIX_REPLAY", "monitor rules freeze")
    require(rules["future_blind"] is True, "monitor future blind")
    require(rules["case_specific_rules"] is False, "no case-specific monitor rules")
    require(rules["semantic_labels_used"] is False, "no semantic labels")
    require(assembly["status"] == "FROZEN_BEFORE_CANONICAL_PACKAGE_ASSEMBLY", "assembly rules freeze")
    require(assembly["semantic_audit_used"] is False, "assembly semantic firewall")
    require(assembly["case_specific_rules"] is False, "no case-specific assembly")

    source_cells = {row["cell"] for row in source["cells"]}
    require(source_cells == {f"X{x}-T{t}" for x in range(1,8) for t in range(1,4)}, "source matrix")
    require(all(row["natural_attempts_for_cell"] == 1 for row in source["cells"]), "first attempts only")

    event_refs = {row["ref"] for row in events}
    require(len(event_refs) == len(events), "event refs unique")
    require(all(row.get("future_evidence_used") is False for row in candidates), "candidate future leakage")
    require(all(row.get("semantic_status") == "NOT_ADJUDICATED" for row in candidates), "candidate semantics")

    ids = [row["package_id"] for row in packages]
    require(len(ids) == len(set(ids)), "package ids unique")
    require(all(row["schema"] == "RB-STAGE2-R7-MONITOR-DERIVED-REPAIR-PACKAGE-v1" for row in packages), "package schema")
    require(all(row["source_cell"] in source_cells for row in packages), "package source cell")
    require(all(row["parent_reconstruction"]["future_evidence_used"] is False for row in packages), "package future leakage")
    require(all("cpr_label" not in row and "cpr_direction" not in row for row in packages), "package CPR leakage")

    gates = Counter(row["repair_gate_status"] for row in packages)
    require(dict(sorted(gates.items())) == summary["repair_gate_counts"], "gate accounting")
    require(gates == Counter({
        "PARENT_RECONSTRUCTION_BLOCKED": 16,
        "LINEAGE_GAP_BLOCKED": 7,
        "NO_REPAIR_REQUIRED": 1,
    }), "frozen gate distribution")
    require(summary["complete_for_structured_repair_count"] == 0, "no active-ready package yet")

    preflight_by_id = {row["package_id"]: row for row in preflight}
    require(set(preflight_by_id) == set(ids), "preflight/package binding")
    for package in packages:
        row = preflight_by_id[package["package_id"]]
        require(row["source_cell"] == package["source_cell"], "preflight source binding")
        require(row["prefix_cutoff_ref"] == package["prefix_cutoff_ref"], "preflight prefix binding")
        require(row["repair_gate_status"] == package["repair_gate_status"], "preflight gate binding")
        require(row["future_evidence_used"] is False, "preflight future leakage")

    forbidden = "\n".join(firewall["forbidden_inputs"])
    monitor_source = (ROOT / "scripts/run_stage2_r7_structural_monitor_v1.py").read_text(encoding="utf-8")
    assembly_source = (ROOT / "scripts/assemble_stage2_r7_repair_packages_v1.py").read_text(encoding="utf-8")
    for token in [
        "r6_grade_semantic_audit",
        "r6_grade_material",
        "cross_task_cross_layer_audit",
        "stage2_cross_task_synthesis_evidence_bundle",
        "stage2_paper_figure_table_registry",
    ]:
        require(token in forbidden, "firewall missing " + token)
        require(token not in monitor_source and token not in assembly_source, "forbidden source dependency " + token)

    immutable = boundary["immutability"]
    require(immutable["rag_corpus_index_embedding_and_retrieval_structure"] == "READ_ONLY", "RAG boundary")
    require(immutable["memorybank_internal_memory_index_strength_and_recall_mechanism"] == "READ_ONLY", "MemoryBank boundary")
    require(immutable["longllmlingua_model_checkpoint_compression_algorithm_and_interface"] == "READ_ONLY", "LongLLMLingua boundary")
    require(boundary["authorization"]["active_repair_execution"] is False, "repair boundary authorization")

    require(package_schema["$id"] == "RB-STAGE2-R7-MONITOR-DERIVED-REPAIR-PACKAGE-v1", "package schema id")

    report = REPORT.read_text(encoding="utf-8")
    assembly_report = ASSEMBLY_REPORT.read_text(encoding="utf-8")
    for token in [
        "21/21 frozen first-attempt natural archives scanned",
        "normalized structural events: **1120**",
        "raw structural candidate signals retained: **244**",
        "active repair continuation from an unverified parent",
    ]:
        require(token in report, "report missing " + token)
    for token in [
        "structurally merged repair episodes/packages: **24**",
        "cells represented by packages: **15/21**",
        "PARENT_RECONSTRUCTION_BLOCKED",
        "LINEAGE_GAP_BLOCKED",
    ]:
        require(token in assembly_report, "assembly report missing " + token)

    print("STAGE2_R7_OFFLINE_MONITOR=PASS")
    print("SOURCE_CELLS=21")
    print("NORMALIZED_EVENTS=1120")
    print("RAW_STRUCTURAL_CANDIDATES=244")
    print("ASSEMBLED_PACKAGES=24")
    print("PACKAGE_CELLS=15")
    print("REPAIR_READY=0")
    print("PARENT_RECONSTRUCTION_BLOCKED=16")
    print("LINEAGE_GAP_BLOCKED=7")
    print("NO_REPAIR_REQUIRED=1")
    print("SEMANTIC_AUDIT_INPUT=NO")
    print("PROVIDER_CALLS=0")


if __name__ == "__main__":
    main()
