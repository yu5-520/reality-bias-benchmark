#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, sha256_file

ARM_SET={"R7_P_PERSISTENT_SEMANTIC","R7_S_STRUCTURED_LINEAGE_REPAIR"}


def _require(ok,message):
    if not ok:
        raise ValueError(message)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--plan-root",required=True)
    ap.add_argument("--raw-root",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    plan_root=Path(a.plan_root)
    raw_root=Path(a.raw_root)
    batch_plan=load_json(plan_root/"batch_plan.json")
    batch_run=load_json(raw_root/"batch_run_summary.json")
    _require(batch_plan["batch_plan_hash"]==batch_run["batch_plan_hash"],"r7_v54_freeze_batch_plan_hash_mismatch")
    _require(batch_plan["case_count"]==batch_run["case_count"]==4,"r7_v54_freeze_case_count_invalid")
    _require(batch_plan["branch_count"]==batch_run["branch_count"]==8,"r7_v54_freeze_branch_count_invalid")
    _require(batch_run["n0_rerun_count"]==0 and batch_run["r5_i_rerun_count"]==0,"r7_v54_freeze_reference_rerun_detected")

    cases=[]
    for row in batch_plan["case_rows"]:
        cid=row["case_id"]
        plan=load_json(plan_root/"cases"/cid/"r7_plan.json")
        raw=raw_root/"cases"/cid/"raw"
        summary=load_json(raw/"run_summary.json")
        traces=load_jsonl(raw/"traces.jsonl")
        _require(len(traces)==2,"r7_v54_freeze_case_trace_count_invalid:"+cid)
        arms={(t.get("r7_condition") or {}).get("canonical_arm_id") for t in traces}
        _require(arms==ARM_SET,"r7_v54_freeze_case_arm_set_invalid:"+cid)
        _require(summary["case_id"]==cid,"r7_v54_freeze_case_summary_id_mismatch:"+cid)
        _require(summary["branch_count"]==2,"r7_v54_freeze_case_branch_count_invalid:"+cid)
        _require(summary["n0_rerun"] is False and summary["r5_i_rerun"] is False,"r7_v54_freeze_case_reference_rerun:"+cid)
        cases.append({
            "case_id":cid,
            "case_plan_hash":plan["plan_hash"],
            "run_summary_hash":summary["summary_hash"],
            "traces_sha256":sha256_file(raw/"traces.jsonl"),
            "run_summary_sha256":sha256_file(raw/"run_summary.json"),
            "trace_count":2,
            "canonical_arm_ids":sorted(arms),
            "r7_persistent_field_envelope_hash":plan["r7_p_persistent_field_envelope_hash"],
            "r7_structured_repair_application_hash":plan["r7_s_repair_application_hash"],
            "lineage_gate_hash":plan["lineage_gate_hash"],
            "semantic_repair_packet_hash":plan["semantic_repair_packet_hash"],
        })

    batch={
        "schema":"RB-V5.4-R7-DUAL-FOUR-CANDIDATE-EVIDENCE-BATCH-v0.1",
        "date":"2026-09-19",
        "status":"FROZEN_BEFORE_STRUCTURAL_OR_SEMANTIC_INTERPRETATION",
        "evidence_role":"SUBJECT_PROCESS_EVIDENCE",
        "raw_evidence_frozen_before_derived_analysis":True,
        "batch_plan_hash":batch_plan["batch_plan_hash"],
        "batch_run_summary_hash":batch_run["summary_hash"],
        "batch_run_summary_sha256":sha256_file(raw_root/"batch_run_summary.json"),
        "case_count":4,
        "branch_count":8,
        "trace_count":8,
        "canonical_replicate_count":1,
        "canonical_arm_ids":["R7_P_PERSISTENT_SEMANTIC","R7_S_STRUCTURED_LINEAGE_REPAIR"],
        "n0_rerun_count":0,
        "r5_i_rerun_count":0,
        "cases":cases,
        "automatic_paid_evaluator":False,
        "problematic_bias_status":"NOT_ESTABLISHED",
        "r5_unique_causal_attribution":"NOT_ESTABLISHED",
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "frozen_evidence_mutated":False,
    }
    batch["evidence_batch_hash"]=stable_hash(batch)
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(batch,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_4_R7_DUAL_EVIDENCE_FROZEN=YES")
    print("CASE_COUNT=4")
    print("BRANCH_COUNT=8")
    print("EVIDENCE_BATCH_HASH="+batch["evidence_batch_hash"])
    print("CPR=NOT_ADJUDICATED")


if __name__=="__main__":
    main()
