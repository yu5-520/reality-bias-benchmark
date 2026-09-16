from __future__ import annotations

import argparse
import json
from pathlib import Path

from arena.system_behavior import (
    RegistryBundle,
    build_system_trajectory_measurement,
    make_behavior_event,
)


def build_fixture() -> tuple[list[dict], dict]:
    RegistryBundle.load()

    events = [
        make_behavior_event(
            behavior_event_id="preflight:0",
            trajectory_id="system-behavior-preflight",
            event_index=0,
            turn=0,
            boundary_id="CONTEXT_RAG_HANDOFF",
            actor="system",
            action_type="read",
            realization_status="REALIZED",
            state_before_hash="s0",
            state_after_hash="s0",
            source_refs=["fixture:context"],
        ),
        make_behavior_event(
            behavior_event_id="preflight:1",
            trajectory_id="system-behavior-preflight",
            event_index=1,
            turn=1,
            boundary_id="SHARED_STATE",
            actor="agent_a",
            action_type="write",
            realization_status="REALIZED",
            state_before_hash="s0",
            state_after_hash="s1",
            target_ref="shared:status",
            source_refs=["preflight:0"],
            parent_event_refs=["preflight:0"],
            structured_diff={"status": {"before": "provisional", "after": "fact"}},
        ),
        make_behavior_event(
            behavior_event_id="preflight:2",
            trajectory_id="system-behavior-preflight",
            event_index=2,
            turn=2,
            boundary_id="MESSAGE_HANDOFF",
            actor="agent_a",
            action_type="message",
            realization_status="REALIZED",
            state_before_hash="s1",
            state_after_hash="s1",
            target_ref="agent_b",
            source_refs=["preflight:1"],
            parent_event_refs=["preflight:1"],
        ),
        make_behavior_event(
            behavior_event_id="preflight:3",
            trajectory_id="system-behavior-preflight",
            event_index=3,
            turn=3,
            boundary_id="RECOVERY_CHECKPOINT",
            actor="system",
            action_type="revise",
            realization_status="REALIZED",
            state_before_hash="s1",
            state_after_hash="s2",
            target_ref="shared:status",
            source_refs=["preflight:1"],
            parent_event_refs=["preflight:2"],
        ),
    ]

    measurement = build_system_trajectory_measurement(
        measurement_id="system-behavior-preflight:m1",
        trajectory_id="system-behavior-preflight",
        source_trace_hash="fixture-trace-hash",
        source_version="OFFLINE_FIXTURE_v0.1",
        termination_status="RUN_COMPLETE",
        behavior_events=events,
        jump_candidate_refs=["jump-candidate:preflight:1"],
        first_jump_candidate_ref="jump-candidate:preflight:1",
        first_jump_turn=1,
        descendant_event_count=2,
        affected_agent_count=2,
        operational_boundary_crossing_count=1,
        retrospective_window_refs=["retrospective:preflight:3"],
        experimental_variables=[
            {
                "variable_id": "EPISTEMIC_STATUS_DOWNGRADE",
                "stage": "MID",
                "registry_version": "0.1",
                "condition": "OFFLINE_FIXTURE_ONLY",
                "intervention_hash": None,
            }
        ],
    )
    return events, measurement


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="results/system_behavior_preflight")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    events, measurement = build_fixture()

    with (outdir / "behavior_events.jsonl").open("w", encoding="utf-8") as fh:
        for row in events:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    (outdir / "system_trajectory_measurement_v4.json").write_text(
        json.dumps(measurement, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (outdir / "SUMMARY.txt").write_text(
        "SYSTEM_BEHAVIOR_PREFLIGHT=PASS\n"
        "SCIENTIFIC_EVIDENCE=NO\n"
        "SEMANTIC_STATUS=NOT_ADJUDICATED\n"
        f"BEHAVIOR_EVENT_COUNT={measurement['behavior_event_count']}\n"
        f"MEASUREMENT_HASH={measurement['measurement_hash']}\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "PASS",
        "outdir": str(outdir),
        "behavior_event_count": measurement["behavior_event_count"],
        "measurement_hash": measurement["measurement_hash"],
        "scientific_evidence": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
