#!/usr/bin/env python3
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def req(v,m):
    if not v:
        raise SystemExit("NMI_P4_RA06_VALIDATION_FAILED: "+m)

def load(p):
    return json.loads((ROOT/p).read_text(encoding="utf-8"))

m=(ROOT/"docs/submission/nmi/NMI_Manuscript_v0.7.md").read_text(encoding="utf-8")
c=load("configs/nmi_submission_contract_v1.8.json")
mf=load("manifests/nmi_p4_ra06_repair_rerun_endpoint_2026-09-21_v0_1.json")
ra=c["p4_reviewer_attacks"]["RA06_repair_rerun_same_endpoint"]

req("R7-S is not a blind rerun" in m,"rerun boundary")
req("compatible or unrelated structure was preserved in 4/4" in m,"preservation")
req("two repairs materially changed the downstream plan and two reconverged" in m,"outcome split")
req(ra["compatible_or_unrelated_structure_preserved"]=="4/4","4/4 preservation")
req(ra["material_divergence"]=="2/4","2/4 divergence")
req(ra["compatible_reconvergence"]=="2/4","2/4 reconvergence")
req(ra["recomputed_descendants"]==[43,35,28,29],"recompute counts")
req(ra["prompt_correction_equals_internal_lineage_repair"] is False,"prompt repair guard")
req(ra["selective_recompute_equals_whole_run_rerun"] is False,"rerun guard")
req(ra["endpoint_equality_implies_no_process_effect"] is False,"endpoint guard")
req(ra["universal_r7s_superiority_established"] is False,"superiority guard")
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
req(3250 <= mw < 3500,f"main words {mw}")
print("NMI_P4_RA06_VALIDATION=PASS")
print(f"ABSTRACT_WORDS={aw}")
print(f"MAIN_TEXT_BEFORE_METHODS={mw}")
print("R7S_PRESERVATION=4/4")
print("R7S_DIVERGENCE=2/4")
print("R7S_RECONVERGENCE=2/4")
print("SELECTIVE_RECOMPUTE_EQUALS_WHOLE_RERUN=false")
print("SAME_ENDPOINT_EQUALS_NO_PROCESS_EFFECT=false")
print("UNIVERSAL_R7S_SUPERIORITY=false")
