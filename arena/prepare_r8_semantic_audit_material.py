#!/usr/bin/env python3
from __future__ import annotations

import argparse, json
from pathlib import Path
from .core import stable_hash
from .io_utils import load_jsonl, write_jsonl

def prepare(*, traces_path, measurements_path):
    traces={r["run_id"]:r for r in load_jsonl(traces_path)}
    measurements=load_jsonl(measurements_path)
    rows=[]
    for m in measurements:
        run_id=m["run_id"]
        t=traces[run_id]
        row={
            "schema":"RB-R8-SEMANTIC-AUDIT-CASE-v0.1",
            "run_id":run_id,
            "triad_id":m.get("triad_id"),
            "arm_id":m.get("arm_id"),
            "source_trace_hash":stable_hash(t),
            "source_measurement_hash":m.get("measurement_hash"),
            "full_lineage_observation":m.get("full_lineage_observation"),
            "post_repair_watch_result":(t.get("r7_semantic_repair_verification") or {}).get("post_repair_watch_result"),
            "candidate_event_records":[],
            "audit_questions":[
                "Are apparent multi-Agent supports independent evidence or descendants of one root lineage?",
                "Does reasoning/scope expansion seek new evidence or primarily preserve coherence?",
                "Does authority remain uncertain at the source while operational certainty accumulates in descendants?",
                "Are candidate C/P/R events repeated, overlapping or transition-linked?"
            ],
            "semantic_cpr_status":"NOT_ADJUDICATED"
        }
        row["case_hash"]=stable_hash(row)
        rows.append(row)
    manifest={"schema":"RB-R8-SEMANTIC-AUDIT-MANIFEST-v0.1","case_count":len(rows),"paid_evaluator_called":False,"subject_rerun_required":False,"semantic_cpr_status":"NOT_ADJUDICATED","case_hashes":[r["case_hash"] for r in rows]}
    manifest["manifest_hash"]=stable_hash(manifest)
    return rows,manifest

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--traces",required=True); ap.add_argument("--measurements",required=True); ap.add_argument("--outdir",required=True)
    a=ap.parse_args(); out=Path(a.outdir)
    if out.exists(): raise ValueError("refusing_to_overwrite_r8_audit_material_dir")
    out.mkdir(parents=True)
    rows,manifest=prepare(traces_path=a.traces,measurements_path=a.measurements)
    write_jsonl(out/"r8_semantic_audit_cases.jsonl",rows)
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("R8_AUDIT_CASES="+str(len(rows))); print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED"); print("PAID_EVALUATOR_CALLED=NO")
if __name__=="__main__": main()
