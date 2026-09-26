#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json
from collections import Counter
from pathlib import Path

NODE_ROLES={"SOURCE","CARRIER","READ","ADOPTION","TRANSFORMATION","DECISION","ACTION","CONSEQUENCE","REVIEW","REENTRY","CLOSURE","BOUNDARY"}
RELATIONS={"MERE_VISIBILITY","READ","ADOPTION","SEMANTIC_TRANSFORMATION","DESCENDANT_INHERITANCE","DECISION_APPLICATION","CONSTRAINS","ENABLES","REENTRY","FINALIZATION","BOUNDARY_PRESERVATION","NOT_ESTABLISHED"}
STATUSES={"SUPPORTED","SUPPORTED_CANDIDATE","NOT_ESTABLISHED","NEGATIVE_BOUNDARY"}
TRANSITION_STATUS={"SUPPORTED","SUPPORTED_CANDIDATE","NOT_ESTABLISHED"}
DIMS={"C","P","R"}
TOPOLOGY={"NO_LOOP","TWO_DIMENSION_CROSSING","TRI_DIMENSION_OPEN_CHAIN","TRI_DIMENSION_CLOSED_LOOP","REPEATED_CLOSED_LOOP","SELF_REINFORCING_LOOP","DECAYING_LOOP","BOUNDARY_TERMINATED_LOOP","UNRESOLVED"}
TRANSITIONS={"C_DRIVES_P","P_REINFORCES_C","R_REOPENS_C","R_REOPENS_P","R_GENERATES_NEW_C","R_GENERATES_NEW_P","P_CREATES_RETROSPECTIVE_SURFACE","C_SURVIVES_INTO_RETROSPECTIVE_WINDOW","OTHER_EVIDENCE_BACKED_TRANSITION"}
AXES={"SEMANTIC_AUTHORITY","COLLABORATION_EXECUTION_SCOPE","TEMPORAL_REACH"}
AXIS_STATUS={"INCREASED","DECREASED","STABLE","NOT_ESTABLISHED"}

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def req_refs(values,allowed,label):
    if not isinstance(values,list) or not values:
        raise ValueError(f"{label}: evidence_refs must be non-empty")
    bad=[x for x in values if x not in allowed]
    if bad: raise ValueError(f"{label}: invented evidence refs {bad[:3]}")

def validate_cell(packet,audit):
    if audit.get("schema")!="stage2-gpt56sol-full-context-cell-audit-v1":
        raise ValueError("formal cell schema mismatch")
    reviewer=audit.get("reviewer") or {}
    expected={
      "model":"GPT-5.6 Sol",
      "execution_mode":"CHATGPT_NATIVE_REASONING",
      "monitor_runtime_bundle_read":False,
      "blind_reference_labels_read":False,
      "blind_reference_records_read":False,
      "deepseek_full_context_pilot_outputs_read":False
    }
    for k,v in expected.items():
        if reviewer.get(k)!=v: raise ValueError(f"reviewer isolation drift: {k}")
    for k in ("group_id","cell_id","x_id","task_id","system_condition"):
        if audit.get(k)!=packet.get(k): raise ValueError(f"identity mismatch: {k}")
    if audit.get("input_packet_sha256")!=packet.get("packet_sha256"):
        raise ValueError("packet sha mismatch")
    allowed={e["ref"] for e in packet.get("evidence") or []}
    route=audit.get("route_summary") or {}
    if route.get("complete_observed_route_reconstructed") is not True:
        raise ValueError("complete observed route not affirmed")

    nodes=audit.get("semantic_nodes")
    if not isinstance(nodes,list) or not nodes: raise ValueError("semantic_nodes required")
    node_ids=[n.get("node_id") for n in nodes]
    if None in node_ids or len(node_ids)!=len(set(node_ids)): raise ValueError("node ids invalid")
    node_set=set(node_ids)
    for n in nodes:
        if n.get("role") not in NODE_ROLES: raise ValueError(f"bad node role {n.get('role')!r}")
        req_refs(n.get("evidence_refs"),allowed,"semantic_node")

    edge_ids=[]
    for e in audit.get("semantic_edges") or []:
        edge_ids.append(e.get("edge_id"))
        if e.get("from_node") not in node_set or e.get("to_node") not in node_set:
            raise ValueError("semantic edge node missing")
        if e.get("relation_type") not in RELATIONS: raise ValueError(f"bad relation {e.get('relation_type')!r}")
        if e.get("status") not in STATUSES: raise ValueError("bad semantic edge status")
        req_refs(e.get("evidence_refs"),allowed,"semantic_edge")
    if None in edge_ids or len(edge_ids)!=len(set(edge_ids)): raise ValueError("edge ids invalid")

    events=audit.get("cpr_events") or []
    event_ids=[e.get("event_id") for e in events]
    if None in event_ids or len(event_ids)!=len(set(event_ids)): raise ValueError("event ids invalid")
    event_set=set(event_ids); event_dim={}; supported_dims=set()
    for e in events:
        if e.get("dimension") not in DIMS: raise ValueError("bad CPR dimension")
        if e.get("status") not in STATUSES: raise ValueError("bad CPR event status")
        event_dim[e["event_id"]]=e["dimension"]
        if e["status"] in {"SUPPORTED","SUPPORTED_CANDIDATE"}: supported_dims.add(e["dimension"])
        for n in e.get("semantic_node_refs") or []:
            if n not in node_set: raise ValueError("CPR event cites missing semantic node")
        req_refs(e.get("evidence_refs"),allowed,"cpr_event")

    supported_transition_pairs=set()
    for tr in audit.get("cpr_transitions") or []:
        if tr.get("from_event") not in event_set or tr.get("to_event") not in event_set:
            raise ValueError("CPR transition event missing")
        if tr.get("edge_type") not in TRANSITIONS: raise ValueError("bad transition type")
        if tr.get("status") not in TRANSITION_STATUS: raise ValueError("bad transition status")
        req_refs(tr.get("evidence_refs"),allowed,"cpr_transition")
        if tr["status"]=="SUPPORTED":
            supported_transition_pairs.add((tr["from_event"],tr["to_event"]))

    topo=audit.get("dynamic_topology") or {}
    klass=topo.get("topology_class")
    if klass not in TOPOLOGY: raise ValueError("bad topology class")
    dims=set(topo.get("dimensions_present") or [])
    if dims!=supported_dims: raise ValueError(f"dimensions_present drift: {dims} != {supported_dims}")
    order=topo.get("loop_event_order") or []
    for eid in order:
        if eid not in event_set: raise ValueError("topology cites missing CPR event")
    closed=bool(topo.get("closed_loop"))
    repeated=bool(topo.get("repeated_loop"))
    reinforcing=bool(topo.get("self_reinforcing"))
    decaying=bool(topo.get("decaying"))
    traversals=int(topo.get("closed_traversal_count") or 0)
    if klass=="NO_LOOP" and closed: raise ValueError("NO_LOOP cannot be closed")
    if klass=="TRI_DIMENSION_OPEN_CHAIN" and (closed or dims!=DIMS): raise ValueError("tri-dimensional open-chain mismatch")
    if klass in {"TRI_DIMENSION_CLOSED_LOOP","REPEATED_CLOSED_LOOP","SELF_REINFORCING_LOOP"}:
        if not closed or dims!=DIMS: raise ValueError("tri/strong loop requires C/P/R + closure")
    if closed:
        if len(order)<4: raise ValueError("closed loop event order too short")
        if event_dim[order[0]]!=event_dim[order[-1]]: raise ValueError("closed loop lacks return dimension")
        for a,b in zip(order,order[1:]):
            if (a,b) not in supported_transition_pairs:
                raise ValueError(f"closed-loop edge not SUPPORTED: {a}->{b}")
    if repeated and traversals<2: raise ValueError("repeated loop requires >=2 traversals")
    if klass=="REPEATED_CLOSED_LOOP" and not repeated: raise ValueError("repeated-loop class mismatch")
    increased=decreased=False
    for ax in topo.get("reinforcement_axes") or []:
        if ax.get("axis") not in AXES or ax.get("status") not in AXIS_STATUS: raise ValueError("bad reinforcement axis")
        req_refs(ax.get("evidence_refs"),allowed,"reinforcement_axis")
        increased |= ax["status"]=="INCREASED"
        decreased |= ax["status"]=="DECREASED"
    if reinforcing and (not closed or not increased): raise ValueError("self-reinforcement lacks supported growth")
    if klass=="SELF_REINFORCING_LOOP" and not reinforcing: raise ValueError("self-reinforcing class mismatch")
    if decaying and not decreased: raise ValueError("decay lacks decreased axis evidence")
    bref=topo.get("boundary_ref")
    if bref is not None and bref not in allowed: raise ValueError("bad topology boundary ref")
    for alt in audit.get("healthy_alternatives") or []:
        req_refs(alt.get("evidence_refs"),allowed,"healthy_alternative")
    if not isinstance(audit.get("not_established"),list): raise ValueError("not_established must be list")
    return audit

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--packet")
    ap.add_argument("--audit")
    ap.add_argument("--inputs")
    ap.add_argument("--audits")
    ap.add_argument("--seal-out")
    a=ap.parse_args()
    if a.packet and a.audit:
        packet=json.loads(Path(a.packet).read_text())
        audit=json.loads(Path(a.audit).read_text())
        validate_cell(packet,audit)
        print(json.dumps({"status":"PASS","cell":f'{audit["group_id"]}-{audit["cell_id"]}'},sort_keys=True))
        return
    if not (a.inputs and a.audits): raise SystemExit("provide --packet/--audit or --inputs/--audits")
    inputs=Path(a.inputs); audits=Path(a.audits)
    ix=json.loads((inputs/"packet_index.json").read_text())
    assert ix["eligible_cell_count"]==80
    rows=[]; topo=Counter(); dims=Counter()
    for meta in ix["cells"]:
        p=inputs/meta["packet_path"]
        full=meta["full_id"]
        out=audits/f"{full}.json"
        if not out.exists(): continue
        packet=json.loads(p.read_text()); audit=json.loads(out.read_text())
        validate_cell(packet,audit)
        rows.append({"full_id":full,"packet_sha256":packet["packet_sha256"],"audit_sha256":sha(out),"topology_class":audit["dynamic_topology"]["topology_class"]})
        topo[audit["dynamic_topology"]["topology_class"]]+=1
        for d in audit["dynamic_topology"].get("dimensions_present") or []: dims[d]+=1
    result={"schema":"stage2-gpt56sol-formal-cell-validation-v1","validated_cells":len(rows),"required_cells":80,"cells":rows,"topology_counts":dict(topo),"dimension_cell_counts":dict(dims)}
    print(json.dumps({"status":"PASS","validated_cells":len(rows)},sort_keys=True))
    if a.seal_out:
        if len(rows)!=80: raise SystemExit("refusing to seal before 80/80 formal cells validate")
        result["status"]="SEALED_80_CELL_FORMAL_LAYER_C"
        result["input_packet_index_sha256"]=sha(inputs/"packet_index.json")
        target=Path(a.seal_out); target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n")

if __name__=="__main__": main()
