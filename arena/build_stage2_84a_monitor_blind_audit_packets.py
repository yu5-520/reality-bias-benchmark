#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, io, json, tarfile
from pathlib import Path

FORBIDDEN = (
    "monitor_evidence","monitor_candidates","repair_packages","runtime_bridge",
    "native_event_index","wire_index","semantic_audit_reference","cpr_prediction"
)
SEMANTIC_KEYS = (
    "event","message","handoff","protocol","provider","retriev","memory",
    "compress","call","stdout","stderr","state","result","ledger"
)
MAX_PACKET_CHARS = 70000
MAX_PREVIEW = 900

def h(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def clip(x, n=MAX_PREVIEW):
    s=x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,sort_keys=True,default=str)
    s=s.replace("\x00","")
    return s if len(s)<=n else s[:n]+f"...[+{len(s)-n} chars]"

def parse(raw: bytes):
    try:
        text=raw.decode("utf-8")
    except UnicodeDecodeError:
        return None,None
    try:
        return text,json.loads(text)
    except Exception:
        return text,None

def member_map(ar):
    return {m.name.removeprefix("./"):m for m in ar.getmembers() if m.isfile()}

def read_member(ar,members,name):
    m=members.get(name)
    if not m: raise KeyError(name)
    f=ar.extractfile(m)
    return f.read() if f else b""

def verify_entries(ar,members,manifest):
    for row in manifest["entries"]:
        p=row["path"]
        low=p.lower()
        if any(tok in low for tok in FORBIDDEN):
            raise RuntimeError(f"forbidden audit path: {p}")
        raw=read_member(ar,members,p)
        if h(raw)!=row["sha256"] or len(raw)!=row["bytes"]:
            raise RuntimeError(f"audit entry mismatch: {p}")

def build_packet(group,cell,cell_dir):
    receipt=json.loads((cell_dir/"attempt_receipt.json").read_text())
    arc=(cell_dir/"first_attempt.tar.gz").read_bytes()
    if h(arc)!=receipt["archive_sha256"]:
        raise RuntimeError(f"{group}/{cell}: archive hash mismatch")
    packet={
        "schema":"stage2-84a-monitor-blind-audit-packet-v1",
        "group_id":group,"cell_id":cell,
        "attempt_receipt":receipt,
        "monitor_blind":True,
        "monitor_runtime_bundle_read":False,
        "route_ref":f"AUDIT_PACKET:{group}:{cell}:ROUTE_INDEX",
        "audit_manifest_sha256":None,
        "audit_manifest_missing":False,
        "evidence":[],
        "route_index":[],
    }
    with tarfile.open(fileobj=io.BytesIO(arc),mode="r:gz") as ar:
        members=member_map(ar)
        if "audit_raw_bundle_manifest.json" not in members:
            packet["audit_manifest_missing"]=True
            packet["coverage"]="TERMINATION_ONLY"
            packet["evidence"].append({
                "ref":"E0001","path":"attempt_receipt.json","sha256":h((cell_dir/"attempt_receipt.json").read_bytes()),
                "sequence":None,"preview":clip(receipt,1800)
            })
            packet["packet_sha256"]=""
            packet["packet_sha256"]=h(json.dumps(packet,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode())
            return packet

        raw_manifest=read_member(ar,members,"audit_raw_bundle_manifest.json")
        manifest=json.loads(raw_manifest)
        assert manifest["role"]=="MONITOR_BLIND_SEMANTIC_AUDIT_INPUT"
        assert manifest["monitor_runtime_bundle_readable_before_reference_seal"] is False
        assert manifest["group_id"]==group and manifest["cell_id"]==cell
        verify_entries(ar,members,manifest)
        packet["audit_manifest_sha256"]=manifest.get("manifest_sha256") or h(raw_manifest)
        packet["coverage"]="AUDIT_RAW_BUNDLE"
        allowed={r["path"]:r for r in manifest["entries"]}

        items=[]
        def add(path,preview,sequence=None,subref=None,sha=None):
            ref=f"E{len(items)+1:04d}"
            items.append({
                "ref":ref,"path":path if subref is None else f"{path}{subref}",
                "sha256":sha or allowed.get(path,{}).get("sha256"),
                "sequence":sequence,"preview":clip(preview)
            })
            return ref

        # Core natural/run state.
        for p in ("natural_A_result.json","run_manifest.json","checkpoint_ledger.json"):
            if p not in allowed: continue
            raw=read_member(ar,members,p); text,obj=parse(raw)
            if p=="natural_A_result.json" and isinstance(obj,dict):
                summary={k:v for k,v in obj.items() if k not in ("history","trace")}
                add(p,summary,sha=allowed[p]["sha256"])
                rows=obj.get("history") if isinstance(obj.get("history"),list) else obj.get("trace")
                if isinstance(rows,list):
                    for i,row in enumerate(rows,1):
                        rr=add(p,row,sequence=(row.get("turn") if isinstance(row,dict) else i),
                               subref=f"#route[{i}]",sha=allowed[p]["sha256"])
                        packet["route_index"].append(rr)
            elif p=="checkpoint_ledger.json" and isinstance(obj,dict):
                cps=obj.get("checkpoints") or []
                compact=[]
                for cp in cps:
                    compact.append({k:cp.get(k) for k in (
                        "boundary","event_ref","model_decision_sequence","restore_capability","checkpoint_hash"
                    )})
                add(p,{"checkpoint_count":len(cps),"checkpoints":compact},sha=allowed[p]["sha256"])
            else:
                add(p,obj if obj is not None else text,sha=allowed[p]["sha256"])

        # Observer/protocol/carrier textual records from the admissible manifest.
        for p,row in sorted(allowed.items()):
            low=p.lower()
            if p in ("natural_A_result.json","run_manifest.json","checkpoint_ledger.json"): continue
            if p.startswith("checkpoints/") and "/application/" in p: continue
            if not any(k in low for k in SEMANTIC_KEYS): continue
            if row["bytes"]>131072: continue
            raw=read_member(ar,members,p)
            text,obj=parse(raw)
            if text is None: continue
            if p.endswith(".jsonl"):
                for ln,line in enumerate(text.splitlines(),1):
                    if not line.strip(): continue
                    try: val=json.loads(line)
                    except Exception: val=line
                    seq=val.get("sequence") if isinstance(val,dict) else None
                    rr=add(p,val,sequence=seq,subref=f"#L{ln}",sha=row["sha256"])
                    if "event" in low or "message" in low or "call" in low:
                        packet["route_index"].append(rr)
            else:
                add(p,obj if obj is not None else text,sha=row["sha256"])
            if len(json.dumps(items,ensure_ascii=False))>MAX_PACKET_CHARS:
                break

        # Repository-state change summary from first/last checkpoint manifests.
        checkpoint_manifests=[p for p in allowed if p.startswith("checkpoints/") and p.endswith("/manifest.json")]
        cp_rows=[]
        for p in checkpoint_manifests:
            raw=read_member(ar,members,p); _,obj=parse(raw)
            if isinstance(obj,dict) and isinstance(obj.get("application_file_hashes"),dict):
                cp_rows.append((obj.get("model_decision_sequence",0),p,obj))
        if cp_rows:
            cp_rows.sort(key=lambda x:(x[0] if isinstance(x[0],int) else 0,x[1]))
            first,last=cp_rows[0],cp_rows[-1]
            a,b=first[2]["application_file_hashes"],last[2]["application_file_hashes"]
            changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
            add(first[1],{
                "derived_from":[first[1],last[1]],"first_event_ref":first[2].get("event_ref"),
                "last_event_ref":last[2].get("event_ref"),"changed_files":changed,
                "first_hashes":{k:a.get(k) for k in changed},"last_hashes":{k:b.get(k) for k in changed}
            },sha=allowed[first[1]]["sha256"])

        packet["evidence"]=items
    packet["packet_sha256"]=""
    packet["packet_sha256"]=h(json.dumps(packet,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode())
    return packet

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--g2",required=True); ap.add_argument("--g3",required=True)
    ap.add_argument("--g4",required=True); ap.add_argument("--g5",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    roots={"G2":Path(args.g2),"G3":Path(args.g3),"G4":Path(args.g4),"G5":Path(args.g5)}
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    index=[]
    for group,root in roots.items():
        for x in range(1,8):
            for t in range(1,4):
                cell=f"X{x}-T{t}"
                cell_dir=root/"stage2"/"replication_v2"/group/"natural_A"/cell
                if not cell_dir.is_dir(): raise SystemExit(f"missing {cell_dir}")
                packet=build_packet(group,cell,cell_dir)
                p=out/f"{group}-{cell}.json"
                p.write_text(json.dumps(packet,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
                index.append({
                    "group_id":group,"cell_id":cell,"packet_path":p.name,
                    "packet_sha256":packet["packet_sha256"],
                    "audit_manifest_sha256":packet["audit_manifest_sha256"],
                    "audit_manifest_missing":packet["audit_manifest_missing"],
                    "evidence_count":len(packet["evidence"]),
                    "route_ref":packet["route_ref"]
                })
    assert len(index)==84
    payload={
        "schema":"stage2-84a-monitor-blind-audit-packet-index-v1",
        "cell_count":84,"monitor_runtime_bundle_read":False,
        "forbidden_monitor_tokens":list(FORBIDDEN),"cells":index
    }
    (out/"packet_index.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":"PASS","cells":84,"missing_manifests":sum(x["audit_manifest_missing"] for x in index)},sort_keys=True))

if __name__=="__main__":
    main()
