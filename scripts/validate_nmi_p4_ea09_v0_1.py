#!/usr/bin/env python3
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def req(v,m):
    if not v: raise SystemExit("NMI_P4_EA09_VALIDATION_FAILED: "+m)
m=(ROOT/"docs/submission/nmi/NMI_Manuscript_v0.11.md").read_text(encoding="utf-8")
c=json.loads((ROOT/"configs/nmi_submission_contract_v1.12.json").read_text(encoding="utf-8"))
req("process qualification" in m.lower(),"process qualification")
req("The paper does not claim universal prevalence or model invariance" in m,"claim restraint")
req(c["status"]=="NMI_P4_COMPLETE_HANDOFF_TO_P5","P4 completion")
req(c["official_editorial_position_snapshot"]["editorial_outcome_predicted"] is False,"no prediction")
req(c["p4_completion"]["theory_expansion_after_p4"] is False,"no more theory expansion")
req(c["next_gate"]=="NMI_P5_MANUSCRIPT_COMPRESSION_AND_FINALIZATION","P5 handoff")
a0=m.index("## Abstract")+len("## Abstract"); sep=m.index("---",a0); mm=m.index("## Methods",sep)
def wc(x):
    x=re.sub(r"\[[^\]]+\]"," ",x); x=re.sub(r"`[^`]*`"," ",x)
    return len(re.findall(r"[A-Za-z0-9À-ɏ'-]+",x))
aw=wc(m[a0:sep]); mw=wc(m[sep+3:mm])
req(aw==147,f"abstract {aw}"); req(3300<=mw<3500,f"main {mw}")
print("NMI_P4_EA09_VALIDATION=PASS")
print(f"ABSTRACT_WORDS={aw}")
print(f"MAIN_TEXT_BEFORE_METHODS={mw}")
print("P4_ATTACK_SUITE_COMPLETE=true")
print("EDITORIAL_OUTCOME_PREDICTED=false")
print("NEXT_GATE=NMI_P5_MANUSCRIPT_COMPRESSION_AND_FINALIZATION")
