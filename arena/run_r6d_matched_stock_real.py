#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from pathlib import Path

from .core import stable_hash
from .cost_budget import BudgetedProvider
from .engine import run_arena_once
from .io_utils import load_json, load_jsonl
from .journal import Journal
from .prepare_r6d_matched_stock_plan import load_runtime_plan
from .providers import provider_from_config
from .r6d_matched_stock_atomic import CONDITIONS, MatchedStockAtomicEpistemicAnnotationTransform
from .run_r6d_specificity_real import (
    _append_jsonl,
    _credential_check,
    _safe_file_id,
    _write_json,
    validate_execution_bindings,
    validate_symmetric_limits,
    verify_trace_exposure_invariants,
)

AUTH_PHRASE = "CALL_REAL_R6D_MATCHED_STOCK_API"
RUN_SUMMARY_SCHEMA = "RB-R6D-MATCHED-STOCK-RUN-SUMMARY-v0.1"


def _transform_for(row: dict, bundle: dict):
    condition = row["condition_id"]
    if condition not in CONDITIONS:
        raise ValueError("unknown_matched_stock_condition")
    return MatchedStockAtomicEpistemicAnnotationTransform(bundle["condition_envelopes"][condition])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan-dir", required=True)
    ap.add_argument("--outdir")
    ap.add_argument("--model-config", required=True)
    ap.add_argument("--provider", required=True)
    ap.add_argument("--execution-code-sha", required=True)
    ap.add_argument("--per-branch-max-calls", type=int, required=True)
    ap.add_argument("--per-branch-spending-ceiling", type=float, required=True)
    ap.add_argument("--global-spending-ceiling", type=float, required=True)
    ap.add_argument("--currency", default="USD")
    ap.add_argument("--authorization-phrase")
    ap.add_argument("--execute-real-api", action="store_true")
    ap.add_argument("--preflight-only", action="store_true")
    args = ap.parse_args()

    if args.preflight_only and args.execute_real_api:
        raise SystemExit("preflight_only_and_execute_real_api_are_mutually_exclusive")

    bundle = load_runtime_plan(args.plan_dir)
    row_count = len(bundle["execution_rows"])
    validate_symmetric_limits(
        row_count=row_count,
        per_branch_max_calls=args.per_branch_max_calls,
        per_branch_spending_ceiling=args.per_branch_spending_ceiling,
        global_spending_ceiling=args.global_spending_ceiling,
    )
    bindings = validate_execution_bindings(
        bundle=bundle,
        model_config_path=args.model_config,
        provider_name=args.provider,
        execution_code_sha=args.execution_code_sha,
    )

    budget = bundle["plan"]["budget_gate"]
    if args.per_branch_max_calls != int(budget["per_branch_max_calls"]):
        raise ValueError("runtime_call_cap_must_equal_frozen_design")
    if abs(args.per_branch_spending_ceiling - float(budget["per_branch_spending_ceiling"])) > 1e-12:
        raise ValueError("runtime_per_branch_ceiling_must_equal_frozen_design")
    if abs(args.global_spending_ceiling - float(budget["global_spending_ceiling"])) > 1e-12:
        raise ValueError("runtime_global_ceiling_must_equal_frozen_design")

    if args.preflight_only:
        print("R6D_MATCHED_STOCK_FORMAL_RUNNER_PREFLIGHT=PASS")
        print("DESIGN_HASH=" + bundle["plan"]["design_hash"])
        print("RUNTIME_PLAN_HASH=" + bundle["plan"]["plan_hash"])
        print("EXECUTION_CODE_SHA=" + args.execution_code_sha)
        print("PLANNED_BRANCHES=" + str(row_count))
        print("PAID_API_CALLED=NO")
        return

    if not args.execute_real_api or args.authorization_phrase != AUTH_PHRASE:
        raise SystemExit("Refusing provider calls: exact R6-D matched-stock authorization required.")
    if not args.outdir:
        raise SystemExit("outdir_required_for_real_matched_stock_execution")

    model_config = bindings["model_config"]
    _credential_check(model_config)
    upstream = provider_from_config(model_config)
    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_matched_stock_output_dir")
    out.mkdir(parents=True)
    traces_path = out / "traces.jsonl"
    errors_path = out / "errors.jsonl"
    journals = out / "journals"

    total_estimated_spend = 0.0
    errors = []
    parent_material_hash = stable_hash(bundle["source_parent_snapshot"])
    condition_trace_counts = {c: 0 for c in CONDITIONS}
    condition_exposure_counts = {c: 0 for c in CONDITIONS}
    rows = sorted(bundle["execution_rows"], key=lambda x: (x["replicate_index"], x["execution_order"]))

    for row in rows:
        provider = BudgetedProvider(
            upstream,
            model_config,
            spending_ceiling=args.per_branch_spending_ceiling,
            currency=args.currency,
            max_calls=args.per_branch_max_calls,
        )
        transform = _transform_for(row, bundle)
        try:
            journal_path = journals / (_safe_file_id(row["run_id"]) + ".jsonl")
            execution_binding = {
                "schema": "RB-R6D-MATCHED-STOCK-EXECUTION-BINDING-v0.1",
                "run_id": row["run_id"],
                "triad_id": row["triad_id"],
                "replicate_index": row["replicate_index"],
                "execution_order": row["execution_order"],
                "condition_id": row["condition_id"],
                "manifest_hash": row["manifest_hash"],
                "design_hash": bundle["plan"]["design_hash"],
                "runtime_plan_hash": bundle["plan"]["plan_hash"],
                "parent_state_hash": bundle["source_parent_snapshot"]["state_hash"],
                "envelope_hash": row["envelope_hash"],
                "execution_code_sha": args.execution_code_sha,
                "bound_before_first_provider_call": True,
                "provider_internal_state_replayed": False,
            }
            execution_binding["binding_hash"] = stable_hash(execution_binding)
            with Journal(journal_path) as journal:
                journal({"record_type": "r6d_matched_stock_execution_binding", "record": execution_binding})
                trace = run_arena_once(
                    load_json(bindings["domain_path"]),
                    copy.deepcopy(bundle["bounded_arena_config"]),
                    provider,
                    row["run_id"],
                    row["logical_seed"],
                    recorder=journal,
                    initial_state_snapshot=bundle["source_parent_snapshot"],
                    runtime_view_transform=transform,
                )

            if stable_hash(bundle["source_parent_snapshot"]) != parent_material_hash:
                raise ValueError("frozen_parent_snapshot_mutated_by_matched_stock_execution")
            exposure = verify_trace_exposure_invariants(
                trace=trace,
                row=row,
                transform=transform,
                parent_snapshot=bundle["source_parent_snapshot"],
            )
            condition_trace_counts[row["condition_id"]] += 1
            condition_exposure_counts[row["condition_id"]] += exposure["direct_experiment_origin_exposure_count"]
            trace["r6d_matched_stock_execution_binding"] = execution_binding
            trace["r6d_exposure_integrity"] = exposure
            trace["r6d_matched_stock_condition"] = {
                "schema": "RB-R6D-MATCHED-STOCK-CONDITION-TRACE-v0.1",
                "triad_id": row["triad_id"],
                "replicate_index": row["replicate_index"],
                "execution_order": row["execution_order"],
                "condition_id": row["condition_id"],
                "design_hash": bundle["plan"]["design_hash"],
                "runtime_plan_hash": bundle["plan"]["plan_hash"],
                "manifest_hash": row["manifest_hash"],
                "direct_response_turn": bundle["plan"]["observation_horizon"]["direct_response_turn"],
                "post_consumption_start_turn": bundle["plan"]["observation_horizon"]["post_consumption_start_turn"],
                "natural_early_termination_interpretation": "RIGHT_CENSORING",
                "provider_internal_state_replayed": False,
                "semantic_cpr_status": "NOT_ADJUDICATED",
            }
            trace["code_commit_sha"] = args.execution_code_sha
            trace["model_config_hash"] = bundle["plan"]["environment_binding"]["model_config_hash"]
            trace["review_status"] = "PENDING_REVIEW"
            _append_jsonl(traces_path, trace)
            total_estimated_spend += float(provider.estimated_spend)
        except Exception as err:
            error = {
                "run_id": row["run_id"],
                "triad_id": row["triad_id"],
                "condition_id": row["condition_id"],
                "manifest_hash": row["manifest_hash"],
                "error": repr(err),
            }
            errors.append(error)
            _append_jsonl(errors_path, error)

    if total_estimated_spend > args.global_spending_ceiling + 1e-12:
        raise ValueError("observed_estimated_spend_exceeds_matched_stock_global_ceiling")

    preserved_trace_count = len(load_jsonl(traces_path)) if traces_path.exists() else 0
    summary = {
        "schema": RUN_SUMMARY_SCHEMA,
        "design_hash": bundle["plan"]["design_hash"],
        "runtime_plan_hash": bundle["plan"]["plan_hash"],
        "execution_code_sha": args.execution_code_sha,
        "planned_branch_count": row_count,
        "preserved_trace_count": preserved_trace_count,
        "runner_error_count": len(errors),
        "condition_trace_counts": condition_trace_counts,
        "direct_experiment_origin_exposure_counts": condition_exposure_counts,
        "estimated_total_spend": total_estimated_spend,
        "currency": args.currency.upper(),
        "per_branch_max_calls": args.per_branch_max_calls,
        "per_branch_spending_ceiling": args.per_branch_spending_ceiling,
        "global_spending_ceiling": args.global_spending_ceiling,
        "provider_calls_are_real": True,
        "authorization_consumed": True,
        "automatic_paid_evaluator_called": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "same_parent_repeats_are_independent_samples": False,
        "terminal_outcome_is_primary": False,
        "automatic_retry_or_replacement_authorized": False,
    }
    summary["summary_hash"] = stable_hash(summary)
    _write_json(out / "run_summary.json", summary)
    print("R6D_MATCHED_STOCK_REAL_RUN_COMPLETE=YES")
    print("PRESERVED_TRACES=" + str(preserved_trace_count))
    print("RUNNER_ERRORS=" + str(len(errors)))
    print("PAID_EVALUATOR_CALLED=NO")
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
