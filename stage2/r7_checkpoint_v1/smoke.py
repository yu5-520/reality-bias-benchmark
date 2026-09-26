from __future__ import annotations

import argparse
import asyncio
import copy
import json
import os
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace

from arena.providers import ScriptedProvider
from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost
from stage2.r7_checkpoint_v1.common import (
    CheckpointRegistry,
    digest,
    file_tree_digest,
    verify_foreign_carrier_refs,
)
from stage2.r7_checkpoint_v1.host_adapter import SoftwareHostCheckpointAdapter

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "stage2"


def _replication_binding():
    return {
        "checkpoint_schema_version": "v1",
        "monitor_rule_version": "stage2_r7_structural_monitor_rules_v1",
        "repair_package_version": "stage2-r7-monitor-derived-repair-package-v1",
    }


def _fixture(destination: Path) -> Path:
    checkout = destination / "checkout"
    shutil.copytree(STAGE2 / "fixtures/project", checkout)
    return checkout


def _registry(destination: Path) -> CheckpointRegistry:
    return CheckpointRegistry(destination / "registry")


def smoke_registry(destination: Path) -> dict:
    checkout = _fixture(destination)
    registry = _registry(destination)
    host = SoftwareEngineeringHost(
        task_id="T2",
        checkout=checkout,
        provider=ScriptedProvider([{"actions": [{"type": "finalize", "answer": "unused"}]}]),
    )
    adapter = SoftwareHostCheckpointAdapter()
    carrier_refs = [{"system": "RAG", "ref": "corpus:v1", "sha256": "a" * 64}]
    before = adapter.save_state(host)
    manifest = adapter.capture(
        system_id="X5_RAG",
        host=host,
        registry=registry,
        application_root=checkout,
        group_id="SMOKE",
        run_id="registry-smoke",
        task_id="T2",
        event_ref="TASK_START",
        model_visible_context={"boundary": "task-start"},
        remaining_horizon=32,
        external_carrier_refs=carrier_refs,
        replication_binding=_replication_binding(),
    )
    checkpoint_hash = manifest["checkpoint_hash"]

    host.queue.clear()
    host.answer = "mutated"
    adapter.load_state(host, registry.load_native_state(checkpoint_hash))
    if digest(adapter.save_state(host)) != digest(before):
        raise RuntimeError("software-host state did not restore")

    original_tree = file_tree_digest(checkout)
    (checkout / "SMOKE_MUTATION.txt").write_text("temporary\n")
    registry.restore_application(checkpoint_hash, checkout)
    if file_tree_digest(checkout) != original_tree:
        raise RuntimeError("application snapshot did not restore")

    if not verify_foreign_carrier_refs(carrier_refs, copy.deepcopy(carrier_refs)):
        raise RuntimeError("foreign carrier reference verification failed")
    changed = copy.deepcopy(carrier_refs)
    changed[0]["sha256"] = "b" * 64
    if verify_foreign_carrier_refs(carrier_refs, changed):
        raise RuntimeError("foreign carrier mismatch was not detected")

    return {
        "schema": "stage2-r7-checkpoint-registry-smoke-v1",
        "status": "PASS",
        "checkpoint_hash": checkpoint_hash,
        "application_restore": "PASS",
        "host_state_round_trip": "PASS",
        "foreign_carrier_policy": "VERIFY_ONLY",
        "provider_calls": 0,
    }


async def smoke_autogen(destination: Path) -> dict:
    from stage2.native_v7.x1_autogen.runner import build_team
    from stage2.native_v7.x1_autogen.smoke import _client
    from stage2.r7_checkpoint_v1.autogen_adapter import AutoGenNativeCheckpointAdapter

    checkout = _fixture(destination)
    restored_checkout = destination / "restored-checkout"
    roles = json.loads((STAGE2 / "roles.json").read_text())
    registry = _registry(destination)
    adapter = AutoGenNativeCheckpointAdapter()

    team1 = build_team(model_client=_client(), roles=roles, checkout=checkout, max_turns=32)
    # Populate a non-empty native Swarm state using the deterministic replay client.
    task = next(
        row for row in json.loads((STAGE2 / "tasks.json").read_text())["tasks"]
        if row["id"] == "T2"
    )
    result = await team1.run(task=task["user_request"])
    if not getattr(result, "messages", None):
        raise RuntimeError("AutoGen checkpoint smoke produced no native team history")
    manifest = await adapter.capture(
        team=team1,
        registry=registry,
        application_root=checkout,
        group_id="SMOKE",
        run_id="autogen-smoke",
        task_id="T2",
        event_ref="AFTER_NATIVE_MODEL_TURN",
        model_visible_context={"task": "T2", "boundary": "post-deterministic-smoke-run"},
        remaining_horizon=32,
        replication_binding=_replication_binding(),
    )
    registry.restore_application(manifest["checkpoint_hash"], restored_checkout)
    team2 = build_team(model_client=_client(), roles=roles, checkout=restored_checkout, max_turns=32)
    await adapter.restore_state(
        team=team2,
        registry=registry,
        checkpoint_hash=manifest["checkpoint_hash"],
    )

    state1 = await team1.save_state()
    state2 = await team2.save_state()
    if digest(dict(state1)) != digest(dict(state2)):
        raise RuntimeError("AutoGen public Team state mismatch after restore")

    return {
        "schema": "stage2-r7-autogen-checkpoint-smoke-v1",
        "status": "PASS",
        "native_api": ["Team.save_state", "Team.load_state"],
        "checkpoint_hash": manifest["checkpoint_hash"],
        "native_state_round_trip": "PASS",
        "application_state_round_trip": "PASS",
        "provider_calls": 0,
    }


def smoke_metagpt(destination: Path) -> dict:
    # MetaGPT eagerly loads its config at import time. Use the same isolated,
    # non-provider bootstrap pattern as the frozen X2 runner; no API call occurs.
    bootstrap = destination / "metagpt-home"
    (bootstrap / ".metagpt").mkdir(parents=True)
    (bootstrap / ".metagpt/config2.yaml").write_text(
        "llm:\n"
        "  api_type: openai\n"
        "  model: stage2-checkpoint-smoke-unused\n"
        "  base_url: https://api.openai.com/v1\n"
        "  api_key: stage2-checkpoint-smoke-unused\n"
    )
    os.environ["HOME"] = str(bootstrap)

    from metagpt.actions import UserRequirement
    from metagpt.environment import Environment
    from metagpt.schema import Message

    from stage2.native_v7.x2_metagpt.checkout import MetaGPTCheckout
    from stage2.native_v7.x2_metagpt.runner import (
        DIRECTORY as META_DIRECTORY,
        ROLES as META_ROLES,
        RuntimeState,
        Stage2MetaRole,
        Stage2ProviderLLM,
    )
    from stage2.r7_checkpoint_v1.metagpt_adapter import (
        MetaGPTNativeCheckpointAdapter,
        restore_runtime_state,
        runtime_state_payload,
    )

    checkout = _fixture(destination)
    registry = _registry(destination)
    adapter = MetaGPTNativeCheckpointAdapter()

    # First verify the pinned upstream Environment public serialization contract.
    environment = Environment()
    environment.publish_message(Message(content="checkpoint-smoke"))
    native = adapter.validate_environment_round_trip(
        environment=environment,
        environment_class=Environment,
        context=environment.context,
    )
    restored_env = adapter.restore_environment(
        environment_class=Environment,
        state=native,
        context=environment.context,
    )
    if digest(adapter.serialize_environment(restored_env)) != digest(native):
        raise RuntimeError("MetaGPT environment did not restore from public serialization")

    # Then verify the actual Stage-II role/environment envelope without calling a model.
    task = next(
        row for row in json.loads((STAGE2 / "tasks.json").read_text())["tasks"]
        if row["id"] == "T2"
    )
    runtime = RuntimeState(max_turns=32)
    runtime.task = task
    checkout_api = MetaGPTCheckout(checkout)
    provider = ScriptedProvider([{"actions": [{"type": "finalize", "answer": "unused"}]}])
    stage2_env = Environment(desc="Software Engineering")
    stage2_roles = [
        Stage2MetaRole(
            name=row["id"],
            profile=row["role"],
            goal=row["responsibility"],
            llm=Stage2ProviderLLM(provider),
            stage2_runtime=runtime,
            stage2_checkout=checkout_api,
            stage2_directory=META_DIRECTORY,
            stage2_entry=META_ROLES["entry_agent"],
        )
        for row in META_ROLES["agents"]
    ]
    stage2_env.add_roles(stage2_roles)
    stage2_env.publish_message(
        Message(
            content=task["user_request"],
            role="user",
            sent_from="USER",
            send_to={META_ROLES["entry_agent"]},
            cause_by=UserRequirement,
            metadata={"kind": "user_request"},
        )
    )
    stage2_state = adapter.serialize_stage2_environment(stage2_env)

    runtime2 = RuntimeState(max_turns=32)
    runtime2.task = task
    checkout_api2 = MetaGPTCheckout(checkout)
    provider2 = ScriptedProvider([{"actions": [{"type": "finalize", "answer": "unused"}]}])
    restored_stage2_env = adapter.restore_stage2_environment(
        state=stage2_state,
        environment_class=Environment,
        role_class=Stage2MetaRole,
        context=stage2_env.context,
        runtime=runtime2,
        checkout_api=checkout_api2,
        directory=META_DIRECTORY,
        entry=META_ROLES["entry_agent"],
        llm_factory=lambda _role: Stage2ProviderLLM(provider2),
    )
    if digest(adapter.serialize_stage2_environment(restored_stage2_env)) != digest(stage2_state):
        raise RuntimeError("Stage-II MetaGPT role/environment state did not restore")

    runtime.turns = 3
    runtime.history = [{"turn": 1, "role": "release_lead"}]
    runtime_payload = runtime_state_payload(runtime)
    restore_runtime_state(runtime2, runtime_payload)
    if digest(runtime_state_payload(runtime2)) != digest(runtime_payload):
        raise RuntimeError("Stage-II MetaGPT runtime envelope did not round-trip")

    manifest = registry.capture(
        system_id="X2_METAGPT",
        group_id="SMOKE",
        run_id="metagpt-smoke",
        task_id="T2",
        event_ref="AFTER_NATIVE_MODEL_TURN",
        adapter_id="stage2-r7-metagpt-native-checkpoint-v1",
        framework_binding=adapter.framework_binding,
        native_state={
            "stage2_environment": stage2_state,
            "stage2_runtime": runtime_payload,
        },
        application_root=checkout,
        model_visible_context={"role": "release_lead", "turn": 3},
        remaining_horizon=29,
        restore_capability="FULL_NATIVE",
        replication_binding=_replication_binding(),
    )

    return {
        "schema": "stage2-r7-metagpt-checkpoint-smoke-v1",
        "status": "PASS",
        "native_api": ["Environment.model_dump", "Environment(**state, context=context)"],
        "checkpoint_hash": manifest["checkpoint_hash"],
        "environment_round_trip": "PASS",
        "stage2_role_environment_round_trip": "PASS",
        "stage2_runtime_envelope_round_trip": "PASS",
        "provider_calls": 0,
    }


def smoke_a2a(destination: Path) -> dict:
    from stage2.native_v7.x3_a2a.service import DIRECTORY
    from stage2.r7_checkpoint_v1.a2a_adapter import (
        A2ANativeCheckpointAdapter,
        CheckpointableRoleRuntime,
    )

    checkout = _fixture(destination)
    registry = _registry(destination)
    directory = {role: f"http://127.0.0.1:{9000+i}" for i, role in enumerate(DIRECTORY)}
    directory_file = destination / "directory.json"
    directory_file.write_text(json.dumps(directory, sort_keys=True) + "\n")

    script = {
        role: [{"actions": [{"type": "finalize", "answer": f"{role} smoke"}]}]
        for role in DIRECTORY
    }
    script_file = destination / "script.json"
    script_file.write_text(json.dumps(script, sort_keys=True) + "\n")

    runtimes1 = {
        role: CheckpointableRoleRuntime(
            role=role,
            checkout=checkout,
            directory_file=directory_file,
            mode="scripted",
            script_file=script_file,
        )
        for role in DIRECTORY
    }
    for i, role in enumerate(sorted(runtimes1)):
        runtimes1[role].sessions["smoke-session"] = {
            "messages": [{"from": "USER", "kind": "smoke", "content": role}],
            "observations": [{"kind": "tool_result", "content": i}],
        }

    adapter = A2ANativeCheckpointAdapter()
    state = adapter.aggregate_role_states(runtimes1)
    manifest = registry.capture(
        system_id="X3_A2A",
        group_id="SMOKE",
        run_id="a2a-smoke",
        task_id="T2",
        event_ref="AFTER_COMPLETED_ROLE_SERVICE_CALL",
        adapter_id="stage2-r7-a2a-role-service-checkpoint-v1",
        framework_binding=adapter.framework_binding,
        native_state=state,
        application_root=checkout,
        model_visible_context={"boundary": "quiescent-role-service"},
        remaining_horizon=25,
        restore_capability="FULL_NATIVE",
        replication_binding=_replication_binding(),
    )

    runtimes2 = {
        role: CheckpointableRoleRuntime(
            role=role,
            checkout=checkout,
            directory_file=directory_file,
            mode="scripted",
            script_file=script_file,
        )
        for role in DIRECTORY
    }
    adapter.restore_role_states(
        role_runtimes=runtimes2,
        state=registry.load_native_state(manifest["checkpoint_hash"]),
    )
    if digest(adapter.aggregate_role_states(runtimes2)) != digest(state):
        raise RuntimeError("A2A role-service global state did not round-trip")

    return {
        "schema": "stage2-r7-a2a-checkpoint-smoke-v1",
        "status": "PASS",
        "checkpoint_hash": manifest["checkpoint_hash"],
        "role_count": len(runtimes1),
        "role_service_state_round_trip": "PASS",
        "a2a_protocol_modified": False,
        "provider_calls": 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", choices=["registry", "autogen", "metagpt", "a2a"], required=True)
    parser.add_argument("--out-root")
    args = parser.parse_args()

    def run(root: Path):
        if args.system == "registry":
            return smoke_registry(root)
        if args.system == "autogen":
            return asyncio.run(smoke_autogen(root))
        if args.system == "metagpt":
            return smoke_metagpt(root)
        return smoke_a2a(root)

    if args.out_root:
        root = Path(args.out_root)
        root.mkdir(parents=True, exist_ok=False)
        result = run(root)
        (root / "checkpoint-smoke-report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
    else:
        with tempfile.TemporaryDirectory() as td:
            result = run(Path(td))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
