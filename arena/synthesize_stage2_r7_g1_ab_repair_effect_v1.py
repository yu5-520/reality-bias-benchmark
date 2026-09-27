#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, json, hashlib
from pathlib import Path

def sha256(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    root=Path(args.root)
    audits=root/"audits"
    seal=json.loads((root/"formal_audit_seal.json").read_text())
    idx=json.loads((audits/"audit_index.json").read_text())
    assert seal["status"]=="SEALED"
    assert seal["audit_count"]==12 and seal["validated_count"]==12
    assert seal["cross_cell_synthesis_gate"]=="OPEN_AFTER_12_CELL_SEAL"
    assert idx["status"]=="SEALED_12_OF_12_VALIDATED"
    rows=[]
    for p in sorted(audits.glob("X*-T*.json")):
        a=json.loads(p.read_text())
        cell=a["cell_id"]; system,task=cell.split("-")
        pe=a["paired_effect"]
        rows.append({
            "cell_id":cell,"system":system,"task":task,
            "direct_target_effect":pe["direct_target_effect"],
            "overall_process_effect":pe["overall_process_effect"],
            "collaboration_scope_change":pe["collaboration_scope_change"],
            "temporal_reach_change":pe["temporal_reach_change"],
            "route_relation":pe["route_relation"],
            "unrelated_structure_preservation":pe["unrelated_structure_preservation"],
            "mechanism":pe["mechanism"],
            "audit_sha256":sha256(p),
        })
    assert len(rows)==12
    def counts(field,subset=rows):
        return dict(sorted(collections.Counter(r[field] for r in subset).items()))
    by_task={}
    for t in ["T1","T2","T3"]:
        ss=[r for r in rows if r["task"]==t]
        by_task[t]={
            "n":len(ss),
            "direct_target_effect":counts("direct_target_effect",ss),
            "overall_process_effect":counts("overall_process_effect",ss),
            "cells":[r["cell_id"] for r in ss],
        }
    by_system={}
    for x in ["X2","X4","X5","X7"]:
        ss=[r for r in rows if r["system"]==x]
        by_system[x]={
            "n":len(ss),
            "direct_target_effect":counts("direct_target_effect",ss),
            "overall_process_effect":counts("overall_process_effect",ss),
            "cells":[r["cell_id"] for r in ss],
        }

    changed=sum(r["direct_target_effect"] in {"REDIRECTED","REDUCED","REMOVED"} for r in rows)
    targeted=sum(r["overall_process_effect"] in {"TARGETED_REDIRECTION","TARGETED_SUPPRESSION"} for r in rows)
    persisted=sum(r["overall_process_effect"]=="PERSISTENCE" for r in rows)
    mixed=sum(r["overall_process_effect"]=="MIXED_EFFECT" for r in rows)
    inconclusive=sum(r["overall_process_effect"]=="INCONCLUSIVE" for r in rows)
    preserved=sum(r["unrelated_structure_preservation"]=="PRESERVED" for r in rows)

    synthesis={
        "schema":"stage2-r7-g1-ab-cross-cell-repair-effect-synthesis-v1",
        "status":"SEALED",
        "source_audit_seal_sha256":sha256(root/"formal_audit_seal.json"),
        "source_audit_index_sha256":sha256(audits/"audit_index.json"),
        "population":{
            "paired_cells":12,
            "systems":["X2","X4","X5","X7"],
            "tasks":["T1","T2","T3"],
            "excluded_fail_closed_cells":["X6-T1","X6-T2","X6-T3"],
            "excluded_reason":"FOREIGN_PARENT_STATE_RECONSTRUCTION_BLOCKED",
        },
        "overall_counts":{
            "direct_target_effect":counts("direct_target_effect"),
            "overall_process_effect":counts("overall_process_effect"),
            "collaboration_scope_change":counts("collaboration_scope_change"),
            "temporal_reach_change":counts("temporal_reach_change"),
            "route_relation":counts("route_relation"),
            "unrelated_structure_preservation":counts("unrelated_structure_preservation"),
        },
        "derived_descriptive_counts":{
            "observable_direct_target_change":changed,
            "targeted_redirection_or_suppression":targeted,
            "persistence":persisted,
            "mixed_effect":mixed,
            "inconclusive":inconclusive,
            "unrelated_structure_preserved":preserved,
        },
        "by_task":by_task,
        "by_system":by_system,
        "cell_results":rows,
        "interpretation":[
            "The paired block does not support a universal repair-success claim: the same one-shot local repair regime produced targeted redirection/suppression, persistence, mixed effects, and one inconclusive case across the 12 frozen pairs.",
            "Six of twelve pairs showed an observable direct target change (REDIRECTED or REDUCED), while five retained PERSISTED direct-target behavior and one was NOT_ESTABLISHED.",
            "Four of twelve pairs showed a clean targeted process effect at the paired-audit level (three TARGETED_REDIRECTION and one TARGETED_SUPPRESSION); four showed PERSISTENCE, three MIXED_EFFECT, and one INCONCLUSIVE.",
            "T2 produced the most consistent route-level change in this group: X2, X4, and X5 were TARGETED_REDIRECTION, while X7 was MIXED_EFFECT. T1 was dominated by persistence/inconclusive outcomes. T3 was heterogeneous.",
            "All 12 paired repairs preserved unrelated structure at repair-executor exit under the frozen preserve-set contract. This supports the engineering claim that content-addressed local intervention can remain boundary-limited even when the downstream process effect is incomplete.",
            "The result separates repair locality from repair efficacy: a repair can be structurally precise and boundary-preserving without guaranteeing that process inertia disappears downstream.",
            "X6 remains an engineering boundary result rather than a paired-effect sample; fail-closed inability to reconstruct mutable foreign parent state is preserved as a limitation, not imputed as repair failure.",
            "Because the agents are probabilistic and each pair is a single frozen natural trajectory plus one local intervention, these counts are descriptive of this prospective group and are not rerun-based frequency estimates."
        ],
        "claim_boundary":{
            "causal_scope":"LOCAL_PAIRED_CONTRAST_FROM_SAME_FROZEN_PARENT",
            "universal_success_claim":False,
            "frequency_estimation_claim":False,
            "endpoint_correctness_primary_object":False,
            "process_reality_primary_object":True,
            "new_subject_provider_calls":0,
            "repair_calls":0,
            "paid_evaluator_calls":0,
            "natural_A_reruns":0,
            "B_reruns":0,
        }
    }
    out=Path(args.out); out.mkdir(parents=True,exist_ok=False)
    (out/"cross_cell_synthesis_v1.json").write_text(json.dumps(synthesis,ensure_ascii=False,indent=2,sort_keys=True)+"\n")

    md=[]
    md.append("# Stage-II R7 G1 A↔B Paired Repair-Effect Synthesis v1")
    md.append("")
    md.append("## Scope")
    md.append("")
    md.append("This synthesis covers the 12 frozen same-parent pairs X2/X4/X5/X7 × T1/T2/T3. X6-T1/T2/T3 remain fail-closed engineering-boundary cases and are not counted as repaired-effect samples. No natural-A reruns, B reruns, new subject calls, repair calls, or paid evaluator calls were used in synthesis.")
    md.append("")
    md.append("## Main result")
    md.append("")
    md.append(f"Across 12 paired cells, {changed}/12 showed an observable direct target change, {targeted}/12 showed a clean targeted process redirection/suppression, {persisted}/12 showed persistence, {mixed}/12 showed mixed effects, and {inconclusive}/12 was inconclusive. Unrelated structure was preserved in {preserved}/12 under the frozen repair boundary.")
    md.append("")
    md.append("The engineering result is therefore not 'repair always works'. The stronger result is that a content-addressed one-shot intervention can stay local and preserve unrelated structure while downstream process dynamics remain heterogeneous. Locality and efficacy are distinct properties.")
    md.append("")
    md.append("## Task-family pattern")
    md.append("")
    md.append("- **T1:** dominated by persistence/inconclusive outcomes; reopening an unresolved action state often did not break the downstream horizon-level inertia.")
    md.append("- **T2:** the most consistent route-level change in this group; X2, X4 and X5 showed targeted redirection, while X7 remained mixed.")
    md.append("- **T3:** heterogeneous; one targeted suppression, two mixed effects and one persistence outcome.")
    md.append("")
    md.append("## Engineering interpretation")
    md.append("")
    md.append("The repair package can be precise without being globally curative. The 12/12 preserve-set result shows that the repair executor respected the selected local surface and exited without collateral mutation. The paired semantics then show that downstream behavior may still persist, reorganize, or only partially contract. This is the useful distinction for the R7 engineering framework: **locate precisely, repair once, exit, then observe the system rather than repeatedly forcing it toward a preferred result.**")
    md.append("")
    md.append("## Claim boundary")
    md.append("")
    md.append("These are prospective paired contrasts from one frozen natural trajectory per cell, not repeated-sampling estimates. Endpoint correctness is retained only as a terminal indicator; the audited object is process reality after the same frozen parent.")
    (out/"R7_G1_AB_Paired_Repair_Effect_Synthesis_v1.md").write_text("\n".join(md)+"\n")
    print(json.dumps({"status":"SEALED","paired_cells":12,"direct_changed":changed,"targeted":targeted,"persistence":persisted,"mixed":mixed,"inconclusive":inconclusive,"preserved":preserved},sort_keys=True))

if __name__=="__main__":
    main()
