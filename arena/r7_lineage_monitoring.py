from __future__ import annotations

from typing import Any, Mapping

from .core import stable_hash

LINEAGE_PACKAGE_SCHEMA = "RB-R7-SEMANTIC-LINEAGE-PACKAGE-v0.1"
WATCH_CONTRACT_SCHEMA = "RB-R7-POST-REPAIR-WATCH-CONTRACT-v0.1"
WATCH_RESULT_SCHEMA = "RB-R7-POST-REPAIR-WATCH-RESULT-v0.1"
OBSERVATION_SCHEMA = "RB-R7-FULL-LINEAGE-OBSERVATION-v0.1"


def _hash_without(row: Mapping[str, Any], key: str) -> str:
    material = dict(row)
    material.pop(key, None)
    return stable_hash(material)


def build_semantic_lineage_package(*, packet: Mapping[str, Any], runtime_plan: Mapping[str, Any]) -> dict[str, Any]:
    pre_anchor = []
    for ref in list(packet.get("evidence_supported_affected_closure_refs") or []):
        if ref not in runtime_plan.get("invalidated_post_anchor_event_refs", []):
            pre_anchor.append(ref)
    row = {
        "schema": LINEAGE_PACKAGE_SCHEMA,
        "package_id": str(packet["packet_id"]) + ":r7-lineage-package:v0.1",
        "repair_anchor_ref": packet["repair_anchor_ref"],
        "target_semantic_id": packet["target_semantic_id"],
        "content_address": packet["content_address"],
        "source_refs": [r for r in list(packet.get("raw_evidence_refs") or [])],
        "transformation_refs": [],
        "authority_refs": [packet["repair_anchor_ref"] + ":authority"],
        "pool_refs": [r for r in list(packet.get("evidence_supported_affected_closure_refs") or []) if "pool" in r.lower()],
        "descendant_candidate_refs": list(dict.fromkeys(list(packet.get("evidence_supported_affected_closure_refs") or []) + list(runtime_plan.get("invalidated_post_anchor_event_refs") or []))),
        "affected_closure_refs": list(packet.get("evidence_supported_affected_closure_refs") or []),
        "repair_closure_refs": list(packet.get("repair_closure_refs") or []),
        "machine_disposition": {
            "invalidated_post_anchor_refs": list(runtime_plan.get("invalidated_post_anchor_event_refs") or []),
            "preserved_pre_anchor_lineage_refs": pre_anchor,
            "unresolved_semantic_compatibility_refs": list(packet.get("evidence_supported_affected_closure_refs") or []),
        },
        "semantic_disposition_status": "DEFERRED_NOT_ADJUDICATED",
        "observation_policy": "FULL_LINEAGE_ALL_ARMS",
    }
    row["package_hash"] = _hash_without(row, "package_hash")
    return row


def build_post_repair_watch_contract(*, runtime_plan: Mapping[str, Any], repair_application: Mapping[str, Any]) -> dict[str, Any]:
    row = {
        "schema": WATCH_CONTRACT_SCHEMA,
        "watch_id": str(runtime_plan["packet_id"]) + ":post-repair-watch:v0.1",
        "repair_anchor_ref": runtime_plan["repair_anchor_ref"],
        "target_semantic_id": runtime_plan["target_semantic_id"],
        "target_state_key": runtime_plan["target_state_key"],
        "old_authority_status": runtime_plan["authority_from_status"],
        "new_authority_status": runtime_plan["authority_to_status"],
        "repair_branch_start_event_count": int(repair_application["repaired_branch_start_event_count"]),
        "monitoring_intensity": "HIGH_AFTER_REPAIR",
        "watch_triggers": [
            "EXACT_OLD_AUTHORITY_REENTRY",
            "TARGET_REWRITE",
            "NEW_STATE_WRITE",
            "AUTHORITY_ESCALATION_CANDIDATE",
            "CLOSURE_EXPANSION_CANDIDATE",
        ],
        "semantic_cpr_status": "NOT_ADJUDICATED",
    }
    row["watch_hash"] = _hash_without(row, "watch_hash")
    return row


def build_full_lineage_observation(*, trace: Mapping[str, Any], arm_id: str, anchor_event_index: int, branch_start_event_count: int, target_state_key: str) -> dict[str, Any]:
    inherited, prospective, writes, messages, invokes, actors = [], [], [], [], [], []
    for event in trace.get("events") or []:
        idx = int(event.get("event_index", -1))
        if idx <= anchor_event_index:
            continue
        ref = f"arena_event:{idx}"
        (inherited if idx < branch_start_event_count else prospective).append(ref)
        actor = event.get("actor")
        if actor and actor not in actors:
            actors.append(actor)
        action = event.get("action") or {}
        if event.get("action_type") == "write_state":
            writes.append({"event_ref": ref, "key": action.get("key"), "status": action.get("status"), "target_write": action.get("key") == target_state_key})
        elif event.get("action_type") == "message":
            messages.append({"event_ref": ref, "to": action.get("to"), "message_id": action.get("message_id")})
        elif event.get("action_type") == "invoke_agent":
            invokes.append({"event_ref": ref, "agent_id": action.get("agent_id"), "invocation_id": action.get("invocation_id")})
    row = {
        "schema": OBSERVATION_SCHEMA,
        "arm_id": arm_id,
        "anchor_event_index": anchor_event_index,
        "branch_start_event_count": branch_start_event_count,
        "inherited_post_anchor_refs": inherited,
        "prospective_event_refs": prospective,
        "state_writes": writes,
        "message_events": messages,
        "invocation_events": invokes,
        "actors": actors,
        "model_call_refs": [f"turn:{c.get('turn')}:agent:{c.get('agent_id')}" for c in trace.get("model_calls") or []],
        "runtime_exposure_count": len([r for r in trace.get("runtime_transform_records") or [] if r.get("experiment_origin") is True]),
        "semantic_cpr_status": "NOT_ADJUDICATED",
    }
    row["observation_hash"] = _hash_without(row, "observation_hash")
    return row


def evaluate_post_repair_watch(*, trace: Mapping[str, Any], contract: Mapping[str, Any]) -> dict[str, Any]:
    start = int(contract["repair_branch_start_event_count"])
    target = contract["target_state_key"]
    old = contract["old_authority_status"]
    exact_reentry, target_writes, new_writes, authority_candidates = [], [], [], []
    for event in trace.get("events") or []:
        idx = int(event.get("event_index", -1))
        if idx < start or not event.get("realized_in_baseline", True):
            continue
        action = event.get("action") or {}
        if event.get("action_type") != "write_state":
            continue
        ref = f"arena_event:{idx}"
        item = {"event_ref": ref, "key": action.get("key"), "status": action.get("status")}
        new_writes.append(item)
        if action.get("key") == target:
            target_writes.append(item)
            if action.get("status") == old:
                exact_reentry.append(ref)
        if action.get("status") == "fact":
            authority_candidates.append(item)
    row = {
        "schema": WATCH_RESULT_SCHEMA,
        "watch_contract_hash": contract["watch_hash"],
        "exact_old_authority_reentry_refs": exact_reentry,
        "target_write_events": target_writes,
        "new_state_write_events": new_writes,
        "authority_escalation_candidates": authority_candidates,
        "closure_expansion_candidate_refs": [x["event_ref"] for x in new_writes if x.get("key") != target],
        "watch_status": "REVIEW_REQUIRED" if exact_reentry or authority_candidates else "STABLE_WITHIN_OBSERVED_HORIZON",
        "semantic_cpr_status": "NOT_ADJUDICATED",
    }
    row["watch_result_hash"] = _hash_without(row, "watch_result_hash")
    return row
