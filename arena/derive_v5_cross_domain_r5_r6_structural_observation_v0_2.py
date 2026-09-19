#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl

INTERVENTION="ONE_SHOT_JUMP_INTERVENTION"
CONTROL="CONTROL_CONTINUATION"


def _require(ok,message):
    if not ok:
        raise ValueError(message)


def _error_class(call:dict|None):
    if not call:
        return None
    err=str(call.get("error") or "")
    if "HTTP 402" in err and "Insufficient Balance" in err:
        return "HTTP_402_INSUFFICIENT_BALANCE"
    if err:
        return "OTHER_PROVIDER_ERROR"
    return None


def _call_ref(trace,call):
    return f"{trace['run_id']}:turn:{call['turn']}:actor:{call['agent_id']}"


def _event_ref(trace,event):
    return f"{trace['run_id']}:event:{event['event_index']}"


def _carrier_candidates(trace,first):
    pre=((first.get("runtime_snapshot") or {}).get("shared_state") or {})
    out=[]
    for event in trace.get("events") or []:
        if not (first["event_index_start"]<=event.get("event_index",-1)<=first["event_index_end"]):
            continue
        if event.get("action_type") not in ("write_state","revise_final_state"):
            continue
        action=event.get("action") or {}
        key=action.get("key")
        preexisting=bool(key is not None and key in pre)
        row={
            "ref":_event_ref(trace,event),
            "event_index":event["event_index"],
            "turn":event["turn"],
            "actor":event["actor"],
            "action_type":event["action_type"],
            "state_key":key,
            "preexisting_state_key":preexisting,
            "preexisting_value_hash":stable_hash(pre.get(key)) if preexisting else None,
            "value_hash":stable_hash(action.get("value")) if key is not None else None,
            "value_changed_from_preexposure":(
                stable_hash(pre.get(key))!=stable_hash(action.get("value"))
                if preexisting and key is not None else None
            ),
            "patch_hash":stable_hash(action.get("patch")) if action.get("patch") is not None else None,
            "structural_role":"DIRECT_EXPOSURE_TURN_CARRIER_CANDIDATE",
        }
        row["carrier_hash"]=stable_hash(row)
        out.append(row)
    return out


def derive(*,traces_path,case_bindings_path,evidence_batch_path):
    traces=load_jsonl(traces_path)
    cases=load_jsonl(case_bindings_path)
    evidence_batch=load_json(evidence_batch_path)
    _require(len(traces)==evidence_batch["preserved_trace_count"],"r5r6_v02_trace_count_mismatch")
    _require(len(cases)==evidence_batch["case_count"],"r5r6_v02_case_count_mismatch")
    _require(evidence_batch.get("runner_error_count")==0,"r5r6_v02_source_runner_errors")
    case_ids={c["case_id"] for c in cases}
    interventions=[r for r in traces if r.get("condition_id")==INTERVENTION]
    _require(len(interventions)==2*len(cases),"r5r6_v02_intervention_geometry_invalid")
    controls={(r["pair_id"],r["replicate_index"]):r for r in traces if r.get("condition_id")==CONTROL}

    records=[]
    for trace in sorted(interventions,key=lambda x:(x["wave_id"],x["replicate_index"])):
        _require(trace["case_id"] in case_ids,"r5r6_v02_unknown_case")
        transforms=list(trace.get("runtime_transform_records") or [])
        _require(len(transforms)==1,"r5r6_v02_requires_one_transform_record")
        tr=transforms[0]
        _require(tr["from_status"]=="fact" and tr["to_status"]=="unconfirmed","r5r6_v02_operator_mismatch")
        _require(trace.get("direct_experiment_origin_exposure_count")==1,"r5r6_v02_direct_exposure_count_mismatch")
        _require(trace.get("experiment_origin_reinjection_count")==0,"r5r6_v02_reinjection_detected")
        _require(trace.get("persistent_experiment_origin_mutation") is False,"r5r6_v02_persistent_mutation_detected")

        calls=list(trace.get("model_calls") or [])
        first=calls[0] if calls else None
        control=controls.get((trace["pair_id"],trace["replicate_index"]))
        control_calls=list(control.get("model_calls") or []) if control else []
        record={
            "schema":"RB-V5-CROSS-DOMAIN-R5R6-STRUCTURAL-OBSERVATION-v0.2",
            "case_id":trace["case_id"],
            "wave_id":trace["wave_id"],
            "domain_id":trace["domain_id"],
            "source_run_id":trace["source_run_id"],
            "source_case_hash":trace["source_case_hash"],
            "r5_run_id":trace["run_id"],
            "replicate_index":trace["replicate_index"],
            "target_state_key":tr["state_key"],
            "authority_transition":{
                "from_status":"fact","to_status":"unconfirmed",
                "direct_exposure_count":1,
                "experiment_origin_reinjection_count":0,
                "persistent_experiment_origin_mutation":False,
            },
            "paired_control_quality":{
                "termination_reason":control.get("termination_reason") if control else None,
                "first_model_call_status":control_calls[0].get("status") if control_calls else None,
                "terminal_provider_failure_class":_error_class(control_calls[-1]) if control_calls else None,
            },
            "case_level_system_inertia_status":"NOT_ADJUDICATED",
            "r7_status":"NOT_AUTHORIZED",
            "semantic_cpr_status":"NOT_ADJUDICATED",
        }

        if not first or first.get("status")!="completed":
            record.update({
                "evidence_quality_status":"INCOMPLETE_FIRST_EXPOSURE_CALL_PROVIDER_FAILURE",
                "provider_failure_class":_error_class(first),
                "direct_exposure":{
                    "actor":tr["actor"],"turn":tr["turn"],
                    "call_ref":f"{trace['run_id']}:turn:{tr['turn']}:actor:{tr['actor']}",
                    "call_status":first.get("status") if first else "missing",
                },
                "direct_turn_carrier_candidates":[],
                "post_stimulus_call_count":0,
                "downstream_structural_observations":[],
                "semantic_audit_eligibility":"NOT_ELIGIBLE_INCOMPLETE_CONTINUATION",
            })
        else:
            carriers=_carrier_candidates(trace,first)
            downstream=[]
            for call in calls[1:]:
                snap=call.get("runtime_snapshot") or {}
                state=snap.get("shared_state") or {}
                meta=snap.get("shared_state_metadata") or {}
                visible=[c["ref"] for c in carriers if c.get("state_key") and c["state_key"] in state]
                writes=[]
                for event in trace.get("events") or []:
                    if call["event_index_start"]<=event.get("event_index",-1)<=call["event_index_end"] and event.get("action_type") in ("write_state","revise_final_state"):
                        writes.append(_event_ref(trace,event))
                downstream.append({
                    "call_ref":_call_ref(trace,call),
                    "turn":call["turn"],"actor":call["agent_id"],
                    "call_status":call.get("status"),
                    "provider_failure_class":_error_class(call),
                    "target_status_seen":(meta.get(tr["state_key"]) or {}).get("status"),
                    "visible_direct_carrier_refs":visible,
                    "downstream_write_refs":writes,
                    "decision_summary_hash":stable_hash(call.get("decision_summary")) if call.get("decision_summary") is not None else None,
                })
            eligible=bool(carriers) and any(x["call_status"]=="completed" for x in downstream)
            record.update({
                "evidence_quality_status":"COMPLETE_DIRECT_RESPONSE_WITH_CONTINUATION" if eligible else "DIRECT_RESPONSE_COMPLETE_BUT_R6_CONTINUATION_INSUFFICIENT",
                "provider_failure_class":None,
                "direct_exposure":{
                    "actor":first["agent_id"],"turn":first["turn"],
                    "call_ref":_call_ref(trace,first),"call_status":first["status"],
                    "decision_summary_hash":stable_hash(first.get("decision_summary")),
                },
                "direct_turn_carrier_candidates":carriers,
                "post_stimulus_call_count":len(downstream),
                "downstream_structural_observations":downstream,
                "semantic_audit_eligibility":"ELIGIBLE_R6_PASSIVE_SEMANTIC_AUDIT" if eligible else "NOT_ELIGIBLE_INSUFFICIENT_CONTINUATION",
            })
        record["structural_observation_hash"]=stable_hash(record)
        records.append(record)

    by_case=defaultdict(list)
    for r in records:
        by_case[r["case_id"]].append(r)
    case_summaries=[]
    for case_id in sorted(by_case,key=lambda cid:min(x["wave_id"] for x in by_case[cid])):
        rows=sorted(by_case[case_id],key=lambda x:x["replicate_index"])
        eligible=sum(x["semantic_audit_eligibility"]=="ELIGIBLE_R6_PASSIVE_SEMANTIC_AUDIT" for x in rows)
        incomplete=sum(x["evidence_quality_status"].startswith("INCOMPLETE") for x in rows)
        item={
            "schema":"RB-V5-CROSS-DOMAIN-R5R6-STRUCTURAL-CASE-SUMMARY-v0.2",
            "case_id":case_id,"wave_id":rows[0]["wave_id"],"domain_id":rows[0]["domain_id"],
            "intervention_branch_count":len(rows),
            "semantic_audit_eligible_branch_count":eligible,
            "incomplete_branch_count":incomplete,
            "case_evidence_quality_status":(
                "COMPLETE_FOR_R6_SEMANTIC_AUDIT" if eligible==len(rows)
                else "INCOMPLETE_R5_CONTINUATION_PROVIDER_FAILURE"
            ),
            "branch_observation_hashes":[x["structural_observation_hash"] for x in rows],
            "r7_status":"NOT_AUTHORIZED",
        }
        item["case_summary_hash"]=stable_hash(item)
        case_summaries.append(item)

    summary={
        "schema":"RB-V5-CROSS-DOMAIN-R5R6-STRUCTURAL-OBSERVATION-SUMMARY-v0.2",
        "source_r5_evidence_batch_hash":evidence_batch["evidence_batch_hash"],
        "source_trace_count":len(traces),
        "intervention_trace_count":len(records),
        "case_count":len(case_summaries),
        "domain_case_counts":dict(sorted(Counter(x["domain_id"] for x in case_summaries).items())),
        "semantic_audit_eligible_intervention_count":sum(x["semantic_audit_eligibility"]=="ELIGIBLE_R6_PASSIVE_SEMANTIC_AUDIT" for x in records),
        "incomplete_first_exposure_provider_failure_count":sum(x["evidence_quality_status"]=="INCOMPLETE_FIRST_EXPOSURE_CALL_PROVIDER_FAILURE" for x in records),
        "semantic_audit_eligible_case_count":sum(x["case_evidence_quality_status"]=="COMPLETE_FOR_R6_SEMANTIC_AUDIT" for x in case_summaries),
        "incomplete_case_count":sum(x["case_evidence_quality_status"]!="COMPLETE_FOR_R6_SEMANTIC_AUDIT" for x in case_summaries),
        "provider_failure_class_counts":{
            "HTTP_402_INSUFFICIENT_BALANCE":sum(x.get("provider_failure_class")=="HTTP_402_INSUFFICIENT_BALANCE" for x in records)
        },
        "new_provider_calls":0,
        "new_paid_evaluator_calls":0,
        "r7_authorized":False,
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "claim_boundary":"Provider-failed branches are incomplete evidence, not negative semantic findings. Only intervention continuations with a completed direct response and downstream continuation are eligible for semantic audit.",
    }
    summary["summary_hash"]=stable_hash(summary)
    return records,case_summaries,summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--traces",required=True)
    ap.add_argument("--case-bindings",required=True)
    ap.add_argument("--evidence-batch",required=True)
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()
    records,cases,summary=derive(
        traces_path=args.traces,case_bindings_path=args.case_bindings,evidence_batch_path=args.evidence_batch
    )
    out=Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r5r6_structural_observation_v02")
    out.mkdir(parents=True)
    write_jsonl(out/"branch_structural_observations.jsonl",records)
    write_jsonl(out/"case_structural_summaries.jsonl",cases)
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_CROSS_DOMAIN_R5R6_STRUCTURAL_OBSERVATION_V02=COMPLETE")
    print("INTERVENTION_TRACE_COUNT="+str(summary["intervention_trace_count"]))
    print("SEMANTIC_AUDIT_ELIGIBLE="+str(summary["semantic_audit_eligible_intervention_count"]))
    print("INCOMPLETE_PROVIDER_FAILURE="+str(summary["incomplete_first_exposure_provider_failure_count"]))
    print("NEW_PROVIDER_CALLS=0")
    print("SUMMARY_HASH="+summary["summary_hash"])


if __name__=="__main__":
    main()
