from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


BEHAVIOR_SCHEMA = "RB-BEHAVIOR-EVENT-v0.1"
TRAJECTORY_SCHEMA = "RB-SYSTEM-TRAJECTORY-MEASUREMENT-v4.0"
VARIABLE_REGISTRY_SCHEMA = "RB-EXPERIMENTAL-VARIABLE-REGISTRY-v0.1"
BOUNDARY_REGISTRY_SCHEMA = "RB-MEASUREMENT-BOUNDARY-REGISTRY-v0.1"

REALIZATION_STATUSES = {"PROPOSAL", "REALIZED", "BLOCKED", "FAILED"}
ACTION_TYPES = {
    "read",
    "write",
    "message",
    "invoke",
    "commit",
    "reopen",
    "revise",
    "inherit",
    "finalize",
    "other",
}
ANCHOR_CLASSES = {
    "ANTECEDENT_ANCHOR",
    "TRANSITION_ANCHOR",
    "PENETRATION_ANCHOR",
    "CHALLENGE_RECOVERY_ANCHOR",
}
VARIABLE_STAGES = {"PRE", "MID", "POST", "STRUCTURE"}


class SystemBehaviorValidationError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_variable_registry(registry: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    if registry.get("schema") != VARIABLE_REGISTRY_SCHEMA:
        raise SystemBehaviorValidationError("unexpected experimental-variable registry schema")
    rows = registry.get("variables")
    if not isinstance(rows, list) or not rows:
        raise SystemBehaviorValidationError("experimental-variable registry must contain variables")

    seen: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        variable_id = row.get("variable_id")
        if not isinstance(variable_id, str) or not variable_id:
            raise SystemBehaviorValidationError("variable_id must be a non-empty string")
        if variable_id in seen:
            raise SystemBehaviorValidationError(f"duplicate variable_id: {variable_id}")
        if row.get("stage") not in VARIABLE_STAGES:
            raise SystemBehaviorValidationError(f"invalid stage for {variable_id}")
        targets = row.get("target_boundary_family")
        if not isinstance(targets, list) or not targets:
            raise SystemBehaviorValidationError(f"missing target_boundary_family for {variable_id}")
        if not isinstance(row.get("held_constant_fields"), list):
            raise SystemBehaviorValidationError(f"missing held_constant_fields for {variable_id}")
        if not isinstance(row.get("expected_observable_family"), list):
            raise SystemBehaviorValidationError(f"missing expected_observable_family for {variable_id}")
        if not isinstance(row.get("evidence_requirements"), list):
            raise SystemBehaviorValidationError(f"missing evidence_requirements for {variable_id}")
        seen[variable_id] = row
    return seen


def validate_boundary_registry(registry: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    if registry.get("schema") != BOUNDARY_REGISTRY_SCHEMA:
        raise SystemBehaviorValidationError("unexpected measurement-boundary registry schema")
    rows = registry.get("boundaries")
    if not isinstance(rows, list) or not rows:
        raise SystemBehaviorValidationError("measurement-boundary registry must contain boundaries")

    seen: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        boundary_id = row.get("boundary_id")
        if not isinstance(boundary_id, str) or not boundary_id:
            raise SystemBehaviorValidationError("boundary_id must be a non-empty string")
        if boundary_id in seen:
            raise SystemBehaviorValidationError(f"duplicate boundary_id: {boundary_id}")
        anchor_classes = row.get("supports_anchor_classes")
        if not isinstance(anchor_classes, list):
            raise SystemBehaviorValidationError(f"missing supports_anchor_classes for {boundary_id}")
        unknown = set(anchor_classes) - ANCHOR_CLASSES
        if unknown:
            raise SystemBehaviorValidationError(
                f"unknown anchor classes for {boundary_id}: {sorted(unknown)}"
            )
        seen[boundary_id] = row
    return seen


def validate_registry_crossrefs(
    variable_registry: Mapping[str, Any], boundary_registry: Mapping[str, Any]
) -> None:
    variables = validate_variable_registry(variable_registry)
    boundaries = validate_boundary_registry(boundary_registry)
    boundary_ids = set(boundaries)
    for variable_id, row in variables.items():
        missing = set(row["target_boundary_family"]) - boundary_ids
        if missing:
            raise SystemBehaviorValidationError(
                f"variable {variable_id} references unknown boundaries: {sorted(missing)}"
            )


def make_behavior_event(
    *,
    behavior_event_id: str,
    trajectory_id: str,
    event_index: int,
    turn: int,
    boundary_id: str,
    actor: str,
    action_type: str,
    realization_status: str,
    state_before_hash: str | None,
    state_after_hash: str | None,
    node_id: str | None = None,
    branch_id: str | None = None,
    target_ref: str | None = None,
    source_refs: Iterable[str] = (),
    parent_event_refs: Iterable[str] = (),
    authority_before: Iterable[str] = (),
    authority_after: Iterable[str] = (),
    raw_event_ref: str | None = None,
    structured_diff: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    record = {
        "schema": BEHAVIOR_SCHEMA,
        "behavior_event_id": behavior_event_id,
        "trajectory_id": trajectory_id,
        "branch_id": branch_id,
        "event_index": event_index,
        "turn": turn,
        "node_id": node_id,
        "boundary_id": boundary_id,
        "actor": actor,
        "action_type": action_type,
        "target_ref": target_ref,
        "realization_status": realization_status,
        "state_before_hash": state_before_hash,
        "state_after_hash": state_after_hash,
        "authority_before": list(authority_before),
        "authority_after": list(authority_after),
        "source_refs": list(source_refs),
        "parent_event_refs": list(parent_event_refs),
        "raw_event_ref": raw_event_ref,
        "structured_diff": dict(structured_diff) if structured_diff is not None else None,
        "semantic_status": "NOT_ADJUDICATED",
    }
    validate_behavior_event(record)
    record["behavior_event_hash"] = content_hash(record)
    return record


def validate_behavior_event(
    record: Mapping[str, Any], *, boundary_registry: Mapping[str, Any] | None = None
) -> None:
    if record.get("schema") != BEHAVIOR_SCHEMA:
        raise SystemBehaviorValidationError("unexpected behavior-event schema")
    for key in ("behavior_event_id", "trajectory_id", "boundary_id", "actor"):
        if not isinstance(record.get(key), str) or not record[key]:
            raise SystemBehaviorValidationError(f"{key} must be a non-empty string")
    for key in ("event_index", "turn"):
        value = record.get(key)
        if not isinstance(value, int) or value < 0:
            raise SystemBehaviorValidationError(f"{key} must be a non-negative integer")
    if record.get("action_type") not in ACTION_TYPES:
        raise SystemBehaviorValidationError("invalid behavior action_type")
    if record.get("realization_status") not in REALIZATION_STATUSES:
        raise SystemBehaviorValidationError("invalid realization_status")
    for key in ("source_refs", "parent_event_refs"):
        if not isinstance(record.get(key), list):
            raise SystemBehaviorValidationError(f"{key} must be a list")
    if boundary_registry is not None:
        boundaries = validate_boundary_registry(boundary_registry)
        if record["boundary_id"] not in boundaries:
            raise SystemBehaviorValidationError(
                f"unknown behavior boundary_id: {record['boundary_id']}"
            )


def build_system_trajectory_measurement(
    *,
    measurement_id: str,
    trajectory_id: str,
    source_trace_hash: str,
    source_version: str,
    termination_status: str,
    behavior_events: Iterable[Mapping[str, Any]],
    jump_candidate_refs: Iterable[str] = (),
    first_jump_candidate_ref: str | None = None,
    first_jump_turn: int | None = None,
    descendant_event_count: int = 0,
    affected_agent_count: int = 0,
    operational_boundary_crossing_count: int = 0,
    retrospective_window_refs: Iterable[str] = (),
    branch_id: str | None = None,
    parent_trace_hash: str | None = None,
    parent_state_hash: str | None = None,
    branch_start_state_hash: str | None = None,
    source_evidence_batch_hash: str | None = None,
    model_config_hash: str | None = None,
    code_sha: str | None = None,
    experimental_variables: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    events = [dict(row) for row in behavior_events]
    for row in events:
        validate_behavior_event(row)
    jump_refs = list(jump_candidate_refs)
    retro_refs = list(retrospective_window_refs)
    record = {
        "schema": TRAJECTORY_SCHEMA,
        "measurement_id": measurement_id,
        "trajectory_id": trajectory_id,
        "branch_id": branch_id,
        "parent_trace_hash": parent_trace_hash,
        "parent_state_hash": parent_state_hash,
        "branch_start_state_hash": branch_start_state_hash,
        "source_trace_hash": source_trace_hash,
        "source_evidence_batch_hash": source_evidence_batch_hash,
        "source_version": source_version,
        "measurement_contract": "System Behavior Measurement v4",
        "model_config_hash": model_config_hash,
        "code_sha": code_sha,
        "termination_status": termination_status,
        "behavior_event_count": len(events),
        "behavior_event_refs": [row["behavior_event_id"] for row in events],
        "r2": {
            "jump_candidate_count": len(jump_refs),
            "jump_candidate_refs": jump_refs,
            "first_jump_candidate_ref": first_jump_candidate_ref,
            "first_jump_turn": first_jump_turn,
            "jump_type_counts": {},
        },
        "r3": {
            "descendant_event_count": descendant_event_count,
            "affected_agent_count": affected_agent_count,
            "operational_boundary_crossing_count": operational_boundary_crossing_count,
            "penetration_status": "NOT_ADJUDICATED",
            "post_jump_persistence": None,
            "provenance_retention_status": None,
        },
        "r4": {
            "retrospective_window_count": len(retro_refs),
            "retrospective_window_refs": retro_refs,
            "semantic_r_status": "NOT_ADJUDICATED",
            "recovery_status": None,
        },
        "experimental_variables": [dict(row) for row in experimental_variables],
        "semantic_status": "NOT_ADJUDICATED",
    }
    record["measurement_hash"] = content_hash(record)
    return record


@dataclass(frozen=True)
class RegistryBundle:
    variables: Mapping[str, Any]
    boundaries: Mapping[str, Any]

    @classmethod
    def load(
        cls,
        variable_path: str | Path = "configs/experimental_variable_registry_v0.1.json",
        boundary_path: str | Path = "configs/measurement_boundary_registry_v0.1.json",
    ) -> "RegistryBundle":
        variables = load_json(variable_path)
        boundaries = load_json(boundary_path)
        validate_registry_crossrefs(variables, boundaries)
        return cls(variables=variables, boundaries=boundaries)
