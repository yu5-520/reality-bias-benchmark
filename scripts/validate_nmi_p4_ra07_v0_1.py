#!/usr/bin/env python3
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def req(v,m):
    if not v: raise SystemExit("NMI_P4_RA07_VALIDATION_FAILED: "+m)
m=(ROOT/"docs/submission/nmi/NMI_Manuscript_v0.9.md").read_text(encoding="utf-8")
c=json.loads((ROOT/"configs/nmi_submission_contract_v1.10.json").read_text(encoding="utf-8"))
ra=c["p4_reviewer_attacks"]["RA07_inter_system_extrapolation"]
req("deliberately an outlook, not an empirical generalization" in m,"outlook wording")
req("vary domain, not system-boundary architecture" in m,"cross-domain boundary")
req("### Generalization boundary" in m,"methods boundary")
req(ra["cross_domain_equals_cross_system_validation"] is False,"cross-domain guard")
req(ra["inter_system_empirically_generalized"] is False,"generalization guard")
req(ra["semantic_authority_contract_empirically_validated"] is False,"contract guard")
req(ra["allowed_status"]=="TESTABLE_OUTLOOK_HYPOTHESIS","outlook status")
a0=m.index("## Abstract")+len("## Abstract"); sep=m.index("---",a0); mm=m.index("## Methods",sep)
def wc(x):
    x=re.sub(r"\[[^\]]+\]"," ",x); x=re.sub(r"`[^`]*`"," ",x)
    return len(re.findall(r"[A-Za-z0-9À-ɏ'-]+",x))
aw=wc(m[a0:sep]); mw=wc(m[sep+3:mm])
req(aw==147,f"abstract {aw}"); req(3150<=mw<3500,f"main {mw}")
print("NMI_P4_RA07_VALIDATION=PASS")
print(f"ABSTRACT_WORDS={aw}")
print(f"MAIN_TEXT_BEFORE_METHODS={mw}")
print("CROSS_DOMAIN_EQUALS_CROSS_SYSTEM=false")
print("INTER_SYSTEM_EMPIRICALLY_GENERALIZED=false")
print("SEMANTIC_AUTHORITY_CONTRACT_VALIDATED=false")
