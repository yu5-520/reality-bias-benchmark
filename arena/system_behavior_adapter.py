from __future__ import annotations

import copy
from collections import Counter
from typing import Any, Iterable, Mapping

from .system_behavior import (
    RegistryBundle,
    build_system_trajectory_measurement,
    content_hash,
    make_behavior_event,
    validate_behavior_event,
)


ADAPTER_SCHEMA = "RB-SYSTEM-BEHAVIOR-ADAPTER-v0.1"
SUPPORTED_TRACE_SCHEMAS = {"R2-ARENA-TRACE-v0.3"}

ACTION_MAP = {
    "message": ("MESSAGE_HANDOFF", "message"),
    "invoke_agent": ("INVOCATION", "invoke"),
    "write_state": ("SHARED_STATE", "write"),
    "revise_final_state": ("FINAL_REOPEN", "revise"),
    "finalize": ("FINAL_REOPEN", "finalize"),
    "late_event": ("MESSAGE_HANDOFF", "message"),
}


class SystemBehaviorAdapterError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemBehaviorAdapterError(message)


def _snapshot_from_event(event: Mapping[str, Any], suffix: str) -> dict[str, Any]:
    return {
        "shared_state": copy.deepcopy(event.get(f"shared_state_{suffix}")),
        "shared_state_metadata": copy.deepcopy(event.get(f"shared_state_metadata_{suffix}")),
        "final_state": copy.deepcopy(event.get(f"final_state_{suffix}")),
        "active_agents": copy.deepcopy(event.get(f"active_agents_{suffix}")),
        "queue": copy.deepcopy(event.get(f"queue_{suffix}")),
    }


def _snapshot_hash(event: Mapping[str, Any], suffix: str) -> str:
    return content_hash(_snapshot_from_event(event, suffix))


def _changed_keys(before: Any, after: Any) -> list[str]:
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        return []
    keys = set(before) | set(after)
    return sorted(key for key in keys if before.get(key) != after.get(key))


def _final_identity(value: Any) -> tuple[str | None, int | None]:
    if not isinstance(value, Mapping):
        return None, None
    revision_count = value.get("revision_count")
    return (
        value.get("state_id") if isinstance(value.get("state_id"), str) else None,
        revision_count if isinstance(revision_count, int) else None,
    )


def _structured_diff(event: Mapping[str, Any]) -> dict[str, Any]:
    before_state = event.get("shared_state_before") or {}
    after_state = event.get("shared_state_after") or {}
    before_meta = event.get("shared_state_metadata_before") or {}
    after_meta = event.get("shared_state_metadata_after") or {}
    before_agents = set(event.get("active_agents_before") or [])
    after_agents = set(event.get("active_agents_after") or [])
    before_queue = event.get("queue_before") or []
    after_queue = event.get("queue_after") or []
    action = event.get("action") or {}
    final_before_id, final_before_revision = _final_identity(event.get("final_state_before"))
    final_after_id, final_after_revision = _final_identity(event.get("final_state_after"))

    out = {
        "source_action_type": event.get("action_type"),
        "source_note": event.get("note"),
        "declared_authority_class": event.get("authority_class"),
        "shared_state_changed_keys": _changed_keys(before_state, after_state),
        "shared_state_metadata_changed_keys": _changed_keys(before_meta, after_meta),
        "final_state_changed": event.get("final_state_before") != event.get("final_state_after"),
        "final_state_before_id": final_before_id,
        "final_state_after_id": final_after_id,
        "final_state_before_revision_count": final_before_revision,
        "final_state_after_revision_count": final_after_revision,
        "active_agents_added": sorted(after_agents - before_agents),
        "active_agents_removed": sorted(before_agents - after_agents),
        "queue_length_before": len(before_queue),
        "queue_length_after": len(after_queue),
    }
    for key in ("key", "status", "agent_id", "to", "message_id", "invocation_id"):
        if key in action:
            out[f"action_{key}"] = copy.deepcopy(action.get(key))
    return out


def _visible_shared_state_origins(call: Mapping[str, Any]) -> list[dict[str, Any]]:
    runtime = call.get("runtime_snapshot") or {}
    metadata = runtime.get("shared_state_metadata") or {}
    state = runtime.get("shared_state") or {}
    out = []
    if not isinstance(metadata, Mapping) or not isinstance(state, Mapping):
        return out
    for key in sorted(metadata):
        meta = metadata.get(key)
        if not isinstance(meta, Mapping):
            continue
        source_event_index = meta.get("event_index")
        if not isinstance(source_event_index, int):
            continue
        out.append(
            {
                "key": str(key),
                "source_event_index": source_event_index,
                "writer": meta.get("writer"),
                "status": meta.get("status"),
                "value_hash": content_hash(state.get(key)),
            }
        )
    return out


def _target_ref(event: Mapping[str, Any]) -> str | None:
    action = event.get("action") or {}
    kind = event.get("action_type")
    if kind == "message":
        return action.get("message_id") or (f"agent:{action.get('to')}" if action.get("to") else None)
    if kind == "invoke_agent":
        return action.get("invocation_id") or (
            f"agent:{action.get('agent_id')}" if action.get("agent_id") else None
        )
    if kind == "write_state":
        key = action.get("key")
        return f"shared_state:{key}" if key else None
    if kind == "revise_final_state":
        return "final_state"
    if kind == "finalize":
        final_after = event.get("final_state_after") or {}
        return final_after.get("state_id") or "final_state"
    if kind == "late_event":
        return action.get("message_id") or "environment_late_event"
    return kind


def _source_event_ref(source_index: int) -> str:
    return f"arena_event:{source_index}"


def _stage_action_events(trace: Mapping[str, Any]) -> list[dict[str, Any]]:
    run_id = str(trace["run_id"])
    branch_id = (trace.get("experimental_branch") or {}).get("branch_id")
    staged: list[dict[str, Any]] = []

    for source_index, event in enumerate(trace.get("events") or []):
        source_event_index = event.get("event_index")
        if not isinstance(source_event_index, int):
            source_event_index = source_index
        turn = event.get("turn")
        _require(isinstance(turn, int) and turn >= 0, "source_event_turn_invalid")
        source_kind = str(event.get("action_type"))
        boundary_id, normalized_action = ACTION_MAP.get(source_kind, ("AGENT_TURN", "other"))
        source_ref = _source_event_ref(source_event_index)
        actor = str(event.get("actor") or "UNKNOWN")
        before_hash = _snapshot_hash(event, "before")
        after_hash = _snapshot_hash(event, "after")
        target_ref = _target_ref(event)
        diff = _structured_diff(event)

        if actor != "ENVIRONMENT":
            proposal_id = f"{run_id}:arena:{source_event_index}:proposal"
            staged.append(
                {
                    "sort_key": (turn, 100 + source_event_index * 10, 0),
                    "event": {
                        "behavior_event_id": proposal_id,
                        "trajectory_id": run_id,
                        "branch_id": branch_id,
                        "turn": turn,
                        "node_id": f"turn:{turn}",
                        "boundary_id": boundary_id,
                        "actor": actor,
                        "action_type": normalized_action,
                        "target_ref": target_ref,
                        "realization_status": "PROPOSAL",
                        "state_before_hash": before_hash,
                        "state_after_hash": before_hash,
                        "source_refs": [source_ref],
                        "parent_event_refs": [],
                        "raw_event_ref": source_ref,
                        "structured_diff": {
                            **diff,
                            "behavior_phase": "PROPOSAL",
                            "source_event_index": source_event_index,
                        },
                    },
                }
            )
            parent_refs = [proposal_id]
        else:
            parent_refs = []

        outcome_id = f"{run_id}:arena:{source_event_index}:outcome"
        staged.append(
            {
                "sort_key": (turn, 100 + source_event_index * 10, 1),
                "event": {
                    "behavior_event_id": outcome_id,
                    "trajectory_id": run_id,
                    "branch_id": branch_id,
                    "turn": turn,
                    "node_id": f"turn:{turn}",
                    "boundary_id": boundary_id,
                    "actor": actor,
                    "action_type": normalized_action,
                    "target_ref": target_ref,
                    "realization_status": "REALIZED" if event.get("realized_in_baseline") else "BLOCKED",
                    "state_before_hash": before_hash,
                    "state_after_hash": after_hash,
                    "source_refs": [source_ref],
                    "parent_event_refs": parent_refs,
                    "raw_event_ref": source_ref,
                    "structured_diff": {
                        **diff,
                        "behavior_phase": "REALIZATION",
                        "source_event_index": source_event_index,
                    },
                },
            }
        )
    return staged


def _stage_message_reads(trace: Mapping[str, Any]) -> list[dict[str, Any]]:
    run_id = str(trace["run_id"])
    branch_id = (trace.get("experimental_branch") or {}).get("branch_id")
    staged: list[dict[str, Any]] = []
    for row_index, row in enumerate(trace.get("message_ledger") or []):
        read_turn = row.get("read_turn")
        read_by = row.get("read_by")
        message_id = row.get("message_id")
        if not isinstance(read_turn, int) or read_turn < 0 or not read_by or not message_id:
            continue
        refs = [f"message:{message_id}"]
        if row.get("invocation_id"):
            refs.append(f"invocation:{row['invocation_id']}")
        staged.append(
            {
                "sort_key": (read_turn, 10, row_index),
                "event": {
                    "behavior_event_id": f"{run_id}:message:{message_id}:read",
                    "trajectory_id": run_id,
                    "branch_id": branch_id,
                    "turn": read_turn,
                    "node_id": f"turn:{read_turn}",
                    "boundary_id": "MESSAGE_HANDOFF",
                    "actor": str(read_by),
                    "action_type": "read",
                    "target_ref": f"message:{message_id}",
                    "realization_status": "REALIZED",
                    "state_before_hash": None,
                    "state_after_hash": None,
                    "source_refs": refs,
                    "parent_event_refs": [],
                    "raw_event_ref": f"message_ledger:{message_id}",
                    "structured_diff": {
                        "behavior_phase": "READ",
                        "message_id": message_id,
                        "sender": row.get("sender"),
                        "recipient": row.get("recipient"),
                        "message_type": row.get("message_type"),
                        "sent_turn": row.get("sent_turn"),
                        "delivered_turn": row.get("delivered_turn"),
                        "read_turn": read_turn,
                    },
                },
            }
        )
    return staged


def _stage_invocation_reads(trace: Mapping[str, Any]) -> list[dict[str, Any]]:
    run_id = str(trace["run_id"])
    branch_id = (trace.get("experimental_branch") or {}).get("branch_id")
    staged: list[dict[str, Any]] = []
    for row_index, row in enumerate(trace.get("invocation_ledger") or []):
        read_turn = row.get("read_turn")
        invocation_id = row.get("invocation_id")
        target = row.get("target")
        if not isinstance(read_turn, int) or read_turn < 0 or not invocation_id or not target:
            continue
        status = row.get("execution_status")
        realization_status = "FAILED" if status == "failed" else "REALIZED"
        staged.append(
            {
                "sort_key": (read_turn, 20, row_index),
                "event": {
                    "behavior_event_id": f"{run_id}:invocation:{invocation_id}:read",
                    "trajectory_id": run_id,
                    "branch_id": branch_id,
                    "turn": read_turn,
                    "node_id": f"turn:{read_turn}",
                    "boundary_id": "INVOCATION",
                    "actor": str(target),
                    "action_type": "read",
                    "target_ref": f"invocation:{invocation_id}",
                    "realization_status": realization_status,
                    "state_before_hash": None,
                    "state_after_hash": None,
                    "source_refs": [f"invocation:{invocation_id}"],
                    "parent_event_refs": [],
                    "raw_event_ref": f"invocation_ledger:{invocation_id}",
                    "structured_diff": {
                        "behavior_phase": "READ",
                        "requester": row.get("requester"),
                        "target": target,
                        "queued": row.get("queued"),
                        "read_turn": read_turn,
                        "execution_turn": row.get("execution_turn"),
                        "execution_status": row.get("execution_status"),
                        "proposal_event_index": row.get("proposal_event_index"),
                    },
                },
            }
        )
    return staged


def _stage_agent_turns(trace: Mapping[str, Any]) -> list[dict[str, Any]]:
    run_id = str(trace["run_id"])
    branch_id = (trace.get("experimental_branch") or {}).get("branch_id")
    staged: list[dict[str, Any]] = []
    for row_index, call in enumerate(trace.get("model_calls") or []):
        turn = call.get("turn")
        actor = call.get("agent_id")
        if not isinstance(turn, int) or turn < 0 or not actor:
            continue
        status = call.get("status")
        realization_status = "REALIZED" if status == "completed" else "FAILED"
        source_refs = [f"model_call:turn:{turn}:agent:{actor}"]
        source_refs.extend(f"message:{mid}" for mid in (call.get("input_message_ids") or []))
        source_refs.extend(f"invocation:{iid}" for iid in (call.get("input_invocation_ids") or []))
        runtime = call.get("runtime_snapshot") or {}
        final_visible_id, final_visible_revision = _final_identity(runtime.get("final_state"))
        staged.append(
            {
                "sort_key": (turn, 90, row_index),
                "event": {
                    "behavior_event_id": f"{run_id}:turn:{turn}:agent:{actor}",
                    "trajectory_id": run_id,
                    "branch_id": branch_id,
                    "turn": turn,
                    "node_id": f"turn:{turn}",
                    "boundary_id": "AGENT_TURN",
                    "actor": str(actor),
                    "action_type": "other",
                    "target_ref": f"turn:{turn}",
                    "realization_status": realization_status,
                    "state_before_hash": None,
                    "state_after_hash": None,
                    "source_refs": source_refs,
                    "parent_event_refs": [],
                    "raw_event_ref": f"model_call:{row_index}",
                    "structured_diff": {
                        "behavior_phase": "NODE_EXECUTION",
                        "runtime_snapshot_hash": call.get("runtime_snapshot_hash"),
                        "event_index_start": call.get("event_index_start"),
                        "event_index_end": call.get("event_index_end"),
                        "input_message_ids": list(call.get("input_message_ids") or []),
                        "input_invocation_ids": list(call.get("input_invocation_ids") or []),
                        "visible_shared_state_origins": _visible_shared_state_origins(call),
                        "visible_final_state_id": final_visible_id,
                        "visible_final_revision_count": final_visible_revision,
                        "call_status": status,
                    },
                },
            }
        )
    return staged


def adapt_arena_trace_v03(trace: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(trace, Mapping), "trace_must_be_object")
    source_version = trace.get("trace_schema_version")
    _require(source_version in SUPPORTED_TRACE_SCHEMAS, f"unsupported_trace_schema:{source_version}")
    _require(isinstance(trace.get("run_id"), str) and trace.get("run_id"), "run_id_required")

    bundle = RegistryBundle.load()
    staged = []
    staged.extend(_stage_message_reads(trace))
    staged.extend(_stage_invocation_reads(trace))
    staged.extend(_stage_agent_turns(trace))
    staged.extend(_stage_action_events(trace))
    staged.sort(key=lambda row: row["sort_key"])

    behavior_events: list[dict[str, Any]] = []
    ids = set()
    for derived_index, staged_row in enumerate(staged):
        raw = staged_row["event"]
        event_id = raw["behavior_event_id"]
        _require(event_id not in ids, f"duplicate_behavior_event_id:{event_id}")
        ids.add(event_id)
        event = make_behavior_event(
            behavior_event_id=event_id,
            trajectory_id=raw["trajectory_id"],
            branch_id=raw.get("branch_id"),
            event_index=derived_index,
            turn=raw["turn"],
            node_id=raw.get("node_id"),
            boundary_id=raw["boundary_id"],
            actor=raw["actor"],
            action_type=raw["action_type"],
            target_ref=raw.get("target_ref"),
            realization_status=raw["realization_status"],
            state_before_hash=raw.get("state_before_hash"),
            state_after_hash=raw.get("state_after_hash"),
            source_refs=raw.get("source_refs") or [],
            parent_event_refs=raw.get("parent_event_refs") or [],
            raw_event_ref=raw.get("raw_event_ref"),
            structured_diff=raw.get("structured_diff"),
        )
        event["behavior_phase"] = (raw.get("structured_diff") or {}).get("behavior_phase")
        event["source_trace_schema_version"] = source_version
        event["behavior_event_hash"] = content_hash(
            {key: value for key, value in event.items() if key != "behavior_event_hash"}
        )
        validate_behavior_event(event, boundary_registry=bundle.boundaries)
        behavior_events.append(event)

    boundary_counts = Counter(row["boundary_id"] for row in behavior_events)
    action_counts = Counter(row["action_type"] for row in behavior_events)
    realization_counts = Counter(row["realization_status"] for row in behavior_events)
    phase_counts = Counter(str(row.get("behavior_phase")) for row in behavior_events)
    unsupported_source_actions = sorted(
        {
            str(row.get("action_type"))
            for row in (trace.get("events") or [])
            if str(row.get("action_type")) not in ACTION_MAP
        }
    )

    source_trace_hash = content_hash(trace)
    branch = trace.get("experimental_branch") or {}
    measurement = build_system_trajectory_measurement(
        measurement_id=f"{trace['run_id']}:system-behavior-v4",
        trajectory_id=trace["run_id"],
        branch_id=branch.get("branch_id"),
        parent_trace_hash=branch.get("parent_trace_hash"),
        parent_state_hash=branch.get("parent_state_hash"),
        branch_start_state_hash=branch.get("branch_start_state_hash"),
        source_trace_hash=source_trace_hash,
        source_version=source_version,
        termination_status=str(trace.get("run_status") or "UNKNOWN"),
        behavior_events=behavior_events,
    )
    measurement["r2"]["jump_detection_status"] = "NOT_RUN_DETECTOR_NOT_FROZEN"
    measurement["r3"]["lineage_status"] = "STRUCTURAL_BEHAVIOR_INDEX_AVAILABLE_JUMP_ANCHOR_NOT_FROZEN"
    measurement["r4"]["retrospective_detection_status"] = "NOT_RUN_JUMP_ANCHOR_NOT_FROZEN"
    measurement["measurement_hash"] = content_hash(
        {key: value for key, value in measurement.items() if key != "measurement_hash"}
    )

    summary = {
        "schema": ADAPTER_SCHEMA,
        "adapter_version": "0.1",
        "source_trace_schema_version": source_version,
        "source_trace_hash": source_trace_hash,
        "run_id": trace["run_id"],
        "run_status": trace.get("run_status"),
        "behavior_event_count": len(behavior_events),
        "boundary_counts": dict(sorted(boundary_counts.items())),
        "action_counts": dict(sorted(action_counts.items())),
        "realization_counts": dict(sorted(realization_counts.items())),
        "phase_counts": dict(sorted(phase_counts.items())),
        "unsupported_source_actions": unsupported_source_actions,
        "semantic_status": "NOT_ADJUDICATED",
        "scientific_evidence_status": "DERIVED_FROM_SOURCE_TRACE_NOT_NEW_SUBJECT_EVIDENCE",
    }
    summary["adapter_output_hash"] = content_hash(summary)

    return {
        "schema": ADAPTER_SCHEMA,
        "summary": summary,
        "behavior_events": behavior_events,
        "system_trajectory_measurement": measurement,
    }
