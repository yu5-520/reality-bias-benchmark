#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(p):
    return json.loads((ROOT/p).read_text())

def req(c,m):
    if not c:
        raise SystemExit("NMI_P3_VALIDATION_FAILED: "+m)

contract=load("configs/nmi_submission_contract_v1.2.json")
manifest=load("manifests/nmi_p3_manuscript_2026-09-20_v0_1.json")
text=(ROOT/manifest["manuscript"]).read_text()

abstract=text.split("## Abstract",1)[1].split("---",1)[0]
main=text.split("---",1)[1].split("## Methods",1)[0]

def words(s):
    s=re.sub(r"`[^`]*`"," ",s)
    s=re.sub(r"[[^]]+]"," ",s)
    s=re.sub(r"[^A-Za-z0-9À-ɏ'-]+"," ",s)
    return [x for x in s.split() if x]

aw=len(words(abstract))
mw=len(words(main))

req(aw <= 150, f"abstract too long: {aw}")
req(mw <= 3500, f"main text too long: {mw}")
req("The value remained unchanged. **Its permission to count as reality did not.**" in text,"opening hook")
req("## An unchanged value can acquire a different reality permission" in text,"Result 1")
req("## Process reality evolves through dynamic permission transitions" in text,"Result 2")
req("## Semantic influence persists through transformed descendants" in text,"Result 3")
req("## Local authority perturbation reveals lineage and inertia" in text,"Result 4")
req("## Process reality can be repaired at lineage level" in text,"Result 5")
req(contract["next_gate"]=="NMI_P4_REVIEWER_ATTACK","next gate")
req(manifest["evidence_boundary"]["new_subject_runs"]==0,"new runs")
req(manifest["evidence_boundary"]["raw_evidence_mutation"] is False,"raw mutation")

print("NMI_P3_VALIDATION=PASS")
print(f"ABSTRACT_WORDS={aw}")
print(f"MAIN_TEXT_WORDS_BEFORE_METHODS={mw}")
print("NEXT=NMI_P4_REVIEWER_ATTACK")
