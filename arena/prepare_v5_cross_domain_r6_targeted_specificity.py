#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .core import stable_hash
from .experimental_control import verify_state_snapshot
from .io_utils import load_json, load_jsonl, write_jsonl
from .one_shot_intervention import (
    CONTROL_CONDITION,
    INTERVENTION_CONDITION,
    make_branch_manifest_v3,
    verify_branch_manifest_v3,
    verify_one_shot_envelope,
)


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _hash_without(row, key):
    material=copy.deepcopy(row)
    material.pop(key,None)
    return stable_hash(material)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-r5-root",required=True)
    ap.add_argument("--config",required=True)
    ap.add_argument("--branch-code-sha",required=True)
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()

    cfg=load_json(args.config)
    _require(cfg.get("schema")=="RB-V5-CROSS-DOMAIN-R6-TARGETED-SPECIFICITY-PLAN-v0.1","r6_targeted_config_schema_invalid")
    root=Path(args.source_r5_root)
    plan=load_json(root/"prepared/r5_first_wave/plan.json")
    cases=load_jsonl(root/"prepared/r5_first_wave/case_bindings.jsonl")
    target_cfg=cfg["target_case"]
    matches=[c for c in cases if c["case_id"]==target_cfg["case_id"]]
    _require(len(matches)==1,"r6_target_case_not_unique")
    case=matches[0]
    for field in ("domain_id","source_case_hash","source_run_id","parent_state_hash","state_key"):
        _require(case.get(field)==target_cfg.get(field),f"r6_target_binding_mismatch:{field}")

    parent=load_json(root/"prepared/r5_first_wave"/case["parent_snapshot_path"])
    envelope=load_json(root/"prepared/r5_first_wave"/case["envelope_path"])
    verify_state_snapshot(parent)
    verify_one_shot_envelope(envelope)
    _require(parent["state_hash"]==target_cfg["parent_state_hash"],"r6_parent_hash_mismatch")
    _require(envelope["envelope_hash"]==target_cfg["envelope_hash"],"r6_envelope_hash_mismatch")
    _require(envelope["from_status"]=="fact" and envelope["to_status"]=="unconfirmed","r6_operator_status_mismatch")
    _require(parent["shared_state_metadata"][case["state_key"]]["status"]=="fact","r6_parent_target_not_fact")
    _require(parent.get("terminated") is False and bool(parent.get("queue")),"r6_parent_not_resumable")

    code_identity={
        "source_r5_execution_commit": plan["branch_execution_commit"],
        "branch_execution_commit": args.branch_code_sha,
    }
    model_identity=copy.deepcopy(case["model_identity"])
    config_identity=copy.deepcopy(case["config_identity"])

    rows=[]
    manifests=[]
    start=int(cfg["followup_geometry"]["new_pair_start_index"])
    end=int(cfg["followup_geometry"]["new_pair_end_index"])
    for replicate in range(start,end+1):
        order=(CONTROL_CONDITION,INTERVENTION_CONDITION) if replicate%2 else (INTERVENTION_CONDITION,CONTROL_CONDITION)
        pattern="CONTROL_FIRST" if replicate%2 else "INTERVENTION_FIRST"
        pair_id=f"{case['case_id']}:r6-specificity-pair:{replicate}"
        for execution_order,condition in enumerate(order,1):
            branch_id=f"{pair_id}:{condition.lower()}"
            bound=None if condition==CONTROL_CONDITION else envelope
            manifest=make_branch_manifest_v3(
                branch_id=branch_id,
                condition_id=condition,
                parent_trace_hash=case["source_trace_hash"],
                parent_snapshot=parent,
                envelope=bound,
                replicate_index=replicate,
                model_identity=model_identity,
                config_identity=config_identity,
                code_identity=code_identity,
            )
            verify_branch_manifest_v3(manifest,parent_snapshot=parent,envelope=bound)
            manifests.append(manifest)
            rows.append({
                "run_id":branch_id,
                "pair_id":pair_id,
                "replicate_index":replicate,
                "logical_seed":replicate,
                "execution_order":execution_order,
                "pair_order_pattern":pattern,
                "condition_id":condition,
                "branch_hash":manifest["branch_hash"],
                "case_id":case["case_id"],
                "domain_id":case["domain_id"],
                "source_run_id":case["source_run_id"],
                "source_case_hash":case["source_case_hash"],
                "parent_state_hash":parent["state_hash"],
                "branch_execution_code_commit_sha":args.branch_code_sha,
                "automatic_paid_evaluator":False,
                "r7_repair_authorized":False,
                "semantic_cpr_status":"NOT_ADJUDICATED",
            })
    _require(len(rows)==16 and len(manifests)==16,"r6_targeted_branch_geometry_invalid")

    out=Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r6_targeted_plan")
    out.mkdir(parents=True)
    (out/"parent_snapshot.json").write_text(json.dumps(parent,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"one_shot_envelope.json").write_text(json.dumps(envelope,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"case_binding.json").write_text(json.dumps(case,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_jsonl(out/"branch_execution_manifest.jsonl",rows)
    write_jsonl(out/"branch_manifests.jsonl",manifests)
    prepared={
        "schema":"RB-V5-CROSS-DOMAIN-R6-TARGETED-SPECIFICITY-EXECUTION-PLAN-v0.1",
        "status":"PREPARED_ONLY_NOT_SELF_AUTHORIZED",
        "source_r5_plan_hash":plan["plan_hash"],
        "source_r5_artifact_id":cfg["source_r5"]["artifact_id"],
        "target_case_id":case["case_id"],
        "parent_state_hash":parent["state_hash"],
        "envelope_hash":envelope["envelope_hash"],
        "branch_execution_commit":args.branch_code_sha,
        "new_pair_count":8,
        "new_branch_count":16,
        "replicate_indexes":list(range(start,end+1)),
        "automatic_paid_evaluator":False,
        "r7_repair_authorized":False,
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "authorization_status":"NOT_AUTHORIZED",
    }
    prepared["plan_hash"]=_hash_without(prepared,"plan_hash")
    (out/"plan.json").write_text(json.dumps(prepared,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_CROSS_DOMAIN_R6_TARGETED_SPECIFICITY_PREPARED=YES")
    print("NEW_PAIR_COUNT=8")
    print("NEW_BRANCH_COUNT=16")
    print("PAID_API_CALLED=NO")


if __name__=="__main__":
    main()
