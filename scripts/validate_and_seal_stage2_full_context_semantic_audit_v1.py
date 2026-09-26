#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter,defaultdict
from pathlib import Path

def sha(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--packets",required=True)
    ap.add_argument("--audit",required=True)
    ap.add_argument("--authorization",required=True)
    ap.add_argument("--blind-seal",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    pd=Path(a.packets); ad=Path(a.audit); out=Path(a.out)
    cfg=json.loads(Path(a.authorization).read_text())
    pidx=json.loads((pd/"packet_index.json").read_text())
    cellsum=json.loads((ad/"cell_audit_summary.json").read_text())
    xtsum=json.loads((ad/"xt_synthesis_summary.json").read_text())
    blind=json.loads(Path(a.blind_seal).read_text())

    assert blind["status"]=="SEALED"
    assert blind["monitor_blind"] is True
    assert cfg["population"]["eligible_full_context"]==80
    assert pidx["eligible_cell_count"]==80
    assert pidx["monitor_runtime_bundle_read"] is False
    assert pidx["blind_reference_labels_read"] is False
    assert cellsum["completed_cells"]==80 and not cellsum["errors"]
    assert xtsum["completed_cohorts"]==21 and not xtsum["errors"]
    assert cellsum["monitor_runtime_bundle_read"] is False and cellsum["blind_reference_labels_read"] is False
    assert xtsum["monitor_runtime_bundle_read"] is False and xtsum["blind_reference_labels_read"] is False
    assert cellsum["subject_calls"]==0 and cellsum["subject_reruns"]==0 and cellsum["repair_calls"]==0
    assert xtsum["subject_calls"]==0 and xtsum["subject_reruns"]==0 and xtsum["repair_calls"]==0
    reserve=float((cfg.get("validator_recovery") or {}).get("unaccounted_prevalidation_call_reserve_usd",0) or 0)
    effective_ceiling=float(cfg["evaluator"]["max_spend_usd"])-reserve
    assert xtsum["estimated_cost_usd_peak_total"]<=effective_ceiling

    packet_by={x["full_id"]:x for x in pidx["cells"]}
    assert len(packet_by)==80
    cell_files=sorted((ad/"cells").glob("G*-X*-T*.json"))
    assert len(cell_files)==80
    topology=Counter(); dims=Counter(); event_status=Counter(); transition_status=Counter()
    by_group=Counter(); by_xt=Counter()
    closed=[]; repeated=[]; reinforcing=[]; decaying=[]; terminated=[]
    reinforcement_axes=Counter()
    event_count=0; transition_count=0; semantic_nodes=0; semantic_edges=0
    for p in cell_files:
        row=json.loads(p.read_text())
        full=row["full_id"]; assert full in packet_by
        assert row["packet_sha256"]==packet_by[full]["packet_sha256"]
        assert row["monitor_runtime_bundle_read"] is False and row["blind_reference_labels_read"] is False
        audit=row["audit"]; topo=audit["dynamic_topology"]
        klass=topo["topology_class"]; topology[klass]+=1
        by_group[row["group_id"]]+=1; by_xt[row["cell_id"]]+=1
        semantic_nodes+=len(audit.get("semantic_nodes") or [])
        semantic_edges+=len(audit.get("semantic_edges") or [])
        events=audit.get("cpr_events") or []; transitions=audit.get("cpr_transitions") or []
        event_count+=len(events); transition_count+=len(transitions)
        for ev in events:
            event_status[(ev["dimension"],ev["status"])]+=1
            if ev["status"] in {"SUPPORTED","SUPPORTED_CANDIDATE"}: dims[ev["dimension"]]+=1
        for tr in transitions: transition_status[(tr["edge_type"],tr["status"])]+=1
        if topo.get("closed_loop"): closed.append(full)
        if topo.get("repeated_loop"): repeated.append(full)
        if topo.get("self_reinforcing"):
            reinforcing.append(full)
            for ax in topo.get("reinforcement_axes") or []:
                if ax.get("status")=="INCREASED": reinforcement_axes[ax["axis"]]+=1
        if topo.get("decaying"): decaying.append(full)
        if topo.get("boundary_terminated"): terminated.append(full)
    assert all(v>=3 for v in by_xt.values()), by_xt
    assert sum(by_group.values())==80

    cohort_files=sorted((ad/"xt_cohorts").glob("X*-T*.json"))
    assert len(cohort_files)==21
    recurrent=Counter()
    for p in cohort_files:
        row=json.loads(p.read_text())
        assert row["monitor_runtime_bundle_read"] is False and row["blind_reference_labels_read"] is False
        for mech in row["synthesis"].get("recurring_mechanism_families") or []:
            recurrent[mech["status"]]+=1

    summary={
      "schema":"stage2-full-context-dynamic-cpr-topology-summary-v1",
      "population_total_natural":84,
      "full_context_eligible":80,
      "excluded_boundary_cells":cfg["population"]["excluded_boundary_cells"],
      "xt_cohorts":21,
      "semantic_node_count":semantic_nodes,
      "semantic_edge_count":semantic_edges,
      "cpr_event_count":event_count,
      "cpr_transition_count":transition_count,
      "topology_class_counts":dict(sorted(topology.items())),
      "supported_or_candidate_event_dimension_counts":dict(sorted(dims.items())),
      "event_status_counts":{f"{k[0]}::{k[1]}":v for k,v in sorted(event_status.items())},
      "transition_status_counts":{f"{k[0]}::{k[1]}":v for k,v in sorted(transition_status.items())},
      "closed_loop_cells":closed,
      "repeated_loop_cells":repeated,
      "self_reinforcing_loop_cells":reinforcing,
      "decaying_loop_cells":decaying,
      "boundary_terminated_loop_cells":terminated,
      "self_reinforcement_axis_counts":dict(sorted(reinforcement_axes.items())),
      "cohort_mechanism_status_counts":dict(sorted(recurrent.items())),
      "counts_are_descriptive_not_prevalence_claims":True,
      "fixed_cpr_order_required":False
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"dynamic_cpr_topology_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n")

    index={
      "schema":"stage2-full-context-process-semantic-audit-index-v1",
      "status":"SEALED_FULL_CONTEXT_PROCESS_SEMANTIC_AUDIT",
      "natural_population":84,
      "full_context_cells":80,
      "xt_cohorts":21,
      "theory_aware":True,
      "monitor_runtime_bundle_read":False,
      "blind_reference_labels_read":False,
      "blind_reference_mutated":False,
      "natural_evidence_mutated":False,
      "subject_calls":0,"subject_reruns":0,"repair_calls":0,"monitor_evaluation":False,
      "provider_call_count_total":xtsum["provider_call_count_total"],
      "estimated_cost_usd_peak_total":xtsum["estimated_cost_usd_peak_total"],
      "recovery_budget_reserve_usd":reserve,
      "effective_tracked_spend_ceiling_usd":effective_ceiling,
      "known_unaccounted_prevalidation_provider_calls":int((cfg.get("validator_recovery") or {}).get("known_unaccounted_prevalidation_provider_calls",0) or 0),
      "packet_index_sha256":sha(pd/"packet_index.json"),
      "cell_audit_summary_sha256":sha(ad/"cell_audit_summary.json"),
      "xt_synthesis_summary_sha256":sha(ad/"xt_synthesis_summary.json"),
      "blind_reference_seal_sha256":sha(Path(a.blind_seal)),
      "dynamic_cpr_topology_summary_sha256":sha(out/"dynamic_cpr_topology_summary.json"),
      "reference_role":"MECHANISM_RECONSTRUCTION_NOT_PRIMARY_MONITOR_REFERENCE"
    }
    (out/"full_context_index.json").write_text(json.dumps(index,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    seal={
      "schema":"stage2-full-context-process-semantic-audit-seal-v1",
      "status":"SEALED",
      "full_context_index_sha256":sha(out/"full_context_index.json"),
      "dynamic_cpr_topology_summary_sha256":sha(out/"dynamic_cpr_topology_summary.json"),
      "experimental_general_chapter_state":"READY",
      "three_way_comparison_state":"READY_AFTER_PRIMARY_MONITOR_EVALUATION_FOR_MONITOR_JOINS",
      "primary_monitor_evaluation_state":"STILL_SEPARATE_NOT_EXECUTED_BY_THIS_SEAL",
      "engineering_B_state":"LOCKED_UNTIL_PRIMARY_MONITOR_EVALUATION_SEALED"
    }
    (out/"full_context_seal.json").write_text(json.dumps(seal,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "status":"PASS","cells":80,"cohorts":21,"cpr_events":event_count,
      "closed_loops":len(closed),"repeated_loops":len(repeated),
      "self_reinforcing_loops":len(reinforcing),"cost_usd_peak":xtsum["estimated_cost_usd_peak_total"]
    },sort_keys=True))

if __name__=="__main__": main()
