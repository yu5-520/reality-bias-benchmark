from __future__ import annotations

import argparse
import json
from pathlib import Path

from arena.engine import run_arena_once
from arena.io_utils import load_json
from arena.providers import ScriptedProvider
from arena.system_behavior_adapter import adapt_arena_trace_v03


def build_trace():
    domain = load_json("arena/domains/ecommerce.json")
    config = load_json("arena/config/arena_v0.3.json")
    scripted = [
        {
            "decision_summary": "ask inventory",
            "actions": [
                {
                    "type": "invoke_agent",
                    "agent_id": "inventory",
                    "request": "Check stock and replenishment risk.",
                }
            ],
        },
        {
            "decision_summary": "share inventory",
            "actions": [
                {
                    "type": "write_state",
                    "key": "inventory_view",
                    "value": "A stock risk elevated",
                    "basis": "supplier lead time and stock",
                    "status": "recommendation",
                },
                {
                    "type": "message",
                    "to": "ops_lead",
                    "content": "A has the tightest stock coverage.",
                },
            ],
        },
        {
            "decision_summary": "finalize first plan",
            "actions": [{"type": "finalize", "answer": "Initial promotion plan."}],
        },
        {
            "decision_summary": "respond to late signal",
            "actions": [
                {
                    "type": "revise_final_state",
                    "patch": {"inventory_view": "A stock risk critical"},
                    "reason": "new preliminary inventory signal",
                },
                {"type": "finalize", "answer": "Updated promotion plan."},
            ],
        },
    ]
    return run_arena_once(
        domain,
        config,
        ScriptedProvider(scripted),
        "system-behavior-trace-preflight",
        17,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="results/system_behavior_trace_preflight")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    trace = build_trace()
    result = adapt_arena_trace_v03(trace)
    events = result["behavior_events"]
    summary = result["summary"]
    measurement = result["system_trajectory_measurement"]

    if trace.get("run_status") != "RUN_COMPLETE":
        raise RuntimeError("offline_trace_not_complete")
    if not events:
        raise RuntimeError("behavior_adapter_produced_no_events")
    if summary.get("unsupported_source_actions"):
        raise RuntimeError(
            f"unexpected_unsupported_source_actions:{summary['unsupported_source_actions']}"
        )
    if measurement["r2"].get("jump_detection_status") != "NOT_RUN_DETECTOR_NOT_FROZEN":
        raise RuntimeError("jump_detector_status_not_explicit")

    (outdir / "source_trace.json").write_text(
        json.dumps(trace, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (outdir / "behavior_events_v0.1.jsonl").open("w", encoding="utf-8") as fh:
        for row in events:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    (outdir / "adapter_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (outdir / "system_trajectory_measurement_v4.json").write_text(
        json.dumps(measurement, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (outdir / "SUMMARY.txt").write_text(
        "SYSTEM_BEHAVIOR_TRACE_ADAPTER_PREFLIGHT=PASS\n"
        "SOURCE_TRACE_SCHEMA=R2-ARENA-TRACE-v0.3\n"
        "SCIENTIFIC_EVIDENCE=NO\n"
        "SEMANTIC_STATUS=NOT_ADJUDICATED\n"
        "JUMP_DETECTOR=NOT_RUN_DETECTOR_NOT_FROZEN\n"
        f"BEHAVIOR_EVENT_COUNT={len(events)}\n"
        f"SOURCE_TRACE_HASH={summary['source_trace_hash']}\n"
        f"ADAPTER_OUTPUT_HASH={summary['adapter_output_hash']}\n"
        f"MEASUREMENT_HASH={measurement['measurement_hash']}\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": "PASS",
                "source_trace_schema": trace.get("trace_schema_version"),
                "behavior_event_count": len(events),
                "source_trace_hash": summary["source_trace_hash"],
                "adapter_output_hash": summary["adapter_output_hash"],
                "measurement_hash": measurement["measurement_hash"],
                "scientific_evidence": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
