from __future__ import annotations

import copy
from typing import Any, Mapping

from .core import stable_hash
from .experimental_control import apply_state_intervention, verify_state_snapshot

PLAN_SCHEMA = "RB-R7-SEMANTIC-REPAIR-RUNTIME-PLAN-v0.2"
REPAIR_APPLICATION_SCHEMA = "RB-R7-SEMANTIC-REPAIR-APPLICATION-v0.1"
VERIFY_SCHEMA = "RB-R7-SEMANTIC-REPAIR-VERIFICATION-v0.2"

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


def _state_cell_hash(snapshot: Mapping[str, Any], key: str) -> str:
    return stable_hash({
        "value": (snapshot.get("shared_state") or {}).get(key),
        "metadata": (snapshot.get("shared_state_metadata") or {}).get(key),
    })


def build_semantic_repair_runtime_plan(*, packet: Mapping[str, Any], gate: Mapping[str, Any], bundle: Mapping[str, Any]) -> dict:
    _require(packet.get("schema") == "RB-SEMANTIC-REPAIR-PACKET-v0.1", "r7_repair_packet_schema_invalid")
    _require(gate.get("schema") == "RB-LINEAGE-COMPLETENESS-GATE-v0.1", "r7_lineage_gate_schema_invalid")
    _require(gate.get("status") == "COMPLETE_FOR_AUTHORIZED_REPAIR", "r7_lineage_gate_not_complete")
    _require(packet.get("repair_authorization_status") in {"READY_FOR_SEPARATE_AUTHORIZATION", "AUTHORIZED_EXTERNALLY"}, "r7_repair_packet_not_ready")
    allowed = set(packet.get("allowed_repair_operations") or [])
    missing = sorted(REQUIRED_RUNTIME_OPERATIONS - allowed)
    _require(not missing, "r7_repair_packet_missing_runtime_operations:" + ",".join(missing))

    alr = bundle["c3_alr_binding"]
    parent = bundle["source_parent_snapshot"]
    checkpoint = bundle["c3_recovery_checkpoint"]
    verify_state_snapshot(parent)
    verify_state_snapshot(checkpoint)

    target_state_key = alr["state_key"]
    from_status = alr["from_status"]
    to_status = alr["to_status"]

    _require(packet.get("repair_anchor_ref"), "r7_repair_anchor_required")
    _require(packet.get("target_semantic_id"), "r7_target_semantic_id_required")
    _require(packet.get("repair_closure_refs"), "r7_repair_closure_required")
    _require(packet.get("evidence_supported_affected_closure_refs"), "r7_affected_closure_required")
    _require(parent["state_hash"] == alr["common_reference_parent_state_hash"], "r7_repair_parent_hash_mismatch")
    _require(checkpoint["state_hash"] == alr["recovery_checkpoint_state_hash"], "r7_repair_checkpoint_hash_mismatch")
    _require(target_state_key in (parent.get("shared_state") or {}), "r7_repair_target_value_missing_from_parent")
    _require(target_state_key in (parent.get("shared_state_metadata") or {}), "r7_repair_target_metadata_missing_from_parent")
    _require((parent["shared_state_metadata"][target_state_key] or {}).get("status") == from_status, "r7_repair_parent_authority_status_mismatch")
    _require(parent.get("terminated") is False and parent.get("queue"), "r7_repair_parent_not_resumable")

    preserved_state_keys = sorted(
        key for key in (parent.get("shared_state") or {})
        if key != target_state_key
    )
    preserved_parent_state_hashes = {
        key: _state_cell_hash(parent, key)
        for key in preserved_state_keys
    }

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
        "authority_from_status": from_status,
        "authority_to_status": to_status,
        "common_reference_parent_state_hash": parent["state_hash"],
        "common_reference_parent_turn": int(parent["turns"]),
        "common_reference_parent_event_count": len(parent.get("events") or []),
        "historical_pre_anchor_checkpoint_state_hash": checkpoint["state_hash"],
        "repair_closure_refs": list(packet["repair_closure_refs"]),
        "affected_closure_refs": list(packet["evidence_supported_affected_closure_refs"]),
        "mechanically_required_replay_refs": list(packet.get("mechanically_required_replay_refs") or []),
        "preserved_unrelated_refs": list(packet.get("preserved_unrelated_refs") or []),
        "preserved_parent_state_keys": preserved_state_keys,
        "preserved_parent_state_hashes": preserved_parent_state_hashes,
        "operation_bindings": {
            "AUTHORITY_DOWNGRADE": "PERSISTENT_BRANCH_STATE_STATUS_MUTATION_ON_FROZEN_POST_J0_PARENT",
            "POOL_INVALIDATION": "REPLACE_TARGET_AUTHORITY_AT_REPAIR_ANCHOR_BEFORE_DESCENDANT_CONTINUATION",
            "DESCENDANT_INVALIDATION": "EXCLUDE_ALL_POST_PARENT_DESCENDANTS_FROM_REPAIRED_BRANCH_START",
            "DEPENDENT_DECISION_REOPEN": "RESUME_EXISTING_POST_J0_QUEUE_FROM_REPAIRED_PARENT",
            "SELECTIVE_RECOMPUTE": "RECOMPUTE_POST_J0_DESCENDANT_CONTINUATION_WITHIN_BOUND_HORIZON",
        },
        "invalidation_scope": "TARGET_AUTHORITY_PLUS_NOT_YET_REALIZED_POST_PARENT_DESCENDANTS",
        "recompute_scope": "POST_J0_DESCENDANT_CONTINUATION_WITHIN_BOUND_HORIZON",
        "unrelated_structure_policy": "REPAIR_APPLICATION_MAY_CHANGE_ONLY_TARGET_AUTHORITY_STATUS",
        "old_lineage_reentry_policy": "DETECT_POST_REPAIR_TARGET_WRITE_RESTORING_PRE_REPAIR_AUTHORITY",
        "provider_internal_state_replayed": False,
        "semantic_success_not_predeclared": True,
    }
    plan["plan_hash"] = _hash_without(plan, "plan_hash")
    return plan


def build_repaired_parent_snapshot(*, parent_snapshot: Mapping[str, Any], plan: Mapping[str, Any]) -> tuple[dict, dict]:
    _require(plan.get("schema") == PLAN_SCHEMA, "r7_semantic_repair_runtime_plan_invalid")
    _require(plan.get("plan_hash") == _hash_without(plan, "plan_hash"), "r7_semantic_repair_runtime_plan_hash_mismatch")
    verify_state_snapshot(dict(parent_snapshot))
    _require(parent_snapshot.get("state_hash") == plan["common_reference_parent_state_hash"], "r7_repair_application_parent_hash_mismatch")

    key = plan["target_state_key"]
    from_status = plan["authority_from_status"]
    to_status = plan["authority_to_status"]
    parent_meta = copy.deepcopy((parent_snapshot.get("shared_state_metadata") or {}).get(key))
    _require(isinstance(parent_meta, dict), "r7_repair_application_target_metadata_missing")
    _require(parent_meta.get("status") == from_status, "r7_repair_application_from_status_mismatch")

    spec = {
        "type": "set_shared_state_status",
        "key": key,
        "status": to_status,
        "result_anchor_ref": f"r7_repair:{plan['packet_id']}:post_j0_parent",
    }
    repaired = apply_state_intervention(dict(parent_snapshot), spec)
    verify_state_snapshot(repaired)

    _require(repaired["state_hash"] != parent_snapshot["state_hash"], "r7_repair_application_state_hash_must_change")
    _require((repaired.get("shared_state") or {}) == (parent_snapshot.get("shared_state") or {}), "r7_repair_application_must_not_change_values")
    _require((repaired["shared_state_metadata"][key] or {}).get("status") == to_status, "r7_repair_application_to_status_missing")
    for meta_key, meta_value in parent_meta.items():
        if meta_key == "status":
            continue
        _require(repaired["shared_state_metadata"][key].get(meta_key) == meta_value, "r7_repair_application_target_metadata_drift:" + meta_key)

    for other_key in plan["preserved_parent_state_keys"]:
        _require(
            _state_cell_hash(repaired, other_key) == plan["preserved_parent_state_hashes"][other_key],
            "r7_repair_application_unrelated_state_drift:" + other_key,
        )

    for field in (
        "turns", "queue", "inboxes", "events", "final_state", "active_agents",
        "total_invocations", "late_event_delivered", "late_event_consumed",
        "terminated", "termination_reason", "message_ledger", "invocation_ledger",
        "execution_ledger",
    ):
        _require(repaired.get(field) == parent_snapshot.get(field), "r7_repair_application_runtime_field_drift:" + field)

    application = {
        "schema": REPAIR_APPLICATION_SCHEMA,
        "version": "0.1",
        "runtime_plan_hash": plan["plan_hash"],
        "packet_hash": plan["packet_hash"],
        "gate_hash": plan["gate_hash"],
        "repair_anchor_ref": plan["repair_anchor_ref"],
        "target_semantic_id": plan["target_semantic_id"],
        "target_state_key": key,
        "parent_state_hash": parent_snapshot["state_hash"],
        "repaired_parent_state_hash": repaired["state_hash"],
        "parent_turn": int(parent_snapshot["turns"]),
        "parent_event_count": len(parent_snapshot.get("events") or []),
        "from_status": from_status,
        "to_status": to_status,
        "target_value_hash_before": stable_hash((parent_snapshot.get("shared_state") or {}).get(key)),
        "target_value_hash_after": stable_hash((repaired.get("shared_state") or {}).get(key)),
        "changed_paths": [f"shared_state_metadata.{key}.status"],
        "direct_unrelated_parent_state_preserved": True,
        "post_parent_descendants_present_at_repair_time": False,
        "provider_internal_state_replayed": False,
    }
    application["repair_application_hash"] = stable_hash(application)
    return repaired, application


def verify_semantic_repair_trace(*, trace: Mapping[str, Any], plan: Mapping[str, Any], repair_application: Mapping[str, Any]) -> dict:
    _require(plan.get("schema") == PLAN_SCHEMA, "r7_semantic_repair_runtime_plan_invalid")
    _require(plan.get("plan_hash") == _hash_without(plan, "plan_hash"), "r7_semantic_repair_runtime_plan_hash_mismatch")
    _require(repair_application.get("schema") == REPAIR_APPLICATION_SCHEMA, "r7_repair_application_schema_invalid")
    app_material = copy.deepcopy(dict(repair_application))
    expected_app_hash = app_material.pop("repair_application_hash", None)
    _require(expected_app_hash == stable_hash(app_material), "r7_repair_application_hash_mismatch")
    _require(repair_application.get("runtime_plan_hash") == plan["plan_hash"], "r7_repair_application_plan_hash_mismatch")
    _require(repair_application.get("packet_hash") == plan["packet_hash"], "r7_repair_application_packet_hash_mismatch")
    _require(repair_application.get("direct_unrelated_parent_state_preserved") is True, "r7_repair_application_unrelated_surface_not_preserved")

    condition = trace.get("r7_condition") or {}
    _require(condition.get("branch_start_state_hash") == repair_application["repaired_parent_state_hash"], "r7_repair_trace_branch_start_hash_mismatch")
    _require(not [r for r in (trace.get("action_transform_records") or []) if r.get("experiment_origin") is True], "r7_direct_repair_must_not_use_action_transform")

    target_key = plan["target_state_key"]
    from_status = plan["authority_from_status"]
    parent_turn = int(plan["common_reference_parent_turn"])
    parent_event_count = int(plan["common_reference_parent_event_count"])

    recomputed_events = [
        event for event in (trace.get("events") or [])
        if int(event.get("event_index") or -1) >= parent_event_count
    ]
    recomputed_event_refs = ["arena_event:" + str(event.get("event_index")) for event in recomputed_events]
    reopened_model_calls = [
        call for call in (trace.get("model_calls") or [])
        if int(call.get("turn") or -1) > parent_turn
    ]

    old_lineage_reentry_refs = []
    post_repair_target_writes = []
    for event in recomputed_events:
        action = event.get("action") or {}
        if (
            event.get("realized_in_baseline")
            and event.get("action_type") == "write_state"
            and action.get("key") == target_key
        ):
            ref = "arena_event:" + str(event.get("event_index"))
            post_repair_target_writes.append({
                "event_ref": ref,
                "turn": event.get("turn"),
                "status": action.get("status"),
            })
            if action.get("status") == from_status:
                old_lineage_reentry_refs.append(ref)

    final_state = trace.get("final_state") or {}
    final_shared_state = final_state.get("state") if isinstance(final_state, Mapping) else {}
    final_metadata = final_state.get("state_metadata") if isinstance(final_state, Mapping) else {}
    if not isinstance(final_shared_state, Mapping):
        final_shared_state = {}
    if not isinstance(final_metadata, Mapping):
        final_metadata = {}

    post_recompute_unrelated_changed_keys = []
    for key, expected_hash in (plan.get("preserved_parent_state_hashes") or {}).items():
        observed_hash = stable_hash({
            "value": final_shared_state.get(key),
            "metadata": final_metadata.get(key),
        })
        if observed_hash != expected_hash:
            post_recompute_unrelated_changed_keys.append(key)

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
        "authority_status_after_repair": plan["authority_to_status"],
        "recomputed_event_refs": recomputed_event_refs,
        "post_repair_target_writes": post_repair_target_writes,
        "old_lineage_reentry_refs": old_lineage_reentry_refs,
        "direct_unrelated_parent_state_preserved": True,
    }

    row = {
        "schema": VERIFY_SCHEMA,
        "version": "0.2",
        "runtime_plan_hash": plan["plan_hash"],
        "repair_application_hash": repair_application["repair_application_hash"],
        "packet_hash": plan["packet_hash"],
        "gate_hash": plan["gate_hash"],
        "repair_anchor_ref": plan["repair_anchor_ref"],
        "target_semantic_id": plan["target_semantic_id"],
        "repair_boundary_turn": parent_turn,
        "repair_boundary_event_count": parent_event_count,
        "authority_state_repair_applied": True,
        "authority_transform_applied": False,
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
        "post_repair_target_writes": post_repair_target_writes,
        "preserved_unrelated_structure": True,
        "preservation_scope": "DIRECT_REPAIR_APPLICATION_SURFACE",
        "post_recompute_unrelated_changed_keys": post_recompute_unrelated_changed_keys,
        "old_lineage_reentry_refs": old_lineage_reentry_refs,
        "old_lineage_reentry_detected": bool(old_lineage_reentry_refs),
        "semantic_lineage_closure_before_hash": stable_hash(before_closure),
        "semantic_lineage_closure_after_hash": stable_hash(after_closure),
        "target_integrity_repair_executed": True,
        "recovery_success_semantic_status": "NOT_ADJUDICATED",
        "terminal_outcome_is_primary": False,
        "interpretation_boundary": (
            "Runtime verification proves that the frozen post-J0 parent was locally repaired before continuation, "
            "that unrelated parent-state cells were not directly mutated, and that downstream re-entry/recomputation were recorded. "
            "Post-recompute changes outside the target are descriptive downstream consequences, not automatically repair collateral. "
            "This record does not adjudicate semantic CPR or recovery efficacy."
        ),
    }
    row["verification_hash"] = stable_hash(row)
    return row
