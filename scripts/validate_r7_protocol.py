#!/usr/bin/env python3
"""Offline integrity validator for the R7 three-arm protocol fixture.

This validator is intentionally model-free. It checks only protocol invariants that
must hold before any paid subject run is allowed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_ARMS = ("C1_ONE_SHOT", "C2_PERSISTENT_FIELD", "C3_ALR")
EXPECTED_PROTOCOL = "RB-R7-STRUCTURAL-INERTIA-CONTROL-v1.2"
EXPECTED_MEASUREMENT = "RB-PROCESS-REALITY-MECHANISM-MEASUREMENT-v0.4"


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(2)


def load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        fail(f"cannot load fixture {path}: {exc}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def validate(doc: dict) -> None:
    require(doc.get("protocol_id") == EXPECTED_PROTOCOL, "unexpected protocol_id")
    require(doc.get("measurement_schema") == EXPECTED_MEASUREMENT, "measurement schema drift")

    parent = doc.get("frozen_parent") or {}
    jump = doc.get("jump") or {}
    checkpoint = doc.get("recovery_checkpoint") or {}
    payload = doc.get("semantic_payload") or {}
    horizon = doc.get("matched_horizon") or {}
    arms = doc.get("arms") or {}
    integrity = doc.get("integrity") or {}

    for key in (
        "parent_state_hash",
        "source_run_id",
        "source_plan_hash",
        "prepared_workflow_run_id",
        "prepared_artifact_id",
        "prepared_artifact_name",
        "prepared_artifact_digest",
        "prepared_inner_tar_sha256",
        "source_raw_workflow_run_id",
        "source_raw_artifact_id",
        "source_raw_artifact_name",
        "source_raw_artifact_digest",
        "source_raw_inner_tar_sha256",
    ):
        require(parent.get(key) not in (None, ""), f"missing frozen parent/source binding: {key}")

    require(bool(jump.get("jump_id")), "missing jump id")
    require(bool(jump.get("source_event")), "missing jump source event")
    require(isinstance(jump.get("source_event_index"), int) and jump["source_event_index"] >= 0, "missing/invalid jump source event index")
    require(bool(jump.get("state_key")), "missing jump state key")
    require(bool(jump.get("target_path")), "missing jump target path")

    require(checkpoint.get("anchor_ref") == "before_turn:8", "unexpected C3 recovery checkpoint anchor")
    require(bool(checkpoint.get("state_hash")), "missing C3 recovery checkpoint hash")
    require(checkpoint.get("turns") == 7, "C3 recovery checkpoint must precede J0 turn")
    require(checkpoint.get("event_count") == jump.get("source_event_index"), "C3 checkpoint event count must stop immediately before J0")
    require(checkpoint.get("queue_head") == jump.get("actor"), "C3 checkpoint must resume the J0 actor")
    require(checkpoint.get("relation_to_jump") == "immediate_pre_authority_ancestor_turn_checkpoint", "C3 checkpoint relation mismatch")
    require(checkpoint.get("common_reference_parent_remains") == "after_turn:8", "C3 must preserve common post-J0 reference parent")
    require(checkpoint.get("state_hash") != parent.get("parent_state_hash"), "C3 rollback checkpoint must be distinct from common reference parent")

    require(bool(payload.get("payload_id")), "missing semantic payload id")
    require(payload.get("target_path") == jump.get("target_path"), "payload target must equal J0 target")
    require(payload.get("operation") == "replace_prompt_visible_value_or_authority_commit_status", "semantic payload operation mismatch")

    require(bool(horizon.get("horizon_id")), "missing matched horizon id")
    require(horizon.get("distance_basis") == "post_jump_agent_turn", "R7 horizon distance basis mismatch")
    require(isinstance(horizon.get("post_jump_turn_cap"), int) and horizon["post_jump_turn_cap"] >= 1, "R7 post-Jump turn cap must be positive")
    require(horizon.get("termination_policy") == "natural_termination_or_common_cap", "R7 termination policy mismatch")
    require(horizon.get("early_termination_policy") == "record_as_censored_not_extended", "R7 early termination must preserve censoring")
    require(
        horizon.get("comparison_policy") == "compare_only_observed_matched_distances_and_preserve_censoring",
        "R7 comparison policy mismatch",
    )

    require(set(arms) == set(REQUIRED_ARMS), "fixture must contain exactly C1, C2 and C3 arms")
    horizon_id = horizon["horizon_id"]
    common_cap = horizon["post_jump_turn_cap"]

    c1 = arms["C1_ONE_SHOT"]
    require(c1.get("mode") == "one_shot_free_continuation", "C1 mode mismatch")
    require(c1.get("propagation_policy") == "first_post_jump_agent_turn_only", "C1 propagation policy mismatch")
    require(c1.get("max_exposures") == 1, "C1 must expose payload exactly once")
    require(c1.get("observation_horizon_id") == horizon_id, "C1 horizon mismatch")
    require(c1.get("persistent_parent_mutation") is False, "C1 must not mutate frozen parent")

    c2 = arms["C2_PERSISTENT_FIELD"]
    require(c2.get("mode") == "persistent_field_propagation", "C2 mode mismatch")
    require(
        c2.get("propagation_policy") == "inject_same_payload_into_each_eligible_post_jump_turn_within_common_horizon",
        "C2 propagation policy mismatch",
    )
    require(c2.get("max_exposures") == common_cap, "C2 exposure cap must equal the common post-Jump horizon")
    require(c2.get("observation_horizon_id") == horizon_id, "C2 horizon mismatch")
    require(c2.get("persistent_parent_mutation") is False, "C2 must not mutate frozen parent")

    c3 = arms["C3_ALR"]
    require(c3.get("mode") == "authority_localized_recovery", "C3 mode mismatch")
    require(
        c3.get("propagation_policy") == "rollback_to_pre_authority_checkpoint_reexecute_and_transform_target_authority_commit_once",
        "C3 propagation policy mismatch",
    )
    require(c3.get("authority_anchor_policy") == "earliest_authority_violating_ancestor", "C3 authority anchor mismatch")
    require(
        c3.get("closure_policy") == "rollback_reexecutes_authority_ancestor_turn_then_observes_new_descendant_lineage",
        "C3 closure policy mismatch",
    )
    require(c3.get("preserve_unaffected") is True, "C3 must preserve unaffected prefix")
    require(c3.get("revision_required") is True, "C3 must create a new revision lineage")
    require(c3.get("observation_horizon_id") == horizon_id, "C3 horizon mismatch")
    require(c3.get("common_reference_parent_mutation") is False, "C3 must not mutate common reference parent")
    require(c3.get("provider_internal_state_replayed") is False, "C3 must not claim provider hidden-state replay")

    for key in (
        "semantic_payload_equal_across_arms",
        "same_reference_parent",
        "same_jump",
        "same_horizon",
        "c3_rollback_checkpoint_explicit",
        "early_termination_preserved_as_censoring",
        "provider_hidden_state_replay_forbidden",
        "fail_closed",
    ):
        require(integrity.get(key) is True, f"integrity invariant not asserted: {key}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "fixture",
        nargs="?",
        default="configs/r7/r7_three_arm_fixture.example.json",
        help="R7 fixture to validate",
    )
    args = parser.parse_args()

    path = Path(args.fixture)
    doc = load_json(path)
    validate(doc)

    print("PASS: R7 protocol fixture satisfies offline fail-closed invariants")
    print(f"fixture={path}")
    print(f"parent={doc['frozen_parent']['parent_state_hash']}")
    print(f"source_plan={doc['frozen_parent']['source_plan_hash']}")
    print(f"jump={doc['jump']['jump_id']} source_event={doc['jump']['source_event']}")
    print(f"recovery_checkpoint={doc['recovery_checkpoint']['anchor_ref']}:{doc['recovery_checkpoint']['state_hash']}")
    print(f"payload={doc['semantic_payload']['payload_id']}")
    print(f"horizon={doc['matched_horizon']['horizon_id']} cap={doc['matched_horizon']['post_jump_turn_cap']}")
    print(f"measurement_schema={doc['measurement_schema']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
