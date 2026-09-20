#!/usr/bin/env python3
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def req(v,m):
    if not v: raise SystemExit("NMI_P4_RA08_VALIDATION_FAILED: "+m)
m=(ROOT/"docs/submission/nmi/NMI_Manuscript_v0.10.md").read_text(encoding="utf-8")
c=json.loads((ROOT/"configs/nmi_submission_contract_v1.11.json").read_text(encoding="utf-8"))
ra=c["p4_reviewer_attacks"]["RA08_subject_model_external_validity"]
req("Subject-model coverage is substantially narrower than domain coverage" in m,"discussion boundary")
req("### Subject-model coverage and external validity" in m,"methods subsection")
req("cross-model semantic review is a different axis" in m,"review/subject distinction")
req(ra["heldout_same_model_provider_lock"] is True,"model lock")
req(ra["cross_domain_supported"] is True,"domain support")
req(ra["subject_model_robustness_established"] is False,"subject robustness")
req(ra["provider_robustness_established"] is False,"provider robustness")
req(ra["cross_model_review_counts_as_subject_replication"] is False,"review guard")
a0=m.index("## Abstract")+len("## Abstract"); sep=m.index("---",a0); mm=m.index("## Methods",sep)
def wc(x):
    x=re.sub(r"\[[^\]]+\]"," ",x); x=re.sub(r"`[^`]*`"," ",x)
    return len(re.findall(r"[A-Za-z0-9À-ɏ'-]+",x))
aw=wc(m[a0:sep]); mw=wc(m[sep+3:mm])
req(aw==147,f"abstract {aw}"); req(3200<=mw<3500,f"main {mw}")
print("NMI_P4_RA08_VALIDATION=PASS")
print(f"ABSTRACT_WORDS={aw}")
print(f"MAIN_TEXT_BEFORE_METHODS={mw}")
print("CROSS_DOMAIN_EQUALS_CROSS_MODEL=false")
print("CROSS_MODEL_REVIEW_EQUALS_SUBJECT_REPLICATION=false")
print("SUBJECT_MODEL_ROBUSTNESS_ESTABLISHED=false")
print("PROVIDER_ROBUSTNESS_ESTABLISHED=false")
