from __future__ import annotations

import copy
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from .system_behavior import BEHAVIOR_SCHEMA, content_hash, load_json
from .system_behavior_dynamics_v4 import build_system_dynamics_view, slice_behavior_events_for_branch


LINEAGE_RULES_SCHEMA = "RB-SOURCE-LINEAGE-RULES-v0.1"
LINEAGE_RELATION_SCHEMA = "RB-SOURCE-LINEAGE-RELATION-v0.1"
LINEAGE_VIEW_SCHEMA = "RB-SYSTEM-LINEAGE-VIEW-v4.0"
NOT_ADJUDICATED = "NOT_ADJUDICATED"


class SystemBehaviorLineageError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemBehaviorLineageError(message)


def validate_lineage_rules(config: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    _require(config.get("schema") == LINEAGE_RULES_SCHEMA, "lineage_rules_schema_invalid")
    _require(config.get("version") == "0.1", "lineage_rules_version_invalid")
    _require(config.get("source_behavior_schema") == BEHAVIOR_SCHEMA, "lineage_behavior_schema_invalid")
    rows = config.get("relations")
    _require(isinstance(rows, list) and rows, "lineage_relations_required")
    out = {}
    for row in rows:
        relation_type = row.get("relation_type")
        _require(isinstance(relation_type, str) and relation_type, "lineage_relation_type_required")
        _require(relation_type not in out, f"duplicate_lineage_relation_type:{relation_type}")
        for key in ("family", "evidence_basis", "strength"):
            _require(isinstance(row.get(key), str) and row.get(key), f"lineage_{key}_required:{relation_type}")
        out[relation_type] = row
    return out


def load_lineage_rules(
    path: str | Path = "configs/source_lineage_rules_v0.1.json",
) -> dict[str, Any]:
    config = load_json(path)
    validate_lineage_rules(config)
    return config


def _diff(event: Mapping[str, Any]) -> Mapping[str, Any]:
    value = event.get("structured_diff")
    return value if isinstance(value, Mapping) else {}


def _message_id_from_read(event: Mapping[str, Any]) -> str | None:
    value = _diff(event).get("message_id")
    return value if isinstance(value, str) and value else None


def _invocation_id_from_read(event: Mapping[str, Any]) -> str | None:
    target = event.get("target_ref")
    if isinstance(target, str) and target.startswith("invocation:"):
        return target.split(":", 1)[1]
    return None


def _make_relation(
    *,
    relation_type: str,
    source_event: Mapping[str, Any],
    target_event: Mapping[str, Any],
    rule_map: Mapping[str, Mapping[str, Any]],
    rules_hash: str,
    evidence_refs: Iterable[str],
    evidence_detail: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    rule = rule_map[relation_type]
    _require(
        source_event["trajectory_id"] == target_event["trajectory_id"],
        "cross_trajectory_lineage_forbidden",
    )
    _require(
        int(source_event["event_index"]) < int(target_event["event_index"]),
        f"lineage_must_move_forward:{relation_type}",
    )
    record = {
        "schema": LINEAGE_RELATION_SCHEMA,
        "lineage_rules_version": "0.1",
        "lineage_rules_hash": rules_hash,
        "relation_type": relation_type,
        "family": rule["family"],
        "strength": rule["strength"],
        "trajectory_id": source_event["trajectory_id"],
        "branch_id": source_event.get("branch_id") or target_event.get("branch_id"),
        "source_behavior_event_id": source_event["behavior_event_id"],
        "target_behavior_event_id": target_event["behavior_event_id"],
        "source_event_index": source_event["event_index"],
        "target_event_index": target_event["event_index"],
        "source_turn": source_event["turn"],
        "target_turn": target_event["turn"],
        "source_actor": source_event["actor"],
        "target_actor": target_event["actor"],
        "evidence_refs": sorted(set(str(ref) for ref in evidence_refs if ref)),
        "evidence_detail": dict(evidence_detail or {}),
        "lineage_status": "SOURCE_BACKED_STRUCTURAL_LINEAGE",
        "semantic_adoption_status": NOT_ADJUDICATED,
        "authority_penetration_status": NOT_ADJUDICATED,
    }
    record["relation_id"] = (
        f"{record['trajectory_id']}:LINEAGE:{relation_type}:"
        f"{record['source_event_index']:04d}:{record['target_event_index']:04d}"
    )
    record["relation_hash"] = content_hash(record)
    return record


def derive_source_backed_lineage(
    behavior_events: Iterable[Mapping[str, Any]],
    rules: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    events = [dict(row) for row in behavior_events]
    events.sort(key=lambda row: int(row["event_index"]))
    if not events:
        return []
    rules_cfg = dict(rules or load_lineage_rules())
    rule_map = validate_lineage_rules(rules_cfg)
    rules_hash = content_hash(rules_cfg)
    event_by_id = {row["behavior_event_id"]: row for row in events}

    relations: list[dict[str, Any]] = []
    seen = set()

    def add(
        relation_type: str,
        source: Mapping[str, Any] | None,
        target: Mapping[str, Any] | None,
        evidence_refs: Iterable[str] = (),
        evidence_detail: Mapping[str, Any] | None = None,
    ) -> None:
        if source is None or target is None:
            return
        if relation_type not in rule_map:
            raise SystemBehaviorLineageError(f"unregistered_lineage_relation:{relation_type}")
        key = (relation_type, source["behavior_event_id"], target["behavior_event_id"])
        if key in seen:
            return
        if int(source["event_index"]) >= int(target["event_index"]):
            return
        seen.add(key)
        relations.append(
            _make_relation(
                relation_type=relation_type,
                source_event=source,
                target_event=target,
                rule_map=rule_map,
                rules_hash=rules_hash,
                evidence_refs=evidence_refs,
                evidence_detail=evidence_detail,
            )
        )

    # Exact proposal → realization identity already exists in BehaviorEvent parent refs.
    for target in events:
        if target.get("behavior_phase") != "REALIZATION":
            continue
        for parent_id in target.get("parent_event_refs") or []:
            parent = event_by_id.get(parent_id)
            add(
                "PROPOSAL_TO_REALIZATION",
                parent,
                target,
                evidence_refs=[parent_id, target.get("raw_event_ref")],
            )

    # Agent-turn execution → proposals generated by that exact source event range.
    proposals = [row for row in events if row.get("behavior_phase") == "PROPOSAL"]
    for turn_event in events:
        if turn_event.get("boundary_id") != "AGENT_TURN":
            continue
        detail = _diff(turn_event)
        start = detail.get("event_index_start")
        end = detail.get("event_index_end")
        if not isinstance(start, int) or not isinstance(end, int):
            continue
        for proposal in proposals:
            source_index = _diff(proposal).get("source_event_index")
            if (
                isinstance(source_index, int)
                and start <= source_index < end
                and proposal.get("actor") == turn_event.get("actor")
                and proposal.get("turn") == turn_event.get("turn")
            ):
                add(
                    "AGENT_TURN_TO_ACTION_PROPOSAL",
                    turn_event,
                    proposal,
                    evidence_refs=[turn_event.get("raw_event_ref"), proposal.get("raw_event_ref")],
                    evidence_detail={"source_event_index": source_index, "range": [start, end]},
                )

    message_reads = {
        mid: row
        for row in events
        if row.get("boundary_id") == "MESSAGE_HANDOFF"
        and row.get("action_type") == "read"
        and (mid := _message_id_from_read(row))
    }
    invocation_reads = {
        iid: row
        for row in events
        if row.get("boundary_id") == "INVOCATION"
        and row.get("action_type") == "read"
        and (iid := _invocation_id_from_read(row))
    }

    # Realized message/invocation delivery → exact ledger read.
    for event in events:
        if event.get("behavior_phase") != "REALIZATION" or event.get("realization_status") != "REALIZED":
            continue
        detail = _diff(event)
        message_id = detail.get("action_message_id")
        invocation_id = detail.get("action_invocation_id")
        if event.get("boundary_id") == "MESSAGE_HANDOFF" and isinstance(message_id, str):
            add(
                "MESSAGE_REALIZATION_TO_READ",
                event,
                message_reads.get(message_id),
                evidence_refs=[f"message:{message_id}", event.get("raw_event_ref")],
                evidence_detail={"message_id": message_id},
            )
        if event.get("boundary_id") == "INVOCATION":
            if isinstance(message_id, str):
                add(
                    "INVOCATION_REALIZATION_TO_MESSAGE_READ",
                    event,
                    message_reads.get(message_id),
                    evidence_refs=[f"message:{message_id}", event.get("raw_event_ref")],
                    evidence_detail={"message_id": message_id, "invocation_id": invocation_id},
                )
            if isinstance(invocation_id, str):
                add(
                    "INVOCATION_REALIZATION_TO_INVOCATION_READ",
                    event,
                    invocation_reads.get(invocation_id),
                    evidence_refs=[f"invocation:{invocation_id}", event.get("raw_event_ref")],
                    evidence_detail={"invocation_id": invocation_id},
                )

    # Exact consumed message/invocation IDs → the Agent turn that received them.
    for turn_event in events:
        if turn_event.get("boundary_id") != "AGENT_TURN":
            continue
        detail = _diff(turn_event)
        for message_id in detail.get("input_message_ids") or []:
            read_event = message_reads.get(message_id)
            if read_event and read_event.get("actor") == turn_event.get("actor") and read_event.get("turn") == turn_event.get("turn"):
                add(
                    "MESSAGE_READ_TO_AGENT_TURN",
                    read_event,
                    turn_event,
                    evidence_refs=[f"message:{message_id}", turn_event.get("raw_event_ref")],
                    evidence_detail={"message_id": message_id},
                )
        for invocation_id in detail.get("input_invocation_ids") or []:
            read_event = invocation_reads.get(invocation_id)
            if read_event and read_event.get("actor") == turn_event.get("actor") and read_event.get("turn") == turn_event.get("turn"):
                add(
                    "INVOCATION_READ_TO_AGENT_TURN",
                    read_event,
                    turn_event,
                    evidence_refs=[f"invocation:{invocation_id}", turn_event.get("raw_event_ref")],
                    evidence_detail={"invocation_id": invocation_id},
                )

    # Exact shared-state source event index recorded in the later runtime snapshot.
    realized_by_source_index = {}
    for event in events:
        if event.get("behavior_phase") != "REALIZATION" or event.get("realization_status") != "REALIZED":
            continue
        source_index = _diff(event).get("source_event_index")
        if isinstance(source_index, int):
            realized_by_source_index[source_index] = event
    for turn_event in events:
        if turn_event.get("boundary_id") != "AGENT_TURN":
            continue
        visible = _diff(turn_event).get("visible_shared_state_origins") or []
        grouped: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
        for origin in visible:
            if isinstance(origin, Mapping) and isinstance(origin.get("source_event_index"), int):
                grouped[origin["source_event_index"]].append(origin)
        for source_index, origins in grouped.items():
            source_event = realized_by_source_index.get(source_index)
            if source_event is None or source_event.get("action_type") not in {"write", "revise"}:
                continue
            writers = {origin.get("writer") for origin in origins if origin.get("writer")}
            if writers and source_event.get("actor") not in writers:
                continue
            add(
                "STATE_MUTATION_TO_AGENT_TURN_VISIBILITY",
                source_event,
                turn_event,
                evidence_refs=[source_event.get("raw_event_ref"), turn_event.get("raw_event_ref")],
                evidence_detail={
                    "source_event_index": source_index,
                    "visible_keys": sorted(str(origin.get("key")) for origin in origins),
                    "origin_hashes": sorted(str(origin.get("value_hash")) for origin in origins),
                },
            )

    # Exact final-state version ancestry and runtime visibility.
    latest_version_event: dict[tuple[str, int], Mapping[str, Any]] = {}
    for event in events:
        detail = _diff(event)
        if event.get("boundary_id") == "AGENT_TURN":
            state_id = detail.get("visible_final_state_id")
            revision_count = detail.get("visible_final_revision_count")
            if isinstance(state_id, str) and isinstance(revision_count, int):
                source = latest_version_event.get((state_id, revision_count))
                add(
                    "FINAL_STATE_VERSION_TO_AGENT_TURN_VISIBILITY",
                    source,
                    event,
                    evidence_refs=[event.get("raw_event_ref")],
                    evidence_detail={"state_id": state_id, "revision_count": revision_count},
                )
            continue

        if event.get("behavior_phase") != "REALIZATION" or event.get("realization_status") != "REALIZED":
            continue
        if event.get("boundary_id") != "FINAL_REOPEN" or event.get("action_type") not in {"revise", "finalize"}:
            continue

        before_id = detail.get("final_state_before_id")
        before_revision = detail.get("final_state_before_revision_count")
        if isinstance(before_id, str) and isinstance(before_revision, int):
            source = latest_version_event.get((before_id, before_revision))
            relation_type = (
                "FINAL_STATE_VERSION_TO_REVISION"
                if event.get("action_type") == "revise"
                else "FINAL_STATE_VERSION_TO_FINALIZE"
            )
            add(
                relation_type,
                source,
                event,
                evidence_refs=[event.get("raw_event_ref")],
                evidence_detail={"state_id": before_id, "revision_count": before_revision},
            )

        after_id = detail.get("final_state_after_id")
        after_revision = detail.get("final_state_after_revision_count")
        if isinstance(after_id, str) and isinstance(after_revision, int):
            latest_version_event[(after_id, after_revision)] = event

    relations.sort(key=lambda row: (row["source_event_index"], row["target_event_index"], row["relation_type"]))
    return relations


def _descendant_metrics(
    root_event_id: str,
    events: list[Mapping[str, Any]],
    relations: list[Mapping[str, Any]],
    operational_crossings: list[Mapping[str, Any]],
) -> dict[str, Any]:
    by_id = {row["behavior_event_id"]: row for row in events}
    adjacency: dict[str, list[str]] = defaultdict(list)
    for relation in relations:
        adjacency[relation["source_behavior_event_id"]].append(relation["target_behavior_event_id"])

    depth = {root_event_id: 0}
    ordered_ids = [row["behavior_event_id"] for row in sorted(events, key=lambda row: row["event_index"])]
    for event_id in ordered_ids:
        if event_id not in depth:
            continue
        for target in adjacency.get(event_id, []):
            depth[target] = max(depth.get(target, -1), depth[event_id] + 1)

    descendants = {event_id for event_id, value in depth.items() if value > 0}
    descendant_actors = sorted(
        {
            by_id[event_id].get("actor")
            for event_id in descendants
            if by_id.get(event_id, {}).get("actor") not in (None, "ENVIRONMENT")
        }
    )
    crossing_by_event: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for crossing in operational_crossings:
        crossing_by_event[crossing["behavior_event_id"]].append(crossing)
    reached_crossings = [
        crossing
        for event_id in descendants
        for crossing in crossing_by_event.get(event_id, [])
    ]
    root_crossings = crossing_by_event.get(root_event_id, [])
    crossing_depths = [depth[crossing["behavior_event_id"]] for crossing in reached_crossings]
    if root_crossings:
        crossing_depths.append(0)
    authority_classes = sorted(
        {
            crossing.get("authority_class")
            for crossing in [*root_crossings, *reached_crossings]
            if crossing.get("authority_class")
        }
    )
    descendant_relation_count = sum(
        1
        for relation in relations
        if relation["source_behavior_event_id"] in depth
        and relation["target_behavior_event_id"] in descendants
    )
    return {
        "root_behavior_event_id": root_event_id,
        "descendant_event_count": len(descendants),
        "descendant_behavior_event_ids": sorted(
            descendants, key=lambda event_id: by_id[event_id]["event_index"]
        ),
        "descendant_relation_count": descendant_relation_count,
        "affected_agent_count": len(descendant_actors),
        "affected_agent_ids": descendant_actors,
        "root_is_operational_crossing": bool(root_crossings),
        "downstream_operational_crossing_count": len(reached_crossings),
        "operational_authority_classes_reached": authority_classes,
        "mechanical_penetration_depth_candidate": max(crossing_depths) if crossing_depths else None,
        "penetration_depth_candidate_status": (
            "STRUCTURAL_LINEAGE_AND_OPERATIONAL_CROSSING_ONLY_NOT_AUTHORITY_ADJUDICATED"
            if crossing_depths
            else "NO_OPERATIONAL_CROSSING_REACHED"
        ),
        "semantic_adoption_status": NOT_ADJUDICATED,
        "authority_penetration_status": NOT_ADJUDICATED,
    }


def build_system_lineage_view(
    adapter_result: Mapping[str, Any],
    *,
    dynamics_view: Mapping[str, Any] | None = None,
    lineage_rules: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    _require(isinstance(adapter_result, Mapping), "adapter_result_required")
    all_events = adapter_result.get("behavior_events")
    _require(isinstance(all_events, list), "adapter_behavior_events_required")
    dynamics = dict(dynamics_view or build_system_dynamics_view(adapter_result))
    slicing = dynamics.get("behavior_slice") or {"mode": "FULL_TRAJECTORY"}
    if slicing.get("mode") == "BRANCH_CONTINUATION_ONLY":
        branch_start_turn = slicing.get("branch_start_turn")
        effective_events = slice_behavior_events_for_branch(all_events, branch_start_turn=branch_start_turn)
    else:
        effective_events = [dict(row) for row in all_events]

    rules_cfg = dict(lineage_rules or load_lineage_rules())
    validate_lineage_rules(rules_cfg)
    rules_hash = content_hash(rules_cfg)
    relations = derive_source_backed_lineage(effective_events, rules_cfg)
    crossings = list(dynamics.get("operational_crossings") or [])
    candidates = list(dynamics.get("jump_candidates") or [])

    candidate_metrics = []
    for candidate in candidates:
        root_id = candidate["behavior_event_id"]
        if not any(row["behavior_event_id"] == root_id for row in effective_events):
            continue
        metrics = _descendant_metrics(root_id, effective_events, relations, crossings)
        metrics["jump_candidate_id"] = candidate["candidate_id"]
        candidate_metrics.append(metrics)

    relation_type_counts = Counter(row["relation_type"] for row in relations)
    first_metrics = candidate_metrics[0] if candidate_metrics else None

    measurement = copy.deepcopy(dynamics["system_trajectory_measurement"])
    measurement["r3"].update(
        {
            "descendant_event_count": first_metrics["descendant_event_count"] if first_metrics else 0,
            "affected_agent_count": first_metrics["affected_agent_count"] if first_metrics else 0,
            "affected_agent_ids": first_metrics["affected_agent_ids"] if first_metrics else [],
            "descendant_relation_count": first_metrics["descendant_relation_count"] if first_metrics else 0,
            "first_jump_downstream_operational_crossing_count": (
                first_metrics["downstream_operational_crossing_count"] if first_metrics else 0
            ),
            "first_jump_mechanical_penetration_depth_candidate": (
                first_metrics["mechanical_penetration_depth_candidate"] if first_metrics else None
            ),
            "first_jump_operational_authority_classes_reached": (
                first_metrics["operational_authority_classes_reached"] if first_metrics else []
            ),
            "lineage_status": "SOURCE_BACKED_STRUCTURAL_LINEAGE_v0.1",
            "penetration_status": NOT_ADJUDICATED,
            "warning": (
                "Descendants are source-backed structural lineage under v0.1 rules. "
                "Mechanical penetration depth is a candidate based on lineage plus operational crossings; "
                "semantic adoption and Authority Penetration remain unadjudicated."
            ),
        }
    )
    measurement["lineage_binding"] = {
        "schema": rules_cfg["schema"],
        "version": rules_cfg["version"],
        "hash": rules_hash,
    }
    measurement["measurement_hash"] = content_hash(
        {key: value for key, value in measurement.items() if key != "measurement_hash"}
    )

    view = {
        "schema": LINEAGE_VIEW_SCHEMA,
        "trajectory_id": measurement.get("trajectory_id"),
        "source_trace_hash": dynamics.get("source_trace_hash"),
        "adapter_output_hash": dynamics.get("adapter_output_hash"),
        "behavior_slice": slicing,
        "lineage_binding": measurement["lineage_binding"],
        "lineage_relation_count": len(relations),
        "lineage_relation_type_counts": dict(sorted(relation_type_counts.items())),
        "lineage_relations": relations,
        "jump_candidate_lineage_metrics": candidate_metrics,
        "system_trajectory_measurement": measurement,
        "semantic_status": NOT_ADJUDICATED,
        "scientific_status": "OFFLINE_SOURCE_BACKED_STRUCTURAL_LINEAGE_ONLY",
    }
    view["lineage_view_hash"] = content_hash(view)
    return view
