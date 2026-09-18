#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from .core import stable_hash
from .io_utils import load_jsonl, load_json, write_jsonl
from .one_shot_intervention import CONTROL_CONDITION, INTERVENTION_CONDITION


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--traces",required=True)
    ap.add_argument("--evidence-batch",required=True)
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()
    traces=load_jsonl(args.traces)
    batch=load_json(args.evidence_batch)
    if len(traces)!=24 or batch.get("preserved_trace_count")!=24:
        raise ValueError("r5_local_response_requires_complete_frozen_evidence")
    by_pair=defaultdict(dict)
    for t in traces:
        by_pair[t["pair_id"]][t["condition_id"]]=t
    if len(by_pair)!=12:
        raise ValueError("r5_expected_12_pairs")
    rows=[]
    for pair_id,pair in sorted(by_pair.items()):
        if set(pair)!={CONTROL_CONDITION,INTERVENTION_CONDITION}:
            raise ValueError("r5_pair_incomplete:"+pair_id)
        c=pair[CONTROL_CONDITION]; i=pair[INTERVENTION_CONDITION]
        cc=(c.get("model_calls") or [None])[0]; ic=(i.get("model_calls") or [None])[0]
        if not cc or not ic:
            raise ValueError("r5_pair_missing_first_call:"+pair_id)
        key=(i.get("runtime_transform_records") or [{}])[0].get("state_key")
        c_status=((cc.get("runtime_snapshot") or {}).get("shared_state_metadata") or {}).get(key,{}).get("status")
        i_status=((ic.get("runtime_snapshot") or {}).get("shared_state_metadata") or {}).get(key,{}).get("status")
        if c_status!="fact" or i_status!="unconfirmed":
            raise ValueError("r5_prompt_delta_status_integrity_failure:"+pair_id)
        row={
            "schema":"RB-V5-CROSS-DOMAIN-R5-LOCAL-STRUCTURAL-RESPONSE-v0.1",
            "pair_id":pair_id,
            "case_id":c["case_id"],
            "domain_id":c["domain_id"],
            "wave_id":c["wave_id"],
            "source_run_id":c["source_run_id"],
            "source_case_hash":c["source_case_hash"],
            "replicate_index":c["replicate_index"],
            "first_actor_control":cc["agent_id"],
            "first_actor_intervention":ic["agent_id"],
            "control_target_status":c_status,
            "intervention_target_status":i_status,
            "first_raw_response_equal":stable_hash(cc.get("raw_content"))==stable_hash(ic.get("raw_content")),
            "first_parsed_envelope_equal":stable_hash(cc.get("parsed_envelope"))==stable_hash(ic.get("parsed_envelope")),
            "first_decision_summary_equal":cc.get("decision_summary")==ic.get("decision_summary"),
            "agent_path_equal":[x.get("agent_id") for x in c.get("model_calls") or []]==[x.get("agent_id") for x in i.get("model_calls") or []],
            "turn_count_control":c.get("turns"),
            "turn_count_intervention":i.get("turns"),
            "termination_reason_equal":c.get("termination_reason")==i.get("termination_reason"),
            "final_state_equal":stable_hash(c.get("final_state"))==stable_hash(i.get("final_state")),
            "semantic_interpretation":"DEFERRED_APPEND_ONLY",
            "r6_semantic_inertia_status":"NOT_ADJUDICATED",
            "semantic_cpr_status":"NOT_ADJUDICATED",
        }
        row["measurement_hash"]=stable_hash(row)
        rows.append(row)
    summary={
        "schema":"RB-V5-CROSS-DOMAIN-R5-LOCAL-STRUCTURAL-RESPONSE-SUMMARY-v0.1",
        "pair_count":len(rows),
        "case_count":len(set(r["case_id"] for r in rows)),
        "domain_pair_counts":dict(sorted(Counter(r["domain_id"] for r in rows).items())),
        "first_raw_response_changed_pairs":sum(not r["first_raw_response_equal"] for r in rows),
        "first_parsed_envelope_changed_pairs":sum(not r["first_parsed_envelope_equal"] for r in rows),
        "first_decision_summary_changed_pairs":sum(not r["first_decision_summary_equal"] for r in rows),
        "agent_path_changed_pairs":sum(not r["agent_path_equal"] for r in rows),
        "final_state_changed_pairs":sum(not r["final_state_equal"] for r in rows),
        "paid_evaluator_called":False,
        "semantic_interpretation":"DEFERRED_APPEND_ONLY",
        "r6_semantic_inertia_status":"NOT_ADJUDICATED",
        "semantic_cpr_status":"NOT_ADJUDICATED",
    }
    summary["summary_hash"]=stable_hash(summary)
    out=Path(args.outdir); out.mkdir(parents=True,exist_ok=True)
    write_jsonl(out/"paired_local_structural_response.jsonl",rows)
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_CROSS_DOMAIN_R5_LOCAL_STRUCTURAL_RESPONSE_DERIVED=YES")
    print("PAIR_COUNT="+str(summary["pair_count"]))
    print("FIRST_PARSED_ENVELOPE_CHANGED_PAIRS="+str(summary["first_parsed_envelope_changed_pairs"]))
    print("AGENT_PATH_CHANGED_PAIRS="+str(summary["agent_path_changed_pairs"]))
    print("FINAL_STATE_CHANGED_PAIRS="+str(summary["final_state_changed_pairs"]))
    print("SEMANTIC_INTERPRETATION=DEFERRED_APPEND_ONLY")


if __name__=="__main__":
    main()
