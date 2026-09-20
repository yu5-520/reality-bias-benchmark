#!/usr/bin/env python3
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def req(v,m):
    if not v: raise SystemExit("NMI_P5_VALIDATION_FAILED: "+m)
m=(ROOT/"docs/submission/nmi/NMI_Manuscript_v0.12.md").read_text(encoding="utf-8")
c=json.loads((ROOT/"configs/nmi_submission_contract_v1.13.json").read_text(encoding="utf-8"))
def wc(x):
    x=re.sub(r"\[[^\]]+\]"," ",x)
    x=re.sub(r"`[^`]*`"," ",x)
    return len(re.findall(r"[A-Za-z0-9À-ɏ'-]+",x))
a0=m.index("## Abstract")+len("## Abstract")
sep=m.index("---",a0)
mm=m.index("## Methods",sep)
aw=wc(m[a0:sep]); mw=wc(m[sep+3:mm])
req(aw==147,f"abstract {aw}")
req(2800<=mw<=3100,f"main {mw}")
req("[L" not in m,"provisional L-key citation remains")
req("## Results" in m and "## Discussion" in m and "## Methods" in m,"journal section structure")
refs=re.findall(r"(?m)^\d+\. ",m[m.index("## References"):])
req(len(refs)==12,f"references {len(refs)}")
for p in c["figures"]["files"]:
    fp=ROOT/p
    req(fp.exists(),f"missing figure {p}")
    req("<svg" in fp.read_text(encoding="utf-8"),f"not svg {p}")
for p in [
 "docs/submission/nmi/NMI_Supplementary_Information_Structure_v1.md",
 "docs/submission/nmi/NMI_Cover_Letter_v0.1.md",
 "docs/submission/nmi/NMI_P5_Finalization_Status_v1.md"]:
    req((ROOT/p).exists(),f"missing {p}")
req(c["status"]=="NMI_P5_COMPLETE_HANDOFF_TO_P6","P5 status")
req(c["p5_completion"]["theory_expansion"] is False,"no theory expansion")
req(c["next_gate"]=="NMI_P6_REPRODUCIBILITY_AND_RELEASE_FREEZE","P6 handoff")
req(c["p6_blockers"]["r8_full_record_repository_integrity"]["overwrite_old_object"] is False,"append-only recovery")
print("NMI_P5_VALIDATION=PASS")
print(f"ABSTRACT_WORDS={aw}")
print(f"MAIN_TEXT_BEFORE_METHODS={mw}")
print("REFERENCES=12")
print("FIGURES=5")
print("NEXT_GATE=NMI_P6_REPRODUCIBILITY_AND_RELEASE_FREEZE")
