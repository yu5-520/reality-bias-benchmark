#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path

from .branch_plan_one_shot import verify_one_shot_branch_plan
from .core import stable_hash
from .cost_budget import BudgetedProvider
from .engine import run_arena_once
from .io_utils import load_json, load_jsonl, sha256_file
from .one_shot_intervention import (
    CONTROL_CONDITION,
    INTERVENTION_CONDITION,
    OneShotRuntimeViewTransform,
    verify_branch_manifest_v3,
    verify_one_shot_envelope,
)
from .providers import provider_from_config

AUTH_PHRASE = "CALL_REAL_R5MID_PROSPECTIVE_ONESHOT_API"
RUN_SUMMARY_SCHEMA = "RB-R5MID-PROSPECTIVE-ONE-SHOT-RUN-SUMMARY-v0.2"
SOURCE_ROLE = "POST_FREEZE_PROSPECTIVE_NATURAL_TRAJECTORY"


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


def validate_symmetric_limits(*, row_count, per_branch_max_calls, per_branch_spending_ceiling, global_spending_ceiling):
    if not isinstance(row_count, int) or row_count <= 0:
        raise ValueError("positive_branch_row_count_required")
    if per_branch_max_calls <= 0 or per_branch_spending_ceiling <= 0 or global_spending_ceiling <= 0:
        raise ValueError("positive_one_shot_limits_required")
    if global_spending_ceiling < per_branch_spending_ceiling * row_count:
        raise ValueError("global_ceiling_must_cover_all_symmetric_per_branch_ceilings")
    return True


def validate_execution_bindings(*, bundle, model_config_path, provider_name, execution_code_sha):
    plan = bundle["plan"]
    parent = bundle["parent_snapshot"]
    envelope = bundle["one_shot_envelope"]
    verify_one_shot_branch_plan(bundle)
    verify_one_shot_envelope(envelope)

    if plan.get("source_evidence_role") != SOURCE_ROLE:
        raise ValueError("formal_one_shot_requires_post_freeze_prospective_source")
    if plan.get("semantic_cpr_status") != "NOT_ADJUDICATED":
        raise ValueError("unexpected_semantic_cpr_plan_state")
    if plan.get("causal_claim_status") != "NOT_TESTED_PREPARED_ONLY":
        raise ValueError("one_shot_plan_must_be_precausal")
    if plan.get("authorization_status") != "NOT_AUTHORIZED":
        raise ValueError("prepared_plan_must_not_self_authorize")
    if plan.get("paid_one_shot_authorization_status") != "NOT_AUTHORIZED":
        raise ValueError("prepared_plan_paid_gate_must_remain_external")
    if plan.get("code_identity", {}).get("branch_execution_commit") != execution_code_sha:
        raise ValueError("execution_code_sha_mismatch_prepared_plan")

    model_config = load_json(model_config_path)
    if model_config.get("provider") != provider_name:
        raise ValueError("provider_model_config_mismatch")
    if sha256_file(model_config_path) != plan.get("model_identity", {}).get("model_config_hash"):
        raise ValueError("model_config_hash_mismatch_prepared_plan")

    config_identity = plan.get("config_identity") or {}
    arena_path = config_identity.get("arena_config_path")
    if not arena_path or sha256_file(arena_path) != config_identity.get("arena_config_hash"):
        raise ValueError("arena_config_hash_mismatch_prepared_plan")
    domain_id = config_identity.get("domain_id")
    domain_path = Path("arena/domains") / f"{domain_id}.json"
    if not domain_path.exists() or sha256_file(domain_path) != config_identity.get("domain_hash"):
        raise ValueError("domain_hash_mismatch_prepared_plan")
    domain = load_json(domain_path)
    if stable_hash(domain.get("task")) != config_identity.get("task_hash"):
        raise ValueError("task_hash_mismatch_prepared_plan")
    if stable_hash(domain.get("agents")) != config_identity.get("agent_registry_hash"):
        raise ValueError("agent_registry_hash_mismatch_prepared_plan")

    if plan.get("parent_snapshot_hash") != parent.get("state_hash") or plan.get("branch_start_snapshot_hash") != parent.get("state_hash"):
        raise ValueError("formal_one_shot_parent_start_hash_mismatch")
    if envelope.get("state_key") != plan.get("common_identity", {}).get("state_key"):
        raise ValueError("formal_one_shot_envelope_state_key_mismatch")
    if envelope.get("source_event_index") != plan.get("common_identity", {}).get("selected_candidate_event_index"):
        raise ValueError("formal_one_shot_envelope_event_mismatch")
    return {"model_config": model_config, "arena_path": arena_path, "domain_path": str(domain_path)}


def verify_trace_exposure_invariants(*, trace, row, envelope, parent_snapshot):
    records = list(trace.get("runtime_transform_records") or [])
    condition = row.get("condition_id")
    if condition == CONTROL_CONDITION:
        if records:
            raise ValueError("control_must_have_zero_experiment_origin_exposures")
        return {
            "direct_experiment_origin_exposure_count": 0,
            "delivery_actor": None,
            "delivery_turn": None,
            "delivery_hash": None,
        }
    if condition != INTERVENTION_CONDITION:
        raise ValueError("unknown_one_shot_condition")
    if len(records) != 1:
        raise ValueError("intervention_must_have_exactly_one_runtime_transform_record")
    record = records[0]
    if record.get("experiment_origin") is not True:
        raise ValueError("one_shot_delivery_must_be_experiment_origin")
    if record.get("envelope_hash") != envelope.get("envelope_hash"):
        raise ValueError("one_shot_delivery_envelope_hash_mismatch")
    if record.get("state_key") != envelope.get("state_key"):
        raise ValueError("one_shot_delivery_state_key_mismatch")
    if record.get("persistent_state_mutation") is not False or record.get("consumed_after_delivery") is not True:
        raise ValueError("one_shot_delivery_lifecycle_invalid")
    expected_turn = int(parent_snapshot.get("turns")) + 1
    if record.get("turn") != expected_turn:
        raise ValueError("one_shot_delivery_not_first_post_jump_turn")
    queue = list(parent_snapshot.get("queue") or [])
    if not queue or record.get("actor") != queue[0]:
        raise ValueError("one_shot_delivery_not_first_structurally_resumed_actor")
    return {
        "direct_experiment_origin_exposure_count": 1,
        "delivery_actor": record.get("actor"),
        "delivery_turn": record.get("turn"),
        "delivery_hash": record.get("delivery_hash"),
    }


def main():
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
    bundle = load_plan_bundle(args.plan_dir)
    row_count = len(bundle["branch_rows"])
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
    if args.preflight_only:
        print("FORMAL_ONESHOT_PREFLIGHT=PASS")
        print("PLAN_HASH=" + bundle["plan"]["plan_hash"])
        print("EXECUTION_CODE_SHA=" + args.execution_code_sha)
        print("PAID_API_CALLED=NO")
        return

    if not args.execute_real_api or args.authorization_phrase != AUTH_PHRASE:
        raise SystemExit("Refusing provider calls: exact prospective one-shot authorization required.")
    if not args.outdir:
        raise SystemExit("outdir_required_for_real_one_shot_execution")
    model_config = bindings["model_config"]
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
    parent_material_hash = stable_hash(bundle["parent_snapshot"])

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
            execution_binding = {
                "schema": "RB-ONE-SHOT-EXECUTION-BINDING-v0.2",
                "run_id": row["run_id"],
                "pair_id": row["pair_id"],
                "condition_id": row["condition_id"],
                "branch_hash": manifest["branch_hash"],
                "plan_hash": bundle["plan"]["plan_hash"],
                "parent_state_hash": bundle["parent_snapshot"]["state_hash"],
                "envelope_hash": bound_envelope.get("envelope_hash") if bound_envelope else None,
                "execution_code_sha": args.execution_code_sha,
                "bound_before_first_provider_call": True,
            }
            execution_binding["binding_hash"] = stable_hash(execution_binding)
            with Journal(journal_path) as journal:
                journal({"record_type": "one_shot_execution_binding", "record": execution_binding})
                trace = run_arena_once(
                    load_json(bindings["domain_path"]),
                    load_json(bindings["arena_path"]),
                    provider,
                    row["run_id"],
                    row.get("logical_seed"),
                    recorder=journal,
                    initial_state_snapshot=bundle["parent_snapshot"],
                    runtime_view_transform=transform,
                )
            if stable_hash(bundle["parent_snapshot"]) != parent_material_hash:
                raise ValueError("frozen_parent_snapshot_mutated_by_branch_execution")
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
            exposure = verify_trace_exposure_invariants(
                trace=trace,
                row=row,
                envelope=bundle["one_shot_envelope"],
                parent_snapshot=bundle["parent_snapshot"],
            )
            if transform_summary["experiment_origin_reinjection_count"] != 0 or transform_summary["persistent_state_mutation"] is not False:
                raise ValueError("one_shot_transform_summary_integrity_failure")
            trace["experimental_branch"] = copy.deepcopy(manifest)
            trace["one_shot_execution_binding"] = execution_binding
            trace["one_shot_intervention_summary"] = transform_summary
            trace["one_shot_exposure_integrity"] = exposure
            trace["pair_id"] = row["pair_id"]
            trace["replicate_index"] = row["replicate_index"]
            trace["condition_id"] = row["condition_id"]
            trace["pair_order_pattern"] = row["pair_order_pattern"]
            trace["branch_plan_hash"] = bundle["plan"]["plan_hash"]
            trace["code_commit_sha"] = args.execution_code_sha
            trace["model_config_hash"] = bundle["plan"]["model_identity"]["model_config_hash"]
            trace["review_status"] = "PENDING_REVIEW"
            _append_jsonl(traces_path, trace)
            total_estimated_spend += float(provider.estimated_spend)
        except Exception as err:
            error = {
                "run_id": row["run_id"],
                "pair_id": row["pair_id"],
                "condition_id": row["condition_id"],
                "branch_hash": row["branch_hash"],
                "error": repr(err),
            }
            errors.append(error)
            _append_jsonl(errors_path, error)

    if total_estimated_spend > args.global_spending_ceiling + 1e-12:
        raise ValueError("observed_estimated_spend_exceeds_global_ceiling")
    summary = {
        "schema": RUN_SUMMARY_SCHEMA,
        "plan_hash": bundle["plan"]["plan_hash"],
        "execution_code_sha": args.execution_code_sha,
        "planned_branch_count": row_count,
        "preserved_trace_count": len(load_jsonl(traces_path)) if traces_path.exists() else 0,
        "runner_error_count": len(errors),
        "estimated_total_spend": total_estimated_spend,
        "currency": args.currency.upper(),
        "per_branch_max_calls": args.per_branch_max_calls,
        "per_branch_spending_ceiling": args.per_branch_spending_ceiling,
        "global_spending_ceiling": args.global_spending_ceiling,
        "automatic_paid_evaluator_called": False,
        "old_phase_b_authorization_reused": False,
        "prospective_natural_authorization_reused": False,
        "authorization_phrase_family": AUTH_PHRASE,
    }
    summary["summary_hash"] = stable_hash(summary)
    _write_json(out / "summary.json", summary)
    _write_json(out / "errors.json", errors)
    if errors:
        raise SystemExit("one-shot branch collection contains runner errors; preserved all available evidence")
    print("PROSPECTIVE_ONE_SHOT_BRANCH_COLLECTION_COMPLETE")
    print("PAID_EVALUATOR_CALLED=NO")


if __name__ == "__main__":
    main()
