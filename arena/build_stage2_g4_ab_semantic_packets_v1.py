#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    from checkpoint_chronology import ordered_checkpoints
else:
    from arena.checkpoint_chronology import ordered_checkpoints

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
MAX_ARM_RAW_CHARS=180000
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

def read_raw(ar,mm,name):
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

def semantic_projection(value:Any,max_items:int=120):
    out=[]; seen=set()
    priority={"content","message","answer","instruction","reason","summary","goal","kind","action","type","role","from","to","sent_from","send_to","path","target","target_ref","name","profile","latest_observed_msg"}
    def walk(v,path="",depth=0):
        if len(out)>=max_items or depth>10:
            return
        if isinstance(v,dict):
            if any(k in v for k in ("content","message","answer","instruction","reason")):
                small={}
                for k,val in v.items():
                    if k in priority and isinstance(val,(str,int,float,bool,type(None),list,dict)):
                        small[k]=clip(val,1800)
                if small:
                    key=json.dumps(small,ensure_ascii=False,sort_keys=True)
                    if key not in seen:
                        seen.add(key); out.append({"path":path or "$","record":small})
            for k,val in v.items():
                if k in priority or isinstance(val,(dict,list)):
                    walk(val,f"{path}.{k}" if path else str(k),depth+1)
        elif isinstance(v,list):
            for i,val in enumerate(v[:80]):
                walk(val,f"{path}[{i}]",depth+1)
        elif isinstance(v,str) and v.strip():
            text=clip(v,1800); key=(path,text)
            if key not in seen:
                seen.add(key); out.append({"path":path or "$","text":text})
    walk(value)
    return out

def route_rows(result):
    rows=result.get("history")
    if isinstance(rows,list): return rows
    rows=result.get("trace")
    return rows if isinstance(rows,list) else []

def row_sequence(row,fallback):
    if isinstance(row,dict):
        for key in ("model_decision_sequence","sequence","turn","round"):
            if isinstance(row.get(key),int):
                return row[key]
    return fallback

def checkpoint_manifests(ar,mm,prefix):
    return ordered_checkpoints(ar,mm,prefix)

def app_snapshot(ar,mm,manifest_path,rel):
    name=manifest_path.rsplit("/manifest.json",1)[0]+"/application/"+rel
    if name not in mm: return None
    raw=read_raw(ar,mm,name)
    if len(raw)>65536:
        return {"path":name,"sha256":h(raw),"content":None,"bytes":len(raw)}
    try: txt=raw.decode("utf-8")
    except UnicodeDecodeError:
        return {"path":name,"sha256":h(raw),"content":None,"bytes":len(raw)}
    return {"path":name,"sha256":h(raw),"content":clip(txt,6000),"bytes":len(raw)}

def selected_package(a_ar,a_mm,package_id):
    rows=read_json(a_ar,a_mm,"repair_packages.json")
    matches=[x for x in rows if x.get("package_id")==package_id]
    if len(matches)!=1:
        raise RuntimeError(f"selected package {package_id} not unique")
    return matches[0]

def add_semantic_files(ar,mm,arm,add,skip):
    arm_chars=0
    for name in sorted(mm):
        low=name.lower()
        if name in skip or any(tok in low for tok in PRIMARY_EXCLUDE) or "/application/" in low:
            continue
        if not any(tok in low for tok in SEMANTIC_TOKENS):
            continue
        m=mm[name]
        if m.size>1048576:
            continue
        raw=read_raw(ar,mm,name)
        txt,obj=maybe_json(raw)
        if txt is None:
            continue
        if name.endswith(".jsonl"):
            for ln,line in enumerate(txt.splitlines(),1):
                if not line.strip(): continue
                try: val=json.loads(line)
                except Exception: val=line
                seq=val.get("sequence") if isinstance(val,dict) else None
                rendered=clip(val,2600)
                if arm_chars+len(rendered)>MAX_ARM_RAW_CHARS:
                    return
                add(arm,f"{name}#L{ln}",val,f"{arm}_RAW_SEMANTIC_OR_CARRIER_EVENT",sequence=seq,sha256=h(raw))
                arm_chars+=len(rendered)
        else:
            if obj is not None and ("native_state" in low or "model_context" in low or "ledger" in low):
                projected=semantic_projection(obj)
                if not projected: continue
                value={"source_sha256":h(raw),"projection":projected}
                kind=f"{arm}_RAW_SEMANTIC_STATE_PROJECTION"
            elif obj is not None:
                if low.endswith("/manifest.json"):
                    value={k:obj.get(k) for k in (
                        "checkpoint_hash","event_ref","model_decision_sequence","remaining_horizon",
                        "external_carrier_refs","application_state_sha256","native_state_sha256",
                        "model_visible_context_sha256"
                    ) if k in obj}
                else:
                    value=obj
                kind=f"{arm}_RAW_SEMANTIC_OR_CARRIER_STATE"
            else:
                value=txt; kind=f"{arm}_RAW_SEMANTIC_OR_CARRIER_STATE"
            rendered=clip(value,6000)
            if arm_chars+len(rendered)>MAX_ARM_RAW_CHARS:
                continue
            add(arm,name,value,kind,sha256=h(raw))
            arm_chars+=len(rendered)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--a-root",required=True)
    ap.add_argument("--b-root",required=True)
    ap.add_argument("--config",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()

    aroot=Path(args.a_root)
    broot=Path(args.b_root)
    cfg=json.loads(Path(args.config).read_text())
    attempted=cfg["population"]["attempted_cells"]
    paired=cfg["population"]["valid_paired_cells"]
    boundaries=cfg["population"]["execution_boundary_cells"]
    assert len(attempted)==12 and len(paired)==11 and boundaries==["X5-T2"]

    gbase=broot/"stage2/replication_v2/G4/engineering_B_v1"
    abase=aroot/"stage2/replication_v2/G4/natural_A"
    gidx=json.loads((gbase/"group_index.json").read_text())
    gseal=json.loads((gbase/"group_seal.json").read_text())
    assert gidx["state"]=="FROZEN_FIRST_B_ATTEMPTS"
    assert gseal["state"]=="SEALED_FIRST_B_ATTEMPTS"
    assert gidx["preserved_count"]==12
    assert gidx["successful_B_count"]==11
    assert gidx["failed_B_count"]==1
    assert gidx["failed_B_cells"]==boundaries
    assert gidx["automatic_retries"]==0
    assert gidx["natural_A_reruns"]==0
    assert gidx["semantic_audit_gate"]=="OPEN_AFTER_ALL_B_FROZEN"
    b_by={x["cell_id"]:x for x in gidx["receipts"]}

    selection=json.loads((Path("stage2/replication_v2/engineering_eligibility_84_v1/G4_b_selection_index.json")).read_text())
    assert selection["eligible_cell_count"]==12
    sel_by={x["cell_id"]:x for x in selection["cells"]}

    out=Path(args.out)
    packets=out/"packets"
    boundary_dir=out/"execution_boundaries"
    packets.mkdir(parents=True,exist_ok=False)
    boundary_dir.mkdir(parents=True,exist_ok=False)
    index=[]

    for cell in paired:
        x,t=cell.split("-",1)
        a_dir=abase/cell
        b_dir=gbase/"cells"/cell
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

        sel=sel_by[cell]
        assert b_receipt["package_id"]==sel["selected_package_id"]
        assert b_receipt["parent_checkpoint_hash"]==sel["selected_parent_checkpoint_hash"]

        ev=[]; counters={"A":0,"B":0,"I":0,"P":0}
        def add(arm,path,value,kind,sequence=None,sha256=None,notes=None):
            counters[arm]+=1
            ref=f"{arm}{counters[arm]:04d}"
            item={"ref":ref,"arm":arm,"path":path,"kind":kind,"sequence":sequence,"sha256":sha256,"content":clip(value)}
            if notes: item["notes"]=notes
            ev.append(item); return ref

        add("P","G4/engineering_B_v1/group_index.json",
            {k:gidx.get(k) for k in ("state","source_workflow_run","b_code_sha","one_B_per_cell","automatic_retries","post_repair_monitor_mode","semantic_audit_gate")},
            "PAIR_PROVENANCE",sha256=stable_hash(gidx))
        add("A",f"stage2/replication_v2/G4/natural_A/{cell}/attempt_receipt.json",a_receipt,"A_ATTEMPT_RECEIPT")
        add("B",f"stage2/replication_v2/G4/engineering_B_v1/cells/{cell}/attempt_receipt.json",b_receipt,"B_ATTEMPT_RECEIPT")

        with tarfile.open(fileobj=io.BytesIO(a_arc),mode="r:gz") as aa, tarfile.open(fileobj=io.BytesIO(b_arc),mode="r:gz") as ba:
            am=members(aa); bm=members(ba)
            package=selected_package(aa,am,sel["selected_package_id"])
            assert package["package_hash"]==sel["selected_package_hash"]
            parent_hash=sel["selected_parent_checkpoint_hash"]
            parent_path=f"checkpoints/{parent_hash}/manifest.json"
            if parent_path not in am:
                raise RuntimeError(f"{cell}: parent manifest missing")
            parent=read_json(aa,am,parent_path)
            assert parent["checkpoint_hash"]==parent_hash
            assert parent["restore_capability"]=="FULL_NATIVE"

            pkg_ref=add("I","A:repair_packages.json#selected",package,"FROZEN_SELECTED_REPAIR_PACKAGE",
                        sequence=package.get("prefix_sequence"),sha256=package.get("package_hash"),
                        notes="Posthoc-visible intervention package; selection was frozen before B without semantic audit.")
            parent_ref=add("P","A:"+parent_path,parent,"SAME_PARENT_CHECKPOINT",
                           sequence=parent.get("model_decision_sequence"),sha256=parent_hash)
            parent_order=next(row[2]["_chronology"] for row in checkpoint_manifests(aa,am,"checkpoints/") if row[2]["checkpoint_hash"]==parent_hash)
            if parent_order["clock"]!="model_decision_sequence":
                raise RuntimeError("Natural-A parent requires a frozen ledger decision clock")
            parent_seq=parent_order["sequence"]

            a_result=read_json(aa,am,"natural_A_result.json")
            a_summary={k:v for k,v in a_result.items() if k not in ("history","trace")}
            a_summary_ref=add("A","natural_A_result.json",a_summary,"A_RUN_SUMMARY")
            a_route_refs=[]
            for i,row in enumerate(route_rows(a_result),1):
                seq=row_sequence(row,i)
                a_route_refs.append(add("A",f"natural_A_result.json#route[{i}]",row,"A_ROUTE_NODE",sequence=seq,
                                        notes="FROZEN_A_ROUTE_CONTEXT_PARENT_BOUND_BY_CHECKPOINT_HASH"))

            required_b=("repair_request.json","repair_response.json","repair_action.json","repair_boundary_result.json","post_repair_result.json","seal.json")
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
                b_route_refs.append(add("B",f"post_repair_result.json#route[{i}]",row,"B_ROUTE_NODE",sequence=seq,notes="POST_REPAIR_CONTINUATION"))

            add_semantic_files(aa,am,"A",add,{"natural_A_result.json","repair_packages.json","monitor_evidence.json","monitor_candidates.json","runtime_bridge.json","seal.json"})
            add_semantic_files(ba,bm,"B",add,set(required_b)|{"post_repair_monitor_evidence.json","post_repair_monitor_candidates.json","post_repair_runtime_bridge.json","post_repair_watch.json"})

            parent_files=parent.get("application_file_hashes") or {}
            a_final=(checkpoint_manifests(aa,am,"checkpoints/") or [None])[-1]
            b_final=(checkpoint_manifests(ba,bm,"post_repair_checkpoints/") or [None])[-1]
            repo_diff={"parent_checkpoint_hash":parent_hash,"parent_event_ref":parent.get("event_ref"),"parent_sequence":parent_seq,"A":None,"B":None}
            for label,entry,ar,mm,arm in (("A",a_final,aa,am,"A"),("B",b_final,ba,bm,"B")):
                if not entry: continue
                _,manifest_path,manifest=entry
                final_files=manifest.get("application_file_hashes") or {}
                changed=sorted(k for k in set(parent_files)|set(final_files) if parent_files.get(k)!=final_files.get(k))
                snaps=[]
                for rel in changed[:16]:
                    snaps.append({"relative_path":rel,"parent":app_snapshot(aa,am,parent_path,rel),"final":app_snapshot(ar,mm,manifest_path,rel)})
                repo_diff[label]={
                    "final_manifest_path":manifest_path,
                    "final_checkpoint_hash":manifest.get("checkpoint_hash"),
                    "final_event_ref":manifest.get("event_ref"),
                    "final_sequence":manifest["_chronology"]["sequence"],
                    "final_chronology":manifest["_chronology"],
                    "changed_files":changed,
                    "hash_transitions":{k:{"parent":parent_files.get(k),"final":final_files.get(k)} for k in changed},
                    "snapshots":snaps,
                }
                add(arm,f"{manifest_path}#repository_diff",repo_diff[label],f"{arm}_REPOSITORY_DIFF",
                    sequence=manifest["_chronology"]["sequence"],sha256=manifest.get("checkpoint_hash"))

            packet={
                "schema":"stage2-g4-ab-process-semantic-packet-v1",
                "group_id":"G4","cell_id":cell,"x_id":x,"task_id":t,
                "system_condition":SYSTEMS[x],"task_family":TASKS[t],
                "source_A_evidence_commit":cfg["source"]["natural_A_evidence_commit"],
                "source_B_evidence_commit":cfg["source"]["repair_B_evidence_commit"],
                "source_A_workflow_run":cfg["source"]["natural_A_cell_workflow_run"][cell],
                "source_B_workflow_run":cfg["source"]["repair_B_workflow_run"],
                "pair_integrity":{
                    "same_parent_checkpoint":True,
                    "parent_checkpoint_hash":parent_hash,
                    "parent_event_ref":parent.get("event_ref"),
                    "parent_model_decision_sequence":parent_seq,
                    "selected_package_id":package["package_id"],
                    "selected_package_hash":package.get("package_hash"),
                    "one_B_per_cell":True,
                    "B_runner_exit_code":0,
                    "B_seal_status":"REPAIR_B_FROZEN",
                    "B_repair_action_count":1,
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
                    "package_ref":pkg_ref,"parent_ref":parent_ref,
                    "repair_anchor_ref":package.get("repair_anchor_ref"),
                    "detection_surface":package.get("detection_surface"),
                    "affected_closure_refs":package.get("affected_closure_refs"),
                    "preserve_refs":package.get("preserve_refs"),
                    "allowed_repair_surface":package.get("allowed_repair_surface"),
                    "intervention_evidence_refs":intervention_refs,
                },
                "arm_A":{"attempt_receipt":a_receipt,"summary_ref":a_summary_ref,"route_refs":a_route_refs,"repository_diff":repo_diff["A"]},
                "arm_B":{"attempt_receipt":b_receipt,"summary_ref":b_summary_ref,"route_refs":b_route_refs,"execution_seal_ref":seal_ref,"repository_diff":repo_diff["B"]},
                "evidence":ev,
            }
            packet["packet_sha256"]=""
            packet["packet_sha256"]=stable_hash(packet)
            p=packets/f"{cell}.json"
            p.write_text(json.dumps(packet,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
            index.append({"cell_id":cell,"packet_path":p.name,"packet_sha256":packet["packet_sha256"],"evidence_count":len(ev),
                          "A_route_nodes":len(a_route_refs),"B_route_nodes":len(b_route_refs),
                          "parent_checkpoint_hash":parent_hash,"package_id":package["package_id"]})

    # Preserve the failed first B attempt as a separate execution-boundary record.
    cell="X5-T2"; sel=sel_by[cell]; a_dir=abase/cell; b_dir=gbase/"cells"/cell
    a_receipt=json.loads((a_dir/"attempt_receipt.json").read_text())
    b_receipt=json.loads((b_dir/"attempt_receipt.json").read_text())
    assert b_receipt["runner_exit_code"]==1 and b_receipt["seal_present"] is False
    b_arc=(b_dir/"first_B_attempt.tar.gz").read_bytes()
    assert h(b_arc)==b_receipt["archive_sha256"]
    extracted={}
    with tarfile.open(fileobj=io.BytesIO(b_arc),mode="r:gz") as ba:
        bm=members(ba)
        for name in sorted(bm):
            low=name.lower()
            if any(k in low for k in ("runner_stderr.txt","runner_stdout.txt","repair_request.json","repair_response.json","repair_action.json","repair_boundary_result.json")):
                raw=read_raw(ba,bm,name)
                txt,obj=maybe_json(raw)
                if txt is not None:
                    extracted[name]={"sha256":h(raw),"content":clip(obj if obj is not None else txt,12000)}
        names=sorted(bm)
    boundary={
        "schema":"stage2-g4-b-execution-boundary-v1",
        "group_id":"G4","cell_id":cell,
        "status":"B_EXECUTION_FAILURE_BOUNDARY",
        "role":"NOT_PAIRED_REPAIR_EFFECT_SAMPLE",
        "source_B_workflow_run":cfg["source"]["repair_B_workflow_run"],
        "source_B_evidence_commit":cfg["source"]["repair_B_evidence_commit"],
        "attempt_index":1,
        "B_rerun":False,
        "natural_A_rerun":False,
        "receipt":b_receipt,
        "selected_package_binding":sel,
        "archive_member_names":names,
        "diagnostic_surfaces":extracted,
        "not_imputed_as_repair_failure":True,
        "not_silently_excluded":True,
    }
    boundary["record_sha256"]=""
    boundary["record_sha256"]=stable_hash(boundary)
    (boundary_dir/f"{cell}.json").write_text(json.dumps(boundary,ensure_ascii=False,indent=2,sort_keys=True)+"\n")

    assert len(index)==11
    packet_index={
        "schema":"stage2-g4-ab-process-semantic-packet-index-v1",
        "status":"FROZEN_11_VALID_PAIRS_PLUS_1_EXECUTION_BOUNDARY",
        "authorization_issue":cfg["authorization_issue"],
        "source_A_evidence_commit":cfg["source"]["natural_A_evidence_commit"],
        "source_B_evidence_commit":cfg["source"]["repair_B_evidence_commit"],
        "attempted_cell_count":12,
        "paired_cell_count":11,
        "execution_boundary_count":1,
        "cells":index,
        "execution_boundary_path":"../execution_boundaries/X5-T2.json",
        "primary_audit_isolation":cfg["primary_audit_isolation"],
        "new_subject_provider_calls":0,
        "repair_calls":0,
        "paid_evaluator_calls":0,
        "natural_A_reruns":0,
        "B_reruns":0,
    }
    (packets/"packet_index.json").write_text(json.dumps(packet_index,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":"PASS","attempted":12,"paired":11,"execution_boundaries":1,
        "evidence_items":sum(x["evidence_count"] for x in index),
        "A_route_nodes":sum(x["A_route_nodes"] for x in index),
        "B_route_nodes":sum(x["B_route_nodes"] for x in index)
    },sort_keys=True))

if __name__=="__main__":
    main()
