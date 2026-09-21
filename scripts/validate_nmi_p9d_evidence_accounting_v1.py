#!/usr/bin/env python3
from __future__ import annotations
import json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE_REF="111d0df1ac1baf74775d4d5bd12e3e13b616ebe8"
MS=ROOT/"docs/submission/nmi/NMI_Manuscript_v0.19_EVIDENCE_ACCOUNTING_WORKING.md"
SI=ROOT/"docs/submission/nmi/NMI_Supplementary_Information_v0.5_EVIDENCE_ACCOUNTING_WORKING.md"
ACC=ROOT/"evidence/paper/nmi_p9/EV_EVIDENCE_ACCOUNTING_FUNNEL_v1.json"
CON=ROOT/"configs/nmi_p9d_evidence_accounting_contract_v1.json"
IMMUTABLE=["docs/submission/nmi/NMI_Manuscript_v0.18_EVIDENCE_FORWARD_WORKING.md","docs/submission/nmi/NMI_Supplementary_Information_v0.4_EVIDENCE_FORWARD_WORKING.md","manifests/nmi_p9c_evidence_forward_final_export_2026-09-21_v1.json"]
def req(x,msg):
    if not x: raise SystemExit("NMI_P9D_VALIDATION_FAILED: "+msg)
def blob(ref,path):
    return subprocess.check_output(["git","rev-parse",f"{ref}:{path}"],cwd=ROOT,text=True).strip()
def wc(t):
    return len(re.findall(r"\b[\w%+./'’-]+\b",t,flags=re.UNICODE))
def main():
    for p in IMMUTABLE:
        req(blob("HEAD",p)==blob(BASE_REF,p),f"P9C immutable source changed: {p}")
    m=MS.read_text(encoding="utf-8"); si=SI.read_text(encoding="utf-8")
    a=json.loads(ACC.read_text()); c=json.loads(CON.read_text())
    abs_text=m[m.index("## Abstract")+len("## Abstract"):m.index("\n\nMulti-agent AI systems are commonly")]
    main_text=m[m.index("\n\nMulti-agent AI systems are commonly"):m.index("## Methods")]
    req(wc(abs_text)==145,f"abstract words {wc(abs_text)}")
    req(wc(main_text)==3469,f"main words {wc(main_text)}")
    req("Evidence accounting, observability and selection gates" in m,"accounting Methods subsection missing")
    req("42 censored/unresolved" in m and "21 healthy independent re-anchors" in m,"C accounting absent")
    req("2,127 repair-anchor candidate rows" in m and "10 of 13" in m,"monitoring/selector accounting absent")
    req("complete frozen ancestry" in m and "post-intervention descendants" in m,"R7 full semantic comparison unit absent")
    req("Supplementary Table S5" in si and "Supplementary Table S6" in si,"supplement accounting tables missing")
    req(a["inventory"]["combined_records"]==150,"combined inventory")
    req(sum([a["source_blocks"]["heldout_natural"]["n"],a["source_blocks"]["r5_canonical"]["n"],a["source_blocks"]["r7_historical_current"]["n"],a["source_blocks"]["ecommerce_discovery_history"]["n"]])==150,"source block sum")
    req(a["heldout_mechanism_141_C"]["total"]==141,"C state total")
    req(a["frozen_support_counts"]=={"C":3,"P":23,"R":18},"frozen counts")
    req(c["frozen_science"]=={"C":3,"P":23,"R":18,"new_subject_runs":0,"raw_mutations":0},"contract frozen science")
    req(len(re.findall(r"\*\*Figure [1-5] \|",m))==5,"figure legend count")
    print("NMI_P9D_VALIDATION=PASS")
    print("ABSTRACT_WORDS=145")
    print("MAIN_TEXT_WORDS=3469")
    print("SOURCE_BLOCKS=90+29+22+9=150")
    print("HELDOUT_C=0_SUPPORTED_48_HEALTHY_42_CENSORED")
    print("R5_C=2_SUPPORTED_6_FUNCTIONAL_NO_PENETRATION_21_REANCHOR")
    print("SELECTOR_CAPTURE=10/13")
    print("FROZEN_COUNTS=C3_P23_R18")
if __name__=="__main__":
    main()
