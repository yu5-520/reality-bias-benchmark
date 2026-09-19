#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, sha256_file


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--raw-dir",required=True); ap.add_argument("--plan-dir",required=True); ap.add_argument("--out",required=True)
    args=ap.parse_args()
    raw=Path(args.raw_dir); plan=Path(args.plan_dir)
    traces=load_jsonl(raw/"traces.jsonl"); summary=load_json(raw/"summary.json"); errors=load_json(raw/"errors.json")
    if len(traces)!=20 or errors or summary.get("runner_error_count")!=0:
        raise ValueError("r5_second_freeze_requires_complete_20_branch_collection")
    batch={
        "schema":"RB-V5-CROSS-DOMAIN-R5-SECOND-WAVE-EVIDENCE-BATCH-v0.1",
        "status":"FROZEN_BEFORE_R6_PASSIVE_DERIVATION",
        "plan_hash":load_json(plan/"plan.json")["plan_hash"],
        "traces_sha256":sha256_file(raw/"traces.jsonl"),"summary_sha256":sha256_file(raw/"summary.json"),
        "authorization_record_sha256":sha256_file(raw/"authorization_record.json"),
        "prepared_plan_sha256":sha256_file(plan/"plan.json"),"case_bindings_sha256":sha256_file(plan/"case_bindings.jsonl"),
        "branch_execution_manifest_sha256":sha256_file(plan/"branch_execution_manifest.jsonl"),
        "branch_manifests_sha256":sha256_file(plan/"branch_manifests.jsonl"),
        "preserved_trace_count":20,"case_count":5,"pair_count":10,"runner_error_count":0,
        "paid_evaluator_called":False,"r6_new_subject_experiment":False,"r7_repair_called":False,"r8_cpr_adjudication":False,
    }
    batch["journal_hashes"]=[{"name":p.name,"sha256":sha256_file(p)} for p in sorted((raw/"journals").glob("*.jsonl"))]
    batch["evidence_batch_hash"]=stable_hash(batch)
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(batch,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_CROSS_DOMAIN_R5_SECOND_RAW_EVIDENCE_FROZEN=YES")
    print("EVIDENCE_BATCH_HASH="+batch["evidence_batch_hash"])


if __name__=="__main__":
    main()
