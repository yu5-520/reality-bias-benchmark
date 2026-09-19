#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _call_ref(run_id: str, call: dict) -> str:
    return f"{run_id}:turn:{call['turn']}:actor:{call['agent_id']}"


def _event_ref(run_id: str, event: dict) -> str:
    return f"{run_id}:event:{event['event_index']}"


def _writes_for_call(trace: dict, call: dict) -> list[dict]:
    rows=[]
    for event in trace.get("events") or []:
        idx=event.get("event_index",-1)
        if not (call["event_index_start"] <= idx <= call["event_index_end"]):
            continue
        if event.get("action_type") not in ("write_state","revise_final_state"):
            continue
        action=event.get("action") or {}
        row={
            "ref":_event_ref(trace["run_id"],event),
            "event_index":idx,
            "turn":event.get("turn"),
            "actor":event.get("actor"),
            "action_type":event.get("action_type"),
            "state_key":action.get("key"),
            "status":action.get("status"),
            "value_hash":stable_hash(action.get("value")) if action.get("key") is not None else None,
            "patch_hash":stable_hash(action.get("patch")) if action.get("patch") is not None else None,
        }
        rows.append(row)
    return rows


def _call_digest(trace: dict, call: dict) -> dict:
    writes=_writes_for_call(trace,call)
    return {
        "call_ref":_call_ref(trace["run_id"],call),
        "turn":call["turn"],
        "actor":call["agent_id"],
        "status":call.get("status"),
        "decision_summary_hash":stable_hash(call.get("decision_summary")) if call.get("decision_summary") is not None else None,
        "decision_summary":call.get("decision_summary"),
        "runtime_snapshot_hash":call.get("runtime_snapshot_hash"),
        "write_refs":[x["ref"] for x in writes],
        "writes":writes,
    }


def _continuation_calls(trace: dict, source_turn: int) -> list[dict]:
    return [c for c in (trace.get("model_calls") or []) if int(c.get("turn",0)) > source_turn]


def _provider_failure_class(call: dict | None) -> str | None:
    if not call or call.get("status")!="failed":
        return None
    err=str(call.get("error") or "")
    if "HTTP 402" in err and "Insufficient Balance" in err:
        return "HTTP_402_INSUFFICIENT_BALANCE"
    return "OTHER_PROVIDER_FAILURE"


def _visible_carrier_refs(call: dict, carriers: list[dict]) -> list[str]:
    snap=call.get("runtime_snapshot") or {}
    state=snap.get("shared_state") or {}
    refs=[]
    for carrier in carriers:
        key=carrier.get("state_key")
        if key and key in state:
            refs.append(carrier["ref"])
    return refs


def derive(*,r5_traces_path:str,case_bindings_path:str,r5_evidence_path:str,natural_root:str):
    r5_traces=load_jsonl(r5_traces_path)
    cases=load_jsonl(case_bindings_path)
    evidence=load_json(r5_evidence_path)

    _require(evidence.get("schema")=="RB-V5-R5-CANONICAL-EVIDENCE-BATCH-v0.1","r6v03_source_evidence_schema_invalid")
    _require(evidence.get("status")=="FROZEN_BEFORE_PASSIVE_R6","r6v03_source_evidence_not_frozen")
    _require(evidence.get("case_count")==len(cases),"r6v03_case_count_mismatch")
    _require(evidence.get("canonical_intervention_trace_count")==len(r5_traces),"r6v03_r5_trace_count_mismatch")
    _require(evidence.get("synthetic_control_trace_count")==0,"r6v03_synthetic_control_forbidden")
    _require(evidence.get("natural_reference_rerun_count")==0,"r6v03_natural_rerun_forbidden")

    r5_by_case={t["case_id"]:t for t in r5_traces}
    _require(len(r5_by_case)==len(r5_traces),"r6v03_r5_case_collision")

    records=[]; review_packages=[]
    for case in sorted(cases,key=lambda r:(r["wave_id"],r["case_id"])):
        case_id=case["case_id"]
        _require(case_id in r5_by_case,f"r6v03_missing_r5_trace:{case_id}")
        r5=r5_by_case[case_id]
        wave=int(case["wave_id"])
        source_turn=int(case["source_turn"])
        natural_paths=list(Path(natural_root).rglob(f"wave-{wave}/raw/traces.jsonl"))
        _require(len(natural_paths)==1,f"r6v03_natural_trace_file_not_unique:{wave}")
        natural_rows=[x for x in load_jsonl(natural_paths[0]) if x.get("run_id")==case["source_run_id"]]
        _require(len(natural_rows)==1,f"r6v03_natural_trace_not_unique:{case['source_run_id']}")
        natural=natural_rows[0]
        _require(stable_hash(natural)==case["source_trace_hash"],f"r6v03_natural_trace_hash_mismatch:{case_id}")
        _require(r5.get("natural_reference_trace_hash")==case["source_trace_hash"],f"r6v03_r5_natural_binding_mismatch:{case_id}")
        _require(r5.get("synthetic_control") is False,f"r6v03_r5_synthetic_control_forbidden:{case_id}")
        _require(int(r5.get("canonical_replicate_index",0))==1,f"r6v03_r5_replicate_invalid:{case_id}")

        transforms=list(r5.get("runtime_transform_records") or [])
        _require(len(transforms)==1,f"r6v03_one_shot_transform_count_invalid:{case_id}")
        transform=transforms[0]
        _require(transform.get("from_status")=="fact" and transform.get("to_status")=="unconfirmed",f"r6v03_transform_delta_invalid:{case_id}")
        _require(transform.get("persistent_state_mutation") is False,f"r6v03_transform_persisted:{case_id}")
        _require(r5.get("experiment_origin_reinjection_count")==0,f"r6v03_reinjection_detected:{case_id}")

        n_calls=_continuation_calls(natural,source_turn)
        i_calls=list(r5.get("model_calls") or [])
        _require(bool(n_calls),f"r6v03_natural_continuation_missing:{case_id}")
        _require(bool(i_calls),f"r6v03_r5_continuation_missing:{case_id}")
        _require(n_calls[0]["agent_id"]==case["expected_first_resume_actor"],f"r6v03_natural_first_actor_mismatch:{case_id}")
        _require(i_calls[0]["agent_id"]==case["expected_first_resume_actor"],f"r6v03_r5_first_actor_mismatch:{case_id}")

        natural_first=_call_digest(natural,n_calls[0])
        r5_first=_call_digest(r5,i_calls[0])
        r5_carriers=[x for x in r5_first["writes"] if x["action_type"] in ("write_state","revise_final_state")]
        natural_carriers=[x for x in natural_first["writes"] if x["action_type"] in ("write_state","revise_final_state")]

        n_down=[]
        for call in n_calls[1:]:
            d=_call_digest(natural,call)
            d["visible_direct_carrier_refs"]=_visible_carrier_refs(call,natural_carriers)
            d["provider_failure_class"]=_provider_failure_class(call)
            n_down.append(d)

        i_down=[]
        for call in i_calls[1:]:
            d=_call_digest(r5,call)
            d["visible_direct_carrier_refs"]=_visible_carrier_refs(call,r5_carriers)
            d["provider_failure_class"]=_provider_failure_class(call)
            i_down.append(d)

        n_seq=[c["agent_id"] for c in n_calls if c.get("status")=="completed"]
        i_seq=[c["agent_id"] for c in i_calls if c.get("status")=="completed"]
        n_keys=[w["state_key"] for c in [natural_first,*n_down] for w in c["writes"] if w["state_key"]]
        i_keys=[w["state_key"] for c in [r5_first,*i_down] for w in c["writes"] if w["state_key"]]

        eligible=(
            natural_first["status"]=="completed"
            and r5_first["status"]=="completed"
            and any(c["status"]=="completed" for c in i_down)
        )
        record={
            "schema":"RB-V5.4-R6-CANONICAL-NATURAL-VS-R5-STRUCTURAL-OBSERVATION-v0.3",
            "case_id":case_id,
            "wave_id":wave,
            "domain_id":case["domain_id"],
            "source_run_id":case["source_run_id"],
            "source_case_hash":case["source_case_hash"],
            "source_audit_hash":case.get("source_audit_hash"),
            "target_state_key":case["state_key"],
            "source_turn":source_turn,
            "natural_reference":{
                "run_id":natural["run_id"],
                "trace_hash":case["source_trace_hash"],
                "continuation_call_count":len(n_calls),
                "termination_reason":natural.get("termination_reason"),
                "first_call":natural_first,
                "downstream_calls":n_down,
                "final_state_hash":stable_hash(natural.get("final_state")),
                "completed_actor_sequence":n_seq,
                "state_write_keys":n_keys,
            },
            "r5_intervention":{
                "run_id":r5["run_id"],
                "condition_id":r5.get("condition_id"),
                "one_shot_transform":transform,
                "continuation_call_count":len(i_calls),
                "termination_reason":r5.get("termination_reason"),
                "first_call":r5_first,
                "direct_turn_carrier_candidates":r5_carriers,
                "downstream_calls":i_down,
                "final_state_hash":stable_hash(r5.get("final_state")),
                "completed_actor_sequence":i_seq,
                "state_write_keys":i_keys,
            },
            "structural_delta":{
                "first_call_decision_summary_equal":natural_first["decision_summary_hash"]==r5_first["decision_summary_hash"],
                "first_call_write_key_set_equal":set(x["state_key"] for x in natural_carriers if x["state_key"])==set(x["state_key"] for x in r5_carriers if x["state_key"]),
                "completed_actor_sequence_equal":n_seq==i_seq,
                "state_write_key_sequence_equal":n_keys==i_keys,
                "final_state_equal":stable_hash(natural.get("final_state"))==stable_hash(r5.get("final_state")),
                "interpretation":"STRUCTURAL_INEQUALITY_ONLY_NOT_SEMANTIC_EFFECT",
            },
            "semantic_audit_eligibility":"ELIGIBLE_R6_CANONICAL_SEMANTIC_AUDIT" if eligible else "NOT_ELIGIBLE_INCOMPLETE_CONTINUATION",
            "system_inertia_status":"NOT_ADJUDICATED",
            "r7_status":"NOT_AUTHORIZED",
            "semantic_cpr_status":"NOT_ADJUDICATED",
        }
        record["structural_observation_hash"]=stable_hash(record)
        records.append(record)

        package={
            "schema":"RB-V5.4-R6-CANONICAL-SEMANTIC-REVIEW-PACKAGE-v0.3",
            "case_id":case_id,
            "wave_id":wave,
            "domain_id":case["domain_id"],
            "target_state_key":case["state_key"],
            "source_case_hash":case["source_case_hash"],
            "structural_observation_hash":record["structural_observation_hash"],
            "natural_reference":{
                "run_id":natural["run_id"],
                "first_call":natural_first,
                "downstream_calls":n_down,
                "final_state":natural.get("final_state"),
            },
            "r5_intervention":{
                "run_id":r5["run_id"],
                "one_shot_transform":transform,
                "first_call":r5_first,
                "downstream_calls":i_down,
                "final_state":r5.get("final_state"),
            },
            "semantic_questions":[
                "What semantic change, if any, occurs immediately after the one-shot authority downgrade?",
                "Does a new or materially changed carrier encode the challenged source relation?",
                "Do downstream Agents read/adopt that carrier in decision or action?",
                "Does the relation persist after the one-shot overlay disappears?",
                "Is persistence better explained by normal inheritance, independent evidence re-anchoring, boundary preservation, a pre-existing conservative gate, or new-carrier constraint persistence?",
                "Does the realized structure support a case-level System Inertia candidate without claiming problematic bias or unique R5 causality?"
            ],
        }
        package["review_package_hash"]=stable_hash(package)
        review_packages.append(package)

    summary={
        "schema":"RB-V5.4-R6-CANONICAL-NATURAL-VS-R5-STRUCTURAL-SUMMARY-v0.3",
        "date":"2026-09-19",
        "source_r5_evidence_batch_hash":evidence["evidence_batch_hash"],
        "case_count":len(records),
        "structural_record_count":len(records),
        "semantic_audit_eligible_case_count":sum(r["semantic_audit_eligibility"]=="ELIGIBLE_R6_CANONICAL_SEMANTIC_AUDIT" for r in records),
        "natural_reference_rerun_count":0,
        "synthetic_control_count":0,
        "new_provider_calls":0,
        "new_paid_evaluator_calls":0,
        "r7_authorized":False,
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "domain_case_counts":dict(sorted(Counter(r["domain_id"] for r in records).items())),
        "claim_boundary":"Structural deltas compare two realized paths (N0 and one R5-I continuation). Inequality of text, actor path, writes or final state is not by itself semantic effect or unique R5 causality."
    }
    summary["summary_hash"]=stable_hash(summary)
    return records,review_packages,summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--r5-traces",required=True)
    ap.add_argument("--case-bindings",required=True)
    ap.add_argument("--r5-evidence",required=True)
    ap.add_argument("--natural-root",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()
    records,packages,summary=derive(
        r5_traces_path=a.r5_traces,
        case_bindings_path=a.case_bindings,
        r5_evidence_path=a.r5_evidence,
        natural_root=a.natural_root,
    )
    out=Path(a.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r6_canonical_v03")
    out.mkdir(parents=True)
    write_jsonl(out/"case_structural_observations.jsonl",records)
    write_jsonl(out/"semantic_review_packages.jsonl",packages)
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_4_R6_CANONICAL_NATURAL_VS_R5=COMPLETE")
    print("CASE_COUNT="+str(summary["case_count"]))
    print("SEMANTIC_AUDIT_ELIGIBLE="+str(summary["semantic_audit_eligible_case_count"]))
    print("NEW_PROVIDER_CALLS=0")
    print("SUMMARY_HASH="+summary["summary_hash"])


if __name__=="__main__":
    main()
