#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .branch_plan_one_shot import verify_one_shot_branch_plan
from .io_utils import load_json, load_jsonl, write_jsonl
from .process_reality_dynamics_v0_1 import build_process_reality_measurement, compare_process_reality
from .system_behavior_adapter import adapt_arena_trace_v03
from .system_behavior_dynamics_v4 import build_system_dynamics_view
from .system_behavior_lineage_v4 import build_system_lineage_view


def load_plan_bundle(plan_dir):
    p = Path(plan_dir)
    bundle = {
        "plan": load_json(p / "branch_plan.json"),
        "parent_snapshot": load_json(p / "parent_snapshot.json"),
        "one_shot_envelope": load_json(p / "one_shot_intervention_envelope.json"),
        "branch_rows": load_jsonl(p / "branch_execution_manifest.jsonl"),
        "branch_manifests": load_jsonl(p / "branch_manifests.jsonl"),
    }
    verify_one_shot_branch_plan(bundle)
    return bundle


def derive(plan_dir, traces_path):
    bundle = load_plan_bundle(plan_dir)
    traces = load_jsonl(traces_path)
    rows = {x["run_id"]: x for x in bundle["branch_rows"]}
    measurements = []
    by_run = {}
    for trace in traces:
        row = rows.get(trace.get("run_id"))
        if row is None:
            raise ValueError("trace_not_in_one_shot_plan:" + str(trace.get("run_id")))
        adapted = adapt_arena_trace_v03(trace)
        dynamics = build_system_dynamics_view(adapted)
        lineage = build_system_lineage_view(adapted, dynamics_view=dynamics)
        m = build_process_reality_measurement(
            trace=trace,
            adapter_result=adapted,
            dynamics_view=dynamics,
            lineage_view=lineage,
            target_source_event_index=bundle["plan"]["common_identity"]["selected_candidate_event_index"],
            branch_start_turn=bundle["parent_snapshot"]["turns"],
        )
        m.update({"pair_id": row["pair_id"], "condition_id": row["condition_id"], "replicate_index": row["replicate_index"]})
        measurements.append(m)
        by_run[trace["run_id"]] = m
    comparisons = []
    for pair_id in sorted({x["pair_id"] for x in bundle["branch_rows"]}):
        pair_rows = [x for x in bundle["branch_rows"] if x["pair_id"] == pair_id]
        control_row = next(x for x in pair_rows if x["condition_id"] == "CONTROL_CONTINUATION")
        intervention_row = next(x for x in pair_rows if x["condition_id"] == "ONE_SHOT_JUMP_INTERVENTION")
        c = by_run.get(control_row["run_id"])
        i = by_run.get(intervention_row["run_id"])
        if c and i and c["run_status"] == i["run_status"] == "RUN_COMPLETE":
            comparison = compare_process_reality(c, i, comparison_id=pair_id + ":PROCESS_REALITY")
            comparison["pair_id"] = pair_id
            comparisons.append(comparison)
    return measurements, comparisons


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan-dir", required=True)
    ap.add_argument("--traces", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_process_measurement_dir")
    out.mkdir(parents=True)
    measurements, comparisons = derive(args.plan_dir, args.traces)
    write_jsonl(out / "process_reality_measurements.jsonl", measurements)
    write_jsonl(out / "paired_process_comparisons.jsonl", comparisons)
    summary = {
        "schema": "RB-PROCESS-REALITY-DERIVATION-SUMMARY-v0.1",
        "measurement_count": len(measurements),
        "complete_pair_comparison_count": len(comparisons),
        "semantic_status": "NOT_ADJUDICATED",
        "paid_evaluator_called": False
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("PROCESS_REALITY_MEASUREMENTS=" + str(len(measurements)))
    print("PAIRED_COMPARISONS=" + str(len(comparisons)))


if __name__ == "__main__":
    main()
