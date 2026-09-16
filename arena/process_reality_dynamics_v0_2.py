from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Mapping

from .system_behavior import content_hash

MEASUREMENT_SCHEMA = "RB-PROCESS-REALITY-MECHANISM-MEASUREMENT-v0.2"
COMPARISON_SCHEMA = "RB-PROCESS-REALITY-PAIRED-COMPARISON-v0.2"


def _sig(event: Mapping[str, Any]) -> str:
    diff = event.get("structured_diff") or {}
    target = event.get("target_ref") or diff.get("action_key") or diff.get("state_key") or "-"
    return "|".join(str(x) for x in (event.get("actor"), event.get("boundary_id"), event.get("action_type"), target))


def _adjacency(relations):
    out = defaultdict(list)
    for row in relations:
        source = row.get("source_behavior_event_id")
        target = row.get("target_behavior_event_id")
        if source and target:
            out[source].append((target, row.get("relation_type") or "LINEAGE"))
    return out


def _reachable(root_id, relations):
    adj = _adjacency(relations)
    depth = {root_id: 0}
    q = deque([root_id])
    while q:
        current = q.popleft()
        for target, _ in adj.get(current, []):
            if target not in depth:
                depth[target] = depth[current] + 1
                q.append(target)
    return depth


def resolve_source_jump_root(*, adapter_result, target_source_event_index: int, target_state_key: str | None = None):
    """Resolve a selected Arena event to its realized BehaviorEvent.

    BehaviorEvent.event_index is a derived, re-numbered index.  A frozen natural
    anchor instead refers to the source Arena event index, which the adapter
    preserves as source_refs=["arena_event:<n>"] and structured_diff.source_event_index.
    Never bind these two index spaces by numeric equality.
    """
    events = list(adapter_result.get("behavior_events") or [])
    source_ref = f"arena_event:{int(target_source_event_index)}"
    target_ref = f"shared_state:{target_state_key}" if target_state_key else None
    matches = []
    for event in events:
        if event.get("realization_status") != "REALIZED":
            continue
        if event.get("action_type") != "write":
            continue
        refs = event.get("source_refs") or []
        diff = event.get("structured_diff") or {}
        source_index_matches = source_ref in refs or diff.get("source_event_index") == target_source_event_index
        if not source_index_matches:
            continue
        if target_ref is not None and event.get("target_ref") != target_ref:
            continue
        matches.append(event)
    if len(matches) == 1:
        return {
            "status": "RESOLVED_EXACT_SOURCE_EVENT",
            "source_event_ref": source_ref,
            "target_state_key": target_state_key,
            "candidate_count": 1,
            "behavior_event": matches[0],
        }
    return {
        "status": "ROOT_UNRESOLVED" if not matches else "ROOT_AMBIGUOUS",
        "source_event_ref": source_ref,
        "target_state_key": target_state_key,
        "candidate_count": len(matches),
        "candidate_behavior_event_ids": [x.get("behavior_event_id") for x in matches],
        "behavior_event": None,
    }


def build_process_reality_measurement(*, trace, adapter_result, dynamics_view, lineage_view, target_source_event_index, branch_start_turn, target_state_key=None, target_candidate_id=None):
    events = list(adapter_result.get("behavior_events") or [])
    by_id = {x["behavior_event_id"]: x for x in events}
    resolution = resolve_source_jump_root(
        adapter_result=adapter_result,
        target_source_event_index=target_source_event_index,
        target_state_key=target_state_key,
    )
    root = resolution.get("behavior_event")
    relations = list(lineage_view.get("lineage_relations") or [])
    depth = _reachable(root["behavior_event_id"], relations) if root else None
    post = [x for x in events if int(x.get("turn", -1)) > int(branch_start_turn)]
    post_ids = {x["behavior_event_id"] for x in post}
    jumps = [x for x in dynamics_view.get("jump_candidates") or [] if int(x.get("turn", -1)) > int(branch_start_turn)]

    if depth is None:
        descendant_jumps = None
        independent_jumps = None
        affected = None
    else:
        descendant_jumps = [x for x in jumps if x.get("behavior_event_id") in depth]
        independent_jumps = [x for x in jumps if x.get("behavior_event_id") not in depth]
        affected = sorted({
            by_id[eid].get("actor") for eid in depth
            if eid in by_id
            and eid != root.get("behavior_event_id")
            and by_id[eid].get("actor") not in (None, "ENVIRONMENT")
        })

    edge_signatures = []
    role_crossings = 0
    for row in relations:
        sid = row.get("source_behavior_event_id")
        tid = row.get("target_behavior_event_id")
        if sid not in post_ids or tid not in post_ids or sid not in by_id or tid not in by_id:
            continue
        left, right = by_id[sid], by_id[tid]
        edge_signatures.append(f"{_sig(left)}=>{row.get('relation_type')}=>{_sig(right)}")
        if left.get("actor") != right.get("actor") and left.get("actor") not in (None, "ENVIRONMENT") and right.get("actor") not in (None, "ENVIRONMENT"):
            role_crossings += 1
    ordered = [_sig(x) for x in sorted(post, key=lambda x: (x.get("event_index", 0), x.get("behavior_phase", "")))]
    delivery = list(trace.get("runtime_transform_records") or [])

    root_resolution = {
        "status": resolution["status"],
        "source_event_ref": resolution["source_event_ref"],
        "target_state_key": target_state_key,
        "candidate_count": resolution["candidate_count"],
        "candidate_behavior_event_ids": resolution.get("candidate_behavior_event_ids", []),
    }
    if root:
        root_resolution["resolved_behavior_event_id"] = root["behavior_event_id"]
        root_resolution["resolved_behavior_event_index"] = root.get("event_index")
        root_resolution["resolved_behavior_event_source_refs"] = list(root.get("source_refs") or [])

    measurement = {
        "schema": MEASUREMENT_SCHEMA,
        "version": "0.2",
        "trajectory_id": trace.get("run_id"),
        "run_status": trace.get("run_status"),
        "target_candidate_id": target_candidate_id,
        "target_source_event_index": target_source_event_index,
        "target_state_key": target_state_key,
        "target_root_behavior_event_id": root.get("behavior_event_id") if root else None,
        "root_resolution": root_resolution,
        "mechanism_measurement_status": "ROOT_RESOLVED" if root else "ROOT_UNRESOLVED_NO_ZERO_IMPUTATION",
        "branch_start_turn": branch_start_turn,
        "direct_experiment_origin_exposure_count": len([x for x in delivery if x.get("experiment_origin") is True]),
        "r2_jump_recurrence": {
            "descendant_rejump_count": len(descendant_jumps) if descendant_jumps is not None else None,
            "descendant_rejump_refs": [x.get("candidate_id") for x in descendant_jumps] if descendant_jumps is not None else None,
            "independent_new_jump_count": len(independent_jumps) if independent_jumps is not None else None,
            "independent_new_jump_refs": [x.get("candidate_id") for x in independent_jumps] if independent_jumps is not None else None,
            "first_descendant_rejump_depth": min((depth[x["behavior_event_id"]] for x in descendant_jumps), default=None) if descendant_jumps is not None else None,
            "semantic_cpr_status": "NOT_ADJUDICATED",
            "missingness_note": None if root else "ROOT_UNRESOLVED; recurrence is missing, not zero."
        },
        "r3_inherited_inertia": {
            "root_reachable_event_count": max(0, len(depth) - 1) if depth is not None else None,
            "root_reach_depth": max(depth.values(), default=0) if depth is not None else None,
            "affected_agent_ids": affected,
            "affected_agent_count": len(affected) if affected is not None else None,
            "role_crossing_count": role_crossings,
            "semantic_adoption_status": "NOT_ADJUDICATED",
            "missingness_note": None if root else "ROOT_UNRESOLVED; lineage/inertia is missing, not zero."
        },
        "path_topology": {
            "ordered_event_signatures": ordered,
            "canonical_edge_signatures": sorted(set(edge_signatures)),
            "canonical_edge_count": len(set(edge_signatures))
        },
        "r6_recovery": {
            "candidate_event_refs": [x["behavior_event_id"] for x in post if x.get("boundary_id") in ("FINAL_REOPEN", "RECOVERY_CHECKPOINT") or x.get("action_type") == "revise"],
            "semantic_recovery_status": "NOT_ADJUDICATED"
        },
        "terminal_outcome": {
            "run_complete": trace.get("run_status") == "RUN_COMPLETE",
            "final_state_present": trace.get("final_state") is not None
        },
        "scientific_warning": "Source Arena event index and derived BehaviorEvent index are distinct namespaces. v0.2 binds roots only through preserved source references / source_event_index plus the selected state key."
    }
    measurement["measurement_hash"] = content_hash(measurement)
    return measurement


def compare_process_reality(control: Mapping[str, Any], intervention: Mapping[str, Any], *, comparison_id: str):
    c_edges = set((control.get("path_topology") or {}).get("canonical_edge_signatures") or [])
    i_edges = set((intervention.get("path_topology") or {}).get("canonical_edge_signatures") or [])
    c_order = list((control.get("path_topology") or {}).get("ordered_event_signatures") or [])
    i_order = list((intervention.get("path_topology") or {}).get("ordered_event_signatures") or [])
    prefix = 0
    for left, right in zip(c_order, i_order):
        if left != right:
            break
        prefix += 1
    union = c_edges | i_edges
    shared = c_edges & i_edges
    row = {
        "schema": COMPARISON_SCHEMA,
        "version": "0.2",
        "comparison_id": comparison_id,
        "control_trajectory_id": control.get("trajectory_id"),
        "intervention_trajectory_id": intervention.get("trajectory_id"),
        "shared_path_prefix_event_count": prefix,
        "first_structural_divergence_index": prefix if prefix < min(len(c_order), len(i_order)) else None,
        "shared_edge_signatures": sorted(shared),
        "control_only_edge_signatures": sorted(c_edges - i_edges),
        "intervention_only_edge_signatures": sorted(i_edges - c_edges),
        "topology_edge_jaccard": (len(shared) / len(union)) if union else 1.0,
        "jump_recurrence": {
            "control_descendant_rejump_count": (control.get("r2_jump_recurrence") or {}).get("descendant_rejump_count"),
            "intervention_descendant_rejump_count": (intervention.get("r2_jump_recurrence") or {}).get("descendant_rejump_count")
        },
        "inertia": {
            "control_root_reach_depth": (control.get("r3_inherited_inertia") or {}).get("root_reach_depth"),
            "intervention_root_reach_depth": (intervention.get("r3_inherited_inertia") or {}).get("root_reach_depth"),
            "control_affected_agent_count": (control.get("r3_inherited_inertia") or {}).get("affected_agent_count"),
            "intervention_affected_agent_count": (intervention.get("r3_inherited_inertia") or {}).get("affected_agent_count")
        },
        "terminal_outcome_comparison_is_primary": False,
        "semantic_causal_effect_status": "NOT_ADJUDICATED",
        "scientific_status": "PAIRED_STRUCTURAL_PROCESS_DIFFERENCE_ONLY"
    }
    row["comparison_hash"] = content_hash(row)
    return row
