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
    raw=Path(args.raw_dir); plan=Path(args.plan_dir)
    traces=load_jsonl(raw/"traces.jsonl")
    summary=load_json(raw/"summary.json")
    errors=load_json(raw/"errors.json")
    p=load_json(plan/"plan.json")
    if errors or summary.get("runner_error_count")!=0:
        raise ValueError("r5_canonical_freeze_requires_zero_runner_errors")
    if len(traces)!=p["case_count"] or len(traces)!=p["branch_count"]:
        raise ValueError("r5_canonical_freeze_requires_one_trace_per_case")
    if p.get("synthetic_control_branch_count")!=0 or p.get("canonical_replicate_count")!=1:
        raise ValueError("r5_canonical_geometry_invalid_at_freeze")
    batch={
        "schema":"RB-V5-R5-CANONICAL-EVIDENCE-BATCH-v0.1",
        "status":"FROZEN_BEFORE_PASSIVE_R6",
        "plan_hash":p["plan_hash"],
        "case_count":p["case_count"],
        "canonical_intervention_trace_count":len(traces),
        "synthetic_control_trace_count":0,
        "canonical_replicate_count":1,
        "natural_reference_rerun_count":0,
        "traces_sha256":sha256_file(raw/"traces.jsonl"),
        "summary_sha256":sha256_file(raw/"summary.json"),
        "authorization_record_sha256":sha256_file(raw/"authorization_record.json"),
        "plan_sha256":sha256_file(plan/"plan.json"),
        "case_bindings_sha256":sha256_file(plan/"case_bindings.jsonl"),
        "branch_execution_manifest_sha256":sha256_file(plan/"branch_execution_manifest.jsonl"),
        "branch_manifests_sha256":sha256_file(plan/"branch_manifests.jsonl"),
        "paid_evaluator_called":False,
        "r6_new_subject_experiment":False,
        "r7_repair_called":False,
        "r8_cpr_adjudication":False,
    }
    batch["journal_hashes"]=[{"name":p.name,"sha256":sha256_file(p)} for p in sorted((raw/"journals").glob("*.jsonl"))]
    batch["evidence_batch_hash"]=stable_hash(batch)
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(batch,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_R5_CANONICAL_EVIDENCE_FROZEN=YES")
    print("EVIDENCE_BATCH_HASH="+batch["evidence_batch_hash"])


if __name__=="__main__":
    main()
