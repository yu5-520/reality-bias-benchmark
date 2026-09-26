from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "stage2/r7_parent_v1"

SUMMARY = BASE / "summary.json"
PARENT = BASE / "parent_resumability_audit.jsonl"
FOREIGN = BASE / "foreign_carrier_binding_audit.jsonl"
CONTRACT = ROOT / "configs/stage2_r7_parent_resumability_contract_v1.json"
FREEZE = ROOT / "configs/stage2_r7_parent_resumability_freeze_v1.json"
REPORT = ROOT / "docs/reports/2026-09-26/StageII_R7_Parent_Resumability_and_Repair_Readiness_Report_v1.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def require(ok: bool, message: str):
    if not ok:
        raise AssertionError(message)


def main():
    summary = load(SUMMARY)
    parents = load_jsonl(PARENT)
    foreign = load_jsonl(FOREIGN)
    contract = load(CONTRACT)
    freeze = load(FREEZE)

    require(summary["schema"] == "RB-STAGE2-R7-PARENT-RESUMABILITY-SUMMARY-v1", "summary schema")
    require(summary["status"] == "OFFLINE_PARENT_RESUMABILITY_AND_FOREIGN_BINDING_AUDIT_COMPLETE", "summary status")
    require(summary["source_packages"] == 24, "source package count")
    require(summary["parent_reconstruction_packages_audited"] == 16 == len(parents), "parent audit count")
    require(summary["foreign_carrier_packages_audited"] == 7 == len(foreign), "foreign audit count")
    require(summary["application_state_verified_package_count"] == 5, "application-state verified count")
    require(summary["native_resume_verified_package_count"] == 0, "native resume must remain zero")
    require(summary["foreign_legal_surface_bound_package_count"] == 0, "foreign legal surface bound")
    require(summary["parent_reconstruction_blocked_count"] == 16, "parent blocked count")
    require(summary["lineage_gap_blocked_count"] == 7, "lineage gap count")
    require(summary["provider_calls"] == 0 and summary["evaluator_calls"] == 0, "offline only")
    require(summary["natural_reruns"] == 0 and summary["stochastic_prefix_replays"] == 0, "no rerun")
    require(summary["semantic_audit_used"] is False, "semantic audit firewall")
    require(summary["active_repair_authorized"] is False, "active repair closed")

    require(contract["status"] == "FROZEN_BEFORE_RESUMABILITY_AUDIT", "contract status")
    require(contract["active_repair_gate"] == "L4_NATIVE_RESUME_VERIFIED", "L4 gate")
    require(contract["authorization"]["provider_calls"] is False, "provider disabled")
    require(contract["authorization"]["active_repair"] is False, "repair disabled")

    require(len({row["package_id"] for row in parents}) == 16, "parent package ids unique")
    require(all(row["result"] == "PARENT_RECONSTRUCTION_BLOCKED" for row in parents), "all parents fail closed")
    require(all(row["provider_calls"] == 0 and row["evaluator_calls"] == 0 for row in parents), "parent offline")
    require(all(row["stochastic_prefix_replay"] is False for row in parents), "no stochastic parent replay")
    require(all(row["private_runtime_state_mutation"] is False for row in parents), "no private mutation")
    require(all(row["semantic_audit_used"] is False for row in parents), "no semantic parent input")
    require(all(row["verification_levels"]["L4_NATIVE_RESUME_VERIFIED"] is False for row in parents), "no L4")

    x1 = [row for row in parents if row["source_cell"].startswith("X1-")]
    require(len(x1) == 5, "X1 package count")
    require(all(row["verification_levels"]["L1_APPLICATION_STATE_BOUND"] for row in x1), "X1 L1")
    require(all(row["detail"]["x1_checkout_reconstruction"]["full_replay_matches_frozen_final_checkout"] is True for row in x1), "X1 final-state replay verification")
    require(all(not row["detail"]["x1_checkout_reconstruction"]["mismatched_final_paths"] for row in x1), "X1 mismatch")
    require(all(not row["detail"]["x1_checkout_reconstruction"]["replay_errors"] for row in x1), "X1 replay errors")

    require(len({row["package_id"] for row in foreign}) == 7, "foreign package ids unique")
    require(all(row["result"] == "LINEAGE_GAP_BLOCKED" for row in foreign), "all foreign gaps remain blocked")
    require(all(row["foreign_state_mutation_allowed"] is False for row in foreign), "foreign state immutable")
    require(all(row["machine_bound_legal_repair_surface"] is False for row in foreign), "no legal surface bound")
    require(all(row["future_suffix_used"] is False for row in foreign), "no future suffix")
    require(all(row["semantic_inference_used"] is False for row in foreign), "no semantic inference")

    require(freeze["status"] == "FROZEN_NO_ACTIVE_REPAIR_AUTHORIZATION", "freeze status")
    require(freeze["resumability_summary_hash"] == summary["summary_hash"], "summary hash bind")
    require(freeze["accounting"]["active_repair_ready"] == 0, "freeze active ready")
    require(freeze["authorization"]["active_repair"] is False, "freeze active repair")
    require(freeze["authorization"]["new_subject_provider_continuation"] is False, "no new subject run")

    report = REPORT.read_text(encoding="utf-8")
    for token in [
        "L1 application-state verified | 5",
        "L4 native resume verified | **0**",
        "PARENT_RECONSTRUCTION_BLOCKED | 16",
        "LINEAGE_GAP_BLOCKED | 7",
        "Active-repair-ready | **0**",
        "Historical same-parent branch",
        "Prospective repair-capable observation",
    ]:
        require(token in report, "report missing: " + token)

    print("STAGE2_R7_PARENT_RESUMABILITY_FREEZE=PASS")
    print("SOURCE_PACKAGES=24")
    print("PARENT_AUDITED=16")
    print("X1_APPLICATION_STATE_VERIFIED=5")
    print("NATIVE_RESUME_VERIFIED=0")
    print("FOREIGN_AUDITED=7")
    print("FOREIGN_LEGAL_SURFACE_BOUND=0")
    print("ACTIVE_REPAIR_READY=0")
    print("PROVIDER_CALLS=0")


if __name__ == "__main__":
    main()
