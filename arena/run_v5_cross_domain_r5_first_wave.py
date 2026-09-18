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
from .experimental_control import verify_state_snapshot
from .io_utils import load_json, load_jsonl, sha256_file
from .journal import Journal
from .one_shot_intervention import (
    CONTROL_CONDITION,
    INTERVENTION_CONDITION,
    OneShotRuntimeViewTransform,
    verify_branch_manifest_v3,
    verify_one_shot_envelope,
)
from .providers import provider_from_config

ROOT = Path(__file__).resolve().parents[1]
AUTH_PHRASE = "CALL_REAL_V5_CROSS_DOMAIN_R5_FIRST_WAVE_API"


def _append_jsonl(path: Path, row: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _write_json(path: Path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_bundle(plan_dir: str):
    p = Path(plan_dir)
    plan = load_json(p / "plan.json")
    cases = load_jsonl(p / "case_bindings.jsonl")
    rows = load_jsonl(p / "branch_execution_manifest.jsonl")
    manifests = load_jsonl(p / "branch_manifests.jsonl")
    if plan.get("schema") != "RB-V5-CROSS-DOMAIN-R5-FIRST-WAVE-EXECUTION-PLAN-v0.1":
        raise ValueError("r5_execution_plan_schema_invalid")
    if plan.get("authorization_status") != "NOT_AUTHORIZED":
        raise ValueError("r5_prepared_plan_must_not_self_authorize")
    if plan.get("case_count") != 6 or plan.get("branch_count") != 24:
        raise ValueError("r5_prepared_geometry_invalid")
    if len(cases) != 6 or len(rows) != 24 or len(manifests) != 24:
        raise ValueError("r5_prepared_files_geometry_invalid")
    return p, plan, cases, rows, manifests


def _verify_case_files(plan_dir: Path, case: dict, execution_code_sha: str):
    if case["code_identity"]["branch_execution_commit"] != execution_code_sha:
        raise ValueError("r5_branch_execution_sha_mismatch")
    cfg = case["config_identity"]
    model = case["model_identity"]
    for path_key, hash_key in (
        ("arena_config_path","arena_config_hash"),
        ("model_config_path","model_config_hash"),
    ):
        path = ROOT / (cfg[path_key] if path_key in cfg else model[path_key])
        expected = cfg.get(hash_key) if hash_key in cfg else model.get(hash_key)
        if sha256_file(path) != expected:
            raise ValueError("r5_binding_hash_mismatch:" + hash_key)
    domain_path = ROOT / f"arena/domains/{case['domain_id']}.json"
    if sha256_file(domain_path) != cfg["domain_hash"]:
        raise ValueError("r5_domain_hash_mismatch:" + case["domain_id"])
    domain = load_json(domain_path)
    if stable_hash(domain["task"]) != cfg["task_hash"]:
        raise ValueError("r5_task_hash_mismatch:" + case["domain_id"])
    if stable_hash(domain["agents"]) != cfg["agent_pool_hash"]:
        raise ValueError("r5_agent_pool_hash_mismatch:" + case["domain_id"])
    parent = load_json(plan_dir / case["parent_snapshot_path"])
    envelope = load_json(plan_dir / case["envelope_path"])
    verify_state_snapshot(parent)
    verify_one_shot_envelope(envelope)
    if parent["state_hash"] != case["parent_state_hash"]:
        raise ValueError("r5_parent_state_hash_mismatch")
    if parent.get("terminated") is not False or not parent.get("queue"):
        raise ValueError("r5_parent_not_resumable")
    if parent["queue"][0] != case["expected_first_resume_actor"]:
        raise ValueError("r5_parent_first_actor_mismatch")
    key = case["state_key"]
    if parent["shared_state_metadata"][key]["status"] != "fact":
        raise ValueError("r5_parent_target_status_not_fact")
    return domain, load_json(ROOT / cfg["arena_config_path"]), load_json(ROOT / model["model_config_path"]), parent, envelope


def _validate_limits(branch_count, per_branch_max_calls, per_branch_ceiling, global_ceiling):
    if per_branch_max_calls <= 0 or per_branch_ceiling <= 0 or global_ceiling <= 0:
        raise ValueError("r5_positive_budget_limits_required")
    if global_ceiling + 1e-12 < branch_count * per_branch_ceiling:
        raise ValueError("r5_global_ceiling_must_cover_symmetric_branch_ceilings")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan-dir", required=True)
    ap.add_argument("--outdir")
    ap.add_argument("--provider", default="deepseek")
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
        raise SystemExit("r5_preflight_and_real_are_mutually_exclusive")
    p, plan, cases, rows, manifests = _load_bundle(args.plan_dir)
    if plan["branch_execution_commit"] != args.execution_code_sha:
        raise ValueError("r5_plan_execution_sha_mismatch")
    _validate_limits(len(rows), args.per_branch_max_calls, args.per_branch_spending_ceiling, args.global_spending_ceiling)

    case_map = {c["case_id"]: c for c in cases}
    manifest_map = {m["branch_hash"]: m for m in manifests}
    verified = {}
    for case in cases:
        verified[case["case_id"]] = _verify_case_files(p, case, args.execution_code_sha)
        if case["model_identity"]["provider"] != args.provider:
            raise ValueError("r5_provider_binding_mismatch")
    for row in rows:
        case = case_map[row["case_id"]]
        _, _, _, parent, envelope = verified[row["case_id"]]
        manifest = manifest_map[row["branch_hash"]]
        bound = None if row["condition_id"] == CONTROL_CONDITION else envelope
        verify_branch_manifest_v3(manifest, parent_snapshot=parent, envelope=bound)

    if args.preflight_only:
        print("V5_CROSS_DOMAIN_R5_FIRST_WAVE_PREFLIGHT=PASS")
        print("CASE_COUNT=6")
        print("BRANCH_COUNT=24")
        print("PAID_API_CALLED=NO")
        return

    if not args.execute_real_api or args.authorization_phrase != AUTH_PHRASE:
        raise SystemExit("Refusing provider calls: exact cross-domain R5 authorization required.")
    if not args.outdir:
        raise SystemExit("r5_outdir_required")
    if args.provider == "deepseek" and not os.environ.get("DEEPSEEK_API_KEY"):
        raise SystemExit("DEEPSEEK_API_KEY is not set")

    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_cross_domain_r5_output")
    out.mkdir(parents=True)
    traces_path = out / "traces.jsonl"
    errors_path = out / "errors.jsonl"
    errors = []
    total_spend = 0.0

    first_model = verified[cases[0]["case_id"]][2]
    upstream = provider_from_config(first_model)
    auth = {
        "schema": "RB-V5-CROSS-DOMAIN-R5-FIRST-WAVE-AUTHORIZATION-v0.1",
        "authorization_phrase": args.authorization_phrase,
        "execution_code_sha": args.execution_code_sha,
        "plan_hash": plan["plan_hash"],
        "case_count": 6,
        "branch_count": 24,
        "provider": args.provider,
        "per_branch_max_calls": args.per_branch_max_calls,
        "per_branch_spending_ceiling": args.per_branch_spending_ceiling,
        "global_spending_ceiling": args.global_spending_ceiling,
        "currency": args.currency.upper(),
        "automatic_paid_evaluator": False,
        "r6_semantic_inertia_adjudication": False,
        "r7_repair_authorized": False,
        "r8_cpr_adjudication": False,
    }
    auth["authorization_hash"] = stable_hash(auth)
    _write_json(out / "authorization_record.json", auth)

    for row in rows:
        case = case_map[row["case_id"]]
        domain, arena_cfg, model_cfg, parent, envelope = verified[row["case_id"]]
        manifest = manifest_map[row["branch_hash"]]
        bound = None if row["condition_id"] == CONTROL_CONDITION else envelope
        provider = BudgetedProvider(
            upstream,
            model_cfg,
            spending_ceiling=args.per_branch_spending_ceiling,
            currency=args.currency,
            max_calls=args.per_branch_max_calls,
        )
        transform = OneShotRuntimeViewTransform(bound) if bound is not None else None
        parent_material_hash = stable_hash(parent)
        journal_path = out / "journals" / (stable_hash({"run_id": row["run_id"]})[:20] + ".jsonl")
        try:
            with Journal(journal_path) as journal:
                trace = run_arena_once(
                    domain,
                    arena_cfg,
                    provider,
                    row["run_id"],
                    row["logical_seed"],
                    recorder=journal,
                    initial_state_snapshot=parent,
                    branch_manifest=manifest,
                    runtime_view_transform=transform,
                )
            if stable_hash(parent) != parent_material_hash:
                raise ValueError("r5_frozen_parent_mutated")
            records = list(trace.get("runtime_transform_records") or [])
            if row["condition_id"] == CONTROL_CONDITION:
                if records:
                    raise ValueError("r5_control_has_experiment_origin_exposure")
                direct_count = 0
            else:
                transform.verify_finished()
                if len(records) != 1:
                    raise ValueError("r5_intervention_requires_exactly_one_exposure")
                rec = records[0]
                if rec.get("actor") != parent["queue"][0] or rec.get("turn") != int(parent["turns"]) + 1:
                    raise ValueError("r5_intervention_not_first_resumed_agent_turn")
                if rec.get("from_status") != "fact" or rec.get("to_status") != "unconfirmed":
                    raise ValueError("r5_intervention_status_delta_invalid")
                if rec.get("persistent_state_mutation") is not False:
                    raise ValueError("r5_intervention_persisted")
                direct_count = 1
            trace.update({
                "v5_cross_domain_r5_first_wave": True,
                "r5_plan_hash": plan["plan_hash"],
                "r5_authorization_hash": auth["authorization_hash"],
                "case_id": row["case_id"],
                "wave_id": row["wave_id"],
                "source_run_id": row["source_run_id"],
                "source_case_hash": row["source_case_hash"],
                "source_audit_hash": row["source_audit_hash"],
                "pair_id": row["pair_id"],
                "replicate_index": row["replicate_index"],
                "condition_id": row["condition_id"],
                "pair_order_pattern": row["pair_order_pattern"],
                "execution_order": row["execution_order"],
                "source_parent_state_hash": row["parent_state_hash"],
                "direct_experiment_origin_exposure_count": direct_count,
                "experiment_origin_reinjection_count": 0,
                "persistent_experiment_origin_mutation": False,
                "provider": args.provider,
                "code_commit_sha": args.execution_code_sha,
                "review_status": "PENDING_R5_LOCAL_RESPONSE_SEMANTIC_AUDIT",
                "r6_semantic_inertia_status": "NOT_ADJUDICATED",
                "r7_repair_status": "NOT_AUTHORIZED",
                "semantic_cpr_status": "NOT_ADJUDICATED",
            })
            _append_jsonl(traces_path, trace)
            total_spend += float(provider.estimated_spend)
        except Exception as err:
            error = {
                "run_id": row["run_id"],
                "case_id": row["case_id"],
                "pair_id": row["pair_id"],
                "condition_id": row["condition_id"],
                "error": repr(err),
            }
            errors.append(error)
            _append_jsonl(errors_path, error)

    if total_spend > args.global_spending_ceiling + 1e-12:
        errors.append({"error":"r5_observed_estimated_spend_exceeds_global_ceiling","estimated_total_spend":total_spend})
        _append_jsonl(errors_path, errors[-1])
    preserved = load_jsonl(traces_path) if traces_path.exists() else []
    summary = {
        "schema": "RB-V5-CROSS-DOMAIN-R5-FIRST-WAVE-RUN-SUMMARY-v0.1",
        "plan_hash": plan["plan_hash"],
        "authorization_hash": auth["authorization_hash"],
        "planned_branch_count": 24,
        "preserved_trace_count": len(preserved),
        "runner_error_count": len(errors),
        "estimated_total_spend": total_spend,
        "currency": args.currency.upper(),
        "provider_calls_present": len(preserved) > 0,
        "paid_evaluator_called": False,
        "r6_semantic_inertia_adjudication": False,
        "r7_repair_called": False,
        "r8_cpr_adjudication": False,
    }
    summary["summary_hash"] = stable_hash(summary)
    _write_json(out / "summary.json", summary)
    _write_json(out / "errors.json", errors)
    if errors:
        raise SystemExit("cross-domain R5 first wave contains errors; preserved all available evidence")
    print("V5_CROSS_DOMAIN_R5_FIRST_WAVE_COMPLETE")
    print("PRESERVED_TRACE_COUNT=" + str(len(preserved)))
    print("ESTIMATED_TOTAL_SPEND=" + str(total_spend))
    print("PAID_EVALUATOR_CALLED=NO")
    print("R6_SEMANTIC_INERTIA=NOT_ADJUDICATED")
    print("CPR=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
