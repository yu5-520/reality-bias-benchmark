from __future__ import annotations

import copy
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from .system_behavior import (
    BOUNDARY_REGISTRY_SCHEMA,
    BEHAVIOR_SCHEMA,
    RegistryBundle,
    content_hash,
    load_json,
    validate_behavior_event,
)


JUMP_DETECTOR_SCHEMA = "RB-STRUCTURAL-JUMP-DETECTOR-v0.1"
JUMP_CANDIDATE_SCHEMA = "RB-STRUCTURAL-JUMP-CANDIDATE-v0.1"
OPERATIONAL_SET_SCHEMA = "RB-OPERATIONAL-BOUNDARY-SET-v0.1"
OPERATIONAL_CROSSING_SCHEMA = "RB-OPERATIONAL-BOUNDARY-CROSSING-v0.1"
DYNAMICS_VIEW_SCHEMA = "RB-SYSTEM-DYNAMICS-VIEW-v4.0"
NOT_ADJUDICATED = "NOT_ADJUDICATED"


class SystemBehaviorDynamicsError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemBehaviorDynamicsError(message)


def _state_hash_changed(event: Mapping[str, Any]) -> bool:
    before = event.get("state_before_hash")
    after = event.get("state_after_hash")
    return isinstance(before, str) and isinstance(after, str) and before != after


def _structured_diff(event: Mapping[str, Any]) -> Mapping[str, Any]:
    value = event.get("structured_diff")
    return value if isinstance(value, Mapping) else {}


def validate_jump_detector(
    config: Mapping[str, Any], *, boundary_registry: Mapping[str, Any] | None = None
) -> None:
    _require(config.get("schema") == JUMP_DETECTOR_SCHEMA, "jump_detector_schema_invalid")
    _require(config.get("version") == "0.1", "jump_detector_version_invalid")
    _require(config.get("source_behavior_schema") == BEHAVIOR_SCHEMA, "jump_detector_behavior_schema_invalid")
    rules = config.get("rules")
    _require(isinstance(rules, list) and rules, "jump_detector_rules_required")

    registered_boundaries = None
    if boundary_registry is not None:
        _require(
            boundary_registry.get("schema") == BOUNDARY_REGISTRY_SCHEMA,
            "measurement_boundary_registry_schema_invalid",
        )
        registered_boundaries = {
            row.get("boundary_id") for row in boundary_registry.get("boundaries") or []
        }

    seen = set()
    for rule in rules:
        rule_id = rule.get("rule_id")
        _require(isinstance(rule_id, str) and rule_id, "jump_detector_rule_id_required")
        _require(rule_id not in seen, f"jump_detector_duplicate_rule:{rule_id}")
        seen.add(rule_id)
        _require(isinstance(rule.get("candidate_type"), str), f"candidate_type_required:{rule_id}")
        _require(isinstance(rule.get("boundary_id"), str), f"boundary_id_required:{rule_id}")
        _require(isinstance(rule.get("action_type"), str), f"action_type_required:{rule_id}")
        _require(
            rule.get("realization_status") in {"PROPOSAL", "REALIZED", "BLOCKED", "FAILED"},
            f"realization_status_invalid:{rule_id}",
        )
        if registered_boundaries is not None:
            _require(
                rule["boundary_id"] in registered_boundaries,
                f"jump_detector_unknown_boundary:{rule['boundary_id']}",
            )
        field = rule.get("structured_diff_field")
        allowed = rule.get("structured_diff_allowed_values")
        _require(
            (field is None and allowed is None)
            or (isinstance(field, str) and isinstance(allowed, list) and allowed),
            f"structured_diff_rule_invalid:{rule_id}",
        )


def validate_operational_boundary_set(
    config: Mapping[str, Any], *, boundary_registry: Mapping[str, Any] | None = None
) -> None:
    _require(config.get("schema") == OPERATIONAL_SET_SCHEMA, "operational_boundary_set_schema_invalid")
    _require(config.get("version") == "0.1", "operational_boundary_set_version_invalid")
    _require(config.get("source_behavior_schema") == BEHAVIOR_SCHEMA, "operational_behavior_schema_invalid")
    rows = config.get("boundaries")
    _require(isinstance(rows, list) and rows, "operational_boundaries_required")

    registered_boundaries = None
    if boundary_registry is not None:
        _require(
            boundary_registry.get("schema") == BOUNDARY_REGISTRY_SCHEMA,
            "measurement_boundary_registry_schema_invalid",
        )
        registered_boundaries = {
            row.get("boundary_id") for row in boundary_registry.get("boundaries") or []
        }

    seen = set()
    for row in rows:
        boundary_id = row.get("operational_boundary_id")
        measurement_boundary_id = row.get("measurement_boundary_id")
        _require(isinstance(boundary_id, str) and boundary_id, "operational_boundary_id_required")
        _require(boundary_id not in seen, f"duplicate_operational_boundary:{boundary_id}")
        seen.add(boundary_id)
        _require(isinstance(measurement_boundary_id, str), f"measurement_boundary_required:{boundary_id}")
        _require(isinstance(row.get("action_type"), str), f"action_type_required:{boundary_id}")
        _require(
            row.get("realization_status") in {"PROPOSAL", "REALIZED", "BLOCKED", "FAILED"},
            f"realization_status_invalid:{boundary_id}",
        )
        if registered_boundaries is not None:
            _require(
                measurement_boundary_id in registered_boundaries,
                f"operational_unknown_measurement_boundary:{measurement_boundary_id}",
            )


def load_v4_dynamics_configs(
    jump_detector_path: str | Path = "configs/structural_jump_detector_v0.1.json",
    operational_boundary_path: str | Path = "configs/operational_boundary_set_v0.1.json",
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    bundle = RegistryBundle.load()
    detector = load_json(jump_detector_path)
    operational = load_json(operational_boundary_path)
    validate_jump_detector(detector, boundary_registry=bundle.boundaries)
    validate_operational_boundary_set(operational, boundary_registry=bundle.boundaries)
    return detector, operational, dict(bundle.boundaries)


def _rule_matches(event: Mapping[str, Any], rule: Mapping[str, Any]) -> bool:
    if event.get("boundary_id") != rule.get("boundary_id"):
        return False
    if event.get("action_type") != rule.get("action_type"):
        return False
    if event.get("realization_status") != rule.get("realization_status"):
        return False
    if rule.get("require_state_hash_change") is True and not _state_hash_changed(event):
        return False
    field = rule.get("structured_diff_field")
    if field is not None:
        if _structured_diff(event).get(field) not in rule.get("structured_diff_allowed_values", []):
            return False
    return True


def _crossing_matches(event: Mapping[str, Any], rule: Mapping[str, Any]) -> bool:
    if event.get("boundary_id") != rule.get("measurement_boundary_id"):
        return False
    if event.get("action_type") != rule.get("action_type"):
        return False
    if event.get("realization_status") != rule.get("realization_status"):
        return False
    if rule.get("require_state_hash_change") is True and not _state_hash_changed(event):
        return False
    return True


def detect_structural_jump_candidates(
    behavior_events: Iterable[Mapping[str, Any]],
    detector: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if detector is None:
        detector, _, boundary_registry = load_v4_dynamics_configs()
    else:
        boundary_registry = RegistryBundle.load().boundaries
        validate_jump_detector(detector, boundary_registry=boundary_registry)

    detector_hash = content_hash(detector)
    out = []
    for event in behavior_events:
        validate_behavior_event(event, boundary_registry=boundary_registry)
        matched = [rule for rule in detector["rules"] if _rule_matches(event, rule)]
        if not matched:
            continue
        record = {
            "schema": JUMP_CANDIDATE_SCHEMA,
            "detector_version": detector["version"],
            "detector_hash": detector_hash,
            "candidate_id": f"{event['trajectory_id']}:JUMPV4:{event['event_index']:04d}",
            "behavior_event_id": event["behavior_event_id"],
            "trajectory_id": event["trajectory_id"],
            "branch_id": event.get("branch_id"),
            "event_index": event["event_index"],
            "turn": event["turn"],
            "actor": event["actor"],
            "boundary_id": event["boundary_id"],
            "action_type": event["action_type"],
            "state_before_hash": event.get("state_before_hash"),
            "state_after_hash": event.get("state_after_hash"),
            "state_hash_changed": _state_hash_changed(event),
            "matched_rule_ids": sorted(rule["rule_id"] for rule in matched),
            "candidate_types": sorted({rule["candidate_type"] for rule in matched}),
            "source_refs": list(event.get("source_refs") or []),
            "behavior_event_hash": event.get("behavior_event_hash"),
            "jump_truth_status": "STRUCTURAL_CANDIDATE_ONLY",
            "semantic_status": NOT_ADJUDICATED,
            "warning": (
                "Structural Jump candidate only. The detector localizes observable displacement; "
                "it does not establish C/P/R, authorization failure, Tension, Escape Propensity, or causal effect."
            ),
        }
        record["candidate_hash"] = content_hash(record)
        out.append(record)
    return out


def detect_operational_boundary_crossings(
    behavior_events: Iterable[Mapping[str, Any]],
    operational_set: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if operational_set is None:
        _, operational_set, boundary_registry = load_v4_dynamics_configs()
    else:
        boundary_registry = RegistryBundle.load().boundaries
        validate_operational_boundary_set(operational_set, boundary_registry=boundary_registry)

    config_hash = content_hash(operational_set)
    out = []
    for event in behavior_events:
        validate_behavior_event(event, boundary_registry=boundary_registry)
        for rule in operational_set["boundaries"]:
            if not _crossing_matches(event, rule):
                continue
            record = {
                "schema": OPERATIONAL_CROSSING_SCHEMA,
                "operational_boundary_set_version": operational_set["version"],
                "operational_boundary_set_hash": config_hash,
                "crossing_id": (
                    f"{event['trajectory_id']}:OPV4:{event['event_index']:04d}:"
                    f"{rule['operational_boundary_id']}"
                ),
                "behavior_event_id": event["behavior_event_id"],
                "trajectory_id": event["trajectory_id"],
                "branch_id": event.get("branch_id"),
                "event_index": event["event_index"],
                "turn": event["turn"],
                "actor": event["actor"],
                "measurement_boundary_id": event["boundary_id"],
                "operational_boundary_id": rule["operational_boundary_id"],
                "authority_class": rule.get("authority_class"),
                "action_type": event["action_type"],
                "state_hash_changed": _state_hash_changed(event),
                "source_refs": list(event.get("source_refs") or []),
                "penetration_status": NOT_ADJUDICATED,
                "warning": (
                    "Mechanical operational crossing only. It is not automatically Authority Penetration "
                    "and does not establish that the crossing was unauthorized."
                ),
            }
            record["crossing_hash"] = content_hash(record)
            out.append(record)
    return out


def slice_behavior_events_for_branch(
    behavior_events: Iterable[Mapping[str, Any]], *, branch_start_turn: int
) -> list[dict[str, Any]]:
    _require(isinstance(branch_start_turn, int) and branch_start_turn >= 0, "branch_start_turn_invalid")
    return [dict(row) for row in behavior_events if int(row.get("turn", -1)) > branch_start_turn]


def _candidate_type_counts(candidates: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for row in candidates:
        counts.update(row.get("candidate_types") or [])
    return dict(sorted(counts.items()))


def build_system_dynamics_view(
    adapter_result: Mapping[str, Any],
    *,
    branch_start_turn: int | None = None,
    detector: Mapping[str, Any] | None = None,
    operational_set: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    _require(isinstance(adapter_result, Mapping), "adapter_result_required")
    behavior_events = adapter_result.get("behavior_events")
    measurement = adapter_result.get("system_trajectory_measurement")
    summary = adapter_result.get("summary")
    _require(isinstance(behavior_events, list), "adapter_behavior_events_required")
    _require(isinstance(measurement, Mapping), "adapter_measurement_required")
    _require(isinstance(summary, Mapping), "adapter_summary_required")

    detector_cfg, operational_cfg, _ = load_v4_dynamics_configs()
    if detector is not None:
        detector_cfg = dict(detector)
        validate_jump_detector(detector_cfg, boundary_registry=RegistryBundle.load().boundaries)
    if operational_set is not None:
        operational_cfg = dict(operational_set)
        validate_operational_boundary_set(
            operational_cfg, boundary_registry=RegistryBundle.load().boundaries
        )

    if branch_start_turn is None:
        effective_events = [dict(row) for row in behavior_events]
        slicing = {
            "mode": "FULL_TRAJECTORY",
            "branch_start_turn": None,
            "rule": None,
        }
    else:
        effective_events = slice_behavior_events_for_branch(
            behavior_events, branch_start_turn=branch_start_turn
        )
        slicing = {
            "mode": "BRANCH_CONTINUATION_ONLY",
            "branch_start_turn": branch_start_turn,
            "rule": "behavior_event.turn > branch_start_turn",
        }

    candidates = detect_structural_jump_candidates(effective_events, detector_cfg)
    crossings = detect_operational_boundary_crossings(effective_events, operational_cfg)
    first = candidates[0] if candidates else None

    if first is None:
        post_candidate_events = []
        post_candidate_crossings = []
        retrospective = []
        post_candidate_actors = []
    else:
        first_index = first["event_index"]
        post_candidate_events = [
            row for row in effective_events if row.get("event_index", -1) > first_index
        ]
        post_candidate_crossings = [
            row for row in crossings if row.get("event_index", -1) > first_index
        ]
        retrospective = [
            row
            for row in post_candidate_events
            if row.get("boundary_id") == "FINAL_REOPEN"
            and row.get("action_type") == "revise"
            and row.get("realization_status") == "REALIZED"
        ]
        post_candidate_actors = sorted(
            {
                row.get("actor")
                for row in post_candidate_events
                if row.get("actor") not in (None, "ENVIRONMENT")
            }
        )

    updated_measurement = copy.deepcopy(measurement)
    updated_measurement["r2"].update(
        {
            "jump_candidate_count": len(candidates),
            "jump_candidate_refs": [row["candidate_id"] for row in candidates],
            "first_jump_candidate_ref": first["candidate_id"] if first else None,
            "first_jump_turn": first["turn"] if first else None,
            "jump_type_counts": _candidate_type_counts(candidates),
            "jump_detection_status": "STRUCTURAL_CANDIDATE_DETECTOR_v0.1",
            "jump_truth_status": NOT_ADJUDICATED,
        }
    )
    updated_measurement["r3"].update(
        {
            "descendant_event_count": 0,
            "affected_agent_count": 0,
            "operational_boundary_crossing_count": len(crossings),
            "post_first_candidate_operational_crossing_count": len(post_candidate_crossings),
            "post_first_candidate_event_count": len(post_candidate_events),
            "post_first_candidate_actor_ids": post_candidate_actors,
            "lineage_status": "NOT_DERIVED_POST_CANDIDATE_ORDER_ONLY",
            "penetration_status": NOT_ADJUDICATED,
            "warning": (
                "Post-candidate event/crossing counts are temporal-order measurements only. "
                "They are not descendants, causal lineage, or Authority Penetration."
            ),
        }
    )
    updated_measurement["r4"].update(
        {
            "retrospective_window_count": len(retrospective),
            "retrospective_window_refs": [row["behavior_event_id"] for row in retrospective],
            "retrospective_detection_status": "STRUCTURAL_REVISION_WINDOW_ONLY",
            "semantic_r_status": NOT_ADJUDICATED,
        }
    )
    updated_measurement["detector_binding"] = {
        "schema": detector_cfg["schema"],
        "version": detector_cfg["version"],
        "hash": content_hash(detector_cfg),
    }
    updated_measurement["operational_boundary_binding"] = {
        "schema": operational_cfg["schema"],
        "version": operational_cfg["version"],
        "hash": content_hash(operational_cfg),
    }
    updated_measurement["behavior_slice"] = slicing
    updated_measurement["measurement_hash"] = content_hash(
        {key: value for key, value in updated_measurement.items() if key != "measurement_hash"}
    )

    view = {
        "schema": DYNAMICS_VIEW_SCHEMA,
        "trajectory_id": measurement.get("trajectory_id"),
        "source_trace_hash": summary.get("source_trace_hash"),
        "adapter_output_hash": summary.get("adapter_output_hash"),
        "behavior_slice": slicing,
        "detector_binding": updated_measurement["detector_binding"],
        "operational_boundary_binding": updated_measurement["operational_boundary_binding"],
        "effective_behavior_event_count": len(effective_events),
        "jump_candidates": candidates,
        "operational_crossings": crossings,
        "system_trajectory_measurement": updated_measurement,
        "semantic_status": NOT_ADJUDICATED,
        "scientific_status": "OFFLINE_STRUCTURAL_MEASUREMENT_ONLY",
    }
    view["dynamics_view_hash"] = content_hash(view)
    return view
