#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from adapters.deepseek_chat import chat_completion, extract_content

TOPOLOGY={
 "NO_LOOP","TWO_DIMENSION_CROSSING","TRI_DIMENSION_OPEN_CHAIN",
 "TRI_DIMENSION_CLOSED_LOOP","REPEATED_CLOSED_LOOP","SELF_REINFORCING_LOOP",
 "DECAYING_LOOP","BOUNDARY_TERMINATED_LOOP","UNRESOLVED"
}
DIMS={"C","P","R"}
EVENT_STATUS={"SUPPORTED","SUPPORTED_CANDIDATE","NOT_ESTABLISHED","NEGATIVE_BOUNDARY"}
EDGE_STATUS={"SUPPORTED","SUPPORTED_CANDIDATE","NOT_ESTABLISHED"}
NODE_ROLES={"SOURCE","CARRIER","READ","ADOPTION","TRANSFORMATION","DECISION","ACTION","CONSEQUENCE","REVIEW","REENTRY","CLOSURE","BOUNDARY"}
RELATIONS={"READ","ADOPTION","SEMANTIC_TRANSFORMATION","DESCENDANT_INHERITANCE","DECISION_APPLICATION","CONSTRAINS","ENABLES","REENTRY","FINALIZATION","BOUNDARY_PRESERVATION","NOT_ESTABLISHED"}
TRANSITIONS={"C_DRIVES_P","P_REINFORCES_C","R_REOPENS_C","R_REOPENS_P","R_GENERATES_NEW_C","R_GENERATES_NEW_P","P_CREATES_RETROSPECTIVE_SURFACE","C_SURVIVES_INTO_RETROSPECTIVE_WINDOW","OTHER_EVIDENCE_BACKED_TRANSITION"}
AXES={"SEMANTIC_AUTHORITY","COLLABORATION_EXECUTION_SCOPE","TEMPORAL_REACH"}
AXIS_STATUS={"INCREASED","DECREASED","STABLE","NOT_ESTABLISHED"}

def digest(raw:bytes)->str: return hashlib.sha256(raw).hexdigest()

def parse_json_text(text):
    text=text.strip()
    try: return json.loads(text)
    except Exception:
        marker=chr(96)*3
        for part in text.split(marker):
            p=part.strip()
            if p.startswith("json"): p=p[4:].strip()
            try: return json.loads(p)
            except Exception: pass
        raise

def add_usage(dst,src):
    for k,v in (src or {}).items():
        if isinstance(v,(int,float)) and not isinstance(v,bool):
            dst[k]=dst.get(k,0)+v

def cost_usd(usage,cfg):
    p=cfg["pricing_snapshot_usd_per_million_tokens"]["peak"]
    hit=float(usage.get("prompt_cache_hit_tokens",0) or 0)
    miss=float(usage.get("prompt_cache_miss_tokens",0) or 0)
    prompt=float(usage.get("prompt_tokens",0) or 0)
    out=float(usage.get("completion_tokens",0) or 0)
    if hit+miss<=0: miss=prompt
    return (hit*p["input_cache_hit"]+miss*p["input_cache_miss"]+out*p["output"])/1_000_000

def require_refs(values,allowed,label):
    for ref in values or []:
        if ref not in allowed: raise ValueError(f"{label}: invented evidence ref {ref}")

def validate(obj,packet):
    if not isinstance(obj,dict): raise ValueError("cell audit must be object")
    if obj.get("schema")!="stage2-full-context-cell-audit-v1": raise ValueError("schema mismatch")
    if obj.get("group_id")!=packet["group_id"] or obj.get("cell_id")!=packet["cell_id"]: raise ValueError("cell identity mismatch")
    allowed={x["ref"] for x in packet["evidence"]}
    rs=obj.get("route_summary") or {}
    if rs.get("complete_observed_route_reconstructed") is not True: raise ValueError("complete observed route not affirmed")

    nodes=obj.get("semantic_nodes")
    if not isinstance(nodes,list) or not nodes: raise ValueError("semantic_nodes required")
    node_ids=[n.get("node_id") for n in nodes]
    if None in node_ids or len(node_ids)!=len(set(node_ids)): raise ValueError("semantic node ids invalid")
    node_set=set(node_ids)
    for n in nodes:
        if n.get("role") not in NODE_ROLES: raise ValueError("bad node role")
        require_refs(n.get("evidence_refs"),allowed,"semantic_node")

    edges=obj.get("semantic_edges") or []
    edge_ids=[]
    for e in edges:
        edge_ids.append(e.get("edge_id"))
        if e.get("from_node") not in node_set or e.get("to_node") not in node_set: raise ValueError("semantic edge node missing")
        if e.get("relation_type") not in RELATIONS: raise ValueError("bad semantic relation")
        if e.get("status") not in EVENT_STATUS: raise ValueError("bad semantic edge status")
        require_refs(e.get("evidence_refs"),allowed,"semantic_edge")
    if None in edge_ids or len(edge_ids)!=len(set(edge_ids)): raise ValueError("semantic edge ids invalid")

    events=obj.get("cpr_events") or []
    event_ids=[e.get("event_id") for e in events]
    if None in event_ids or len(event_ids)!=len(set(event_ids)): raise ValueError("CPR event ids invalid")
    event_set=set(event_ids)
    event_dim={}
    supported_dims=set()
    for e in events:
        dim=e.get("dimension")
        if dim not in DIMS: raise ValueError("bad CPR dimension")
        if e.get("status") not in EVENT_STATUS: raise ValueError("bad CPR status")
        event_dim[e["event_id"]]=dim
        if e.get("status") in {"SUPPORTED","SUPPORTED_CANDIDATE"}: supported_dims.add(dim)
        for nr in e.get("semantic_node_refs") or []:
            if nr not in node_set: raise ValueError("CPR event semantic node missing")
        require_refs(e.get("evidence_refs"),allowed,"cpr_event")

    transitions=obj.get("cpr_transitions") or []
    transition_pairs=set()
    for tr in transitions:
        if tr.get("from_event") not in event_set or tr.get("to_event") not in event_set: raise ValueError("transition event missing")
        if tr.get("edge_type") not in TRANSITIONS: raise ValueError("bad transition type")
        if tr.get("status") not in EDGE_STATUS: raise ValueError("bad transition status")
        require_refs(tr.get("evidence_refs"),allowed,"cpr_transition")
        if tr.get("status")=="SUPPORTED":
            transition_pairs.add((tr["from_event"],tr["to_event"]))

    topo=obj.get("dynamic_topology") or {}
    klass=topo.get("topology_class")
    if klass not in TOPOLOGY: raise ValueError("bad topology class")
    dims=set(topo.get("dimensions_present") or [])
    if not dims<=DIMS: raise ValueError("bad dimensions_present")
    if dims!=supported_dims: raise ValueError(f"dimensions_present drift: {dims} != {supported_dims}")
    order=topo.get("loop_event_order") or []
    for eid in order:
        if eid not in event_set: raise ValueError("loop references missing CPR event")
    closed=bool(topo.get("closed_loop"))
    repeated=bool(topo.get("repeated_loop"))
    reinforcing=bool(topo.get("self_reinforcing"))
    decaying=bool(topo.get("decaying"))
    traversals=int(topo.get("closed_traversal_count") or 0)
    if klass=="NO_LOOP" and closed: raise ValueError("NO_LOOP cannot be closed")
    if klass=="TRI_DIMENSION_OPEN_CHAIN" and (closed or dims!=DIMS): raise ValueError("bad tri open chain")
    if klass in {"TRI_DIMENSION_CLOSED_LOOP","REPEATED_CLOSED_LOOP","SELF_REINFORCING_LOOP"}:
        if not closed or dims!=DIMS: raise ValueError("tri/strong loop requires C,P,R and closure")
    if closed:
        if len(order)<4: raise ValueError("closed loop order too short")
        if event_dim[order[0]]!=event_dim[order[-1]]: raise ValueError("closed loop lacks return dimension")
        for a,b in zip(order,order[1:]):
            if (a,b) not in transition_pairs:
                raise ValueError(f"closed loop edge not SUPPORTED: {a}->{b}")
    if repeated and traversals<2: raise ValueError("repeated loop requires >=2 traversals")
    if klass=="REPEATED_CLOSED_LOOP" and not repeated: raise ValueError("repeated class requires repeated_loop")
    axes=topo.get("reinforcement_axes") or []
    increased=False; decreased=False
    for ax in axes:
        if ax.get("axis") not in AXES or ax.get("status") not in AXIS_STATUS: raise ValueError("bad reinforcement axis")
        require_refs(ax.get("evidence_refs"),allowed,"reinforcement_axis")
        increased |= ax.get("status")=="INCREASED"
        decreased |= ax.get("status")=="DECREASED"
    if reinforcing and (not closed or not increased): raise ValueError("self reinforcement requires closed loop + increased axis")
    if klass=="SELF_REINFORCING_LOOP" and not reinforcing: raise ValueError("self-reinforcing class mismatch")
    if decaying and not decreased: raise ValueError("decay requires decreased axis")
    if topo.get("boundary_ref") is not None and topo["boundary_ref"] not in allowed: raise ValueError("bad boundary ref")

    for alt in obj.get("healthy_alternatives") or []:
        require_refs(alt.get("evidence_refs"),allowed,"healthy_alternative")
    if not isinstance(obj.get("not_established"),list): raise ValueError("not_established must be list")
    return obj

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--packets",required=True)
    ap.add_argument("--prompt",required=True)
    ap.add_argument("--model-config",required=True)
    ap.add_argument("--authorization",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    pd=Path(a.packets); out=Path(a.out)
    out.mkdir(parents=True,exist_ok=True)
    (out/"cells").mkdir(exist_ok=True); (out/"provider_raw_cells").mkdir(exist_ok=True)
    prompt=Path(a.prompt).read_text()
    cfg=json.loads(Path(a.model_config).read_text())
    auth=json.loads(Path(a.authorization).read_text())
    assert auth["status"]=="AUTHORIZED_ACTIVE_FORWARD_ANALYSIS"
    assert auth["inputs"]["monitor_runtime_bundle_access"] is False
    assert auth["inputs"]["blind_reference_prerequisite"]["labels_read"] is False
    assert auth["prohibited_actions"]["subject_calls"] is False
    assert auth["prohibited_actions"]["repair_calls"] is False
    ix=json.loads((pd/"packet_index.json").read_text())
    assert ix["eligible_cell_count"]==80
    assert ix["blind_reference_labels_read"] is False and ix["monitor_runtime_bundle_read"] is False

    max_spend=float(auth["evaluator"]["max_spend_usd"])
    usage={}; calls=0; completed=[]; errors=[]
    for meta in ix["cells"]:
        packet=json.loads((pd/meta["packet_path"]).read_text())
        if packet["packet_sha256"]!=meta["packet_sha256"]: raise SystemExit("packet hash mismatch")
        full=meta["full_id"]
        target=out/"cells"/f"{full}.json"
        raw_target=out/"provider_raw_cells"/f"{full}.json"
        if target.is_file():
            prior=json.loads(target.read_text())
            validate(prior["audit"],packet)
            if prior.get("packet_sha256")!=packet["packet_sha256"]: raise SystemExit("resume packet mismatch")
            rawmeta=json.loads(raw_target.read_text()) if raw_target.is_file() else {}
            add_usage(usage,rawmeta.get("usage") or {}); calls+=int(rawmeta.get("provider_call_count",0) or 0)
            completed.append({"full_id":full,"resumed":True,"packet_sha256":packet["packet_sha256"],
                              "topology_class":prior["audit"]["dynamic_topology"]["topology_class"]})
            print(json.dumps({"cell":full,"resumed":True,"cost_usd":round(cost_usd(usage,cfg),6)},sort_keys=True),flush=True)
            continue
        try:
            if cost_usd(usage,cfg)>=max_spend: raise RuntimeError("hard spend ceiling reached")
            response=chat_completion(
                cfg,
                [{"role":"system","content":prompt},{"role":"user","content":json.dumps(packet,ensure_ascii=False,separators=(",",":"))}],
                evaluator=True,response_format_json=True
            )
            raw=extract_content(response)
            audit=validate(parse_json_text(raw),packet)
            n=1+int(response.get("_json_format_retry_count",0) or 0)
            calls+=n; add_usage(usage,response.get("usage") or {})
            if cost_usd(usage,cfg)>max_spend: raise RuntimeError("hard spend ceiling exceeded")
            wrapper={
              "schema":"stage2-full-context-cell-audit-record-v1",
              "full_id":full,"group_id":packet["group_id"],"cell_id":packet["cell_id"],
              "packet_sha256":packet["packet_sha256"],"audit_manifest_sha256":packet["audit_manifest_sha256"],
              "theory_aware":True,"monitor_runtime_bundle_read":False,"blind_reference_labels_read":False,
              "audit":audit,
              "provider":{"model":response.get("model"),"provider_call_count":n}
            }
            target.write_text(json.dumps(wrapper,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
            raw_target.write_text(json.dumps({
              "model":response.get("model"),"response_id":response.get("id"),
              "usage":response.get("usage") or {},"provider_call_count":n,
              "json_format_retry_count":n-1,"raw_text":raw
            },ensure_ascii=False,indent=2,sort_keys=True)+"\n")
            completed.append({"full_id":full,"resumed":False,"packet_sha256":packet["packet_sha256"],
                              "topology_class":audit["dynamic_topology"]["topology_class"]})
            print(json.dumps({"cell":full,"topology":audit["dynamic_topology"]["topology_class"],
                              "cost_usd":round(cost_usd(usage,cfg),6)},sort_keys=True),flush=True)
        except Exception as exc:
            errors.append({"full_id":full,"error":repr(exc),"packet_sha256":packet["packet_sha256"]})
            break

    summary={
      "schema":"stage2-full-context-cell-audit-summary-v1",
      "requested_cells":80,"completed_cells":len(completed),"errors":errors,
      "provider_call_count":calls,"aggregate_usage":usage,"estimated_cost_usd_peak":cost_usd(usage,cfg),
      "max_spend_usd":max_spend,"theory_aware":True,
      "monitor_runtime_bundle_read":False,"blind_reference_labels_read":False,
      "subject_calls":0,"subject_reruns":0,"repair_calls":0,"monitor_evaluation":False,
      "prompt_sha256":digest(prompt.encode()),"packet_index_sha256":digest((pd/"packet_index.json").read_bytes()),
      "cells":completed
    }
    (out/"cell_audit_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"completed_cells":len(completed),"provider_call_count":calls,
                      "estimated_cost_usd_peak":summary["estimated_cost_usd_peak"]},sort_keys=True))
    if errors or len(completed)!=80: raise SystemExit("full-context cell audit incomplete; partial outputs preserved")

if __name__=="__main__": main()
