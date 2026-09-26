#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

TOPOLOGY={"NO_LOOP","TWO_DIMENSION_CROSSING","TRI_DIMENSION_OPEN_CHAIN","TRI_DIMENSION_CLOSED_LOOP","REPEATED_CLOSED_LOOP","SELF_REINFORCING_LOOP","DECAYING_LOOP","BOUNDARY_TERMINATED_LOOP","UNRESOLVED"}
DIMS={"C","P","R"}
STATUSES={"SUPPORTED","SUPPORTED_CANDIDATE","NOT_ESTABLISHED","NEGATIVE_BOUNDARY"}
TRANSITION_STATUS={"SUPPORTED","SUPPORTED_CANDIDATE","NOT_ESTABLISHED"}
RELATIONS={"MERE_VISIBILITY","READ","ADOPTION","SEMANTIC_TRANSFORMATION","DESCENDANT_INHERITANCE","DECISION_APPLICATION","CONSTRAINS","ENABLES","REENTRY","FINALIZATION","BOUNDARY_PRESERVATION","NOT_ESTABLISHED"}
AXES={"SEMANTIC_AUTHORITY","COLLABORATION_EXECUTION_SCOPE","TEMPORAL_REACH"}

def require(cond,msg):
    if not cond: raise SystemExit("GPT56SOL_LAYER_C_VALIDATION_FAILED: "+msg)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--inputs",required=True)
    ap.add_argument("--audits",required=True)
    ap.add_argument("--expected-count",type=int,default=80)
    a=ap.parse_args()
    inp=Path(a.inputs); out=Path(a.audits)
    ix=json.loads((inp/"packet_index.json").read_text())
    require(ix["eligible_cell_count"]==a.expected_count,"input count mismatch")
    require(ix["monitor_runtime_bundle_read"] is False,"input monitor contamination")
    require(ix["blind_reference_labels_read"] is False,"input blind-label contamination")
    packets={r["full_id"]:r for r in ix["cells"]}
    files=sorted(out.glob("G*-X*-T*.json"))
    require(len(files)==a.expected_count,f"audit file count {len(files)} != {a.expected_count}")
    seen=set()
    topologies={}
    for p in files:
        row=json.loads(p.read_text())
        require(row["schema"]=="stage2-gpt56sol-full-context-cell-audit-v1",f"{p.name}: schema")
        reviewer=row["reviewer"]
        require(reviewer["model"]=="GPT-5.6 Sol",f"{p.name}: reviewer")
        require(reviewer["execution_mode"]=="CHATGPT_NATIVE_REASONING",f"{p.name}: execution mode")
        for key in ("monitor_runtime_bundle_read","blind_reference_labels_read","blind_reference_records_read","deepseek_full_context_pilot_outputs_read"):
            require(reviewer[key] is False,f"{p.name}: isolation {key}")
        full=f'{row["group_id"]}-{row["cell_id"]}'
        require(full in packets,f"{p.name}: not in frozen population")
        require(full not in seen,f"{p.name}: duplicate")
        seen.add(full)
        require(row["input_packet_sha256"]==packets[full]["packet_sha256"],f"{p.name}: packet hash")
        packet=json.loads((inp/packets[full]["packet_path"]).read_text())
        allowed={e["ref"] for e in packet["evidence"]}
        def refs(values,label):
            for ref in values or []:
                require(ref in allowed,f"{p.name}: {label} invented ref {ref}")
        nodes=row["semantic_nodes"]
        node_ids={n["node_id"] for n in nodes}
        require(len(node_ids)==len(nodes),f"{p.name}: node ids")
        for n in nodes: refs(n.get("evidence_refs"),"node")
        for e in row["semantic_edges"]:
            require(e["from_node"] in node_ids and e["to_node"] in node_ids,f"{p.name}: semantic edge node")
            require(e["relation_type"] in RELATIONS,f"{p.name}: relation")
            require(e["status"] in STATUSES,f"{p.name}: edge status")
            refs(e.get("evidence_refs"),"semantic edge")
        events=row["cpr_events"]
        event_ids={e["event_id"] for e in events}
        require(len(event_ids)==len(events),f"{p.name}: CPR event ids")
        event_dim={}
        supported_dims=set()
        for ev in events:
            require(ev["dimension"] in DIMS,f"{p.name}: CPR dimension")
            require(ev["status"] in STATUSES,f"{p.name}: CPR status")
            event_dim[ev["event_id"]]=ev["dimension"]
            if ev["status"] in {"SUPPORTED","SUPPORTED_CANDIDATE"}: supported_dims.add(ev["dimension"])
            refs(ev.get("evidence_refs"),"CPR event")
            for n in ev.get("semantic_node_refs") or []: require(n in node_ids,f"{p.name}: CPR node")
        supported_pairs=set()
        for tr in row["cpr_transitions"]:
            require(tr["from_event"] in event_ids and tr["to_event"] in event_ids,f"{p.name}: transition event")
            require(tr["status"] in TRANSITION_STATUS,f"{p.name}: transition status")
            refs(tr.get("evidence_refs"),"CPR transition")
            if tr["status"]=="SUPPORTED": supported_pairs.add((tr["from_event"],tr["to_event"]))
        topo=row["dynamic_topology"]
        klass=topo["topology_class"]
        require(klass in TOPOLOGY,f"{p.name}: topology")
        require(set(topo.get("dimensions_present") or [])==supported_dims,f"{p.name}: dimensions_present")
        order=topo.get("loop_event_order") or []
        for ev in order: require(ev in event_ids,f"{p.name}: loop event")
        closed=bool(topo.get("closed_loop"))
        repeated=bool(topo.get("repeated_loop"))
        reinforcing=bool(topo.get("self_reinforcing"))
        if closed:
            require(len(order)>=4,f"{p.name}: closed loop order")
            require(event_dim[order[0]]==event_dim[order[-1]],f"{p.name}: return dimension")
            for x,y in zip(order,order[1:]): require((x,y) in supported_pairs,f"{p.name}: unsupported loop edge {x}->{y}")
        if klass in {"TRI_DIMENSION_CLOSED_LOOP","REPEATED_CLOSED_LOOP","SELF_REINFORCING_LOOP"}:
            require(closed and supported_dims==DIMS,f"{p.name}: tri-loop prerequisites")
        if repeated: require(int(topo.get("closed_traversal_count") or 0)>=2,f"{p.name}: repeated loop count")
        increased=False; decreased=False
        for ax in topo.get("reinforcement_axes") or []:
            require(ax["axis"] in AXES,f"{p.name}: axis")
            refs(ax.get("evidence_refs"),"reinforcement axis")
            increased |= ax.get("status")=="INCREASED"
            decreased |= ax.get("status")=="DECREASED"
        if reinforcing: require(closed and increased,f"{p.name}: reinforcement prerequisites")
        if topo.get("decaying"): require(decreased,f"{p.name}: decay evidence")
        refs([topo["boundary_ref"]] if topo.get("boundary_ref") else [],"boundary")
        for alt in row["healthy_alternatives"]: refs(alt.get("evidence_refs"),"healthy alternative")
        topologies[klass]=topologies.get(klass,0)+1
    require(set(packets)==seen,"population coverage mismatch")
    print(json.dumps({"status":"PASS","audits":len(files),"topology_counts":topologies},sort_keys=True))

if __name__=="__main__": main()
