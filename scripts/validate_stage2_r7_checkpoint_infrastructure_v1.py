from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONTRACT = ROOT / "configs/stage2_r7_checkpoint_contract_v1.json"
FREEZE = ROOT / "configs/stage2_r7_checkpoint_conformance_freeze_v1.json"
SCHEMA = ROOT / "schemas/stage2_r7_checkpoint_manifest_v1.schema.json"
REPORT = ROOT / "docs/reports/2026-09-26/StageII_R7_Prospective_Checkpoint_Conformance_Report_v1.md"
PLAN = ROOT / "docs/R_Plan_v7.39.md"
COMMON = ROOT / "stage2/r7_checkpoint_v1/common.py"
AUTOGEN = ROOT / "stage2/r7_checkpoint_v1/autogen_adapter.py"
METAGPT = ROOT / "stage2/r7_checkpoint_v1/metagpt_adapter.py"
A2A = ROOT / "stage2/r7_checkpoint_v1/a2a_adapter.py"
HOST = ROOT / "stage2/r7_checkpoint_v1/host_adapter.py"
CONTROLLER = ROOT / "stage2/r7_checkpoint_v1/controller.py"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok: bool, message: str):
    if not ok:
        raise AssertionError(message)


def main():
    contract = load(CONTRACT)
    freeze = load(FREEZE)
    schema = load(SCHEMA)

    require(contract["schema"] == "RB-STAGE2-R7-PROSPECTIVE-CHECKPOINT-CONTRACT-v1", "contract schema")
    require(contract["status"] == "FROZEN_INFRASTRUCTURE_ONLY_NO_SCIENTIFIC_SUBJECT_RUN", "contract status")
    auth = contract["authorization"]
    require(auth["engineering_smoke_only"] is True, "engineering smoke only")
    require(auth["provider_calls"] is False, "provider calls disabled")
    require(auth["evaluator_calls"] is False, "evaluator calls disabled")
    require(auth["scientific_subject_runs"] is False, "subject runs disabled")
    require(auth["active_repair"] is False, "active repair disabled")
    require(contract["geometry"]["historical_21_paths"] == "UNCHANGED_AND_NOT_RETROFITTED", "historical paths")
    require(contract["geometry"]["prospective_group_name"] == "StageII-R7-G1", "group id")

    require(freeze["schema"] == "RB-STAGE2-R7-CHECKPOINT-CONFORMANCE-FREEZE-v1", "freeze schema")
    require(freeze["status"] == "FROZEN_ENGINEERING_CONFORMANCE_PASS_NO_SCIENTIFIC_SUBJECT_RUN", "freeze status")
    require(freeze["workflow_run_id"] == 36228005932, "workflow binding")
    require(freeze["provider_calls"] == 0, "freeze provider calls")
    require(freeze["evaluator_calls"] == 0, "freeze evaluator calls")
    require(freeze["scientific_subject_runs"] == 0, "freeze subject calls")
    require(freeze["active_repairs"] == 0, "freeze active repair")
    systems = freeze["systems"]
    require(all(row["status"] == "PASS" for row in systems.values()), "all conformance surfaces pass")
    require(systems["X1_AUTOGEN"]["native_state_round_trip"] == "PASS", "AutoGen state")
    require(systems["X2_METAGPT"]["stage2_role_environment_round_trip"] == "PASS", "MetaGPT role env")
    require(systems["X3_A2A"]["role_service_state_round_trip"] == "PASS", "A2A role service")
    require(systems["X3_A2A"]["a2a_protocol_modified"] is False, "A2A protocol unchanged")
    require(systems["REGISTRY_X4_X7_HOST"]["foreign_carrier_policy"] == "VERIFY_ONLY", "foreign verify only")
    require(freeze["prospective_geometry"]["first_active_subject_run_authorized"] is False, "G1 not yet authorized")

    foreign = freeze["foreign_information_systems"]
    require(foreign["RAG"] == "REFERENCE_HASH_ONLY_NO_INTERNAL_MUTATION", "RAG boundary")
    require(foreign["MemoryBank"] == "REFERENCE_HASH_ONLY_NO_INTERNAL_MUTATION", "MemoryBank boundary")
    require(foreign["LongLLMLingua"] == "REFERENCE_HASH_ONLY_NO_INTERNAL_MUTATION", "LongLLMLingua boundary")
    require("UNCHANGED" in foreign["MCP"], "MCP boundary")

    require(schema["$id"] == "RB-STAGE2-R7-CHECKPOINT-MANIFEST-v1", "manifest schema id")
    required = set(schema["required"])
    for field in contract["required_manifest_fields"]:
        require(field in required, "schema missing field " + field)

    autogen = AUTOGEN.read_text(encoding="utf-8")
    require("team.save_state()" in autogen, "AutoGen save_state")
    require("team.load_state(state)" in autogen, "AutoGen load_state")
    require("._" not in autogen.replace("__future__", ""), "AutoGen adapter must not reach private state")

    metagpt = METAGPT.read_text(encoding="utf-8")
    require('{"addresses", "watch", "send_to"}' in metagpt, "MetaGPT set canonicalization")
    require("Environment.model_dump" in metagpt or "environment.model_dump" in metagpt, "MetaGPT public serialization")
    require("stage2_runtime" in metagpt, "MetaGPT Stage-II runtime envelope")

    a2a = A2A.read_text(encoding="utf-8")
    require("a2a.server" not in a2a, "checkpoint adapter must not add A2A server protocol surface")
    require("AgentCard(" not in a2a and "SendMessageRequest" not in a2a, "A2A protocol untouched")
    require("save_stage2_state" in a2a and "load_stage2_state" in a2a, "A2A service state API")

    common = COMMON.read_text(encoding="utf-8")
    require("verify_foreign_carrier_refs" in common, "foreign carrier verifier")
    require("shutil.copytree" in common, "application snapshot path")

    host = HOST.read_text(encoding="utf-8")
    require("REFERENCE_AND_HASH_ONLY" in host, "host external carrier rule")
    require("RAG" not in host or "X5_RAG" in host, "host should not implement RAG mutation")

    controller = CONTROLLER.read_text(encoding="utf-8")
    require("FIRST_MONITOR_REPAIR_ELIGIBLE_POINT" in controller, "first eligible checkpoint")
    require("uncheckpointed model decision" in controller, "model decision freshness gate")

    report = REPORT.read_text(encoding="utf-8")
    for token in [
        "ENGINEERING CONFORMANCE PASS",
        "provider calls: **0**",
        "native-state round-trip: PASS",
        "Stage-II nine-role environment round-trip: PASS",
        "A2A protocol modified: **false**",
        "StageII-R7-G1",
    ]:
        require(token in report, "report missing " + token)

    plan = PLAN.read_text(encoding="utf-8")
    for token in [
        "CHECKPOINT INFRASTRUCTURE CONFORMANT",
        "Scientific subject runs: **0**",
        "StageII-R7-G1",
        "no prospective scientific subject execution is authorized",
    ]:
        require(token in plan, "plan missing " + token)

    print("STAGE2_R7_CHECKPOINT_INFRASTRUCTURE=PASS")
    print("REGISTRY_HOST=PASS")
    print("AUTOGEN_NATIVE_STATE=PASS")
    print("METAGPT_STAGE2_ENVIRONMENT=PASS")
    print("A2A_ROLE_SERVICE_STATE=PASS")
    print("A2A_PROTOCOL_MODIFIED=NO")
    print("FOREIGN_CARRIERS=VERIFY_ONLY")
    print("SCIENTIFIC_SUBJECT_RUNS=0")
    print("ACTIVE_REPAIRS=0")


if __name__ == "__main__":
    main()
