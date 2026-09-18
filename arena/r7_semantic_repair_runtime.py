from __future__ import annotations

import copy
from typing import Any, Mapping

from .core import stable_hash

PLAN_SCHEMA = "RB-R7-SEMANTIC-REPAIR-RUNTIME-PLAN-v0.1"
VERIFY_SCHEMA = "RB-R7-SEMANTIC-REPAIR-VERIFICATION-v0.1"

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


def build_semantic_repair_runtime_plan(*, packet: Mapping[str, Any], gate: Mapping[str, Any], bundle: Mapping[str, Any]) -> dict:
    _require(packet.get("schema") == "RB-SEMANTIC-REPAIR-PACKET-v0.1", "r7_repair_packet_schema_invalid")
    _require(gate.get("schema") == "RB-LINEAGE-COMPLETENESS-GATE-v0.1", "r7_lineage_gate_schema_invalid")
    _require(gate.get("status") == "COMPLETE_FOR_AUTHORIZED_REPAIR", "r7_lineage_gate_not_complete")
    _require(packet.get("repair_authorization_status") in {"READY_FOR_SEPARATE_AUTHORIZATION", "AUTHORIZED_EXTERNALLY"}, "r7_repair_packet_not_ready")
    allowed = set(packet.get("allowed_repair_operations") or [])
    missing = sorted(REQUIRED_RUNTIME_OPERATIONS - allowed)
    _require(not missing, "r7_repair_packet_missing_runtime_operations:" + ",".join(missing))

    alr = bundle["c3_alr_binding"]
    checkpoint = bundle["c3_recovery_checkpoint"]
    parent = bundle["source_parent_snapshot"]
    target_state_key = alr["state_key"]

    _require(packet.get("repair_anchor_ref"), "r7_repair_anchor_required")
    _require(packet.get("target_semantic_id"), "r7_target_semantic_id_required")
    _require(packet.get("repair_closure_refs"), "r7_repair_closure_required")
    _require(packet.get("evidence_supported_affected_closure_refs"), "r7_affected_closure_required")
    _require(checkpoint["turns"] + 1 == int(alr["target_reexecution_turn"]), "r7_repair_checkpoint_turn_mismatch")
    _require(parent["state_hash"] == alr["common_reference_parent_state_hash"], "r7_repair_parent_hash_mismatch")
    _require(checkpoint["state_hash"] == alr["recovery_checkpoint_state_hash"], "r7_repair_checkpoint_hash_mismatch")

    preserved_state_keys = sorted(
        key for key in (checkpoint.get("shared_state") or {})
        if key != target_state_key
    )
    preserved_state_hashes = {
        key: stable_hash({
            "value": (checkpoint.get("shared_state") or {}).get(key),
            "metadata": (checkpoint.get("shared_state_metadata") or {}).get(key),
        })
        for key in preserved_state_keys
    }

    plan = {
        "schema": PLAN_SCHEMA,
        "version": "0.1",
        "packet_id": packet["packet_id"],
        "packet_hash": packet.get("packet_hash"),
        "gate_id": gate["gate_id"],
        "gate_hash": gate.get("gate_hash"),
        "repair_anchor_ref": packet["repair_anchor_ref"],
        "target_semantic_id": packet["target_semantic_id"],
        "content_address": packet["content_address"],
        "target_state_key": target_state_key,
        "authority_from_status": alr["from_status"],
        "authority_to_status": alr["to_status"],
        "recovery_checkpoint_state_hash": checkpoint["state_hash"],
        "common_reference_parent_state_hash": parent["state_hash"],
        "repair_closure_refs": list(packet["repair_closure_refs"]),
        "affected_closure_refs": list(packet["evidence_supported_affected_closure_refs"]),
        "mechanically_required_replay_refs": list(packet.get("mechanically_required_replay_refs") or []),
        "preserved_unrelated_refs": list(packet.get("preserved_unrelated_refs") or []),
        "preserved_checkpoint_state_keys": preserved_state_keys,
        "preserved_checkpoint_state_hashes": preserved_state_hashes,
        "operation_bindings": {
            "AUTHORITY_DOWNGRADE": "ACTION_ENVELOPE_TRANSFORM_ON_REEXECUTED_AUTHORITY_COMMIT",
            "POOL_INVALIDATION": "CHECKPOINT_EXCLUSION_OF_POST_ANCHOR_POOL_REALIZATIONS",
            "DESCENDANT_INVALIDATION": "CHECKPOINT_EXCLUSION_OF_POST_ANCHOR_DESCENDANTS",
            "DEPENDENT_DECISION_REOPEN": "REEXECUTE_FROM_AUTHORITY_ANCESTOR_CHECKPOINT",
            "SELECTIVE_RECOMPUTE": "RECOMPUTE_REOPENED_POST_ANCHOR_CONTINUATION_WITHIN_BOUND_HORIZON",
        },
        "invalidation_scope": "REPAIR_CLOSURE_PLUS_POST_ANCHOR_REALIZATIONS",
        "recompute_scope": "REOPENED_POST_ANCHOR_CONTINUATION_WITHIN_BOUND_HORIZON",
        "unrelated_structure_policy": "VERIFY_CHECKPOINT_UNRELATED_STATE_PRESERVATION",
        "old_lineage_reentry_policy": "DETECT_TARGET_STATE_KEY_REWRITE_TO_PRE_REPAIR_AUTHORITY",
        "semantic_success_not_predeclared": True,
    }
    plan["plan_hash"] = _hash_without(plan, "plan_hash")
    return plan


def verify_semantic_repair_trace(*, trace: Mapping[str, Any], plan: Mapping[str, Any], transform_summary: Mapping[str, Any]) -> dict:
    _require(plan.get("schema") == PLAN_SCHEMA, "r7_semantic_repair_runtime_plan_invalid")
    _require(plan.get("plan_hash") == _hash_without(plan, "plan_hash"), "r7_semantic_repair_runtime_plan_hash_mismatch")
    _require(transform_summary.get("transform_count") == 1, "r7_semantic_repair_requires_one_authority_transform")

    target_key = plan["target_state_key"]
    from_status = plan["authority_from_status"]
    to_status = plan["authority_to_status"]

    transform_records = [
        row for row in (trace.get("action_transform_records") or [])
        if row.get("state_key") == target_key and row.get("transform_applied") is True
    ]
    _require(len(transform_records) == 1, "r7_semantic_repair_target_transform_not_unique")
    transform = transform_records[0]
    repair_turn = int(transform["turn"])

    realized_target_writes = []
    for event in trace.get("events") or []:
        action = event.get("action") or {}
        if (
            event.get("realized_in_baseline")
            and event.get("action_type") == "write_state"
            and action.get("key") == target_key
        ):
            realized_target_writes.append(event)

    repaired_target_events = [
        event for event in realized_target_writes
        if int(event.get("turn") or -1) == repair_turn and (event.get("action") or {}).get("status") == to_status
    ]
    _require(repaired_target_events, "r7_repaired_target_write_not_realized")

    old_lineage_reentry_refs = []
    for event in realized_target_writes:
        if int(event.get("turn") or -1) <= repair_turn:
            continue
        if (event.get("action") or {}).get("status") == from_status:
            old_lineage_reentry_refs.append("arena_event:" + str(event.get("event_index")))

    recomputed_events = [
        event for event in (trace.get("events") or [])
        if int(event.get("turn") or -1) >= repair_turn
    ]
    recomputed_event_refs = ["arena_event:" + str(event.get("event_index")) for event in recomputed_events]
    reopened_model_calls = [
        call for call in (trace.get("model_calls") or [])
        if int(call.get("turn") or -1) >= repair_turn
    ]

    final_state = trace.get("final_state") or {}
    final_shared_state = final_state.get("state") if isinstance(final_state, Mapping) else {}
    final_metadata = final_state.get("state_metadata") if isinstance(final_state, Mapping) else {}
    if not isinstance(final_shared_state, Mapping):
        final_shared_state = {}
    if not isinstance(final_metadata, Mapping):
        final_metadata = {}

    preserved_checks = {}
    for key, expected_hash in (plan.get("preserved_checkpoint_state_hashes") or {}).items():
        observed_hash = stable_hash({
            "value": final_shared_state.get(key),
            "metadata": final_metadata.get(key),
        })
        preserved_checks[key] = {
            "expected_checkpoint_hash": expected_hash,
            "observed_final_hash": observed_hash,
            "preserved": observed_hash == expected_hash,
        }

    preserved_unrelated_ok = all(row["preserved"] for row in preserved_checks.values()) if preserved_checks else True

    before_closure = {
        "repair_closure_refs": list(plan["repair_closure_refs"]),
        "affected_closure_refs": list(plan["affected_closure_refs"]),
        "target_state_key": target_key,
        "authority_status": from_status,
        "common_reference_parent_state_hash": plan["common_reference_parent_state_hash"],
    }
    after_closure = {
        "repair_closure_refs": list(plan["repair_closure_refs"]),
        "affected_closure_refs": list(plan["affected_closure_refs"]),
        "target_state_key": target_key,
        "authority_status_after_repair": to_status,
        "recomputed_event_refs": recomputed_event_refs,
        "old_lineage_reentry_refs": old_lineage_reentry_refs,
        "preserved_unrelated_ok": preserved_unrelated_ok,
    }

    row = {
        "schema": VERIFY_SCHEMA,
        "version": "0.1",
        "runtime_plan_hash": plan["plan_hash"],
        "packet_hash": plan["packet_hash"],
        "gate_hash": plan["gate_hash"],
        "repair_anchor_ref": plan["repair_anchor_ref"],
        "target_semantic_id": plan["target_semantic_id"],
        "repair_turn": repair_turn,
        "authority_transform_applied": True,
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
        "preserved_unrelated_checks": preserved_checks,
        "preserved_unrelated_structure": preserved_unrelated_ok,
        "old_lineage_reentry_refs": old_lineage_reentry_refs,
        "old_lineage_reentry_detected": bool(old_lineage_reentry_refs),
        "semantic_lineage_closure_before_hash": stable_hash(before_closure),
        "semantic_lineage_closure_after_hash": stable_hash(after_closure),
        "target_integrity_repair_executed": True,
        "recovery_success_semantic_status": "NOT_ADJUDICATED",
        "terminal_outcome_is_primary": False,
        "interpretation_boundary": (
            "Runtime verification proves execution of the packet-bound repair mechanics and records structural re-entry/preservation. "
            "It does not adjudicate semantic CPR or declare recovery efficacy."
        ),
    }
    row["verification_hash"] = stable_hash(row)
    return row
