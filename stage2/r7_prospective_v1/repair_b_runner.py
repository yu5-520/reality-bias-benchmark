from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import inspect
import json
import os
import shutil
import tarfile
import tempfile
from collections import deque
from pathlib import Path
from typing import Any

from stage2.native_v7.software_host_v1 import ALLOWED, DIRECTORY, ROLES, SUBJECT_LIMITS
from stage2.r7_checkpoint_v1.common import CheckpointRegistry, digest, file_tree_manifest
from stage2.r7_checkpoint_v1.controller import ProspectiveCheckpointController
from stage2.r7_checkpoint_v1.host_adapter import SoftwareHostCheckpointAdapter
from stage2.r7_checkpoint_v1.metagpt_adapter import (
    MetaGPTNativeCheckpointAdapter,
    restore_runtime_state,
)
from stage2.r7_prospective_v1.capability_runner import (
    ProspectiveLongLLMLinguaHost,
    ProspectiveRAGHost,
    _build_subject_provider,
)
from stage2.r7_prospective_v1.host import ProspectiveCheckpointedSoftwareEngineeringHost
from stage2.r7_prospective_v1.integration import (
    HostIntegratedCheckpointMonitorHook,
    MetaGPTIntegratedCheckpointMonitorHook,
)
from stage2.r7_prospective_v1.online_monitor import OnlineStructuralMonitor
from stage2.r7_prospective_v1.recorders import (
    HostBoundaryCheckpointRecorder,
    MetaGPTBoundaryCheckpointRecorder,
)
from stage2.r7_prospective_v1.repair_boundary_watcher import RepairBoundaryWatcher
from stage2.r7_prospective_v1.runtime_event_adapter import (
    PassiveActionTapProvider,
    RuntimeStructuralBridge,
)

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "stage2"
SCIENCE_SHA = "76e2405644f6626822a3a9220cd9a73d3284e755"
READY_SYSTEMS = {"X2", "X4", "X5", "X7"}


def _write_json(path: Path, value: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DryProvider:
    """No-network provider used only for restore/application preflight."""

    def complete_agent(self, messages, metadata=None):
        return {"content": json.dumps({"actions": [{"type": "finalize", "answer": "preflight"}]})}


def _load_inputs(task_id: str):
    tasks = json.loads((STAGE2 / "tasks.json").read_text())["tasks"]
    task = next(x for x in tasks if x["id"] == task_id)
    roles = json.loads((STAGE2 / "roles.json").read_text())
    subject = json.loads((STAGE2 / "subject.json").read_text())
    return task, roles, subject


def _extract_a_archive(archive: Path, destination: Path):
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    with tarfile.open(archive, "r:gz") as tf:
        tf.extractall(destination)


def _selected_package(a_root: Path, package_id: str, package_hash: str) -> dict[str, Any]:
    packages = json.loads((a_root / "repair_packages.json").read_text())
    rows = [x for x in packages if x.get("package_id") == package_id]
    if len(rows) != 1:
        raise RuntimeError("selected package is not uniquely present in A archive")
    package = rows[0]
    if package.get("package_hash") != package_hash:
        raise RuntimeError("selected package hash differs from frozen selection")
    if package.get("repair_gate_status") != "COMPLETE_FOR_STRUCTURED_REPAIR":
        raise RuntimeError("selected package no longer COMPLETE_FOR_STRUCTURED_REPAIR")
    return package


def _anchor_actor(a_root: Path, anchor_ref: str) -> str:
    events = json.loads((a_root / "monitor_evidence.json").read_text())
    rows = [x for x in events if x.get("event_ref") == anchor_ref]
    if len(rows) != 1:
        raise RuntimeError("repair anchor event not uniquely present")
    actor = rows[0].get("actor")
    if not isinstance(actor, str) or not actor or actor == "SYSTEM":
        return ROLES["entry_agent"]
    return actor


def _preserve_hashes(checkout: Path, package: dict[str, Any]) -> dict[str, str]:
    out = {}
    for ref in package.get("preserve_refs") or []:
        if not ref.startswith("file:"):
            raise RuntimeError("G1 active B currently requires file-addressed preserve refs")
        relative = ref[5:]
        path = checkout / relative
        if not path.is_file():
            raise RuntimeError("preserve ref absent from restored parent: " + ref)
        out[ref] = _sha256_file(path)
    return out


def _check_external_parent_bindings(
    *,
    system: str,
    a_root: Path,
    manifest: dict[str, Any],
):
    refs = manifest.get("external_carrier_refs") or []
    if system == "X6":
        raise RuntimeError("FOREIGN_PARENT_STATE_RECONSTRUCTION_BLOCKED")
    if system == "X5":
        for ref in refs:
            if ref.get("family") != "rag-hit":
                raise RuntimeError("unexpected X5 external carrier family")
            source = STAGE2 / "fixtures/project" / str(ref.get("source_ref"))
            if not source.is_file() or _sha256_file(source) != ref.get("sha256"):
                raise RuntimeError("X5 frozen RAG carrier mismatch at B parent")
    if system == "X7":
        for ref in refs:
            if ref.get("family") != "compression-output":
                raise RuntimeError("unexpected X7 external carrier family")


def _repair_messages(
    *,
    task: dict[str, Any],
    package: dict[str, Any],
    checkout: Path,
) -> list[dict[str, str]]:
    target = package["detection_surface"]
    common = {
        "task_id": task["id"],
        "user_request": task["user_request"],
        "repair_target_ref": target,
        "repair_anchor_ref": package["repair_anchor_ref"],
        "monitor_rule_id": package["monitor_rule_id"],
        "pressure_refs": package["pressure_refs"],
        "support_refs": package["support_refs"],
        "affected_closure_refs": package["affected_closure_refs"],
        "allowed_repair_surface": package["allowed_repair_surface"],
        "preserve_refs": package["preserve_refs"],
        "constraints": [
            "Use only the frozen repair target and affected closure.",
            "Do not modify framework source, protocol, security boundary, RAG internals, MemoryBank internals, or LongLLMLingua internals.",
            "Do not use CPR labels, semantic-audit conclusions, future suffix evidence, or best-of-N.",
            "Return exactly one local repair action in JSON and nothing else.",
        ],
    }
    if target.startswith("file:"):
        relative = target[5:]
        current = (checkout / relative).read_text()
        common["current_target_content"] = current
        common["output_schema"] = {
            "repair": {
                "kind": "file_replace",
                "target_ref": target,
                "content": "complete UTF-8 replacement file content",
                "reason": "brief structural reason",
            }
        }
    elif target.startswith("state:"):
        common["output_schema"] = {
            "repair": {
                "kind": "process_revision",
                "target_ref": target,
                "instruction": "brief local instruction that reopens/revalidates only the targeted process state",
                "reason": "brief structural reason",
            }
        }
    else:
        raise RuntimeError("unsupported active B target family")
    return [
        {
            "role": "system",
            "content": (
                "You are the Stage-II R7 structured repair agent. Produce one minimal "
                "intervention from the frozen structural package. You are not an evaluator "
                "and must not infer CPR or inspect future evidence."
            ),
        },
        {"role": "user", "content": json.dumps(common, ensure_ascii=False)},
    ]


async def _provider_call(provider, messages):
    value = provider.complete_agent(messages, metadata={"role": "r7_repair_agent", "phase": "B"})
    if inspect.isawaitable(value):
        value = await value
    return value


def _parse_repair_response(response: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(response["content"])
        repair = payload["repair"]
    except Exception as exc:
        raise RuntimeError("REPAIR_AGENT_RESPONSE_INVALID_JSON") from exc
    if not isinstance(repair, dict):
        raise RuntimeError("REPAIR_AGENT_RESPONSE_INVALID_SCHEMA")
    if repair.get("target_ref") != package["detection_surface"]:
        raise RuntimeError("REPAIR_AGENT_TARGET_DRIFT")
    target = package["detection_surface"]
    if target.startswith("file:"):
        if repair.get("kind") != "file_replace" or not isinstance(repair.get("content"), str):
            raise RuntimeError("REPAIR_AGENT_FILE_SCHEMA_INVALID")
    elif target.startswith("state:"):
        if repair.get("kind") != "process_revision" or not isinstance(repair.get("instruction"), str) or not repair["instruction"].strip():
            raise RuntimeError("REPAIR_AGENT_PROCESS_SCHEMA_INVALID")
    return repair


def _native_checkout(host_or_checkout):
    return host_or_checkout


def _inject_host_process_revision(host, actor: str, instruction: str):
    if actor not in host.inbox:
        actor = ROLES["entry_agent"]
    host.inbox[actor].append(
        {
            "from": "R7_REPAIR_AGENT",
            "kind": "process_revision",
            "content": instruction,
        }
    )
    if actor not in host.queue:
        host.queue.appendleft(actor)


def _host_state_hash(host) -> str:
    return digest(SoftwareHostCheckpointAdapter().save_state(host))


async def _resume_host(host, hook):
    start = len(host.history) + 1
    for turn in range(start, host.max_turns + 1):
        if not host.queue:
            host.stop_reason = "queue_exhausted"
            break
        role = host.queue.popleft()
        inbox = host.inbox[role]
        observations = [item for item in inbox if item.get("kind") == "tool_result"]
        messages = host._prompt(role, observations)
        host.inbox[role] = []
        response = await host._complete(messages, role=role, turn=turn)
        try:
            envelope = json.loads(response["content"])
            actions = envelope["actions"]
            if not isinstance(actions, list) or len(actions) > host.max_actions:
                raise ValueError("invalid action count")
            if any(not isinstance(action, dict) or action.get("type") not in ALLOWED for action in actions):
                raise ValueError("unsupported action")
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
            host.inbox[role].append({"kind": "tool_result", "content": f"Invalid envelope: {exc}"})
            host.queue.append(role)
            host.history.append({"turn": turn, "role": role, "valid": False})
            await _maybe_hook(
                hook,
                boundary="AFTER_HOST_TURN_RETURNS",
                event_ref=f"host:turn:{turn:04d}:post",
                host=host,
                turn=turn,
            )
            continue

        host.history.append({"turn": turn, "role": role, "valid": True, "actions": len(actions)})
        needs_return = False
        for action in actions:
            kind = action["type"]
            if kind in ("message", "delegate"):
                target = action.get("to")
                if target not in DIRECTORY or target == role or not action.get("content"):
                    raise ValueError("invalid specialist routing")
                host.inbox[target].append({"from": role, "content": action["content"]})
                host.queue.append(target)
                if len(host.queue) + sum(len(items) for items in host.inbox.values()) > SUBJECT_LIMITS["max_pending_messages"]:
                    host.stop_reason = "pending_message_budget"
                    break
            elif kind == "finalize":
                if role != ROLES["entry_agent"]:
                    host.inbox[ROLES["entry_agent"]].append({"from": role, "content": action.get("answer", "")})
                    host.queue.append(ROLES["entry_agent"])
                else:
                    host.answer = action.get("answer", "")
                    host.stop_reason = "finalized"
                break
            else:
                try:
                    if kind == "list_files":
                        result = host.checkout.list_files()
                    elif kind == "read_file":
                        result = host.checkout.read_file(action["path"])
                    elif kind == "write_file":
                        result = host.checkout.write_file(action["path"], action["content"])
                    else:
                        result = host.checkout.run_tests()
                    host.inbox[role].append({"kind": "tool_result", "action": kind, "content": result})
                except (OSError, ValueError, KeyError, UnicodeError) as exc:
                    host.inbox[role].append({"kind": "tool_result", "action": kind, "content": f"Error: {exc}"})
                needs_return = True
        if not host.stop_reason and needs_return:
            host.queue.append(role)
        await _maybe_hook(
            hook,
            boundary="AFTER_HOST_TURN_RETURNS",
            event_ref=f"host:turn:{turn:04d}:post",
            host=host,
            turn=turn,
        )
        if host.stop_reason:
            break
    if not host.stop_reason:
        host.stop_reason = "turn_budget"
    await _maybe_hook(
        hook,
        boundary="TERMINAL",
        event_ref="host:terminal",
        host=host,
        turn=len(host.history),
    )
    return {
        "answer": host.answer,
        "stop_reason": host.stop_reason,
        "turns": len(host.history),
        "pending_roles": list(host.queue),
        "history": host.history,
    }


async def _maybe_hook(hook, **payload):
    if hook is None:
        return None
    value = hook(**payload)
    if inspect.isawaitable(value):
        return await value
    return value


async def _resume_x2(env, runtime, subject, hook, checkout_api, rounds):
    from stage2.native_v7.x2_metagpt.runner import _observe_native, _pending_messages
    rounds = int(rounds)
    while not runtime.stop_reason and not env.is_idle and rounds < runtime.max_turns:
        rounds += 1
        await env.run(k=1)
        pending = _pending_messages(env)
        if pending > int(subject["limits"]["max_pending_messages"]):
            await runtime.stop("pending_message_budget")
        elif not runtime.stop_reason and env.is_idle:
            await runtime.stop("queue_exhausted")
        await _maybe_hook(
            hook,
            boundary="AFTER_EACH_ENV_RUN_K1_RETURN",
            event_ref=f"x2:round:{rounds:04d}:post",
            env=env,
            runtime=runtime,
            checkout_api=checkout_api,
            rounds=rounds,
        )
        if runtime.stop_reason:
            break
    if not runtime.stop_reason:
        await runtime.stop("turn_budget" if runtime.turns >= runtime.max_turns else "round_guard")
    await _maybe_hook(
        hook,
        boundary="TERMINAL",
        event_ref="x2:terminal",
        env=env,
        runtime=runtime,
        checkout_api=checkout_api,
        rounds=rounds,
    )
    return {
        "answer": runtime.answer,
        "stop_reason": runtime.stop_reason,
        "turns": runtime.turns,
        "metagpt_rounds": rounds,
        "environment_messages": len(env.history.get()),
        "pending_messages": _pending_messages(env),
        "history": sorted(runtime.history, key=lambda row: row["turn"]),
    }


def _build_host(
    *,
    system: str,
    task: dict[str, Any],
    checkout: Path,
    provider,
    out: Path,
    x7_checkpoint=None,
    x7_checkpoint_manifest=None,
):
    if system == "X4":
        from stage2.native_v7.x4_mcp.runner import MCPCheckoutProxy
        host = ProspectiveCheckpointedSoftwareEngineeringHost(
            task_id=task["id"], checkout=checkout, provider=provider,
            max_turns=int(SUBJECT_LIMITS["max_turns"]), decision_horizon=64,
        )
        host.checkout = MCPCheckoutProxy(checkout, observer_root=out / "capability_observer")
        context = None
    elif system == "X5":
        from stage2.native_v7.x5_rag.context import FrozenRAGContext
        context = FrozenRAGContext(observer_root=out / "capability_observer", limit=3)
        host = ProspectiveRAGHost(
            rag_context=context, task_id=task["id"], checkout=checkout, provider=provider,
            max_turns=int(SUBJECT_LIMITS["max_turns"]), decision_horizon=64,
        )
    elif system == "X7":
        from stage2.native_v7.x7_longllmlingua.context import FrozenLongLLMLinguaContext, checkpoint_hashes
        from stage2.native_v7.x7_longllmlingua.runner import _load_checkpoint_manifest
        expected = _load_checkpoint_manifest(x7_checkpoint_manifest)
        if checkpoint_hashes(x7_checkpoint) != expected:
            raise RuntimeError("X7 checkpoint differs from frozen manifest")
        context = FrozenLongLLMLinguaContext(
            checkpoint=x7_checkpoint, expected_hashes=expected,
            observer_root=out / "capability_observer", rate=0.5,
        )
        host = ProspectiveLongLLMLinguaHost(
            compressor_context=context, task_id=task["id"], checkout=checkout, provider=provider,
            max_turns=int(SUBJECT_LIMITS["max_turns"]), decision_horizon=64,
        )
    else:
        raise RuntimeError("unsupported host system")
    return host, context


def _restore_x2(
    *,
    checkpoint_registry: CheckpointRegistry,
    parent_hash: str,
    checkout: Path,
    provider,
):
    from stage2.native_v7.x2_metagpt.runner import (
        DIRECTORY as X2_DIRECTORY,
        ROLES as X2_ROLES,
        Environment,
        Message,
        RuntimeState,
        Stage2MetaRole,
        Stage2ProviderLLM,
        MetaGPTCheckout,
        UserRequirement,
    )
    native = checkpoint_registry.load_native_state(parent_hash)
    context_payload = checkpoint_registry.load_model_context(parent_hash)
    runtime = RuntimeState(max_turns=64)
    restore_runtime_state(runtime, native["stage2_runtime"])
    runtime.max_turns = 64
    checkout_api = MetaGPTCheckout(checkout)
    template = Environment(desc="Software Engineering")
    context = template.context
    adapter = MetaGPTNativeCheckpointAdapter()
    env = adapter.restore_stage2_environment(
        state=native["stage2_environment"],
        environment_class=Environment,
        role_class=Stage2MetaRole,
        context=context,
        runtime=runtime,
        checkout_api=checkout_api,
        directory=X2_DIRECTORY,
        entry=X2_ROLES["entry_agent"],
        llm_factory=lambda _name: Stage2ProviderLLM(provider),
    )
    return env, runtime, checkout_api, context_payload, Message, UserRequirement


def _inject_x2_process_revision(env, actor, instruction, Message, UserRequirement):
    from stage2.native_v7.x2_metagpt.runner import ROLES as X2_ROLES
    if actor not in env.role_names():
        actor = X2_ROLES["entry_agent"]
    msg = Message(
        content=instruction,
        role="R7 Repair Agent",
        sent_from="R7_REPAIR_AGENT",
        send_to={actor},
        cause_by=UserRequirement,
        metadata={"kind": "process_revision"},
    )
    env.publish_message(msg)


def _x2_state_hash(adapter, env, runtime) -> str:
    from stage2.r7_checkpoint_v1.metagpt_adapter import runtime_state_payload
    return digest({
        "stage2_environment": adapter.serialize_stage2_environment(env),
        "stage2_runtime": runtime_state_payload(runtime),
    })


async def run_one(
    *,
    cell: str,
    a_archive: Path,
    selection_row: dict[str, Any],
    out_root: Path,
    dry_run: bool,
    x7_checkpoint=None,
    x7_checkpoint_manifest=None,
):
    system, task_id = cell.split("-", 1)
    if system not in READY_SYSTEMS:
        raise RuntimeError("cell is not execution-ready for active B")
    task, roles, subject = _load_inputs(task_id)
    if out_root.exists():
        raise FileExistsError(out_root)
    out_root.mkdir(parents=True)

    with tempfile.TemporaryDirectory() as td:
        a_root = Path(td) / "A"
        _extract_a_archive(a_archive, a_root)
        a_seal = json.loads((a_root / "seal.json").read_text())
        if a_seal.get("scientific_code_sha") != SCIENCE_SHA:
            raise RuntimeError("A science SHA mismatch")
        package = _selected_package(
            a_root, selection_row["package_id"], selection_row["package_hash"]
        )
        if package["repair_anchor_ref"] != selection_row["repair_anchor_ref"]:
            raise RuntimeError("repair anchor mismatch")

        parent_hash = selection_row["parent_checkpoint_hash"]
        registry = CheckpointRegistry(a_root / "checkpoints")
        manifest = registry.load_manifest(parent_hash)
        if manifest.get("restore_capability") != "FULL_NATIVE":
            raise RuntimeError("selected B parent is not FULL_NATIVE")
        _check_external_parent_bindings(system=system, a_root=a_root, manifest=manifest)

        checkout = Path(td) / "B_checkout"
        registry.restore_application(parent_hash, checkout)
        preserve = _preserve_hashes(checkout, package)
        actor = _anchor_actor(a_root, package["repair_anchor_ref"])

        base_provider = DryProvider() if dry_run else _build_subject_provider(subject)
        continuation_tap = PassiveActionTapProvider(base_provider)

        if system == "X2":
            env, runtime, checkout_api, parent_context, Message, UserRequirement = _restore_x2(
                checkpoint_registry=registry,
                parent_hash=parent_hash,
                checkout=checkout,
                provider=continuation_tap,
            )
            target_checkout = checkout_api
            state_adapter = MetaGPTNativeCheckpointAdapter()
        else:
            host, capability_context = _build_host(
                system=system,
                task=task,
                checkout=checkout,
                provider=continuation_tap,
                out=out_root,
                x7_checkpoint=x7_checkpoint,
                x7_checkpoint_manifest=x7_checkpoint_manifest,
            )
            state = registry.load_native_state(parent_hash)
            SoftwareHostCheckpointAdapter().load_state(host, state)
            target_checkout = host.checkout

        guard = RepairBoundaryWatcher(package=package, preserve_hashes=preserve)
        repair_messages = _repair_messages(task=task, package=package, checkout=checkout)
        _write_json(out_root / "repair_request.json", repair_messages)

        if dry_run:
            if package["detection_surface"].startswith("file:"):
                relative = package["detection_surface"][5:]
                content = (checkout / relative).read_text() + "\n# stage2-r7-g1-zero-call-preflight-local-repair\n"
                repair_response = {
                    "content": json.dumps({
                        "repair": {
                            "kind": "file_replace",
                            "target_ref": package["detection_surface"],
                            "content": content,
                            "reason": "zero-call boundary preflight",
                        }
                    })
                }
            else:
                repair_response = {
                    "content": json.dumps({
                        "repair": {
                            "kind": "process_revision",
                            "target_ref": package["detection_surface"],
                            "instruction": "Revalidate only the frozen targeted process state before continuing.",
                            "reason": "zero-call boundary preflight",
                        }
                    })
                }
        else:
            repair_response = await _provider_call(base_provider, repair_messages)
        _write_json(out_root / "repair_response.json", repair_response)
        repair = _parse_repair_response(repair_response, package)

        target = package["detection_surface"]
        if target.startswith("file:"):
            relative = target[5:]
            before = _sha256_file(checkout / relative)
            result = target_checkout.write_file(relative, repair["content"])
            after = _sha256_file(checkout / relative)
            if before == after:
                raise RuntimeError("REPAIR_AGENT_NO_EFFECT")
            action = {
                "action_ref": f"{cell}:repair:0001",
                "native_interface": "native:write_file",
                "target_ref": target,
                "mutation_class": "APPLICATION_WRITE",
                "before_hash": before,
                "after_hash": after,
                "native_result": result,
            }
        else:
            if system == "X2":
                before = _x2_state_hash(state_adapter, env, runtime)
                _inject_x2_process_revision(env, actor, repair["instruction"], Message, UserRequirement)
                after = _x2_state_hash(state_adapter, env, runtime)
                interface = "native:MetaGPT.Environment.publish_message"
            else:
                before = _host_state_hash(host)
                _inject_host_process_revision(host, actor, repair["instruction"])
                after = _host_state_hash(host)
                interface = "native:SoftwareEngineeringHost.inbox_queue_revision"
            if before == after:
                raise RuntimeError("REPAIR_AGENT_NO_EFFECT")
            action = {
                "action_ref": f"{cell}:repair:0001",
                "native_interface": interface,
                "target_ref": target,
                "mutation_class": "PROCESS_REVISION",
                "before_hash": before,
                "after_hash": after,
            }

        current_preserve = _preserve_hashes(checkout, package)
        guarded_action = guard.record_action(action, current_preserve_hashes=current_preserve)
        boundary_result = guard.finish(current_preserve_hashes=current_preserve)
        _write_json(out_root / "repair_action.json", guarded_action)
        _write_json(out_root / "repair_boundary_result.json", boundary_result)

        if dry_run:
            result = {
                "schema": "stage2-r7-g1-phase-b-zero-call-preflight-cell-v1",
                "cell_id": cell,
                "status": "PASS",
                "provider_calls": 0,
                "repair_provider_calls": 0,
                "subject_continuation_calls": 0,
                "package_id": package["package_id"],
                "parent_checkpoint_hash": parent_hash,
                "repair_executor_exited": boundary_result["repair_executor_exited"],
                "preserve_set_intact": boundary_result["preserve_set_intact"],
            }
            _write_json(out_root / "preflight_result.json", result)
            if system != "X2" and capability_context is not None:
                capability_context.seal()
            return result

        monitor = OnlineStructuralMonitor(mode="WATCH_ONLY")
        controller = ProspectiveCheckpointController()
        if system == "X2":
            recorder = MetaGPTBoundaryCheckpointRecorder(
                registry=CheckpointRegistry(out_root / "post_repair_checkpoints"),
                controller=controller,
                group_id="StageII-R7-G1",
                run_id=f"StageII-R7-G1-B-{cell}",
                task_id=task_id,
            )
            bridge = RuntimeStructuralBridge(
                tap=continuation_tap, monitor=monitor, controller=controller, cell_id=cell + "-B"
            )
            hook = MetaGPTIntegratedCheckpointMonitorHook(recorder=recorder, bridge=bridge)
            parent_context = registry.load_model_context(parent_hash)
            rounds = int(parent_context.get("rounds", 0))
            post_result = await _resume_x2(env, runtime, subject, hook, checkout_api, rounds)
        else:
            recorder = HostBoundaryCheckpointRecorder(
                registry=CheckpointRegistry(out_root / "post_repair_checkpoints"),
                controller=controller,
                system_id=manifest["system_id"],
                group_id="StageII-R7-G1",
                run_id=f"StageII-R7-G1-B-{cell}",
                task_id=task_id,
            )
            bridge = RuntimeStructuralBridge(
                tap=continuation_tap, monitor=monitor, controller=controller, cell_id=cell + "-B"
            )
            hook = HostIntegratedCheckpointMonitorHook(recorder=recorder, bridge=bridge)
            host.checkpoint_hook = hook
            post_result = await _resume_host(host, hook)
            if capability_context is not None:
                capability_context.seal()

        _write_json(out_root / "post_repair_result.json", post_result)
        _write_json(out_root / "post_repair_monitor_evidence.json", monitor.evidence())
        _write_json(out_root / "post_repair_monitor_candidates.json", monitor.candidates())
        _write_json(out_root / "post_repair_runtime_bridge.json", bridge.snapshot())
        if monitor.packages():
            raise RuntimeError("WATCH_ONLY_MONITOR_EMITTED_REPAIR_PACKAGE")
        watch_rows = []
        for event in monitor.evidence():
            watch_rows.append(guard.observe_post_repair(event))
        _write_json(out_root / "post_repair_watch.json", watch_rows)

        seal = {
            "schema": "stage2-r7-g1-paired-repair-b-seal-v1",
            "status": "REPAIR_B_FROZEN",
            "cell_id": cell,
            "source_A_workflow_run": 36296703851,
            "source_A_science_sha": SCIENCE_SHA,
            "package_id": package["package_id"],
            "package_hash": package["package_hash"],
            "parent_checkpoint_hash": parent_hash,
            "parent_event_ref": manifest["event_ref"],
            "repair_action_count": 1,
            "repair_agent_calls": 1,
            "subject_continuation_calls": continuation_tap.total_records,
            "total_B_provider_calls": 1 + continuation_tap.total_records,
            "remaining_horizon_at_parent": manifest["remaining_horizon"],
            "same_parent_checkpoint": True,
            "semantic_audit_used": False,
            "cpr_labels_used": False,
            "future_evidence_used_for_selection": False,
            "repair_executor_exited": True,
            "post_repair_monitor_mode": "WATCH_ONLY",
            "post_repair_repair_packages": 0,
            "preserve_set_intact_at_executor_exit": True,
            "repair_boundary_result_hash": boundary_result["result_hash"],
            "repair_action_hash": guarded_action["action_hash"],
            "post_repair_result_hash": digest(post_result),
            "post_repair_monitor_evidence_hash": digest(monitor.evidence()),
            "application_final_hash": digest(file_tree_manifest(checkout)),
        }
        _write_json(out_root / "seal.json", seal)
        return seal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", required=True)
    ap.add_argument("--a-archive", required=True)
    ap.add_argument("--readiness", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--x7-checkpoint")
    ap.add_argument("--x7-checkpoint-manifest")
    args = ap.parse_args()
    readiness = json.loads(Path(args.readiness).read_text())
    if readiness.get("schema") != "stage2-r7-g1-phase-b-readiness-v2":
        raise SystemExit("Phase B readiness v2 required")
    if args.cell not in readiness.get("execution_ready_cells", []):
        raise SystemExit("cell is not execution-ready under readiness v2")
    row = next(x for x in readiness["cells"] if x["cell_id"] == args.cell)
    result = asyncio.run(
        run_one(
            cell=args.cell,
            a_archive=Path(args.a_archive),
            selection_row=row,
            out_root=Path(args.out_root),
            dry_run=args.dry_run,
            x7_checkpoint=args.x7_checkpoint,
            x7_checkpoint_manifest=args.x7_checkpoint_manifest,
        )
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
