from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from stage2.r7_checkpoint_v1.common import CheckpointRegistry, digest
from stage2.r7_checkpoint_v1.controller import ProspectiveCheckpointController
from stage2.r7_prospective_v1.integration import MetaGPTIntegratedCheckpointMonitorHook
from stage2.r7_prospective_v1.online_monitor import OnlineStructuralMonitor
from stage2.r7_prospective_v1.recorders import MetaGPTBoundaryCheckpointRecorder
from stage2.r7_prospective_v1.run_manifest import build_run_manifest
from stage2.r7_prospective_v1.evidence_channels import seal_evidence_channels
from stage2.r7_prospective_v1.replication_contract import resolve_decision_horizon, run_id, semantic_audit_state
from stage2.r7_prospective_v1.runtime_event_adapter import (
    PassiveActionTapProvider,
    RuntimeStructuralBridge,
)
from stage2.r7_prospective_v1.x2_metagpt import run_task_with_checkpoints

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "stage2"


def _write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


async def run_x2_natural_A(
    *,
    checkout,
    task_file,
    roles_file,
    subject_file,
    out_root,
    provider=None,
    group_id="StageII-R7-G1",
    decision_horizon=None,
):
    task = json.loads(Path(task_file).read_text())
    out = Path(out_root)
    out.mkdir(parents=True, exist_ok=False)
    subject_mode = provider is None
    active_provider = provider
    if active_provider is None:
        from stage2.native_v7.x2_metagpt.runner import build_subject_provider
        subject = json.loads(Path(subject_file).read_text())
        active_provider = build_subject_provider(subject)
    subject = json.loads(Path(subject_file).read_text())
    horizon = resolve_decision_horizon(group_id=group_id, subject=subject, requested=decision_horizon)

    tap = PassiveActionTapProvider(active_provider)
    registry = CheckpointRegistry(out / "checkpoints")
    controller = ProspectiveCheckpointController()
    monitor = OnlineStructuralMonitor(mode="PACKAGE_FREEZE")
    recorder = MetaGPTBoundaryCheckpointRecorder(
        registry=registry,
        controller=controller,
        group_id=group_id,
        run_id=run_id(group_id=group_id, cell_id=f"X2-{task['id']}"),
        task_id=task["id"],
    )
    bridge = RuntimeStructuralBridge(
        tap=tap,
        monitor=monitor,
        controller=controller,
        cell_id=f"X2-{task['id']}",
    )
    hook = MetaGPTIntegratedCheckpointMonitorHook(recorder=recorder, bridge=bridge)

    failure = None
    result = None
    try:
        result = await run_task_with_checkpoints(
            checkout=checkout,
            task_file=task_file,
            roles_file=roles_file,
            subject_file=subject_file,
            observer_root=out / "metagpt_observer",
            provider=tap,
            checkpoint_hook=hook,
            decision_horizon=horizon,
        )
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        if result is not None:
            _write_json(out / "natural_A_result.json", result)
        if failure is not None:
            _write_json(out / "failure.json", failure)
        _write_json(out / "checkpoint_ledger.json", controller.ledger())
        _write_json(out / "monitor_evidence.json", monitor.evidence())
        _write_json(out / "monitor_candidates.json", monitor.candidates())
        _write_json(out / "repair_packages.json", monitor.packages())
        _write_json(out / "runtime_bridge.json", bridge.snapshot())

    if tap.total_records > horizon:
        raise RuntimeError("X2 natural A exceeded frozen turn ceiling")
    manifest = build_run_manifest(
        cell_id=f"X2-{task['id']}",
        framework_binding={
            "system": "X2_METAGPT",
            "framework": "MetaGPT",
            "version": "1.0.0",
        },
        checkpoint_ledger=controller.ledger(),
        natural_result=result,
        monitor_snapshot=bridge.snapshot(),
        packages=monitor.packages(),
        natural_subject_calls=tap.total_records if subject_mode else 0,
        group_id=group_id,
        semantic_audit_state=semantic_audit_state(group_id=group_id),
    )
    _write_json(out / "run_manifest.json", manifest)
    channel_seal = seal_evidence_channels(
        out_root=out,
        group_id=group_id,
        cell_id=f"X2-{task['id']}",
        audit_paths=["natural_A_result.json", "checkpoint_ledger.json", "checkpoints", "metagpt_observer"],
        monitor_paths=["monitor_evidence.json", "monitor_candidates.json", "repair_packages.json", "runtime_bridge.json"],
    )
    seal = {
        "schema": ("RB-STAGE2-R7-G1-NATURAL-A-SEAL-v1" if group_id == "StageII-R7-G1" else "RB-STAGE2-PROSPECTIVE-NATURAL-A-SEAL-v2"),
        "group_id": group_id,
        "cell_id": f"X2-{task['id']}",
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
        **channel_seal,
        "natural_result_hash": digest(result),
        "repair_actions_during_A": 0,
        "semantic_audit_state": semantic_audit_state(group_id=group_id),
    }
    _write_json(out / "seal.json", seal)
    return seal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--roles-file", required=True)
    parser.add_argument("--subject-file", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--group-id", default="StageII-R7-G1")
    parser.add_argument("--decision-horizon", type=int)
    args = parser.parse_args()
    result = asyncio.run(
        run_x2_natural_A(
            checkout=args.checkout,
            task_file=args.task_file,
            roles_file=args.roles_file,
            subject_file=args.subject_file,
            out_root=args.out_root,
            group_id=args.group_id,
            decision_horizon=args.decision_horizon,
        )
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
