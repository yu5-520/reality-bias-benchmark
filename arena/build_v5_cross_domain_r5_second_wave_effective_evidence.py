#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl, sha256_file

SCHEMA="RB-V5-CROSS-DOMAIN-R5-SECOND-WAVE-EFFECTIVE-EVIDENCE-v0.1"


def _require(ok,message):
    if not ok:
        raise ValueError(message)


def _is_first_call_402(trace):
    calls=list(trace.get("model_calls") or [])
    if trace.get("termination_reason")!="model_call_failure" or len(calls)!=1:
        return False
    c=calls[0]
    err=str(c.get("error") or "")
    return c.get("status")=="failed" and "HTTP 402" in err and "Insufficient Balance" in err and not any(x.get("status")=="completed" for x in calls)


def _late_failure_quality(trace):
    calls=list(trace.get("model_calls") or [])
    failed=[c for c in calls if c.get("status")=="failed"]
    if not failed:
        return "COMPLETE_OR_BUDGET_CENSORED_WITHOUT_PROVIDER_FAILURE"
    completed=sum(c.get("status")=="completed" for c in calls)
    err=str(failed[-1].get("error") or "")
    if completed>0 and "HTTP 402" in err and "Insufficient Balance" in err:
        return "LATE_HTTP_402_AFTER_SCIENTIFIC_RESPONSES"
    return "OTHER_PROVIDER_FAILURE_AFTER_START"


def build(*,original_raw_dir,recovery_raw_dir,original_plan_dir,original_evidence_path,recovery_evidence_path,outdir):
    orig_raw=Path(original_raw_dir); rec_raw=Path(recovery_raw_dir); orig_plan=Path(original_plan_dir)
    orig=load_jsonl(orig_raw/"traces.jsonl")
    rec=load_jsonl(rec_raw/"traces.jsonl")
    cases=load_jsonl(orig_plan/"case_bindings.jsonl")
    orig_ev=load_json(original_evidence_path); rec_ev=load_json(recovery_evidence_path)

    _require(len(orig)==20,"effective_original_trace_count_invalid")
    _require(len(rec)==12,"effective_recovery_trace_count_invalid")
    _require(len(cases)==5,"effective_case_count_invalid")
    _require(orig_ev["evidence_batch_hash"]=="b01e11cb041be4d3d29bd94d93552ac0bfdd56fc67cd5b7b011e8f90bb46d676","effective_original_evidence_hash_mismatch")
    _require(rec_ev["evidence_batch_hash"]=="62f39fe00cd427066559558f52d1b2b18c163c7e76e9787190846797b21d6578","effective_recovery_evidence_hash_mismatch")

    orig_by_run={t["run_id"]:t for t in orig}
    _require(len(orig_by_run)==20,"effective_original_run_collision")
    failed_first=[t for t in orig if _is_first_call_402(t)]
    _require(len(failed_first)==12,"effective_original_first_call_402_count_invalid")
    _require(sorted({int(t["wave_id"]) for t in failed_first})==[4,5,6],"effective_original_402_wave_set_invalid")

    rec_by_source={t["source_failed_run_id"]:t for t in rec}
    _require(len(rec_by_source)==12,"effective_recovery_source_mapping_collision")
    _require(set(rec_by_source)=={t["run_id"] for t in failed_first},"effective_recovery_source_mapping_mismatch")

    effective=[]
    provenance=[]
    replaced=0
    for t in orig:
        if _is_first_call_402(t):
            rt=copy.deepcopy(rec_by_source[t["run_id"]])
            rt["effective_evidence_provenance"]={
                "effective_role":"RECOVERY_REPLACES_PRE_RESPONSE_PROVIDER_FAILURE_FOR_DERIVED_ANALYSIS_ONLY",
                "source_original_failed_run_id":t["run_id"],
                "source_original_failed_trace_hash":stable_hash(t),
                "recovery_run_id":rt["run_id"],
                "recovery_trace_hash":stable_hash(rec_by_source[t["run_id"]]),
                "original_failed_trace_preserved":True,
                "scientific_outcome_aware_selection":False,
            }
            effective.append(rt)
            provenance.append({
                "case_id":rt["case_id"],"wave_id":rt["wave_id"],"pair_id":rt["pair_id"],
                "replicate_index":rt["replicate_index"],"condition_id":rt["condition_id"],
                "effective_source":"RECOVERY",
                "original_run_id":t["run_id"],"original_trace_hash":stable_hash(t),
                "effective_run_id":rt["run_id"],"effective_trace_hash":stable_hash(rt),
                "original_quality":"FIRST_CALL_HTTP_402_ZERO_SCIENTIFIC_RESPONSE",
                "effective_quality":_late_failure_quality(rt),
            })
            replaced+=1
        else:
            ot=copy.deepcopy(t)
            ot["effective_evidence_provenance"]={
                "effective_role":"ORIGINAL_VALID_CONTINUATION",
                "source_original_run_id":t["run_id"],
                "source_original_trace_hash":stable_hash(t),
                "original_trace_preserved":True,
            }
            effective.append(ot)
            provenance.append({
                "case_id":ot["case_id"],"wave_id":ot["wave_id"],"pair_id":ot["pair_id"],
                "replicate_index":ot["replicate_index"],"condition_id":ot["condition_id"],
                "effective_source":"ORIGINAL",
                "original_run_id":t["run_id"],"original_trace_hash":stable_hash(t),
                "effective_run_id":ot["run_id"],"effective_trace_hash":stable_hash(ot),
                "original_quality":_late_failure_quality(t),
                "effective_quality":_late_failure_quality(t),
            })

    _require(replaced==12,"effective_replacement_count_invalid")
    _require(len(effective)==20,"effective_trace_count_invalid")
    effective.sort(key=lambda x:(int(x["wave_id"]),int(x["replicate_index"]),int(x["execution_order"])))
    provenance.sort(key=lambda x:(int(x["wave_id"]),int(x["replicate_index"]),x["condition_id"]))

    # Scientific intervention continuations must now all contain a completed direct response.
    interventions=[t for t in effective if t["condition_id"]=="ONE_SHOT_JUMP_INTERVENTION"]
    _require(len(interventions)==10,"effective_intervention_count_invalid")
    for t in interventions:
        calls=list(t.get("model_calls") or [])
        _require(bool(calls) and calls[0].get("status")=="completed","effective_intervention_first_call_not_completed:"+t["run_id"])

    out=Path(outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_effective_r5_second_wave")
    out.mkdir(parents=True)
    write_jsonl(out/"effective_traces.jsonl",effective)
    write_jsonl(out/"trace_provenance.jsonl",provenance)
    write_jsonl(out/"case_bindings.jsonl",cases)

    summary={
        "schema":SCHEMA,
        "status":"FROZEN_DERIVED_EFFECTIVE_EVIDENCE",
        "original_evidence_batch_hash":orig_ev["evidence_batch_hash"],
        "recovery_evidence_batch_hash":rec_ev["evidence_batch_hash"],
        "original_trace_count":20,
        "recovery_trace_count":12,
        "effective_trace_count":20,
        "effective_case_count":5,
        "effective_intervention_count":10,
        "original_trace_used_count":8,
        "recovery_trace_used_count":12,
        "original_first_call_402_trace_count":12,
        "original_first_call_402_traces_preserved":True,
        "original_evidence_overwritten":False,
        "wave3_control_rep2_quality":"LATE_HTTP_402_AFTER_SCIENTIFIC_RESPONSES",
        "wave3_control_rep2_recovered":False,
        "selection_scientific_outcome_aware":False,
        "r6_new_subject_experiment":False,
        "new_provider_calls":0,
        "new_paid_evaluator_calls":0,
        "r7_authorized":False,
        "semantic_cpr_status":"NOT_ADJUDICATED",
    }
    summary["summary_hash"]=stable_hash(summary)
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_R5_SECOND_WAVE_EFFECTIVE_EVIDENCE=FROZEN")
    print("EFFECTIVE_TRACE_COUNT=20")
    print("EFFECTIVE_INTERVENTION_COUNT=10")
    print("ORIGINAL_USED=8")
    print("RECOVERY_USED=12")
    print("SUMMARY_HASH="+summary["summary_hash"])


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--original-raw-dir",required=True)
    ap.add_argument("--recovery-raw-dir",required=True)
    ap.add_argument("--original-plan-dir",required=True)
    ap.add_argument("--original-evidence",required=True)
    ap.add_argument("--recovery-evidence",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()
    build(
        original_raw_dir=a.original_raw_dir,
        recovery_raw_dir=a.recovery_raw_dir,
        original_plan_dir=a.original_plan_dir,
        original_evidence_path=a.original_evidence,
        recovery_evidence_path=a.recovery_evidence,
        outdir=a.outdir,
    )
