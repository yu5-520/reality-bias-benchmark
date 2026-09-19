#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl
from .one_shot_intervention import (
    CONTROL_CONDITION,
    INTERVENTION_CONDITION,
    make_branch_manifest_v3,
    verify_branch_manifest_v3,
)
from .experimental_control import verify_state_snapshot
from .one_shot_intervention import verify_one_shot_envelope

PLAN_SCHEMA="RB-V5-CROSS-DOMAIN-R5-SECOND-WAVE-BALANCE-RECOVERY-EXECUTION-PLAN-v0.1"


def _require(ok,message):
    if not ok:
        raise ValueError(message)


def _hash_without(row,key):
    material=copy.deepcopy(row)
    material.pop(key,None)
    return stable_hash(material)


def _is_balance_failure(trace):
    calls=list(trace.get("model_calls") or [])
    if trace.get("termination_reason")!="model_call_failure":
        return False
    if len(calls)!=1:
        return False
    first=calls[0]
    if first.get("status")!="failed":
        return False
    if any(c.get("status")=="completed" for c in calls):
        return False
    err=str(first.get("error") or "")
    return "HTTP 402" in err and "Insufficient Balance" in err


def prepare(*,source_plan_dir:str,source_raw_dir:str,source_evidence_batch_path:str,recovery_config_path:str,branch_code_sha:str):
    cfg=load_json(recovery_config_path)
    _require(cfg.get("schema")=="RB-V5-CROSS-DOMAIN-R5-SECOND-WAVE-BALANCE-RECOVERY-PLAN-v0.1","recovery_config_schema_invalid")
    _require(cfg.get("status")=="FROZEN_PRE_EXECUTION_RECOVERY_PLAN","recovery_config_status_invalid")
    source_plan=Path(source_plan_dir)
    source_raw=Path(source_raw_dir)
    evidence=load_json(source_evidence_batch_path)
    _require(evidence.get("evidence_batch_hash")==cfg["source_r5_second_wave"]["evidence_batch_hash"],"recovery_source_evidence_hash_mismatch")
    _require(evidence.get("preserved_trace_count")==20,"recovery_source_trace_count_invalid")
    _require(evidence.get("case_count")==5,"recovery_source_case_count_invalid")

    old_plan=load_json(source_plan/"plan.json")
    old_cases=load_jsonl(source_plan/"case_bindings.jsonl")
    old_rows=load_jsonl(source_plan/"branch_execution_manifest.jsonl")
    old_manifests=load_jsonl(source_plan/"branch_manifests.jsonl")
    traces=load_jsonl(source_raw/"traces.jsonl")
    _require(old_plan.get("schema")=="RB-V5-CROSS-DOMAIN-R5-SECOND-WAVE-EXECUTION-PLAN-v0.1","recovery_source_plan_schema_invalid")
    _require(len(old_cases)==5 and len(old_rows)==20 and len(old_manifests)==20 and len(traces)==20,"recovery_source_geometry_invalid")

    trace_by_run={t["run_id"]:t for t in traces}
    row_by_run={r["run_id"]:r for r in old_rows}
    old_manifest_by_hash={m["branch_hash"]:m for m in old_manifests}
    case_by_id={c["case_id"]:c for c in old_cases}
    selected=[]
    for row in old_rows:
        t=trace_by_run.get(row["run_id"])
        _require(t is not None,"recovery_source_trace_missing:"+row["run_id"])
        if _is_balance_failure(t):
            selected.append((row,t))

    expected=cfg["expected_geometry"]
    _require(len(selected)==expected["branch_count"],f"recovery_selected_branch_count_invalid:{len(selected)}")
    selected_case_ids=sorted({r["case_id"] for r,_ in selected})
    _require(selected_case_ids==sorted(expected["case_ids"]),"recovery_selected_case_set_mismatch")
    _require(sorted({int(r["wave_id"]) for r,_ in selected})==sorted(expected["wave_ids"]),"recovery_selected_wave_set_mismatch")

    # Require complete matched-pair recovery: both conditions for both replicates in every selected case.
    for case_id in expected["case_ids"]:
        rows=[r for r,_ in selected if r["case_id"]==case_id]
        _require(len(rows)==4,"recovery_case_branch_count_invalid:"+case_id)
        combos={(int(r["replicate_index"]),r["condition_id"]) for r in rows}
        _require(combos=={
            (1,CONTROL_CONDITION),(1,INTERVENTION_CONDITION),
            (2,CONTROL_CONDITION),(2,INTERVENTION_CONDITION),
        },"recovery_case_condition_geometry_invalid:"+case_id)

    new_cases=[]
    case_payloads={}
    for case_id in expected["case_ids"]:
        source_case=copy.deepcopy(case_by_id[case_id])
        parent=load_json(source_plan/source_case["parent_snapshot_path"])
        envelope=load_json(source_plan/source_case["envelope_path"])
        verify_state_snapshot(parent); verify_one_shot_envelope(envelope)
        source_case_binding_hash=source_case["case_binding_hash"]
        source_case["source_second_wave_case_binding_hash"]=source_case_binding_hash
        source_case["code_identity"]=copy.deepcopy(source_case["code_identity"])
        source_case["code_identity"]["branch_execution_commit"]=branch_code_sha
        source_case["recovery_parent_reused_exactly"]=True
        source_case["recovery_reason"]="HTTP_402_INSUFFICIENT_BALANCE_BEFORE_FIRST_SCIENTIFIC_RESPONSE"
        source_case.pop("case_binding_hash",None)
        source_case["case_binding_hash"]=stable_hash(source_case)
        new_cases.append(source_case)
        case_payloads[case_id]=(parent,envelope)

    new_case_map={c["case_id"]:c for c in new_cases}
    recovery_rows=[]; recovery_manifests=[]
    suffix=cfg["recovery_policy"]["new_run_id_suffix"]
    for source_row,failed_trace in selected:
        case=new_case_map[source_row["case_id"]]
        parent,envelope=case_payloads[source_row["case_id"]]
        condition=source_row["condition_id"]
        bound=None if condition==CONTROL_CONDITION else envelope
        source_manifest=old_manifest_by_hash[source_row["branch_hash"]]
        new_run_id=source_row["run_id"]+":"+suffix
        new_branch_id=source_manifest["branch_id"]+":"+suffix
        bm=make_branch_manifest_v3(
            branch_id=new_branch_id,
            condition_id=condition,
            parent_trace_hash=case["source_trace_hash"],
            parent_snapshot=parent,
            envelope=bound,
            replicate_index=int(source_row["replicate_index"]),
            model_identity=case["model_identity"],
            config_identity=case["config_identity"],
            code_identity=case["code_identity"],
        )
        verify_branch_manifest_v3(bm,parent_snapshot=parent,envelope=bound)
        recovery_manifests.append(bm)
        first=(failed_trace.get("model_calls") or [None])[0] or {}
        row={
            "run_id":new_run_id,
            "branch_id":new_branch_id,
            "case_id":source_row["case_id"],
            "wave_id":source_row["wave_id"],
            "domain_id":source_row["domain_id"],
            "pair_id":source_row["pair_id"],
            "replicate_index":source_row["replicate_index"],
            "logical_seed":source_row["logical_seed"],
            "execution_order":source_row["execution_order"],
            "pair_order_pattern":source_row["pair_order_pattern"],
            "condition_id":condition,
            "branch_hash":bm["branch_hash"],
            "parent_state_hash":source_row["parent_state_hash"],
            "source_failed_run_id":source_row["run_id"],
            "source_failed_branch_hash":source_row["branch_hash"],
            "source_failed_trace_hash":stable_hash(failed_trace),
            "source_failure_termination_reason":failed_trace.get("termination_reason"),
            "source_failure_first_call_status":first.get("status"),
            "source_failure_class":"HTTP_402_INSUFFICIENT_BALANCE",
            "source_failure_completed_model_call_count":sum(c.get("status")=="completed" for c in failed_trace.get("model_calls") or []),
            "recovery_selection_scientific_outcome_aware":False,
            "branch_execution_code_commit_sha":branch_code_sha,
            "automatic_paid_evaluator":False,
            "r6_new_subject_experiment":False,
            "r7_repair_authorized":False,
            "r8_cpr_adjudication":False,
        }
        recovery_rows.append(row)

    new_cases.sort(key=lambda x:x["wave_id"])
    plan={
        "schema":PLAN_SCHEMA,
        "version":"0.1",
        "status":"PREPARED_RECOVERY_ONLY_NOT_SELF_AUTHORIZED",
        "source_r5_workflow_run_id":cfg["source_r5_second_wave"]["workflow_run_id"],
        "source_r5_artifact_id":cfg["source_r5_second_wave"]["artifact_id"],
        "source_r5_evidence_batch_hash":evidence["evidence_batch_hash"],
        "source_r5_plan_hash":old_plan["plan_hash"],
        "branch_execution_commit":branch_code_sha,
        "case_count":3,
        "branch_count":12,
        "wave_ids":[4,5,6],
        "replicate_pairs_per_case":2,
        "selection_rule":cfg["selection_rule"],
        "recovery_policy":cfg["recovery_policy"],
        "budget":cfg["budget"],
        "authorization_status":"NOT_AUTHORIZED",
        "automatic_paid_evaluator":False,
        "r6_new_subject_experiment":False,
        "r7_repair_authorized":False,
        "r8_cpr_adjudication":False,
        "case_binding_hashes":[c["case_binding_hash"] for c in new_cases],
        "source_failed_trace_hashes":[r["source_failed_trace_hash"] for r in recovery_rows],
        "branch_hashes":[m["branch_hash"] for m in recovery_manifests],
    }
    plan["plan_hash"]=_hash_without(plan,"plan_hash")
    return plan,new_cases,recovery_rows,recovery_manifests,case_payloads


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-plan-dir",required=True)
    ap.add_argument("--source-raw-dir",required=True)
    ap.add_argument("--source-evidence-batch",required=True)
    ap.add_argument("--recovery-config",required=True)
    ap.add_argument("--branch-code-sha",required=True)
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()
    plan,cases,rows,manifests,payloads=prepare(
        source_plan_dir=args.source_plan_dir,
        source_raw_dir=args.source_raw_dir,
        source_evidence_batch_path=args.source_evidence_batch,
        recovery_config_path=args.recovery_config,
        branch_code_sha=args.branch_code_sha,
    )
    out=Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r5_second_wave_recovery_plan")
    out.mkdir(parents=True)
    (out/"plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_jsonl(out/"case_bindings.jsonl",cases)
    write_jsonl(out/"branch_execution_manifest.jsonl",rows)
    write_jsonl(out/"branch_manifests.jsonl",manifests)
    for case in cases:
        d=out/"cases"/case["case_id"]; d.mkdir(parents=True)
        parent,envelope=payloads[case["case_id"]]
        (d/"parent_snapshot.json").write_text(json.dumps(parent,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        (d/"one_shot_envelope.json").write_text(json.dumps(envelope,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_R5_SECOND_WAVE_BALANCE_RECOVERY_PREPARED=YES")
    print("CASE_COUNT=3")
    print("BRANCH_COUNT=12")
    print("WAVES=4,5,6")
    print("PLAN_HASH="+plan["plan_hash"])


if __name__=="__main__":
    main()
