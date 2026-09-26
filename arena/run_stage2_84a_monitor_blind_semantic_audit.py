#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from adapters.deepseek_chat import chat_completion, extract_content

STRUCTURES={"SCOPE_EXPANSION","STATE_MISMATCH","HISTORICAL_REENTRY","REPEATED_REVIEW_REOPEN","AUTHORITY_STATUS_SHIFT","RECURSIVE_MEMORY_FEEDBACK","CARRIER_TRANSFORMATION","SEMANTIC_REPOSITORY_CLOSURE_DIVERGENCE","OTHER_FROZEN_STRUCTURAL_SIGNATURE"}
STATUSES={"SUPPORTED","SUPPORTED_CANDIDATE","NOT_ESTABLISHED","NEGATIVE_BOUNDARY"}
RELATIONS={"MERE_VISIBILITY","READ","ADOPTION","SEMANTIC_TRANSFORMATION","DESCENDANT_INHERITANCE","DECISION_APPLICATION","CONSTRAINS","ENABLES","REENTRY","FINALIZATION","BOUNDARY_PRESERVATION","NOT_ESTABLISHED",None}
CPR={"C","P","R"}

def digest(b): return hashlib.sha256(b).hexdigest()

def parse_json_text(s):
    s=s.strip()
    try:
        return json.loads(s)
    except Exception:
        marker=chr(96)*3
        for p in s.split(marker):
            p=p.strip()
            if p.startswith("json"): p=p[4:].strip()
            try: return json.loads(p)
            except Exception: pass
        raise

def add_usage(dst,src):
    for k,v in (src or {}).items():
        if isinstance(v,(int,float)) and not isinstance(v,bool): dst[k]=dst.get(k,0)+v

def cost(usage,cfg):
    p=cfg["pricing_snapshot_usd_per_million_tokens"]["peak"]
    hit=float(usage.get("prompt_cache_hit_tokens",0) or 0)
    miss=float(usage.get("prompt_cache_miss_tokens",0) or 0)
    prompt=float(usage.get("prompt_tokens",0) or 0)
    out=float(usage.get("completion_tokens",0) or 0)
    if hit+miss<=0: miss=prompt
    return (hit*p["input_cache_hit"]+miss*p["input_cache_miss"]+out*p["output"])/1_000_000

def validate(obj,allowed):
    if not isinstance(obj,dict) or not isinstance(obj.get("cell_summary"),dict) or not isinstance(obj.get("references"),list):
        raise ValueError("bad top-level audit object")
    if not obj["references"] or len(obj["references"])>8:
        raise ValueError("reference count must be 1..8")
    for i,r in enumerate(obj["references"],1):
        if r.get("structure_family") not in STRUCTURES: raise ValueError(f"bad structure family {i}")
        if r.get("claim_status") not in STATUSES: raise ValueError(f"bad claim status {i}")
        if r.get("relation_type") not in RELATIONS: raise ValueError(f"bad relation {i}")
        dims=r.get("cpr_dimensions",[])
        if not isinstance(dims,list) or not set(dims)<=CPR or len(dims)!=len(set(dims)):
            raise ValueError(f"bad CPR {i}")
        ev=r.get("evidence_refs")
        if not isinstance(ev,list) or not ev or any(x not in allowed for x in ev):
            raise ValueError(f"bad evidence refs {i}")
        for k in ("source_ref","carrier_ref","decision_or_action_ref","consequence_ref"):
            if r.get(k) is not None and r.get(k) not in allowed:
                raise ValueError(f"invented {k} {i}")
        if len(dims)>1 and not r.get("cross_penetration_path"):
            raise ValueError(f"missing cross path {i}")
        if r.get("claim_status")=="SUPPORTED" and r.get("evidence_surface_available") is not True:
            raise ValueError(f"supported without surface {i}")
    return obj

def normalize(group,cell,route,i,r):
    keys=("structure_family","claim_status","source_ref","carrier_ref","semantic_before","semantic_after","semantic_delta","producer_actor","reader_or_adopter_actor","relation_type","decision_or_action_ref","consequence_ref","first_observable_sequence","first_consequence_sequence","cross_penetration_path","closure_state")
    out={"reference_id":f"{group}-{cell}-REF-{i:02d}","group_id":group,"cell_id":cell,"complete_route_ref":route}
    for k in keys: out[k]=r.get(k)
    out["cpr_dimensions"]=r.get("cpr_dimensions",[])
    out["evidence_surface_required"]=r.get("evidence_surface_required") or []
    out["evidence_surface_available"]=bool(r.get("evidence_surface_available"))
    out["negative_case"]=bool(r.get("negative_case"))
    out["not_established_fields"]=r.get("not_established_fields") or []
    out["evidence_refs"]=r["evidence_refs"]
    return out

def missing(packet):
    return {
      "cell_summary":{
        "closure_state":"PRESERVED_TERMINATION_WITHOUT_AUDIT_RAW_MANIFEST",
        "audit_coverage":"TERMINATION_ONLY",
        "termination_class":"PRESERVED_RUNNER_OR_PROVIDER_TERMINATION",
        "positive_structure_count":0,
        "negative_boundary_count":0,
        "notes":"No audit-raw bundle was sealed; semantic lineage is not reconstructed."
      },
      "references":[{
        "structure_family":"OTHER_FROZEN_STRUCTURAL_SIGNATURE",
        "claim_status":"NOT_ESTABLISHED",
        "source_ref":"E0001","carrier_ref":None,
        "semantic_before":None,"semantic_after":None,"semantic_delta":None,
        "producer_actor":None,"reader_or_adopter_actor":None,
        "relation_type":"NOT_ESTABLISHED",
        "decision_or_action_ref":None,"consequence_ref":None,
        "first_observable_sequence":None,"first_consequence_sequence":None,
        "cpr_dimensions":[],"cross_penetration_path":None,
        "closure_state":"PRESERVED_TERMINATION_WITHOUT_AUDIT_RAW_MANIFEST",
        "evidence_surface_required":["audit_raw_bundle"],
        "evidence_surface_available":False,"negative_case":False,
        "not_established_fields":["semantic_lineage","cpr_dimensions","cross_penetration"],
        "evidence_refs":["E0001"]
      }]
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--packets",required=True)
    ap.add_argument("--prompt",required=True)
    ap.add_argument("--model-config",required=True)
    ap.add_argument("--authorization",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    pd=Path(a.packets)
    out=Path(a.out)
    out.mkdir(parents=True,exist_ok=True)
    (out/"cell_audits").mkdir(exist_ok=True)
    (out/"provider_raw").mkdir(exist_ok=True)

    prompt=Path(a.prompt).read_text()
    cfg=json.loads(Path(a.model_config).read_text())
    auth=json.loads(Path(a.authorization).read_text())

    assert auth["status"]=="AUTHORIZED_BY_USER_CHAT_EXECUTE"
    assert auth["blindness"]["monitor_runtime_bundle_access"] is False
    assert auth["prohibited_actions"]["subject_calls"] is False
    assert auth["prohibited_actions"]["repair_calls"] is False
    max_spend=float(auth["evaluator"]["max_spend_usd"])

    ix=json.loads((pd/"packet_index.json").read_text())
    assert ix["cell_count"]==84 and ix["monitor_runtime_bundle_read"] is False

    usage={}
    calls=0
    allrefs=[]
    cells=[]
    errors=[]

    for meta in ix["cells"]:
        group,cell=meta["group_id"],meta["cell_id"]
        packet=json.loads((pd/meta["packet_path"]).read_text())
        assert packet["packet_sha256"]==meta["packet_sha256"]
        allowed={e["ref"] for e in packet["evidence"]}
        try:
            if packet["audit_manifest_missing"]:
                obj=missing(packet)
                rawmeta={"model":None,"usage":{},"provider_call_count":0,"raw_text":None}
            else:
                if cost(usage,cfg)>=max_spend:
                    raise RuntimeError("hard spend ceiling reached")
                resp=chat_completion(
                    cfg,
                    [
                        {"role":"system","content":prompt},
                        {"role":"user","content":json.dumps(packet,ensure_ascii=False,separators=(",",":"))}
                    ],
                    evaluator=True,
                    response_format_json=True
                )
                raw=extract_content(resp)
                obj=validate(parse_json_text(raw),allowed)
                n=1+int(resp.get("_json_format_retry_count",0) or 0)
                calls+=n
                add_usage(usage,resp.get("usage") or {})
                if cost(usage,cfg)>max_spend:
                    raise RuntimeError("hard spend ceiling exceeded")
                rawmeta={
                    "model":resp.get("model"),
                    "response_id":resp.get("id"),
                    "usage":resp.get("usage") or {},
                    "provider_call_count":n,
                    "json_format_retry_count":n-1,
                    "raw_text":raw
                }

            validate(obj,allowed)
            refs=[normalize(group,cell,packet["route_ref"],i,r) for i,r in enumerate(obj["references"],1)]
            audit={
                "schema":"stage2-84a-cell-semantic-audit-v1",
                "group_id":group,
                "cell_id":cell,
                "packet_sha256":packet["packet_sha256"],
                "audit_manifest_sha256":packet["audit_manifest_sha256"],
                "monitor_blind":True,
                "monitor_runtime_bundle_read":False,
                "cell_summary":obj["cell_summary"],
                "reference_records":refs,
                "provider":{"model":rawmeta.get("model"),"provider_call_count":rawmeta.get("provider_call_count",0)}
            }
            (out/"cell_audits"/f"{group}-{cell}.json").write_text(
                json.dumps(audit,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
            )
            (out/"provider_raw"/f"{group}-{cell}.json").write_text(
                json.dumps(rawmeta,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
            )
            allrefs.extend(refs)
            cells.append({
                "group_id":group,
                "cell_id":cell,
                "packet_sha256":packet["packet_sha256"],
                "audit_manifest_sha256":packet["audit_manifest_sha256"],
                "audit_manifest_missing":packet["audit_manifest_missing"],
                "reference_count":len(refs)
            })
            print(json.dumps({
                "cell":f"{group}-{cell}",
                "refs":len(refs),
                "cost_usd":round(cost(usage,cfg),6)
            },sort_keys=True),flush=True)
        except Exception as exc:
            errors.append({
                "group_id":group,
                "cell_id":cell,
                "error":repr(exc),
                "packet_sha256":packet["packet_sha256"]
            })
            break

    with (out/"reference_records.jsonl").open("w") as f:
        for r in allrefs:
            f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n")

    summary={
        "schema":"stage2-84a-semantic-audit-run-summary-v1",
        "requested_cells":84,
        "completed_cells":len(cells),
        "reference_records":len(allrefs),
        "errors":errors,
        "aggregate_usage":usage,
        "provider_call_count":calls,
        "estimated_cost_usd_peak":cost(usage,cfg),
        "max_spend_usd":max_spend,
        "monitor_blind":True,
        "monitor_runtime_bundle_read":False,
        "subject_calls":0,
        "subject_reruns":0,
        "repair_calls":0,
        "monitor_evaluation":False,
        "prompt_sha256":digest(prompt.encode()),
        "packet_index_sha256":digest((pd/"packet_index.json").read_bytes()),
        "cells":cells
    }
    (out/"audit_run_summary.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    )
    print(json.dumps({
        k:summary[k]
        for k in ("completed_cells","reference_records","provider_call_count","estimated_cost_usd_peak")
    },sort_keys=True))
    if errors or len(cells)!=84:
        raise SystemExit("semantic audit incomplete; partial outputs preserved")

if __name__=="__main__":
    main()
