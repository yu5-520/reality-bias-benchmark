from __future__ import annotations

import copy
from collections import defaultdict
from typing import Any

from stage2.r7_checkpoint_v1.common import digest


FOREIGN_PREFIXES = (
    "rag-hit:",
    "memory-recall:",
    "memory-state:",
    "compression-channel:",
    "compression-input:",
    "compression-output:",
)


class StructuralEventError(ValueError):
    pass


def _repair_surface_for(ref: str) -> str | None:
    if ref.startswith("file:"):
        return "NATIVE_APPLICATION_WRITE_OR_REVISION:" + ref
    if ref.startswith("message:"):
        return "NATIVE_MESSAGE_OR_TASK_SUPERSESSION:" + ref
    if ref.startswith("state:"):
        return "AUTHORIZED_PROCESS_STATE_REVISION:" + ref
    return None


def _is_foreign(ref: str) -> bool:
    return ref.startswith(FOREIGN_PREFIXES)


class OnlineStructuralMonitor:
    """Prefix-only structural monitor for prospective R7.

    This monitor has no semantic-audit or CPR input. A package is immutable once
    frozen. Later events are retained only as later monitor evidence and cannot
    expand the already-frozen package.
    """

    REQUIRED_EVENT_FIELDS = {
        "sequence",
        "event_ref",
        "actor",
        "kind",
        "object_refs",
        "written_refs",
        "downstream_legal_refs",
        "preserve_refs",
    }

    def __init__(self, *, mode: str = "PACKAGE_FREEZE"):
        if mode not in {"PACKAGE_FREEZE", "WATCH_ONLY"}:
            raise ValueError("unsupported monitor mode")
        self.mode = mode
        self._last_sequence = 0
        self._event_refs: set[str] = set()
        self._events: list[dict[str, Any]] = []
        self._objects: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "sequences": [],
                "actors": set(),
                "event_refs": [],
                "write_sequences": [],
                "downstream_legal_refs": set(),
            }
        )
        self._frozen_by_object: dict[str, dict[str, Any]] = {}
        self._candidate_log: list[dict[str, Any]] = []

    @property
    def last_sequence(self) -> int:
        return self._last_sequence

    def _validate_event(self, event: dict[str, Any]) -> dict[str, Any]:
        missing = self.REQUIRED_EVENT_FIELDS - set(event)
        if missing:
            raise StructuralEventError("missing event fields: " + ",".join(sorted(missing)))
        sequence = event["sequence"]
        if not isinstance(sequence, int) or sequence <= self._last_sequence:
            raise StructuralEventError("event sequence must be strictly increasing")
        event_ref = event["event_ref"]
        if not isinstance(event_ref, str) or not event_ref or event_ref in self._event_refs:
            raise StructuralEventError("event_ref must be unique and non-empty")
        for key in ("object_refs", "written_refs", "downstream_legal_refs", "preserve_refs"):
            if not isinstance(event[key], list) or any(not isinstance(x, str) for x in event[key]):
                raise StructuralEventError(f"{key} must be a list[str]")
        if not isinstance(event["actor"], str) or not event["actor"]:
            raise StructuralEventError("actor required")
        if not isinstance(event["kind"], str) or not event["kind"]:
            raise StructuralEventError("kind required")
        return copy.deepcopy(event)

    def feed(
        self,
        event: dict[str, Any],
        *,
        checkpoint_manifest: dict[str, Any] | None,
        checkpoint_fresh: bool,
    ) -> list[dict[str, Any]]:
        row = self._validate_event(event)
        self._last_sequence = row["sequence"]
        self._event_refs.add(row["event_ref"])
        self._events.append(row)

        touched = list(dict.fromkeys(row["object_refs"] + row["written_refs"]))
        for ref in touched:
            state = self._objects[ref]
            state["sequences"].append(row["sequence"])
            state["actors"].add(row["actor"])
            state["event_refs"].append(row["event_ref"])
            state["downstream_legal_refs"].update(row["downstream_legal_refs"])
            if ref in row["written_refs"]:
                state["write_sequences"].append(row["sequence"])

        triggers: list[tuple[str, str]] = []
        for ref in touched:
            if ref in self._frozen_by_object:
                continue
            state = self._objects[ref]
            seqs = state["sequences"]
            if len(state["actors"]) >= 2 and len(seqs) >= 2:
                triggers.append((ref, "MULTI_CONSUMER_ADDRESSABLE_REUSE"))
                continue
            if len(seqs) >= 3 and seqs[-1] - seqs[0] >= 2:
                triggers.append((ref, "REENTRY_OR_REUSE"))
                continue
            if state["write_sequences"] and any(
                sequence > state["write_sequences"][0] for sequence in seqs
            ):
                triggers.append((ref, "WRITE_THEN_REUSE"))
                continue
            if _is_foreign(ref) and len(seqs) >= 3:
                triggers.append((ref, "IMMUTABLE_CARRIER_REPEAT"))
                continue
            if row["kind"] == "CONTEXT_TRANSFORMATION" and ref.startswith(
                ("compression-channel:", "compression-output:")
            ):
                triggers.append((ref, "CONTEXT_TRANSFORMATION_EXPOSURE"))

        if row["kind"] == "TERMINAL" and int(row.get("pending_roles", 0)) >= 1:
            for ref, state in sorted(self._objects.items()):
                if ref in self._frozen_by_object:
                    continue
                if len(state["sequences"]) >= 3:
                    triggers.append((ref, "TERMINAL_OPEN_WITH_REUSE"))
                    break

        new_packages = []
        for ref, rule_id in triggers:
            if ref in self._frozen_by_object:
                continue
            candidate = {
                "schema": "RB-STAGE2-R7-G1-STRUCTURAL-CANDIDATE-v1",
                "object_ref": ref,
                "rule_id": rule_id,
                "trigger_event_ref": row["event_ref"],
                "prefix_sequence": row["sequence"],
                "future_evidence_used": False,
                "semantic_audit_used": False,
                "cpr_label": None,
            }
            candidate["candidate_hash"] = digest(
                {k: v for k, v in candidate.items() if k != "candidate_hash"}
            )
            self._candidate_log.append(candidate)
            if self.mode == "WATCH_ONLY":
                continue
            package = self._freeze_package(
                object_ref=ref,
                rule_id=rule_id,
                trigger_event=row,
                checkpoint_manifest=checkpoint_manifest,
                checkpoint_fresh=checkpoint_fresh,
            )
            self._frozen_by_object[ref] = copy.deepcopy(package)
            new_packages.append(copy.deepcopy(package))
        return new_packages

    def _freeze_package(
        self,
        *,
        object_ref: str,
        rule_id: str,
        trigger_event: dict[str, Any],
        checkpoint_manifest: dict[str, Any] | None,
        checkpoint_fresh: bool,
    ) -> dict[str, Any]:
        state = self._objects[object_ref]
        parent_verified = bool(
            checkpoint_manifest
            and checkpoint_manifest.get("restore_capability") == "FULL_NATIVE"
            and checkpoint_manifest.get("checkpoint_hash")
            and checkpoint_fresh
        )
        parent_hash = checkpoint_manifest.get("checkpoint_hash") if checkpoint_manifest else None

        downstream = sorted(state["downstream_legal_refs"])
        surfaces: list[str] = []
        direct = _repair_surface_for(object_ref)
        if direct is not None:
            surfaces.append(direct)
        if _is_foreign(object_ref):
            for ref in downstream:
                surface = _repair_surface_for(ref)
                if surface is not None:
                    surfaces.append(surface)

        preserve_refs = sorted(set(trigger_event["preserve_refs"]))
        requires_forbidden = bool(trigger_event.get("requires_forbidden_boundary", False))

        if not parent_verified:
            repair_gate_status = "PARENT_RECONSTRUCTION_BLOCKED"
            g1_block_code = "CHECKPOINT_BOUNDARY_BLOCKED"
        elif _is_foreign(object_ref) and not downstream:
            repair_gate_status = "LINEAGE_GAP_BLOCKED"
            g1_block_code = "LINEAGE_GAP_BLOCKED"
        elif not preserve_refs:
            repair_gate_status = "LINEAGE_GAP_BLOCKED"
            g1_block_code = "LINEAGE_GAP_BLOCKED"
        elif requires_forbidden:
            repair_gate_status = "SAFETY_BOUNDARY_BLOCKED"
            g1_block_code = "SAFETY_BOUNDARY_BLOCKED"
        elif not surfaces:
            repair_gate_status = "NATIVE_CAPABILITY_BLOCKED"
            g1_block_code = "NATIVE_CAPABILITY_BLOCKED"
        else:
            repair_gate_status = "COMPLETE_FOR_STRUCTURED_REPAIR"
            g1_block_code = None

        support_refs = list(state["event_refs"])
        affected = [object_ref] + downstream
        base = {
            "schema": "RB-STAGE2-R7-G1-MONITOR-DERIVED-REPAIR-PACKAGE-v1",
            "package_id": "pending",
            "source_cell": trigger_event.get("cell_id", "X0-T0"),
            "prefix_cutoff_ref": trigger_event["event_ref"],
            "prefix_sequence": trigger_event["sequence"],
            "monitor_rule_id": rule_id,
            "monitor_evidence_refs": support_refs,
            "pressure_refs": [trigger_event["event_ref"]],
            "support_refs": support_refs,
            "ancestor_refs": support_refs[:-1],
            "descendant_refs": [],
            "affected_closure_refs": affected,
            "preserve_refs": preserve_refs,
            "repair_anchor_ref": trigger_event["event_ref"],
            "content_address": "",
            "detection_surface": object_ref,
            "allowed_repair_surface": sorted(set(surfaces)),
            "native_capability_requirements": sorted(set(surfaces)),
            "forbidden_mutations": [
                "FRAMEWORK_SOURCE_MODIFICATION",
                "PROTOCOL_MODIFICATION",
                "PRIVATE_RUNTIME_STATE_MUTATION",
                "MCP_BACKEND_DIRECT_MUTATION",
                "RAG_INTERNAL_MUTATION",
                "MEMORYBANK_INTERNAL_MUTATION",
                "LONGLMLINGUA_INTERNAL_MUTATION",
                "WHOLE_SYSTEM_RESET",
            ],
            "parent_reconstruction": {
                "status": "VERIFIED" if parent_verified else "BLOCKED",
                "parent_hash_refs": [parent_hash] if parent_hash else [],
                "future_evidence_used": False,
            },
            "repair_gate_status": repair_gate_status,
            "g1_block_code": g1_block_code,
            "post_repair_watch": {
                "old_support_reentry": True,
                "new_support_emergence": True,
                "authority_regeneration": True,
                "scope_reopening": True,
                "carrier_migration": True,
            },
            "semantic_audit_used": False,
            "cpr_label": None,
            "future_evidence_used": False,
        }
        content_hash = digest({k: v for k, v in base.items() if k not in {"package_id", "content_address"}})
        base["package_id"] = f"g1pkg:{content_hash[:24]}"
        base["content_address"] = f"sha256:{content_hash}"
        package_hash = digest(base)
        base["package_hash"] = package_hash
        return base

    def packages(self) -> list[dict[str, Any]]:
        return [copy.deepcopy(row) for _, row in sorted(self._frozen_by_object.items())]

    def candidates(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._candidate_log)

    def evidence(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._events)
