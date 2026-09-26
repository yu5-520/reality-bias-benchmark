from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs/stage2_r7_g1_prospective_repair_contract_v1.json"
BOUNDARIES = ROOT / "configs/stage2_r7_g1_checkpoint_safe_boundaries_v1.json"
CHECKPOINT = ROOT / "configs/stage2_r7_checkpoint_contract_v1.json"
CONFORMANCE = ROOT / "configs/stage2_r7_checkpoint_conformance_freeze_v1.json"
TASKS = ROOT / "stage2/tasks.json"
ROLES = ROOT / "stage2/roles.json"
SUBJECT = ROOT / "stage2/subject.json"
ACTION = ROOT / "stage2/native_v7/action_contract_registry.json"
PREFLIGHT = ROOT / "configs/stage2_r7_g1_preflight_freeze_v1.json"
REPLICATION = ROOT / "configs/stage2_r7_prospective_replication_registry_v1.json"
RUN_SCHEMA = ROOT / "schemas/stage2_r7_g1_run_manifest_v1.schema.json"
HOST = ROOT / "stage2/r7_prospective_v1/host.py"
X2 = ROOT / "stage2/r7_prospective_v1/x2_metagpt.py"
RECORDERS = ROOT / "stage2/r7_prospective_v1/recorders.py"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    header = f"blob {len(raw)}\0".encode()
    return hashlib.sha1(header + raw).hexdigest()


def require(ok: bool, message: str):
    if not ok:
        raise AssertionError(message)


def main():
    contract = load(CONTRACT)
    boundaries = load(BOUNDARIES)
    checkpoint = load(CHECKPOINT)
    conformance = load(CONFORMANCE)
    preflight = load(PREFLIGHT)
    replication = load(REPLICATION)
    run_schema = load(RUN_SCHEMA)

    require(contract["schema"] == "RB-STAGE2-R7-G1-PROSPECTIVE-REPAIR-CONTRACT-v1", "G1 contract schema")
    require(contract["status"] == "FROZEN_CONTRACT_NO_SUBJECT_EXECUTION_YET", "G1 contract status")
    group = contract["group"]
    require(group["group_id"] == "StageII-R7-G1", "G1 id")
    require(group["planned_natural_cells"] == 21, "G1 21 cells")
    require(group["natural_attempts_per_cell"] == 1, "one attempt per cell")
    require(group["natural_resampling"] is False, "no natural resampling")
    require(group["not_a_rerun_of_original_21"] is True, "new prospective evidence")

    bindings = contract["frozen_input_bindings"]
    require(git_blob_sha(TASKS) == bindings["tasks_git_blob_sha"], "tasks blob drift")
    require(git_blob_sha(ROLES) == bindings["roles_git_blob_sha"], "roles blob drift")
    require(git_blob_sha(SUBJECT) == bindings["subject_git_blob_sha"], "subject blob drift")
    require(git_blob_sha(ACTION) == bindings["action_contract_git_blob_sha"], "action contract blob drift")

    natural = contract["natural_A"]
    require(natural["checkpoint_recorder_active_from_task_start"] is True, "checkpoint recorder")
    require(natural["structural_monitor_active_from_task_start"] is True, "structural monitor")
    require(natural["repair_actions_during_A"] == 0, "A cannot be repaired")
    require(natural["monitor_future_blind"] is True, "future blind")
    require(natural["semantic_audit_input"] is False, "semantic firewall")
    require(natural["cpr_labels_input"] is False, "CPR firewall")
    require(natural["A_must_continue_uninterrupted_after_candidate_freeze"] is True, "A continuation")
    require(natural["A_frozen_before_B_execution"] is True, "A before B")

    candidate = contract["candidate_and_package"]
    require(candidate["source"] == "STRUCTURAL_MONITOR_ONLY", "monitor-only package")
    require(candidate["semantic_cherry_picking"] is False, "no semantic cherry-picking")
    require(candidate["future_suffix_used_for_package"] is False, "no future suffix")
    require(candidate["package_contains_cpr_label"] is False, "no CPR in package")
    require("FULL_NATIVE_PARENT_CHECKPOINT_AT_EXACT_LEGAL_BOUNDARY" in candidate["eligible_gate_requires"], "full checkpoint gate")
    require("NO_UNCHECKPOINTED_MODEL_DECISION_AFTER_PARENT" in candidate["eligible_gate_requires"], "freshness gate")

    repair = contract["repair_B"]
    require(repair["B_per_eligible_package"] == 1, "one B")
    require(repair["best_of_n"] is False, "no best of N")
    require(repair["retry_for_reproducibility"] is False, "no retry")
    require(repair["repair_package_applied_once"] is True, "one package application")
    require(repair["repair_executor_exits_after_package"] is True, "executor exit")
    require(repair["continuous_repair_after_package"] is False, "no continuous repair")

    forbidden = set(contract["repair_authority"]["forbidden"])
    for token in [
        "FRAMEWORK_SOURCE_MODIFICATION",
        "PROTOCOL_MODIFICATION",
        "NATIVE_SECURITY_BOUNDARY_BYPASS",
        "PRIVATE_RUNTIME_STATE_MUTATION",
        "RAG_INTERNAL_MUTATION",
        "MEMORYBANK_INTERNAL_MUTATION",
        "LONGLMLINGUA_INTERNAL_MUTATION",
        "POSTHOC_SEMANTIC_AUDIT_TO_CHOOSE_OR_EXPAND_PACKAGE",
    ]:
        require(token in forbidden, "missing forbidden boundary " + token)

    auth = contract["authorization"]
    require(auth["contract_freeze"] is True and auth["offline_preflight"] is True, "offline authorization")
    require(auth["prospective_subject_provider_calls"] is False, "subject calls disabled")
    require(auth["active_repair_provider_calls"] is False, "repair calls disabled")
    require(auth["paid_evaluator_calls"] is False, "evaluator disabled")

    require(boundaries["status"] == "FROZEN_BEFORE_G1_SUBJECT_RUN", "safe boundary freeze")
    require(boundaries["systems"]["X1"]["mid_run_boundary"] == "UNPROVEN", "X1 fail closed")
    require(boundaries["systems"]["X2"]["mid_run_boundary"] == "VERIFIED_BY_RUNNER_GEOMETRY", "X2 round boundary")
    require(boundaries["systems"]["X3"]["mid_nested_call_boundary"] == "UNPROVEN", "X3 fail closed")
    for x in ["X4", "X5", "X6", "X7"]:
        require("AFTER_HOST_TURN_RETURNS" in boundaries["systems"][x]["safe_full_boundaries"], x + " host boundary")

    require(checkpoint["status"] == "FROZEN_INFRASTRUCTURE_ONLY_NO_SCIENTIFIC_SUBJECT_RUN", "checkpoint contract")
    require(conformance["status"] == "FROZEN_ENGINEERING_CONFORMANCE_PASS_NO_SCIENTIFIC_SUBJECT_RUN", "checkpoint conformance")
    require(conformance["provider_calls"] == 0 and conformance["scientific_subject_runs"] == 0, "checkpoint smoke only")
    require(conformance["systems"]["X3_A2A"]["a2a_protocol_modified"] is False, "A2A unchanged")

    require(preflight["status"] == "FROZEN_NON_STUDY_PREFLIGHT_PASS_SUBJECT_EXECUTION_CLOSED", "G1 preflight status")
    require(preflight["workflow_run_id"] == 36228869124, "G1 preflight workflow")
    require(preflight["provider_calls"] == 0 and preflight["subject_calls"] == 0, "G1 preflight no subject")
    require(preflight["active_repairs"] == 0, "G1 preflight no repair")
    require(preflight["results"]["X2_METAGPT"]["checkpoint_count"] == 9, "X2 checkpoint count")
    require(preflight["results"]["X2_METAGPT"]["control_flow_equivalent"] is True, "X2 equivalence")
    require(preflight["results"]["X4_X7_HOST"]["checkpoint_count"] == 9, "host checkpoint count")
    require(preflight["results"]["X4_X7_HOST"]["foreign_carrier_mutation"] is False, "foreign carrier immutable")
    require(preflight["results"]["STATIC_BOUNDARY"]["X1_mid_run"] == "UNPROVEN_FAIL_CLOSED", "X1 static boundary")
    require(preflight["results"]["STATIC_BOUNDARY"]["X3_mid_nested_call"] == "UNPROVEN_FAIL_CLOSED", "X3 static boundary")

    require(replication["status"] == "FROZEN_NAMING_AND_BINDING_POLICY", "replication registry")
    require(replication["groups"]["StageII-R7-G1"]["state"] == "CONTRACT_PREPARED_SUBJECT_NOT_STARTED", "G1 replication state")
    require(run_schema["$id"] == "RB-STAGE2-R7-G1-RUN-MANIFEST-v1", "run manifest schema")
    require(run_schema["properties"]["natural_attempt_index"]["const"] == 1, "run manifest first attempt")

    host = HOST.read_text(encoding="utf-8")
    x2 = X2.read_text(encoding="utf-8")
    recorders = RECORDERS.read_text(encoding="utf-8")
    require("checkpoint_hook" in host and "AFTER_HOST_TURN_RETURNS" in host, "host hook")
    require("await env.run(k=1)" in x2 and "AFTER_EACH_ENV_RUN_K1_RETURN" in x2, "MetaGPT hook")
    require("record_model_decision()" in recorders, "decision sequence binding")
    for body, name in [(host, "host"), (x2, "x2"), (recorders, "recorders")]:
        for forbidden_source in [
            "r6_grade_semantic_audit",
            "r6_grade_material",
            "cross_task_cross_layer_audit",
            "cpr_label",
            "cpr_direction",
        ]:
            require(forbidden_source not in body, f"{name} leaked semantic source {forbidden_source}")

    print("STAGE2_R7_G1_CONTRACT=PASS")
    print("GROUP=StageII-R7-G1")
    print("PLANNED_NATURAL_CELLS=21")
    print("NATURAL_ATTEMPTS_PER_CELL=1")
    print("SUBJECT_CALLS_AUTHORIZED=NO")
    print("ACTIVE_REPAIR_AUTHORIZED=NO")
    print("X1_MIDRUN_CHECKPOINT=UNPROVEN_FAIL_CLOSED")
    print("X2_ROUND_CHECKPOINT=REGISTERED")
    print("X3_NESTED_CHECKPOINT=UNPROVEN_FAIL_CLOSED")
    print("X4_X7_HOST_TURN_CHECKPOINT=REGISTERED")
    print("G1_CHECKPOINT_HOOK_PREFLIGHT=PASS")
    print("G1_SCIENTIFIC_SUBJECT_STARTED=NO")


if __name__ == "__main__":
    main()
