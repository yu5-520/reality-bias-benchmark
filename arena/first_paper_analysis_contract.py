from __future__ import annotations

import copy
import math
import random
import statistics
from pathlib import Path
from typing import Any, Iterable, Mapping

from .branch_comparison_v4 import verify_branch_comparison_v4
from .system_behavior import content_hash, load_json


CONTRACT_SCHEMA = "RB-FIRST-PAPER-ANALYSIS-CONTRACT-v0.1"
ANALYSIS_SCHEMA = "RB-FIRST-PAPER-STRUCTURAL-ANALYSIS-v0.1"
CONTRACT_PATH = "configs/first_paper_analysis_contract_v0.1.json"
PRIMARY_DELTA_PATH = (
    "structural_deltas",
    "r5_mid_branch_anchor",
    "potential_downstream_operational_crossing_count",
    "delta_intervention_minus_control",
)


class FirstPaperAnalysisContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FirstPaperAnalysisContractError(message)


def load_analysis_contract(path: str | Path = CONTRACT_PATH) -> dict[str, Any]:
    contract = load_json(path)
    validate_analysis_contract(contract)
    return contract


def validate_analysis_contract(contract: Mapping[str, Any]) -> bool:
    _require(contract.get("schema") == CONTRACT_SCHEMA, "first_paper_contract_schema_invalid")
    _require(contract.get("version") == "0.1", "first_paper_contract_version_invalid")
    _require(
        contract.get("status") == "FROZEN_BEFORE_NEW_V4_SUBJECT_EVIDENCE",
        "first_paper_contract_status_not_frozen",
    )
    _require(
        contract.get("experiment_family") == "R5R6-FROZEN-PARENT-BRANCH-v0.1",
        "first_paper_contract_experiment_family_invalid",
    )
    variable = contract.get("experimental_variable") or {}
    _require(variable.get("variable_id") == "EPISTEMIC_STATUS_DOWNGRADE", "first_paper_variable_invalid")
    _require(variable.get("stage") == "MID", "first_paper_variable_stage_invalid")
    _require(variable.get("control_condition_id") == "CONTROL_CONTINUATION", "first_paper_control_condition_invalid")
    _require(
        variable.get("intervention_condition_id") == "STATUS_DOWNGRADE_INTERVENTION",
        "first_paper_intervention_condition_invalid",
    )
    primary = ((contract.get("outcomes") or {}).get("primary_confirmatory_structural") or {})
    _require(
        primary.get("outcome_id") == "R5MID_ANCHOR_DOWNSTREAM_OPERATIONAL_CROSSING_COUNT",
        "first_paper_primary_outcome_invalid",
    )
    _require(primary.get("pair_delta_definition") == "INTERVENTION_MINUS_CONTROL", "first_paper_primary_delta_invalid")
    aggregation = ((contract.get("batch_aggregation") or {}).get("primary_structural") or {})
    _require(aggregation.get("estimate") == "ARITHMETIC_MEAN_OF_PAIR_DELTAS", "first_paper_primary_estimator_invalid")
    _require(aggregation.get("robust_summary") == "MEDIAN_OF_PAIR_DELTAS", "first_paper_robust_estimator_invalid")
    _require(aggregation.get("primary_p_value") == "NONE", "first_paper_primary_p_value_must_be_none")
    uncertainty = aggregation.get("uncertainty") or {}
    _require(uncertainty.get("method") == "PAIRED_NONPARAMETRIC_PERCENTILE_BOOTSTRAP", "first_paper_uncertainty_method_invalid")
    _require(type(uncertainty.get("resamples")) is int and uncertainty["resamples"] >= 1000, "first_paper_bootstrap_resamples_invalid")
    _require(type(uncertainty.get("minimum_complete_pairs")) is int and uncertainty["minimum_complete_pairs"] >= 2, "first_paper_min_pairs_invalid")
    _require(type(uncertainty.get("deterministic_seed")) is int, "first_paper_bootstrap_seed_invalid")
    confidence = uncertainty.get("confidence_level")
    _require(type(confidence) in (int, float) and 0 < confidence < 1, "first_paper_confidence_invalid")
    semantic = ((contract.get("outcomes") or {}).get("key_secondary_semantic") or {})
    _require(semantic.get("packet_scope") == "BRANCH_START_ANCHOR_PROPAGATION", "first_paper_semantic_scope_invalid")
    _require(semantic.get("review_field") == "authority_penetration", "first_paper_semantic_field_invalid")
    _require(semantic.get("required_evidence_sufficiency") == "SUFFICIENT", "first_paper_semantic_sufficiency_invalid")
    freeze_rules = contract.get("analysis_freeze_rules") or []
    _require(any("hashed into the forward v4 research binding" in row for row in freeze_rules), "first_paper_binding_freeze_rule_missing")
    return True


def _path_value(record: Mapping[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = record
    for key in path:
        if not isinstance(value, Mapping) or key not in value:
            return None
        value = value[key]
    return value


def _percentile(sorted_values: list[float], q: float) -> float:
    _require(bool(sorted_values), "percentile_requires_values")
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    pos = (len(sorted_values) - 1) * q
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return float(sorted_values[low])
    weight = pos - low
    return float(sorted_values[low] * (1 - weight) + sorted_values[high] * weight)


def _bootstrap_mean_interval(values: list[float], *, confidence: float, resamples: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    n = len(values)
    samples = []
    for _ in range(resamples):
        draw = [values[rng.randrange(n)] for _ in range(n)]
        samples.append(statistics.fmean(draw))
    samples.sort()
    alpha = 1 - confidence
    return {
        "method": "PAIRED_NONPARAMETRIC_PERCENTILE_BOOTSTRAP",
        "confidence_level": confidence,
        "resamples": resamples,
        "deterministic_seed": seed,
        "lower": _percentile(samples, alpha / 2),
        "upper": _percentile(samples, 1 - alpha / 2),
    }


def _validate_primary_comparison(comparison: Mapping[str, Any]) -> float:
    verify_branch_comparison_v4(comparison)
    _require(comparison.get("experimental_variable_id") == "EPISTEMIC_STATUS_DOWNGRADE", "first_paper_comparison_variable_invalid")
    _require(comparison.get("semantic_status") == "NOT_ADJUDICATED", "first_paper_comparison_semantic_promoted")
    _require(comparison.get("causal_effect_status") == "NOT_ADJUDICATED", "first_paper_comparison_causal_promoted")
    delta = _path_value(comparison, PRIMARY_DELTA_PATH)
    _require(type(delta) in (int, float) and not isinstance(delta, bool), "first_paper_primary_delta_missing")
    return float(delta)


def analyze_structural_comparisons(
    comparisons: Iterable[Mapping[str, Any]],
    *,
    derivation_summary: Mapping[str, Any] | None = None,
    contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract_cfg = dict(contract or load_analysis_contract())
    validate_analysis_contract(contract_cfg)
    rows = [dict(row) for row in comparisons]
    pair_ids = [row.get("pair_id") for row in rows]
    _require(len(pair_ids) == len(set(pair_ids)), "first_paper_duplicate_pair_id")
    deltas = [_validate_primary_comparison(row) for row in rows]

    planned_pair_count = len(rows)
    censored_pair_count = 0
    integrity_failure_count = 0
    pair_index = []
    if derivation_summary is not None:
        planned = derivation_summary.get("planned_pair_count")
        _require(type(planned) is int and planned >= len(rows), "first_paper_planned_pair_count_invalid")
        planned_pair_count = planned
        for row in derivation_summary.get("pair_index") or []:
            status = row.get("pair_status")
            pair_index.append(copy.deepcopy(dict(row)))
            if status == "PAIR_NOT_COMPARABLE_NONCOMPLETE_TRACE":
                censored_pair_count += 1
            elif status not in {"PAIR_COMPARED_STRUCTURALLY_V4", "PAIR_NOT_COMPARABLE_NONCOMPLETE_TRACE"}:
                integrity_failure_count += 1
        compared_in_summary = sum(1 for row in pair_index if row.get("pair_status") == "PAIR_COMPARED_STRUCTURALLY_V4")
        _require(compared_in_summary == len(rows), "first_paper_summary_comparison_count_mismatch")

    complete_pair_count = len(deltas)
    negative = sum(value < 0 for value in deltas)
    zero = sum(value == 0 for value in deltas)
    positive = sum(value > 0 for value in deltas)
    mean = statistics.fmean(deltas) if deltas else None
    median = statistics.median(deltas) if deltas else None
    uncertainty_cfg = contract_cfg["batch_aggregation"]["primary_structural"]["uncertainty"]
    if len(deltas) >= uncertainty_cfg["minimum_complete_pairs"]:
        interval = _bootstrap_mean_interval(
            deltas,
            confidence=float(uncertainty_cfg["confidence_level"]),
            resamples=int(uncertainty_cfg["resamples"]),
            seed=int(uncertainty_cfg["deterministic_seed"]),
        )
        interval_status = "ESTIMATED"
    else:
        interval = None
        interval_status = "NOT_ESTIMATED_MINIMUM_PAIR_COUNT_NOT_MET"

    order_groups: dict[str, list[float]] = {}
    for row, delta in zip(rows, deltas):
        key = str(row.get("pair_order_pattern") or "UNKNOWN")
        order_groups.setdefault(key, []).append(delta)
    order_sensitivity = {
        key: {
            "pair_count": len(values),
            "mean_pair_delta": statistics.fmean(values),
            "median_pair_delta": statistics.median(values),
        }
        for key, values in sorted(order_groups.items())
    }

    analysis = {
        "schema": ANALYSIS_SCHEMA,
        "version": "0.1",
        "analysis_contract_hash": content_hash(contract_cfg),
        "paper_scope": contract_cfg["paper_scope"],
        "experimental_variable_id": "EPISTEMIC_STATUS_DOWNGRADE",
        "primary_outcome_id": contract_cfg["outcomes"]["primary_confirmatory_structural"]["outcome_id"],
        "pair_delta_definition": "INTERVENTION_MINUS_CONTROL",
        "planned_pair_count": planned_pair_count,
        "complete_pair_count": complete_pair_count,
        "censored_pair_count": censored_pair_count,
        "integrity_failure_count": integrity_failure_count,
        "all_pair_deltas": [
            {"pair_id": row["pair_id"], "pair_order_pattern": row.get("pair_order_pattern"), "delta": delta}
            for row, delta in zip(rows, deltas)
        ],
        "mean_pair_delta": mean,
        "median_pair_delta": median,
        "negative_delta_count": negative,
        "zero_delta_count": zero,
        "positive_delta_count": positive,
        "primary_interval_status": interval_status,
        "primary_interval": interval,
        "primary_p_value": None,
        "order_sensitivity": order_sensitivity,
        "pair_index": pair_index,
        "semantic_status": "NOT_INCLUDED_IN_STRUCTURAL_ANALYSIS",
        "causal_claim_status": "NOT_ESTABLISHED_BY_STRUCTURAL_ANALYSIS_ALONE",
        "scientific_status": "FROZEN_CONTRACT_STRUCTURAL_ESTIMATE",
        "warning": (
            "The primary endpoint is branch-anchor structural reach to mechanical operational crossings. "
            "It is not semantic Authority Penetration and does not by itself establish a generalized causal law."
        ),
    }
    analysis["analysis_hash"] = content_hash(analysis)
    return analysis


def resolve_semantic_endpoint(
    records: Iterable[Mapping[str, Any]],
    *,
    field: str = "authority_penetration",
) -> dict[str, Any]:
    rows = [dict(row) for row in records]
    eligible = [
        row
        for row in rows
        if row.get("record_kind") == "independent"
        and ((row.get("judgments") or {}).get("evidence_sufficiency") == "SUFFICIENT")
    ]
    by_reviewer: dict[str, list[dict[str, Any]]] = {}
    for row in eligible:
        reviewer_id = str((row.get("reviewer") or {}).get("id") or "")
        _require(reviewer_id, "first_paper_semantic_reviewer_id_required")
        by_reviewer.setdefault(reviewer_id, []).append(row)
    duplicate_reviewers = sorted(key for key, values in by_reviewer.items() if len(values) != 1)
    if duplicate_reviewers:
        return {
            "status": "DATA_QUALITY_UNRESOLVED_DUPLICATE_INDEPENDENT_REVIEWER_RECORDS",
            "value": None,
            "duplicate_reviewer_ids": duplicate_reviewers,
        }
    if len(by_reviewer) < 2:
        return {"status": "PENDING_MINIMUM_INDEPENDENT_REVIEWERS", "value": None, "eligible_reviewer_count": len(by_reviewer)}
    values = [str((values[0].get("judgments") or {}).get(field) or "") for values in by_reviewer.values()]
    if all(value == values[0] for value in values):
        return {"status": "RESOLVED_INDEPENDENT_AGREEMENT", "value": values[0], "eligible_reviewer_count": len(values)}

    eligible_ids = {values[0]["review_record_id"] for values in by_reviewer.values()}
    adjudications = [
        row
        for row in rows
        if row.get("record_kind") == "adjudication"
        and ((row.get("judgments") or {}).get("evidence_sufficiency") == "SUFFICIENT")
        and eligible_ids.issubset(set(row.get("parent_review_ids") or []))
    ]
    if len(adjudications) == 1:
        value = str((adjudications[0].get("judgments") or {}).get(field) or "")
        return {
            "status": "RESOLVED_APPEND_ONLY_ADJUDICATION",
            "value": value,
            "eligible_reviewer_count": len(values),
            "adjudication_review_record_id": adjudications[0].get("review_record_id"),
        }
    if len(adjudications) > 1:
        return {"status": "DATA_QUALITY_UNRESOLVED_MULTIPLE_ADJUDICATIONS", "value": None}
    return {
        "status": "DISAGREEMENT_UNRESOLVED",
        "value": None,
        "eligible_reviewer_count": len(values),
        "observed_values": sorted(set(values)),
    }
