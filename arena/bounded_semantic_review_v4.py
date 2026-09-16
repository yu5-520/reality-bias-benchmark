from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Iterable, Mapping

from .system_behavior import content_hash, load_json
from .system_behavior_dynamics_v4 import NOT_ADJUDICATED


REVIEW_CONTRACT_SCHEMA = "RB-SEMANTIC-AUTHORITY-REVIEW-CONTRACT-v0.1"
PACKET_SCHEMA = "RB-BOUNDED-SEMANTIC-REVIEW-PACKET-v0.1"
REVIEW_RECORD_SCHEMA = "RB-SEMANTIC-AUTHORITY-REVIEW-RECORD-v0.1"


class BoundedSemanticReviewError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BoundedSemanticReviewError(message)


def _hash_without(record: Mapping[str, Any], key: str) -> str:
    material = copy.deepcopy(dict(record))
    material.pop(key, None)
    return content_hash(material)


def load_review_contract(
    path: str | Path = "configs/semantic_authority_review_contract_v0.1.json",
) -> dict[str, Any]:
    contract = load_json(path)
    validate_review_contract(contract)
    return contract


def validate_review_contract(contract: Mapping[str, Any]) -> bool:
    _require(contract.get("schema") == REVIEW_CONTRACT_SCHEMA, "review_contract_schema_invalid")
    _require(contract.get("version") == "0.1", "review_contract_version_invalid")
    bounds = contract.get("packet_bounds") or {}
    for key in (
        "max_behavior_events",
        "max_lineage_relations",
        "max_operational_crossings",
        "max_source_model_calls",
        "max_allowed_expansion_refs",
    ):
        _require(isinstance(bounds.get(key), int) and bounds[key] >= 0, f"review_bound_invalid:{key}")
    enums = contract.get("output_enums") or {}
    for key in (
        "jump_semantic_class",
        "semantic_adoption",
        "decision_effect",
        "authority_penetration",
        "retrospective_outcome",
        "evidence_sufficiency",
    ):
        _require(isinstance(enums.get(key), list) and enums[key], f"review_enum_required:{key}")
    return True


def _behavior_by_id(adapter_result: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for row in adapter_result.get("behavior_events") or []:
        event_id = row.get("behavior_event_id")
        if isinstance(event_id, str):
            out[event_id] = dict(row)
    return out


def _source_event_by_index(source_trace: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    out = {}
    for offset, row in enumerate(source_trace.get("events") or []):
        index = row.get("event_index")
        if not isinstance(index, int):
            index = offset
        out[index] = dict(row)
    return out


def _source_event_index(behavior_event: Mapping[str, Any]) -> int | None:
    value = (behavior_event.get("structured_diff") or {}).get("source_event_index")
    return value if isinstance(value, int) else None


def _call_index_for_source_event(source_trace: Mapping[str, Any], source_event_index: int) -> int | None:
    for index, call in enumerate(source_trace.get("model_calls") or []):
        start = call.get("event_index_start")
        end = call.get("event_index_end")
        if isinstance(start, int) and isinstance(end, int) and start <= source_event_index < end:
            return index
    return None


def _visible_input(call: Mapping[str, Any]) -> dict[str, Any]:
    runtime = call.get("runtime_snapshot") or {}
    keep = (
        "shared_state",
        "shared_state_metadata",
        "final_state",
        "inbox",
        "active_agents",
        "queue",
        "remaining_turn_budget",
    )
    return {key: copy.deepcopy(runtime.get(key)) for key in keep if key in runtime}


def _compact_call(source_trace: Mapping[str, Any], index: int) -> dict[str, Any]:
    call = (source_trace.get("model_calls") or [])[index]
    return {
        "source_ref": f"model_call:{index}",
        "agent_id": call.get("agent_id"),
        "turn": call.get("turn"),
        "status": call.get("status"),
        "event_index_start": call.get("event_index_start"),
        "event_index_end": call.get("event_index_end"),
        "input_message_ids": list(call.get("input_message_ids") or []),
        "input_invocation_ids": list(call.get("input_invocation_ids") or []),
        "visible_input": _visible_input(call),
        "decision_summary": call.get("decision_summary"),
        "raw_output": call.get("raw_content"),
        "note": "Visible source-call input/output only; not hidden chain-of-thought.",
    }


def _compact_source_event(index: int, row: Mapping[str, Any]) -> dict[str, Any]:
    keep = (
        "event_index",
        "turn",
        "actor",
        "action_type",
        "authority_class",
        "realized_in_baseline",
        "action",
        "note",
        "shared_state_before",
        "shared_state_after",
        "shared_state_metadata_before",
        "shared_state_metadata_after",
        "final_state_before",
        "final_state_after",
    )
    out = {key: copy.deepcopy(row.get(key)) for key in keep if key in row}
    out["source_ref"] = f"arena_event:{index}"
    return out


def _agent_contracts(domain: Mapping[str, Any] | None, actor_ids: Iterable[str]) -> list[dict[str, Any]]:
    if not isinstance(domain, Mapping):
        return []
    wanted = set(actor_ids)
    return [
        {
            "agent_id": row.get("id"),
            "role": row.get("role"),
            "responsibility": row.get("responsibility"),
        }
        for row in domain.get("agents") or []
        if row.get("id") in wanted
    ]


def _task_contract(domain: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(domain, Mapping):
        return {"status": "NOT_PROVIDED"}
    task = domain.get("task") or {}
    return {
        "domain_id": domain.get("domain_id"),
        "goal": copy.deepcopy(task.get("goal")),
        "public_context": copy.deepcopy(task.get("public_context")),
        "initial_shared_state": copy.deepcopy(task.get("initial_shared_state")),
        "late_event": copy.deepcopy(task.get("late_event")),
    }


def _prioritized_event_ids(
    root_id: str,
    descendants: list[str],
    event_by_id: Mapping[str, Mapping[str, Any]],
    crossing_event_ids: set[str],
) -> list[str]:
    ordered: list[str] = []

    def add(event_id: str) -> None:
        if event_id in event_by_id and event_id not in ordered:
            ordered.append(event_id)

    add(root_id)
    for event_id in descendants:
        if event_id in crossing_event_ids:
            add(event_id)
    for event_id in descendants:
        if (event_by_id.get(event_id) or {}).get("boundary_id") == "AGENT_TURN":
            add(event_id)
    for event_id in descendants:
        if (event_by_id.get(event_id) or {}).get("action_type") in {"write", "invoke", "revise", "finalize"}:
            add(event_id)
    for event_id in descendants:
        add(event_id)
    return ordered


def _packet_for_candidate(
    *,
    source_trace: Mapping[str, Any],
    adapter_result: Mapping[str, Any],
    dynamics_view: Mapping[str, Any],
    lineage_view: Mapping[str, Any],
    candidate: Mapping[str, Any],
    candidate_metrics: Mapping[str, Any],
    contract: Mapping[str, Any],
    domain: Mapping[str, Any] | None,
    evidence_batch_hash: str | None,
    v4_research_binding_hash: str | None,
) -> dict[str, Any]:
    event_by_id = _behavior_by_id(adapter_result)
    source_events = _source_event_by_index(source_trace)
    root_id = candidate["behavior_event_id"]
    root = event_by_id.get(root_id)
    _require(root is not None, f"review_root_behavior_event_missing:{root_id}")

    descendants = list(candidate_metrics.get("descendant_behavior_event_ids") or [])
    relevant_ids = {root_id, *descendants}
    all_relations = [
        row
        for row in lineage_view.get("lineage_relations") or []
        if row.get("source_behavior_event_id") in relevant_ids
        and row.get("target_behavior_event_id") in relevant_ids
    ]
    exact_crossings = [
        row
        for row in dynamics_view.get("operational_crossings") or []
        if row.get("behavior_event_id") in relevant_ids
    ]
    crossing_event_ids = {row["behavior_event_id"] for row in exact_crossings}

    bounds = contract["packet_bounds"]
    ordered_ids = _prioritized_event_ids(root_id, descendants, event_by_id, crossing_event_ids)
    selected_ids = ordered_ids[: bounds["max_behavior_events"]]
    selected_set = set(selected_ids)

    selected_relations = [
        row
        for row in all_relations
        if row.get("source_behavior_event_id") in selected_set
        and row.get("target_behavior_event_id") in selected_set
    ][: bounds["max_lineage_relations"]]
    selected_crossings = [
        row for row in exact_crossings if row.get("behavior_event_id") in selected_set
    ][: bounds["max_operational_crossings"]]
    operational_events = [
        event_by_id[row["behavior_event_id"]]
        for row in selected_crossings
        if row.get("behavior_event_id") in event_by_id
    ]

    retrospective_events = [
        event_by_id[event_id]
        for event_id in selected_ids
        if event_by_id[event_id].get("boundary_id") == "FINAL_REOPEN"
        and event_by_id[event_id].get("action_type") == "revise"
        and int(event_by_id[event_id].get("event_index", -1)) > int(root.get("event_index", -1))
    ]

    source_indices: list[int] = []
    for event_id in selected_ids:
        source_index = _source_event_index(event_by_id[event_id])
        if isinstance(source_index, int) and source_index not in source_indices:
            source_indices.append(source_index)
    compact_source_events = [
        _compact_source_event(index, source_events[index])
        for index in source_indices
        if index in source_events
    ]

    call_indices: list[int] = []
    for source_index in source_indices:
        call_index = _call_index_for_source_event(source_trace, source_index)
        if isinstance(call_index, int) and call_index not in call_indices:
            call_indices.append(call_index)
    call_indices = call_indices[: bounds["max_source_model_calls"]]
    source_calls = [_compact_call(source_trace, index) for index in call_indices]

    actor_ids = sorted(
        {
            str(event_by_id[event_id].get("actor"))
            for event_id in selected_ids
            if event_by_id[event_id].get("actor") not in (None, "ENVIRONMENT")
        }
    )

    omitted_event_ids = [event_id for event_id in ordered_ids if event_id not in selected_set]
    selected_relation_ids = {row.get("relation_id") for row in selected_relations}
    omitted_relation_ids = [
        row.get("relation_id")
        for row in all_relations
        if row.get("relation_id") not in selected_relation_ids
    ]
    selected_crossing_ids = {row.get("crossing_id") for row in selected_crossings}
    omitted_crossing_ids = [
        row.get("crossing_id")
        for row in exact_crossings
        if row.get("crossing_id") not in selected_crossing_ids
    ]
    expansion_refs: list[str] = []
    for ref in [*omitted_event_ids, *omitted_relation_ids, *omitted_crossing_ids]:
        if isinstance(ref, str) and ref not in expansion_refs:
            expansion_refs.append(ref)
    expansion_refs = expansion_refs[: bounds["max_allowed_expansion_refs"]]

    reached_classes = list(candidate_metrics.get("operational_authority_classes_reached") or [])
    packet = {
        "schema": PACKET_SCHEMA,
        "version": "0.1",
        "packet_id": f"{candidate['candidate_id']}:SEMANTIC-AUTHORITY-v0.1",
        "trajectory_id": candidate["trajectory_id"],
        "branch_id": candidate.get("branch_id"),
        "source_trace_hash": (adapter_result.get("summary") or {}).get("source_trace_hash"),
        "evidence_batch_hash": evidence_batch_hash or "NOT_BOUND_FOR_ENGINEERING_PREFLIGHT",
        "v4_research_binding_hash": v4_research_binding_hash or "NOT_BOUND_FOR_ENGINEERING_PREFLIGHT",
        "review_contract_binding": {
            "schema": contract["schema"],
            "version": contract["version"],
            "hash": content_hash(contract),
        },
        "task_contract": _task_contract(domain),
        "agent_contracts": _agent_contracts(domain, actor_ids),
        "jump_candidate": copy.deepcopy(dict(candidate)),
        "root_behavior_event": copy.deepcopy(dict(root)),
        "source_context": {
            "source_events": compact_source_events,
            "source_model_calls": source_calls,
            "hidden_chain_of_thought_included": False,
        },
        "lineage_window": {
            "relations": copy.deepcopy(selected_relations),
            "behavior_events": [copy.deepcopy(event_by_id[event_id]) for event_id in selected_ids],
            "descendant_event_count_total": candidate_metrics.get("descendant_event_count", 0),
            "descendant_event_count_in_packet": len([event_id for event_id in selected_ids if event_id != root_id]),
            "affected_agent_ids_total": list(candidate_metrics.get("affected_agent_ids") or []),
            "truncated": len(ordered_ids) > len(selected_ids) or len(all_relations) > len(selected_relations),
        },
        "operational_window": {
            "mechanical_crossings": copy.deepcopy(selected_crossings),
            "mechanical_crossing_events": copy.deepcopy(operational_events),
            "mechanical_crossing_count_total": len(exact_crossings),
            "mechanical_penetration_depth_candidate": candidate_metrics.get("mechanical_penetration_depth_candidate"),
            "operational_authority_classes_reached": reached_classes,
            "authority_penetration_status": NOT_ADJUDICATED,
            "authority_criteria": {
                authority_class: copy.deepcopy(contract["authority_criteria"].get(authority_class))
                for authority_class in reached_classes
                if authority_class in contract["authority_criteria"]
            },
        },
        "retrospective_window": {
            "revision_events": copy.deepcopy(retrospective_events),
            "semantic_r_status": NOT_ADJUDICATED,
        },
        "adjudication_questions": copy.deepcopy(contract["adjudication_questions"]),
        "output_enums": copy.deepcopy(contract["output_enums"]),
        "boundary_fields": {
            "jump_semantic_class": NOT_ADJUDICATED,
            "semantic_adoption": NOT_ADJUDICATED,
            "decision_effect": NOT_ADJUDICATED,
            "authority_penetration": NOT_ADJUDICATED,
            "retrospective_outcome": NOT_ADJUDICATED,
            "evidence_sufficiency": NOT_ADJUDICATED,
        },
        "context_expansion": {
            "allowed_refs": expansion_refs,
            "one_expansion_round_max": True,
            "omitted_event_count": len(omitted_event_ids),
            "omitted_relation_count": len(omitted_relation_ids),
            "omitted_crossing_count": len(omitted_crossing_ids),
        },
        "review_status": "PENDING_REVIEW",
        "scientific_status": "BOUNDED_EVIDENCE_PACKET_ONLY_NOT_SEMANTIC_CONCLUSION",
        "warning": (
            "This packet localizes frozen structural evidence for later semantic/Authority adjudication. "
            "Mechanical lineage/crossing fields are not semantic adoption, C/P/R, or Authority Penetration."
        ),
    }
    packet["packet_hash"] = _hash_without(packet, "packet_hash")
    return packet


def build_bounded_review_packets(
    source_trace: Mapping[str, Any],
    adapter_result: Mapping[str, Any],
    dynamics_view: Mapping[str, Any],
    lineage_view: Mapping[str, Any],
    *,
    domain: Mapping[str, Any] | None = None,
    contract: Mapping[str, Any] | None = None,
    evidence_batch_hash: str | None = None,
    v4_research_binding_hash: str | None = None,
) -> list[dict[str, Any]]:
    contract_cfg = dict(contract or load_review_contract())
    validate_review_contract(contract_cfg)
    _require(dynamics_view.get("trajectory_id") == lineage_view.get("trajectory_id"), "review_dynamics_lineage_trajectory_mismatch")
    _require(dynamics_view.get("source_trace_hash") == lineage_view.get("source_trace_hash"), "review_dynamics_lineage_source_hash_mismatch")
    candidates = {row["candidate_id"]: row for row in dynamics_view.get("jump_candidates") or []}
    metrics = {
        row["jump_candidate_id"]: row
        for row in lineage_view.get("jump_candidate_lineage_metrics") or []
    }
    packets = []
    for candidate_id in sorted(candidates, key=lambda value: candidates[value].get("event_index", 0)):
        candidate_metrics = metrics.get(candidate_id)
        if candidate_metrics is None:
            continue
        packet = _packet_for_candidate(
            source_trace=source_trace,
            adapter_result=adapter_result,
            dynamics_view=dynamics_view,
            lineage_view=lineage_view,
            candidate=candidates[candidate_id],
            candidate_metrics=candidate_metrics,
            contract=contract_cfg,
            domain=domain,
            evidence_batch_hash=evidence_batch_hash,
            v4_research_binding_hash=v4_research_binding_hash,
        )
        verify_review_packet(packet, contract_cfg)
        packets.append(packet)
    return packets


def verify_review_packet(packet: Mapping[str, Any], contract: Mapping[str, Any] | None = None) -> bool:
    contract_cfg = dict(contract or load_review_contract())
    validate_review_contract(contract_cfg)
    _require(packet.get("schema") == PACKET_SCHEMA, "review_packet_schema_invalid")
    _require(packet.get("version") == "0.1", "review_packet_version_invalid")
    _require(packet.get("packet_hash") == _hash_without(packet, "packet_hash"), "review_packet_hash_mismatch")
    binding = packet.get("review_contract_binding") or {}
    _require(binding.get("schema") == contract_cfg["schema"], "review_packet_contract_schema_mismatch")
    _require(binding.get("version") == contract_cfg["version"], "review_packet_contract_version_mismatch")
    _require(binding.get("hash") == content_hash(contract_cfg), "review_packet_contract_hash_mismatch")
    _require(packet.get("review_status") == "PENDING_REVIEW", "review_packet_status_must_be_pending")
    _require(all(value == NOT_ADJUDICATED for value in (packet.get("boundary_fields") or {}).values()), "review_packet_semantic_contamination")
    _require((packet.get("operational_window") or {}).get("authority_penetration_status") == NOT_ADJUDICATED, "review_packet_authority_promoted")
    _require((packet.get("retrospective_window") or {}).get("semantic_r_status") == NOT_ADJUDICATED, "review_packet_r_promoted")
    bounds = contract_cfg["packet_bounds"]
    _require(len((packet.get("lineage_window") or {}).get("behavior_events") or []) <= bounds["max_behavior_events"], "review_packet_behavior_bound_exceeded")
    _require(len((packet.get("lineage_window") or {}).get("relations") or []) <= bounds["max_lineage_relations"], "review_packet_lineage_bound_exceeded")
    _require(len((packet.get("operational_window") or {}).get("mechanical_crossings") or []) <= bounds["max_operational_crossings"], "review_packet_crossing_bound_exceeded")
    _require(len((packet.get("source_context") or {}).get("source_model_calls") or []) <= bounds["max_source_model_calls"], "review_packet_source_call_bound_exceeded")
    _require(len((packet.get("context_expansion") or {}).get("allowed_refs") or []) <= bounds["max_allowed_expansion_refs"], "review_packet_expansion_bound_exceeded")
    return True


def normalize_review_output(
    packet: Mapping[str, Any],
    reviewer_output: Mapping[str, Any],
    *,
    reviewer_id: str,
    review_round_id: str,
) -> dict[str, Any]:
    contract = load_review_contract()
    verify_review_packet(packet, contract)
    _require(isinstance(reviewer_output, Mapping), "reviewer_output_must_be_object")
    status = str(reviewer_output.get("review_status") or "").upper()
    if status == "REQUEST_EXPANSION":
        ref = reviewer_output.get("context_expansion_ref")
        _require(ref in (packet.get("context_expansion") or {}).get("allowed_refs", []), "review_expansion_ref_not_allowed")
        reason = str(reviewer_output.get("reason") or "").strip()
        _require(reason, "review_expansion_reason_required")
        record = {
            "schema": REVIEW_RECORD_SCHEMA,
            "version": "0.1",
            "packet_id": packet["packet_id"],
            "packet_hash": packet["packet_hash"],
            "reviewer_id": reviewer_id,
            "review_round_id": review_round_id,
            "review_status": "REQUEST_EXPANSION",
            "context_expansion_ref": ref,
            "reason": reason,
            "append_only": True,
        }
        record["review_record_hash"] = _hash_without(record, "review_record_hash")
        return record

    _require(status == "FINAL", "review_status_must_be_final_or_request_expansion")
    normalized = {}
    for key, allowed in contract["output_enums"].items():
        value = str(reviewer_output.get(key) or "").upper()
        _require(value in allowed, f"review_output_enum_invalid:{key}:{value}")
        normalized[key] = value
    confidence = reviewer_output.get("confidence")
    if isinstance(confidence, str):
        confidence = float(confidence)
    _require(isinstance(confidence, (int, float)) and not isinstance(confidence, bool) and 0 <= confidence <= 1, "review_confidence_invalid")
    rationale = str(reviewer_output.get("rationale") or "").strip()
    _require(rationale, "review_rationale_required")
    evidence_refs = reviewer_output.get("evidence_refs") or []
    _require(isinstance(evidence_refs, list), "review_evidence_refs_must_be_array")
    record = {
        "schema": REVIEW_RECORD_SCHEMA,
        "version": "0.1",
        "packet_id": packet["packet_id"],
        "packet_hash": packet["packet_hash"],
        "trajectory_id": packet["trajectory_id"],
        "reviewer_id": reviewer_id,
        "review_round_id": review_round_id,
        "review_status": "FINAL",
        **normalized,
        "confidence": float(confidence),
        "rationale": rationale,
        "evidence_refs": list(dict.fromkeys(str(ref) for ref in evidence_refs)),
        "uncertainties": [str(value) for value in (reviewer_output.get("uncertainties") or [])],
        "append_only": True,
        "source_evidence_unchanged": True,
    }
    record["review_record_hash"] = _hash_without(record, "review_record_hash")
    return record
