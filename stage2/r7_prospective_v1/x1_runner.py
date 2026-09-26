from __future__ import annotations

import argparse
import asyncio
import copy
import json
from pathlib import Path
from typing import Any

from stage2.native_v7.observer import PassiveEventObserver, native_bytes
from stage2.native_v7.x1_autogen.runner import (
    FINAL_MARKER,
    _load_inputs,
    build_deepseek_client,
    build_team,
)
from stage2.r7_checkpoint_v1.autogen_adapter import AutoGenNativeCheckpointAdapter
from stage2.r7_checkpoint_v1.common import CheckpointRegistry, digest
from stage2.r7_prospective_v1.online_monitor import OnlineStructuralMonitor
from stage2.r7_prospective_v1.run_manifest import build_run_manifest
from stage2.r7_prospective_v1.evidence_channels import seal_evidence_channels
from stage2.r7_prospective_v1.replication_contract import resolve_decision_horizon, run_id, semantic_audit_state

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "stage2"


class CountingModelClient:
    """Transparent call counter around the already-selected AutoGen model client."""

    def __init__(self, client):
        self._client = client
        self.create_calls = 0
        self.create_stream_calls = 0

    @property
    def model_info(self):
        return self._client.model_info

    @property
    def capabilities(self):
        return getattr(self._client, "capabilities", None)

    async def create(self, *args, **kwargs):
        self.create_calls += 1
        return await self._client.create(*args, **kwargs)

    def create_stream(self, *args, **kwargs):
        self.create_stream_calls += 1
        return self._client.create_stream(*args, **kwargs)

    async def close(self):
        return await self._client.close()

    def count_tokens(self, *args, **kwargs):
        return self._client.count_tokens(*args, **kwargs)

    def remaining_tokens(self, *args, **kwargs):
        return self._client.remaining_tokens(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._client, name)


def _write_json(path: Path, value: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _recursive_action_refs(value: Any) -> tuple[list[str], list[str]]:
    refs: list[str] = []
    written: list[str] = []
    if isinstance(value, dict):
        name = value.get("name")
        arguments = value.get("arguments")
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = None
        if name in {"read_file", "write_file"} and isinstance(arguments, dict):
            path = arguments.get("path")
            if isinstance(path, str) and path:
                ref = "file:" + path
                refs.append(ref)
                if name == "write_file":
                    written.append(ref)
        for child in value.values():
            r, w = _recursive_action_refs(child)
            refs.extend(r)
            written.extend(w)
    elif isinstance(value, list):
        for child in value:
            r, w = _recursive_action_refs(child)
            refs.extend(r)
            written.extend(w)
    return list(dict.fromkeys(refs)), list(dict.fromkeys(written))


def _event_actor(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("source", "sender", "name"):
            v = value.get(key)
            if isinstance(v, str) and v:
                return v
    return "AUTOGEN"


async def run_x1_natural_A(
    *,
    checkout,
    task_file,
    roles_file,
    subject_file,
    out_root,
    model_client=None,
    group_id="StageII-R7-G1",
    decision_horizon=None,
):
    task, roles, subject = _load_inputs(task_file, roles_file, subject_file)
    horizon = resolve_decision_horizon(group_id=group_id, subject=subject, requested=decision_horizon)
    out = Path(out_root)
    out.mkdir(parents=True, exist_ok=False)
    own_client = model_client is None
    base_client = build_deepseek_client(subject) if own_client else model_client
    client = CountingModelClient(base_client)
    team = build_team(
        model_client=client,
        roles=roles,
        checkout=checkout,
        max_turns=horizon,
    )
    registry = CheckpointRegistry(out / "checkpoints")
    adapter = AutoGenNativeCheckpointAdapter()
    monitor = OnlineStructuralMonitor(mode="PACKAGE_FREEZE")
    observer = PassiveEventObserver(out / "autogen_observer", probe="X1")

    start = await adapter.capture(
        team=team,
        registry=registry,
        application_root=checkout,
        group_id=group_id,
        run_id=run_id(group_id=group_id, cell_id=f"X1-{task['id']}"),
        task_id=task["id"],
        event_ref="x1:task-start",
        model_visible_context={"task_id": task["id"], "boundary": "before-team-run"},
        remaining_horizon=horizon,
        replication_binding={
            "repair_contract_version": "RB-STAGE2-R7-G1-PROSPECTIVE-REPAIR-CONTRACT-v1"
        },
    )

    native_rows = []
    final = None
    sequence = 0
    try:
        async for item in team.run_stream(task=task["user_request"]):
            raw = native_bytes(item)
            preserved = observer.observe(raw, surface="autogen_agentchat.run_stream")
            if preserved != raw:
                raise RuntimeError("observer altered AutoGen event bytes")
            sequence += 1
            try:
                parsed = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                parsed = {"raw_sha256": digest(raw)}
            refs, written = _recursive_action_refs(parsed)
            structural = {
                "sequence": sequence,
                "event_ref": f"X1-{task['id']}:native:{sequence:06d}",
                "cell_id": f"X1-{task['id']}",
                "actor": _event_actor(parsed),
                "kind": str(parsed.get("type") or parsed.get("message_type") or "AUTOGEN_NATIVE_EVENT")
                    if isinstance(parsed, dict) else "AUTOGEN_NATIVE_EVENT",
                "object_refs": refs,
                "written_refs": written,
                "downstream_legal_refs": [],
                "preserve_refs": [],
            }
            # The only checkpoint currently legal before terminal is task-start;
            # after the first native event it is intentionally stale for active repair.
            packages = monitor.feed(
                structural,
                checkpoint_manifest=start,
                checkpoint_fresh=False,
            )
            native_rows.append({
                "event_ref": structural["event_ref"],
                "raw_sha256": digest(raw),
                "object_refs": refs,
                "package_ids": [row["package_id"] for row in packages],
            })
            if hasattr(item, "stop_reason"):
                final = item
    finally:
        observer.seal()

    if final is None:
        if own_client:
            await base_client.close()
        raise RuntimeError("AutoGen Swarm did not emit terminal TaskResult")

    terminal = await adapter.capture(
        team=team,
        registry=registry,
        application_root=checkout,
        group_id=group_id,
        run_id=run_id(group_id=group_id, cell_id=f"X1-{task['id']}"),
        task_id=task["id"],
        event_ref="x1:terminal",
        model_visible_context={"task_id": task["id"], "boundary": "after-team-run"},
        remaining_horizon=max(0, horizon - client.create_calls),
        replication_binding={
            "repair_contract_version": "RB-STAGE2-R7-G1-PROSPECTIVE-REPAIR-CONTRACT-v1"
        },
    )
    if own_client:
        await base_client.close()

    result = {
        "stop_reason": getattr(final, "stop_reason", None),
        "messages": len(getattr(final, "messages", []) or []),
        "native_events": sequence,
        "answer": (
            getattr(getattr(final, "messages", [None])[-1], "content", None)
            if getattr(final, "messages", None)
            else None
        ),
    }
    if client.create_stream_calls:
        raise RuntimeError("unexpected AutoGen streaming model-client call path")
    if client.create_calls > horizon:
        raise RuntimeError("X1 exceeded frozen model invocation ceiling")

    checkpoint_ledger = {
        "schema": "RB-STAGE2-R7-PROSPECTIVE-CHECKPOINT-LEDGER-v1",
        "model_decision_sequence": client.create_calls,
        "first_eligible_event_ref": None,
        "first_eligible_checkpoint_hash": None,
        "checkpoints": [
            {
                "boundary": "TASK_START",
                "event_ref": "x1:task-start",
                "checkpoint_hash": start["checkpoint_hash"],
                "checkpoint_id": start["checkpoint_id"],
                "model_decision_sequence": 0,
                "restore_capability": "FULL_NATIVE",
            },
            {
                "boundary": "TERMINAL",
                "event_ref": "x1:terminal",
                "checkpoint_hash": terminal["checkpoint_hash"],
                "checkpoint_id": terminal["checkpoint_id"],
                "model_decision_sequence": client.create_calls,
                "restore_capability": "FULL_NATIVE",
            },
        ],
    }
    monitor_snapshot = {
        "schema": "RB-STAGE2-R7-G1-X1-RAW-STREAM-MONITOR-v1",
        "event_count": len(monitor.evidence()),
        "candidate_count": len(monitor.candidates()),
        "package_count": len(monitor.packages()),
        "package_gate_counts": {
            "PARENT_RECONSTRUCTION_BLOCKED": sum(
                1 for row in monitor.packages()
                if row["repair_gate_status"] == "PARENT_RECONSTRUCTION_BLOCKED"
            )
        },
        "raw_event_index_hash": digest(native_rows),
        "repair_boundary": "MID_RUN_CHECKPOINT_UNPROVEN",
    }
    manifest = build_run_manifest(
        cell_id=f"X1-{task['id']}",
        framework_binding={
            "system": "X1_AUTOGEN",
            "framework": "AutoGen AgentChat Swarm",
            "upstream_commit": "027ecf0a379bcc1d09956d46d12d44a3ad9cee14",
        },
        checkpoint_ledger=checkpoint_ledger,
        natural_result=result,
        monitor_snapshot=monitor_snapshot,
        packages=monitor.packages(),
        natural_subject_calls=client.create_calls if own_client else 0,
        group_id=group_id,
        semantic_audit_state=semantic_audit_state(group_id=group_id),
    )

    _write_json(out / "natural_A_result.json", result)
    _write_json(out / "checkpoint_ledger.json", checkpoint_ledger)
    _write_json(out / "monitor_evidence.json", monitor.evidence())
    _write_json(out / "monitor_candidates.json", monitor.candidates())
    _write_json(out / "repair_packages.json", monitor.packages())
    _write_json(out / "native_event_index.json", native_rows)
    _write_json(out / "run_manifest.json", manifest)
    channel_seal = seal_evidence_channels(
        out_root=out,
        group_id=group_id,
        cell_id=f"X1-{task['id']}",
        audit_paths=["natural_A_result.json", "checkpoint_ledger.json", "checkpoints", "autogen_observer"],
        monitor_paths=["monitor_evidence.json", "monitor_candidates.json", "repair_packages.json", "native_event_index.json"],
    )
    seal = {
        "schema": ("RB-STAGE2-R7-G1-NATURAL-A-SEAL-v1" if group_id == "StageII-R7-G1" else "RB-STAGE2-PROSPECTIVE-NATURAL-A-SEAL-v2"),
        "group_id": group_id,
        "cell_id": f"X1-{task['id']}",
        "status": "NATURAL_A_FROZEN_REPAIR_MIDRUN_CHECKPOINT_BLOCKED",
        "provider_mode": "SUBJECT" if own_client else "NON_STUDY_INJECTED",
        "natural_subject_calls": client.create_calls if own_client else 0,
        "model_decision_count": client.create_calls,
        "checkpoint_count": 2,
        "midrun_checkpoint_status": "UNPROVEN_FAIL_CLOSED",
        "structural_event_count": len(monitor.evidence()),
        "candidate_count": len(monitor.candidates()),
        "package_count": len(monitor.packages()),
        "complete_package_count": 0,
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
    parser.add_argument("--group-id", default="StageII-R7-G1")
    parser.add_argument("--decision-horizon", type=int)
    args = parser.parse_args()
    result = asyncio.run(
        run_x1_natural_A(
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
