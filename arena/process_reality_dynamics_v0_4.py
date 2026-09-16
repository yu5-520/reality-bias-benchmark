from __future__ import annotations

from collections import Counter, defaultdict, deque
from typing import Any, Mapping

from .process_reality_dynamics_v0_2 import resolve_source_jump_root
from .system_behavior import content_hash

MEASUREMENT_SCHEMA = "RB-PROCESS-REALITY-MECHANISM-MEASUREMENT-v0.4"
COMPARISON_SCHEMA = "RB-PROCESS-REALITY-PAIRED-COMPARISON-v0.4"
PATH_FAMILY_CAP = 4096


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
    boundary = str(event.get("boundary_id") or "-")
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
    phase = event.get("behavior_phase") or diff.get("behavior_phase") or "-"
    status = event.get("realization_status") or "-"
    return "|".join(str(x) for x in (
        event.get("actor") or "UNKNOWN",
        event.get("boundary_id") or "-",
        event.get("action_type") or "-",
        phase,
        status,
        canonical_target_ref(event),
    ))


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


def _degree_metrics(node_ids, relations):
    indegree = Counter()
    outdegree = Counter()
    for row in relations:
        sid = row.get("source_behavior_event_id")
        tid = row.get("target_behavior_event_id")
        if sid in node_ids and tid in node_ids:
            outdegree[sid] += 1
            indegree[tid] += 1
    branch_nodes = sorted(x for x in node_ids if outdegree[x] > 1)
    merge_nodes = sorted(x for x in node_ids if indegree[x] > 1)
    return {
        "branch_node_count": len(branch_nodes),
        "merge_node_count": len(merge_nodes),
        "branch_node_ids": branch_nodes,
        "merge_node_ids": merge_nodes,
        "max_outdegree": max((outdegree[x] for x in node_ids), default=0),
        "max_indegree": max((indegree[x] for x in node_ids), default=0),
    }


def _actor_reentry(events):
    ordered = [x for x in sorted(events, key=lambda x: int(x.get("event_index", 0))) if x.get("actor") not in (None, "ENVIRONMENT")]
    compressed = []
    for event in ordered:
        actor = event.get("actor")
        if not compressed or compressed[-1]["actor"] != actor:
            compressed.append({
                "actor": actor,
                "event_index": event.get("event_index"),
                "turn": event.get("turn"),
                "behavior_event_id": event.get("behavior_event_id"),
            })
    seen = set()
    reentries = []
    for row in compressed:
        actor = row["actor"]
        if actor in seen:
            reentries.append(row)
        else:
            seen.add(actor)
    return {
        "compressed_actor_sequence": [x["actor"] for x in compressed],
        "role_reentry_count": len(reentries),
        "role_reentry_records": reentries,
        "semantic_loop_status": "NOT_ADJUDICATED",
    }


def _enumerate_path_families(root_id, node_ids, relations, by_id, cap=PATH_FAMILY_CAP):
    adjacency = defaultdict(list)
    for row in relations:
        sid = row.get("source_behavior_event_id")
        tid = row.get("target_behavior_event_id")
        if sid in node_ids and tid in node_ids:
            adjacency[sid].append((tid, str(row.get("relation_type") or "LINEAGE")))
    for sid in adjacency:
        adjacency[sid].sort(key=lambda x: (int(by_id[x[0]].get("event_index", 0)), x[1], x[0]))

    signatures = []
    overflow = False

    def walk(node_id, tokens):
        nonlocal overflow
        if overflow:
            return
        edges = adjacency.get(node_id, [])
        if not edges:
            signatures.append("=>".join(tokens))
            if len(signatures) >= cap:
                overflow = True
            return
        for target_id, relation_type in edges:
            if overflow:
                return
            walk(target_id, tokens + [relation_type, canonical_event_signature(by_id[target_id])])

    if root_id in node_ids:
        walk(root_id, [canonical_event_signature(by_id[root_id])])
    unique = sorted(set(signatures))
    return {
        "observed_path_family_signatures": unique,
        "observed_path_family_count": len(unique),
        "path_family_cap": cap,
        "path_family_overflow": overflow,
        "path_family_hash": content_hash(unique),
        "interpretation": "Source-backed realized lineage path families only; not an exhaustive counterfactual possibility space.",
    }


def _delivery_keys(trace):
    records = [x for x in trace.get("runtime_transform_records") or [] if x.get("experiment_origin") is True]
    return {(x.get("actor"), x.get("turn")) for x in records}


def _jump_classification(*, jumps, depth, delivery_keys, by_id):
    rows = []
    for jump in sorted(jumps, key=lambda x: int(x.get("event_index", 0))):
        eid = jump.get("behavior_event_id")
        if depth is None:
            lineage_class = "LINEAGE_UNRESOLVED"
            lineage_depth = None
        elif eid in depth:
            lineage_class = "DESCENDANT_REJUMP"
            lineage_depth = depth[eid]
        else:
            lineage_class = "INDEPENDENT_NEW_JUMP"
            lineage_depth = None
        event = by_id.get(eid) or {}
        rows.append({
            "candidate_id": jump.get("candidate_id"),
            "behavior_event_id": eid,
            "event_index": jump.get("event_index"),
            "turn": jump.get("turn"),
            "actor": jump.get("actor"),
            "boundary_id": jump.get("boundary_id"),
            "candidate_types": list(jump.get("candidate_types") or []),
            "lineage_class": lineage_class,
            "lineage_depth": lineage_depth,
            "direct_experiment_exposure": (event.get("actor"), event.get("turn")) in delivery_keys,
        })
    return rows


def _first_rejump_detail(*, classification, root, root_candidate_types):
    descendants = [x for x in classification if x["lineage_class"] == "DESCENDANT_REJUMP"]
    if not descendants:
        return None
    first = min(descendants, key=lambda x: int(x.get("event_index", 10**18)))
    first_types = set(first.get("candidate_types") or [])
    root_types = set(root_candidate_types or [])
    return {
        "candidate_id": first.get("candidate_id"),
        "behavior_event_id": first.get("behavior_event_id"),
        "actor": first.get("actor"),
        "boundary_id": first.get("boundary_id"),
        "lineage_depth": first.get("lineage_depth"),
        "event_distance": int(first.get("event_index")) - int(root.get("event_index")),
        "turn_distance": int(first.get("turn")) - int(root.get("turn")),
        "actor_changed_from_root": first.get("actor") != root.get("actor"),
        "boundary_changed_from_root": first.get("boundary_id") != root.get("boundary_id"),
        "root_candidate_types": sorted(root_types),
        "first_rejump_candidate_types": sorted(first_types),
        "candidate_type_overlap": sorted(root_types & first_types),
        "candidate_family_continuity": bool(root_types & first_types) if root_types else None,
        "direct_experiment_exposure": first.get("direct_experiment_exposure"),
    }


def _multiset_weighted_jaccard(left: Mapping[str, int], right: Mapping[str, int]) -> float:
    keys = set(left) | set(right)
    if not keys:
        return 1.0
    numerator = sum(min(int(left.get(k, 0)), int(right.get(k, 0))) for k in keys)
    denominator = sum(max(int(left.get(k, 0)), int(right.get(k, 0))) for k in keys)
    return numerator / denominator if denominator else 1.0


def _multiset_survival(source: Mapping[str, int], other: Mapping[str, int]) -> float | None:
    total = sum(int(v) for v in source.values())
    if total == 0:
        return None
    shared = sum(min(int(source.get(k, 0)), int(other.get(k, 0))) for k in source)
    return shared / total


def _set_jaccard(left, right):
    lset, rset = set(left), set(right)
    union = lset | rset
    return len(lset & rset) / len(union) if union else 1.0


def _first_reconvergence(control_order, intervention_order, prefix):
    if prefix >= len(control_order) or prefix >= len(intervention_order):
        return None
    candidates = []
    positions = defaultdict(list)
    for j in range(prefix, len(intervention_order)):
        positions[intervention_order[j]].append(j)
    for i in range(prefix, len(control_order)):
        for j in positions.get(control_order[i], []):
            if i == prefix and j == prefix:
                continue
            candidates.append((max(i, j), i + j, i, j, control_order[i]))
    if not candidates:
        return None
    _, _, i, j, signature = min(candidates)
    return {
        "canonical_event_signature": signature,
        "control_index": i,
        "intervention_index": j,
        "control_distance_after_divergence": i - prefix,
        "intervention_distance_after_divergence": j - prefix,
        "interpretation": "First shared canonical event signature after the prefix divergence; structural signature reconvergence, not full-state equality.",
    }


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
    post_relations = [x for x in relations if x.get("source_behavior_event_id") in post_ids and x.get("target_behavior_event_id") in post_ids]
    jumps = [x for x in dynamics_view.get("jump_candidates") or [] if int(x.get("turn", -1)) > int(branch_start_turn)]
    delivery_keys = _delivery_keys(trace)

    root_candidate = None
    if root:
        root_candidate = next((x for x in dynamics_view.get("jump_candidates") or [] if x.get("behavior_event_id") == root["behavior_event_id"]), None)
    root_candidate_types = list((root_candidate or {}).get("candidate_types") or [])

    if depth is None:
        all_descendant_ids = None
        continuation_descendant_ids = None
        scoped_node_ids = None
        root_relations = None
        affected = None
    else:
        all_descendant_ids = {eid for eid in depth if eid != root["behavior_event_id"]}
        continuation_descendant_ids = {
            eid for eid in all_descendant_ids
            if eid in by_id and int(by_id[eid].get("turn", -1)) > int(branch_start_turn)
        }
        scoped_node_ids = {root["behavior_event_id"]} | continuation_descendant_ids
        root_relations = [
            x for x in relations
            if x.get("source_behavior_event_id") in scoped_node_ids and x.get("target_behavior_event_id") in scoped_node_ids
        ]
        affected = sorted({
            by_id[eid].get("actor") for eid in continuation_descendant_ids
            if by_id[eid].get("actor") not in (None, "ENVIRONMENT")
        })

    classification = _jump_classification(jumps=jumps, depth=depth, delivery_keys=delivery_keys, by_id=by_id)
    descendant_jumps = [x for x in classification if x["lineage_class"] == "DESCENDANT_REJUMP"]
    independent_jumps = [x for x in classification if x["lineage_class"] == "INDEPENDENT_NEW_JUMP"]
    unresolved_jumps = [x for x in classification if x["lineage_class"] == "LINEAGE_UNRESOLVED"]
    first_rejump = _first_rejump_detail(
        classification=classification,
        root=root,
        root_candidate_types=root_candidate_types,
    ) if root else None

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
            "root_actor": root.get("actor"),
            "root_boundary_id": root.get("boundary_id"),
            "root_candidate_types": root_candidate_types,
        })

    full_post_multiset = _edge_multiset(post_relations, by_id)
    full_post_ordered = [canonical_event_signature(x) for x in sorted(post_events, key=lambda x: (int(x.get("event_index", 0)), str(x.get("behavior_phase") or "")))]

    if scoped_node_ids is None:
        root_multiset = None
        root_ordered = None
        root_cross_actor = None
        full_reachable_count = None
        continuation_reachable_count = None
        continuation_reach_depth = None
        degrees = None
        reentry = None
        path_families = None
    else:
        root_multiset = _edge_multiset(root_relations, by_id)
        root_ordered = [
            canonical_event_signature(by_id[eid])
            for eid in sorted(continuation_descendant_ids, key=lambda eid: int(by_id[eid].get("event_index", 0)))
        ]
        root_cross_actor = _cross_actor_count(root_relations, by_id)
        full_reachable_count = len(all_descendant_ids)
        continuation_reachable_count = len(continuation_descendant_ids)
        continuation_reach_depth = max((depth[eid] for eid in continuation_descendant_ids), default=0)
        degrees = _degree_metrics(scoped_node_ids, root_relations)
        reentry = _actor_reentry([by_id[eid] for eid in continuation_descendant_ids])
        path_families = _enumerate_path_families(root["behavior_event_id"], scoped_node_ids, root_relations, by_id)

    recovery_candidates = [
        x["behavior_event_id"] for x in post_events
        if x.get("boundary_id") in ("FINAL_REOPEN", "RECOVERY_CHECKPOINT") or x.get("action_type") == "revise"
    ]

    measurement = {
        "schema": MEASUREMENT_SCHEMA,
        "version": "0.4",
        "trajectory_id": trace.get("run_id"),
        "run_status": trace.get("run_status"),
        "observation_censored": bool(trace.get("observation_censored")),
        "target_candidate_id": target_candidate_id,
        "target_source_event_index": target_source_event_index,
        "target_state_key": target_state_key,
        "target_root_behavior_event_id": root.get("behavior_event_id") if root else None,
        "root_resolution": root_resolution,
        "mechanism_measurement_status": "ROOT_RESOLVED" if root else "ROOT_UNRESOLVED_NO_ZERO_IMPUTATION",
        "branch_start_turn": branch_start_turn,
        "direct_experiment_origin_exposure_count": len(delivery_keys),
        "r2_jump_recurrence": {
            "downstream_jump_classification": classification,
            "descendant_rejump_count": len(descendant_jumps) if depth is not None else None,
            "descendant_rejump_refs": [x.get("candidate_id") for x in descendant_jumps] if depth is not None else None,
            "independent_new_jump_count": len(independent_jumps) if depth is not None else None,
            "independent_new_jump_refs": [x.get("candidate_id") for x in independent_jumps] if depth is not None else None,
            "lineage_unresolved_jump_count": len(unresolved_jumps),
            "first_descendant_rejump": first_rejump,
            "first_descendant_rejump_depth": first_rejump.get("lineage_depth") if first_rejump else None,
            "first_rejump_event_distance": first_rejump.get("event_distance") if first_rejump else None,
            "first_rejump_turn_distance": first_rejump.get("turn_distance") if first_rejump else None,
            "semantic_cpr_status": "NOT_ADJUDICATED",
            "missingness_note": None if root else "ROOT_UNRESOLVED; recurrence is missing, not zero.",
        },
        "r3_inherited_inertia": {
            "all_root_reachable_event_count": full_reachable_count,
            "continuation_root_reachable_event_count": continuation_reachable_count,
            "continuation_root_reach_depth": continuation_reach_depth,
            "affected_agent_ids": affected,
            "affected_agent_count": len(affected) if affected is not None else None,
            "root_descendant_cross_actor_relation_count": root_cross_actor,
            "branch_merge_metrics": degrees,
            "role_reentry": reentry,
            "semantic_adoption_status": "NOT_ADJUDICATED",
            "semantic_role_or_authority_crossing_status": "NOT_ADJUDICATED",
            "missingness_note": None if root else "ROOT_UNRESOLVED; lineage/inertia is missing, not zero.",
        },
        "root_descendant_topology": {
            "canonical_ordered_event_signatures": root_ordered,
            "canonical_edge_multiset": root_multiset,
            "canonical_unique_edge_count": len(root_multiset) if root_multiset is not None else None,
            "canonical_edge_instance_count": sum(root_multiset.values()) if root_multiset is not None else None,
            "edge_multiset_hash": content_hash(root_multiset) if root_multiset is not None else None,
            "ordered_sequence_hash": content_hash(root_ordered) if root_ordered is not None else None,
            "observed_path_families": path_families,
            "scope": "SELECTED_ROOT_PLUS_SOURCE_BACKED_DESCENDANTS_ENTERING_POST_BRANCH_CONTINUATION",
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
            "semantic_recovery_status": "NOT_ADJUDICATED",
        },
        "terminal_outcome": {
            "run_complete": trace.get("run_status") == "RUN_COMPLETE",
            "final_state_present": trace.get("final_state") is not None,
        },
        "scientific_warning": (
            "v0.4 adds event/turn re-Jump distance, branch/merge, role re-entry and realized source-backed path families. "
            "These are mechanical structural measurements. Re-entry is not automatically a semantic loop; cross-Agent relations are not automatically authority penetration; observed path families are not an exhaustive counterfactual possibility space."
        ),
    }
    measurement["measurement_hash"] = content_hash(measurement)
    return measurement


def _counter(value):
    return Counter({str(k): int(v) for k, v in (value or {}).items()})


def compare_process_reality(control: Mapping[str, Any], intervention: Mapping[str, Any], *, comparison_id: str):
    c_root = _counter((control.get("root_descendant_topology") or {}).get("canonical_edge_multiset"))
    i_root = _counter((intervention.get("root_descendant_topology") or {}).get("canonical_edge_multiset"))
    c_full = _counter((control.get("full_post_context_topology") or {}).get("canonical_edge_multiset"))
    i_full = _counter((intervention.get("full_post_context_topology") or {}).get("canonical_edge_multiset"))
    c_order = list((control.get("root_descendant_topology") or {}).get("canonical_ordered_event_signatures") or [])
    i_order = list((intervention.get("root_descendant_topology") or {}).get("canonical_ordered_event_signatures") or [])
    c_paths = list((((control.get("root_descendant_topology") or {}).get("observed_path_families") or {}).get("observed_path_family_signatures") or []))
    i_paths = list((((intervention.get("root_descendant_topology") or {}).get("observed_path_families") or {}).get("observed_path_family_signatures") or []))

    prefix = 0
    for left, right in zip(c_order, i_order):
        if left != right:
            break
        prefix += 1
    reconvergence = _first_reconvergence(c_order, i_order, prefix)
    c_inertia = control.get("r3_inherited_inertia") or {}
    i_inertia = intervention.get("r3_inherited_inertia") or {}
    c_deg = c_inertia.get("branch_merge_metrics") or {}
    i_deg = i_inertia.get("branch_merge_metrics") or {}
    c_reentry = c_inertia.get("role_reentry") or {}
    i_reentry = i_inertia.get("role_reentry") or {}
    c_agents = set(c_inertia.get("affected_agent_ids") or [])
    i_agents = set(i_inertia.get("affected_agent_ids") or [])
    c_rejump = control.get("r2_jump_recurrence") or {}
    i_rejump = intervention.get("r2_jump_recurrence") or {}

    row = {
        "schema": COMPARISON_SCHEMA,
        "version": "0.4",
        "comparison_id": comparison_id,
        "control_trajectory_id": control.get("trajectory_id"),
        "intervention_trajectory_id": intervention.get("trajectory_id"),
        "layer1_jump_recurrence": {
            "control_descendant_rejump_count": c_rejump.get("descendant_rejump_count"),
            "intervention_descendant_rejump_count": i_rejump.get("descendant_rejump_count"),
            "control_first_rejump_event_distance": c_rejump.get("first_rejump_event_distance"),
            "intervention_first_rejump_event_distance": i_rejump.get("first_rejump_event_distance"),
            "control_first_rejump_turn_distance": c_rejump.get("first_rejump_turn_distance"),
            "intervention_first_rejump_turn_distance": i_rejump.get("first_rejump_turn_distance"),
            "control_first_rejump": c_rejump.get("first_descendant_rejump"),
            "intervention_first_rejump": i_rejump.get("first_descendant_rejump"),
        },
        "layer2_inherited_inertia": {
            "shared_path_prefix_event_count": prefix,
            "first_structural_divergence_index": prefix if prefix < min(len(c_order), len(i_order)) else None,
            "first_signature_reconvergence": reconvergence,
            "post_exposure_edge_set_overlap": _set_jaccard(c_root, i_root),
            "post_exposure_edge_multiset_overlap": _multiset_weighted_jaccard(c_root, i_root),
            "control_descendant_edge_survival_in_intervention": _multiset_survival(c_root, i_root),
            "intervention_descendant_edge_survival_in_control": _multiset_survival(i_root, c_root),
            "control_continuation_root_reach_depth": c_inertia.get("continuation_root_reach_depth"),
            "intervention_continuation_root_reach_depth": i_inertia.get("continuation_root_reach_depth"),
            "control_continuation_root_reachable_event_count": c_inertia.get("continuation_root_reachable_event_count"),
            "intervention_continuation_root_reachable_event_count": i_inertia.get("continuation_root_reachable_event_count"),
            "shared_affected_agents": sorted(c_agents & i_agents),
            "control_only_affected_agents": sorted(c_agents - i_agents),
            "intervention_only_affected_agents": sorted(i_agents - c_agents),
        },
        "layer3_path_topology": {
            "shared_path_families": sorted(set(c_paths) & set(i_paths)),
            "control_only_path_families": sorted(set(c_paths) - set(i_paths)),
            "intervention_only_path_families": sorted(set(i_paths) - set(c_paths)),
            "path_family_jaccard": _set_jaccard(c_paths, i_paths),
            "control_path_family_count": len(set(c_paths)),
            "intervention_path_family_count": len(set(i_paths)),
            "control_branch_node_count": c_deg.get("branch_node_count"),
            "intervention_branch_node_count": i_deg.get("branch_node_count"),
            "control_merge_node_count": c_deg.get("merge_node_count"),
            "intervention_merge_node_count": i_deg.get("merge_node_count"),
            "control_role_reentry_count": c_reentry.get("role_reentry_count"),
            "intervention_role_reentry_count": i_reentry.get("role_reentry_count"),
            "control_root_descendant_cross_actor_relation_count": c_inertia.get("root_descendant_cross_actor_relation_count"),
            "intervention_root_descendant_cross_actor_relation_count": i_inertia.get("root_descendant_cross_actor_relation_count"),
            "edge_set_jaccard": _set_jaccard(c_root, i_root),
            "edge_multiset_weighted_jaccard": _multiset_weighted_jaccard(c_root, i_root),
            "semantic_loop_status": "NOT_ADJUDICATED",
            "semantic_responsibility_or_authority_crossing_status": "NOT_ADJUDICATED",
        },
        "full_post_context_topology": {
            "edge_set_jaccard": _set_jaccard(c_full, i_full),
            "edge_multiset_weighted_jaccard": _multiset_weighted_jaccard(c_full, i_full),
            "interpretation": "Context diagnostic only; not selected-root inertia.",
        },
        "terminal_outcome_comparison_is_primary": False,
        "semantic_causal_effect_status": "NOT_ADJUDICATED",
        "scientific_status": "PAIRED_THREE_LAYER_ROOT_SCOPED_STRUCTURAL_PROCESS_DIFFERENCE_ONLY",
        "scientific_warning": "Structural reconvergence means recurrence of a canonical event signature after divergence, not full hidden-state or semantic convergence.",
    }
    row["comparison_hash"] = content_hash(row)
    return row
