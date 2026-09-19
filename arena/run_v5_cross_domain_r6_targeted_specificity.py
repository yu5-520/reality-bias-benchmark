#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
from .providers import ScriptedProvider, provider_from_config

ROOT=Path(__file__).resolve().parents[1]
AUTH_PHRASE="CALL_REAL_V5_CROSS_DOMAIN_R6_TARGETED_SPECIFICITY_API"


def _append_jsonl(path,row):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as f:
        f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n")
        f.flush()
        os.fsync(f.fileno())


def _write_json(path,row):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(row,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")


def _load(plan_dir):
    p=Path(plan_dir)
    plan=load_json(p/"plan.json")
    parent=load_json(p/"parent_snapshot.json")
    envelope=load_json(p/"one_shot_envelope.json")
    case=load_json(p/"case_binding.json")
    rows=load_jsonl(p/"branch_execution_manifest.jsonl")
    manifests=load_jsonl(p/"branch_manifests.jsonl")
    if plan.get("schema")!="RB-V5-CROSS-DOMAIN-R6-TARGETED-SPECIFICITY-EXECUTION-PLAN-v0.1":
        raise ValueError("r6_targeted_plan_schema_invalid")
    if plan.get("authorization_status")!="NOT_AUTHORIZED":
        raise ValueError("r6_targeted_plan_self_authorized")
    if len(rows)!=16 or len(manifests)!=16:
        raise ValueError("r6_targeted_geometry_invalid")
    return p,plan,parent,envelope,case,rows,manifests


def _verify_bindings(p,plan,parent,envelope,case,rows,manifests,execution_sha,provider):
    verify_state_snapshot(parent)
    verify_one_shot_envelope(envelope)
    if plan["branch_execution_commit"]!=execution_sha:
        raise ValueError("r6_targeted_execution_sha_mismatch")
    if parent["state_hash"]!=plan["parent_state_hash"] or envelope["envelope_hash"]!=plan["envelope_hash"]:
        raise ValueError("r6_targeted_parent_or_envelope_mismatch")
    cfg=case["config_identity"]; model=case["model_identity"]
    if model["provider"]!=provider:
        raise ValueError("r6_targeted_provider_mismatch")
    for path_key,hash_key in (("arena_config_path","arena_config_hash"),("model_config_path","model_config_hash")):
        path=ROOT/(cfg[path_key] if path_key in cfg else model[path_key])
        expected=cfg.get(hash_key) if hash_key in cfg else model.get(hash_key)
        if sha256_file(path)!=expected:
            raise ValueError("r6_targeted_binding_hash_mismatch:"+hash_key)
    domain_path=ROOT/f"arena/domains/{case['domain_id']}.json"
    if sha256_file(domain_path)!=cfg["domain_hash"]:
        raise ValueError("r6_targeted_domain_hash_mismatch")
    domain=load_json(domain_path)
    if stable_hash(domain["task"])!=cfg["task_hash"] or stable_hash(domain["agents"])!=cfg["agent_pool_hash"]:
        raise ValueError("r6_targeted_domain_semantic_hash_mismatch")
    manifest_map={m["branch_hash"]:m for m in manifests}
    for row in rows:
        bound=None if row["condition_id"]==CONTROL_CONDITION else envelope
        verify_branch_manifest_v3(manifest_map[row["branch_hash"]],parent_snapshot=parent,envelope=bound)
    return domain,load_json(ROOT/cfg["arena_config_path"]),load_json(ROOT/model["model_config_path"]),manifest_map


def _offline_preflight(domain,arena_cfg,parent,envelope,rows,manifest_map):
    checked=0
    for row in rows:
        bound=None if row["condition_id"]==CONTROL_CONDITION else envelope
        transform=OneShotRuntimeViewTransform(bound) if bound is not None else None
        scripted=ScriptedProvider([
            {"decision_summary":"offline r6 specificity lifecycle","actions":[]}
            for _ in range(max(128,int(arena_cfg.get("max_turns",64))+8))
        ])
        before=stable_hash(parent)
        trace=run_arena_once(
            domain,arena_cfg,scripted,"offline:"+row["run_id"],row["logical_seed"],
            initial_state_snapshot=parent,
            branch_manifest=manifest_map[row["branch_hash"]],
            runtime_view_transform=transform,
        )
        if stable_hash(parent)!=before:
            raise ValueError("r6_targeted_offline_parent_mutated")
        records=list(trace.get("runtime_transform_records") or [])
        if row["condition_id"]==CONTROL_CONDITION:
            if records:
                raise ValueError("r6_targeted_offline_control_exposure")
        else:
            transform.verify_finished()
            if len(records)!=1 or records[0].get("from_status")!="fact" or records[0].get("to_status")!="unconfirmed":
                raise ValueError("r6_targeted_offline_intervention_invalid")
        checked+=1
    if checked!=16:
        raise ValueError("r6_targeted_offline_count_invalid")
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

    if args.global_spending_ceiling+1e-12 < 16*args.per_branch_spending_ceiling:
        raise ValueError("r6_targeted_global_ceiling_too_low")
    p,plan,parent,envelope,case,rows,manifests=_load(args.plan_dir)
    domain,arena_cfg,model_cfg,manifest_map=_verify_bindings(
        p,plan,parent,envelope,case,rows,manifests,args.execution_code_sha,args.provider
    )
    if args.preflight_only:
        checked=_offline_preflight(domain,arena_cfg,parent,envelope,rows,manifest_map)
        print("V5_CROSS_DOMAIN_R6_TARGETED_SPECIFICITY_PREFLIGHT=PASS")
        print("OFFLINE_BRANCH_LIFECYCLE_CHECKED="+str(checked))
        print("PAID_API_CALLED=NO")
        return

    if not args.execute_real_api or args.authorization_phrase!=AUTH_PHRASE:
        raise SystemExit("Refusing provider calls: exact R6 targeted specificity authorization required.")
    if not args.outdir:
        raise SystemExit("r6_targeted_outdir_required")
    if args.provider=="deepseek" and not os.environ.get("DEEPSEEK_API_KEY"):
        raise SystemExit("DEEPSEEK_API_KEY is not set")
    if args.per_branch_max_calls<=0 or args.per_branch_spending_ceiling<=0 or args.global_spending_ceiling<=0:
        raise SystemExit("positive R6 targeted budgets required")

    out=Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r6_targeted_output")
    out.mkdir(parents=True)

    auth={
        "schema":"RB-V5-CROSS-DOMAIN-R6-TARGETED-SPECIFICITY-AUTHORIZATION-v0.1",
        "authorization_phrase":args.authorization_phrase,
        "execution_code_sha":args.execution_code_sha,
        "plan_hash":plan["plan_hash"],
        "target_case_id":case["case_id"],
        "new_pair_count":8,
        "new_branch_count":16,
        "provider":args.provider,
        "per_branch_max_calls":args.per_branch_max_calls,
        "per_branch_spending_ceiling":args.per_branch_spending_ceiling,
        "global_spending_ceiling":args.global_spending_ceiling,
        "currency":args.currency.upper(),
        "automatic_paid_evaluator":False,
        "r7_repair_authorized":False,
        "semantic_cpr_status":"NOT_ADJUDICATED",
    }
    auth["authorization_hash"]=stable_hash(auth)
    _write_json(out/"authorization_record.json",auth)

    upstream=provider_from_config(model_cfg)
    traces_path=out/"traces.jsonl"
    errors=[]
    total_spend=0.0
    for row in rows:
        provider=BudgetedProvider(
            upstream,model_cfg,
            spending_ceiling=args.per_branch_spending_ceiling,
            currency=args.currency,
            max_calls=args.per_branch_max_calls,
        )
        bound=None if row["condition_id"]==CONTROL_CONDITION else envelope
        transform=OneShotRuntimeViewTransform(bound) if bound is not None else None
        journal_path=out/"journals"/(stable_hash({"run_id":row["run_id"]})[:20]+".jsonl")
        try:
            with Journal(journal_path) as journal:
                trace=run_arena_once(
                    domain,arena_cfg,provider,row["run_id"],row["logical_seed"],
                    recorder=journal,
                    initial_state_snapshot=parent,
                    branch_manifest=manifest_map[row["branch_hash"]],
                    runtime_view_transform=transform,
                )
            records=list(trace.get("runtime_transform_records") or [])
            if row["condition_id"]==CONTROL_CONDITION:
                if records:
                    raise ValueError("r6_targeted_control_has_exposure")
            else:
                transform.verify_finished()
                if len(records)!=1 or records[0].get("actor")!=parent["queue"][0]:
                    raise ValueError("r6_targeted_intervention_exposure_invalid")
            trace.update({
                "v5_cross_domain_r6_targeted_specificity":True,
                "r6_plan_hash":plan["plan_hash"],
                "r6_authorization_hash":auth["authorization_hash"],
                "case_id":case["case_id"],
                "pair_id":row["pair_id"],
                "replicate_index":row["replicate_index"],
                "condition_id":row["condition_id"],
                "pair_order_pattern":row["pair_order_pattern"],
                "source_parent_state_hash":parent["state_hash"],
                "provider":args.provider,
                "code_commit_sha":args.execution_code_sha,
                "review_status":"PENDING_TARGETED_SEMANTIC_SPECIFICITY_AUDIT",
                "system_inertia_status":"NOT_ADJUDICATED",
                "r7_repair_status":"NOT_AUTHORIZED",
                "semantic_cpr_status":"NOT_ADJUDICATED",
            })
            _append_jsonl(traces_path,trace)
            total_spend+=float(provider.estimated_spend)
        except Exception as err:
            e={"run_id":row["run_id"],"pair_id":row["pair_id"],"condition_id":row["condition_id"],"error":repr(err)}
            errors.append(e)
            _append_jsonl(out/"errors.jsonl",e)

    preserved=load_jsonl(traces_path) if traces_path.exists() else []
    summary={
        "schema":"RB-V5-CROSS-DOMAIN-R6-TARGETED-SPECIFICITY-RUN-SUMMARY-v0.1",
        "plan_hash":plan["plan_hash"],
        "authorization_hash":auth["authorization_hash"],
        "planned_branch_count":16,
        "preserved_trace_count":len(preserved),
        "runner_error_count":len(errors),
        "estimated_total_spend":total_spend,
        "currency":args.currency.upper(),
        "paid_evaluator_called":False,
        "system_inertia_status":"NOT_ADJUDICATED",
        "r7_repair_called":False,
        "semantic_cpr_status":"NOT_ADJUDICATED",
    }
    summary["summary_hash"]=stable_hash(summary)
    _write_json(out/"summary.json",summary)
    _write_json(out/"errors.json",errors)
    if errors:
        raise SystemExit("R6 targeted specificity collection contains errors; evidence preserved")
    print("V5_CROSS_DOMAIN_R6_TARGETED_SPECIFICITY_COMPLETE")
    print("PRESERVED_TRACE_COUNT="+str(len(preserved)))
    print("ESTIMATED_TOTAL_SPEND="+str(total_spend))
    print("PAID_EVALUATOR_CALLED=NO")


if __name__=="__main__":
    main()
