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
from .one_shot_intervention import INTERVENTION_CONDITION, OneShotRuntimeViewTransform, verify_branch_manifest_v3
from .providers import ScriptedProvider, provider_from_config
from .run_v5_cross_domain_r5_first_wave import _append_jsonl, _write_json, _verify_case_files, _validate_limits

AUTH_PHRASE="CALL_REAL_V5_CROSS_DOMAIN_R5_CANONICAL_API"
PLAN_SCHEMA="RB-V5-CROSS-DOMAIN-R5-CANONICAL-EXECUTION-PLAN-v0.1"


def _load_bundle(plan_dir:str):
    p=Path(plan_dir)
    plan=load_json(p/"plan.json")
    cases=load_jsonl(p/"case_bindings.jsonl")
    rows=load_jsonl(p/"branch_execution_manifest.jsonl")
    manifests=load_jsonl(p/"branch_manifests.jsonl")
    if plan.get("schema")!=PLAN_SCHEMA:
        raise ValueError("r5_canonical_plan_schema_invalid")
    if plan.get("authorization_status")!="NOT_AUTHORIZED":
        raise ValueError("r5_canonical_plan_must_not_self_authorize")
    if plan.get("branch_count")!=plan.get("case_count"):
        raise ValueError("r5_canonical_branch_count_must_equal_case_count")
    if plan.get("synthetic_control_branch_count")!=0:
        raise ValueError("r5_canonical_synthetic_control_forbidden")
    if plan.get("canonical_replicate_count")!=1:
        raise ValueError("r5_canonical_replicate_count_must_be_one")
    if len(cases)!=plan["case_count"] or len(rows)!=plan["case_count"] or len(manifests)!=plan["case_count"]:
        raise ValueError("r5_canonical_files_geometry_invalid")
    for row in rows:
        if row.get("condition_id")!=INTERVENTION_CONDITION:
            raise ValueError("r5_canonical_only_one_shot_intervention_allowed")
        if int(row.get("replicate_index",0))!=1:
            raise ValueError("r5_canonical_replicate_index_must_be_one")
        if row.get("synthetic_control") is not False:
            raise ValueError("r5_canonical_row_synthetic_control_forbidden")
    return p,plan,cases,rows,manifests


def _preflight(cases,rows,manifests,verified):
    manifest_map={m["branch_hash"]:m for m in manifests}
    checked=0
    for row in rows:
        domain,arena_cfg,_,parent,envelope=verified[row["case_id"]]
        manifest=manifest_map[row["branch_hash"]]
        scripted=ScriptedProvider([
            {"decision_summary":"offline canonical R5 lifecycle preflight","actions":[]}
            for _ in range(max(128,int(arena_cfg.get("max_turns",64))+8))
        ])
        transform=OneShotRuntimeViewTransform(envelope)
        before=stable_hash(parent)
        trace=run_arena_once(
            domain,arena_cfg,scripted,"offline-preflight:"+row["run_id"],1,
            initial_state_snapshot=parent,branch_manifest=manifest,runtime_view_transform=transform,
        )
        if stable_hash(parent)!=before:
            raise ValueError("r5_canonical_preflight_mutated_parent")
        transform.verify_finished()
        recs=list(trace.get("runtime_transform_records") or [])
        if len(recs)!=1:
            raise ValueError("r5_canonical_preflight_requires_one_transform")
        rec=recs[0]
        if rec.get("actor")!=parent["queue"][0] or rec.get("turn")!=int(parent["turns"])+1:
            raise ValueError("r5_canonical_preflight_exposure_position_invalid")
        if rec.get("from_status")!="fact" or rec.get("to_status")!="unconfirmed":
            raise ValueError("r5_canonical_preflight_status_delta_invalid")
        if rec.get("persistent_state_mutation") is not False:
            raise ValueError("r5_canonical_preflight_persistent_mutation")
        checked+=1
    if checked!=len(cases):
        raise ValueError("r5_canonical_preflight_count_mismatch")
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

    if args.preflight_only and args.execute_real_api:
        raise SystemExit("r5_canonical_preflight_and_real_mutually_exclusive")
    p,plan,cases,rows,manifests=_load_bundle(args.plan_dir)
    if plan["branch_execution_commit"]!=args.execution_code_sha:
        raise ValueError("r5_canonical_execution_sha_mismatch")
    _validate_limits(len(rows),args.per_branch_max_calls,args.per_branch_spending_ceiling,args.global_spending_ceiling)

    manifest_map={m["branch_hash"]:m for m in manifests}
    verified={}
    for case in cases:
        verified[case["case_id"]]=_verify_case_files(p,case,args.execution_code_sha)
        if case["model_identity"]["provider"]!=args.provider:
            raise ValueError("r5_canonical_provider_binding_mismatch")
    for row in rows:
        _,_,_,parent,envelope=verified[row["case_id"]]
        verify_branch_manifest_v3(manifest_map[row["branch_hash"]],parent_snapshot=parent,envelope=envelope)

    if args.preflight_only:
        checked=_preflight(cases,rows,manifests,verified)
        print("V5_R5_CANONICAL_PREFLIGHT=PASS")
        print("CASE_COUNT="+str(len(cases)))
        print("BRANCH_COUNT="+str(len(rows)))
        print("OFFLINE_BRANCH_LIFECYCLE_CHECKED="+str(checked))
        print("PAID_API_CALLED=NO")
        return

    if not args.execute_real_api or args.authorization_phrase!=AUTH_PHRASE:
        raise SystemExit("Refusing provider calls: exact canonical R5 authorization required.")
    if not args.outdir:
        raise SystemExit("r5_canonical_outdir_required")
    if args.provider=="deepseek" and not os.environ.get("DEEPSEEK_API_KEY"):
        raise SystemExit("DEEPSEEK_API_KEY is not set")

    out=Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r5_canonical_output")
    out.mkdir(parents=True)
    traces_path=out/"traces.jsonl"; errors_path=out/"errors.jsonl"
    errors=[]; total_spend=0.0
    auth={
        "schema":"RB-V5-R5-CANONICAL-AUTHORIZATION-v0.1",
        "authorization_phrase":args.authorization_phrase,
        "execution_code_sha":args.execution_code_sha,
        "plan_hash":plan["plan_hash"],
        "case_count":plan["case_count"],
        "branch_count":plan["branch_count"],
        "synthetic_control_branch_count":0,
        "canonical_replicate_count":1,
        "provider":args.provider,
        "per_branch_max_calls":args.per_branch_max_calls,
        "per_branch_spending_ceiling":args.per_branch_spending_ceiling,
        "global_spending_ceiling":args.global_spending_ceiling,
        "currency":args.currency.upper(),
        "automatic_paid_evaluator":False,
        "r6_new_subject_experiment":False,
        "r7_repair_authorized":False,
        "r8_cpr_adjudication":False,
    }
    auth["authorization_hash"]=stable_hash(auth)
    _write_json(out/"authorization_record.json",auth)

    for row in rows:
        domain,arena_cfg,model_cfg,parent,envelope=verified[row["case_id"]]
        provider=BudgetedProvider(
            provider_from_config(model_cfg),model_cfg,
            spending_ceiling=args.per_branch_spending_ceiling,currency=args.currency,max_calls=args.per_branch_max_calls,
        )
        transform=OneShotRuntimeViewTransform(envelope)
        before=stable_hash(parent)
        journal_path=out/"journals"/(stable_hash({"run_id":row["run_id"]})[:20]+".jsonl")
        try:
            with Journal(journal_path) as journal:
                trace=run_arena_once(
                    domain,arena_cfg,provider,row["run_id"],1,recorder=journal,
                    initial_state_snapshot=parent,
                    branch_manifest=manifest_map[row["branch_hash"]],
                    runtime_view_transform=transform,
                )
            if stable_hash(parent)!=before:
                raise ValueError("r5_canonical_frozen_parent_mutated")
            transform.verify_finished()
            recs=list(trace.get("runtime_transform_records") or [])
            if len(recs)!=1:
                raise ValueError("r5_canonical_requires_exactly_one_exposure")
            rec=recs[0]
            if rec.get("actor")!=parent["queue"][0] or rec.get("turn")!=int(parent["turns"])+1:
                raise ValueError("r5_canonical_exposure_position_invalid")
            trace.update({
                "v5_r5_canonical":True,
                "r5_plan_hash":plan["plan_hash"],
                "r5_authorization_hash":auth["authorization_hash"],
                "case_id":row["case_id"],
                "wave_id":row["wave_id"],
                "source_run_id":row["source_run_id"],
                "source_case_hash":row["source_case_hash"],
                "source_audit_hash":row.get("source_audit_hash"),
                "natural_reference_run_id":row["natural_reference_run_id"],
                "natural_reference_trace_hash":row["natural_reference_trace_hash"],
                "condition_id":INTERVENTION_CONDITION,
                "canonical_replicate_index":1,
                "synthetic_control":False,
                "direct_experiment_origin_exposure_count":1,
                "experiment_origin_reinjection_count":0,
                "persistent_experiment_origin_mutation":False,
                "provider":args.provider,
                "code_commit_sha":args.execution_code_sha,
                "review_status":"PENDING_R6_PASSIVE_STRUCTURAL_SEMANTIC_AUDIT",
                "r7_repair_status":"NOT_AUTHORIZED",
                "semantic_cpr_status":"NOT_ADJUDICATED",
            })
            _append_jsonl(traces_path,trace)
            total_spend+=float(provider.estimated_spend)
        except Exception as err:
            e={"run_id":row["run_id"],"case_id":row["case_id"],"error":repr(err)}
            errors.append(e); _append_jsonl(errors_path,e)

    preserved=load_jsonl(traces_path) if traces_path.exists() else []
    summary={
        "schema":"RB-V5-R5-CANONICAL-RUN-SUMMARY-v0.1",
        "plan_hash":plan["plan_hash"],
        "authorization_hash":auth["authorization_hash"],
        "planned_case_count":plan["case_count"],
        "planned_branch_count":plan["branch_count"],
        "preserved_trace_count":len(preserved),
        "runner_error_count":len(errors),
        "synthetic_control_branch_count":0,
        "canonical_replicate_count":1,
        "estimated_total_spend":total_spend,
        "currency":args.currency.upper(),
        "paid_evaluator_called":False,
        "r6_new_subject_experiment":False,
        "r7_repair_called":False,
        "r8_cpr_adjudication":False,
    }
    summary["summary_hash"]=stable_hash(summary)
    _write_json(out/"summary.json",summary); _write_json(out/"errors.json",errors)
    if errors:
        raise SystemExit("canonical R5 contains errors; available evidence preserved")
    print("V5_R5_CANONICAL_COMPLETE")
    print("PRESERVED_TRACE_COUNT="+str(len(preserved)))
    print("SYNTHETIC_CONTROL_BRANCH_COUNT=0")
    print("CANONICAL_REPLICATE_COUNT=1")
    print("ESTIMATED_TOTAL_SPEND="+str(total_spend))


if __name__=="__main__":
    main()
