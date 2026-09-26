from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs/stage2_r7_g1_execution_readiness_contract_v1.json"
LAUNCH = ROOT / "configs/stage2_r7_g1_launch_manifest_v1.json"
FREEZE = ROOT / "configs/stage2_r7_g1_execution_readiness_freeze_v1.json"
SUBJECT = ROOT / "stage2/subject.json"
PLAN = ROOT / "docs/R_Plan_v7.43.md"
REPORT = ROOT / "docs/reports/2026-09-26/StageII_R7_G1_Scientific_Execution_Readiness_Report_v1.md"
X1 = ROOT / "stage2/r7_prospective_v1/x1_runner.py"
X2 = ROOT / "stage2/r7_prospective_v1/x2_runner.py"
X3 = ROOT / "stage2/r7_prospective_v1/x3_runner.py"
CAP = ROOT / "stage2/r7_prospective_v1/capability_runner.py"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok: bool, message: str):
    if not ok:
        raise AssertionError(message)


def main():
    contract = load(CONTRACT)
    launch = load(LAUNCH)
    freeze = load(FREEZE)
    subject = load(SUBJECT)

    require(contract["schema"] == "RB-STAGE2-R7-G1-EXECUTION-READINESS-CONTRACT-v1", "contract schema")
    require(contract["status"] == "FROZEN_READY_AWAITING_EXPLICIT_ACTIVE_EXECUTION_AUTHORIZATION", "contract status")
    geometry = contract["scientific_geometry"]
    require(geometry["historical_reference_cells"] == 21, "historical reference count")
    require(geometry["new_prospective_cells"] == 15, "prospective count")
    require(geometry["active_systems"] == ["X2","X4","X5","X6","X7"], "active systems")
    require(geometry["active_tasks"] == ["T1","T2","T3"], "active tasks")
    require(geometry["first_attempt_only"] is True, "first attempt")
    require(geometry["natural_resampling"] is False, "no resampling")
    require(geometry["all_A_before_any_B"] is True, "A before B")
    require(geometry["B_per_cell_max"] == 1, "B cap")
    require(geometry["best_of_n"] is False and geometry["retry_for_reproducibility"] is False, "no retry/best-of")

    resources = contract["model_resource_ceiling"]
    require(subject["limits"]["max_total_model_invocations"] == 64, "subject invocation ceiling")
    require(resources["per_trajectory_logical_model_invocations"] == 64, "contract per-trajectory ceiling")
    require(resources["prospective_natural_cells"] == 15, "resource natural cells")
    require(resources["natural_logical_invocation_ceiling"] == 960, "natural ceiling")
    require(resources["active_B_branch_ceiling"] == 15, "B branch ceiling")
    require(resources["B_logical_invocation_ceiling"] == 960, "B ceiling")
    require(resources["group_logical_model_invocation_ceiling"] == 1920, "group logical ceiling")
    require(resources["transport_max_retries"] == 2, "retry bind")
    require(resources["absolute_network_attempt_ceiling"] == 5760, "network ceiling")

    auth = contract["authorization"]
    require(auth["prospective_subject_provider_calls"] is False, "subject calls not authorized")
    require(auth["active_repair_provider_calls"] is False, "repair calls not authorized")
    require(auth["paid_evaluator_calls"] is False, "evaluator calls not authorized")

    require(launch["schema"] == "RB-STAGE2-R7-G1-LAUNCH-MANIFEST-v1", "launch schema")
    require(launch["status"] == "FROZEN_READY_AWAITING_EXPLICIT_ACTIVE_EXECUTION_AUTHORIZATION", "launch status")
    require(len(launch["cells"]) == 15, "launch cell count")
    expected = [f"{x}-{t}" for x in ["X2","X4","X5","X6","X7"] for t in ["T1","T2","T3"]]
    observed = [row["cell_id"] for row in launch["cells"]]
    require(observed == expected, "launch cell order")
    require(all(row["natural_attempts"] == 1 for row in launch["cells"]), "one natural attempt")
    require(all(row["active_B_max"] == 1 for row in launch["cells"]), "one B max")
    require(all(row["semantic_audit_before_B"] is False for row in launch["cells"]), "semantic audit locked")
    require(launch["relation_to_original_stage2"]["original_21_natural_paths"] == "IMMUTABLE_REFERENCE_BASELINE", "historical baseline")
    require(set(launch["relation_to_original_stage2"]["omitted_new_runs"]) == {
        "X1-T1","X1-T2","X1-T3","X3-T1","X3-T2","X3-T3"
    }, "X1/X3 omitted prospective reruns")
    require(launch["execution_order"]["phase_1"] == "RUN_AND_FREEZE_ALL_15_NATURAL_A_FIRST_ATTEMPTS", "phase 1")
    require(launch["authorization"]["subject_calls"] is False, "launch subject gate")

    require(freeze["schema"] == "RB-STAGE2-R7-G1-EXECUTION-READINESS-FREEZE-v1", "freeze schema")
    require(freeze["status"] == "FROZEN_READY_AWAITING_EXPLICIT_ACTIVE_EXECUTION_AUTHORIZATION", "freeze status")
    require(freeze["preflight_workflow_run_id"] == 36231420391, "preflight workflow")
    require(freeze["provider_calls"] == 0 and freeze["subject_calls"] == 0, "offline preflight")
    require(freeze["active_repairs"] == 0, "no active repair")
    for system in ["X1","X2","X3","X4","X5","X6","X7"]:
        row = freeze["results"][system]
        require(row["status"] == "PASS", f"{system} readiness")
        require(row["control_flow_equivalent"] is True, f"{system} flow")
        require(row["checkout_equivalent"] is True, f"{system} checkout")
    require(freeze["results"]["X1"]["midrun_checkpoint_status"] == "UNPROVEN_FAIL_CLOSED", "X1 midrun fail closed")
    require(freeze["results"]["X1"]["active_midrun_B_capable"] is False, "X1 no active midrun B")
    require(freeze["results"]["X3"]["nested_checkpoint_status"] == "UNPROVEN_FAIL_CLOSED", "X3 nested fail closed")
    require(freeze["results"]["X3"]["a2a_protocol_modified"] is False, "A2A unchanged")
    require(freeze["results"]["X3"]["active_midrun_B_capable"] is False, "X3 no active nested B")
    require(freeze["engineering_wrapper_readiness"]["all_passed"] is True, "seven wrapper preflight")
    require(freeze["results"]["X4"]["mcp_protocol_modified"] is False, "MCP unchanged")
    require(freeze["results"]["X6"]["foreign_memory_mutated_by_repair"] is False, "MemoryBank untouched")
    require(freeze["results"]["X7"]["compressor_state_mutated_by_repair"] is False, "LongLLMLingua untouched")
    require(freeze["authorization"]["active_subject_execution"] is False, "active execution closed")

    x1 = X1.read_text(encoding="utf-8")
    x2 = X2.read_text(encoding="utf-8")
    x3 = X3.read_text(encoding="utf-8")
    cap = CAP.read_text(encoding="utf-8")
    require("repair_actions_during_A" in x1 and "repair_actions_during_A" in x2 and "repair_actions_during_A" in x3 and "repair_actions_during_A" in cap, "A repair-free seal")
    require("semantic_audit_state" in x1 and "semantic_audit_state" in x2 and "semantic_audit_state" in x3 and "semantic_audit_state" in cap, "semantic lock")
    require("UNPROVEN_FAIL_CLOSED" in x1, "X1 wrapper must retain midrun fail-close")
    require("UNPROVEN_FAIL_CLOSED" in x3 and "a2a_protocol_modified" in x3, "X3 wrapper must retain nested fail-close and protocol accounting")
    require('"X7": "X7_LONGLMLINGUA"' in cap, "canonical X7 system id")

    report = REPORT.read_text(encoding="utf-8")
    for token in [
        "READY / ACTIVE SUBJECT EXECUTION NOT YET AUTHORIZED",
        "SEVEN-SYSTEM WRAPPER PREFLIGHT PASS",
        "15 new prospective natural first attempts",
        "1,920 logical model invocations",
        "COMPLETE_FOR_STRUCTURED_REPAIR",
        "No subject/provider execution is started by this report",
    ]:
        require(token in report, "report missing " + token)

    plan = PLAN.read_text(encoding="utf-8")
    for token in [
        "SEVEN PROSPECTIVE WRAPPERS ENGINEERING-READY",
        "15 ACTIVE PROSPECTIVE FIRST ATTEMPTS READY",
        "X1/X3 MID-RUN REPAIR FAIL-CLOSED",
        "Not yet authorized:",
        "G1 Phase A",
    ]:
        require(token in plan, "plan missing " + token)

    print("STAGE2_R7_G1_EXECUTION_READINESS=PASS")
    print("SEVEN_SYSTEM_WRAPPER_PREFLIGHT=PASS")
    print("X1_MIDRUN_ACTIVE_B=BLOCKED")
    print("X3_NESTED_ACTIVE_B=BLOCKED")
    print("HISTORICAL_REFERENCE_CELLS=21")
    print("PROSPECTIVE_ACTIVE_CELLS=15")
    print("ACTIVE_SYSTEMS=X2,X4,X5,X6,X7")
    print("ALL_A_BEFORE_ANY_B=YES")
    print("B_MAX_PER_CELL=1")
    print("LOGICAL_MODEL_INVOCATION_CEILING=1920")
    print("PAID_EVALUATOR_CALLS=0")
    print("ACTIVE_SUBJECT_EXECUTION_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
