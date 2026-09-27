#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path
from typing import Any

SYSTEMS={"X2":"MetaGPT","X4":"MCP","X5":"RAG","X7":"LongLLMLingua"}
TASKS={
    "T1":"version iteration / compatibility-chain historical residue",
    "T2":"broad coding request / implementation-scope expansion",
    "T3":"before-after update version check / historical path retirement",
}
SEMANTIC_TOKENS=(
    "event","message","handoff","protocol","provider","retriev","rag","memory","compress",
    "call","stdout","stderr","state","result","ledger","checkpoint","tool","resource",
    "wire","carrier","observation","trace"
)
PRIMARY_EXCLUDE=(
    "monitor_candidates","monitor_evidence","post_repair_monitor","post_repair_watch",
    "runtime_bridge","semantic_audit","reference_records","blind_reference","cpr_prediction"
)
MAX_PACKET_CHARS=420000
MAX_ITEM_CHARS=7000

def h(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def stable_hash(obj:Any)->str:
    return h(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode())

def clip(value:Any,n:int=MAX_ITEM_CHARS)->str:
    if isinstance(value,str):
        s=value
    else:
        s=json.dumps(value,ensure_ascii=False,sort_keys=True,default=str)
    s=s.replace("\x00","")
    if len(s)<=n:
        return s
    return s[:n]+f"...[+{len(s)-n} chars]"

def members(ar:tarfile.TarFile):
    return {m.name.removeprefix("./"):m for m in ar.getmembers() if m.isfile()}

def read_raw(ar:tarfile.TarFile, mm:dict[str,tarfile.TarInfo], name:str)->bytes:
    f=ar.extractfile(mm[name])
    return f.read() if f else b""

def read_json(ar,mm,name):
    return json.loads(read_raw(ar,mm,name).decode("utf-8"))

def maybe_json(raw:bytes):
    try:
        txt=raw.decode("utf-8")
    except UnicodeDecodeError:
        return None,None
    try:
        return txt,json.loads(txt)
    except Exception:
        return txt,None

def route_rows(result:dict[str,Any]):
    rows=result.get("history")
    if isinstance(rows,list):
        return rows
    rows=result.get("trace")
    if isinstance(rows,list):
        return rows
    return []

def row_sequence(row:Any, fallback:int):
    if isinstance(row,dict):
        for key in ("model_decision_sequence","sequence","turn","round"):
            v=row.get(key)
            if isinstance(v,int):
                return v
    return fallback

def checkpoint_manifests(ar,mm,prefix):
    out=[]
    for name in mm:
        if not name.startswith(prefix) or not name.endswith("/manifest.json"):
            continue
        try:
            obj=read_json(ar,mm,name)
        except Exception:
            continue
        if not isinstance(obj,dict) or "application_file_hashes" not in obj:
            continue
        seq=obj.get("model_decision_sequence")
        out.append((seq if isinstance(seq,int) else -1,name,obj))
    out.sort(key=lambda x:(x[0],x[1]))
    return out

def app_snapshot(ar,mm,manifest_path,rel):
    base=manifest_path.rsplit("/manifest.json",1)[0]+"/application/"+rel
    if base not in mm:
        return None
    raw=read_raw(ar,mm,base)
    if len(raw)>65536:
        return {"path":base,"sha256":h(raw),"content":None,"bytes":len(raw)}
    try:
        txt=raw.decode("utf-8")
    except UnicodeDecodeError:
        return {"path":base,"sha256":h(raw),"content":None,"bytes":len(raw)}
    return {"path":base,"sha256":h(raw),"content":clip(txt,6000),"bytes":len(raw)}

def selected_package(a_ar,a_mm,package_id):
    if "repair_packages.json" not in a_mm:
        raise RuntimeError("A archive missing repair_packages.json")
    rows=read_json(a_ar,a_mm,"repair_packages.json")
    matches=[x for x in rows if x.get("package_id")==package_id]
    if len(matches)!=1:
        raise RuntimeError(f"selected package {package_id} not unique")
    return matches[0]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--evidence-root",required=True)
    ap.add_argument("--config",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()

    root=Path(args.evidence_root)
    cfg=json.loads(Path(args.config).read_text())
    expected=cfg["population"]["paired_cells"]
    gidx=json.loads((root/"phase_b_provider_v2_group_index.json").read_text())
    assert gidx["state"]=="FROZEN_B_FIRST_ATTEMPTS"
    assert gidx["successful_B_count"]==12
    assert gidx["failed_B_count"]==0
    assert gidx["missing_cells"]==[]
    assert gidx["preserved_cells"]==expected
    assert gidx["semantic_audit_gate"]=="OPEN_AFTER_B_FREEZE"
    b_by={x["cell_id"]:x for x in gidx["receipts"]}

    out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    index=[]

    for cell in expected:
        x,t=cell.split("-",1)
        a_dir=root/"natural_A_provider_v2"/cell
        b_dir=root/"repair_B_provider_v2"/cell
        a_receipt=json.loads((a_dir/"attempt_receipt.json").read_text())
        b_receipt=json.loads((b_dir/"attempt_receipt.json").read_text())
        assert b_receipt==b_by[cell]
        a_arc=(a_dir/"first_attempt.tar.gz").read_bytes()
        b_arc=(b_dir/"first_B_attempt.tar.gz").read_bytes()
        assert h(a_arc)==a_receipt["archive_sha256"]
        assert h(b_arc)==b_receipt["archive_sha256"]
        assert b_receipt["runner_exit_code"]==0
        assert b_receipt["seal_status"]=="REPAIR_B_FROZEN"
        assert b_receipt["same_parent_checkpoint"] is True
        assert b_receipt["repair_action_count"]==1

        ev=[]
        counters={"A":0,"B":0,"I":0,"P":0}
        def add(arm,path,value,kind,sequence=None,sha256=None,notes=None):
            counters[arm]+=1
            ref=f"{arm}{counters[arm]:04d}"
            item={
                "ref":ref,"arm":arm,"path":path,"kind":kind,
                "sequence":sequence,"sha256":sha256,
                "content":clip(value),
            }
            if notes:
                item["notes"]=notes
            ev.append(item)
            return ref

        add("P","phase_b_provider_v2_group_index.json",
            {k:gidx.get(k) for k in (
                "state","source_workflow_run","b_code_sha","group_claim_commit",
                "one_B_per_cell","automatic_retries","post_repair_monitor_mode",
                "semantic_audit_gate"
            )},
            "PAIR_PROVENANCE",sha256=stable_hash(gidx))
        add("A",str(a_dir/"attempt_receipt.json"),a_receipt,"A_ATTEMPT_RECEIPT")
        add("B",str(b_dir/"attempt_receipt.json"),b_receipt,"B_ATTEMPT_RECEIPT")

        with tarfile.open(fileobj=io.BytesIO(a_arc),mode="r:gz") as aa, \
             tarfile.open(fileobj=io.BytesIO(b_arc),mode="r:gz") as ba:
            am=members(aa); bm=members(ba)
            package=selected_package(aa,am,b_receipt["package_id"])
            assert package["package_id"]==b_receipt["package_id"]
            parent_hash=b_receipt["parent_checkpoint_hash"]
            parent_path=f"checkpoints/{parent_hash}/manifest.json"
            if parent_path not in am:
                raise RuntimeError(f"{cell}: parent manifest missing")
            parent=read_json(aa,am,parent_path)
            assert parent["checkpoint_hash"]==parent_hash
            assert parent["restore_capability"]=="FULL_NATIVE"

            pkg_ref=add("I","A:repair_packages.json#selected",package,"FROZEN_SELECTED_REPAIR_PACKAGE",
                        sequence=package.get("prefix_sequence"),
                        sha256=package.get("package_hash"),
                        notes="Posthoc-visible intervention package; selection was frozen before B and no semantic audit was used.")
            parent_ref=add("P","A:"+parent_path,parent,"SAME_PARENT_CHECKPOINT",
                           sequence=parent.get("model_decision_sequence"),
                           sha256=parent_hash)
            parent_seq=parent.get("model_decision_sequence")
            if not isinstance(parent_seq,int):
                parent_seq=package.get("prefix_sequence")
            if not isinstance(parent_seq,int):
                parent_seq=0

            # A natural arm
            if "natural_A_result.json" not in am:
                raise RuntimeError(f"{cell}: A result missing")
            a_result=read_json(aa,am,"natural_A_result.json")
            a_summary={k:v for k,v in a_result.items() if k not in ("history","trace")}
            a_summary_ref=add("A","natural_A_result.json",a_summary,"A_RUN_SUMMARY")
            a_route_refs=[]
            for i,row in enumerate(route_rows(a_result),1):
                seq=row_sequence(row,i)
                ref=add("A",f"natural_A_result.json#route[{i}]",row,
                        "A_ROUTE_NODE",sequence=seq,
                        notes="POST_PARENT" if seq>=parent_seq else "PRE_PARENT_CONTEXT")
                a_route_refs.append(ref)

            # B intervention and continuation
            required_b=("repair_request.json","repair_response.json","repair_action.json",
                        "repair_boundary_result.json","post_repair_result.json","seal.json")
            for name in required_b:
                if name not in bm:
                    raise RuntimeError(f"{cell}: B archive missing {name}")
            intervention_refs=[pkg_ref,parent_ref]
            for name,kind in (
                ("repair_request.json","REPAIR_REQUEST"),
                ("repair_response.json","REPAIR_RESPONSE"),
                ("repair_action.json","REPAIR_ACTION"),
                ("repair_boundary_result.json","REPAIR_BOUNDARY_RESULT"),
            ):
                obj=read_json(ba,bm,name)
                intervention_refs.append(add("I","B:"+name,obj,kind,sha256=h(read_raw(ba,bm,name))))
            b_seal=read_json(ba,bm,"seal.json")
            seal_ref=add("B","seal.json",b_seal,"B_EXECUTION_SEAL")
            b_result=read_json(ba,bm,"post_repair_result.json")
            b_summary={k:v for k,v in b_result.items() if k not in ("history","trace")}
            b_summary_ref=add("B","post_repair_result.json",b_summary,"B_RUN_SUMMARY")
            b_route_refs=[]
            for i,row in enumerate(route_rows(b_result),1):
                seq=row_sequence(row,i)
                ref=add("B",f"post_repair_result.json#route[{i}]",row,
                        "B_ROUTE_NODE",sequence=seq,notes="POST_REPAIR_CONTINUATION")
                b_route_refs.append(ref)

            # Raw semantic/carrier surfaces, excluding monitor verdict surfaces.
            def add_semantic_files(ar,mm,arm,skip):
                for name in sorted(mm):
                    low=name.lower()
                    if name in skip:
                        continue
                    if any(tok in low for tok in PRIMARY_EXCLUDE):
                        continue
                    if "/application/" in low:
                        continue
                    if not any(tok in low for tok in SEMANTIC_TOKENS):
                        continue
                    m=mm[name]
                    if m.size>262144:
                        continue
                    raw=read_raw(ar,mm,name)
                    txt,obj=maybe_json(raw)
                    if txt is None:
                        continue
                    if name.endswith(".jsonl"):
                        for ln,line in enumerate(txt.splitlines(),1):
                            if not line.strip():
                                continue
                            try:
                                val=json.loads(line)
                            except Exception:
                                val=line
                            seq=val.get("sequence") if isinstance(val,dict) else None
                            add(arm,f"{name}#L{ln}",val,
                                f"{arm}_RAW_SEMANTIC_OR_CARRIER_EVENT",sequence=seq,sha256=h(raw))
                            if len(json.dumps(ev,ensure_ascii=False,separators=(",",":")))>MAX_PACKET_CHARS:
                                return
                    else:
                        add(arm,name,obj if obj is not None else txt,
                            f"{arm}_RAW_SEMANTIC_OR_CARRIER_STATE",sha256=h(raw))
                    if len(json.dumps(ev,ensure_ascii=False,separators=(",",":")))>MAX_PACKET_CHARS:
                        return

            add_semantic_files(aa,am,"A",{
                "natural_A_result.json","repair_packages.json","monitor_evidence.json",
                "monitor_candidates.json","runtime_bridge.json","seal.json",
            })
            add_semantic_files(ba,bm,"B",set(required_b)|{
                "post_repair_monitor_evidence.json","post_repair_monitor_candidates.json",
                "post_repair_runtime_bridge.json","post_repair_watch.json",
            })

            # Repository-state comparisons from same parent to each arm's final checkpoint.
            parent_files=parent.get("application_file_hashes") or {}
            a_cps=checkpoint_manifests(aa,am,"checkpoints/")
            b_cps=checkpoint_manifests(ba,bm,"post_repair_checkpoints/")
            a_final=a_cps[-1] if a_cps else None
            b_final=b_cps[-1] if b_cps else None

            repo_diff={"parent_checkpoint_hash":parent_hash,"parent_event_ref":parent.get("event_ref"),
                       "parent_sequence":parent_seq,"A":None,"B":None}
            for label,entry,ar,mm,arm in (
                ("A",a_final,aa,am,"A"),
                ("B",b_final,ba,bm,"B"),
            ):
                if not entry:
                    continue
                _,manifest_path,manifest=entry
                final_files=manifest.get("application_file_hashes") or {}
                changed=sorted(k for k in set(parent_files)|set(final_files) if parent_files.get(k)!=final_files.get(k))
                snaps=[]
                for rel in changed[:16]:
                    before=app_snapshot(aa,am,parent_path,rel)
                    after=app_snapshot(ar,mm,manifest_path,rel)
                    snaps.append({"relative_path":rel,"parent":before,"final":after})
                repo_diff[label]={
                    "final_manifest_path":manifest_path,
                    "final_checkpoint_hash":manifest.get("checkpoint_hash"),
                    "final_event_ref":manifest.get("event_ref"),
                    "final_sequence":manifest.get("model_decision_sequence"),
                    "changed_files":changed,
                    "hash_transitions":{k:{"parent":parent_files.get(k),"final":final_files.get(k)} for k in changed},
                    "snapshots":snaps,
                }
                add(arm,f"{manifest_path}#repository_diff",repo_diff[label],
                    f"{arm}_REPOSITORY_DIFF",sequence=manifest.get("model_decision_sequence"),
                    sha256=manifest.get("checkpoint_hash"))

            packet={
                "schema":"stage2-r7-g1-ab-process-semantic-packet-v1",
                "cell_id":cell,"x_id":x,"task_id":t,
                "system_condition":SYSTEMS[x],"task_family":TASKS[t],
                "source_evidence_commit":cfg["source"]["evidence_commit"],
                "source_A_workflow_run":cfg["source"]["natural_A_workflow_run"],
                "source_B_workflow_run":cfg["source"]["repair_B_workflow_run"],
                "pair_integrity":{
                    "same_parent_checkpoint":True,
                    "parent_checkpoint_hash":parent_hash,
                    "parent_event_ref":parent.get("event_ref"),
                    "parent_model_decision_sequence":parent_seq,
                    "selected_package_id":package["package_id"],
                    "selected_package_hash":package.get("package_hash"),
                    "one_B_per_cell":True,
                    "B_runner_exit_code":b_receipt["runner_exit_code"],
                    "B_seal_status":b_receipt["seal_status"],
                    "B_repair_action_count":b_receipt["repair_action_count"],
                    "B_repair_agent_calls":b_receipt["repair_agent_calls"],
                    "B_subject_continuation_calls":b_receipt["subject_continuation_calls"],
                    "B_total_provider_calls":b_receipt["total_B_provider_calls"],
                },
                "isolation":{
                    "prior_layer_c_labels_read":False,
                    "prior_layer_b_reference_labels_read":False,
                    "monitor_predictions_read":False,
                    "monitor_candidate_labels_read":False,
                    "repair_package_visible_posthoc":True,
                    "actual_repair_action_visible_posthoc":True,
                },
                "intervention":{
                    "package_ref":pkg_ref,
                    "parent_ref":parent_ref,
                    "repair_anchor_ref":package.get("repair_anchor_ref"),
                    "detection_surface":package.get("detection_surface"),
                    "affected_closure_refs":package.get("affected_closure_refs"),
                    "preserve_refs":package.get("preserve_refs"),
                    "allowed_repair_surface":package.get("allowed_repair_surface"),
                    "intervention_evidence_refs":intervention_refs,
                },
                "arm_A":{
                    "attempt_receipt":a_receipt,
                    "summary_ref":a_summary_ref,
                    "route_refs":a_route_refs,
                    "repository_diff":repo_diff["A"],
                },
                "arm_B":{
                    "attempt_receipt":b_receipt,
                    "summary_ref":b_summary_ref,
                    "route_refs":b_route_refs,
                    "execution_seal_ref":seal_ref,
                    "repository_diff":repo_diff["B"],
                },
                "evidence":ev,
            }
            packet["packet_sha256"]=""
            packet["packet_sha256"]=stable_hash(packet)
            out_path=out/f"{cell}.json"
            out_path.write_text(json.dumps(packet,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
            index.append({
                "cell_id":cell,"packet_path":out_path.name,
                "packet_sha256":packet["packet_sha256"],
                "evidence_count":len(ev),
                "A_route_nodes":len(a_route_refs),
                "B_route_nodes":len(b_route_refs),
                "parent_checkpoint_hash":parent_hash,
                "package_id":package["package_id"],
            })

    assert len(index)==12
    packet_index={
        "schema":"stage2-r7-g1-ab-process-semantic-packet-index-v1",
        "status":"FROZEN_PRIMARY_A_B_AUDIT_INPUTS",
        "authorization_issue":cfg["authorization_issue"],
        "source_evidence_commit":cfg["source"]["evidence_commit"],
        "cell_count":12,
        "cells":index,
        "isolation":cfg["primary_audit_isolation"],
        "new_subject_provider_calls":0,
        "repair_calls":0,
        "paid_evaluator_calls":0,
    }
    (out/"packet_index.json").write_text(json.dumps(packet_index,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":"PASS","cells":12,
        "evidence_items":sum(x["evidence_count"] for x in index),
        "A_route_nodes":sum(x["A_route_nodes"] for x in index),
        "B_route_nodes":sum(x["B_route_nodes"] for x in index),
    },sort_keys=True))

if __name__=="__main__":
    main()
