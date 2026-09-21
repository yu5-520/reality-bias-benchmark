#!/usr/bin/env python3
from __future__ import annotations
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

BASE_MANUSCRIPT="docs/submission/nmi/NMI_Manuscript_v0.17_PUBLIC_RAW.md"
BASE_SI="docs/submission/nmi/NMI_Supplementary_Information_v0.3.md"
BASE_CONTRACT="configs/nmi_submission_contract_v1.19.json"
PLAN="docs/submission/nmi/NMI_P9_Evidence_Forward_Rewrite_Plan_v1.md"
CONTRACT="configs/nmi_p9_evidence_forward_rewrite_contract_v1.json"
REGISTRY="configs/nmi_p9_paper_evidence_registry_v1.json"
FIGPLAN="configs/nmi_p9_figure_evidence_plan_v1.json"
WORKING="docs/submission/nmi/NMI_Manuscript_v0.18_EVIDENCE_FORWARD_WORKING.md"
SI_WORKING="docs/submission/nmi/NMI_Supplementary_Information_v0.4_EVIDENCE_FORWARD_WORKING.md"

def req(cond,msg):
    if not cond:
        raise SystemExit("NMI_P9_VALIDATION_FAILED: "+msg)

def git_blob(ref,path):
    return subprocess.check_output(["git","rev-parse",f"{ref}:{path}"],cwd=ROOT,text=True).strip()

def main():
    for p in [BASE_MANUSCRIPT,BASE_SI,BASE_CONTRACT,PLAN,CONTRACT,REGISTRY,FIGPLAN,WORKING,SI_WORKING]:
        req((ROOT/p).exists(),f"missing {p}")

    c=json.loads((ROOT/CONTRACT).read_text())
    r=json.loads((ROOT/REGISTRY).read_text())
    f=json.loads((ROOT/FIGPLAN).read_text())

    req(c["status"]=="ACTIVE_EVIDENCE_LAYER_EXTRACTION","contract status")
    req(c["baseline"]["baseline_is_immutable_for_p9"] is True,"baseline protection")
    req(c["frozen_counts"]["combined_inventory"]==150,"combined count")
    req(c["frozen_counts"]["heldout_mechanism_second_audit"]==141,"141 count")
    req(c["frozen_counts"]["ecommerce_discovery_reaudit"]==9,"9 count")
    req(c["frozen_counts"]["dynamic_C_high_confidence"]==3,"C count")
    req(c["frozen_counts"]["dynamic_P_supported"]==23,"P count")
    req(c["frozen_counts"]["dynamic_R_current_frozen_supported"]==18,"R count")

    req(c["execution_authorization"]["new_subject_runs"] is False,"new subject runs forbidden")
    req(c["execution_authorization"]["provider_calls"] is False,"provider calls forbidden")
    req(c["execution_authorization"]["evaluator_calls"] is False,"evaluator calls forbidden")
    req(c["execution_authorization"]["frozen_raw_mutation"] is False,"raw mutation forbidden")
    req(c["execution_authorization"]["silent_reclassification"] is False,"silent reclassification forbidden")

    ids={x["evidence_id"] for x in r["entries"]}
    required={
        "EV-C-NATURAL-ECOM-0002",
        "EV-C-HEALTHY-ECOM-0001",
        "EV-P-SE-NATURAL-0001",
        "EV-R6-SC-DESCENDANT",
        "EV-R6-FIN-REANCHOR",
        "EV-R7-DIVERGE-8B1731",
        "EV-R7-RECONVERGE-CF726",
        "EV-R-FORWARD-STRENGTHEN-W3",
    }
    req(required <= ids,"seed evidence routes incomplete")

    forward=next(x for x in r["entries"] if x["evidence_id"]=="EV-R-FORWARD-STRENGTHEN-W3")
    req("NOT_COUNTED" in forward["verification_status"],"forward R candidate must stay outside frozen count")

    req(len(f["figures"])==5,"five-figure plan")
    req(sum(1 for x in f["figures"] if x["evidence_ids"])>=5,"all figures evidence-bound")

    wm=(ROOT/WORKING).read_text()
    req("natural emergence" in wm.lower(),"natural-emergence narrative missing")
    req("Goal-preserving process expansion" in wm,"P section missing")
    req("Functional semantic lineage" in wm,"lineage section missing")
    req("Cumulative semantic synthesis" in wm,"semantic synthesis section missing")

    # Protect the P8H.2 baseline by requiring current blobs to match the commit
    # that was explicitly named as the P9 predecessor when the rewrite began.
    baseline_ref="f7148f80540ccb9f7179f2aa6f5a0a815bd2183c"
    for path in [BASE_MANUSCRIPT,BASE_SI,BASE_CONTRACT]:
        req(git_blob("HEAD",path)==git_blob(baseline_ref,path),f"P8H.2 baseline modified: {path}")

    print("NMI_P9_REWRITE_PLAN=PASS")
    print("P8H2_BASELINE_IMMUTABLE=PASS")
    print("FROZEN_COUNTS=3/23/18")
    print("PAPER_EVIDENCE_REGISTRY=SEEDED")
    print("FIGURE_PLAN=5_EVIDENCE_BOUND")
    print("NEW_SUBJECT_PROVIDER_EVALUATOR_CALLS=0")
    print("NEXT_GATE=P9A_COMPLETE_RAW_ROUTE_EXTRACTION")

if __name__=="__main__":
    main()
