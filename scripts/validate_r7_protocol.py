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
EXPECTED_PROTOCOL = "RB-R7-STRUCTURAL-INERTIA-CONTROL-v1.0"
EXPECTED_MEASUREMENT = "RB-PROCESS-REALITY-MECHANISM-MEASUREMENT-v0.4"


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(2)


def load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # fail closed
        fail(f"cannot load fixture {path}: {exc}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def validate(doc: dict) -> None:
    require(doc.get("protocol_id") == EXPECTED_PROTOCOL, "unexpected protocol_id")
    require(doc.get("measurement_schema") == EXPECTED_MEASUREMENT, "measurement schema drift")

    parent = doc.get("frozen_parent") or {}
    jump = doc.get("jump") or {}
    payload = doc.get("semantic_payload") or {}
    arms = doc.get("arms") or {}
    integrity = doc.get("integrity") or {}

    require(bool(parent.get("parent_state_hash")), "missing frozen parent hash")
    require(bool(parent.get("source_run_id")), "missing source run id")
    require(bool(jump.get("jump_id")), "missing jump id")
    require(bool(jump.get("source_event")), "missing jump source event")
    require(bool(jump.get("target_path")), "missing jump target path")
    require(bool(payload.get("payload_id")), "missing semantic payload id")
    require(payload.get("target_path") == jump.get("target_path"), "payload target must equal J0 target")

    require(set(arms) == set(REQUIRED_ARMS), "fixture must contain exactly C1, C2 and C3 arms")

    c1 = arms["C1_ONE_SHOT"]
    require(c1.get("mode") == "one_shot_free_continuation", "C1 mode mismatch")
    require(c1.get("propagation_policy") == "first_post_jump_agent_turn_only", "C1 propagation policy mismatch")
    require(c1.get("max_exposures") == 1, "C1 must expose payload exactly once")
    require(c1.get("persistent_parent_mutation") is False, "C1 must not mutate frozen parent")

    c2 = arms["C2_PERSISTENT_FIELD"]
    require(c2.get("mode") == "persistent_field_propagation", "C2 mode mismatch")
    require(c2.get("propagation_policy") == "inject_same_payload_into_each_eligible_post_jump_turn", "C2 propagation policy mismatch")
    require(c2.get("max_exposures") is None, "C2 persistent propagation must not be capped by the fixture")
    require(c2.get("persistent_parent_mutation") is False, "C2 must not mutate frozen parent")

    c3 = arms["C3_ALR"]
    require(c3.get("mode") == "authority_localized_recovery", "C3 mode mismatch")
    require(c3.get("propagation_policy") == "structural_recovery", "C3 propagation policy mismatch")
    require(c3.get("authority_anchor_policy") == "earliest_authority_violating_ancestor", "C3 authority anchor mismatch")
    require(c3.get("closure_policy") == "registered_dependency_closure", "C3 closure policy mismatch")
    require(c3.get("preserve_unaffected") is True, "C3 must preserve unaffected nodes")
    require(c3.get("revision_required") is True, "C3 must create a new revision lineage")
    require(c3.get("persistent_parent_mutation") is False, "C3 must not mutate frozen parent")

    for key in (
        "semantic_payload_equal_across_arms",
        "same_parent",
        "same_jump",
        "same_horizon",
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
    print(f"jump={doc['jump']['jump_id']} source_event={doc['jump']['source_event']}")
    print(f"payload={doc['semantic_payload']['payload_id']}")
    print(f"measurement_schema={doc['measurement_schema']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
