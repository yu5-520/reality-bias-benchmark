#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, sha256_file
from .prepare_r6d_matched_stock_plan import CONDITIONS, load_runtime_plan

FREEZE_SCHEMA = "RB-R6D-MATCHED-STOCK-RAW-EVIDENCE-FREEZE-v0.1"
EXPECTED_CONDITION_COUNTS = {c: 3 for c in CONDITIONS}
EXPECTED_EXPOSURE_COUNTS = {c: 3 for c in CONDITIONS}


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
    bundle = load_runtime_plan(plan_dir)
    raw = Path(raw_dir)
    traces_path = raw / "traces.jsonl"
    summary_path = raw / "run_summary.json"
    errors_path = raw / "errors.jsonl"
    _require(summary_path.is_file(), "matched_stock_run_summary_missing")
    summary = load_json(summary_path)
    traces = _load_optional_jsonl(traces_path)
    errors = _load_optional_jsonl(errors_path)
    plan = bundle["plan"]

    _require(summary.get("schema") == "RB-R6D-MATCHED-STOCK-RUN-SUMMARY-v0.1", "matched_stock_run_summary_schema_invalid")
    _require(summary.get("design_hash") == plan["design_hash"], "matched_stock_summary_design_hash_mismatch")
    _require(summary.get("runtime_plan_hash") == plan["plan_hash"], "matched_stock_summary_plan_hash_mismatch")
    _require(summary.get("provider_calls_are_real") is True, "matched_stock_freeze_requires_real_subject_output")
    _require(summary.get("authorization_consumed") is True, "matched_stock_freeze_requires_consumed_authorization")
    _require(summary.get("automatic_paid_evaluator_called") is False, "matched_stock_paid_evaluator_must_not_run")
    _require(summary.get("semantic_cpr_status") == "NOT_ADJUDICATED", "matched_stock_semantic_status_invalid")
    _require(summary.get("same_parent_repeats_are_independent_samples") is False, "matched_stock_independence_overclaim_forbidden")
    _require(summary.get("terminal_outcome_is_primary") is False, "matched_stock_terminal_primary_forbidden")

    planned_branch_count = int(summary.get("planned_branch_count", -1))
    preserved_trace_count = int(summary.get("preserved_trace_count", -1))
    runner_error_count = int(summary.get("runner_error_count", -1))
    _require(planned_branch_count == int(plan.get("branch_row_count", -2)) == 9, "matched_stock_planned_branch_count_invalid")
    _require(preserved_trace_count == len(traces), "matched_stock_trace_count_summary_mismatch")
    _require(runner_error_count == len(errors), "matched_stock_error_count_summary_mismatch")

    condition_counts = {c: 0 for c in CONDITIONS}
    exposure_counts = {c: 0 for c in CONDITIONS}
    observed_run_ids = set()
    trace_hashes = []
    for trace in traces:
        condition = trace.get("r6d_matched_stock_condition") or {}
        cond = condition.get("condition_id")
        _require(cond in condition_counts, "matched_stock_trace_condition_invalid")
        run_id = trace.get("run_id")
        _require(isinstance(run_id, str) and run_id and run_id not in observed_run_ids, "matched_stock_trace_run_id_invalid")
        observed_run_ids.add(run_id)
        condition_counts[cond] += 1
        exposure = (trace.get("r6d_exposure_integrity") or {}).get("direct_experiment_origin_exposure_count")
        _require(exposure == 1, "matched_stock_trace_must_have_one_exposure")
        exposure_counts[cond] += 1
        _require(condition.get("semantic_cpr_status") == "NOT_ADJUDICATED", "matched_stock_trace_semantic_status_invalid")
        _require(condition.get("provider_internal_state_replayed") is False, "matched_stock_hidden_state_replay_forbidden")
        trace_hashes.append(stable_hash(trace))

    error_run_ids = set()
    for error in errors:
        run_id = error.get("run_id")
        _require(isinstance(run_id, str) and run_id and run_id not in error_run_ids and run_id not in observed_run_ids, "matched_stock_error_run_id_invalid")
        error_run_ids.add(run_id)
        _require(error.get("condition_id") in CONDITIONS, "matched_stock_error_condition_invalid")

    planned_rows = {row["run_id"]: row for row in bundle["execution_rows"]}
    _require(observed_run_ids.issubset(planned_rows), "matched_stock_unplanned_trace_run_id")
    _require(error_run_ids.issubset(planned_rows), "matched_stock_unplanned_error_run_id")
    missing_run_ids = sorted(set(planned_rows) - observed_run_ids - error_run_ids)
    batch_complete = (
        preserved_trace_count == 9
        and runner_error_count == 0
        and not missing_run_ids
        and condition_counts == EXPECTED_CONDITION_COUNTS
        and exposure_counts == EXPECTED_EXPOSURE_COUNTS
    )

    files = {
        "traces_jsonl_sha256": sha256_file(traces_path) if traces_path.is_file() else None,
        "run_summary_sha256": sha256_file(summary_path),
        "errors_jsonl_sha256": sha256_file(errors_path) if errors_path.is_file() else None,
        "runtime_plan_json_sha256": sha256_file(Path(plan_dir) / "r6d_matched_stock_plan.json"),
        "source_parent_snapshot_sha256": sha256_file(Path(plan_dir) / "source_parent_snapshot.json"),
        "s2_envelope_sha256": sha256_file(Path(plan_dir) / "s2_envelope.json"),
        "s3_envelope_sha256": sha256_file(Path(plan_dir) / "s3_envelope.json"),
        "s4_envelope_sha256": sha256_file(Path(plan_dir) / "s4_envelope.json"),
        "bounded_arena_config_sha256": sha256_file(Path(plan_dir) / "r6d_matched_stock_bounded_arena_config.json"),
        "execution_rows_sha256": sha256_file(Path(plan_dir) / "execution_rows.jsonl"),
    }
    freeze = {
        "schema": FREEZE_SCHEMA,
        "version": "0.1",
        "status": "RAW_SCIENTIFIC_SUBJECT_EVIDENCE_FROZEN_BEFORE_DERIVATION" if batch_complete else "RAW_SCIENTIFIC_SUBJECT_EVIDENCE_FROZEN_INCOMPLETE_BEFORE_DERIVATION",
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
        "interpretation_boundary": "Immutable raw matched-stock subject evidence binding only. Incomplete branches and failures are preserved as observed. No R6 derivation, specificity conclusion, CPR adjudication, or automatic retry/replacement is performed here."
    }
    freeze["evidence_batch_hash"] = stable_hash(freeze)
    _require(freeze["evidence_batch_hash"] == _hash_without(freeze, "evidence_batch_hash"), "matched_stock_evidence_batch_hash_internal_error")
    out = Path(output_path)
    if out.exists():
        raise ValueError("refusing_to_overwrite_matched_stock_raw_freeze_manifest")
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
    print("R6D_MATCHED_STOCK_RAW_EVIDENCE_FREEZE=PASS")
    print("STATUS=" + freeze["status"])
    print("BATCH_COMPLETE=" + ("YES" if freeze["batch_complete"] else "NO"))
    print("EVIDENCE_BATCH_HASH=" + freeze["evidence_batch_hash"])
    print("AUTOMATIC_RETRY_AUTHORIZED=NO")
    print("DERIVED_ANALYSIS_BEFORE_FREEZE=NO")
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
