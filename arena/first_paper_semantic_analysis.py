from __future__ import annotations

import copy
import statistics
from collections import Counter, defaultdict
from typing import Any, Iterable, Mapping

from .first_paper_analysis_contract import load_analysis_contract, resolve_semantic_endpoint, validate_analysis_contract
from .system_behavior import content_hash
from .v4_review_ledger import validate_review_ledger_records
from .v4_review_packets import validate_review_packet


SEMANTIC_ANALYSIS_SCHEMA = "RB-FIRST-PAPER-SEMANTIC-ANALYSIS-v0.1"
PACKET_SCOPE = "BRANCH_START_ANCHOR_PROPAGATION"
CONTROL = "CONTROL_CONTINUATION"
INTERVENTION = "STATUS_DOWNGRADE_INTERVENTION"
RESOLVED_STATUSES = {"RESOLVED_INDEPENDENT_AGREEMENT", "RESOLVED_APPEND_ONLY_ADJUDICATION"}


class FirstPaperSemanticAnalysisError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FirstPaperSemanticAnalysisError(message)


def _resolved_value(records: list[Mapping[str, Any]], field: str) -> dict[str, Any]:
    resolved = resolve_semantic_endpoint(records, field=field)
    value = resolved.get("value") if resolved.get("status") in RESOLVED_STATUSES else None
    return {**resolved, "resolved_value": value}


def _packet_identity(packet: Mapping[str, Any]) -> tuple[str, str]:
    _require(packet.get("packet_scope") == PACKET_SCOPE, "first_paper_semantic_packet_scope_invalid")
    anchor = packet.get("branch_start_anchor") or {}
    pair_id = anchor.get("pair_id")
    condition_id = anchor.get("condition_id")
    _require(isinstance(pair_id, str) and pair_id, "first_paper_semantic_pair_id_required")
    _require(condition_id in {CONTROL, INTERVENTION}, "first_paper_semantic_condition_invalid")
    return pair_id, condition_id


def _transition_key(control: str, intervention: str) -> str:
    return f"{control}->{intervention}"


def analyze_semantic_reviews(
    packets: Iterable[Mapping[str, Any]],
    review_records: Iterable[Mapping[str, Any]],
    *,
    derivation_summary: Mapping[str, Any] | None = None,
    contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract_cfg = dict(contract or load_analysis_contract())
    validate_analysis_contract(contract_cfg)
    semantic_cfg = contract_cfg["outcomes"]["key_secondary_semantic"]
    _require(semantic_cfg.get("packet_scope") == PACKET_SCOPE, "first_paper_semantic_contract_scope_invalid")
    _require(semantic_cfg.get("review_field") == "authority_penetration", "first_paper_semantic_contract_field_invalid")

    packet_rows = [dict(row) for row in packets]
    for packet in packet_rows:
        validate_review_packet(packet)
        _packet_identity(packet)
    packet_ids = [row["packet_id"] for row in packet_rows]
    _require(len(packet_ids) == len(set(packet_ids)), "first_paper_semantic_duplicate_packet_id")

    review_rows = [dict(row) for row in review_records]
    if review_rows:
        validate_review_ledger_records(packet_rows, [], review_rows)

    packet_by_pair_condition: dict[tuple[str, str], Mapping[str, Any]] = {}
    for packet in packet_rows:
        key = _packet_identity(packet)
        _require(key not in packet_by_pair_condition, f"first_paper_semantic_duplicate_pair_condition_packet:{key}")
        packet_by_pair_condition[key] = packet

    reviews_by_packet: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in review_rows:
        reviews_by_packet[row["packet_id"]].append(row)

    packet_resolution_index = []
    resolution_by_pair_condition: dict[tuple[str, str], dict[str, Any]] = {}
    for packet in packet_rows:
        pair_id, condition_id = _packet_identity(packet)
        packet_reviews = reviews_by_packet.get(packet["packet_id"], [])
        authority = _resolved_value(packet_reviews, "authority_penetration")
        adoption = _resolved_value(packet_reviews, "semantic_adoption")
        decision = _resolved_value(packet_reviews, "decision_effect")
        resolution = {
            "packet_id": packet["packet_id"],
            "trajectory_id": packet["trajectory_id"],
            "pair_id": pair_id,
            "condition_id": condition_id,
            "eligible_review_record_count": len(packet_reviews),
            "authority_penetration": authority,
            "semantic_adoption": adoption,
            "decision_effect": decision,
        }
        resolution_by_pair_condition[(pair_id, condition_id)] = resolution
        packet_resolution_index.append(resolution)

    planned_pair_ids = set(pair_id for pair_id, _ in packet_by_pair_condition)
    derivation_pair_status = {}
    planned_pair_count = len(planned_pair_ids)
    if derivation_summary is not None:
        planned = derivation_summary.get("planned_pair_count")
        _require(type(planned) is int and planned >= 0, "first_paper_semantic_planned_pair_count_invalid")
        planned_pair_count = planned
        for row in derivation_summary.get("pair_index") or []:
            pair_id = row.get("pair_id")
            if isinstance(pair_id, str) and pair_id:
                planned_pair_ids.add(pair_id)
                derivation_pair_status[pair_id] = row.get("pair_status")
        _require(planned_pair_count >= len(planned_pair_ids), "first_paper_semantic_planned_pair_count_below_known_pairs")

    encoding = semantic_cfg["numeric_encoding_for_paired_estimand"]
    determinate = set(semantic_cfg["determinate_values"])
    authority_pair_deltas = []
    pair_index = []
    unresolved_categories = Counter()
    adoption_transitions = Counter()
    decision_transitions = Counter()

    for pair_id in sorted(planned_pair_ids):
        structural_status = derivation_pair_status.get(pair_id)
        if structural_status == "PAIR_NOT_COMPARABLE_NONCOMPLETE_TRACE":
            status = "EXECUTION_CENSORED_NOT_SEMANTIC_ZERO"
            unresolved_categories[status] += 1
            pair_index.append({
                "pair_id": pair_id,
                "status": status,
                "structural_pair_status": structural_status,
                "authority_penetration_delta": None,
            })
            continue
        if structural_status not in {None, "PAIR_COMPARED_STRUCTURALLY_V4"}:
            status = "DATA_INTEGRITY_OR_PAIR_IDENTITY_UNRESOLVED"
            unresolved_categories[status] += 1
            pair_index.append({
                "pair_id": pair_id,
                "status": status,
                "structural_pair_status": structural_status,
                "authority_penetration_delta": None,
            })
            continue

        control = resolution_by_pair_condition.get((pair_id, CONTROL))
        intervention = resolution_by_pair_condition.get((pair_id, INTERVENTION))
        if control is None or intervention is None:
            status = "SEMANTIC_PACKET_MISSING"
            unresolved_categories[status] += 1
            pair_index.append({
                "pair_id": pair_id,
                "status": status,
                "missing_conditions": [
                    condition
                    for condition, row in ((CONTROL, control), (INTERVENTION, intervention))
                    if row is None
                ],
                "authority_penetration_delta": None,
            })
            continue

        c_authority = control["authority_penetration"]["resolved_value"]
        i_authority = intervention["authority_penetration"]["resolved_value"]
        authority_resolved = c_authority in determinate and i_authority in determinate
        if authority_resolved:
            delta = encoding[i_authority] - encoding[c_authority]
            authority_pair_deltas.append({
                "pair_id": pair_id,
                "control": c_authority,
                "intervention": i_authority,
                "delta": delta,
            })
            status = "RESOLVED_AUTHORITY_PAIR"
        else:
            delta = None
            status = "SEMANTIC_AUTHORITY_UNRESOLVED_OR_NONDETERMINATE"
            unresolved_categories[status] += 1

        c_adoption = control["semantic_adoption"]["resolved_value"]
        i_adoption = intervention["semantic_adoption"]["resolved_value"]
        if c_adoption is not None and i_adoption is not None:
            adoption_transitions[_transition_key(c_adoption, i_adoption)] += 1

        c_decision = control["decision_effect"]["resolved_value"]
        i_decision = intervention["decision_effect"]["resolved_value"]
        if c_decision is not None and i_decision is not None:
            decision_transitions[_transition_key(c_decision, i_decision)] += 1

        pair_index.append({
            "pair_id": pair_id,
            "status": status,
            "control_packet_id": control["packet_id"],
            "intervention_packet_id": intervention["packet_id"],
            "control_authority_resolution_status": control["authority_penetration"]["status"],
            "intervention_authority_resolution_status": intervention["authority_penetration"]["status"],
            "control_authority_penetration": c_authority,
            "intervention_authority_penetration": i_authority,
            "authority_penetration_delta": delta,
        })

    delta_values = [row["delta"] for row in authority_pair_deltas]
    resolved_pair_count = len(delta_values)
    unresolved_pair_count = max(0, planned_pair_count - resolved_pair_count)
    authority_summary = {
        "outcome_id": semantic_cfg["outcome_id"],
        "review_field": semantic_cfg["review_field"],
        "pair_delta_definition": semantic_cfg["pair_delta_definition"],
        "batch_estimand": semantic_cfg["batch_estimand"],
        "resolved_pair_deltas": authority_pair_deltas,
        "resolved_pair_count": resolved_pair_count,
        "mean_resolved_pair_delta": statistics.fmean(delta_values) if delta_values else None,
        "median_resolved_pair_delta": statistics.median(delta_values) if delta_values else None,
        "negative_delta_count": sum(value < 0 for value in delta_values),
        "zero_delta_count": sum(value == 0 for value in delta_values),
        "positive_delta_count": sum(value > 0 for value in delta_values),
        "estimate_status": "ESTIMATED_RESOLVED_PAIRS_ONLY" if delta_values else "NOT_ESTIMATED_NO_RESOLVED_PAIRS",
        "unresolved_category_counts": dict(sorted(unresolved_categories.items())),
        "warning": "Only determinate YES/NO packet endpoints resolved under the frozen reviewer rule enter this semantic estimand. Uncertainty, disagreement, insufficient review, missing packets and execution censoring are never encoded as NO.",
    }

    analysis = {
        "schema": SEMANTIC_ANALYSIS_SCHEMA,
        "version": "0.1",
        "analysis_contract_hash": content_hash(contract_cfg),
        "paper_scope": contract_cfg["paper_scope"],
        "packet_scope": PACKET_SCOPE,
        "key_secondary_outcome_id": semantic_cfg["outcome_id"],
        "packet_count": len(packet_rows),
        "review_record_count": len(review_rows),
        "planned_pair_count": planned_pair_count,
        "resolved_pair_count": resolved_pair_count,
        "unresolved_pair_count": unresolved_pair_count,
        "packet_resolution_index": packet_resolution_index,
        "pair_index": pair_index,
        "authority_penetration": authority_summary,
        "secondary_transition_tables": {
            "semantic_adoption": dict(sorted(adoption_transitions.items())),
            "decision_effect": dict(sorted(decision_transitions.items())),
        },
        "primary_structural_endpoint_unchanged": True,
        "semantic_endpoint_role": "KEY_SECONDARY_MECHANISTIC_ENDPOINT",
        "source_evidence_mutated": False,
        "automatic_paid_evaluator_called": False,
        "scientific_status": "APPEND_ONLY_RESOLVED_SEMANTIC_ENDPOINT_AGGREGATION",
        "warning": (
            "This analysis aggregates only append-only Reviewer-v4 resolutions under the frozen first-paper contract. "
            "It does not replace the primary structural endpoint and does not convert unresolved semantic evidence into a negative result."
        ),
    }
    analysis["analysis_hash"] = content_hash(analysis)
    return analysis
