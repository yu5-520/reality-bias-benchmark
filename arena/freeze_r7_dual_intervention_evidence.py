#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, sha256_file


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--raw-dir",required=True)
    ap.add_argument("--plan-dir",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    raw=Path(args.raw_dir); plan_dir=Path(args.plan_dir)
    plan=load_json(plan_dir/"r7_plan.json")
    summary=load_json(raw/"run_summary.json")
    traces=load_jsonl(raw/"traces.jsonl")
    if plan.get("schema")!="RB-R7-DUAL-INTERVENTION-EXECUTION-PLAN-v0.1":
        raise ValueError("r7_dual_freeze_plan_schema_invalid")
    if len(traces)!=2 or summary.get("branch_count")!=2:
        raise ValueError("r7_dual_freeze_requires_exactly_two_traces")
    if plan.get("canonical_replicate_count")!=1 or plan.get("r5_c1_reference_execution_count")!=0:
        raise ValueError("r7_dual_freeze_geometry_invalid")
    arms={(t.get("r7_condition") or {}).get("canonical_arm_id") for t in traces}
    if arms!={"R7_P_PERSISTENT_SEMANTIC","R7_S_STRUCTURED_LINEAGE_REPAIR"}:
        raise ValueError("r7_dual_freeze_arm_set_invalid")
    batch={
        "schema":"RB-R7-DUAL-INTERVENTION-EVIDENCE-BATCH-v0.1",
        "status":"FROZEN_BEFORE_SEMANTIC_CLOSURE",
        "plan_hash":plan["plan_hash"],
        "case_id":plan["case_id"],
        "trace_count":2,
        "canonical_replicate_count":1,
        "r5_reference_rerun":False,
        "canonical_arm_ids":plan["canonical_arm_ids"],
        "traces_sha256":sha256_file(raw/"traces.jsonl"),
        "run_summary_sha256":sha256_file(raw/"run_summary.json"),
        "r7_persistent_field_envelope_hash":plan["r7_p_persistent_field_envelope_hash"],
        "r7_structured_repair_application_hash":plan["r7_s_repair_application_hash"],
        "automatic_paid_evaluator":False,
        "semantic_cpr_status":"NOT_ADJUDICATED",
    }
    batch["evidence_batch_hash"]=stable_hash(batch)
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(batch,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("R7_DUAL_EVIDENCE_FROZEN=YES")
    print("EVIDENCE_BATCH_HASH="+batch["evidence_batch_hash"])


if __name__=="__main__":
    main()
