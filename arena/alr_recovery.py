from __future__ import annotations

import copy
from typing import Any, Iterable, Mapping

from .core import stable_hash

ALR_PLAN_SCHEMA = "RB-ALR-LOCALIZED-RECOVERY-PLAN-v0.1"
ALR_REVISION_SCHEMA = "RB-ALR-REVISION-LINEAGE-v0.1"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _hash_without(row: Mapping[str, Any], key: str) -> str:
    material = copy.deepcopy(dict(row))
    material.pop(key, None)
    return stable_hash(material)


def _unique(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        _require(isinstance(value, str) and value, "alr_node_ref_must_be_nonempty_string")
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def build_alr_recovery_plan(
    *,
    recovery_id: str,
    parent_trace_hash: str,
    parent_state_hash: str,
    jump_ref: str,
    authority_ancestor_ref: str,
    dependency_edges: list[Mapping[str, Any]],
    semantic_payload_hash: str,
    recovery_condition: Mapping[str, Any],
    all_known_node_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Build a deterministic, lineage-aware localized recovery plan.

    `dependency_edges` must contain directed structural relations with `source_ref`
    and `target_ref`. The affected closure is the authority ancestor plus every
    downstream node reachable from it. Unaffected nodes are preserved by default.

    This function plans structure only. It does not judge whether the semantic
    correction is true, and it does not call a model.
    """
    _require(isinstance(recovery_id, str) and recovery_id, "alr_recovery_id_required")
    _require(isinstance(parent_trace_hash, str) and parent_trace_hash, "alr_parent_trace_hash_required")
    _require(isinstance(parent_state_hash, str) and parent_state_hash, "alr_parent_state_hash_required")
    _require(isinstance(jump_ref, str) and jump_ref, "alr_jump_ref_required")
    _require(isinstance(authority_ancestor_ref, str) and authority_ancestor_ref, "alr_authority_ancestor_ref_required")
    _require(isinstance(semantic_payload_hash, str) and semantic_payload_hash, "alr_semantic_payload_hash_required")
    _require(isinstance(recovery_condition, Mapping) and recovery_condition, "alr_recovery_condition_required")
    _require(isinstance(dependency_edges, list), "alr_dependency_edges_must_be_list")

    normalized_edges: list[dict[str, Any]] = []
    adjacency: dict[str, list[str]] = {}
    observed_nodes: list[str] = []
    for raw in dependency_edges:
        _require(isinstance(raw, Mapping), "alr_dependency_edge_must_be_object")
        source_ref = raw.get("source_ref")
        target_ref = raw.get("target_ref")
        _require(isinstance(source_ref, str) and source_ref, "alr_dependency_edge_source_required")
        _require(isinstance(target_ref, str) and target_ref, "alr_dependency_edge_target_required")
        relation = raw.get("relation") or "depends_on"
        edge = {
            "source_ref": source_ref,
            "target_ref": target_ref,
            "relation": relation,
        }
        if "evidence_ref" in raw:
            edge["evidence_ref"] = raw.get("evidence_ref")
        normalized_edges.append(edge)
        adjacency.setdefault(source_ref, []).append(target_ref)
        observed_nodes.extend([source_ref, target_ref])

    closure: list[str] = []
    seen: set[str] = set()
    stack = [authority_ancestor_ref]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        closure.append(node)
        # Reverse sorted push keeps deterministic forward lexical traversal.
        for nxt in sorted(adjacency.get(node, []), reverse=True):
            if nxt not in seen:
                stack.append(nxt)

    known_nodes = _unique(list(all_known_node_refs or []) + observed_nodes + [jump_ref, authority_ancestor_ref])
    preserved = [node for node in known_nodes if node not in seen]

    _require(authority_ancestor_ref in closure, "alr_authority_ancestor_missing_from_closure")
    _require(set(closure).isdisjoint(set(preserved)), "alr_affected_preserved_overlap")

    plan = {
        "schema": ALR_PLAN_SCHEMA,
        "version": "0.1",
        "recovery_id": recovery_id,
        "parent_trace_hash": parent_trace_hash,
        "parent_state_hash": parent_state_hash,
        "jump_ref": jump_ref,
        "authority_ancestor_ref": authority_ancestor_ref,
        "dependency_edges": normalized_edges,
        "dependency_graph_hash": stable_hash(normalized_edges),
        "affected_dependency_closure": closure,
        "affected_dependency_closure_hash": stable_hash(closure),
        "reopen_node_refs": closure,
        "preserve_node_refs": preserved,
        "semantic_payload_hash": semantic_payload_hash,
        "recovery_condition": copy.deepcopy(dict(recovery_condition)),
        "recovery_condition_hash": stable_hash(dict(recovery_condition)),
        "recovery_scope": "AFFECTED_DEPENDENCY_CLOSURE_ONLY",
        "unaffected_node_policy": "PRESERVE_BY_DEFAULT",
        "provider_internal_state_replayed": False,
        "semantic_truth_adjudicated_by_planner": False,
    }
    plan["plan_hash"] = _hash_without(plan, "plan_hash")
    verify_alr_recovery_plan(plan)
    return plan


def verify_alr_recovery_plan(plan: Mapping[str, Any]) -> bool:
    _require(isinstance(plan, Mapping), "alr_plan_must_be_object")
    _require(plan.get("schema") == ALR_PLAN_SCHEMA, "alr_plan_schema_invalid")
    _require(plan.get("recovery_scope") == "AFFECTED_DEPENDENCY_CLOSURE_ONLY", "alr_recovery_scope_invalid")
    _require(plan.get("unaffected_node_policy") == "PRESERVE_BY_DEFAULT", "alr_preserve_policy_invalid")
    _require(plan.get("provider_internal_state_replayed") is False, "alr_provider_replay_claim_invalid")
    _require(plan.get("semantic_truth_adjudicated_by_planner") is False, "alr_planner_must_not_adjudicate_semantic_truth")
    closure = list(plan.get("affected_dependency_closure") or [])
    reopen = list(plan.get("reopen_node_refs") or [])
    preserve = list(plan.get("preserve_node_refs") or [])
    _require(closure and closure == reopen, "alr_reopen_must_equal_affected_closure")
    _require(plan.get("authority_ancestor_ref") in closure, "alr_authority_ancestor_not_reopened")
    _require(set(reopen).isdisjoint(set(preserve)), "alr_reopen_preserve_overlap")
    _require(plan.get("dependency_graph_hash") == stable_hash(plan.get("dependency_edges") or []), "alr_dependency_graph_hash_mismatch")
    _require(plan.get("affected_dependency_closure_hash") == stable_hash(closure), "alr_closure_hash_mismatch")
    _require(plan.get("recovery_condition_hash") == stable_hash(plan.get("recovery_condition")), "alr_recovery_condition_hash_mismatch")
    _require(plan.get("plan_hash") == _hash_without(plan, "plan_hash"), "alr_plan_hash_mismatch")
    return True


def make_revision_lineage_record(
    *,
    plan: Mapping[str, Any],
    prior_revision_hash: str | None,
    recovered_state_hash: str,
    reopened_node_refs: list[str],
    preserved_node_refs: list[str],
) -> dict[str, Any]:
    verify_alr_recovery_plan(plan)
    _require(isinstance(recovered_state_hash, str) and recovered_state_hash, "alr_recovered_state_hash_required")
    reopened = _unique(reopened_node_refs)
    preserved = _unique(preserved_node_refs)
    _require(set(reopened).issubset(set(plan["reopen_node_refs"])), "alr_revision_reopened_outside_plan")
    _require(set(preserved).issubset(set(plan["preserve_node_refs"])), "alr_revision_preserved_outside_plan")
    _require(set(reopened).isdisjoint(set(preserved)), "alr_revision_reopen_preserve_overlap")

    row = {
        "schema": ALR_REVISION_SCHEMA,
        "version": "0.1",
        "recovery_id": plan["recovery_id"],
        "plan_hash": plan["plan_hash"],
        "parent_state_hash": plan["parent_state_hash"],
        "prior_revision_hash": prior_revision_hash,
        "recovered_state_hash": recovered_state_hash,
        "reopened_node_refs": reopened,
        "preserved_node_refs": preserved,
        "provider_internal_state_replayed": False,
    }
    row["revision_hash"] = _hash_without(row, "revision_hash")
    verify_revision_lineage_record(row, plan=plan)
    return row


def verify_revision_lineage_record(row: Mapping[str, Any], *, plan: Mapping[str, Any]) -> bool:
    verify_alr_recovery_plan(plan)
    _require(isinstance(row, Mapping), "alr_revision_record_must_be_object")
    _require(row.get("schema") == ALR_REVISION_SCHEMA, "alr_revision_schema_invalid")
    _require(row.get("plan_hash") == plan.get("plan_hash"), "alr_revision_plan_hash_mismatch")
    _require(row.get("parent_state_hash") == plan.get("parent_state_hash"), "alr_revision_parent_hash_mismatch")
    _require(row.get("provider_internal_state_replayed") is False, "alr_revision_provider_replay_claim_invalid")
    _require(set(row.get("reopened_node_refs") or []).issubset(set(plan.get("reopen_node_refs") or [])), "alr_revision_reopened_outside_plan")
    _require(set(row.get("preserved_node_refs") or []).issubset(set(plan.get("preserve_node_refs") or [])), "alr_revision_preserved_outside_plan")
    _require(row.get("revision_hash") == _hash_without(row, "revision_hash"), "alr_revision_hash_mismatch")
    return True
