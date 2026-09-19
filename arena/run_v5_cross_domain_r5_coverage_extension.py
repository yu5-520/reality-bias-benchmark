#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .core import stable_hash
from .cost_budget import BudgetedProvider
from .engine import run_arena_once
from .io_utils import load_json, load_jsonl
from .journal import Journal
from .one_shot_intervention import (
    CONTROL_CONDITION,
    INTERVENTION_CONDITION,
    OneShotRuntimeViewTransform,
    verify_branch_manifest_v3,
)
from .providers import ScriptedProvider, provider_from_config
from .run_v5_cross_domain_r5_first_wave import _verify_case_files

AUTH_PHRASE="CALL_REAL_V5_CROSS_DOMAIN_R5_COVERAGE_EXTENSION_API"


def _append_jsonl(path,row):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as f:
        f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n")
        f.flush()
        os.fsync(f.fileno())


def _write_json(path,row):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(row,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")


def _load_bundle(plan_dir):
    p=Path(plan_dir)
    plan=load_json(p/"plan.json")
    cases=load_jsonl(p/"case_bindings.jsonl")
    rows=load_jsonl(p/"branch_execution_manifest.jsonl")
    manifests=load_jsonl(p/"branch_manifests.jsonl")
    if plan.get("schema")!="RB-V5-CROSS-DOMAIN-R5-COVERAGE-EXTENSION-EXECUTION-PLAN-v0.1":
        raise ValueError("r5_coverage_plan_schema_invalid")
    if plan.get("authorization_status")!="NOT_AUTHORIZED":
        raise ValueError("r5_coverage_plan_self_authorized")
    if plan.get("case_count")!=23 or plan.get("pair_count")!=23 or plan.get("branch_count")!=46:
        raise ValueError("r5_coverage_plan_geometry_invalid")
    if len(cases)!=23 or len(rows)!=46 or len(manifests)!=46:
        raise ValueError("r5_coverage_bundle_geometry_invalid")
    return p,plan,cases,rows,manifests


def _validate_budget(branch_count,max_calls,per_branch,global_ceiling):
    if max_calls<=0 or per_branch<=0 or global_ceiling<=0:
        raise ValueError("r5_coverage_positive_budget_required")
    if global_ceiling+1e-12 < branch_count*per_branch:
        raise ValueError("r5_coverage_global_ceiling_too_low")


def _offline_preflight(cases,rows,manifests,verified):
    case_map={c["case_id"]:c for c in cases}
    manifest_map={m["branch_hash"]:m for m in manifests}
    checked=0
    for row in rows:
        case=case_map[row["case_id"]]
        domain,arena_cfg,_,parent,envelope=verified[row["case_id"]]
        manifest=manifest_map[row["branch_hash"]]
        bound=None if row["condition_id"]==CONTROL_CONDITION else envelope
        transform=OneShotRuntimeViewTransform(bound) if bound is not None else None
        scripted=ScriptedProvider([
            {"decision_summary":"offline coverage lifecycle","actions":[]}
            for _ in range(max(128,int(arena_cfg.get("max_turns",64))+8))
        ])
        before=stable_hash(parent)
        trace=run_arena_once(
            domain,arena_cfg,scripted,"offline:"+row["run_id"],1,
            initial_state_snapshot=parent,
            branch_manifest=manifest,
            runtime_view_transform=transform,
        )
        if stable_hash(parent)!=before:
            raise ValueError("r5_coverage_offline_parent_mutated")
        records=list(trace.get("runtime_transform_records") or [])
        if row["condition_id"]==CONTROL_CONDITION:
            if records:
                raise ValueError("r5_coverage_offline_control_exposure")
        else:
            transform.verify_finished()
            if len(records)!=1:
                raise ValueError("r5_coverage_offline_intervention_exposure_count")
            rec=records[0]
            if rec.get("actor")!=parent["queue"][0]:
                raise ValueError("r5_coverage_offline_intervention_actor")
            if rec.get("turn")!=int(parent["turns"])+1:
                raise ValueError("r5_coverage_offline_intervention_turn")
            if rec.get("from_status")!="fact" or rec.get("to_status")!="unconfirmed":
                raise ValueError("r5_coverage_offline_intervention_delta")
        checked+=1
    if checked!=46:
        raise ValueError("r5_coverage_offline_checked_count")
    return checked


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--plan-dir",required=True)
    ap.add_argument("--outdir")
    ap.add_argument("--provider",default="deepseek")
    ap.add_argument("--execution-code-sha",required=True)
    ap.add_argument("--per-branch-max-calls",type=int,required=True)
    ap.add_argument("--per-branch-spending-ceiling",type=float,required=True)
    ap.add_argument("--global-spending-ceiling",type=float,required=True)
    ap.add_argument("--currency",default="USD")
    ap.add_argument("--authorization-phrase")
    ap.add_argument("--execute-real-api",action="store_true")
    ap.add_argument("--preflight-only",action="store_true")
    args=ap.parse_args()

    p,plan,cases,rows,manifests=_load_bundle(args.plan_dir)
    if plan["branch_execution_commit"]!=args.execution_code_sha:
        raise ValueError("r5_coverage_execution_sha_mismatch")
    _validate_budget(len(rows),args.per_branch_max_calls,args.per_branch_spending_ceiling,args.global_spending_ceiling)

    case_map={c["case_id"]:c for c in cases}
    manifest_map={m["branch_hash"]:m for m in manifests}
    verified={}
    for case in cases:
        verified[case["case_id"]]=_verify_case_files(p,case,args.execution_code_sha)
        if case["model_identity"]["provider"]!=args.provider:
            raise ValueError("r5_coverage_provider_binding_mismatch")
    for row in rows:
        _,_,_,parent,envelope=verified[row["case_id"]]
        bound=None if row["condition_id"]==CONTROL_CONDITION else envelope
        verify_branch_manifest_v3(manifest_map[row["branch_hash"]],parent_snapshot=parent,envelope=bound)

    if args.preflight_only:
        checked=_offline_preflight(cases,rows,manifests,verified)
        print("V5_CROSS_DOMAIN_R5_COVERAGE_PREFLIGHT=PASS")
        print("CASE_COUNT=23")
        print("BRANCH_COUNT=46")
        print("OFFLINE_BRANCH_LIFECYCLE_CHECKED="+str(checked))
        print("PAID_API_CALLED=NO")
        return

    if not args.execute_real_api or args.authorization_phrase!=AUTH_PHRASE:
        raise SystemExit("Refusing provider calls: exact R5 coverage authorization required.")
    if not args.outdir:
        raise SystemExit("r5_coverage_outdir_required")
    if args.provider=="deepseek" and not os.environ.get("DEEPSEEK_API_KEY"):
        raise SystemExit("DEEPSEEK_API_KEY is not set")

    out=Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r5_coverage_output")
    out.mkdir(parents=True)

    first_model=verified[cases[0]["case_id"]][2]
    upstream=provider_from_config(first_model)
    auth={
        "schema":"RB-V5-CROSS-DOMAIN-R5-COVERAGE-AUTHORIZATION-v0.1",
        "authorization_phrase":args.authorization_phrase,
        "execution_code_sha":args.execution_code_sha,
        "plan_hash":plan["plan_hash"],
        "case_count":23,
        "pair_count":23,
        "branch_count":46,
        "provider":args.provider,
        "per_branch_max_calls":args.per_branch_max_calls,
        "per_branch_spending_ceiling":args.per_branch_spending_ceiling,
        "global_spending_ceiling":args.global_spending_ceiling,
        "currency":args.currency.upper(),
        "automatic_paid_evaluator":False,
        "r6_followup_authorized":False,
        "r7_repair_authorized":False,
        "semantic_cpr_status":"NOT_ADJUDICATED",
    }
    auth["authorization_hash"]=stable_hash(auth)
    _write_json(out/"authorization_record.json",auth)

    errors=[]; total_spend=0.0
    traces_path=out/"traces.jsonl"
    for row in rows:
        domain,arena_cfg,model_cfg,parent,envelope=verified[row["case_id"]]
        provider=BudgetedProvider(
            upstream,model_cfg,
            spending_ceiling=args.per_branch_spending_ceiling,
            currency=args.currency,
            max_calls=args.per_branch_max_calls,
        )
        bound=None if row["condition_id"]==CONTROL_CONDITION else envelope
        transform=OneShotRuntimeViewTransform(bound) if bound is not None else None
        before=stable_hash(parent)
        journal_path=out/"journals"/(stable_hash({"run_id":row["run_id"]})[:20]+".jsonl")
        try:
            with Journal(journal_path) as journal:
                trace=run_arena_once(
                    domain,arena_cfg,provider,row["run_id"],1,
                    recorder=journal,
                    initial_state_snapshot=parent,
                    branch_manifest=manifest_map[row["branch_hash"]],
                    runtime_view_transform=transform,
                )
            if stable_hash(parent)!=before:
                raise ValueError("r5_coverage_frozen_parent_mutated")
            records=list(trace.get("runtime_transform_records") or [])
            if row["condition_id"]==CONTROL_CONDITION:
                if records:
                    raise ValueError("r5_coverage_control_has_exposure")
                direct_count=0
            else:
                transform.verify_finished()
                if len(records)!=1:
                    raise ValueError("r5_coverage_intervention_exposure_count")
                rec=records[0]
                if rec.get("actor")!=parent["queue"][0] or rec.get("turn")!=int(parent["turns"])+1:
                    raise ValueError("r5_coverage_intervention_delivery_boundary")
                direct_count=1
            trace.update({
                "v5_cross_domain_r5_coverage_extension":True,
                "r5_plan_hash":plan["plan_hash"],
                "r5_authorization_hash":auth["authorization_hash"],
                "case_id":row["case_id"],
                "coverage_index":row["coverage_index"],
                "wave_id":row["wave_id"],
                "source_run_id":row["source_run_id"],
                "source_case_hash":row["source_case_hash"],
                "source_audit_hash":row["source_audit_hash"],
                "pair_id":row["pair_id"],
                "condition_id":row["condition_id"],
                "pair_order_pattern":row["pair_order_pattern"],
                "execution_order":row["execution_order"],
                "source_parent_state_hash":row["parent_state_hash"],
                "direct_experiment_origin_exposure_count":direct_count,
                "experiment_origin_reinjection_count":0,
                "persistent_experiment_origin_mutation":False,
                "provider":args.provider,
                "code_commit_sha":args.execution_code_sha,
                "review_status":"PENDING_R5_COVERAGE_SEMANTIC_AUDIT",
                "r6_followup_status":"NOT_AUTHORIZED",
                "r7_repair_status":"NOT_AUTHORIZED",
                "semantic_cpr_status":"NOT_ADJUDICATED",
            })
            _append_jsonl(traces_path,trace)
            total_spend+=float(provider.estimated_spend)
        except Exception as err:
            e={"run_id":row["run_id"],"case_id":row["case_id"],"condition_id":row["condition_id"],"error":repr(err)}
            errors.append(e)
            _append_jsonl(out/"errors.jsonl",e)

    preserved=load_jsonl(traces_path) if traces_path.exists() else []
    summary={
        "schema":"RB-V5-CROSS-DOMAIN-R5-COVERAGE-RUN-SUMMARY-v0.1",
        "plan_hash":plan["plan_hash"],
        "authorization_hash":auth["authorization_hash"],
        "planned_branch_count":46,
        "preserved_trace_count":len(preserved),
        "runner_error_count":len(errors),
        "estimated_total_spend":total_spend,
        "currency":args.currency.upper(),
        "paid_evaluator_called":False,
        "r6_followup_authorized":False,
        "r7_repair_called":False,
        "semantic_cpr_status":"NOT_ADJUDICATED",
    }
    summary["summary_hash"]=stable_hash(summary)
    _write_json(out/"summary.json",summary)
    _write_json(out/"errors.json",errors)
    if errors:
        raise SystemExit("R5 coverage extension contains errors; all available evidence preserved")
    print("V5_CROSS_DOMAIN_R5_COVERAGE_COMPLETE")
    print("PRESERVED_TRACE_COUNT="+str(len(preserved)))
    print("ESTIMATED_TOTAL_SPEND="+str(total_spend))
    print("PAID_EVALUATOR_CALLED=NO")


if __name__=="__main__":
    main()
