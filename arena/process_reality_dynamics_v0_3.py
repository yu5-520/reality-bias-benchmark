from __future__ import annotations

from collections import Counter, defaultdict, deque
from typing import Any, Mapping

from .process_reality_dynamics_v0_2 import resolve_source_jump_root
from .system_behavior import content_hash

MEASUREMENT_SCHEMA = "RB-PROCESS-REALITY-MECHANISM-MEASUREMENT-v0.3"
COMPARISON_SCHEMA = "RB-PROCESS-REALITY-PAIRED-COMPARISON-v0.3"


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


def canonical_target_ref(event: Mapping[str, Any]) -> str:
    """Return a run-ID/event-ID/turn-ID independent structural target.

    Keep stable semantic interface keys (shared-state key, target Agent role) but
    collapse per-run message/invocation/final-state/turn identifiers.
    """
    boundary = str(event.get("boundary_id") or "-")
    action = str(event.get("action_type") or "-")
    diff = event.get("structured_diff") or {}
    target = event.get("target_ref")

    if boundary == "SHARED_STATE":
        if isinstance(target, str) and target.startswith("shared_state:"):
            return target
        key = diff.get("action_key") or diff.get("state_key")
        return f"shared_state:{key}" if key else "shared_state"

    if boundary == "MESSAGE_HANDOFF":
        recipient = diff.get("action_to") or diff.get("recipient")
        return f"message_to:{recipient}" if recipient else "message"

    if boundary == "INVOCATION":
        agent = diff.get("action_agent_id") or diff.get("target")
        return f"agent:{agent}" if agent else "invocation"

    if boundary == "FINAL_REOPEN":
        return "final_state"

    if boundary == "AGENT_TURN":
        return "agent_turn"

    if isinstance(target, str):
        if target.startswith("shared_state:") or target.startswith("agent:"):
            return target
        if target.startswith("message:"):
            return "message"
        if target.startswith("invocation:"):
            return "invocation"
        if target.startswith("turn:"):
            return "agent_turn"
        if "FINAL" in target.upper() or "final_state" in target.lower():
            return "final_state"
        return "opaque_target"
    return "-"


def canonical_event_signature(event: Mapping[str, Any]) -> str:
    diff = event.get("structured_diff") or {}
    phase = diff.get("behavior_phase") or "-"
    status = event.get("realization_status") or "-"
    parts = (
        event.get("actor") or "UNKNOWN",
        event.get("boundary_id") or "-",
        event.get("action_type") or "-",
        phase,
        status,
        canonical_target_ref(event),
    )
    return "|".join(str(x) for x in parts)


def canonical_relation_signature(relation: Mapping[str, Any], by_id: Mapping[str, Mapping[str, Any]]) -> str | None:
    sid = relation.get("source_behavior_event_id")
    tid = relation.get("target_behavior_event_id")
    if sid not in by_id or tid not in by_id:
        return None
    return (
        canonical_event_signature(by_id[sid])
        + "=>"
        + str(relation.get("relation_type") or "LINEAGE")
        + "=>"
        + canonical_event_signature(by_id[tid])
    )


def _edge_multiset(relations, by_id):
    counter = Counter()
    for relation in relations:
        signature = canonical_relation_signature(relation, by_id)
        if signature:
            counter[signature] += 1
    return dict(sorted(counter.items()))


def _cross_actor_count(relations, by_id):
    count = 0
    for relation in relations:
        sid = relation.get("source_behavior_event_id")
        tid = relation.get("target_behavior_event_id")
        if sid not in by_id or tid not in by_id:
            continue
        left = by_id[sid].get("actor")
        right = by_id[tid].get("actor")
        if left != right and left not in (None, "ENVIRONMENT") and right not in (None, "ENVIRONMENT"):
            count += 1
    return count


def _multiset_weighted_jaccard(left: Mapping[str, int], right: Mapping[str, int]) -> float:
    keys = set(left) | set(right)
    if not keys:
        return 1.0
    numerator = sum(min(int(left.get(k, 0)), int(right.get(k, 0))) for k in keys)
    denominator = sum(max(int(left.get(k, 0)), int(right.get(k, 0))) for k in keys)
    return numerator / denominator if denominator else 1.0


def build_process_reality_measurement(
    *,
    trace,
    adapter_result,
    dynamics_view,
    lineage_view,
    target_source_event_index,
    branch_start_turn,
    target_state_key=None,
    target_candidate_id=None,
):
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

    post_events = [x for x in events if int(x.get("turn", -1)) > int(branch_start_turn)]
    post_ids = {x["behavior_event_id"] for x in post_events}
    post_relations = [
        x for x in relations
        if x.get("source_behavior_event_id") in post_ids and x.get("target_behavior_event_id") in post_ids
    ]
    jumps = [x for x in dynamics_view.get("jump_candidates") or [] if int(x.get("turn", -1)) > int(branch_start_turn)]

    if depth is None:
        descendant_jumps = None
        independent_jumps = None
        all_descendant_ids = None
        continuation_descendant_ids = None
        root_continuation_relations = None
        affected = None
    else:
        all_descendant_ids = {eid for eid in depth if eid != root["behavior_event_id"]}
        continuation_descendant_ids = {
            eid for eid in all_descendant_ids
            if eid in by_id and int(by_id[eid].get("turn", -1)) > int(branch_start_turn)
        }
        root_continuation_relations = [
            x for x in relations
            if x.get("source_behavior_event_id") in depth
            and x.get("target_behavior_event_id") in continuation_descendant_ids
        ]
        descendant_jumps = [x for x in jumps if x.get("behavior_event_id") in continuation_descendant_ids]
        independent_jumps = [x for x in jumps if x.get("behavior_event_id") not in depth]
        affected = sorted({
            by_id[eid].get("actor") for eid in continuation_descendant_ids
            if by_id[eid].get("actor") not in (None, "ENVIRONMENT")
        })

    root_resolution = {
        "status": resolution["status"],
        "source_event_ref": resolution["source_event_ref"],
        "target_state_key": target_state_key,
        "candidate_count": resolution["candidate_count"],
        "candidate_behavior_event_ids": resolution.get("candidate_behavior_event_ids", []),
    }
    if root:
        root_resolution.update({
            "resolved_behavior_event_id": root["behavior_event_id"],
            "resolved_behavior_event_index": root.get("event_index"),
            "resolved_behavior_event_source_refs": list(root.get("source_refs") or []),
        })

    full_post_multiset = _edge_multiset(post_relations, by_id)
    full_post_ordered = [
        canonical_event_signature(x)
        for x in sorted(post_events, key=lambda x: (x.get("event_index", 0), str(x.get("behavior_phase") or "")))
    ]

    if continuation_descendant_ids is None:
        root_multiset = None
        root_ordered = None
        root_cross_actor = None
        full_reachable_count = None
        continuation_reachable_count = None
        continuation_reach_depth = None
    else:
        root_multiset = _edge_multiset(root_continuation_relations, by_id)
        root_ordered = [
            canonical_event_signature(by_id[eid])
            for eid in sorted(continuation_descendant_ids, key=lambda eid: int(by_id[eid].get("event_index", 0)))
        ]
        root_cross_actor = _cross_actor_count(root_continuation_relations, by_id)
        full_reachable_count = len(all_descendant_ids)
        continuation_reachable_count = len(continuation_descendant_ids)
        continuation_reach_depth = max((depth[eid] for eid in continuation_descendant_ids), default=0)

    delivery = list(trace.get("runtime_transform_records") or [])
    recovery_candidates = [
        x["behavior_event_id"] for x in post_events
        if x.get("boundary_id") in ("FINAL_REOPEN", "RECOVERY_CHECKPOINT") or x.get("action_type") == "revise"
    ]

    measurement = {
        "schema": MEASUREMENT_SCHEMA,
        "version": "0.3",
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
            "all_root_reachable_event_count": full_reachable_count,
            "continuation_root_reachable_event_count": continuation_reachable_count,
            "continuation_root_reach_depth": continuation_reach_depth,
            "affected_agent_ids": affected,
            "affected_agent_count": len(affected) if affected is not None else None,
            "root_descendant_cross_actor_relation_count": root_cross_actor,
            "semantic_adoption_status": "NOT_ADJUDICATED",
            "semantic_role_or_authority_crossing_status": "NOT_ADJUDICATED",
            "missingness_note": None if root else "ROOT_UNRESOLVED; lineage/inertia is missing, not zero."
        },
        "root_descendant_topology": {
            "canonical_ordered_event_signatures": root_ordered,
            "canonical_edge_multiset": root_multiset,
            "canonical_unique_edge_count": len(root_multiset) if root_multiset is not None else None,
            "canonical_edge_instance_count": sum(root_multiset.values()) if root_multiset is not None else None,
            "edge_multiset_hash": content_hash(root_multiset) if root_multiset is not None else None,
            "ordered_sequence_hash": content_hash(root_ordered) if root_ordered is not None else None,
            "scope": "SELECTED_ROOT_DESCENDANTS_ENTERING_POST_BRANCH_CONTINUATION",
        },
        "full_post_context_topology": {
            "canonical_ordered_event_signatures": full_post_ordered,
            "canonical_edge_multiset": full_post_multiset,
            "canonical_unique_edge_count": len(full_post_multiset),
            "canonical_edge_instance_count": sum(full_post_multiset.values()),
            "cross_actor_relation_count": _cross_actor_count(post_relations, by_id),
            "edge_multiset_hash": content_hash(full_post_multiset),
            "ordered_sequence_hash": content_hash(full_post_ordered),
            "scope": "ALL_POST_BRANCH_ACTIVITY_CONTEXT_NOT_INERTIA_BY_DEFINITION",
        },
        "r6_recovery": {
            "candidate_event_refs": recovery_candidates,
            "semantic_recovery_status": "NOT_ADJUDICATED"
        },
        "terminal_outcome": {
            "run_complete": trace.get("run_status") == "RUN_COMPLETE",
            "final_state_present": trace.get("final_state") is not None
        },
        "scientific_warning": (
            "v0.3 separates selected-root descendant topology from all post-branch activity and canonicalizes away run/event/message/invocation/turn identity. "
            "Cross-actor structural relations are not semantic responsibility or authority penetration without review."
        ),
    }
    measurement["measurement_hash"] = content_hash(measurement)
    return measurement


def _counter(value):
    return Counter({str(k): int(v) for k, v in (value or {}).items()})


def _set_jaccard(left, right):
    lset, rset = set(left), set(right)
    union = lset | rset
    return len(lset & rset) / len(union) if union else 1.0


def compare_process_reality(control: Mapping[str, Any], intervention: Mapping[str, Any], *, comparison_id: str):
    c_root = _counter((control.get("root_descendant_topology") or {}).get("canonical_edge_multiset"))
    i_root = _counter((intervention.get("root_descendant_topology") or {}).get("canonical_edge_multiset"))
    c_full = _counter((control.get("full_post_context_topology") or {}).get("canonical_edge_multiset"))
    i_full = _counter((intervention.get("full_post_context_topology") or {}).get("canonical_edge_multiset"))
    c_order = list((control.get("root_descendant_topology") or {}).get("canonical_ordered_event_signatures") or [])
    i_order = list((intervention.get("root_descendant_topology") or {}).get("canonical_ordered_event_signatures") or [])

    prefix = 0
    for left, right in zip(c_order, i_order):
        if left != right:
            break
        prefix += 1

    row = {
        "schema": COMPARISON_SCHEMA,
        "version": "0.3",
        "comparison_id": comparison_id,
        "control_trajectory_id": control.get("trajectory_id"),
        "intervention_trajectory_id": intervention.get("trajectory_id"),
        "root_descendant_topology": {
            "shared_path_prefix_event_count": prefix,
            "first_structural_divergence_index": prefix if prefix < min(len(c_order), len(i_order)) else None,
            "shared_edge_signatures": sorted(set(c_root) & set(i_root)),
            "control_only_edge_signatures": sorted(set(c_root) - set(i_root)),
            "intervention_only_edge_signatures": sorted(set(i_root) - set(c_root)),
            "edge_set_jaccard": _set_jaccard(c_root, i_root),
            "edge_multiset_weighted_jaccard": _multiset_weighted_jaccard(c_root, i_root),
        },
        "full_post_context_topology": {
            "edge_set_jaccard": _set_jaccard(c_full, i_full),
            "edge_multiset_weighted_jaccard": _multiset_weighted_jaccard(c_full, i_full),
            "interpretation": "context diagnostic only; not selected-root inertia",
        },
        "jump_recurrence": {
            "control_descendant_rejump_count": (control.get("r2_jump_recurrence") or {}).get("descendant_rejump_count"),
            "intervention_descendant_rejump_count": (intervention.get("r2_jump_recurrence") or {}).get("descendant_rejump_count"),
        },
        "inertia": {
            "control_continuation_root_reach_depth": (control.get("r3_inherited_inertia") or {}).get("continuation_root_reach_depth"),
            "intervention_continuation_root_reach_depth": (intervention.get("r3_inherited_inertia") or {}).get("continuation_root_reach_depth"),
            "control_continuation_root_reachable_event_count": (control.get("r3_inherited_inertia") or {}).get("continuation_root_reachable_event_count"),
            "intervention_continuation_root_reachable_event_count": (intervention.get("r3_inherited_inertia") or {}).get("continuation_root_reachable_event_count"),
            "control_affected_agent_count": (control.get("r3_inherited_inertia") or {}).get("affected_agent_count"),
            "intervention_affected_agent_count": (intervention.get("r3_inherited_inertia") or {}).get("affected_agent_count"),
            "control_root_descendant_cross_actor_relation_count": (control.get("r3_inherited_inertia") or {}).get("root_descendant_cross_actor_relation_count"),
            "intervention_root_descendant_cross_actor_relation_count": (intervention.get("r3_inherited_inertia") or {}).get("root_descendant_cross_actor_relation_count"),
        },
        "terminal_outcome_comparison_is_primary": False,
        "semantic_causal_effect_status": "NOT_ADJUDICATED",
        "scientific_status": "PAIRED_ROOT_SCOPED_STRUCTURAL_PROCESS_DIFFERENCE_ONLY",
    }
    row["comparison_hash"] = content_hash(row)
    return row
