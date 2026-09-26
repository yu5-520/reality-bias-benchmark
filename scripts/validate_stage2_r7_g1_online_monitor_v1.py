from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs/stage2_r7_g1_online_monitor_contract_v1.json"
FREEZE = ROOT / "configs/stage2_r7_g1_online_monitor_preflight_freeze_v1.json"
SCHEMA = ROOT / "schemas/stage2_r7_g1_monitor_derived_repair_package_v1.schema.json"
MONITOR = ROOT / "stage2/r7_prospective_v1/online_monitor.py"
WATCHER = ROOT / "stage2/r7_prospective_v1/repair_boundary_watcher.py"
PREFLIGHT = ROOT / "stage2/r7_prospective_v1/online_monitor_preflight.py"
PLAN = ROOT / "docs/R_Plan_v7.41.md"
REPORT = ROOT / "docs/reports/2026-09-26/StageII_R7_G1_Online_Monitor_and_Repair_Boundary_Preflight_Report_v1.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok: bool, message: str):
    if not ok:
        raise AssertionError(message)


def main():
    contract = load(CONTRACT)
    freeze = load(FREEZE)
    schema = load(SCHEMA)

    require(contract["schema"] == "RB-STAGE2-R7-G1-ONLINE-MONITOR-CONTRACT-v1", "contract schema")
    require(contract["status"] == "FROZEN_BEFORE_ONLINE_MONITOR_PREFLIGHT", "contract status")
    require(contract["input_policy"]["semantic_audit"] is False, "semantic audit input")
    require(contract["input_policy"]["cpr_labels"] is False, "CPR input")
    require(contract["input_policy"]["future_suffix"] is False, "future suffix")
    require(contract["package_freeze"]["later_events_may_expand_package"] is False, "later expansion")
    require(contract["package_freeze"]["later_semantic_audit_may_expand_package"] is False, "semantic expansion")
    require(contract["package_freeze"]["full_native_checkpoint_required_for_complete_gate"] is True, "checkpoint gate")
    require(contract["in_repair_boundary_watcher"]["fail_closed"] is True, "fail closed")
    require(contract["post_repair_watch"]["repair_actions_allowed"] is False, "watch only")

    auth = contract["authorization"]
    require(auth["prospective_subject_provider_calls"] is False, "subject calls disabled")
    require(auth["active_repair_provider_calls"] is False, "repair calls disabled")
    require(auth["paid_evaluator_calls"] is False, "evaluator disabled")

    require(freeze["status"] == "FROZEN_OFFLINE_PREFLIGHT_PASS_SUBJECT_EXECUTION_CLOSED", "freeze status")
    require(freeze["workflow_run_id"] == 36229433474, "workflow bind")
    require(freeze["provider_calls"] == 0 and freeze["subject_calls"] == 0, "offline preflight")
    require(freeze["active_repairs"] == 0, "no active repair")
    require(freeze["semantic_audit_input"] is False and freeze["cpr_input"] is False, "semantic firewall")
    result = freeze["results"]
    require(result["first_eligible_prefix_sequence"] == 2, "first eligible prefix")
    require(result["future_event_package_immutability"] == "PASS", "package immutability")
    require(result["valid_repair_action_boundary"] == "PASS", "valid repair")
    require(result["repair_executor_exit"] is True, "executor exit")
    require(result["post_repair_watch_only"] is True, "post repair watch")
    require("RAG_INTERNAL_MUTATION" in result["forbidden_foreign_mutation_violation"], "foreign mutation block")
    require("PRESERVE_SET_MISMATCH" in result["preserve_set_violation"], "preserve block")
    require(result["foreign_carrier_without_downstream_binding"] == "LINEAGE_GAP_BLOCKED", "foreign lineage gate")
    require(result["stale_checkpoint_gate"] == "CHECKPOINT_BOUNDARY_BLOCKED", "checkpoint boundary gate")
    require(result["watch_only_package_count"] == 0, "watch-only package count")

    require(schema["$id"] == "RB-STAGE2-R7-G1-MONITOR-DERIVED-REPAIR-PACKAGE-v1", "package schema")
    require(schema["properties"]["semantic_audit_used"]["const"] is False, "schema semantic audit")
    require(schema["properties"]["future_evidence_used"]["const"] is False, "schema future evidence")
    require(schema["properties"]["cpr_label"]["type"] == "null", "schema CPR null")

    monitor = MONITOR.read_text(encoding="utf-8")
    watcher = WATCHER.read_text(encoding="utf-8")
    preflight = PREFLIGHT.read_text(encoding="utf-8")

    require("STRICTLY_INCREASING" not in monitor or "strictly increasing" in monitor.lower(), "sequence guard")
    require("semantic_audit_used" in monitor and '"cpr_label": None' in monitor, "monitor semantic firewall")
    require("if ref in self._frozen_by_object" in monitor, "immutable package object gate")
    require("WATCH_ONLY" in monitor, "watch-only mode")
    require("FORBIDDEN_MUTATION_CLASSES" in watcher, "forbidden mutation class")
    require("PRESERVE_SET_MISMATCH" in watcher, "preserve-set watcher")
    require("POST_REPAIR_CONTINUOUS_REPAIR_FORBIDDEN" in watcher, "continuous repair block")

    for body, label in [(monitor, "monitor"), (watcher, "watcher"), (preflight, "preflight")]:
        for forbidden in [
            "r6_grade_semantic_audit",
            "r6_grade_material",
            "cross_task_cross_layer_audit",
            "stage2_cross_task_synthesis_evidence_bundle",
        ]:
            require(forbidden not in body, f"{label} leaked semantic source {forbidden}")

    report = REPORT.read_text(encoding="utf-8")
    for token in [
        "PREFIX-ONLY MONITOR PREFLIGHT PASS",
        "future-event package immutability PASS",
        "POST_REPAIR_CONTINUOUS_REPAIR_FORBIDDEN",
        "LINEAGE_GAP_BLOCKED",
        "No G1 subject call is authorized",
    ]:
        require(token in report, "report missing " + token)

    plan = PLAN.read_text(encoding="utf-8")
    for token in [
        "PREFIX-ONLY ONLINE MONITOR PREFLIGHT PASS",
        "SUBJECT EXECUTION CLOSED",
        "NATIVE EVENT-ADAPTER INTEGRATION NEXT",
        "Not authorized:",
    ]:
        require(token in plan, "plan missing " + token)

    print("STAGE2_R7_G1_ONLINE_MONITOR=PASS")
    print("PREFIX_ONLY=YES")
    print("PACKAGE_FUTURE_EXPANSION=NO")
    print("SEMANTIC_AUDIT_INPUT=NO")
    print("CPR_INPUT=NO")
    print("FOREIGN_INTERNAL_MUTATION=BLOCKED")
    print("PRESERVE_SET_DRIFT=BLOCKED")
    print("POST_REPAIR_CONTINUOUS_ACTION=BLOCKED")
    print("SUBJECT_CALLS_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
