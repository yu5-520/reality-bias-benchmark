#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path

from .core import stable_hash
from .cost_budget import BudgetedProvider
from .engine import run_arena_once
from .io_utils import load_json, load_jsonl, sha256_file
from .prepare_r6d_specificity_plan import load_r6d_runtime_plan
from .providers import provider_from_config
from .r5r6_specificity_atomic_v0_2 import S0, S1, S2, AtomicEpistemicAnnotationTransform

AUTH_PHRASE = "CALL_REAL_R6D_SPECIFICITY_API"
RUN_SUMMARY_SCHEMA = "RB-R6D-SPECIFICITY-RUN-SUMMARY-v0.1"


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _write_json(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _credential_check(model_config: dict) -> None:
    provider = model_config.get("provider")
    if provider == "deepseek":
        if not os.environ.get("DEEPSEEK_API_KEY"):
            raise SystemExit("DEEPSEEK_API_KEY is not set")
        return
    if provider == "alibaba_cloud_bailian_business_space":
        if not os.environ.get(model_config.get("credential_env", "BAI")):
            raise SystemExit("Bailian credential is not set")
        return
    raise SystemExit("unsupported provider: " + str(provider))


def _safe_file_id(run_id: str) -> str:
    return stable_hash({"run_id": run_id})[:20]


def validate_symmetric_limits(*, row_count: int, per_branch_max_calls: int, per_branch_spending_ceiling: float, global_spending_ceiling: float) -> bool:
    if not isinstance(row_count, int) or row_count <= 0:
        raise ValueError("positive_branch_row_count_required")
    if per_branch_max_calls <= 0 or per_branch_spending_ceiling <= 0 or global_spending_ceiling <= 0:
        raise ValueError("positive_r6d_limits_required")
    if global_spending_ceiling + 1e-12 < per_branch_spending_ceiling * row_count:
        raise ValueError("global_ceiling_must_cover_all_symmetric_per_branch_ceilings")
    return True


def validate_execution_bindings(*, bundle: dict, model_config_path: str, provider_name: str, execution_code_sha: str) -> dict:
    plan = bundle["plan"]
    design_env = plan["environment_binding"]
    if plan.get("plan_code_sha") != execution_code_sha:
        raise ValueError("execution_code_sha_mismatch_runtime_plan")
    if plan.get("real_subject_execution_authorized") is not False:
        raise ValueError("runtime_plan_must_not_self_authorize")
    if plan.get("paid_subject_authorization_status") != "NOT_AUTHORIZED":
        raise ValueError("runtime_paid_gate_must_remain_external")
    if plan.get("semantic_cpr_status") != "NOT_ADJUDICATED":
        raise ValueError("unexpected_semantic_cpr_plan_state")
    if plan.get("same_parent_repeats_are_independent_samples") is not False:
        raise ValueError("same_parent_repeats_independence_overclaim")

    model_config = load_json(model_config_path)
    if model_config.get("provider") != provider_name:
        raise ValueError("provider_model_config_mismatch")
    if sha256_file(model_config_path) != design_env["model_config_hash"]:
        raise ValueError("model_config_hash_mismatch_design")
    arena_path = design_env["arena_config_path"]
    if sha256_file(arena_path) != design_env["arena_config_hash"]:
        raise ValueError("arena_config_hash_mismatch_design")
    domain_path = Path("arena/domains") / f"{design_env['domain_id']}.json"
    if not domain_path.exists() or sha256_file(domain_path) != design_env["domain_hash"]:
        raise ValueError("domain_hash_mismatch_design")
    domain = load_json(domain_path)
    if stable_hash(domain["task"]) != design_env["task_hash"]:
        raise ValueError("task_hash_mismatch_design")
    if stable_hash(domain["agents"]) != design_env["agent_registry_hash"]:
        raise ValueError("agent_registry_hash_mismatch_design")
    if bundle["source_parent_snapshot"]["state_hash"] != plan["source_binding"]["common_parent_state_hash"]:
        raise ValueError("runtime_parent_hash_mismatch_plan")
    return {"model_config": model_config, "domain_path": str(domain_path), "arena_path": arena_path}


def _transform_for(row: dict, bundle: dict):
    condition = row["condition_id"]
    if condition == S0:
        return None
    if condition == S1:
        return AtomicEpistemicAnnotationTransform(bundle["s1_envelope"])
    if condition == S2:
        return AtomicEpistemicAnnotationTransform(bundle["s2_envelope"])
    raise ValueError("unknown_r6d_condition")


def verify_trace_exposure_invariants(*, trace: dict, row: dict, transform, parent_snapshot: dict) -> dict:
    records = list(trace.get("runtime_transform_records") or [])
    condition = row["condition_id"]
    expected_turn = int(parent_snapshot["turns"]) + 1
    expected_actor = list(parent_snapshot.get("queue") or [None])[0]
    if condition == S0:
        if records:
            raise ValueError("s0_must_have_zero_experiment_origin_exposures")
        return {
            "direct_experiment_origin_exposure_count": 0,
            "experiment_origin_reinjection_count": 0,
            "persistent_state_mutation": False,
            "delivery_actor": None,
            "delivery_turn": None,
            "delivery_hash": None,
        }
    transform.verify_finished()
    summary = transform.summary()
    if len(records) != 1 or summary["direct_experiment_origin_exposure_count"] != 1:
        raise ValueError("treated_condition_must_have_exactly_one_exposure")
    if summary["experiment_origin_reinjection_count"] != 0:
        raise ValueError("treated_condition_reinjection_forbidden")
    if summary["persistent_state_mutation"] is not False:
        raise ValueError("treated_condition_persistent_mutation_forbidden")
    record = records[0]
    if record.get("turn") != expected_turn or record.get("actor") != expected_actor:
        raise ValueError("treated_delivery_boundary_invalid")
    if record.get("condition_id") != condition:
        raise ValueError("treated_delivery_condition_mismatch")
    return {
        "direct_experiment_origin_exposure_count": 1,
        "experiment_origin_reinjection_count": 0,
        "persistent_state_mutation": False,
        "delivery_actor": record.get("actor"),
        "delivery_turn": record.get("turn"),
        "delivery_hash": record.get("delivery_hash"),
        "target_locator": record.get("target_locator"),
    }


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

    bundle = load_r6d_runtime_plan(args.plan_dir)
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
        print("R6D_FORMAL_RUNNER_PREFLIGHT=PASS")
        print("DESIGN_HASH=" + bundle["plan"]["design_hash"])
        print("RUNTIME_PLAN_HASH=" + bundle["plan"]["plan_hash"])
        print("EXECUTION_CODE_SHA=" + args.execution_code_sha)
        print("PLANNED_BRANCHES=" + str(row_count))
        print("PAID_API_CALLED=NO")
        return

    if not args.execute_real_api or args.authorization_phrase != AUTH_PHRASE:
        raise SystemExit("Refusing provider calls: exact R6-D specificity authorization required.")
    if not args.outdir:
        raise SystemExit("outdir_required_for_real_r6d_execution")

    model_config = bindings["model_config"]
    _credential_check(model_config)
    upstream = provider_from_config(model_config)

    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r6d_output_dir")
    out.mkdir(parents=True)
    traces_path = out / "traces.jsonl"
    errors_path = out / "errors.jsonl"
    journals = out / "journals"

    total_estimated_spend = 0.0
    errors: list[dict] = []
    parent_material_hash = stable_hash(bundle["source_parent_snapshot"])
    condition_trace_counts = {S0: 0, S1: 0, S2: 0}
    condition_exposure_counts = {S0: 0, S1: 0, S2: 0}
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
            from .journal import Journal

            journal_path = journals / (_safe_file_id(row["run_id"]) + ".jsonl")
            execution_binding = {
                "schema": "RB-R6D-SPECIFICITY-EXECUTION-BINDING-v0.1",
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
                journal({"record_type": "r6d_execution_binding", "record": execution_binding})
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
                raise ValueError("frozen_parent_snapshot_mutated_by_r6d_branch_execution")
            exposure = verify_trace_exposure_invariants(
                trace=trace,
                row=row,
                transform=transform,
                parent_snapshot=bundle["source_parent_snapshot"],
            )
            condition_trace_counts[row["condition_id"]] += 1
            condition_exposure_counts[row["condition_id"]] += exposure["direct_experiment_origin_exposure_count"]

            trace["r6d_execution_binding"] = execution_binding
            trace["r6d_exposure_integrity"] = exposure
            trace["r6d_condition"] = {
                "schema": "RB-R6D-SPECIFICITY-CONDITION-TRACE-v0.1",
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
        raise ValueError("observed_estimated_spend_exceeds_r6d_global_ceiling")

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
    }
    summary["summary_hash"] = stable_hash(summary)
    _write_json(out / "run_summary.json", summary)

    if errors:
        raise SystemExit(f"R6-D execution completed with {len(errors)} branch errors; raw evidence preserved in {out}")
    if preserved_trace_count != row_count:
        raise SystemExit("R6-D execution trace count mismatch; raw evidence preserved")
    print("R6D_REAL_SUBJECT_EXECUTION=COMPLETE")
    print("DESIGN_HASH=" + summary["design_hash"])
    print("RUNTIME_PLAN_HASH=" + summary["runtime_plan_hash"])
    print("PRESERVED_TRACES=" + str(preserved_trace_count))
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")
    print("PAID_EVALUATOR_CALLED=NO")


if __name__ == "__main__":
    main()
