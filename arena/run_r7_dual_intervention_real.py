#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl
from .prepare_r7_dual_intervention_plan import verify_r7_dual_plan
from .run_r7_three_arm_real import (
    _credential_check,
    execute_real_batch,
    validate_execution_bindings,
    validate_symmetric_limits,
)
from .providers import provider_from_config

AUTH_PHRASE="CALL_REAL_R7_DUAL_INTERVENTION_API"


def _load_bundle(plan_dir):
    p=Path(plan_dir)
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
        "semantic_lineage_package":load_json(p/"semantic_lineage_package.json"),
        "post_repair_watch_contract":load_json(p/"post_repair_watch_contract.json"),
        "lineage_completeness_gate":load_json(p/"lineage_completeness_gate.json"),
        "bounded_arena_config":load_json(p/"r7_bounded_arena_config.json"),
        "arm_manifests":load_jsonl(p/"arm_manifests.jsonl"),
        "execution_rows":load_jsonl(p/"execution_rows.jsonl"),
    }
    verify_r7_dual_plan(bundle)
    return bundle


def _canonicalize_outputs(outdir:Path):
    traces_path=outdir/"traces.jsonl"
    traces=load_jsonl(traces_path)
    mapping={"C2_PERSISTENT_FIELD":"R7_P_PERSISTENT_SEMANTIC","C3_ALR":"R7_S_STRUCTURED_LINEAGE_REPAIR"}
    for trace in traces:
        cond=trace.get("r7_condition") or {}
        legacy=cond.get("arm_id")
        if legacy not in mapping:
            raise ValueError("r7_dual_unexpected_legacy_arm:"+str(legacy))
        cond["legacy_arm_id"]=legacy
        cond["canonical_arm_id"]=mapping[legacy]
        cond["execution_scope"]="CANONICAL_DUAL_INTERVENTION"
        trace["r7_condition"]=cond
        trace["r7_canonical_dual"]=True
    write_jsonl(traces_path,traces)

    summary=load_json(outdir/"run_summary.json")
    summary["schema"]="RB-R7-DUAL-INTERVENTION-REAL-RUN-v0.1"
    summary["execution_scope"]="CANONICAL_DUAL_INTERVENTION"
    summary["canonical_arm_ids"]=["R7_P_PERSISTENT_SEMANTIC","R7_S_STRUCTURED_LINEAGE_REPAIR"]
    summary["canonical_replicate_count"]=1
    summary["r5_reference_rerun"]=False
    summary["branch_count"]=2
    summary["new_provider_branch_count"]=2
    summary["summary_hash"]=stable_hash({k:v for k,v in summary.items() if k!="summary_hash"})
    (outdir/"run_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--plan-dir",required=True)
    ap.add_argument("--source-r5-plan-dir",required=True)
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
        raise SystemExit("r7_dual_preflight_and_real_mutually_exclusive")
    bundle=_load_bundle(args.plan_dir)
    validate_symmetric_limits(
        row_count=2,
        per_branch_max_calls=args.per_branch_max_calls,
        per_branch_spending_ceiling=args.per_branch_spending_ceiling,
        global_spending_ceiling=args.global_spending_ceiling,
    )
    bindings=validate_execution_bindings(
        bundle=bundle,
        source_r5_plan_dir=args.source_r5_plan_dir,
        model_config_path=args.model_config,
        provider_name=args.provider,
        execution_code_sha=args.execution_code_sha,
    )
    if bundle["plan"]["branch_count"]!=2 or bundle["plan"]["r5_c1_reference_execution_count"]!=0:
        raise ValueError("r7_dual_execution_geometry_invalid")

    if args.preflight_only:
        print("R7_DUAL_PREFLIGHT=PASS")
        print("BRANCH_COUNT=2")
        print("CANONICAL_REPLICATE_COUNT=1")
        print("R5_REFERENCE_RERUN=NO")
        print("PAID_API_CALLED=NO")
        return

    if not args.execute_real_api or args.authorization_phrase!=AUTH_PHRASE:
        raise SystemExit("Refusing provider calls: exact canonical R7 dual authorization required.")
    if not args.outdir:
        raise SystemExit("r7_dual_outdir_required")
    _credential_check(bindings["model_config"])
    upstream=provider_from_config(bindings["model_config"])
    out=Path(args.outdir)
    summary=execute_real_batch(
        bundle=bundle,bindings=bindings,upstream=upstream,outdir=out,
        per_branch_max_calls=args.per_branch_max_calls,
        per_branch_spending_ceiling=args.per_branch_spending_ceiling,
        global_spending_ceiling=args.global_spending_ceiling,
        currency=args.currency,
        execution_code_sha=args.execution_code_sha,
        only_arm=None,
    )
    summary=_canonicalize_outputs(out)
    if summary.get("branch_count")!=2:
        raise SystemExit("canonical R7 dual did not preserve two-branch geometry")
    print("R7_DUAL_COMPLETE")
    print("BRANCH_COUNT=2")
    print("R5_REFERENCE_RERUN=NO")
    print("ESTIMATED_TOTAL_SPEND="+str(summary["estimated_total_spend"]))


if __name__=="__main__":
    main()
