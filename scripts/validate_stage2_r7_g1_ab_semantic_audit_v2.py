#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

CPR={"SUPPORTED","SUPPORTED_CANDIDATE","NOT_ESTABLISHED","NEGATIVE_BOUNDARY"}
TOPO={"NO_LOOP","TWO_DIMENSION_CROSSING","TRI_DIMENSION_OPEN_CHAIN","TRI_DIMENSION_CLOSED_LOOP","REPEATED_CLOSED_LOOP","SELF_REINFORCING_LOOP","DECAYING_LOOP","BOUNDARY_TERMINATED_LOOP","UNRESOLVED"}
DIRECT={"REMOVED","REDUCED","PERSISTED","REGENERATED","REDIRECTED","NOT_ESTABLISHED","CENSORED"}
CHANGE={"DECREASED","STABLE","INCREASED","MIXED","NOT_ESTABLISHED"}
ROUTE={"DIVERGED","PARTIAL_DIVERGENCE","RECONVERGED","NEAR_IDENTICAL","CENSORED","NOT_ESTABLISHED"}
PRESERVE={"PRESERVED","PARTIALLY_PRESERVED","NOT_PRESERVED","NOT_ESTABLISHED"}
OVERALL={"TARGETED_SUPPRESSION","TARGETED_REDIRECTION","PERSISTENCE","REGENERATION","OVERCORRECTION_OR_SCOPE_DAMAGE","MIXED_EFFECT","INCONCLUSIVE"}
STATUS={"SUPPORTED","SUPPORTED_CANDIDATE","NOT_ESTABLISHED","NEGATIVE_BOUNDARY"}
NODE_ROLES={"SOURCE","CARRIER","READ","ADOPTION","TRANSFORMATION","DECISION","ACTION","CONSEQUENCE","REVIEW","REENTRY","CLOSURE","BOUNDARY"}
RELATIONS={"READ","ADOPTION","SEMANTIC_TRANSFORMATION","DESCENDANT_INHERITANCE","DECISION_APPLICATION","CONSTRAINS","ENABLES","REENTRY","FINALIZATION","BOUNDARY_PRESERVATION","NOT_ESTABLISHED"}

def req(cond,msg):
    if not cond:
        raise SystemExit("R7_G1_AB_SEMANTIC_VALIDATION_FAILED: "+msg)

def validate_packets(root:Path):
    idx=json.loads((root/"packet_index.json").read_text())
    req(idx["schema"]=="stage2-r7-g1-ab-process-semantic-packet-index-v2","packet index schema")
    req(idx["status"]=="FROZEN_BALANCED_PRIMARY_A_B_AUDIT_INPUTS","packet index state")
    req(idx["authorization_issue"]==287,"authorization")
    req(idx["source_evidence_commit"]=="c78d140b42f512abab41190163e3f2d8b0750c39","evidence commit")
    req(idx["cell_count"]==12 and len(idx["cells"])==12,"packet count")
    req(idx["new_subject_provider_calls"]==0 and idx["repair_calls"]==0 and idx["paid_evaluator_calls"]==0,"forbidden calls")
    expected=["X2-T1","X2-T2","X2-T3","X4-T1","X4-T2","X4-T3","X5-T1","X5-T2","X5-T3","X7-T1","X7-T2","X7-T3"]
    req([x["cell_id"] for x in idx["cells"]]==expected,"population/order")
    for x in idx["cells"]:
        p=root/x["packet_path"]
        row=json.loads(p.read_text())
        req(row["schema"]=="stage2-r7-g1-ab-process-semantic-packet-v2",f'{x["cell_id"]}: schema')
        req(row["cell_id"]==x["cell_id"],f'{x["cell_id"]}: identity')
        req(row["packet_sha256"]==x["packet_sha256"],f'{x["cell_id"]}: packet hash binding')
        pi=row["pair_integrity"]
        req(pi["same_parent_checkpoint"] is True,f'{x["cell_id"]}: same parent')
        req(pi["parent_checkpoint_hash"]==x["parent_checkpoint_hash"],f'{x["cell_id"]}: parent hash')
        req(pi["selected_package_id"]==x["package_id"],f'{x["cell_id"]}: package')
        req(pi["one_B_per_cell"] is True and pi["B_runner_exit_code"]==0,f'{x["cell_id"]}: B execution')
        req(pi["B_seal_status"]=="REPAIR_B_FROZEN" and pi["B_repair_action_count"]==1,f'{x["cell_id"]}: B seal/action')
        iso=row["isolation"]
        for k in ("prior_layer_c_labels_read","prior_layer_b_reference_labels_read","monitor_predictions_read","monitor_candidate_labels_read"):
            req(iso[k] is False,f'{x["cell_id"]}: isolation {k}')
        refs=[e["ref"] for e in row["evidence"]]
        req(len(refs)==len(set(refs)),f'{x["cell_id"]}: evidence refs unique')
        refset=set(refs)
        req(row["arm_A"]["summary_ref"] in refset and row["arm_B"]["summary_ref"] in refset,f'{x["cell_id"]}: summary refs')
        req(all(r in refset for r in row["arm_A"]["route_refs"]),f'{x["cell_id"]}: A route refs')
        req(all(r in refset for r in row["arm_B"]["route_refs"]),f'{x["cell_id"]}: B route refs')
        req(all(r in refset for r in row["intervention"]["intervention_evidence_refs"]),f'{x["cell_id"]}: intervention refs')
    return {"status":"PASS","packets":12}

def check_refs(values,allowed,label):
    for r in values or []:
        req(r in allowed,f"{label}: invented evidence ref {r}")

def validate_arm(arm,label,allowed):
    req(isinstance(arm.get("termination_class"),str),f"{label}: termination")
    req(isinstance(arm.get("closure_state"),str),f"{label}: closure")
    req(isinstance(arm.get("censored"),bool),f"{label}: censored")
    nodes=arm.get("semantic_nodes") or []
    ids={n["node_id"] for n in nodes}
    req(len(ids)==len(nodes),f"{label}: duplicate nodes")
    for n in nodes:
        req(n["role"] in NODE_ROLES,f"{label}: node role")
        check_refs(n.get("evidence_refs"),allowed,f"{label} node")
    for e in arm.get("semantic_edges") or []:
        req(e["from_node"] in ids and e["to_node"] in ids,f"{label}: edge node")
        req(e["relation_type"] in RELATIONS,f"{label}: relation")
        req(e["status"] in STATUS,f"{label}: edge status")
        check_refs(e.get("evidence_refs"),allowed,f"{label} edge")
    dims=arm.get("cpr_dimensions") or {}
    req(set(dims)=={"C","P","R"},f"{label}: CPR keys")
    req(all(v in CPR for v in dims.values()),f"{label}: CPR status")
    topo=arm.get("dynamic_topology") or {}
    req(topo.get("topology_class") in TOPO,f"{label}: topology")
    req(isinstance(topo.get("closed_loop"),bool),f"{label}: closed_loop")
    req(isinstance(topo.get("self_reinforcing"),bool),f"{label}: self_reinforcing")
    check_refs(arm.get("evidence_refs"),allowed,f"{label} summary")

def validate_audits(packet_root:Path,audit_root:Path):
    idx=json.loads((packet_root/"packet_index.json").read_text())
    packet_by={x["cell_id"]:x for x in idx["cells"]}
    files=sorted(audit_root.glob("X*-T*.json"))
    req(len(files)==12,f"audit count {len(files)}")
    seen=set()
    for p in files:
        a=json.loads(p.read_text())
        req(a["schema"]=="stage2-r7-g1-ab-paired-process-semantic-audit-v1",f"{p.name}: schema")
        rev=a["reviewer"]
        req(rev["model"]=="GPT-5.6 Sol" and rev["execution_mode"]=="CHATGPT_NATIVE_REASONING",f"{p.name}: reviewer")
        for k in ("prior_layer_c_labels_read","prior_layer_b_reference_labels_read","monitor_predictions_read"):
            req(rev[k] is False,f"{p.name}: isolation {k}")
        cell=a["cell_id"]
        req(cell in packet_by and cell not in seen,f"{p.name}: cell")
        seen.add(cell)
        req(a["input_packet_sha256"]==packet_by[cell]["packet_sha256"],f"{p.name}: packet hash")
        packet=json.loads((packet_root/packet_by[cell]["packet_path"]).read_text())
        allowed={e["ref"] for e in packet["evidence"]}
        pi=a["pair_integrity"]
        req(pi["same_parent_checkpoint"] is True and pi["one_repair_action"] is True,f"{p.name}: pair integrity")
        req(pi["repair_executor_exited"] is True and pi["B_rerun"] is False and pi["natural_A_rerun"] is False,f"{p.name}: rerun/executor")
        validate_arm(a["arm_A"],p.name+" A",allowed)
        validate_arm(a["arm_B"],p.name+" B",allowed)
        pe=a["paired_effect"]
        req(pe["direct_target_effect"] in DIRECT,f"{p.name}: direct target")
        req(pe["semantic_authority_change"] in CHANGE,f"{p.name}: semantic change")
        req(pe["collaboration_scope_change"] in CHANGE,f"{p.name}: scope change")
        req(pe["temporal_reach_change"] in CHANGE,f"{p.name}: temporal change")
        req(pe["route_relation"] in ROUTE,f"{p.name}: route relation")
        req(pe["unrelated_structure_preservation"] in PRESERVE,f"{p.name}: preservation")
        req(pe["overall_process_effect"] in OVERALL,f"{p.name}: overall")
        check_refs(pe.get("evidence_refs"),allowed,f"{p.name} paired effect")
        for f in a.get("cross_arm_findings") or []:
            req(f["status"] in STATUS,f"{p.name}: finding status")
            check_refs(f.get("evidence_refs"),allowed,f"{p.name} finding")
        for h in a.get("healthy_alternatives") or []:
            req(h["status"] in {"SUPPORTED","SUPPORTED_CANDIDATE","NOT_ESTABLISHED"},f"{p.name}: healthy status")
            check_refs(h.get("evidence_refs"),allowed,f"{p.name} healthy")
    req(set(packet_by)==seen,"audit population coverage")
    return {"status":"PASS","audits":12}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--packets",required=True)
    ap.add_argument("--audits")
    args=ap.parse_args()
    p=Path(args.packets)
    result=validate_packets(p)
    if args.audits:
        result.update(validate_audits(p,Path(args.audits)))
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
