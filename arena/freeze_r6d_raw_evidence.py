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

FREEZE_SCHEMA = "RB-R6D-SPECIFICITY-RAW-EVIDENCE-FREEZE-v0.2"
EXPECTED_CONDITION_COUNTS = {S0: 3, S1: 3, S2: 3}
EXPECTED_EXPOSURE_COUNTS = {S0: 0, S1: 3, S2: 3}


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _hash_without(row: dict, key: str) -> str:
    material = copy.deepcopy(row)
    material.pop(key, None)
    return stable_hash(material)


def _load_optional_jsonl(path: Path) -> list[dict]:
    return load_jsonl(path) if path.is_file() else []


def freeze_raw_evidence(*, plan_dir: str | Path, raw_dir: str | Path, output_path: str | Path) -> dict:
    """Freeze every preserved subject trace/error before any derived analysis.

    A partially completed real batch is still scientific raw evidence. This
    function therefore freezes incomplete batches instead of rejecting them.
    Completion and censoring/failure status are recorded explicitly so later
    analysis cannot silently convert missing branches into zero effects or
    trigger automatic replacement runs.
    """
    bundle = load_r6d_runtime_plan(plan_dir)
    raw = Path(raw_dir)
    traces_path = raw / "traces.jsonl"
    summary_path = raw / "run_summary.json"
    errors_path = raw / "errors.jsonl"

    _require(summary_path.is_file(), "r6d_run_summary_missing")
    summary = load_json(summary_path)
    traces = _load_optional_jsonl(traces_path)
    errors = _load_optional_jsonl(errors_path)
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

    planned_branch_count = int(summary.get("planned_branch_count", -1))
    preserved_trace_count = int(summary.get("preserved_trace_count", -1))
    runner_error_count = int(summary.get("runner_error_count", -1))
    _require(planned_branch_count == int(plan.get("branch_row_count", -2)) == 9, "r6d_planned_branch_count_invalid")
    _require(preserved_trace_count == len(traces), "r6d_trace_count_summary_mismatch")
    _require(runner_error_count == len(errors), "r6d_error_count_summary_mismatch")
    _require(0 <= preserved_trace_count <= planned_branch_count, "r6d_preserved_trace_count_out_of_range")
    _require(0 <= runner_error_count <= planned_branch_count, "r6d_runner_error_count_out_of_range")
    _require(preserved_trace_count + runner_error_count <= planned_branch_count, "r6d_trace_error_count_exceeds_plan")

    condition_counts = {S0: 0, S1: 0, S2: 0}
    exposure_counts = {S0: 0, S1: 0, S2: 0}
    observed_run_ids: set[str] = set()
    trace_hashes: list[str] = []

    for trace in traces:
        condition = trace.get("r6d_condition") or {}
        cond = condition.get("condition_id")
        _require(cond in condition_counts, "r6d_trace_condition_invalid")
        run_id = trace.get("run_id")
        _require(isinstance(run_id, str) and run_id, "r6d_trace_run_id_missing")
        _require(run_id not in observed_run_ids, "r6d_duplicate_trace_run_id")
        observed_run_ids.add(run_id)
        condition_counts[cond] += 1
        _require(condition_counts[cond] <= EXPECTED_CONDITION_COUNTS[cond], "r6d_condition_count_exceeds_plan")

        exposure = (trace.get("r6d_exposure_integrity") or {}).get("direct_experiment_origin_exposure_count")
        _require(exposure in (0, 1), "r6d_trace_exposure_count_invalid")
        if cond == S0:
            _require(exposure == 0, "r6d_s0_exposure_forbidden")
        else:
            _require(exposure == 1, "r6d_treated_trace_must_have_one_exposure")
        exposure_counts[cond] += int(exposure)
        _require(exposure_counts[cond] <= EXPECTED_EXPOSURE_COUNTS[cond], "r6d_exposure_count_exceeds_plan")

        _require(condition.get("semantic_cpr_status") == "NOT_ADJUDICATED", "r6d_trace_semantic_status_invalid")
        _require(condition.get("provider_internal_state_replayed") is False, "r6d_trace_hidden_state_replay_forbidden")
        trace_hashes.append(stable_hash(trace))

    error_run_ids: set[str] = set()
    for error in errors:
        run_id = error.get("run_id")
        _require(isinstance(run_id, str) and run_id, "r6d_error_run_id_missing")
        _require(run_id not in error_run_ids, "r6d_duplicate_error_run_id")
        _require(run_id not in observed_run_ids, "r6d_run_cannot_be_both_preserved_trace_and_error")
        error_run_ids.add(run_id)
        _require(error.get("condition_id") in EXPECTED_CONDITION_COUNTS, "r6d_error_condition_invalid")

    planned_rows = {row["run_id"]: row for row in bundle["execution_rows"]}
    _require(set(observed_run_ids).issubset(planned_rows), "r6d_unplanned_trace_run_id")
    _require(set(error_run_ids).issubset(planned_rows), "r6d_unplanned_error_run_id")
    missing_run_ids = sorted(set(planned_rows) - observed_run_ids - error_run_ids)

    batch_complete = (
        preserved_trace_count == planned_branch_count
        and runner_error_count == 0
        and not missing_run_ids
        and condition_counts == EXPECTED_CONDITION_COUNTS
        and exposure_counts == EXPECTED_EXPOSURE_COUNTS
    )

    files = {
        "traces_jsonl_sha256": sha256_file(traces_path) if traces_path.is_file() else None,
        "run_summary_sha256": sha256_file(summary_path),
        "errors_jsonl_sha256": sha256_file(errors_path) if errors_path.is_file() else None,
        "runtime_plan_json_sha256": sha256_file(Path(plan_dir) / "r6d_plan.json"),
        "source_parent_snapshot_sha256": sha256_file(Path(plan_dir) / "source_parent_snapshot.json"),
        "s1_envelope_sha256": sha256_file(Path(plan_dir) / "s1_envelope.json"),
        "s2_envelope_sha256": sha256_file(Path(plan_dir) / "s2_envelope.json"),
        "bounded_arena_config_sha256": sha256_file(Path(plan_dir) / "r6d_bounded_arena_config.json"),
        "execution_rows_sha256": sha256_file(Path(plan_dir) / "execution_rows.jsonl"),
    }

    freeze = {
        "schema": FREEZE_SCHEMA,
        "version": "0.2",
        "status": (
            "RAW_SCIENTIFIC_SUBJECT_EVIDENCE_FROZEN_BEFORE_DERIVATION"
            if batch_complete
            else "RAW_SCIENTIFIC_SUBJECT_EVIDENCE_FROZEN_INCOMPLETE_BEFORE_DERIVATION"
        ),
        "batch_complete": batch_complete,
        "design_hash": plan["design_hash"],
        "runtime_plan_hash": plan["plan_hash"],
        "execution_code_sha": summary["execution_code_sha"],
        "planned_branch_count": planned_branch_count,
        "preserved_trace_count": preserved_trace_count,
        "runner_error_count": runner_error_count,
        "missing_run_ids": missing_run_ids,
        "error_run_ids": sorted(error_run_ids),
        "condition_trace_counts": condition_counts,
        "expected_condition_trace_counts": EXPECTED_CONDITION_COUNTS,
        "direct_experiment_origin_exposure_counts": exposure_counts,
        "expected_direct_experiment_origin_exposure_counts": EXPECTED_EXPOSURE_COUNTS,
        "trace_hashes": trace_hashes,
        "error_hashes": [stable_hash(x) for x in errors],
        "files": files,
        "provider_calls_are_real": True,
        "authorization_consumed": True,
        "paid_evaluator_called": False,
        "derived_analysis_executed_before_freeze": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "same_parent_repeats_are_independent_samples": False,
        "terminal_outcome_is_primary": False,
        "automatic_replacement_or_retry_authorized": False,
        "interpretation_boundary": (
            "Immutable raw subject evidence binding only. Incomplete branches and failures are preserved as observed. "
            "This freezer performs no R6 structural derivation, target-specificity conclusion, CPR adjudication, or automatic retry/replacement."
        ),
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
    print("STATUS=" + freeze["status"])
    print("BATCH_COMPLETE=" + ("YES" if freeze["batch_complete"] else "NO"))
    print("EVIDENCE_BATCH_HASH=" + freeze["evidence_batch_hash"])
    print("PRESERVED_TRACES=" + str(freeze["preserved_trace_count"]))
    print("RUNNER_ERRORS=" + str(freeze["runner_error_count"]))
    print("AUTOMATIC_RETRY_AUTHORIZED=NO")
    print("DERIVED_ANALYSIS_BEFORE_FREEZE=NO")
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
