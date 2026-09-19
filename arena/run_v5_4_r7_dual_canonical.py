#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl, sha256_file
from .providers import provider_from_config
from .run_r7_three_arm_real import execute_real_batch, validate_symmetric_limits, _credential_check

AUTH_PHRASE="CALL_REAL_V5_4_R7_DUAL_API"
ARM_MAP={
    "C2_PERSISTENT_FIELD":"R7_P_PERSISTENT_SEMANTIC",
    "C3_ALR":"R7_S_STRUCTURED_LINEAGE_REPAIR",
}


def _require(ok,message):
    if not ok:
        raise ValueError(message)


def _hash_without(row,key):
    m=dict(row)
    m.pop(key,None)
    return stable_hash(m)


def _load_case_bundle(case_dir):
    p=Path(case_dir)
    bundle={
        "plan":load_json(p/"r7_plan.json"),
        "source_parent_snapshot":load_json(p/"source_parent_snapshot.json"),
        "c3_recovery_checkpoint":load_json(p/"c3_recovery_checkpoint.json"),
        "c1_one_shot_envelope":load_json(p/"c1_one_shot_envelope.json"),
        "c2_persistent_field_envelope":load_json(p/"c2_persistent_field_envelope.json"),
        "c3_alr_binding":load_json(p/"c3_alr_binding.json"),
        "semantic_repair_runtime_plan":load_json(p/"semantic_repair_runtime_plan.json"),
        "c3_repaired_parent_snapshot":load_json(p/"c3_repaired_parent_snapshot.json"),
        "c3_repair_application":load_json(p/"c3_repair_application.json"),
        "semantic_repair_packet":load_json(p/"semantic_repair_packet.json"),
        "semantic_lineage_closure":load_json(p/"semantic_lineage_closure.json"),
        "semantic_lineage_package":load_json(p/"semantic_lineage_package.json"),
        "post_repair_watch_contract":load_json(p/"post_repair_watch_contract.json"),
        "lineage_completeness_gate":load_json(p/"lineage_completeness_gate.json"),
        "bounded_arena_config":load_json(p/"r7_bounded_arena_config.json"),
        "arm_manifests":load_jsonl(p/"arm_manifests.jsonl"),
        "execution_rows":load_jsonl(p/"execution_rows.jsonl"),
    }
    plan=bundle["plan"]
    _require(plan["schema"]=="RB-V5.4-R7-DUAL-CASE-PLAN-v0.1","r7_v54_case_plan_schema_invalid")
    _require(plan["plan_hash"]==_hash_without(plan,"plan_hash"),"r7_v54_case_plan_hash_mismatch")
    _require(plan["branch_count"]==2 and plan["new_provider_branch_count"]==2,"r7_v54_case_branch_count_invalid")
    _require(plan["canonical_replicate_count"]==1,"r7_v54_replicate_invalid")
    _require(plan["n0_reference_rerun_count"]==0 and plan["r5_i_reference_rerun_count"]==0,"r7_v54_reference_rerun_forbidden")
    _require(plan["real_subject_execution_authorized"] is False,"r7_v54_prepared_plan_self_authorized")
    _require(plan["semantic_cpr_status"]=="NOT_ADJUDICATED","r7_v54_cpr_boundary_changed")
    _require(bundle["lineage_completeness_gate"]["status"]=="COMPLETE_FOR_AUTHORIZED_REPAIR","r7_v54_lineage_gate_not_complete")
    _require(bundle["semantic_repair_packet"]["repair_authorization_status"]=="READY_FOR_SEPARATE_AUTHORIZATION","r7_v54_packet_not_ready")
    _require(len(bundle["execution_rows"])==len(bundle["arm_manifests"])==2,"r7_v54_bundle_geometry_invalid")
    _require({x["canonical_arm_id"] for x in bundle["execution_rows"]}==set(ARM_MAP.values()),"r7_v54_arm_set_invalid")
    return bundle


def _validate_bindings(bundle,execution_code_sha,provider_name,model_config_path):
    p=bundle["plan"]
    _require(p["plan_code_sha"]==execution_code_sha,"r7_v54_execution_code_sha_mismatch:"+p["case_id"])
    mi=p["source_model_identity"]
    ci=p["source_config_identity"]
    model_config=load_json(model_config_path)
    _require(model_config["provider"]==provider_name==mi["provider"],"r7_v54_provider_mismatch:"+p["case_id"])
    _require(sha256_file(model_config_path)==mi["model_config_hash"],"r7_v54_model_hash_mismatch:"+p["case_id"])
    arena_path=ci["arena_config_path"]
    _require(sha256_file(arena_path)==ci["arena_config_hash"],"r7_v54_arena_hash_mismatch:"+p["case_id"])
    domain_path=Path("arena/domains")/(ci["domain_id"]+".json")
    _require(domain_path.exists(),"r7_v54_domain_missing:"+p["case_id"])
    _require(sha256_file(domain_path)==ci["domain_hash"],"r7_v54_domain_hash_mismatch:"+p["case_id"])
    domain=load_json(domain_path)
    _require(stable_hash(domain["task"])==ci["task_hash"],"r7_v54_task_hash_mismatch:"+p["case_id"])
    _require(stable_hash(domain["agents"])==ci["agent_pool_hash"],"r7_v54_agent_pool_hash_mismatch:"+p["case_id"])
    _require(bundle["semantic_repair_runtime_plan"]["plan_hash"]==p["semantic_repair_runtime_plan_hash"],"r7_v54_repair_plan_hash_mismatch:"+p["case_id"])
    _require(bundle["c3_repair_application"]["repair_application_hash"]==p["r7_s_repair_application_hash"],"r7_v54_repair_application_hash_mismatch:"+p["case_id"])
    _require(bundle["c3_repaired_parent_snapshot"]["state_hash"]==p["r7_s_repaired_parent_state_hash"],"r7_v54_repaired_parent_hash_mismatch:"+p["case_id"])
    _require(bundle["c2_persistent_field_envelope"]["envelope_hash"]==p["r7_p_persistent_field_envelope_hash"],"r7_v54_persistent_hash_mismatch:"+p["case_id"])
    _require(int(bundle["bounded_arena_config"]["max_turns"])==int(p["matched_horizon"]["absolute_turn_cap"]),"r7_v54_turn_cap_mismatch:"+p["case_id"])
    return {"model_config":model_config,"domain":domain}


def _canonicalize_case(raw_dir,plan):
    traces_path=Path(raw_dir)/"traces.jsonl"
    traces=load_jsonl(traces_path)
    _require(len(traces)==2,"r7_v54_expected_two_traces:"+plan["case_id"])
    for trace in traces:
        cond=trace.get("r7_condition") or {}
        legacy=cond.get("arm_id")
        _require(legacy in ARM_MAP,"r7_v54_unexpected_legacy_arm:"+str(legacy))
        cond["legacy_arm_id"]=legacy
        cond["canonical_arm_id"]=ARM_MAP[legacy]
        cond["execution_scope"]="V5_4_CANONICAL_DUAL_INTERVENTION"
        trace["r7_condition"]=cond
        trace["r7_canonical_dual"]=True
        trace["r7_case_id"]=plan["case_id"]
    write_jsonl(traces_path,traces)
    summary=load_json(Path(raw_dir)/"run_summary.json")
    summary["schema"]="RB-V5.4-R7-DUAL-CASE-REAL-RUN-v0.1"
    summary["case_id"]=plan["case_id"]
    summary["execution_scope"]="V5_4_CANONICAL_DUAL_INTERVENTION"
    summary["canonical_arm_ids"]=plan["canonical_arm_ids"]
    summary["canonical_replicate_count"]=1
    summary["n0_rerun"]=False
    summary["r5_i_rerun"]=False
    summary["branch_count"]=2
    summary["new_provider_branch_count"]=2
    summary["problematic_bias_status"]="NOT_ESTABLISHED"
    summary["r5_unique_causal_attribution"]="NOT_ESTABLISHED"
    summary["semantic_cpr_status"]="NOT_ADJUDICATED"
    summary["summary_hash"]=stable_hash({k:v for k,v in summary.items() if k!="summary_hash"})
    (Path(raw_dir)/"run_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--plan-root",required=True)
    ap.add_argument("--outdir")
    ap.add_argument("--model-config",required=True)
    ap.add_argument("--provider",required=True)
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
        raise SystemExit("r7_v54_preflight_and_real_mutually_exclusive")
    root=Path(args.plan_root)
    batch=load_json(root/"batch_plan.json")
    _require(batch["schema"]=="RB-V5.4-R7-DUAL-FOUR-CANDIDATE-BATCH-PLAN-v0.1","r7_v54_batch_plan_schema_invalid")
    _require(batch["batch_plan_hash"]==_hash_without(batch,"batch_plan_hash"),"r7_v54_batch_plan_hash_mismatch")
    _require(batch["case_count"]==4 and batch["branch_count"]==8,"r7_v54_batch_geometry_invalid")
    _require(batch["n0_rerun_count"]==0 and batch["r5_i_rerun_count"]==0,"r7_v54_batch_reference_rerun_forbidden")
    _require(batch["plan_code_sha"]==args.execution_code_sha,"r7_v54_batch_code_sha_mismatch")

    validate_symmetric_limits(
        row_count=8,
        per_branch_max_calls=args.per_branch_max_calls,
        per_branch_spending_ceiling=args.per_branch_spending_ceiling,
        global_spending_ceiling=args.global_spending_ceiling,
    )

    case_bundles=[]
    for row in batch["case_rows"]:
        bundle=_load_case_bundle(root/"cases"/row["case_id"])
        bindings=_validate_bindings(bundle,args.execution_code_sha,args.provider,args.model_config)
        case_bundles.append((row["case_id"],bundle,bindings))

    if args.preflight_only:
        print("V5_4_R7_DUAL_PREFLIGHT=PASS")
        print("CASE_COUNT=4")
        print("BRANCH_COUNT=8")
        print("N0_RERUN=NO")
        print("R5_I_RERUN=NO")
        print("PAID_API_CALLED=NO")
        return

    if not args.execute_real_api or args.authorization_phrase!=AUTH_PHRASE:
        raise SystemExit("Refusing provider calls: exact V5.4 canonical R7 dual authorization required.")
    if not args.outdir:
        raise SystemExit("r7_v54_outdir_required")
    _credential_check(case_bundles[0][2]["model_config"])

    out=Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_v54_r7_output")
    out.mkdir(parents=True)
    batch_cases=[]
    total_spend=0.0
    for case_id,bundle,bindings in case_bundles:
        upstream=provider_from_config(bindings["model_config"])
        case_raw=out/"cases"/case_id/"raw"
        summary=execute_real_batch(
            bundle=bundle,
            bindings=bindings,
            upstream=upstream,
            outdir=case_raw,
            per_branch_max_calls=args.per_branch_max_calls,
            per_branch_spending_ceiling=args.per_branch_spending_ceiling,
            global_spending_ceiling=args.per_branch_spending_ceiling*2,
            currency=args.currency,
            execution_code_sha=args.execution_code_sha,
            only_arm=None,
        )
        summary=_canonicalize_case(case_raw,bundle["plan"])
        total_spend+=float(summary["estimated_total_spend"])
        batch_cases.append({
            "case_id":case_id,
            "case_plan_hash":bundle["plan"]["plan_hash"],
            "run_summary_hash":summary["summary_hash"],
            "trace_count":summary["trace_count"],
            "run_complete_count":summary["run_complete_count"],
            "censored_or_nonrealized_count":summary["censored_or_nonrealized_count"],
            "failed_count":summary["failed_count"],
            "estimated_spend":summary["estimated_total_spend"],
        })

    _require(total_spend<=args.global_spending_ceiling+1e-12,"r7_v54_global_spend_exceeded")
    batch_summary={
        "schema":"RB-V5.4-R7-DUAL-FOUR-CANDIDATE-REAL-RUN-v0.1",
        "batch_plan_hash":batch["batch_plan_hash"],
        "execution_code_sha":args.execution_code_sha,
        "case_count":4,
        "branch_count":8,
        "trace_count":sum(x["trace_count"] for x in batch_cases),
        "run_complete_count":sum(x["run_complete_count"] for x in batch_cases),
        "censored_or_nonrealized_count":sum(x["censored_or_nonrealized_count"] for x in batch_cases),
        "failed_count":sum(x["failed_count"] for x in batch_cases),
        "canonical_replicate_count":1,
        "canonical_arm_ids":["R7_P_PERSISTENT_SEMANTIC","R7_S_STRUCTURED_LINEAGE_REPAIR"],
        "n0_rerun_count":0,
        "r5_i_rerun_count":0,
        "estimated_total_spend":total_spend,
        "currency":args.currency,
        "global_spending_ceiling":args.global_spending_ceiling,
        "cases":batch_cases,
        "automatic_paid_evaluator":False,
        "problematic_bias_status":"NOT_ESTABLISHED",
        "r5_unique_causal_attribution":"NOT_ESTABLISHED",
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "interpretation_boundary":"Raw R7-P/R7-S process evidence only. Structural/semantic interpretation is a later frozen-evidence step; no branch is rerun merely to reproduce a stochastic realization.",
    }
    batch_summary["summary_hash"]=stable_hash(batch_summary)
    (out/"batch_run_summary.json").write_text(json.dumps(batch_summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_4_R7_DUAL_COMPLETE")
    print("CASE_COUNT=4")
    print("BRANCH_COUNT=8")
    print("TRACE_COUNT="+str(batch_summary["trace_count"]))
    print("RUN_COMPLETE_COUNT="+str(batch_summary["run_complete_count"]))
    print("CENSORED_OR_NONREALIZED_COUNT="+str(batch_summary["censored_or_nonrealized_count"]))
    print("FAILED_COUNT="+str(batch_summary["failed_count"]))
    print("N0_RERUN=NO")
    print("R5_I_RERUN=NO")
    print("ESTIMATED_TOTAL_SPEND="+str(batch_summary["estimated_total_spend"]))
    print("SUMMARY_HASH="+batch_summary["summary_hash"])


if __name__=="__main__":
    main()
