from __future__ import annotations

import copy
from collections import defaultdict
from typing import Any, Mapping

from .system_behavior import content_hash


ANCHOR_SCHEMA = "RB-BRANCH-START-STATE-ANCHOR-v0.1"
ANCHOR_VIEW_SCHEMA = "RB-BRANCH-ANCHOR-LINEAGE-v4.0"
NOT_ADJUDICATED = "NOT_ADJUDICATED"


class BranchAnchorLineageV4Error(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BranchAnchorLineageV4Error(message)


def build_branch_start_anchor(
    *,
    trajectory_id: str,
    branch_row: Mapping[str, Any],
    plan: Mapping[str, Any],
    branch_start_snapshot: Mapping[str, Any],
    experimental_variable_id: str,
) -> dict[str, Any]:
    common = plan.get("common_identity") or {}
    state_key = common.get("state_key")
    _require(isinstance(state_key, str) and state_key, "branch_anchor_state_key_required")
    state = branch_start_snapshot.get("shared_state") or {}
    metadata = branch_start_snapshot.get("shared_state_metadata") or {}
    _require(state_key in state, "branch_anchor_state_value_missing")
    meta = metadata.get(state_key)
    _require(isinstance(meta, Mapping), "branch_anchor_state_metadata_missing")
    source_event_index = meta.get("event_index")
    _require(isinstance(source_event_index, int) and source_event_index >= 0, "branch_anchor_source_event_index_required")
    status = meta.get("status")
    _require(isinstance(status, str) and status, "branch_anchor_status_required")
    _require(branch_row.get("run_id") == trajectory_id, "branch_anchor_trajectory_row_mismatch")
    _require(branch_row.get("branch_start_state_hash") == branch_start_snapshot.get("state_hash"), "branch_anchor_start_state_hash_mismatch")

    anchor = {
        "schema": ANCHOR_SCHEMA,
        "version": "0.1",
        "trajectory_id": trajectory_id,
        "branch_id": branch_row.get("branch_id"),
        "pair_id": branch_row.get("pair_id"),
        "replicate_index": branch_row.get("replicate_index"),
        "condition_id": branch_row.get("condition_id"),
        "parent_state_hash": branch_row.get("parent_state_hash"),
        "branch_start_state_hash": branch_row.get("branch_start_state_hash"),
        "source_selection_record_hash": branch_row.get("source_selection_record_hash"),
        "selected_candidate_id": common.get("selected_candidate_id"),
        "selected_candidate_event_ref": common.get("selected_candidate_event_ref"),
        "state_key": state_key,
        "state_value_hash": content_hash(state.get(state_key)),
        "state_status": status,
        "source_event_index": source_event_index,
        "writer": meta.get("writer"),
        "experimental_variable_id": experimental_variable_id,
        "semantic_status": NOT_ADJUDICATED,
        "scientific_status": "FROZEN_BRANCH_START_STATE_OBSERVATION",
    }
    anchor["anchor_hash"] = content_hash(anchor)
    return anchor


def _matching_visibility_turns(
    behavior_events: list[Mapping[str, Any]],
    anchor: Mapping[str, Any],
) -> list[dict[str, Any]]:
    out = []
    for event in behavior_events:
        if event.get("boundary_id") != "AGENT_TURN" or event.get("realization_status") != "REALIZED":
            continue
        origins = (event.get("structured_diff") or {}).get("visible_shared_state_origins") or []
        for origin in origins:
            if not isinstance(origin, Mapping):
                continue
            if (
                origin.get("key") == anchor["state_key"]
                and origin.get("source_event_index") == anchor["source_event_index"]
                and origin.get("value_hash") == anchor["state_value_hash"]
                and origin.get("status") == anchor["state_status"]
            ):
                out.append(
                    {
                        "behavior_event_id": event["behavior_event_id"],
                        "event_index": event["event_index"],
                        "turn": event["turn"],
                        "actor": event["actor"],
                        "origin": copy.deepcopy(dict(origin)),
                    }
                )
                break
    out.sort(key=lambda row: row["event_index"])
    return out


def _descendants_from_visibility_roots(
    root_ids: list[str],
    behavior_events: list[Mapping[str, Any]],
    lineage_relations: list[Mapping[str, Any]],
) -> tuple[dict[str, int], list[dict[str, Any]]]:
    event_by_id = {row["behavior_event_id"]: row for row in behavior_events}
    adjacency: dict[str, list[str]] = defaultdict(list)
    for relation in lineage_relations:
        source = relation.get("source_behavior_event_id")
        target = relation.get("target_behavior_event_id")
        if source in event_by_id and target in event_by_id:
            adjacency[source].append(target)

    depth: dict[str, int] = {root_id: 0 for root_id in root_ids if root_id in event_by_id}
    ordered_ids = [row["behavior_event_id"] for row in sorted(behavior_events, key=lambda row: row["event_index"])]
    for event_id in ordered_ids:
        if event_id not in depth:
            continue
        for target in adjacency.get(event_id, []):
            depth[target] = max(depth.get(target, -1), depth[event_id] + 1)

    used_relations = [
        dict(row)
        for row in lineage_relations
        if row.get("source_behavior_event_id") in depth
        and row.get("target_behavior_event_id") in depth
    ]
    return depth, used_relations


def derive_branch_anchor_lineage(
    *,
    adapter_result: Mapping[str, Any],
    dynamics_view: Mapping[str, Any],
    lineage_view: Mapping[str, Any],
    anchor: Mapping[str, Any],
) -> dict[str, Any]:
    behavior_events = [dict(row) for row in adapter_result.get("behavior_events") or []]
    slicing = dynamics_view.get("behavior_slice") or {"mode": "FULL_TRAJECTORY"}
    if slicing.get("mode") == "BRANCH_CONTINUATION_ONLY":
        start_turn = slicing.get("branch_start_turn")
        _require(isinstance(start_turn, int), "branch_anchor_branch_start_turn_required")
        behavior_events = [row for row in behavior_events if int(row.get("turn", -1)) > start_turn]
    _require(dynamics_view.get("trajectory_id") == anchor.get("trajectory_id"), "branch_anchor_dynamics_trajectory_mismatch")
    _require(lineage_view.get("trajectory_id") == anchor.get("trajectory_id"), "branch_anchor_lineage_trajectory_mismatch")

    visibility = _matching_visibility_turns(behavior_events, anchor)
    root_ids = [row["behavior_event_id"] for row in visibility]
    depth, used_relations = _descendants_from_visibility_roots(
        root_ids,
        behavior_events,
        list(lineage_view.get("lineage_relations") or []),
    )
    event_by_id = {row["behavior_event_id"]: row for row in behavior_events}
    descendants = {event_id for event_id, value in depth.items() if value > 0}
    crossings = [
        dict(row)
        for row in dynamics_view.get("operational_crossings") or []
        if row.get("behavior_event_id") in descendants
    ]
    crossing_depths = [depth[row["behavior_event_id"]] for row in crossings if row.get("behavior_event_id") in depth]
    affected_agents = sorted(
        {
            event_by_id[event_id].get("actor")
            for event_id in descendants
            if event_by_id.get(event_id, {}).get("actor") not in (None, "ENVIRONMENT")
        }
    )
    authority_classes = sorted(
        {
            row.get("authority_class")
            for row in crossings
            if row.get("authority_class")
        }
    )

    view = {
        "schema": ANCHOR_VIEW_SCHEMA,
        "version": "4.0",
        "trajectory_id": anchor["trajectory_id"],
        "branch_id": anchor.get("branch_id"),
        "pair_id": anchor.get("pair_id"),
        "condition_id": anchor.get("condition_id"),
        "branch_start_anchor": copy.deepcopy(dict(anchor)),
        "behavior_slice": copy.deepcopy(dict(slicing)),
        "anchor_visible_agent_turn_count": len(visibility),
        "anchor_visible_agent_ids": sorted({row["actor"] for row in visibility}),
        "anchor_visibility_events": visibility,
        "potential_downstream_event_count": len(descendants),
        "potential_downstream_behavior_event_ids": sorted(
            descendants,
            key=lambda event_id: event_by_id[event_id]["event_index"],
        ),
        "potential_downstream_relation_count": len(used_relations),
        "potential_downstream_affected_agent_count": len(affected_agents),
        "potential_downstream_affected_agent_ids": affected_agents,
        "potential_downstream_operational_crossing_count": len(crossings),
        "potential_downstream_operational_crossing_ids": [row["crossing_id"] for row in crossings],
        "potential_downstream_authority_classes_reached": authority_classes,
        "mechanical_anchor_reach_depth_candidate": max(crossing_depths) if crossing_depths else None,
        "semantic_reliance_status": NOT_ADJUDICATED,
        "authority_penetration_status": NOT_ADJUDICATED,
        "causal_effect_status": NOT_ADJUDICATED,
        "scientific_status": "BRANCH_START_EXPOSURE_LINEAGE_CANDIDATE_ONLY",
        "warning": (
            "The branch-start anchor is a frozen state observation, not a reconstructed historical BehaviorEvent. "
            "Exact runtime visibility plus downstream structural lineage establishes potential exposure/reach only; "
            "it does not establish semantic reliance, Authority Penetration, or causal effect."
        ),
    }
    view["anchor_lineage_view_hash"] = content_hash(view)
    return view


def measurement_fields(view: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "branch_start_anchor_hash": (view.get("branch_start_anchor") or {}).get("anchor_hash"),
        "state_key": (view.get("branch_start_anchor") or {}).get("state_key"),
        "state_status": (view.get("branch_start_anchor") or {}).get("state_status"),
        "anchor_visible_agent_turn_count": view.get("anchor_visible_agent_turn_count", 0),
        "anchor_visible_agent_ids": list(view.get("anchor_visible_agent_ids") or []),
        "potential_downstream_event_count": view.get("potential_downstream_event_count", 0),
        "potential_downstream_relation_count": view.get("potential_downstream_relation_count", 0),
        "potential_downstream_affected_agent_count": view.get("potential_downstream_affected_agent_count", 0),
        "potential_downstream_affected_agent_ids": list(view.get("potential_downstream_affected_agent_ids") or []),
        "potential_downstream_operational_crossing_count": view.get("potential_downstream_operational_crossing_count", 0),
        "potential_downstream_authority_classes_reached": list(view.get("potential_downstream_authority_classes_reached") or []),
        "mechanical_anchor_reach_depth_candidate": view.get("mechanical_anchor_reach_depth_candidate"),
        "semantic_reliance_status": NOT_ADJUDICATED,
        "authority_penetration_status": NOT_ADJUDICATED,
        "causal_effect_status": NOT_ADJUDICATED,
        "warning": view.get("warning"),
    }
