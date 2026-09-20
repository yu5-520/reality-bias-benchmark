#!/usr/bin/env python3
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def req(v,m):
    if not v:
        raise SystemExit("NMI_P4_RA03_VALIDATION_FAILED: "+m)

def load(p):
    return json.loads((ROOT/p).read_text(encoding="utf-8"))

m=(ROOT/"docs/submission/nmi/NMI_Manuscript_v0.4.md").read_text(encoding="utf-8")
c=load("configs/nmi_submission_contract_v1.5.json")
mf=load("manifests/nmi_p4_ra03_semantic_subjectivity_posthoc_2026-09-20_v0_1.json")

req("retrospective mechanism analysis, not a preregistered confirmatory test" in m,"retrospective disclosure")
req("complete 90-trajectory held-out natural cohort is reviewed" in m,"full-cohort safeguard")
req("Independent blinded reviewer replication remains necessary external validation" in m,"reviewer limitation")
ra=c["p4_reviewer_attacks"]["RA03_semantic_subjectivity_posthoc"]
req(ra["rubric_preregistered_before_subject_generation"] is False,"preregistration guard")
req(ra["full_heldout_cohort_reviewed"] is True,"full cohort")
req(ra["outcome_conditioned_subject_reruns"]==0,"no outcome reruns")
req(ra["semantic_reviewer_dependence_remains"] is True,"subjectivity retained")
req(mf["execution_boundary"]["new_semantic_adjudication"] is False,"no new adjudication")

abstract=m.split("## Abstract",1)[1].split("---",1)[0]
main=m.split("---",1)[1].split("## Methods",1)[0]
def word(x):
    x=re.sub(r"\[[^\]]+\]"," ",x)
    x=re.sub(r"`[^`]*`"," ",x)
    return len(re.findall(r"[A-Za-z0-9À-ɏ'-]+",x))
aw=word(abstract); mw=word(main)
req(aw==147,f"abstract words {aw}")
req(2950 <= mw < 3500,f"main words {mw}")
print("NMI_P4_RA03_VALIDATION=PASS")
print(f"ABSTRACT_WORDS={aw}")
print(f"MAIN_TEXT_BEFORE_METHODS={mw}")
print("R8_PREREGISTERED=false")
print("HELDOUT_FULL_COHORT_REVIEWED=true")
print("OUTCOME_CONDITIONED_SUBJECT_RERUNS=0")
print("SEMANTIC_REVIEWER_DEPENDENCE_REMAINS=true")
