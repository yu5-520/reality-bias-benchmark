#!/usr/bin/env python3
from __future__ import annotations

import argparse, gzip, json, zipfile
from collections import Counter
from pathlib import Path
from typing import Any

def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]

def load_gz_jsonl(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]

def walk(obj: Any, path=()):
    if isinstance(obj, dict):
        for k,v in obj.items():
            yield from walk(v, path+(str(k),))
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            yield from walk(v, path+(str(i),))
    else:
        yield path,obj

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--triage-zip", required=True)
    ap.add_argument("--r8-records", required=True)
    ap.add_argument("--outdir", required=True)
    args=ap.parse_args()

    out=Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    triage_dir=out/"triage_extract"; triage_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(args.triage_zip) as z:
        z.extractall(triage_dir)

    triage_trajs=load_jsonl(triage_dir/"trajectory_triage_summary.jsonl")
    triage_cases=load_jsonl(triage_dir/"semantic_triage_cases.jsonl")
    run_ids={x["source_run_id"] for x in triage_trajs}
    r8=load_gz_jsonl(Path(args.r8_records))

    top=Counter()
    leaf_key=Counter()
    matched=[]
    unmatched=[]
    multi=[]
    for rec in r8:
        top.update(rec.keys())
        strings=[]
        for p,v in walk(rec):
            if p: leaf_key[p[-1]]+=1
            if isinstance(v,str) and v in run_ids:
                strings.append((p,v))
        vals=sorted(set(v for _,v in strings))
        if len(vals)==1:
            matched.append((vals[0],rec,strings))
        elif len(vals)==0:
            unmatched.append(rec)
        else:
            multi.append((vals,rec,strings))

    sample = matched[0] if matched else None
    probe_out={
        "r8_record_count":len(r8),
        "triage_trajectory_count":len(triage_trajs),
        "triage_case_count":len(triage_cases),
        "triage_run_id_count":len(run_ids),
        "matched_r8_to_triage_run_count":len(matched),
        "matched_unique_run_count":len({x[0] for x in matched}),
        "unmatched_r8_record_count":len(unmatched),
        "multi_match_r8_record_count":len(multi),
        "top_level_keys":top.most_common(),
        "leaf_key_frequency_top200":leaf_key.most_common(200),
        "sample_matched_run_id": sample[0] if sample else None,
        "sample_run_id_paths":[(".".join(map(str,p)),v) for p,v in (sample[2] if sample else [])],
    }
    (out/"schema_probe_summary.json").write_text(json.dumps(probe_out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    if sample:
        (out/"sample_natural_record.json").write_text(json.dumps(sample[1],indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    # Collect compact views of every natural record: all scalar leaves whose path/key mentions
    # adjudication, verdict, episode, C/P/R, support, event, turn, lineage, scope, retrospective.
    keywords=("adjud","verdict","episode","support","dynamic","permission","lineage","scope",
              "retrospective","event","turn","coupling","cpr","trajectory","run_id","source_run")
    compact=[]
    for run_id,rec,_ in matched:
        leaves=[]
        for p,v in walk(rec):
            ps=".".join(map(str,p))
            low=ps.lower()
            if any(k in low for k in keywords) and not isinstance(v,(dict,list)):
                if isinstance(v,(str,int,float,bool)) or v is None:
                    leaves.append({"path":ps,"value":v})
        compact.append({"run_id":run_id,"leaves":leaves})
    (out/"natural_record_compact_views.json").write_text(json.dumps(compact,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    print("NMI_P4_SCOUT_RECALL_SCHEMA_PROBE=PASS")
    print(f"R8_RECORDS={len(r8)}")
    print(f"TRIAGE_RUNS={len(run_ids)}")
    print(f"MATCHED_UNIQUE_RUNS={len({x[0] for x in matched})}")
    print(f"MATCHED_RECORDS={len(matched)}")

if __name__=="__main__":
    main()
