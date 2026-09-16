from __future__ import annotations

import argparse
import json
from pathlib import Path

from arena.engine import run_arena_once
from arena.io_utils import load_json
from arena.providers import ScriptedProvider
from arena.system_behavior_adapter import adapt_arena_trace_v03
from arena.system_behavior_dynamics_v4 import build_system_dynamics_view


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
        "system-behavior-dynamics-preflight",
        23,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="results/system_behavior_dynamics_preflight")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    trace = build_trace()
    adapted = adapt_arena_trace_v03(trace)
    view = build_system_dynamics_view(adapted)
    measurement = view["system_trajectory_measurement"]
    candidates = view["jump_candidates"]
    crossings = view["operational_crossings"]

    if trace.get("run_status") != "RUN_COMPLETE":
        raise RuntimeError("offline_trace_not_complete")
    if len(candidates) != 3:
        raise RuntimeError(f"unexpected_jump_candidate_count:{len(candidates)}")
    if len(crossings) != 5:
        raise RuntimeError(f"unexpected_operational_crossing_count:{len(crossings)}")
    if measurement["r2"].get("jump_truth_status") != "NOT_ADJUDICATED":
        raise RuntimeError("jump_truth_was_semantically_promoted")
    if measurement["r3"].get("penetration_status") != "NOT_ADJUDICATED":
        raise RuntimeError("penetration_was_semantically_promoted")
    if measurement["r3"].get("descendant_event_count") != 0:
        raise RuntimeError("temporal_order_was_mislabeled_as_lineage")

    (outdir / "source_trace.json").write_text(
        json.dumps(trace, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (outdir / "adapter_summary.json").write_text(
        json.dumps(adapted["summary"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (outdir / "behavior_events_v0.1.jsonl").open("w", encoding="utf-8") as fh:
        for row in adapted["behavior_events"]:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with (outdir / "structural_jump_candidates_v0.1.jsonl").open("w", encoding="utf-8") as fh:
        for row in candidates:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with (outdir / "operational_boundary_crossings_v0.1.jsonl").open("w", encoding="utf-8") as fh:
        for row in crossings:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    (outdir / "system_trajectory_measurement_v4.json").write_text(
        json.dumps(measurement, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (outdir / "system_dynamics_view_v4.json").write_text(
        json.dumps(view, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (outdir / "SUMMARY.txt").write_text(
        "SYSTEM_BEHAVIOR_DYNAMICS_PREFLIGHT=PASS\n"
        "SCIENTIFIC_EVIDENCE=NO\n"
        "JUMP_TRUTH_STATUS=NOT_ADJUDICATED\n"
        "PENETRATION_STATUS=NOT_ADJUDICATED\n"
        "LINEAGE_STATUS=NOT_DERIVED_POST_CANDIDATE_ORDER_ONLY\n"
        f"JUMP_CANDIDATE_COUNT={len(candidates)}\n"
        f"OPERATIONAL_CROSSING_COUNT={len(crossings)}\n"
        f"DETECTOR_HASH={measurement['detector_binding']['hash']}\n"
        f"OPERATIONAL_BOUNDARY_SET_HASH={measurement['operational_boundary_binding']['hash']}\n"
        f"DYNAMICS_VIEW_HASH={view['dynamics_view_hash']}\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": "PASS",
                "jump_candidate_count": len(candidates),
                "operational_crossing_count": len(crossings),
                "detector_hash": measurement["detector_binding"]["hash"],
                "operational_boundary_set_hash": measurement["operational_boundary_binding"]["hash"],
                "dynamics_view_hash": view["dynamics_view_hash"],
                "scientific_evidence": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
