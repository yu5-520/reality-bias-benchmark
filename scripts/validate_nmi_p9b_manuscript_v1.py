#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANUSCRIPT=ROOT/"docs/submission/nmi/NMI_Manuscript_v0.18_EVIDENCE_FORWARD_WORKING.md"
SI=ROOT/"docs/submission/nmi/NMI_Supplementary_Information_v0.4_EVIDENCE_FORWARD_WORKING.md"
REGISTRY=ROOT/"configs/nmi_p9_paper_evidence_registry_v1.1.json"
LEDGERS=ROOT/"evidence/paper/nmi_p9/p9a_exemplar_evidence_ledgers_v1.json"
R5CAT=ROOT/"evidence/paper/nmi_p9/p9a_r5_frozen_case_structure_catalog_v1.json"

BASE_REF="f7148f80540ccb9f7179f2aa6f5a0a815bd2183c"
BASE_FILES=[
    "docs/submission/nmi/NMI_Manuscript_v0.17_PUBLIC_RAW.md",
    "docs/submission/nmi/NMI_Supplementary_Information_v0.3.md",
    "configs/nmi_submission_contract_v1.19.json",
]

def fail(msg: str) -> None:
    raise SystemExit("NMI_P9B_VALIDATION_FAILED: "+msg)

def req(cond: bool, msg: str) -> None:
    if not cond:
        fail(msg)

def git_blob(ref: str, path: str) -> str:
    return subprocess.check_output(["git","rev-parse",f"{ref}:{path}"],cwd=ROOT,text=True).strip()

def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w%+./'’-]+\b", text, flags=re.UNICODE))

def main() -> None:
    m=MANUSCRIPT.read_text(encoding="utf-8")
    si=SI.read_text(encoding="utf-8")
    reg=json.loads(REGISTRY.read_text(encoding="utf-8"))
    led=json.loads(LEDGERS.read_text(encoding="utf-8"))
    r5=json.loads(R5CAT.read_text(encoding="utf-8"))

    # Baseline protection
    for path in BASE_FILES:
        req(git_blob("HEAD",path)==git_blob(BASE_REF,path),f"P8H.2 baseline modified: {path}")

    # Journal-facing structure
    req("## Abstract" in m and "## Results" in m and "## Discussion" in m and "## Methods" in m,"required manuscript sections")
    discussion=m[m.index("## Discussion"):m.index("## Methods")]
    req("### " not in discussion,"Discussion must not contain subheadings")
    req("## Introduction" not in m,"Introduction must remain unheaded")

    # Word counts
    abs_text=m[m.index("## Abstract")+len("## Abstract"):m.index("\n\nMulti-agent AI systems are commonly")]
    main_text=m[m.index("\n\nMulti-agent AI systems are commonly"):m.index("## Methods")]
    req(word_count(abs_text)<=150,f"abstract over 150 words: {word_count(abs_text)}")
    req(word_count(main_text)<=3500,f"main text over 3500 words: {word_count(main_text)}")

    # No drafting placeholders
    for needle in ("[Carry forward","[Write only","[Preserve verified","[EVIDENCE:","TODO","placeholder"):
        req(needle.lower() not in m.lower(),f"manuscript drafting placeholder remains: {needle}")

    # Evidence-first content gates
    required_phrases=[
        "arena-ecommerce-0002",
        "reconciled_by_inventory",
        "arena-ecommerce-0001",
        "v5-xd-software_engineering-fr001-0001",
        "wave-3-56ee79f97f54",
        "wave-1-92211309fb1b",
        "wave-4-8b1731b57396",
        "wave-4-cf726639de1d",
        "Functional Semantic Lineage",
        "shared process-reality layer",
        "lineage-independent logistics evidence was re-read",
    ]
    for phrase in required_phrases:
        req(phrase.lower() in m.lower(),f"required evidence phrase absent: {phrase}")

    # Counts remain frozen
    for phrase in ("three high-confidence Dynamic C anchors","23 Dynamic P-supported trajectories","18 Dynamic R-supported trajectories"):
        req(phrase in m,f"frozen count wording absent: {phrase}")
    req(reg["p9a_gate"]["frozen_counts_changed"] is False,"registry says frozen counts changed")
    req(led["freeze_boundary"]["frozen_C_count_change"]==0,"C count mutation")
    req(led["freeze_boundary"]["frozen_P_count_change"]==0,"P count mutation")
    req(led["freeze_boundary"]["frozen_R_count_change"]==0,"R count mutation")
    req(r5["case_count"]==29 and r5["stronger_candidate_count"]==4 and r5["non_stronger_count"]==25,"R5 accounting")

    # Figure / reference / SI gates
    req(len(re.findall(r"\*\*Figure [1-5] \|",m))==5,"must have exactly five figure legends")
    refs=m[m.index("## References"):m.index("## Figure legends")]
    req(len(re.findall(r"(?m)^\d+\.",refs))==12,"reference count must remain 12")
    req("## Supplementary Table S3 — Prior-art boundary" in si,"real Supplementary Table S3 missing")
    s3=si[si.index("## Supplementary Table S3 — Prior-art boundary"):]
    req("| Prior research area |" in s3,"Supplementary Table S3 is not a table")
    req("141" in si and "150" in si and "9" in si,"SI evidence accounting incomplete")
    req("DIRECT_REPAIR_APPLICATION_AT_ANCHOR" in si,"SI R7 preservation boundary missing")
    req("c68c90a5f7c9fd9135c80b5c2333692945b2d953703facc48c816a50df0d78c4" in si,"exact P audit record missing from SI")

    # Forward R candidate must stay out of counts
    fw=[x for x in reg["entries"] if x["evidence_id"]=="EV-R-FORWARD-STRENGTHEN-W3"][0]
    req("NOT_COUNTED" in fw["verification_status"],"forward R candidate was promoted")
    req("CENSORED_UNRESOLVED" in led["exemplars"][-1]["existing_R8"]["R"],"forward R existing status overwritten")
    req(led["exemplars"][-1]["count_effect"]==0,"forward R count effect nonzero")

    print("NMI_P9B_VALIDATION=PASS")
    print(f"ABSTRACT_WORDS={word_count(abs_text)}")
    print(f"MAIN_TEXT_WORDS={word_count(main_text)}")
    print("FIGURE_LEGENDS=5")
    print("REFERENCES=12")
    print("P8H2_BASELINE_IMMUTABLE=PASS")
    print("FROZEN_COUNTS=C3_P23_R18")
    print("P9A_RAW_EVIDENCE_BINDING=PASS")
    print("P9B_RESULTS_DISCUSSION_METHODS_SI=PASS")
    print("NEXT_GATE=P9C_FIGURE_MATERIALIZATION_AND_FULL_MANUSCRIPT_QA")

if __name__=="__main__":
    main()
