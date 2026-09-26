from __future__ import annotations

import argparse
import asyncio
import json
import os
import socket
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

from stage2.native_v7.x3_a2a.runner import (
    DIRECTORY,
    ROLES,
    SUBJECT,
    _call_initial,
    _free_port,
    _load_inputs,
    _start_process,
    _stop_all,
    _wait_for_cards,
)
from stage2.r7_checkpoint_v1.common import CheckpointRegistry, digest
from stage2.r7_prospective_v1.online_monitor import OnlineStructuralMonitor
from stage2.r7_prospective_v1.run_manifest import build_run_manifest
from stage2.r7_prospective_v1.evidence_channels import seal_evidence_channels
from stage2.r7_prospective_v1.replication_contract import resolve_decision_horizon, run_id, semantic_audit_state

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "stage2"


def _write_json(path: Path, value: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


async def _wait_for_sidecars(state_files: dict[str, Path], processes, *, timeout_steps=120):
    for _ in range(timeout_steps):
        if any(proc.poll() is not None for proc in processes):
            failed = [proc.args for proc in processes if proc.poll() is not None]
            raise RuntimeError(f"A2A service exited before sidecar checkpoint readiness: {failed!r}")
        if all(path.is_file() for path in state_files.values()):
            return
        await asyncio.sleep(0.1)
    missing = [role for role, path in state_files.items() if not path.is_file()]
    raise TimeoutError(f"A2A role checkpoint sidecars did not become ready: {missing}")


def _read_sidecars(state_files: dict[str, Path]) -> dict[str, Any]:
    roles = {}
    for role, path in sorted(state_files.items()):
        row = json.loads(path.read_text())
        if row.get("schema") != "RB-STAGE2-R7-G1-A2A-ROLE-SIDECAR-v1":
            raise RuntimeError("unexpected A2A sidecar schema")
        if row.get("role") != role:
            raise RuntimeError("A2A sidecar role mismatch")
        state = row.get("state")
        if digest(state) != row.get("state_sha256"):
            raise RuntimeError("A2A sidecar state hash mismatch")
        roles[role] = state
    return {
        "schema": "stage2-r7-a2a-global-role-state-v1",
        "roles": roles,
    }


def _wire_structural_monitor(wire_root: Path, *, cell_id: str, start_checkpoint: dict[str, Any]):
    monitor = OnlineStructuralMonitor(mode="PACKAGE_FREEZE")
    rows = []
    sequence = 0
    for path in sorted(wire_root.rglob("*")):
        if not path.is_file():
            continue
        if not (
            path.name.endswith("-post-request.bin")
            or path.name.endswith("-post-response.bin")
        ):
            continue
        sequence += 1
        raw = path.read_bytes()
        ref = "message:" + digest(raw)
        event = {
            "sequence": sequence,
            "event_ref": f"{cell_id}:wire:{sequence:06d}",
            "cell_id": cell_id,
            "actor": path.parent.name or "A2A_WIRE",
            "kind": "A2A_WIRE_REQUEST" if path.name.endswith("-post-request.bin") else "A2A_WIRE_RESPONSE",
            "object_refs": [ref],
            "written_refs": [],
            "downstream_legal_refs": [],
            "preserve_refs": [],
        }
        packages = monitor.feed(
            event,
            checkpoint_manifest=start_checkpoint,
            checkpoint_fresh=False,
        )
        rows.append({
            "event_ref": event["event_ref"],
            "wire_ref": str(path.relative_to(wire_root)),
            "raw_sha256": digest(raw),
            "package_ids": [row["package_id"] for row in packages],
        })
    return monitor, rows


async def run_x3_natural_A(
    *,
    checkout,
    task_file,
    roles_file,
    subject_file,
    out_root,
    mode="subject",
    script_file=None,
    group_id="StageII-R7-G1",
    decision_horizon=None,
):
    task, subject = _load_inputs(task_file, roles_file, subject_file)
    horizon = resolve_decision_horizon(group_id=group_id, subject=subject, requested=decision_horizon)
    if mode == "subject" and not os.environ.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("X3 prospective subject mode requires frozen DeepSeek credential")
    if mode == "scripted" and not script_file:
        raise ValueError("X3 prospective scripted mode requires --script-file")

    out = Path(out_root)
    out.mkdir(parents=True, exist_ok=False)
    logs = out / "process"
    wire = out / "wire"
    sidecar_root = out / "role_sidecars"
    logs.mkdir()
    wire.mkdir()
    sidecar_root.mkdir()

    backend_ports = {role: _free_port() for role in DIRECTORY}
    proxy_ports = {role: _free_port() for role in DIRECTORY}
    public_directory = {
        role: f"http://127.0.0.1:{proxy_ports[role]}" for role in DIRECTORY
    }
    directory_file = out / "service-directory.json"
    _write_json(directory_file, public_directory)
    state_files = {
        role: sidecar_root / f"{role}.json" for role in DIRECTORY
    }

    env_base = os.environ.copy()
    env_base["PYTHONPATH"] = str(ROOT)
    processes = []
    streams = []
    start_checkpoint = None
    terminal_checkpoint = None
    result = None
    registry = CheckpointRegistry(out / "checkpoints")
    try:
        for role in DIRECTORY:
            service_cmd = [
                sys.executable,
                "-m",
                "stage2.r7_prospective_v1.x3_service",
                "--role",
                role,
                "--checkout",
                str(Path(checkout).resolve()),
                "--directory-file",
                str(directory_file),
                "--public-url",
                public_directory[role],
                "--port",
                str(backend_ports[role]),
                "--mode",
                mode,
                "--checkpoint-state-file",
                str(state_files[role]),
                "--max-turns",
                str(horizon),
            ]
            if script_file:
                service_cmd += ["--script-file", str(Path(script_file).resolve())]
            proc, stream = _start_process(
                service_cmd,
                env_base,
                logs / f"{role}-service.stderr.bin",
            )
            processes.append(proc)
            streams.append(stream)

        for role in DIRECTORY:
            proxy_cmd = [
                sys.executable,
                "-m",
                "stage2.native_v7.x3_a2a.proxy",
                "--backend",
                f"http://127.0.0.1:{backend_ports[role]}",
                "--observer-root",
                str(wire / role),
                "--role",
                role,
                "--port",
                str(proxy_ports[role]),
            ]
            proc, stream = _start_process(
                proxy_cmd,
                env_base,
                logs / f"{role}-proxy.stderr.bin",
            )
            processes.append(proc)
            streams.append(stream)

        await _wait_for_cards(public_directory, processes)
        await _wait_for_sidecars(state_files, processes)
        start_state = _read_sidecars(state_files)
        start_checkpoint = registry.capture(
            system_id="X3_A2A",
            group_id=group_id,
            run_id=run_id(group_id=group_id, cell_id=f"X3-{task['id']}"),
            task_id=task["id"],
            event_ref="x3:task-start",
            adapter_id="stage2-r7-a2a-role-service-sidecar-v1",
            framework_binding={
                "framework": "A2A",
                "protocol_version": "1.0",
                "protocol_commit": "173695755607e884aa9acf8ce4feed90e32727a1",
                "sdk_commit": "0d5473ca4fa6d40034a6a7c8d65bce5cd85d8167",
                "checkpoint_surface": "out-of-band Stage-II role-service application sidecar",
            },
            native_state=start_state,
            application_root=checkout,
            model_visible_context={"task_id": task["id"], "boundary": "before-top-level-request"},
            remaining_horizon=horizon,
            external_carrier_refs=[],
            restore_capability="FULL_NATIVE",
            replication_binding={
                "repair_contract_version": "RB-STAGE2-R7-G1-PROSPECTIVE-REPAIR-CONTRACT-v1"
            },
        )

        session_id = f"x3-{task['id']}-{uuid.uuid4()}"
        result = await _call_initial(
            public_directory[ROLES["entry_agent"]],
            {
                "schema": "stage2-x3-role-call-v1",
                "session_id": session_id,
                "task_id": task["id"],
                "sender": "USER",
                "target": ROLES["entry_agent"],
                "kind": "user_request",
                "content": task["user_request"],
                "remaining_turns": horizon,
                "depth": 0,
            },
        )
        result["a2a_calls"] = 1 + int(result.get("protocol_calls", 0))
        result["service_count"] = len(DIRECTORY)
        result["session_id"] = session_id

        await asyncio.sleep(0.05)
        terminal_state = _read_sidecars(state_files)
        terminal_checkpoint = registry.capture(
            system_id="X3_A2A",
            group_id=group_id,
            run_id=run_id(group_id=group_id, cell_id=f"X3-{task['id']}"),
            task_id=task["id"],
            event_ref="x3:terminal",
            adapter_id="stage2-r7-a2a-role-service-sidecar-v1",
            framework_binding={
                "framework": "A2A",
                "protocol_version": "1.0",
                "protocol_commit": "173695755607e884aa9acf8ce4feed90e32727a1",
                "sdk_commit": "0d5473ca4fa6d40034a6a7c8d65bce5cd85d8167",
                "checkpoint_surface": "out-of-band Stage-II role-service application sidecar",
            },
            native_state=terminal_state,
            application_root=checkout,
            model_visible_context={"task_id": task["id"], "boundary": "after-top-level-request"},
            remaining_horizon=max(
                0,
                horizon - int(result.get("turns_used", 0)),
            ),
            external_carrier_refs=[],
            restore_capability="FULL_NATIVE",
            replication_binding={
                "repair_contract_version": "RB-STAGE2-R7-G1-PROSPECTIVE-REPAIR-CONTRACT-v1"
            },
        )
    finally:
        _stop_all(processes, streams)

    if result is None or start_checkpoint is None or terminal_checkpoint is None:
        raise RuntimeError("X3 prospective natural A did not complete its quiescent checkpoint geometry")

    monitor, wire_index = _wire_structural_monitor(
        wire,
        cell_id=f"X3-{task['id']}",
        start_checkpoint=start_checkpoint,
    )
    turns = int(result.get("turns_used", 0))
    if turns < 1 or turns > horizon:
        raise RuntimeError("X3 prospective turn accounting outside frozen ceiling")

    checkpoint_ledger = {
        "schema": "RB-STAGE2-R7-PROSPECTIVE-CHECKPOINT-LEDGER-v1",
        "model_decision_sequence": turns,
        "first_eligible_event_ref": None,
        "first_eligible_checkpoint_hash": None,
        "checkpoints": [
            {
                "boundary": "TASK_START",
                "event_ref": "x3:task-start",
                "checkpoint_hash": start_checkpoint["checkpoint_hash"],
                "checkpoint_id": start_checkpoint["checkpoint_id"],
                "model_decision_sequence": 0,
                "restore_capability": "FULL_NATIVE",
            },
            {
                "boundary": "TERMINAL",
                "event_ref": "x3:terminal",
                "checkpoint_hash": terminal_checkpoint["checkpoint_hash"],
                "checkpoint_id": terminal_checkpoint["checkpoint_id"],
                "model_decision_sequence": turns,
                "restore_capability": "FULL_NATIVE",
            },
        ],
    }
    monitor_snapshot = {
        "schema": "RB-STAGE2-R7-G1-X3-WIRE-MONITOR-v1",
        "event_count": len(monitor.evidence()),
        "candidate_count": len(monitor.candidates()),
        "package_count": len(monitor.packages()),
        "wire_index_hash": digest(wire_index),
        "repair_boundary": "NESTED_ACTIVE_CALL_CHECKPOINT_UNPROVEN",
        "a2a_protocol_modified": False,
    }
    manifest = build_run_manifest(
        cell_id=f"X3-{task['id']}",
        framework_binding={
            "system": "X3_A2A",
            "framework": "A2A",
            "protocol_version": "1.0",
            "protocol_commit": "173695755607e884aa9acf8ce4feed90e32727a1",
            "sdk_commit": "0d5473ca4fa6d40034a6a7c8d65bce5cd85d8167",
        },
        checkpoint_ledger=checkpoint_ledger,
        natural_result=result,
        monitor_snapshot=monitor_snapshot,
        packages=monitor.packages(),
        natural_subject_calls=turns if mode == "subject" else 0,
        group_id=group_id,
        semantic_audit_state=semantic_audit_state(group_id=group_id),
    )

    _write_json(out / "natural_A_result.json", result)
    _write_json(out / "checkpoint_ledger.json", checkpoint_ledger)
    _write_json(out / "monitor_evidence.json", monitor.evidence())
    _write_json(out / "monitor_candidates.json", monitor.candidates())
    _write_json(out / "repair_packages.json", monitor.packages())
    _write_json(out / "wire_index.json", wire_index)
    _write_json(out / "run_manifest.json", manifest)
    channel_seal = seal_evidence_channels(
        out_root=out,
        group_id=group_id,
        cell_id=f"X3-{task['id']}",
        audit_paths=["natural_A_result.json", "checkpoint_ledger.json", "checkpoints", "wire", "process"],
        monitor_paths=["monitor_evidence.json", "monitor_candidates.json", "repair_packages.json", "wire_index.json"],
    )
    seal = {
        "schema": ("RB-STAGE2-R7-G1-NATURAL-A-SEAL-v1" if group_id == "StageII-R7-G1" else "RB-STAGE2-PROSPECTIVE-NATURAL-A-SEAL-v2"),
        "group_id": group_id,
        "cell_id": f"X3-{task['id']}",
        "status": "NATURAL_A_FROZEN_REPAIR_NESTED_CHECKPOINT_BLOCKED",
        "provider_mode": "SUBJECT" if mode == "subject" else "NON_STUDY_SCRIPTED",
        "natural_subject_calls": turns if mode == "subject" else 0,
        "model_decision_count": turns,
        "checkpoint_count": 2,
        "nested_checkpoint_status": "UNPROVEN_FAIL_CLOSED",
        "structural_event_count": len(monitor.evidence()),
        "candidate_count": len(monitor.candidates()),
        "package_count": len(monitor.packages()),
        "complete_package_count": 0,
        "a2a_protocol_modified": False,
        "run_manifest_hash": manifest["manifest_hash"],
        **channel_seal,
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
    parser.add_argument("--mode", choices=["subject", "scripted"], default="subject")
    parser.add_argument("--script-file")
    parser.add_argument("--group-id", default="StageII-R7-G1")
    parser.add_argument("--decision-horizon", type=int)
    args = parser.parse_args()
    result = asyncio.run(
        run_x3_natural_A(
            checkout=args.checkout,
            task_file=args.task_file,
            roles_file=args.roles_file,
            subject_file=args.subject_file,
            out_root=args.out_root,
            mode=args.mode,
            script_file=args.script_file,
            group_id=args.group_id,
            decision_horizon=args.decision_horizon,
        )
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
