#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from .branch_plan_one_shot import verify_one_shot_branch_plan
from .core import stable_hash
from .cost_budget import BudgetedProvider
from .engine import run_arena_once
from .io_utils import load_json, load_jsonl
from .one_shot_intervention import INTERVENTION_CONDITION, OneShotRuntimeViewTransform, verify_branch_manifest_v3
from .providers import provider_from_config

AUTH_PHRASE = "CALL_REAL_R5MID_ONESHOT_BRANCH_API"


def _append_jsonl(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _write_json(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def _credential_check(model_config):
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


def _safe_file_id(run_id):
    return stable_hash({"run_id": run_id})[:20]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan-dir", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--model-config", required=True)
    ap.add_argument("--provider", required=True)
    ap.add_argument("--per-branch-max-calls", type=int, required=True)
    ap.add_argument("--per-branch-spending-ceiling", type=float, required=True)
    ap.add_argument("--global-spending-ceiling", type=float, required=True)
    ap.add_argument("--currency", default="USD")
    ap.add_argument("--authorization-phrase", required=True)
    ap.add_argument("--execute-real-api", action="store_true")
    args = ap.parse_args()
    if not args.execute_real_api or args.authorization_phrase != AUTH_PHRASE:
        raise SystemExit("Refusing provider calls: new one-shot explicit authorization required.")
    bundle = load_plan_bundle(args.plan_dir)
    row_count = len(bundle["branch_rows"])
    if args.per_branch_max_calls <= 0 or args.per_branch_spending_ceiling <= 0:
        raise SystemExit("positive per-branch limits required")
    if args.global_spending_ceiling < args.per_branch_spending_ceiling * row_count:
        raise SystemExit("global ceiling must cover all symmetric per-branch ceilings")
    model_config = load_json(args.model_config)
    if model_config.get("provider") != args.provider:
        raise ValueError("provider_model_config_mismatch")
    _credential_check(model_config)
    upstream = provider_from_config(model_config)
    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_one_shot_output_dir")
    out.mkdir(parents=True)
    traces_path = out / "traces.jsonl"
    errors_path = out / "errors.jsonl"
    journals = out / "journals"
    manifest_by_hash = {x["branch_hash"]: x for x in bundle["branch_manifests"]}
    total_estimated_spend = 0.0
    errors = []
    for row in bundle["branch_rows"]:
        manifest = manifest_by_hash[row["branch_hash"]]
        bound_envelope = bundle["one_shot_envelope"] if row["condition_id"] == INTERVENTION_CONDITION else None
        verify_branch_manifest_v3(manifest, parent_snapshot=bundle["parent_snapshot"], envelope=bound_envelope)
        provider = BudgetedProvider(
            upstream,
            model_config,
            spending_ceiling=args.per_branch_spending_ceiling,
            currency=args.currency,
            max_calls=args.per_branch_max_calls,
        )
        transform = OneShotRuntimeViewTransform(bound_envelope) if bound_envelope is not None else None
        try:
            from .journal import Journal
            journal_path = journals / (_safe_file_id(row["run_id"]) + ".jsonl")
            with Journal(journal_path) as journal:
                trace = run_arena_once(
                    load_json(Path("arena/domains") / (bundle["plan"]["config_identity"]["domain_id"] + ".json")),
                    load_json(bundle["plan"]["config_identity"]["arena_config_path"]),
                    provider,
                    row["run_id"],
                    row.get("logical_seed"),
                    recorder=journal,
                    initial_state_snapshot=bundle["parent_snapshot"],
                    runtime_view_transform=transform,
                )
            transform_summary = transform.summary() if transform else {
                "envelope_hash": None,
                "direct_experiment_origin_exposure_count": 0,
                "consumed": False,
                "experiment_origin_reinjection_count": 0,
                "persistent_state_mutation": False,
                "delivery_record_hashes": [],
            }
            if transform:
                transform.verify_finished()
            trace["experimental_branch"] = manifest
            trace["one_shot_intervention_summary"] = transform_summary
            trace["pair_id"] = row["pair_id"]
            trace["replicate_index"] = row["replicate_index"]
            trace["condition_id"] = row["condition_id"]
            trace["pair_order_pattern"] = row["pair_order_pattern"]
            trace["branch_plan_hash"] = bundle["plan"]["plan_hash"]
            trace["code_commit_sha"] = bundle["plan"]["code_identity"]["branch_execution_commit"]
            trace["model_config_hash"] = bundle["plan"]["model_identity"]["model_config_hash"]
            trace["review_status"] = "PENDING_REVIEW"
            _append_jsonl(traces_path, trace)
            total_estimated_spend += float(provider.estimated_spend)
        except Exception as err:
            error = {"run_id": row["run_id"], "pair_id": row["pair_id"], "condition_id": row["condition_id"], "error": repr(err)}
            errors.append(error)
            _append_jsonl(errors_path, error)
    summary = {
        "schema": "RB-R5MID-ONE-SHOT-RUN-SUMMARY-v0.1",
        "plan_hash": bundle["plan"]["plan_hash"],
        "planned_branch_count": row_count,
        "runner_error_count": len(errors),
        "estimated_total_spend": total_estimated_spend,
        "currency": args.currency.upper(),
        "per_branch_max_calls": args.per_branch_max_calls,
        "per_branch_spending_ceiling": args.per_branch_spending_ceiling,
        "global_spending_ceiling": args.global_spending_ceiling,
        "automatic_paid_evaluator_called": False,
        "old_phase_b_authorization_reused": False,
    }
    _write_json(out / "summary.json", summary)
    if errors:
        raise SystemExit("one-shot branch collection contains runner errors; preserved available evidence")
    print("ONE_SHOT_BRANCH_COLLECTION_COMPLETE")
    print("PAID_EVALUATOR_CALLED=NO")


if __name__ == "__main__":
    main()
