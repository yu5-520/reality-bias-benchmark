"""External observation normalization for the enhanced Stage-II monitor.

This module only normalizes already-observed evidence. It does not change a
studied framework, infer semantic adoption from proximity, or grant mutation
authority.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from stage2.r7_checkpoint_v1.common import digest


class ObservationError(ValueError):
    pass


_REQUIRED_STRUCTURAL_FIELDS = {
    "sequence",
    "event_ref",
    "actor",
    "kind",
    "object_refs",
    "written_refs",
    "downstream_legal_refs",
    "preserve_refs",
}


def _list_of_strings(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ObservationError(f"{field} must be list[str]")
    return list(value)


def adapt_structural_event(
    event: Mapping[str, Any],
    *,
    trajectory_id: str,
    evidence_ref: str,
    version: str | None = None,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Normalize one existing structural-monitor event without adding edges."""
    row = copy.deepcopy(dict(event))
    missing = _REQUIRED_STRUCTURAL_FIELDS - set(row)
    if missing:
        raise ObservationError("missing structural fields: " + ",".join(sorted(missing)))
    if not trajectory_id or not evidence_ref:
        raise ObservationError("trajectory_id and evidence_ref are required")
    sequence = row["sequence"]
    if type(sequence) is not int or sequence < 0:
        raise ObservationError("sequence must be a non-negative integer")
    event_ref = row["event_ref"]
    actor = row["actor"]
    kind = row["kind"]
    if not isinstance(event_ref, str) or not event_ref:
        raise ObservationError("event_ref required")
    if not isinstance(actor, str) or not actor:
        raise ObservationError("actor required")
    if not isinstance(kind, str) or not kind:
        raise ObservationError("kind required")

    material = {
        "schema": "RB-STAGE2-ENHANCED-OBSERVATION-v1",
        "trajectory_id": trajectory_id,
        "event_ref": event_ref,
        "native_sequence": sequence,
        "actor": actor,
        "event_kind": kind,
        "object_refs": _list_of_strings(row["object_refs"], "object_refs"),
        "written_refs": _list_of_strings(row["written_refs"], "written_refs"),
        "downstream_legal_refs": _list_of_strings(
            row["downstream_legal_refs"], "downstream_legal_refs"
        ),
        "preserve_refs": _list_of_strings(row["preserve_refs"], "preserve_refs"),
        "evidence_ref": evidence_ref,
        "source_kind": "FROZEN_RUNTIME_EVENT",
        "version": version,
        "observed_at": observed_at,
        "content_hash": row.get("content_hash") or row.get("sha256"),
        "field_path": row.get("field_path"),
        "text_span": row.get("text_span"),
        "visibility_scope": row.get("visibility_scope"),
    }
    material["observation_id"] = "obs:" + digest(material)[:24]
    return material


def adapt_relation_evidence(record: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize an existing relation-evidence record.

    Evidence level and semantic-use status are preserved. No semantic status is
    upgraded by this adapter.
    """
    row = copy.deepcopy(dict(record))
    for field in ("relation_id", "source_ref", "destination_ref", "relation_type"):
        if not isinstance(row.get(field), str) or not row[field]:
            raise ObservationError(f"{field} required")
    evidence_refs = row.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs:
        raise ObservationError("evidence_refs required")
    if any(not isinstance(item, str) or not item for item in evidence_refs):
        raise ObservationError("evidence_refs must be non-empty strings")

    semantic_use = row.get("semantic_use_status", "UNRESOLVED")
    if semantic_use in {"ADOPTED_AS_PREMISE", "REJECTED_OR_ABANDONED"}:
        status = "SUPPORTED" if semantic_use == "ADOPTED_AS_PREMISE" else "REJECTED"
        basis = "SEMANTIC_REVIEW"
    elif row.get("evidence_level", "UNRESOLVED") == "UNRESOLVED":
        status = "UNKNOWN"
        basis = "UNRESOLVED_RELATION_EVIDENCE"
    else:
        status = "SUPPORTED"
        basis = "SOURCE_BACKED_STRUCTURAL_RELATION"

    return {
        "schema": "RB-STAGE2-ENHANCED-RELATION-v1",
        "relation_id": row["relation_id"],
        "source_ref": row["source_ref"],
        "destination_ref": row["destination_ref"],
        "relation_type": row["relation_type"],
        "status": status,
        "basis": basis,
        "evidence_refs": sorted(set(evidence_refs)),
        "semantic_scope_status": row.get("semantic_scope_status", "UNRESOLVED"),
        "semantic_use_status": semantic_use,
        "content_address": row.get("content_address"),
        "target_semantic_id": row.get("target_semantic_id"),
        "actor": row.get("actor"),
        "turn": row.get("turn"),
        "judgment_version": row.get("judgment_version"),
    }
