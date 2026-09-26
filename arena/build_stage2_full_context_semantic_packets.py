#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, io, json, tarfile
from pathlib import Path

FORBIDDEN=(
    "monitor_evidence","monitor_candidates","repair_packages","runtime_bridge",
    "native_event_index","wire_index","semantic_audit_reference","cpr_prediction",
    "reference_records","blind_reference"
)
SEMANTIC_KEYS=(
    "event","message","handoff","protocol","provider","retriev","memory","compress",
    "call","stdout","stderr","state","result","ledger","checkpoint","tool","resource"
)
MAX_PACKET_CHARS=280000
MAX_PREVIEW=1400

SYSTEMS={
    "X1":"AutoGen","X2":"MetaGPT","X3":"A2A","X4":"MCP",
    "X5":"RAG","X6":"MemoryBank","X7":"LongLLMLingua"
}
TASKS={
    "T1":"version iteration / compatibility-chain historical residue",
    "T2":"broad coding request / implementation-scope expansion",
    "T3":"before-after update version check / historical path retirement"
}

def h(raw:bytes)->str: return hashlib.sha256(raw).hexdigest()

def clip(value,n=MAX_PREVIEW):
    s=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True,default=str)
    s=s.replace("\x00","")
    return s if len(s)<=n else s[:n]+f"...[+{len(s)-n} chars]"

def parse(raw:bytes):
    try: text=raw.decode("utf-8")
    except UnicodeDecodeError: return None,None
    try: return text,json.loads(text)
    except Exception: return text,None

def preview(obj):
    if not isinstance(obj,dict): return clip(obj)
    keys=("sequence","turn","type","surface","source","sender","recipient","role","agent","name",
          "target","content","message","request","response","result","tool","tool_name","arguments",
          "action","actions","status","task","artifact","handoff_target","function","error","decision")
    out={k:obj[k] for k in keys if k in obj}
    return clip(out if out else obj)

def member_map(ar):
    return {m.name.removeprefix("./"):m for m in ar.getmembers() if m.isfile()}

def read(ar,members,name):
    f=ar.extractfile(members[name])
    return f.read() if f else b""

def verify(ar,members,manifest):
    for row in manifest["entries"]:
        p=row["path"]; low=p.lower()
        if any(tok in low for tok in FORBIDDEN):
            raise RuntimeError(f"forbidden input path: {p}")
        if p not in members: raise RuntimeError(f"manifest member missing: {p}")
        raw=read(ar,members,p)
        if h(raw)!=row["sha256"] or len(raw)!=row["bytes"]:
            raise RuntimeError(f"manifest hash/size mismatch: {p}")

def build_packet(group,cell,cell_dir):
    x,t=cell.split("-")
    receipt=json.loads((cell_dir/"attempt_receipt.json").read_text())
    arc=(cell_dir/"first_attempt.tar.gz").read_bytes()
    if h(arc)!=receipt["archive_sha256"]: raise RuntimeError(f"{group}/{cell}: archive mismatch")
    packet={
      "schema":"stage2-full-context-process-semantic-packet-v1",
      "group_id":group,"cell_id":cell,"x_id":x,"task_id":t,
      "system_condition":SYSTEMS[x],"task_family":TASKS[t],
      "study_context":{
        "common_logical_model_decision_ceiling":64,
        "process_reality_primary_object":True,
        "theory_aware":True,
        "blind_reference_labels_read":False,
        "monitor_runtime_bundle_read":False
      },
      "attempt_receipt":receipt,
      "audit_manifest_sha256":None,
      "evidence":[],
      "route_index":[],
      "repository_state":None
    }
    with tarfile.open(fileobj=io.BytesIO(arc),mode="r:gz") as ar:
        members=member_map(ar)
        if "audit_raw_bundle_manifest.json" not in members:
            raise RuntimeError(f"{group}/{cell}: no legal audit_raw_bundle_manifest")
        raw_manifest=read(ar,members,"audit_raw_bundle_manifest.json")
        manifest=json.loads(raw_manifest)
        assert manifest["role"]=="MONITOR_BLIND_SEMANTIC_AUDIT_INPUT"
        assert manifest["monitor_runtime_bundle_readable_before_reference_seal"] is False
        assert manifest["group_id"]==group and manifest["cell_id"]==cell
        verify(ar,members,manifest)
        packet["audit_manifest_sha256"]=manifest.get("manifest_sha256") or h(raw_manifest)
        allowed={r["path"]:r for r in manifest["entries"]}
        items=[]
        def add(path,value,sequence=None,subref=None,sha=None,kind="EVIDENCE"):
            ref=f"E{len(items)+1:04d}"
            items.append({"ref":ref,"path":path+(subref or ""),"sha256":sha or allowed.get(path,{}).get("sha256"),
                          "sequence":sequence,"kind":kind,"preview":preview(value)})
            return ref

        # Complete runner route first.
        p="natural_A_result.json"
        if p in allowed:
            raw=read(ar,members,p); text,obj=parse(raw)
            if isinstance(obj,dict):
                summary={k:v for k,v in obj.items() if k not in ("history","trace")}
                add(p,summary,sha=allowed[p]["sha256"],kind="RUN_SUMMARY")
                rows=obj.get("history") if isinstance(obj.get("history"),list) else obj.get("trace")
                if isinstance(rows,list):
                    for i,row in enumerate(rows,1):
                        seq=row.get("turn",i) if isinstance(row,dict) else i
                        rr=add(p,row,sequence=seq,subref=f"#route[{i}]",sha=allowed[p]["sha256"],kind="ROUTE_NODE")
                        packet["route_index"].append(rr)

        for p in ("run_manifest.json","checkpoint_ledger.json"):
            if p not in allowed: continue
            raw=read(ar,members,p); text,obj=parse(raw)
            if p=="checkpoint_ledger.json" and isinstance(obj,dict):
                cps=obj.get("checkpoints") or []
                compact=[{k:cp.get(k) for k in ("boundary","event_ref","model_decision_sequence","restore_capability","checkpoint_hash")} for cp in cps]
                add(p,{"checkpoint_count":len(cps),"checkpoints":compact},sha=allowed[p]["sha256"],kind="CHECKPOINT_TIMELINE")
            else:
                add(p,obj if obj is not None else text,sha=allowed[p]["sha256"],kind="RUN_METADATA")

        # All admissible observer/protocol/carrier event lines, compacted but ordered.
        for p,row in sorted(allowed.items()):
            low=p.lower()
            if p in ("natural_A_result.json","run_manifest.json","checkpoint_ledger.json"): continue
            if p.startswith("checkpoints/") and "/application/" in p: continue
            if not any(k in low for k in SEMANTIC_KEYS): continue
            if row["bytes"]>524288: continue
            raw=read(ar,members,p); text,obj=parse(raw)
            if text is None: continue
            if p.endswith(".jsonl"):
                for ln,line in enumerate(text.splitlines(),1):
                    if not line.strip(): continue
                    try: val=json.loads(line)
                    except Exception: val=line
                    seq=val.get("sequence") if isinstance(val,dict) else None
                    rr=add(p,val,sequence=seq,subref=f"#L{ln}",sha=row["sha256"],kind="NATIVE_OR_CARRIER_EVENT")
                    packet["route_index"].append(rr)
            else:
                add(p,obj if obj is not None else text,sha=row["sha256"],kind="OBSERVER_OR_CARRIER_STATE")
            if len(json.dumps(items,ensure_ascii=False,separators=(",",":")))>MAX_PACKET_CHARS:
                break

        # First/last persisted application-state comparison with changed file texts where available.
        cps=[]
        for p in allowed:
            if p.startswith("checkpoints/") and p.endswith("/manifest.json"):
                raw=read(ar,members,p); _,obj=parse(raw)
                if isinstance(obj,dict) and isinstance(obj.get("application_file_hashes"),dict):
                    cps.append((obj.get("model_decision_sequence",0),p,obj))
        if cps:
            cps.sort(key=lambda z:(z[0] if isinstance(z[0],int) else 0,z[1]))
            first,last=cps[0],cps[-1]; a,b=first[2]["application_file_hashes"],last[2]["application_file_hashes"]
            changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
            state={"first_manifest":first[1],"last_manifest":last[1],
                   "first_event_ref":first[2].get("event_ref"),"last_event_ref":last[2].get("event_ref"),
                   "changed_files":changed,
                   "hash_transitions":{k:{"before":a.get(k),"after":b.get(k)} for k in changed},
                   "changed_file_snapshots":[]}
            for rel in changed[:24]:
                candidates=[p for p in allowed if p.endswith("/application/"+rel)]
                candidates=sorted(candidates)
                if not candidates: continue
                for label,pp in (("earliest",candidates[0]),("latest",candidates[-1])):
                    raw=read(ar,members,pp); text,_=parse(raw)
                    if text is not None and len(raw)<=65536:
                        ref=add(pp,clip(text,5000),sha=allowed[pp]["sha256"],kind="PERSISTED_FILE_SNAPSHOT")
                        state["changed_file_snapshots"].append({"relative_path":rel,"position":label,"evidence_ref":ref})
            packet["repository_state"]=state
            add(first[1],state,sha=allowed[first[1]]["sha256"],kind="REPOSITORY_STATE_DIFF")

        packet["evidence"]=items
    packet["route_index"]=list(dict.fromkeys(packet["route_index"]))
    packet["packet_sha256"]=""
    packet["packet_sha256"]=h(json.dumps(packet,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode())
    return packet

def main():
    ap=argparse.ArgumentParser()
    for g in ("g2","g3","g4","g5"): ap.add_argument("--"+g,required=True)
    ap.add_argument("--config",required=True); ap.add_argument("--out",required=True)
    a=ap.parse_args()
    cfg=json.loads(Path(a.config).read_text())
    eligible=set(cfg["population"]["eligible_cells"])
    roots={"G2":Path(a.g2),"G3":Path(a.g3),"G4":Path(a.g4),"G5":Path(a.g5)}
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for group,root in roots.items():
        for x in range(1,8):
            for t in range(1,4):
                cell=f"X{x}-T{t}"; full=f"{group}-{cell}"
                if full not in eligible: continue
                packet=build_packet(group,cell,root/"stage2"/"replication_v2"/group/"natural_A"/cell)
                path=out/f"{full}.json"
                path.write_text(json.dumps(packet,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
                rows.append({"group_id":group,"cell_id":cell,"full_id":full,"packet_path":path.name,
                             "packet_sha256":packet["packet_sha256"],"audit_manifest_sha256":packet["audit_manifest_sha256"],
                             "evidence_count":len(packet["evidence"]),"route_node_count":len(packet["route_index"])})
    assert len(rows)==80, len(rows)
    index={"schema":"stage2-full-context-packet-index-v1","eligible_cell_count":80,
           "blind_reference_labels_read":False,"monitor_runtime_bundle_read":False,
           "cells":rows,"excluded_boundary_cells":cfg["population"]["excluded_boundary_cells"]}
    (out/"packet_index.json").write_text(json.dumps(index,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":"PASS","cells":80,"evidence_items":sum(r["evidence_count"] for r in rows),
                      "route_nodes":sum(r["route_node_count"] for r in rows)},sort_keys=True))

if __name__=="__main__": main()
