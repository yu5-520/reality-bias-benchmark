#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from pathlib import Path

REQ={"reference_id","group_id","cell_id","structure_family","claim_status","complete_route_ref",
"evidence_surface_required","evidence_surface_available","negative_case","evidence_refs"}
GROUPS={"G2","G3","G4","G5"}
STATUSES={"SUPPORTED","SUPPORTED_CANDIDATE","NOT_ESTABLISHED","NEGATIVE_BOUNDARY"}
FAMILIES={"SCOPE_EXPANSION","STATE_MISMATCH","HISTORICAL_REENTRY","REPEATED_REVIEW_REOPEN",
"AUTHORITY_STATUS_SHIFT","RECURSIVE_MEMORY_FEEDBACK","CARRIER_TRANSFORMATION",
"SEMANTIC_REPOSITORY_CLOSURE_DIVERGENCE","OTHER_FROZEN_STRUCTURAL_SIGNATURE"}

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--packets",required=True)
    ap.add_argument("--audit",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    pd,ad,out=Path(a.packets),Path(a.audit),Path(a.out)
    pidx=json.loads((pd/"packet_index.json").read_text())
    summary=json.loads((ad/"audit_run_summary.json").read_text())
    assert pidx["cell_count"]==84
    assert pidx["monitor_runtime_bundle_read"] is False
    assert summary["completed_cells"]==84 and not summary["errors"]
    assert summary["monitor_blind"] is True
    assert summary["monitor_runtime_bundle_read"] is False
    assert summary["subject_calls"]==0 and summary["subject_reruns"]==0
    assert summary["repair_calls"]==0 and summary["monitor_evaluation"] is False

    rows=[json.loads(x) for x in (ad/"reference_records.jsonl").read_text().splitlines() if x.strip()]
    assert rows
    cellset=set()
    ids=set()
    status=Counter()
    fam=Counter()
    dims=Counter()
    negative=0
    for r in rows:
        assert REQ<=set(r)
        assert r["reference_id"] not in ids
        ids.add(r["reference_id"])
        assert r["group_id"] in GROUPS
        assert r["claim_status"] in STATUSES
        assert r["structure_family"] in FAMILIES
        assert r["evidence_refs"]
        cellset.add((r["group_id"],r["cell_id"]))
        status[r["claim_status"]]+=1
        fam[r["structure_family"]]+=1
        for d in r.get("cpr_dimensions",[]): dims[d]+=1
        negative += int(bool(r["negative_case"]))
    expected={(g,f"X{x}-T{t}") for g in GROUPS for x in range(1,8) for t in range(1,4)}
    assert cellset==expected, (len(cellset),sorted(expected-cellset)[:5])
    assert len(list((ad/"cell_audits").glob("*.json")))==84
    assert len(pidx["cells"])==84

    files=[]
    for root,label in ((pd,"packets"),(ad,"audit")):
        for path in sorted(root.rglob("*")):
            if path.is_file():
                files.append({"scope":label,"path":str(path.relative_to(root)),"sha256":sha(path),"bytes":path.stat().st_size})
    seal={
      "schema":"stage2-84a-semantic-audit-reference-set-index-v1",
      "status":"SEALED",
      "population":"G2_G5_84_NATURAL_A",
      "cell_count":84,
      "reference_record_count":len(rows),
      "monitor_blind":True,
      "monitor_runtime_bundle_read":False,
      "subject_calls":0,
      "subject_reruns":0,
      "repair_calls":0,
      "monitor_evaluation_state":"READY_AFTER_REFERENCE_SEAL_NOT_EXECUTED",
      "engineering_B_state":"LOCKED",
      "provider_call_count":summary["provider_call_count"],
      "estimated_cost_usd_peak":summary["estimated_cost_usd_peak"],
      "claim_status_counts":dict(status),
      "structure_family_counts":dict(fam),
      "cpr_dimension_record_counts":dict(dims),
      "negative_case_count":negative,
      "packet_index_sha256":sha(pd/"packet_index.json"),
      "reference_records_sha256":sha(ad/"reference_records.jsonl"),
      "audit_summary_sha256":sha(ad/"audit_run_summary.json"),
      "files":files
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(seal,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:seal[k] for k in ("status","cell_count","reference_record_count","provider_call_count","estimated_cost_usd_peak","negative_case_count")},sort_keys=True))

if __name__=="__main__": main()
