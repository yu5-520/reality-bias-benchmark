from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Any

from arena.providers import DeepSeekArenaProvider
from stage2.native_v7.software_host_v1 import ROLES, TASKS
from stage2.r7_checkpoint_v1.common import CheckpointRegistry, digest
from stage2.r7_checkpoint_v1.controller import ProspectiveCheckpointController
from stage2.r7_prospective_v1.host import ProspectiveCheckpointedSoftwareEngineeringHost
from stage2.r7_prospective_v1.integration import HostIntegratedCheckpointMonitorHook
from stage2.r7_prospective_v1.online_monitor import OnlineStructuralMonitor
from stage2.r7_prospective_v1.recorders import HostBoundaryCheckpointRecorder
from stage2.r7_prospective_v1.run_manifest import build_run_manifest
from stage2.r7_prospective_v1.runtime_event_adapter import (
    PassiveActionTapProvider,
    RuntimeStructuralBridge,
)

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "stage2"
CANONICAL_SUBJECT = json.loads((STAGE2 / "subject.json").read_text())


def _load_inputs(task_file, roles_file, subject_file):
    task = json.loads(Path(task_file).read_text())
    roles = json.loads(Path(roles_file).read_text())
    subject = json.loads(Path(subject_file).read_text())
    if task.get("id") not in TASKS or task != TASKS[task["id"]]:
        raise ValueError("task file differs from frozen T1-T3")
    if roles != ROLES:
        raise ValueError("roles file differs from frozen nine-role roster")
    if subject != CANONICAL_SUBJECT:
        raise ValueError("subject file differs from frozen subject profile")
    return task, subject


def _build_subject_provider(subject):
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("prospective G1 subject mode requires DEEPSEEK_API_KEY")
    source = ROOT / subject["source_config"]
    config = json.loads(source.read_text())
    if (
        config["provider"] != subject["provider"]
        or config["model_alias"] != subject["model_alias"]
        or config["expected_model_version"] != subject["expected_model_version"]
        or config["subject"] != subject["subject"]
    ):
        raise ValueError("DeepSeek source configuration differs from frozen subject")
    return DeepSeekArenaProvider(config)


class ProspectiveRAGHost(ProspectiveCheckpointedSoftwareEngineeringHost):
    def __init__(self, *, rag_context, **kwargs):
        super().__init__(**kwargs)
        self.rag_context = rag_context

    def _prompt(self, role, observations):
        messages = super()._prompt(role, observations)
        return self.rag_context.enrich(messages, role=role, task=self.task)


class ProspectiveMemoryBankHost(ProspectiveCheckpointedSoftwareEngineeringHost):
    def __init__(self, *, memory_context, **kwargs):
        super().__init__(**kwargs)
        self.memory_context = memory_context

    def _prompt(self, role, observations):
        messages = super()._prompt(role, observations)
        return self.memory_context.enrich(messages, role=role, task=self.task)

    async def _complete(self, messages, *, role, turn):
        response = await super()._complete(messages, role=role, turn=turn)
        self.memory_context.remember(role=role, response=response)
        return response


class ProspectiveLongLLMLinguaHost(ProspectiveCheckpointedSoftwareEngineeringHost):
    def __init__(self, *, compressor_context, **kwargs):
        super().__init__(**kwargs)
        self.compressor_context = compressor_context

    def _prompt(self, role, observations):
        messages = super()._prompt(role, observations)
        return self.compressor_context.enrich(messages, role=role, task=self.task)


def _write_json(path: Path, value: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


async def run_capability_natural_A(
    *,
    system: str,
    checkout,
    task_file,
    roles_file,
    subject_file,
    out_root,
    provider=None,
    x6_upstream=None,
    x6_embedding_model=None,
    x6_embedding_manifest=None,
    x7_checkpoint=None,
    x7_checkpoint_manifest=None,
):
    if system not in {"X4", "X5", "X6", "X7"}:
        raise ValueError("capability runner supports X4-X7")
    task, subject = _load_inputs(task_file, roles_file, subject_file)
    out = Path(out_root)
    out.mkdir(parents=True, exist_ok=False)
    checkpoint_root = out / "checkpoints"
    capability_observer = out / "capability_observer"

    subject_mode = provider is None
    active_provider = provider if provider is not None else _build_subject_provider(subject)
    tap = PassiveActionTapProvider(active_provider)
    registry = CheckpointRegistry(checkpoint_root)
    controller = ProspectiveCheckpointController()
    monitor = OnlineStructuralMonitor(mode="PACKAGE_FREEZE")

    system_ids = {
        "X4": "X4_MCP",
        "X5": "X5_RAG",
        "X6": "X6_MEMORYBANK",
        "X7": "X7_LONGLINGUA",
    }
    recorder = HostBoundaryCheckpointRecorder(
        registry=registry,
        controller=controller,
        system_id=system_ids[system],
        group_id="StageII-R7-G1",
        run_id=f"StageII-R7-G1-{system}-{task['id']}",
        task_id=task["id"],
    )
    bridge = RuntimeStructuralBridge(
        tap=tap,
        monitor=monitor,
        controller=controller,
        cell_id=f"{system}-{task['id']}",
    )
    hook = HostIntegratedCheckpointMonitorHook(recorder=recorder, bridge=bridge)

    context = None
    if system == "X4":
        from stage2.native_v7.x4_mcp.runner import MCPCheckoutProxy

        host = ProspectiveCheckpointedSoftwareEngineeringHost(
            task_id=task["id"],
            checkout=checkout,
            provider=tap,
            max_turns=int(subject["limits"]["max_turns"]),
            checkpoint_hook=hook,
        )
        host.checkout = MCPCheckoutProxy(checkout, observer_root=capability_observer)
        framework_binding = {
            "system": "X4_MCP",
            "protocol": "MCP",
            "host": "software_engineering_host_v1",
        }
    elif system == "X5":
        from stage2.native_v7.x5_rag.context import FrozenRAGContext

        context = FrozenRAGContext(observer_root=capability_observer, limit=3)
        host = ProspectiveRAGHost(
            rag_context=context,
            task_id=task["id"],
            checkout=checkout,
            provider=tap,
            max_turns=int(subject["limits"]["max_turns"]),
            checkpoint_hook=hook,
        )
        framework_binding = {
            "system": "X5_RAG",
            "retrieval": "stage2.retrieval.retrieve",
            "host": "software_engineering_host_v1",
        }
    elif system == "X6":
        from stage2.native_v7.x6_memorybank.context import OfficialMemoryBankContext

        if not all([x6_upstream, x6_embedding_model, x6_embedding_manifest]):
            raise ValueError("X6 requires frozen upstream and embedding assets")
        context = OfficialMemoryBankContext(
            upstream_root=x6_upstream,
            embedding_model=x6_embedding_model,
            embedding_manifest=x6_embedding_manifest,
            memory_root=out / "memorybank_state",
            observer_root=capability_observer,
            top_k=3,
        )
        host = ProspectiveMemoryBankHost(
            memory_context=context,
            task_id=task["id"],
            checkout=checkout,
            provider=tap,
            max_turns=int(subject["limits"]["max_turns"]),
            checkpoint_hook=hook,
        )
        framework_binding = {
            "system": "X6_MEMORYBANK",
            "upstream": "MemoryBank-SiliconFriend",
            "host": "software_engineering_host_v1",
        }
    else:
        from stage2.native_v7.x7_longllmlingua.context import (
            FrozenLongLLMLinguaContext,
            checkpoint_hashes,
        )
        from stage2.native_v7.x7_longllmlingua.runner import _load_checkpoint_manifest

        if not x7_checkpoint or not x7_checkpoint_manifest:
            raise ValueError("X7 requires frozen LongLLMLingua checkpoint assets")
        expected_hashes = _load_checkpoint_manifest(x7_checkpoint_manifest)
        if checkpoint_hashes(x7_checkpoint) != expected_hashes:
            raise ValueError("X7 checkpoint differs from frozen manifest")
        context = FrozenLongLLMLinguaContext(
            checkpoint=x7_checkpoint,
            expected_hashes=expected_hashes,
            observer_root=capability_observer,
            rate=0.5,
        )
        host = ProspectiveLongLLMLinguaHost(
            compressor_context=context,
            task_id=task["id"],
            checkout=checkout,
            provider=tap,
            max_turns=int(subject["limits"]["max_turns"]),
            checkpoint_hook=hook,
        )
        framework_binding = {
            "system": "X7_LONGLINGUA",
            "package": "llmlingua==0.2.2",
            "host": "software_engineering_host_v1",
        }

    failure = None
    result = None
    try:
        result = await host.run()
    except Exception as exc:
        failure = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        raise
    finally:
        if context is not None:
            context.seal()
        if result is not None:
            _write_json(out / "natural_A_result.json", result)
        if failure is not None:
            _write_json(out / "failure.json", failure)
        _write_json(out / "checkpoint_ledger.json", controller.ledger())
        _write_json(out / "monitor_evidence.json", monitor.evidence())
        _write_json(out / "monitor_candidates.json", monitor.candidates())
        _write_json(out / "repair_packages.json", monitor.packages())
        _write_json(out / "runtime_bridge.json", bridge.snapshot())

    if tap.total_records > int(subject["limits"]["max_turns"]):
        raise RuntimeError("prospective natural A exceeded frozen model-turn ceiling")
    if result is None:
        raise RuntimeError("prospective natural A produced no result")

    manifest = build_run_manifest(
        cell_id=f"{system}-{task['id']}",
        framework_binding=framework_binding,
        checkpoint_ledger=controller.ledger(),
        natural_result=result,
        monitor_snapshot=bridge.snapshot(),
        packages=monitor.packages(),
        natural_subject_calls=tap.total_records if subject_mode else 0,
    )
    _write_json(out / "run_manifest.json", manifest)
    seal = {
        "schema": "RB-STAGE2-R7-G1-NATURAL-A-SEAL-v1",
        "group_id": "StageII-R7-G1",
        "cell_id": f"{system}-{task['id']}",
        "status": "NATURAL_A_FROZEN_PENDING_REPAIR_GATE",
        "natural_subject_calls": tap.total_records if subject_mode else 0,
        "model_decision_count": tap.total_records,
        "provider_mode": "SUBJECT" if subject_mode else "NON_STUDY_INJECTED",
        "checkpoint_count": len(controller.ledger()["checkpoints"]),
        "structural_event_count": len(monitor.evidence()),
        "candidate_count": len(monitor.candidates()),
        "package_count": len(monitor.packages()),
        "complete_package_count": sum(
            1 for row in monitor.packages()
            if row["repair_gate_status"] == "COMPLETE_FOR_STRUCTURED_REPAIR"
        ),
        "run_manifest_hash": manifest["manifest_hash"],
        "natural_result_hash": digest(result),
        "repair_actions_during_A": 0,
        "semantic_audit_state": "LOCKED_UNTIL_A_AND_B_FROZEN",
    }
    _write_json(out / "seal.json", seal)
    return seal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", required=True, choices=["X4","X5","X6","X7"])
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--roles-file", required=True)
    parser.add_argument("--subject-file", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--x6-upstream")
    parser.add_argument("--x6-embedding-model")
    parser.add_argument("--x6-embedding-manifest")
    parser.add_argument("--x7-checkpoint")
    parser.add_argument("--x7-checkpoint-manifest")
    args = parser.parse_args()
    result = asyncio.run(
        run_capability_natural_A(
            system=args.system,
            checkout=args.checkout,
            task_file=args.task_file,
            roles_file=args.roles_file,
            subject_file=args.subject_file,
            out_root=args.out_root,
            x6_upstream=args.x6_upstream,
            x6_embedding_model=args.x6_embedding_model,
            x6_embedding_manifest=args.x6_embedding_manifest,
            x7_checkpoint=args.x7_checkpoint,
            x7_checkpoint_manifest=args.x7_checkpoint_manifest,
        )
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
