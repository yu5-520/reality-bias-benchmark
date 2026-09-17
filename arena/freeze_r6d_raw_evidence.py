#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, sha256_file
from .prepare_r6d_specificity_plan import load_r6d_runtime_plan
from .r5r6_specificity_atomic_v0_2 import S0, S1, S2

FREEZE_SCHEMA = "RB-R6D-SPECIFICITY-RAW-EVIDENCE-FREEZE-v0.1"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _hash_without(row: dict, key: str) -> str:
    material = copy.deepcopy(row)
    material.pop(key, None)
    return stable_hash(material)


def freeze_raw_evidence(*, plan_dir: str | Path, raw_dir: str | Path, output_path: str | Path) -> dict:
    bundle = load_r6d_runtime_plan(plan_dir)
    raw = Path(raw_dir)
    traces_path = raw / "traces.jsonl"
    summary_path = raw / "run_summary.json"
    errors_path = raw / "errors.jsonl"

    _require(traces_path.is_file(), "r6d_raw_traces_missing")
    _require(summary_path.is_file(), "r6d_run_summary_missing")
    traces = load_jsonl(traces_path)
    summary = load_json(summary_path)
    plan = bundle["plan"]

    _require(summary.get("schema") == "RB-R6D-SPECIFICITY-RUN-SUMMARY-v0.1", "r6d_run_summary_schema_invalid")
    _require(summary.get("design_hash") == plan["design_hash"], "r6d_summary_design_hash_mismatch")
    _require(summary.get("runtime_plan_hash") == plan["plan_hash"], "r6d_summary_plan_hash_mismatch")
    _require(summary.get("provider_calls_are_real") is True, "r6d_freeze_requires_real_subject_output")
    _require(summary.get("authorization_consumed") is True, "r6d_freeze_requires_consumed_authorization")
    _require(summary.get("automatic_paid_evaluator_called") is False, "r6d_paid_evaluator_must_not_run")
    _require(summary.get("semantic_cpr_status") == "NOT_ADJUDICATED", "r6d_semantic_status_invalid")
    _require(summary.get("same_parent_repeats_are_independent_samples") is False, "r6d_independence_overclaim_forbidden")
    _require(summary.get("terminal_outcome_is_primary") is False, "r6d_terminal_primary_forbidden")
    _require(len(traces) == int(summary.get("preserved_trace_count", -1)), "r6d_trace_count_summary_mismatch")

    condition_counts = {S0: 0, S1: 0, S2: 0}
    exposure_counts = {S0: 0, S1: 0, S2: 0}
    trace_hashes = []
    for trace in traces:
        cond = trace.get("r6d_condition", {}).get("condition_id")
        _require(cond in condition_counts, "r6d_trace_condition_invalid")
        condition_counts[cond] += 1
        exposure = trace.get("r6d_exposure_integrity", {}).get("direct_experiment_origin_exposure_count")
        _require(exposure in (0, 1), "r6d_trace_exposure_count_invalid")
        exposure_counts[cond] += int(exposure)
        _require(trace.get("r6d_condition", {}).get("semantic_cpr_status") == "NOT_ADJUDICATED", "r6d_trace_semantic_status_invalid")
        _require(trace.get("r6d_condition", {}).get("provider_internal_state_replayed") is False, "r6d_trace_hidden_state_replay_forbidden")
        trace_hashes.append(stable_hash(trace))

    _require(condition_counts == {S0: 3, S1: 3, S2: 3}, "r6d_frozen_condition_counts_invalid")
    _require(exposure_counts == {S0: 0, S1: 3, S2: 3}, "r6d_frozen_exposure_counts_invalid")

    files = {
        "traces_jsonl_sha256": sha256_file(traces_path),
        "run_summary_sha256": sha256_file(summary_path),
        "runtime_plan_json_sha256": sha256_file(Path(plan_dir) / "r6d_plan.json"),
        "source_parent_snapshot_sha256": sha256_file(Path(plan_dir) / "source_parent_snapshot.json"),
        "s1_envelope_sha256": sha256_file(Path(plan_dir) / "s1_envelope.json"),
        "s2_envelope_sha256": sha256_file(Path(plan_dir) / "s2_envelope.json"),
        "bounded_arena_config_sha256": sha256_file(Path(plan_dir) / "r6d_bounded_arena_config.json"),
        "execution_rows_sha256": sha256_file(Path(plan_dir) / "execution_rows.jsonl"),
        "errors_jsonl_sha256": sha256_file(errors_path) if errors_path.is_file() else None,
    }

    freeze = {
        "schema": FREEZE_SCHEMA,
        "version": "0.1",
        "status": "RAW_SCIENTIFIC_SUBJECT_EVIDENCE_FROZEN_BEFORE_DERIVATION",
        "design_hash": plan["design_hash"],
        "runtime_plan_hash": plan["plan_hash"],
        "execution_code_sha": summary["execution_code_sha"],
        "planned_branch_count": summary["planned_branch_count"],
        "preserved_trace_count": summary["preserved_trace_count"],
        "runner_error_count": summary["runner_error_count"],
        "condition_trace_counts": condition_counts,
        "direct_experiment_origin_exposure_counts": exposure_counts,
        "trace_hashes": trace_hashes,
        "files": files,
        "provider_calls_are_real": True,
        "authorization_consumed": True,
        "paid_evaluator_called": False,
        "derived_analysis_executed_before_freeze": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "same_parent_repeats_are_independent_samples": False,
        "terminal_outcome_is_primary": False,
        "interpretation_boundary": "Immutable raw subject evidence binding only. No R6 structural derivation, target-specificity conclusion or CPR adjudication is performed by this freezer.",
    }
    freeze["evidence_batch_hash"] = stable_hash(freeze)
    _require(freeze["evidence_batch_hash"] == _hash_without(freeze, "evidence_batch_hash"), "r6d_evidence_batch_hash_internal_error")

    out = Path(output_path)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r6d_raw_freeze_manifest")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(freeze, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return freeze


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan-dir", required=True)
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    freeze = freeze_raw_evidence(plan_dir=args.plan_dir, raw_dir=args.raw_dir, output_path=args.output)
    print("R6D_RAW_EVIDENCE_FREEZE=PASS")
    print("EVIDENCE_BATCH_HASH=" + freeze["evidence_batch_hash"])
    print("PRESERVED_TRACES=" + str(freeze["preserved_trace_count"]))
    print("DERIVED_ANALYSIS_BEFORE_FREEZE=NO")
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
