from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FREEZE = ROOT / "configs/stage2_r7_g1_native_event_integration_freeze_v1.json"
PARENT = ROOT / "configs/stage2_r7_g1_parent_freeze_semantics_v1.json"
RUN_SCHEMA = ROOT / "schemas/stage2_r7_g1_run_manifest_v1.schema.json"
ADAPTER = ROOT / "stage2/r7_prospective_v1/runtime_event_adapter.py"
INTEGRATION = ROOT / "stage2/r7_prospective_v1/integration.py"
MANIFEST = ROOT / "stage2/r7_prospective_v1/run_manifest.py"
CONTROLLER = ROOT / "stage2/r7_checkpoint_v1/controller.py"
REPORT = ROOT / "docs/reports/2026-09-26/StageII_R7_G1_Native_Runtime_Event_Integration_Report_v1.md"
PLAN = ROOT / "docs/R_Plan_v7.42.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok: bool, message: str):
    if not ok:
        raise AssertionError(message)


def main():
    freeze = load(FREEZE)
    parent = load(PARENT)
    schema = load(RUN_SCHEMA)

    require(freeze["schema"] == "RB-STAGE2-R7-G1-NATIVE-EVENT-INTEGRATION-FREEZE-v1", "freeze schema")
    require(freeze["status"] == "FROZEN_NON_STUDY_INTEGRATION_PASS_SUBJECT_EXECUTION_CLOSED", "freeze status")
    require(freeze["workflow_run_id"] == 36230045769, "workflow binding")
    require(freeze["provider_calls"] == 0 and freeze["subject_calls"] == 0, "non-study only")
    require(freeze["active_repairs"] == 0, "no active repair")
    require(freeze["semantic_audit_input"] is False and freeze["cpr_input"] is False, "semantic firewall")

    static = freeze["results"]["STATIC_BOUNDARY"]
    require(static["status"] == "PASS", "static pass")
    require(static["X1_mid_run"] == "CHECKPOINT_BOUNDARY_BLOCKED", "X1 blocked")
    require(static["X3_nested_call"] == "CHECKPOINT_BOUNDARY_BLOCKED", "X3 blocked")
    require(static["historical_parent_survives_natural_A_continuation"] is True, "frozen parent")

    x2 = freeze["results"]["X2_METAGPT"]
    require(x2["status"] == "PASS", "X2 pass")
    require(x2["native_rounds"] == 5, "X2 rounds")
    require(x2["checkpoint_count"] == 7, "X2 checkpoints")
    require(x2["structural_event_count"] == 6, "X2 structural events")
    require(x2["package_count"] == 1 and x2["complete_package_count"] == 1, "X2 package")
    require(x2["control_flow_equivalent"] is True and x2["checkout_equivalent"] is True, "X2 equivalence")
    require(x2["frozen_at_model_decision"] == 3, "X2 freeze point")
    require(x2["natural_A_final_model_decision"] == 5, "X2 A continuation")
    require(x2["historical_parent_available_after_A"] is True, "X2 historical parent")
    require(x2["strict_current_parent_blocked_after_A"] is True, "X2 current parent distinction")

    x5 = freeze["results"]["X5_RAG_HOST"]
    require(x5["status"] == "PASS", "X5 pass")
    require(x5["scripted_model_decisions"] == 5, "X5 decisions")
    require(x5["checkpoint_count"] == 7, "X5 checkpoints")
    require(x5["structural_event_count"] == 21, "X5 events")
    require(x5["package_count"] == 4, "X5 package count")
    require(x5["complete_package_count"] == 1, "X5 complete package")
    require(x5["foreign_lineage_gap_count"] == 3, "X5 foreign lineage gaps")
    require(x5["control_flow_equivalent"] is True and x5["checkout_equivalent"] is True, "X5 equivalence")
    require(x5["historical_parent_available_after_A"] is True, "X5 historical parent")

    bridge = freeze["runtime_bridge"]
    require(bridge["provider_response_identity"] == "RETURNED_UNCHANGED", "provider identity")
    require(bridge["checkpoint_order"] == "CHECKPOINT_FIRST_THEN_FLUSH_COMPLETED_TURN_STRUCTURAL_COPY", "checkpoint order")
    require(bridge["foreign_carrier_temporal_proximity_implies_lineage"] is False, "no temporal lineage inference")
    require(bridge["run_manifest_semantic_audit_state"] == "LOCKED_UNTIL_A_AND_B_FROZEN", "semantic lock")

    timing = freeze["parent_freeze_semantics"]
    require(timing["freshness_checked_at_package_freeze"] is True, "freshness timing")
    require(timing["later_natural_A_continuation_invalidates_frozen_parent"] is False, "A must not invalidate")
    require(timing["later_natural_A_continuation_may_expand_package"] is False, "A no expansion")
    require(timing["B_after_A_freeze_may_restore_exact_frozen_parent"] is True, "B restore parent")

    auth = freeze["authorization"]
    require(auth["prospective_subject_provider_calls"] is False, "subject closed")
    require(auth["active_repair_provider_calls"] is False, "repair closed")
    require(auth["paid_evaluator_calls"] is False, "evaluator closed")

    require(parent["status"] == "FROZEN_BEFORE_NATIVE_EVENT_INTEGRATION_PREFLIGHT", "parent semantics freeze")
    require(parent["after_package_freeze"]["natural_A_must_continue"] is True, "A continues")
    require(parent["after_package_freeze"]["B_launch_after_A_freeze_may_restore_original_frozen_parent"] is True, "B launch")

    require(schema["$id"] == "RB-STAGE2-R7-G1-RUN-MANIFEST-v1", "run schema")
    require("manifest_hash" in schema["required"], "manifest hash required")
    require(schema["properties"]["natural_attempt_index"]["const"] == 1, "first attempt")
    require(schema["properties"]["natural_A"]["properties"]["repair_actions"]["const"] == 0, "A repair-free")

    adapter = ADAPTER.read_text(encoding="utf-8")
    integration = INTEGRATION.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    controller = CONTROLLER.read_text(encoding="utf-8")

    require("return self._record(value, metadata)" in adapter, "provider response passthrough")
    require("temporal proximity" in adapter, "foreign lineage caution")
    require("foreign_carrier_refs_from_host" in integration, "carrier integration")
    require("checkpoint_hash" in manifest and "semantic_audit_state" in manifest, "run manifest fields")
    require("repair_parent_at_freeze" in controller, "historical parent API")

    for body, label in [(adapter, "adapter"), (integration, "integration"), (manifest, "manifest")]:
        for forbidden in [
            "r6_grade_semantic_audit",
            "r6_grade_material",
            "cross_task_cross_layer_audit",
            "stage2_cross_task_synthesis_evidence_bundle",
        ]:
            require(forbidden not in body, f"{label} leaked semantic source {forbidden}")

    report = REPORT.read_text(encoding="utf-8")
    for token in [
        "NATIVE EVENT → CHECKPOINT → PREFIX MONITOR INTEGRATION PASS",
        "three repeated RAG-hit packages",
        "LINEAGE_GAP_BLOCKED",
        "repair_parent_at_freeze()",
        "CHECKPOINT_BOUNDARY_BLOCKED",
        "No scientific subject call or active repair call is authorized",
    ]:
        require(token in report, "report missing " + token)

    plan = PLAN.read_text(encoding="utf-8")
    for token in [
        "RUNTIME EVENT BRIDGE INTEGRATED",
        "SUBJECT EXECUTION READINESS GATE NEXT",
        "Not authorized:",
        "explicit active-execution authorization",
    ]:
        require(token in plan, "plan missing " + token)

    print("STAGE2_R7_G1_NATIVE_EVENT_INTEGRATION=PASS")
    print("X2_NATIVE_INTEGRATION=PASS")
    print("X5_RAG_HOST_INTEGRATION=PASS")
    print("X5_COMPLETE_PACKAGES=1")
    print("X5_FOREIGN_LINEAGE_GAPS=3")
    print("HISTORICAL_PARENT_AFTER_A=AVAILABLE")
    print("X1_MIDRUN=CHECKPOINT_BOUNDARY_BLOCKED")
    print("X3_NESTED=CHECKPOINT_BOUNDARY_BLOCKED")
    print("SUBJECT_CALLS_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
