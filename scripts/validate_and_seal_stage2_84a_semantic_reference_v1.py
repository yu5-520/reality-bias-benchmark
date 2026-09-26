#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter,defaultdict
from pathlib import Path

FORBIDDEN=("monitor_evidence","monitor_candidates","repair_packages","runtime_bridge","native_event_index","wire_index","cpr_prediction")
REQ={"reference_id","group_id","cell_id","structure_family","claim_status","complete_route_ref","evidence_surface_required","evidence_surface_available","negative_case","evidence_refs"}
STAT={"SUPPORTED","SUPPORTED_CANDIDATE","NOT_ESTABLISHED","NEGATIVE_BOUNDARY"}
STRUCT={"SCOPE_EXPANSION","STATE_MISMATCH","HISTORICAL_REENTRY","REPEATED_REVIEW_REOPEN","AUTHORITY_STATUS_SHIFT","RECURSIVE_MEMORY_FEEDBACK","CARRIER_TRANSFORMATION","SEMANTIC_REPOSITORY_CLOSURE_DIVERGENCE","OTHER_FROZEN_STRUCTURAL_SIGNATURE"}

def h(p:Path):
    x=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): x.update(b)
    return x.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--packets",required=True)
    ap.add_argument("--audit",required=True)
    ap.add_argument("--authorization",required=True)
    ap.add_argument("--source-block-index",required=True)
    args=ap.parse_args()
    pd=Path(args.packets); ad=Path(args.audit)
    auth=json.loads(Path(args.authorization).read_text())
    source=json.loads(Path(args.source_block_index).read_text())
    pi=json.loads((pd/"packet_index.json").read_text())
    summary=json.loads((ad/"audit_run_summary.json").read_text())
    assert source["complete"] is True and source["natural_first_attempts"]==84
    assert auth["source_block_index"]["blob_sha"]=="b3599a0a6b46f279b94a648b0c82213e58455e33"
    assert pi["cell_count"]==84 and pi["monitor_runtime_bundle_read"] is False
    assert summary["completed_cells"]==84 and not summary["errors"]
    assert summary["monitor_blind"] is True and summary["monitor_runtime_bundle_read"] is False
    assert summary["subject_calls"]==0 and summary["subject_reruns"]==0 and summary["repair_calls"]==0
    assert summary["estimated_cost_usd_peak"]<=summary["max_spend_usd"]<=10.0

    packet_by={(x["group_id"],x["cell_id"]):x for x in pi["cells"]}
    assert len(packet_by)==84
    for g in ("G2","G3","G4","G5"):
        assert sum(k[0]==g for k in packet_by)==21

    refs=[]
    for line in (ad/"reference_records.jsonl").read_text().splitlines():
        if line.strip(): refs.append(json.loads(line))
    assert refs and len({r["reference_id"] for r in refs})==len(refs)
    status=Counter(); structures=Counter(); by_group=Counter(); by_cell=Counter(); cpr=Counter()
    for r in refs:
        assert REQ<=set(r)
        assert r["claim_status"] in STAT
        assert r["structure_family"] in STRUCT
        key=(r["group_id"],r["cell_id"])
        assert key in packet_by
        packet=json.loads((pd/packet_by[key]["packet_path"]).read_text())
        allowed={x["ref"] for x in packet["evidence"]}
        assert r["complete_route_ref"]==packet["route_ref"]
        assert r["evidence_refs"] and all(x in allowed for x in r["evidence_refs"])
        for k in ("source_ref","carrier_ref","decision_or_action_ref","consequence_ref"):
            if r.get(k) is not None: assert r[k] in allowed
        if r["claim_status"]=="SUPPORTED": assert r["evidence_surface_available"] is True
        if len(r.get("cpr_dimensions",[]))>1: assert r.get("cross_penetration_path")
        status[r["claim_status"]]+=1; structures[r["structure_family"]]+=1; by_group[r["group_id"]]+=1; by_cell[key]+=1
        for d in r.get("cpr_dimensions",[]): cpr[d]+=1
    assert len(by_cell)==84 and all(v>=1 for v in by_cell.values())

    # Verify no audit packet/reference source path is monitor-derived.
    for meta in pi["cells"]:
        packet=json.loads((pd/meta["packet_path"]).read_text())
        assert packet["monitor_runtime_bundle_read"] is False
        for e in packet["evidence"]:
            low=e["path"].lower()
            assert not any(tok in low for tok in FORBIDDEN), e["path"]

    ref_hash=h(ad/"reference_records.jsonl")
    index={
      "schema":"stage2-84a-semantic-reference-set-index-v1",
      "status":"SEALED_MONITOR_BLIND_REFERENCE_SET",
      "population":"G2_G5_84_NATURAL_A",
      "cell_count":84,
      "reference_record_count":len(refs),
      "reference_records_sha256":ref_hash,
      "packet_index_sha256":h(pd/"packet_index.json"),
      "audit_run_summary_sha256":h(ad/"audit_run_summary.json"),
      "source_84a_block_index_sha256":h(Path(args.source_block_index)),
      "monitor_blind":True,
      "monitor_runtime_bundle_read":False,
      "subject_calls":0,
      "subject_reruns":0,
      "repair_calls":0,
      "provider_call_count":summary["provider_call_count"],
      "estimated_cost_usd_peak":summary["estimated_cost_usd_peak"],
      "claim_status_counts":dict(sorted(status.items())),
      "structure_family_counts":dict(sorted(structures.items())),
      "cpr_dimension_record_counts":dict(sorted(cpr.items())),
      "reference_records_by_group":dict(sorted(by_group.items())),
      "groups":{"G2":21,"G3":21,"G4":21,"G5":21},
      "reference_role":"WITHIN_STUDY_SEMANTIC_PROCESS_ADJUDICATION_NOT_UNIVERSAL_GROUND_TRUTH"
    }
    (ad/"reference_set_index.json").write_text(json.dumps(index,indent=2,sort_keys=True)+"\n")
    seal={
      "schema":"stage2-84a-semantic-reference-set-seal-v1",
      "status":"SEALED",
      "reference_set_index_sha256":h(ad/"reference_set_index.json"),
      "reference_records_sha256":ref_hash,
      "monitor_evaluation_state":"READY_AFTER_REFERENCE_SEAL",
      "engineering_B_state":"LOCKED_UNTIL_PRIMARY_MONITOR_EVALUATION_SEALED",
      "experimental_general_chapter_synthesis_state":"READY",
      "monitor_blind":True
    }
    (ad/"reference_set_seal.json").write_text(json.dumps(seal,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":"PASS","cells":84,"records":len(refs),"reference_sha256":ref_hash,"claim_status_counts":dict(status),"structure_counts":dict(structures)},sort_keys=True))

if __name__=="__main__": main()
