from __future__ import annotations

import copy
from typing import Any, Mapping

from .system_behavior import content_hash


COMPARISON_SCHEMA = "RB-BRANCH-TRAJECTORY-COMPARISON-v4.0"
COMPARISON_VERSION = "4.0"
NOT_ADJUDICATED = "NOT_ADJUDICATED"


class BranchComparisonV4Error(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BranchComparisonV4Error(message)


def _numeric_delta(intervention: Any, control: Any) -> int | float | None:
    if isinstance(intervention, bool) or isinstance(control, bool):
        return None
    if isinstance(intervention, (int, float)) and isinstance(control, (int, float)):
        return intervention - control
    return None


def _count_delta_map(intervention: Mapping[str, Any], control: Mapping[str, Any]) -> dict[str, int | float]:
    out: dict[str, int | float] = {}
    for key in sorted(set(control) | set(intervention)):
        left = control.get(key, 0)
        right = intervention.get(key, 0)
        if isinstance(left, bool) or isinstance(right, bool):
            continue
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            out[key] = right - left
    return out


def _authority_class_delta(intervention: list[str], control: list[str]) -> dict[str, list[str]]:
    control_set = set(str(value) for value in control)
    intervention_set = set(str(value) for value in intervention)
    return {
        "control_only": sorted(control_set - intervention_set),
        "intervention_only": sorted(intervention_set - control_set),
        "shared": sorted(control_set & intervention_set),
    }


def _single_variable(measurement: Mapping[str, Any]) -> Mapping[str, Any]:
    rows = measurement.get("experimental_variables") or []
    _require(isinstance(rows, list) and len(rows) == 1, "v4_comparison_requires_one_experimental_variable")
    _require(isinstance(rows[0], Mapping), "v4_comparison_variable_record_invalid")
    return rows[0]


def _metric(control: Mapping[str, Any], intervention: Mapping[str, Any], key: str) -> dict[str, Any]:
    return {
        "control": control.get(key),
        "intervention": intervention.get(key),
        "delta_intervention_minus_control": _numeric_delta(intervention.get(key), control.get(key)),
    }


def build_branch_comparison_v4(
    control: Mapping[str, Any],
    intervention: Mapping[str, Any],
    *,
    comparison_id: str,
) -> dict[str, Any]:
    _require(control.get("schema") == "RB-SYSTEM-TRAJECTORY-MEASUREMENT-v4.0", "control_measurement_schema_invalid")
    _require(intervention.get("schema") == "RB-SYSTEM-TRAJECTORY-MEASUREMENT-v4.0", "intervention_measurement_schema_invalid")
    _require(isinstance(comparison_id, str) and comparison_id, "comparison_id_required")
    _require(control.get("pair_id") == intervention.get("pair_id"), "v4_comparison_pair_id_mismatch")
    _require(control.get("parent_state_hash") == intervention.get("parent_state_hash"), "v4_comparison_parent_state_hash_mismatch")
    _require(control.get("branch_plan_hash") == intervention.get("branch_plan_hash"), "v4_comparison_branch_plan_hash_mismatch")
    _require(control.get("source_evidence_batch_hash") == intervention.get("source_evidence_batch_hash"), "v4_comparison_evidence_batch_hash_mismatch")
    _require(control.get("v4_research_binding_hash") == intervention.get("v4_research_binding_hash"), "v4_comparison_binding_hash_mismatch")
    _require(control.get("replicate_index") == intervention.get("replicate_index"), "v4_comparison_replicate_index_mismatch")
    _require(control.get("condition_id") == "CONTROL_CONTINUATION", "v4_comparison_control_condition_invalid")
    _require(intervention.get("condition_id") == "STATUS_DOWNGRADE_INTERVENTION", "v4_comparison_intervention_condition_invalid")
    _require(control.get("semantic_status") == NOT_ADJUDICATED, "v4_comparison_control_semantic_status_invalid")
    _require(intervention.get("semantic_status") == NOT_ADJUDICATED, "v4_comparison_intervention_semantic_status_invalid")

    control_variable = _single_variable(control)
    intervention_variable = _single_variable(intervention)
    variable_id = control_variable.get("variable_id")
    _require(variable_id == intervention_variable.get("variable_id"), "v4_comparison_variable_id_mismatch")
    _require(control_variable.get("assignment") == "CONTROL", "v4_comparison_control_assignment_invalid")
    _require(intervention_variable.get("assignment") == "MANIPULATION", "v4_comparison_intervention_assignment_invalid")

    c_r2 = control.get("r2") or {}
    i_r2 = intervention.get("r2") or {}
    c_r3 = control.get("r3") or {}
    i_r3 = intervention.get("r3") or {}
    c_r4 = control.get("r4") or {}
    i_r4 = intervention.get("r4") or {}
    c_r5 = control.get("r5_mid") or {}
    i_r5 = intervention.get("r5_mid") or {}
    _require(c_r5 and i_r5, "v4_comparison_r5_mid_anchor_metrics_required")
    _require(c_r5.get("state_key") == i_r5.get("state_key"), "v4_comparison_r5_mid_state_key_mismatch")
    _require(c_r5.get("semantic_reliance_status") == NOT_ADJUDICATED, "v4_comparison_control_anchor_semantic_promoted")
    _require(i_r5.get("semantic_reliance_status") == NOT_ADJUDICATED, "v4_comparison_intervention_anchor_semantic_promoted")

    structural_deltas = {
        "behavior_event_count": _metric(control, intervention, "behavior_event_count"),
        "r2": {
            "jump_candidate_count": _metric(c_r2, i_r2, "jump_candidate_count"),
            "first_jump_turn": _metric(c_r2, i_r2, "first_jump_turn"),
            "jump_type_count_delta": _count_delta_map(
                i_r2.get("jump_type_counts") or {},
                c_r2.get("jump_type_counts") or {},
            ),
        },
        "r3": {
            "descendant_event_count": _metric(c_r3, i_r3, "descendant_event_count"),
            "affected_agent_count": _metric(c_r3, i_r3, "affected_agent_count"),
            "operational_boundary_crossing_count": _metric(c_r3, i_r3, "operational_boundary_crossing_count"),
            "first_jump_downstream_operational_crossing_count": _metric(c_r3, i_r3, "first_jump_downstream_operational_crossing_count"),
            "first_jump_mechanical_penetration_depth_candidate": _metric(c_r3, i_r3, "first_jump_mechanical_penetration_depth_candidate"),
            "operational_authority_classes_reached": _authority_class_delta(
                i_r3.get("first_jump_operational_authority_classes_reached") or [],
                c_r3.get("first_jump_operational_authority_classes_reached") or [],
            ),
        },
        "r4": {
            "retrospective_window_count": _metric(c_r4, i_r4, "retrospective_window_count"),
        },
        "r5_mid_branch_anchor": {
            "state_key": c_r5.get("state_key"),
            "control_state_status": c_r5.get("state_status"),
            "intervention_state_status": i_r5.get("state_status"),
            "anchor_visible_agent_turn_count": _metric(c_r5, i_r5, "anchor_visible_agent_turn_count"),
            "potential_downstream_event_count": _metric(c_r5, i_r5, "potential_downstream_event_count"),
            "potential_downstream_relation_count": _metric(c_r5, i_r5, "potential_downstream_relation_count"),
            "potential_downstream_affected_agent_count": _metric(c_r5, i_r5, "potential_downstream_affected_agent_count"),
            "potential_downstream_operational_crossing_count": _metric(c_r5, i_r5, "potential_downstream_operational_crossing_count"),
            "mechanical_anchor_reach_depth_candidate": _metric(c_r5, i_r5, "mechanical_anchor_reach_depth_candidate"),
            "potential_downstream_authority_classes_reached": _authority_class_delta(
                i_r5.get("potential_downstream_authority_classes_reached") or [],
                c_r5.get("potential_downstream_authority_classes_reached") or [],
            ),
            "semantic_reliance_status": NOT_ADJUDICATED,
            "authority_penetration_status": NOT_ADJUDICATED,
        },
    }

    comparison = {
        "schema": COMPARISON_SCHEMA,
        "version": COMPARISON_VERSION,
        "comparison_id": comparison_id,
        "pair_id": control["pair_id"],
        "replicate_index": control.get("replicate_index"),
        "pair_order_pattern": control.get("pair_order_pattern"),
        "control_run_id": control.get("trajectory_id"),
        "intervention_run_id": intervention.get("trajectory_id"),
        "control_measurement_hash": control.get("measurement_hash"),
        "intervention_measurement_hash": intervention.get("measurement_hash"),
        "common_parent_state_hash": control.get("parent_state_hash"),
        "branch_plan_hash": control.get("branch_plan_hash"),
        "source_evidence_batch_hash": control.get("source_evidence_batch_hash"),
        "v4_research_binding_hash": control.get("v4_research_binding_hash"),
        "experimental_variable_id": variable_id,
        "control_level": copy.deepcopy(control_variable.get("level")),
        "intervention_level": copy.deepcopy(intervention_variable.get("level")),
        "structural_deltas": structural_deltas,
        "semantic_status": NOT_ADJUDICATED,
        "causal_effect_status": NOT_ADJUDICATED,
        "scientific_status": "PAIRED_STRUCTURAL_DIFFERENCE_ONLY",
        "warning": (
            "This record compares two bound branch trajectories from the same frozen parent. "
            "R5-MID branch-anchor fields are rooted at the exact branch-start state and measure structural exposure/reach. "
            "A structural delta is not by itself semantic reliance, C/P/R, Authority Penetration, recovery, or a generalized causal effect."
        ),
    }
    comparison["comparison_hash"] = content_hash(comparison)
    verify_branch_comparison_v4(comparison)
    return comparison


def verify_branch_comparison_v4(comparison: Mapping[str, Any]) -> bool:
    _require(comparison.get("schema") == COMPARISON_SCHEMA, "v4_comparison_schema_invalid")
    _require(comparison.get("version") == COMPARISON_VERSION, "v4_comparison_version_invalid")
    for key in (
        "comparison_id",
        "pair_id",
        "control_measurement_hash",
        "intervention_measurement_hash",
        "common_parent_state_hash",
        "branch_plan_hash",
        "source_evidence_batch_hash",
        "v4_research_binding_hash",
        "experimental_variable_id",
        "comparison_hash",
    ):
        _require(isinstance(comparison.get(key), str) and comparison[key], f"v4_comparison_{key}_required")
    _require(comparison.get("semantic_status") == NOT_ADJUDICATED, "v4_comparison_semantic_status_invalid")
    _require(comparison.get("causal_effect_status") == NOT_ADJUDICATED, "v4_comparison_causal_status_invalid")
    _require(isinstance(comparison.get("structural_deltas"), Mapping), "v4_comparison_structural_deltas_required")
    _require(isinstance((comparison.get("structural_deltas") or {}).get("r5_mid_branch_anchor"), Mapping), "v4_comparison_r5_mid_deltas_required")
    material = copy.deepcopy(dict(comparison))
    supplied_hash = material.pop("comparison_hash", None)
    _require(supplied_hash == content_hash(material), "v4_comparison_hash_mismatch")
    return True
