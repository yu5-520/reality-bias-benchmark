#!/usr/bin/env python3
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def req(v,m):
    if not v:
        raise SystemExit("NMI_P4_RA05_VALIDATION_FAILED: "+m)

def load(p):
    return json.loads((ROOT/p).read_text(encoding="utf-8"))

m=(ROOT/"docs/submission/nmi/NMI_Manuscript_v0.6.md").read_text(encoding="utf-8")
c=load("configs/nmi_submission_contract_v1.7.json")
mf=load("manifests/nmi_p4_ra05_r5_causal_boundary_2026-09-21_v0_1.json")
ra=c["p4_reviewer_attacks"]["RA05_r5_causal_boundary"]

req("Canonical R5 is not an average-treatment-effect design" in m,"ATE boundary")
req("R5 as intervention-response evidence" in m,"intervention-response wording")
req(ra["canonical_geometry"]["new_sampled_natural_controls"]==0,"no sampled control")
req(ra["canonical_geometry"]["intervention_continuation_per_case"]==1,"one intervention")
req(ra["persistent_state_mutation"] is False,"no persistent mutation")
req(ra["automatic_reinjection"] is False,"no reinjection")
req(ra["unique_r5_causality_established"]=="0/29","unique causality guard")
req(ra["average_treatment_effect_claim"] is False,"ATE claim false")
req(ra["universal_effect_direction_claim"] is False,"direction claim false")
req(mf["execution_boundary"]["new_subject_runs"]==0,"no new subject")
req(mf["execution_boundary"]["new_semantic_adjudication"] is False,"no new adjudication")

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
req(3180 <= mw < 3500,f"main words {mw}")
print("NMI_P4_RA05_VALIDATION=PASS")
print(f"ABSTRACT_WORDS={aw}")
print(f"MAIN_TEXT_BEFORE_METHODS={mw}")
print("R5_NEW_SAMPLED_CONTROL=0")
print("R5_CANONICAL_REPLICATE=1")
print("R5_UNIQUE_CAUSALITY=0/29")
print("R5_ATE_CLAIM=false")
print("R5_UNIVERSAL_DIRECTION_CLAIM=false")
