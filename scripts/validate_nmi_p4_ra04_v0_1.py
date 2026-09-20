#!/usr/bin/env python3
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def req(v,m):
    if not v:
        raise SystemExit("NMI_P4_RA04_VALIDATION_FAILED: "+m)

def load(p):
    return json.loads((ROOT/p).read_text(encoding="utf-8"))

m=(ROOT/"docs/submission/nmi/NMI_Manuscript_v0.5.md").read_text(encoding="utf-8")
c=load("configs/nmi_submission_contract_v1.6.json")
mf=load("manifests/nmi_p4_ra04_propagation_taxonomy_2026-09-20_v0_1.json")
ra=c["p4_reviewer_attacks"]["RA04_propagation_failure_taxonomy_reduction"]

req("The distinction from ordinary information propagation is operational rather than terminological." in m,"propagation distinction")
req("25 of 29 persistence cases" in m,"R5 negative comparator")
req(ra["ecommerce_functional_continuation"]=="9/9","9/9 continuation")
req(ra["propagation_equals_C"] is False,"propagation guard")
req(ra["collaboration_activity_equals_P"] is False,"P guard")
req(ra["retrieval_reopen_equals_R"] is False,"R guard")
req(ra["persistence_equals_system_inertia"] is False,"inertia guard")
req(ra["universal_first_ever_claim"] is False,"novelty guard")
req(mf["execution_boundary"]["new_semantic_adjudication"] is False,"no adjudication")

a0=m.index("## Abstract")+len("## Abstract")
sep=m.index("---",a0)
mm=m.index("## Methods",sep)
abstract=m[a0:sep]
main=m[sep+3:mm]
def word(x):
    x=re.sub(r"\[[^\]]+\]"," ",x)
    x=re.sub(r"`[^`]*`"," ",x)
    return len(re.findall(r"[A-Za-z0-9À-ɏ'-]+",x))
aw=word(abstract); mw=word(main)
req(aw==147,f"abstract words {aw}")
req(3100 <= mw < 3500,f"main words {mw}")
print("NMI_P4_RA04_VALIDATION=PASS")
print(f"ABSTRACT_WORDS={aw}")
print(f"MAIN_TEXT_BEFORE_METHODS={mw}")
print("PROPAGATION_EQUALS_C=false")
print("COLLABORATION_ACTIVITY_EQUALS_P=false")
print("RETRIEVAL_REOPEN_EQUALS_R=false")
print("PERSISTENCE_EQUALS_SYSTEM_INERTIA=false")
print("UNIVERSAL_FIRST_EVER_CLAIM=false")
