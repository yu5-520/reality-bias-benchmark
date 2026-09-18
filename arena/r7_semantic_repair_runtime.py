from __future__ import annotations

import copy
from typing import Any, Mapping

from .core import stable_hash
from .experimental_control import verify_state_snapshot
from .r7_lineage_monitoring import build_post_repair_watch_contract, evaluate_post_repair_watch

# R7 v5.3 validation marker: repository-native offline chain must pass before subject redispatch.
PLAN_SCHEMA = "RB-R7-SEMANTIC-REPAIR-RUNTIME-PLAN-v0.3"
REPAIR_APPLICATION_SCHEMA = "RB-R7-SEMANTIC-REPAIR-APPLICATION-v0.2"
VERIFY_SCHEMA = "RB-R7-SEMANTIC-REPAIR-VERIFICATION-v0.4"

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


def _anchor_event_index(repair_anchor_ref: str) -> int:
    parts = str(repair_anchor_ref).split(":")
    _require(len(parts) >= 2 and parts[0] == "arena_event", "r7_repair_anchor_ref_invalid")
    try:
        idx = int(parts[1])
    except Exception as exc:
        raise ValueError("r7_repair_anchor_event_index_invalid") from exc
    _require(idx >= 0, "r7_repair_anchor_event_index_negative")
    return idx


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
    anchor_index = _anchor_event_index(str(packet.get("repair_anchor_ref")))

    _require(packet.get("target_semantic_id"), "r7_target_semantic_id_required")
    _require(packet.get("repair_closure_refs"), "r7_repair_closure_required")
    _require(packet.get("evidence_supported_affected_closure_refs"), "r7_affected_closure_required")
    _require(parent["state_hash"] == alr["common_reference_parent_state_hash"], "r7_repair_parent_hash_mismatch")
    _require(checkpoint["state_hash"] == alr["recovery_checkpoint_state_hash"], "r7_repair_checkpoint_hash_mismatch")
    _require(target_state_key in (parent.get("shared_state") or {}), "r7_repair_target_value_missing_from_parent")
    _require(target_state_key in (parent.get("shared_state_metadata") or {}), "r7_repair_target_metadata_missing_from_parent")
    _require((parent["shared_state_metadata"][target_state_key] or {}).get("status") == from_status, "r7_repair_parent_authority_status_mismatch")
    _require(parent.get("terminated") is False, "r7_repair_parent_terminal")
    events = list(parent.get("events") or [])
    _require(anchor_index < len(events), "r7_repair_anchor_outside_parent")
    anchor = events[anchor_index]
    _require(anchor.get("event_index") == anchor_index, "r7_repair_anchor_event_identity_mismatch")
    _require(anchor.get("action_type") == "write_state", "r7_repair_anchor_must_be_write_state")
    _require((anchor.get("action") or {}).get("key") == target_state_key, "r7_repair_anchor_target_key_mismatch")

    invalidated_events = [e for e in events if int(e.get("event_index", -1)) > anchor_index]
    invalidated_event_refs = ["arena_event:" + str(e["event_index"]) for e in invalidated_events]
    affected_message_ids: list[str] = []
    affected_invocation_ids: list[str] = []
    dependent_agents: list[str] = []
    for event in invalidated_events:
        action = event.get("action") or {}
        if event.get("action_type") == "message":
            if action.get("message_id"):
                affected_message_ids.append(str(action["message_id"]))
            if action.get("to"):
                dependent_agents.append(str(action["to"]))
        elif event.get("action_type") == "invoke_agent":
            if action.get("invocation_id"):
                affected_invocation_ids.append(str(action["invocation_id"]))
            if action.get("agent_id"):
                dependent_agents.append(str(action["agent_id"]))

    preserved_state_keys = sorted(key for key in (parent.get("shared_state") or {}) if key != target_state_key)
    preserved_anchor_state_hashes = {
        key: stable_hash({
            "value": (anchor.get("shared_state_after") or {}).get(key),
            "metadata": (anchor.get("shared_state_metadata_after") or {}).get(key),
        })
        for key in preserved_state_keys
    }

    plan = {
        "schema": PLAN_SCHEMA,
        "version": "0.3",
        "packet_id": packet["packet_id"],
        "packet_hash": packet.get("packet_hash"),
        "gate_id": gate["gate_id"],
        "gate_hash": gate.get("gate_hash"),
        "repair_anchor_ref": packet["repair_anchor_ref"],
        "repair_anchor_event_index": anchor_index,
        "target_semantic_id": packet["target_semantic_id"],
        "content_address": packet["content_address"],
        "target_state_key": target_state_key,
        "authority_from_status": from_status,
        "authority_to_status": to_status,
        "common_reference_parent_state_hash": parent["state_hash"],
        "common_reference_parent_turn": int(parent["turns"]),
        "common_reference_parent_event_count": len(events),
        "historical_pre_anchor_checkpoint_state_hash": checkpoint["state_hash"],
        "repair_branch_start_event_count": anchor_index + 1,
        "invalidated_post_anchor_event_refs": invalidated_event_refs,
        "invalidated_post_anchor_message_ids": sorted(set(affected_message_ids)),
        "invalidated_post_anchor_invocation_ids": sorted(set(affected_invocation_ids)),
        "dependent_reopen_agent_ids": sorted(set(dependent_agents)),
        "repair_closure_refs": list(packet["repair_closure_refs"]),
        "affected_closure_refs": list(packet["evidence_supported_affected_closure_refs"]),
        "mechanically_required_replay_refs": list(packet.get("mechanically_required_replay_refs") or []),
        "preserved_unrelated_refs": list(packet.get("preserved_unrelated_refs") or []),
        "preserved_anchor_state_keys": preserved_state_keys,
        "preserved_anchor_state_hashes": preserved_anchor_state_hashes,
        "operation_bindings": {
            "AUTHORITY_DOWNGRADE": "REVISE_TARGET_AUTHORITY_AT_FROZEN_REPAIR_ANCHOR",
            "POOL_INVALIDATION": "REMOVE_POST_ANCHOR_POOL_MATERIALIZATIONS_FROM_BRANCH_START",
            "DESCENDANT_INVALIDATION": "TRUNCATE_POST_ANCHOR_EVENTS_AND_REMOVE_THEIR_PENDING_MESSAGES_INVOCATIONS",
            "DEPENDENT_DECISION_REOPEN": "REQUEUE_RECIPIENTS_OF_INVALIDATED_POST_ANCHOR_HANDOFFS",
            "SELECTIVE_RECOMPUTE": "RECOMPUTE_FROM_REPAIRED_ANCHOR_WITHIN_FROZEN_COMMON_HORIZON",
        },
        "invalidation_scope": "POST_ANCHOR_DESCENDANTS_PRESENT_IN_FROZEN_PARENT",
        "recompute_scope": "REOPENED_POST_ANCHOR_CONTINUATION_WITHIN_BOUND_HORIZON",
        "unrelated_structure_policy": "PRESERVE_ANCHOR_STATE_CELLS_OUTSIDE_TARGET_AND_EXPLICITLY_RECORD_STRUCTURAL_INVALIDATION",
        "old_lineage_reentry_policy": "DETECT_POST_REPAIR_TARGET_WRITE_RESTORING_PRE_REPAIR_AUTHORITY",
        "provider_internal_state_replayed": False,
        "semantic_success_not_predeclared": True,
    }
    plan["plan_hash"] = _hash_without(plan, "plan_hash")
    return plan


def build_repaired_parent_snapshot(*, parent_snapshot: Mapping[str, Any], plan: Mapping[str, Any]) -> tuple[dict, dict]:
    _require(plan.get("schema") == PLAN_SCHEMA, "r7_semantic_repair_runtime_plan_invalid")
    _require(plan.get("plan_hash") == _hash_without(plan, "plan_hash"), "r7_semantic_repair_runtime_plan_hash_mismatch")
    parent = copy.deepcopy(dict(parent_snapshot))
    verify_state_snapshot(parent)
    _require(parent.get("state_hash") == plan["common_reference_parent_state_hash"], "r7_repair_application_parent_hash_mismatch")

    anchor_index = int(plan["repair_anchor_event_index"])
    anchor = parent["events"][anchor_index]
    key = plan["target_state_key"]
    from_status = plan["authority_from_status"]
    to_status = plan["authority_to_status"]
    anchor_after_state = copy.deepcopy(anchor.get("shared_state_after") or {})
    anchor_after_meta = copy.deepcopy(anchor.get("shared_state_metadata_after") or {})
    _require(key in anchor_after_state and key in anchor_after_meta, "r7_repair_application_anchor_target_missing")
    _require(anchor_after_meta[key].get("status") == from_status, "r7_repair_application_from_status_mismatch")

    repaired = copy.deepcopy(parent)
    repaired["shared_state"] = anchor_after_state
    repaired["shared_state_metadata"] = anchor_after_meta
    repaired["shared_state_metadata"][key]["status"] = to_status
    repaired["final_state"] = copy.deepcopy(anchor.get("final_state_after"))
    repaired["active_agents"] = copy.deepcopy(anchor.get("active_agents_after") or parent.get("active_agents") or [])
    repaired["events"] = copy.deepcopy(parent["events"][: anchor_index + 1])

    invalid_message_ids = set(plan.get("invalidated_post_anchor_message_ids") or [])
    invalid_invocation_ids = set(plan.get("invalidated_post_anchor_invocation_ids") or [])
    repaired["message_ledger"] = [
        copy.deepcopy(row) for row in (parent.get("message_ledger") or [])
        if row.get("message_id") not in invalid_message_ids
    ]
    repaired["invocation_ledger"] = [
        copy.deepcopy(row) for row in (parent.get("invocation_ledger") or [])
        if row.get("invocation_id") not in invalid_invocation_ids
    ]
    repaired["inboxes"] = {}
    for agent_id, items in (parent.get("inboxes") or {}).items():
        cleaned = []
        for raw in items:
            if raw.get("_message_id") in invalid_message_ids:
                continue
            if raw.get("_invocation_id") in invalid_invocation_ids:
                continue
            cleaned.append(copy.deepcopy(raw))
        repaired["inboxes"][agent_id] = cleaned

    queue_after_anchor = list(anchor.get("queue_after") or [])
    reopened = list(plan.get("dependent_reopen_agent_ids") or [])
    new_queue: list[str] = []
    for agent_id in queue_after_anchor + reopened:
        if agent_id and agent_id not in new_queue:
            new_queue.append(agent_id)
    _require(new_queue, "r7_repair_application_no_dependent_agent_to_reopen")
    repaired["queue"] = new_queue

    repaired["total_invocations"] = sum(1 for row in repaired["invocation_ledger"] if row.get("queued"))
    valid_finalize = [e for e in repaired["events"] if e.get("action_type") == "finalize" and e.get("realized_in_baseline")]
    repaired["last_finalizer"] = valid_finalize[-1].get("actor") if valid_finalize else None
    repaired["terminated"] = False
    repaired["termination_reason"] = None
    repaired["anchor_ref"] = f"r7_repair:{plan['packet_id']}:after_anchor_event:{anchor_index}"
    repaired["state_hash"] = _hash_without(repaired, "state_hash")
    verify_state_snapshot(repaired)

    _require((repaired.get("shared_state") or {}).get(key) == (anchor.get("shared_state_after") or {}).get(key), "r7_repair_application_must_not_change_target_value")
    _require(repaired["shared_state_metadata"][key].get("status") == to_status, "r7_repair_application_to_status_missing")
    for meta_key, meta_value in (anchor.get("shared_state_metadata_after") or {}).get(key, {}).items():
        if meta_key == "status":
            continue
        _require(repaired["shared_state_metadata"][key].get(meta_key) == meta_value, "r7_repair_application_target_metadata_drift:" + meta_key)

    for other_key in plan["preserved_anchor_state_keys"]:
        observed = stable_hash({
            "value": repaired["shared_state"].get(other_key),
            "metadata": repaired["shared_state_metadata"].get(other_key),
        })
        _require(observed == plan["preserved_anchor_state_hashes"][other_key], "r7_repair_application_unrelated_state_drift:" + other_key)

    _require(len(repaired["events"]) == plan["repair_branch_start_event_count"], "r7_repair_application_event_truncation_mismatch")
    _require(not any(row.get("message_id") in invalid_message_ids for row in repaired["message_ledger"]), "r7_repair_application_invalidated_message_still_in_ledger")
    for items in repaired["inboxes"].values():
        _require(not any(raw.get("_message_id") in invalid_message_ids for raw in items), "r7_repair_application_invalidated_message_still_in_inbox")

    application = {
        "schema": REPAIR_APPLICATION_SCHEMA,
        "version": "0.2",
        "runtime_plan_hash": plan["plan_hash"],
        "packet_hash": plan["packet_hash"],
        "gate_hash": plan["gate_hash"],
        "repair_anchor_ref": plan["repair_anchor_ref"],
        "repair_anchor_event_index": anchor_index,
        "target_semantic_id": plan["target_semantic_id"],
        "target_state_key": key,
        "parent_state_hash": parent["state_hash"],
        "repaired_parent_state_hash": repaired["state_hash"],
        "parent_turn": int(parent["turns"]),
        "parent_event_count": len(parent.get("events") or []),
        "repaired_branch_start_event_count": len(repaired["events"]),
        "from_status": from_status,
        "to_status": to_status,
        "target_value_hash_before": stable_hash((anchor.get("shared_state_after") or {}).get(key)),
        "target_value_hash_after": stable_hash((repaired.get("shared_state") or {}).get(key)),
        "changed_paths": [f"shared_state_metadata.{key}.status"],
        "invalidated_event_refs": list(plan["invalidated_post_anchor_event_refs"]),
        "invalidated_message_ids": list(plan["invalidated_post_anchor_message_ids"]),
        "invalidated_invocation_ids": list(plan["invalidated_post_anchor_invocation_ids"]),
        "reopened_agent_ids": list(reopened),
        "direct_unrelated_anchor_state_preserved": True,
        "post_anchor_descendants_invalidated": True,
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
    _require(repair_application.get("direct_unrelated_anchor_state_preserved") is True, "r7_repair_application_unrelated_surface_not_preserved")
    _require(repair_application.get("post_anchor_descendants_invalidated") is True, "r7_repair_application_descendants_not_invalidated")

    condition = trace.get("r7_condition") or {}
    _require(condition.get("branch_start_state_hash") == repair_application["repaired_parent_state_hash"], "r7_repair_trace_branch_start_hash_mismatch")
    _require(not [r for r in (trace.get("action_transform_records") or []) if r.get("experiment_origin") is True], "r7_direct_repair_must_not_use_action_transform")

    target_key = plan["target_state_key"]
    from_status = plan["authority_from_status"]
    branch_start_event_count = int(repair_application["repaired_branch_start_event_count"])

    recomputed_events = [
        event for event in (trace.get("events") or [])
        if int(event.get("event_index") or -1) >= branch_start_event_count
    ]
    recomputed_event_refs = ["arena_event:" + str(event.get("event_index")) for event in recomputed_events]
    reopened_model_calls = [
        call for call in (trace.get("model_calls") or [])
        if int(call.get("turn") or -1) > int(plan["common_reference_parent_turn"])
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
    for key, expected_hash in (plan.get("preserved_anchor_state_hashes") or {}).items():
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
        "invalidated_post_anchor_event_refs": list(plan["invalidated_post_anchor_event_refs"]),
    }
    after_closure = {
        "repair_closure_refs": list(plan["repair_closure_refs"]),
        "affected_closure_refs": list(plan["affected_closure_refs"]),
        "target_state_key": target_key,
        "authority_status_after_repair": plan["authority_to_status"],
        "recomputed_event_refs": recomputed_event_refs,
        "post_repair_target_writes": post_repair_target_writes,
        "old_lineage_reentry_refs": old_lineage_reentry_refs,
        "direct_unrelated_anchor_state_preserved": True,
    }

    watch_contract = build_post_repair_watch_contract(runtime_plan=plan, repair_application=repair_application)
    watch_result = evaluate_post_repair_watch(trace=trace, contract=watch_contract)

    row = {
        "schema": VERIFY_SCHEMA,
        "version": "0.4",
        "runtime_plan_hash": plan["plan_hash"],
        "repair_application_hash": repair_application["repair_application_hash"],
        "packet_hash": plan["packet_hash"],
        "gate_hash": plan["gate_hash"],
        "repair_anchor_ref": plan["repair_anchor_ref"],
        "target_semantic_id": plan["target_semantic_id"],
        "repair_anchor_event_index": plan["repair_anchor_event_index"],
        "repair_branch_start_event_count": branch_start_event_count,
        "authority_state_repair_applied": True,
        "authority_transform_applied": False,
        "pool_invalidation_method": plan["operation_bindings"]["POOL_INVALIDATION"],
        "descendant_invalidation_method": plan["operation_bindings"]["DESCENDANT_INVALIDATION"],
        "dependent_decision_reopen_method": plan["operation_bindings"]["DEPENDENT_DECISION_REOPEN"],
        "selective_recompute_method": plan["operation_bindings"]["SELECTIVE_RECOMPUTE"],
        "repair_closure_invalidated_at_branch_start": True,
        "invalidated_event_refs": list(repair_application["invalidated_event_refs"]),
        "invalidated_message_ids": list(repair_application["invalidated_message_ids"]),
        "reopened_agent_ids": list(repair_application["reopened_agent_ids"]),
        "reopened_model_call_refs": [
            "turn:" + str(call.get("turn")) + ":agent:" + str(call.get("agent_id"))
            for call in reopened_model_calls
        ],
        "recomputed_descendant_refs": recomputed_event_refs,
        "post_repair_target_writes": post_repair_target_writes,
        "preserved_unrelated_structure": True,
        "preservation_scope": "DIRECT_REPAIR_APPLICATION_AT_ANCHOR",
        "post_recompute_unrelated_changed_keys": post_recompute_unrelated_changed_keys,
        "old_lineage_reentry_refs": old_lineage_reentry_refs,
        "old_lineage_reentry_detected": bool(old_lineage_reentry_refs),
        "semantic_lineage_closure_before_hash": stable_hash(before_closure),
        "semantic_lineage_closure_after_hash": stable_hash(after_closure),
        "target_integrity_repair_executed": True,
        "post_repair_watch_contract": watch_contract,
        "post_repair_watch_result": watch_result,
        "post_repair_watch_contract_hash": watch_contract["watch_hash"],
        "post_repair_watch_result_hash": watch_result["watch_result_hash"],
        "recovery_success_semantic_status": "NOT_ADJUDICATED",
        "terminal_outcome_is_primary": False,
        "interpretation_boundary": (
            "Runtime verification proves deterministic repair at the frozen anchor, explicit invalidation of post-anchor descendants already present in the parent, "
            "reopening of their dependent recipients, and recording of recomputed descendants/re-entry. "
            "Downstream state changes after recomputation are descriptive consequences and are not automatically classified as direct repair collateral. "
            "This record does not adjudicate semantic CPR or recovery efficacy."
        ),
    }
    row["verification_hash"] = stable_hash(row)
    return row
