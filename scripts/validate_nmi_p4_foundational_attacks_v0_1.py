#!/usr/bin/env python3
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def req(v,m):
    if not v:
        raise SystemExit("NMI_P4_FOUNDATIONAL_ATTACKS_VALIDATION_FAILED: "+m)

def load(p):
    return json.loads((ROOT/p).read_text(encoding="utf-8"))

m=(ROOT/"docs/submission/nmi/NMI_Manuscript_v0.3.md").read_text(encoding="utf-8")
c=load("configs/nmi_submission_contract_v1.4.json")
mf=load("manifests/nmi_p4_foundational_attacks_2026-09-20_v0_1.json")

req("A process-reality monitor could operate as an external observability layer" in m,"monitor outlook")
req("Reasoning capability is not itself new external evidence or target-system authorization" in m,"capability boundary")
req("semantic transfer does not automatically imply authority transfer" in m,"inter-system invariant")
req(c["p4_foundational_attacks"]["FA01_structural_scout_recall"]["narrow_union_capture"]=="10/13","FA01")
req(c["p4_foundational_attacks"]["FA02_capability_absorption_system_boundary"]["empirical_future_frequency_claim"] is False,"FA02 future guard")
req(c["engineering_outlook"]["repair_agent_global_write_authority"] is False,"repair authority guard")
req(mf["execution_boundary"]["new_subject_runs"]==0,"no subject runs")
req(mf["execution_boundary"]["new_semantic_adjudication"] is False,"no new adjudication")

abstract=m.split("## Abstract",1)[1].split("---",1)[0]
main=m.split("---",1)[1].split("## Methods",1)[0]
def word(x):
    x=re.sub(r"\[[^\]]+\]"," ",x)
    x=re.sub(r"`[^`]*`"," ",x)
    return len(re.findall(r"[A-Za-z0-9À-ɏ'-]+",x))
aw=word(abstract); mw=word(main)
req(aw==147,f"abstract words {aw}")
req(2800 <= mw < 3500,f"main words {mw}")
print("NMI_P4_FOUNDATIONAL_ATTACKS_VALIDATION=PASS")
print(f"ABSTRACT_WORDS={aw}")
print(f"MAIN_TEXT_BEFORE_METHODS={mw}")
print("FA01_CAPTURE=10/13")
print("FA02_FUTURE_FREQUENCY_CLAIM=false")
print("REPAIR_AGENT_GLOBAL_WRITE_AUTHORITY=false")
