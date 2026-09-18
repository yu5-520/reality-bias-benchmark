from __future__ import annotations

import copy
from typing import Any, Mapping

from .core import stable_hash
from .experimental_control import apply_state_intervention, verify_state_snapshot

PLAN_SCHEMA = "RB-R7-SEMANTIC-REPAIR-RUNTIME-PLAN-v0.2"
VERIFY_SCHEMA = "RB-R7-SEMANTIC-REPAIR-VERIFICATION-v0.2"
REVISION_SCHEMA = "RB-R7-DIRECT-ANCHOR-REVISION-v0.1"

REQUIRED_RUNTIME_OPERATIONS = {
    "AUTHORITY_DOWNGRADE",
    "POOL_INVALIDATION",
    "DESCENDANT_INVALIDATION",
    "SELECTIVE_RECOMPUTE",
    "DEPENDENT_DECISION_REOPEN",
}


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _hash_without(row: Mapping[str, Any], key: str) -> str:
    material = copy.deepcopy(dict(row))
    material.pop(key, None)
    return stable_hash(material)


def _validate_packet_gate(packet: Mapping[str, Any], gate: Mapping[str, Any]) -> None:
    _require(packet.get("schema") == "RB-SEMANTIC-REPAIR-PACKET-v0.1", "r7_repair_packet_schema_invalid")
    _require(gate.get("schema") == "RB-LINEAGE-COMPLETENESS-GATE-v0.1", "r7_lineage_gate_schema_invalid")
    _require(gate.get("status") == "COMPLETE_FOR_AUTHORIZED_REPAIR", "r7_lineage_gate_not_complete")
    _require(
        packet.get("repair_authorization_status") in {"READY_FOR_SEPARATE_AUTHORIZATION", "AUTHORIZED_EXTERNALLY"},
        "r7_repair_packet_not_ready",
    )
    allowed = set(packet.get("allowed_repair_operations") or [])
    missing = sorted(REQUIRED_RUNTIME_OPERATIONS - allowed)
    _require(not missing, "r7_repair_packet_missing_runtime_operations:" + ",".join(missing))


def _unrelated_snapshot_material(snapshot: Mapping[str, Any], target_key: str) -> dict:
    return {
        "shared_state": {
            key: copy.deepcopy(value)
            for key, value in (snapshot.get("shared_state") or {}).items()
            if key != target_key
        },
        "shared_state_metadata": {
            key: copy.deepcopy(value)
            for key, value in (snapshot.get("shared_state_metadata") or {}).items()
            if key != target_key
        },
        "final_state": copy.deepcopy(snapshot.get("final_state")),
        "active_agents": copy.deepcopy(snapshot.get("active_agents")),
        "inboxes": copy.deepcopy(snapshot.get("inboxes")),
        "queue": copy.deepcopy(snapshot.get("queue")),
        "events": copy.deepcopy(snapshot.get("events")),
        "turns": snapshot.get("turns"),
        "total_invocations": snapshot.get("total_invocations"),
        "message_ledger": copy.deepcopy(snapshot.get("message_ledger")),
        "invocation_ledger": copy.deepcopy(snapshot.get("invocation_ledger")),
        "execution_ledger": copy.deepcopy(snapshot.get("execution_ledger")),
        "message_seq": snapshot.get("message_seq"),
        "invocation_seq": snapshot.get("invocation_seq"),
        "last_read_message_ids": copy.deepcopy(snapshot.get("last_read_message_ids")),
        "last_read_invocation_ids": copy.deepcopy(snapshot.get("last_read_invocation_ids")),
    }


def build_repaired_parent_snapshot(
    *,
    packet: Mapping[str, Any],
    gate: Mapping[str, Any],
    parent: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> tuple[dict, dict]:
    """Create the C3 branch start by revising the already-observed Repair Anchor.

    v0.2 removes the old stochastic prerequisite that the provider must reproduce
    the historical J0 write after rollback. The frozen post-J0 parent already
    contains the content-addressed target. Repair is a branch-local revision of
    that recorded authority state, followed by prospective recomputation only.
    """
    _validate_packet_gate(packet, gate)
    verify_state_snapshot(parent)

    target_key = binding["state_key"]
    from_status = binding["from_status"]
    to_status = binding["to_status"]
    _require(target_key in (parent.get("shared_state") or {}), "r7_direct_repair_target_state_missing")
    metadata = copy.deepcopy((parent.get("shared_state_metadata") or {}).get(target_key) or {})
    _require(metadata.get("status") == from_status, "r7_direct_repair_parent_authority_status_mismatch")
    _require(
        metadata.get("event_index") == int(binding["jump_source_event_index"]),
        "r7_direct_repair_parent_event_binding_mismatch",
    )
    _require(packet.get("repair_anchor_ref"), "r7_repair_anchor_required")
    _require(packet.get("target_semantic_id"), "r7_target_semantic_id_required")

    revised_metadata = copy.deepcopy(metadata)
    revised_metadata["status"] = to_status
    revised_metadata["repair_revision"] = {
        "schema": REVISION_SCHEMA,
        "repair_anchor_ref": packet["repair_anchor_ref"],
        "target_semantic_id": packet["target_semantic_id"],
        "semantic_repair_packet_hash": packet.get("packet_hash"),
        "lineage_completeness_gate_hash": gate.get("gate_hash"),
        "revision_of_event_index": int(binding["jump_source_event_index"]),
        "from_status": from_status,
        "to_status": to_status,
        "revision_mode": "BRANCH_LOCAL_DIRECT_ANCHOR_REVISION",
    }

    intervention = {
        "type": "set_shared_state",
        "key": target_key,
        "value": copy.deepcopy(parent["shared_state"][target_key]),
        "metadata": revised_metadata,
        "result_anchor_ref": "repair_revision:" + str(packet["repair_anchor_ref"]),
    }
    repaired = apply_state_intervention(parent, intervention)
    verify_state_snapshot(repaired)

    _require(parent["state_hash"] != repaired["state_hash"], "r7_direct_repair_must_change_branch_state_hash")
    _require(
        repaired["shared_state"][target_key] == parent["shared_state"][target_key],
        "r7_direct_repair_must_not_replace_target_value",
    )
    _require(
        repaired["shared_state_metadata"][target_key]["status"] == to_status,
        "r7_direct_repair_target_status_not_revised",
    )

    parent_unrelated_hash = stable_hash(_unrelated_snapshot_material(parent, target_key))
    repaired_unrelated_hash = stable_hash(_unrelated_snapshot_material(repaired, target_key))
    _require(
        parent_unrelated_hash == repaired_unrelated_hash,
        "r7_direct_repair_touched_unrelated_parent_material",
    )

    revision = {
        "schema": REVISION_SCHEMA,
        "version": "0.1",
        "repair_anchor_ref": packet["repair_anchor_ref"],
        "target_semantic_id": packet["target_semantic_id"],
        "target_state_key": target_key,
        "source_parent_state_hash": parent["state_hash"],
        "repaired_parent_state_hash": repaired["state_hash"],
        "source_parent_turn": int(parent["turns"]),
        "source_anchor_event_index": int(binding["jump_source_event_index"]),
        "from_status": from_status,
        "to_status": to_status,
        "semantic_repair_packet_hash": packet.get("packet_hash"),
        "lineage_completeness_gate_hash": gate.get("gate_hash"),
        "target_value_preserved": True,
        "unrelated_parent_material_preserved": True,
        "unrelated_parent_material_hash": parent_unrelated_hash,
        "provider_internal_state_replayed": False,
    }
    revision["revision_hash"] = stable_hash(revision)
    return repaired, revision


def build_semantic_repair_runtime_plan(*, packet: Mapping[str, Any], gate: Mapping[str, Any], bundle: Mapping[str, Any]) -> dict:
    _validate_packet_gate(packet, gate)

    binding = bundle["c3_alr_binding"]
    parent = bundle["source_parent_snapshot"]
    repaired = bundle["c3_repaired_parent_snapshot"]
    revision = bundle["c3_direct_anchor_revision"]
    target_state_key = binding["state_key"]

    verify_state_snapshot(parent)
    verify_state_snapshot(repaired)
    _require(packet.get("repair_closure_refs"), "r7_repair_closure_required")
    _require(packet.get("evidence_supported_affected_closure_refs"), "r7_affected_closure_required")
    _require(parent["state_hash"] == binding["common_reference_parent_state_hash"], "r7_repair_parent_hash_mismatch")
    _require(repaired["state_hash"] == binding["repaired_parent_state_hash"], "r7_repaired_parent_hash_mismatch")
    _require(revision["repaired_parent_state_hash"] == repaired["state_hash"], "r7_revision_repaired_hash_mismatch")

    plan = {
        "schema": PLAN_SCHEMA,
        "version": "0.2",
        "packet_id": packet["packet_id"],
        "packet_hash": packet.get("packet_hash"),
        "gate_id": gate["gate_id"],
        "gate_hash": gate.get("gate_hash"),
        "repair_anchor_ref": packet["repair_anchor_ref"],
        "target_semantic_id": packet["target_semantic_id"],
        "content_address": packet["content_address"],
        "target_state_key": target_state_key,
        "authority_from_status": binding["from_status"],
        "authority_to_status": binding["to_status"],
        "common_reference_parent_state_hash": parent["state_hash"],
        "repaired_parent_state_hash": repaired["state_hash"],
        "direct_anchor_revision_hash": revision["revision_hash"],
        "repair_parent_turn": int(parent["turns"]),
        "post_repair_first_turn": int(parent["turns"]) + 1,
        "repair_closure_refs": list(packet["repair_closure_refs"]),
        "affected_closure_refs": list(packet["evidence_supported_affected_closure_refs"]),
        "mechanically_required_replay_refs": list(packet.get("mechanically_required_replay_refs") or []),
        "preserved_unrelated_refs": list(packet.get("preserved_unrelated_refs") or []),
        "operation_bindings": {
            "AUTHORITY_DOWNGRADE": "BRANCH_LOCAL_DIRECT_REVISION_OF_CONTENT_ADDRESSED_ANCHOR",
            "POOL_INVALIDATION": "REVISE_TARGET_SHARED_POOL_AUTHORITY_IN_BRANCH_START_STATE",
            "DESCENDANT_INVALIDATION": "START_FROM_FROZEN_POST_J0_PARENT_BEFORE_ANY_POST_ANCHOR_DESCENDANTS",
            "DEPENDENT_DECISION_REOPEN": "RESUME_FROZEN_POST_J0_QUEUE_FROM_REPAIRED_PARENT",
            "SELECTIVE_RECOMPUTE": "RECOMPUTE_ONLY_POST_J0_CONTINUATION_WITHIN_BOUND_HORIZON",
        },
        "invalidation_scope": "TARGET_AUTHORITY_PLUS_ALL_NOT_YET_REALIZED_POST_J0_DESCENDANTS",
        "recompute_scope": "POST_J0_CONTINUATION_ONLY",
        "unrelated_structure_policy": "DIRECT_REPAIR_MUST_PRESERVE_ALL_NON_TARGET_PARENT_MATERIAL",
        "old_lineage_reentry_policy": "DETECT_POST_REPAIR_TARGET_REWRITE_TO_PRE_REPAIR_AUTHORITY",
        "semantic_success_not_predeclared": True,
    }
    plan["plan_hash"] = _hash_without(plan, "plan_hash")
    return plan


def verify_semantic_repair_trace(
    *,
    trace: Mapping[str, Any],
    plan: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    repaired_parent: Mapping[str, Any],
) -> dict:
    _require(plan.get("schema") == PLAN_SCHEMA, "r7_semantic_repair_runtime_plan_invalid")
    _require(plan.get("plan_hash") == _hash_without(plan, "plan_hash"), "r7_semantic_repair_runtime_plan_hash_mismatch")
    verify_state_snapshot(source_parent)
    verify_state_snapshot(repaired_parent)
    _require(source_parent["state_hash"] == plan["common_reference_parent_state_hash"], "r7_verify_source_parent_hash_mismatch")
    _require(repaired_parent["state_hash"] == plan["repaired_parent_state_hash"], "r7_verify_repaired_parent_hash_mismatch")

    target_key = plan["target_state_key"]
    from_status = plan["authority_from_status"]
    to_status = plan["authority_to_status"]
    repair_turn = int(plan["repair_parent_turn"])

    _require(
        source_parent["shared_state_metadata"][target_key]["status"] == from_status,
        "r7_verify_source_authority_status_mismatch",
    )
    _require(
        repaired_parent["shared_state_metadata"][target_key]["status"] == to_status,
        "r7_verify_repaired_authority_status_mismatch",
    )
    _require(
        source_parent["shared_state"][target_key] == repaired_parent["shared_state"][target_key],
        "r7_verify_target_value_changed_by_repair",
    )
    _require(
        stable_hash(_unrelated_snapshot_material(source_parent, target_key))
        == stable_hash(_unrelated_snapshot_material(repaired_parent, target_key)),
        "r7_verify_direct_repair_touched_unrelated_material",
    )

    old_lineage_reentry_refs = []
    recomputed_events = []
    for event in trace.get("events") or []:
        turn = int(event.get("turn") or -1)
        if turn <= repair_turn:
            continue
        recomputed_events.append(event)
        action = event.get("action") or {}
        if (
            event.get("realized_in_baseline")
            and event.get("action_type") == "write_state"
            and action.get("key") == target_key
            and action.get("status") == from_status
        ):
            old_lineage_reentry_refs.append("arena_event:" + str(event.get("event_index")))

    recomputed_event_refs = ["arena_event:" + str(event.get("event_index")) for event in recomputed_events]
    reopened_model_calls = [
        call for call in (trace.get("model_calls") or [])
        if int(call.get("turn") or -1) > repair_turn
    ]

    final_state = trace.get("final_state") or {}
    final_shared_state = final_state.get("state") if isinstance(final_state, Mapping) else {}
    final_metadata = final_state.get("state_metadata") if isinstance(final_state, Mapping) else {}
    if not isinstance(final_shared_state, Mapping):
        final_shared_state = {}
    if not isinstance(final_metadata, Mapping):
        final_metadata = {}

    post_repair_unrelated_change_refs = []
    for key in sorted(set(repaired_parent.get("shared_state") or {}) - {target_key}):
        start_hash = stable_hash({
            "value": repaired_parent["shared_state"].get(key),
            "metadata": repaired_parent["shared_state_metadata"].get(key),
        })
        final_hash = stable_hash({
            "value": final_shared_state.get(key),
            "metadata": final_metadata.get(key),
        })
        if start_hash != final_hash:
            post_repair_unrelated_change_refs.append("shared_state:" + key)

    before_closure = {
        "repair_closure_refs": list(plan["repair_closure_refs"]),
        "affected_closure_refs": list(plan["affected_closure_refs"]),
        "target_state_key": target_key,
        "authority_status": from_status,
        "source_parent_state_hash": source_parent["state_hash"],
    }
    after_closure = {
        "repair_closure_refs": list(plan["repair_closure_refs"]),
        "affected_closure_refs": list(plan["affected_closure_refs"]),
        "target_state_key": target_key,
        "authority_status_at_branch_start": to_status,
        "repaired_parent_state_hash": repaired_parent["state_hash"],
        "recomputed_event_refs": recomputed_event_refs,
        "old_lineage_reentry_refs": old_lineage_reentry_refs,
        "post_repair_unrelated_change_refs": post_repair_unrelated_change_refs,
    }

    row = {
        "schema": VERIFY_SCHEMA,
        "version": "0.2",
        "runtime_plan_hash": plan["plan_hash"],
        "packet_hash": plan["packet_hash"],
        "gate_hash": plan["gate_hash"],
        "repair_anchor_ref": plan["repair_anchor_ref"],
        "target_semantic_id": plan["target_semantic_id"],
        "repair_turn": repair_turn,
        "direct_anchor_revision_hash": plan["direct_anchor_revision_hash"],
        "authority_revision_applied_at_branch_start": True,
        "pool_invalidation_method": plan["operation_bindings"]["POOL_INVALIDATION"],
        "descendant_invalidation_method": plan["operation_bindings"]["DESCENDANT_INVALIDATION"],
        "dependent_decision_reopen_method": plan["operation_bindings"]["DEPENDENT_DECISION_REOPEN"],
        "selective_recompute_method": plan["operation_bindings"]["SELECTIVE_RECOMPUTE"],
        "repair_closure_invalidated_at_branch_start": True,
        "reopened_model_call_refs": [
            "turn:" + str(call.get("turn")) + ":agent:" + str(call.get("agent_id"))
            for call in reopened_model_calls
        ],
        "recomputed_descendant_refs": recomputed_event_refs,
        "direct_repair_preserved_unrelated_parent_material": True,
        "preserved_unrelated_structure": True,
        "post_repair_unrelated_change_refs": post_repair_unrelated_change_refs,
        "old_lineage_reentry_refs": old_lineage_reentry_refs,
        "old_lineage_reentry_detected": bool(old_lineage_reentry_refs),
        "semantic_lineage_closure_before_hash": stable_hash(before_closure),
        "semantic_lineage_closure_after_hash": stable_hash(after_closure),
        "target_integrity_repair_executed": True,
        "recovery_success_semantic_status": "NOT_ADJUDICATED",
        "terminal_outcome_is_primary": False,
        "interpretation_boundary": (
            "Runtime verification proves direct execution of the packet-bound anchor revision and records downstream "
            "re-entry/recomputation. Post-repair changes outside the target key are recorded, not automatically labeled damage. "
            "This record does not adjudicate semantic CPR or empirical recovery success."
        ),
    }
    row["verification_hash"] = stable_hash(row)
    return row
