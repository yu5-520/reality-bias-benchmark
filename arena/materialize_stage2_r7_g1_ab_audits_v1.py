#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path

JUDGMENTS = {
"X2-T1":{"direct":"NOT_ESTABLISHED","sem":"NOT_ESTABLISHED","scope":"NOT_ESTABLISHED","time":"STABLE","route":"PARTIAL_DIVERGENCE","preserve":"PRESERVED","overall":"INCONCLUSIVE","mech":"The repair reopened the unresolved verification state, but both arms reached the turn budget without repository change. B contains a small route change, yet the packet does not establish that the targeted process state was resolved rather than merely re-entered."},
"X2-T2":{"direct":"REDIRECTED","sem":"NOT_ESTABLISHED","scope":"DECREASED","time":"DECREASED","route":"DIVERGED","preserve":"PRESERVED","overall":"TARGETED_REDIRECTION","mech":"From the same frozen parent, the local checkout.py repair redirected the continuation away from the long multi-role natural suffix toward a short release-lead continuation. The natural arm changed the web layer, whereas B preserved the non-target set and ended after four continuation turns."},
"X2-T3":{"direct":"REDUCED","sem":"NOT_ESTABLISHED","scope":"DECREASED","time":"DECREASED","route":"DIVERGED","preserve":"PRESERVED","overall":"TARGETED_SUPPRESSION","mech":"The repair directly rewrote the legacy compatibility target while preserving the unrelated file set. Relative to the 64-turn natural suffix, B contracted to four continuation turns, supporting a local suppression effect on the legacy-route surface, although full semantic closure is not independently established."},
"X4-T1":{"direct":"PERSISTED","sem":"NOT_ESTABLISHED","scope":"STABLE","time":"STABLE","route":"PARTIAL_DIVERGENCE","preserve":"PRESERVED","overall":"PERSISTENCE","mech":"The process-state repair passed its boundary, but both arms remained turn-budget censored with no repository change. Route timing shifted, yet the unresolved action process remained observable through the terminal boundary."},
"X4-T2":{"direct":"REDIRECTED","sem":"NOT_ESTABLISHED","scope":"DECREASED","time":"DECREASED","route":"DIVERGED","preserve":"PRESERVED","overall":"TARGETED_REDIRECTION","mech":"Revalidating the shared file-list state was followed by a substantially shorter continuation that finalized after modifying the web payment-button path, whereas the natural arm exhausted its horizon without repository change. The preserved-set boundary remained intact."},
"X4-T3":{"direct":"PERSISTED","sem":"NOT_ESTABLISHED","scope":"MIXED","time":"STABLE","route":"PARTIAL_DIVERGENCE","preserve":"PRESERVED","overall":"MIXED_EFFECT","mech":"The repair changed routing composition toward reviewer/SRE activity but did not shorten the temporal horizon or produce a repository-state difference. The target therefore remained unresolved at the observable terminal boundary while the collaboration route reorganized."},
"X5-T1":{"direct":"PERSISTED","sem":"NOT_ESTABLISHED","scope":"STABLE","time":"STABLE","route":"NEAR_IDENTICAL","preserve":"PRESERVED","overall":"PERSISTENCE","mech":"Both natural and repaired arms exhausted the turn budget without valid route progress or repository mutation. The local process revision therefore did not produce an observable downstream resolution of the targeted unknown action state."},
"X5-T2":{"direct":"REDIRECTED","sem":"NOT_ESTABLISHED","scope":"DECREASED","time":"DECREASED","route":"PARTIAL_DIVERGENCE","preserve":"PRESERVED","overall":"TARGETED_REDIRECTION","mech":"The repaired continuation retained the task-relevant web changes but reached finalization earlier and with a narrower observed role set than the natural arm. This supports a route-level redirection after file-list revalidation rather than a whole-system reset."},
"X5-T3":{"direct":"REDUCED","sem":"NOT_ESTABLISHED","scope":"MIXED","time":"STABLE","route":"PARTIAL_DIVERGENCE","preserve":"PRESERVED","overall":"MIXED_EFFECT","mech":"The B intervention directly altered the frozen run.py target and preserved unrelated files, but the downstream process still consumed the full horizon. The local target changed while broader temporal inertia remained."},
"X7-T1":{"direct":"PERSISTED","sem":"NOT_ESTABLISHED","scope":"STABLE","time":"STABLE","route":"PARTIAL_DIVERGENCE","preserve":"PRESERVED","overall":"PERSISTENCE","mech":"The local process revision changed when a valid release-lead action appeared but did not change the full-horizon termination or repository state. The targeted unresolved action state therefore remained persistent at the observed process level."},
"X7-T2":{"direct":"REDUCED","sem":"NOT_ESTABLISHED","scope":"MIXED","time":"STABLE","route":"DIVERGED","preserve":"PRESERVED","overall":"MIXED_EFFECT","mech":"The repair directly modified the web/index.html target and changed the continuation route, but B still exhausted the full horizon. The target surface was reduced locally without demonstrating global process closure."},
"X7-T3":{"direct":"PERSISTED","sem":"NOT_ESTABLISHED","scope":"STABLE","time":"STABLE","route":"NEAR_IDENTICAL","preserve":"PRESERVED","overall":"PERSISTENCE","mech":"Both arms remained release-lead dominated, reached the turn budget, and produced no repository difference. The file-list process revision therefore did not yield an observable downstream break in the persistent route."}
}

def parse_content(e):
    value=e["content"]
    for _ in range(3):
        if not isinstance(value,str):
            break
        try:
            value=json.loads(value)
        except Exception:
            break
    return value

def first(row, kind):
    return next(e for e in row["evidence"] if e["kind"] == kind)

def arm_object(row, arm):
    summary = first(row, f"{arm}_RUN_SUMMARY")
    repo_ev = first(row, f"{arm}_REPOSITORY_DIFF")
    routes = [(e, parse_content(e)) for e in row["evidence"] if e["kind"] == f"{arm}_ROUTE_NODE"]
    valid = [(e,o) for e,o in routes if isinstance(o,dict) and o.get("valid") is True]
    nodes=[]
    if valid:
        e,o=valid[0]
        nodes.append({"node_id":f"{arm}-N01","sequence":e.get("sequence") or 0,"actor":o.get("role","unknown"),"role":"ACTION","semantic_state":f"First observable valid {arm} continuation action after the paired parent.","evidence_refs":[e["ref"]]})
        e2,o2=valid[-1]
        if e2["ref"] != e["ref"]:
            nodes.append({"node_id":f"{arm}-N02","sequence":e2.get("sequence") or 0,"actor":o2.get("role","unknown"),"role":"ACTION","semantic_state":f"Last observable valid {arm} continuation action before termination.","evidence_refs":[e2["ref"]]})
    repo = parse_content(repo_ev)
    nodes.append({"node_id":f"{arm}-N{len(nodes)+1:02d}","sequence":9998,"actor":"SYSTEM","role":"CONSEQUENCE","semantic_state":f"Repository consequence from parent: changed_files={json.dumps(repo.get('changed_files',[]),ensure_ascii=False)}.","evidence_refs":[repo_ev["ref"]]})
    summ = parse_content(summary)
    nodes.append({"node_id":f"{arm}-N{len(nodes)+1:02d}","sequence":9999,"actor":"SYSTEM","role":"BOUNDARY","semantic_state":f"Termination={summ.get('stop_reason','unknown')}; turns={summ.get('turns','unknown')}; answer_present={summ.get('answer') is not None}.","evidence_refs":[summary["ref"]]})
    refs=[]
    for n in nodes:
        for r in n["evidence_refs"]:
            if r not in refs: refs.append(r)
    return {
        "termination_class":summ.get("stop_reason","unknown"),
        "closure_state":"FINALIZED_OR_ANSWERED" if summ.get("answer") is not None else "OPEN_OR_CENSORED",
        "censored":summ.get("stop_reason") in {"turn_budget","round_guard"},
        "semantic_nodes":nodes,
        "semantic_edges":[],
        "cpr_dimensions":{"C":"NOT_ESTABLISHED","P":"NOT_ESTABLISHED","R":"NOT_ESTABLISHED"},
        "dynamic_topology":{"topology_class":"UNRESOLVED","closed_loop":False,"self_reinforcing":False,"notes":"The paired packet supports route/termination comparison but does not independently establish a closed CPR loop without importing prior semantic labels."},
        "key_lineage":"Observable execution route and repository consequence reconstructed from frozen arm evidence; hidden reasoning is not inferred.",
        "evidence_refs":refs
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--packets",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    packet_root=Path(args.packets)
    out=Path(args.out); out.mkdir(parents=True,exist_ok=False)
    idx=json.loads((packet_root/"packet_index.json").read_text())
    assert idx["status"]=="FROZEN_BALANCED_PRIMARY_A_B_AUDIT_INPUTS"
    assert idx["cell_count"]==12
    by={x["cell_id"]:x for x in idx["cells"]}
    results=[]
    for cell,j in JUDGMENTS.items():
        row=json.loads((packet_root/by[cell]["packet_path"]).read_text())
        assert row["packet_sha256"]==by[cell]["packet_sha256"]
        pkg_ev=first(row,"FROZEN_SELECTED_REPAIR_PACKAGE")
        resp_ev=first(row,"REPAIR_RESPONSE")
        action_ev=first(row,"REPAIR_ACTION")
        boundary_ev=first(row,"REPAIR_BOUNDARY_RESULT")
        a_summary=first(row,"A_RUN_SUMMARY"); b_summary=first(row,"B_RUN_SUMMARY")
        a_repo=first(row,"A_REPOSITORY_DIFF"); b_repo=first(row,"B_REPOSITORY_DIFF")
        pkg=parse_content(pkg_ev); resp=parse_content(resp_ev); action=parse_content(action_ev)
        repair={}
        if isinstance(resp,dict):
            try: repair=json.loads(resp.get("content","{}")).get("repair",{})
            except Exception: repair={}
        audit={
          "schema":"stage2-r7-g1-ab-paired-process-semantic-audit-v1",
          "reviewer":{"model":"GPT-5.6 Sol","execution_mode":"CHATGPT_NATIVE_REASONING","prior_layer_c_labels_read":False,"prior_layer_b_reference_labels_read":False,"monitor_predictions_read":False},
          "cell_id":cell,
          "input_packet_sha256":row["packet_sha256"],
          "pair_integrity":{"same_parent_checkpoint":True,"one_repair_action":True,"repair_executor_exited":True,"B_rerun":False,"natural_A_rerun":False},
          "intervention_summary":{"package_id":pkg["package_id"],"repair_target_ref":pkg["detection_surface"],"repair_kind":repair.get("kind") or action.get("mutation_class","unknown"),"summary":repair.get("instruction") or repair.get("reason") or f"One local intervention on {pkg['detection_surface']}."},
          "arm_A":arm_object(row,"A"),
          "arm_B":arm_object(row,"B"),
          "paired_effect":{"direct_target_effect":j["direct"],"semantic_authority_change":j["sem"],"collaboration_scope_change":j["scope"],"temporal_reach_change":j["time"],"route_relation":j["route"],"unrelated_structure_preservation":j["preserve"],"overall_process_effect":j["overall"],"mechanism":j["mech"],"evidence_refs":[a_summary["ref"],b_summary["ref"],a_repo["ref"],b_repo["ref"],action_ev["ref"],boundary_ev["ref"]]},
          "cross_arm_findings":[
            {"finding_id":"F01","status":"NOT_ESTABLISHED" if j["overall"]=="INCONCLUSIVE" else "SUPPORTED_CANDIDATE","statement":j["mech"],"evidence_refs":[a_summary["ref"],b_summary["ref"],a_repo["ref"],b_repo["ref"],action_ev["ref"],boundary_ev["ref"]]},
            {"finding_id":"F02","status":"SUPPORTED","statement":"The B intervention executed exactly once within the frozen repair boundary and the preserve set was intact at repair-executor exit.","evidence_refs":[action_ev["ref"],boundary_ev["ref"]]}
          ],
          "healthy_alternatives":[{"type":"STOCHASTIC_CONTINUATION","status":"SUPPORTED_CANDIDATE","notes":"A/B route differences may partly reflect probabilistic continuation from the same parent; this paired observation is used as a local causal contrast, not as rerun-based frequency evidence.","evidence_refs":[a_summary["ref"],b_summary["ref"]]}],
          "not_established":["C/P/R dimensions are not independently re-labeled from prior Layer-B/Layer-C judgments in this primary paired audit.","Hidden model reasoning is not inferred from event order.","Endpoint correctness is not used as the primary repair-effect criterion."]
        }
        (out/f"{cell}.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
        results.append({"cell_id":cell,"input_packet_sha256":row["packet_sha256"],"overall_process_effect":j["overall"],"direct_target_effect":j["direct"]})
    packet_index_sha256=hashlib.sha256((packet_root/"packet_index.json").read_bytes()).hexdigest()
    index={"schema":"stage2-r7-g1-ab-paired-process-semantic-audit-index-v1","status":"DRAFTED_12_OF_12_PENDING_VALIDATION","reviewer_model":"GPT-5.6 Sol","execution_mode":"CHATGPT_NATIVE_REASONING","authorization_issue":287,"source_packet_freeze_commit":"8b4c996b55909855bb8c678e578e310e2863376c","source_packet_index_sha256":packet_index_sha256,"audit_count":12,"cells":results,"new_subject_provider_calls":0,"repair_calls":0,"paid_evaluator_calls":0}
    (out/"audit_index.json").write_text(json.dumps(index,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":"MATERIALIZED","audits":12},sort_keys=True))

if __name__=="__main__":
    main()
