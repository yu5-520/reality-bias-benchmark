from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
from typing import Any, Callable

from stage2.r7_checkpoint_v1.common import digest, file_tree_manifest
from stage2.r7_checkpoint_v1.controller import (
    CheckpointBoundary,
    ProspectiveCheckpointController,
)
from stage2.r7_prospective_v1.online_monitor import OnlineStructuralMonitor


class PassiveActionTapProvider:
    """Copy model action envelopes without changing the returned provider object."""

    def __init__(self, provider):
        self.provider = provider
        self.records: list[dict[str, Any]] = []

    def _record(self, result, metadata):
        row = {
            "metadata": copy.deepcopy(metadata or {}),
            "valid_json": False,
            "actions": [],
        }
        try:
            envelope = json.loads(result["content"])
            actions = envelope.get("actions")
            if isinstance(actions, list):
                row["valid_json"] = True
                row["actions"] = copy.deepcopy(actions)
        except (KeyError, TypeError, json.JSONDecodeError):
            pass
        self.records.append(row)
        return result

    def complete_agent(self, messages, metadata=None):
        value = self.provider.complete_agent(messages, metadata)
        if inspect.isawaitable(value):
            async def awaited():
                result = await value
                return self._record(result, metadata)
            return awaited()
        return self._record(value, metadata)

    def drain(self) -> list[dict[str, Any]]:
        rows = self.records
        self.records = []
        return rows


def _file_preserve_refs(checkout_root: str | Path, mutable_refs: set[str]) -> list[str]:
    manifest = file_tree_manifest(checkout_root)
    return [
        "file:" + path
        for path in sorted(manifest)
        if "file:" + path not in mutable_refs
    ]


def _message_ref(actor: str, target: str, content: Any) -> str:
    return "message:" + digest(
        {"actor": actor, "target": target, "content": content}
    )


def _action_refs(actor: str, action: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    kind = str(action.get("type") or "unknown")
    if kind in {"read_file", "write_file"}:
        path = action.get("path")
        ref = "file:" + str(path)
        return ref, [ref] if kind == "write_file" else [], []
    if kind in {"message", "delegate"}:
        ref = _message_ref(actor, str(action.get("to")), action.get("content"))
        return ref, [], []
    if kind == "list_files":
        return "state:file-list", [], []
    if kind == "run_tests":
        return "state:test-run", [], []
    if kind == "finalize":
        return "state:finalize:" + actor, [], []
    return "state:action:" + kind, [], []


def foreign_carrier_refs_from_host(host) -> list[dict[str, Any]]:
    """Read experiment-visible capability outputs without mutating the capability."""

    rows: list[dict[str, Any]] = []

    rag = getattr(host, "rag_context", None)
    if rag is not None:
        for hit in getattr(rag, "last_hits", []) or []:
            sha = hit.get("sha256")
            if sha:
                rows.append({
                    "family": "rag-hit",
                    "object_ref": "rag-hit:" + str(sha),
                    "source_ref": str(hit.get("path")),
                    "sha256": str(sha),
                    "mutation": "FORBIDDEN",
                })

    memory = getattr(host, "memory_context", None)
    if memory is not None:
        root = getattr(memory, "memory_root", None)
        if root is not None and Path(root).exists():
            for path in sorted(Path(root).glob("*.json")):
                rows.append({
                    "family": "memory-state",
                    "object_ref": "memory-state:" + digest(path.read_bytes()),
                    "source_ref": str(path.name),
                    "sha256": digest(path.read_bytes()),
                    "mutation": "FORBIDDEN",
                })

    compressor = getattr(host, "compressor_context", None)
    if compressor is not None and getattr(compressor, "last_result", None) is not None:
        result = copy.deepcopy(compressor.last_result)
        rows.append({
            "family": "compression-output",
            "object_ref": "compression-output:" + digest(result),
            "source_ref": "PromptCompressor.last_result",
            "sha256": digest(result),
            "mutation": "FORBIDDEN",
        })

    return rows


class RuntimeStructuralBridge:
    """Bind passive action copies and carrier copies to an exact checkpoint."""

    def __init__(
        self,
        *,
        tap: PassiveActionTapProvider,
        monitor: OnlineStructuralMonitor,
        controller: ProspectiveCheckpointController,
        cell_id: str,
    ):
        self.tap = tap
        self.monitor = monitor
        self.controller = controller
        self.cell_id = cell_id
        self.sequence = 0
        self.frozen_packages: list[dict[str, Any]] = []
        self.first_complete_package_id: str | None = None

    def _next_event(
        self,
        *,
        actor: str,
        kind: str,
        object_refs: list[str],
        written_refs: list[str],
        downstream_legal_refs: list[str],
        preserve_refs: list[str],
    ) -> dict[str, Any]:
        self.sequence += 1
        return {
            "sequence": self.sequence,
            "event_ref": f"{self.cell_id}:struct:{self.sequence:06d}",
            "cell_id": self.cell_id,
            "actor": actor,
            "kind": kind,
            "object_refs": object_refs,
            "written_refs": written_refs,
            "downstream_legal_refs": downstream_legal_refs,
            "preserve_refs": preserve_refs,
        }

    def flush_turn(
        self,
        *,
        checkpoint_manifest: dict[str, Any],
        checkout_root: str | Path,
        carrier_refs: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        if checkpoint_manifest.get("restore_capability") != "FULL_NATIVE":
            checkpoint_fresh = False
        else:
            checkpoint_fresh = True

        new_packages: list[dict[str, Any]] = []
        rows = self.tap.drain()
        for row in rows:
            actor = str(row["metadata"].get("role") or "UNKNOWN")
            if not row["valid_json"]:
                event = self._next_event(
                    actor=actor,
                    kind="INVALID_ENVELOPE",
                    object_refs=["state:invalid-envelope:" + actor],
                    written_refs=[],
                    downstream_legal_refs=[],
                    preserve_refs=_file_preserve_refs(checkout_root, set()),
                )
                new_packages.extend(
                    self.monitor.feed(
                        event,
                        checkpoint_manifest=checkpoint_manifest,
                        checkpoint_fresh=checkpoint_fresh,
                    )
                )
                continue

            for action in row["actions"]:
                ref, written, downstream = _action_refs(actor, action)
                mutable = {ref} if ref.startswith("file:") else set()
                event = self._next_event(
                    actor=actor,
                    kind="ACTION_" + str(action.get("type", "unknown")).upper(),
                    object_refs=[ref],
                    written_refs=written,
                    downstream_legal_refs=downstream,
                    preserve_refs=_file_preserve_refs(checkout_root, mutable),
                )
                new_packages.extend(
                    self.monitor.feed(
                        event,
                        checkpoint_manifest=checkpoint_manifest,
                        checkpoint_fresh=checkpoint_fresh,
                    )
                )

            # External carriers were visible to this completed model turn, but a
            # legal downstream dependency is NOT inferred from temporal proximity.
            for carrier in carrier_refs or []:
                ref = carrier.get("object_ref")
                if not isinstance(ref, str) or not ref:
                    continue
                event = self._next_event(
                    actor=actor,
                    kind="IMMUTABLE_CARRIER_EXPOSURE",
                    object_refs=[ref],
                    written_refs=[],
                    downstream_legal_refs=[],
                    preserve_refs=_file_preserve_refs(checkout_root, set()),
                )
                new_packages.extend(
                    self.monitor.feed(
                        event,
                        checkpoint_manifest=checkpoint_manifest,
                        checkpoint_fresh=checkpoint_fresh,
                    )
                )

        for package in new_packages:
            self.frozen_packages.append(copy.deepcopy(package))
            if (
                package.get("repair_gate_status") == "COMPLETE_FOR_STRUCTURED_REPAIR"
                and self.first_complete_package_id is None
            ):
                self.controller.register_manifest(
                    boundary=CheckpointBoundary.FIRST_MONITOR_REPAIR_ELIGIBLE,
                    event_ref=package["prefix_cutoff_ref"],
                    manifest=checkpoint_manifest,
                )
                self.first_complete_package_id = package["package_id"]
        return copy.deepcopy(new_packages)

    def feed_terminal(
        self,
        *,
        checkpoint_manifest: dict[str, Any],
        pending_roles: int,
        checkout_root: str | Path,
    ) -> list[dict[str, Any]]:
        self.sequence += 1
        event = {
            "sequence": self.sequence,
            "event_ref": f"{self.cell_id}:struct:{self.sequence:06d}",
            "cell_id": self.cell_id,
            "actor": "SYSTEM",
            "kind": "TERMINAL",
            "object_refs": [],
            "written_refs": [],
            "downstream_legal_refs": [],
            "preserve_refs": _file_preserve_refs(checkout_root, set()),
            "pending_roles": int(pending_roles),
        }
        packages = self.monitor.feed(
            event,
            checkpoint_manifest=checkpoint_manifest,
            checkpoint_fresh=checkpoint_manifest.get("restore_capability") == "FULL_NATIVE",
        )
        self.frozen_packages.extend(copy.deepcopy(packages))
        return packages

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": "RB-STAGE2-R7-G1-RUNTIME-STRUCTURAL-BRIDGE-v1",
            "cell_id": self.cell_id,
            "event_count": len(self.monitor.evidence()),
            "candidate_count": len(self.monitor.candidates()),
            "package_count": len(self.monitor.packages()),
            "first_complete_package_id": self.first_complete_package_id,
            "evidence_hash": digest(self.monitor.evidence()),
            "candidate_hash": digest(self.monitor.candidates()),
            "package_set_hash": digest(self.monitor.packages()),
        }
