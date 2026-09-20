#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(p):
    return json.loads((ROOT/p).read_text())

def req(cond,msg):
    if not cond:
        raise SystemExit("NMI_SUBMISSION_TRACK_VALIDATION_FAILED: "+msg)

c=load("configs/nmi_submission_contract_v1.json")
m=load("manifests/nmi_submission_track_2026-09-20_v1.json")

req(c["target_journal"]=="Nature Machine Intelligence","journal")
req(c["target_content_type"]=="Article","content type")
req(c["phase_transition"]["create_r10_for_first_submission"] is False,"R10 freeze")
req(c["format_targets"]["official_main_text_max_words"]==3500,"word limit")
req(c["format_targets"]["official_abstract_max_words"]==150,"abstract")
req(c["format_targets"]["official_display_item_max"]==6,"display max")
req(c["format_targets"]["main_display_item_target"]==5,"figure target")
req(c["authorization"]["new_subject_runs"]==0,"subject runs")
req(c["authorization"]["raw_evidence_mutation"] is False,"raw mutation")
req(m["next_gate"]=="NMI_P3_MANUSCRIPT_V0_1","next gate")

for p in m["files"] + m["inherited_scientific_closure"]:
    req((ROOT/p).exists(),"missing "+p)

print("NMI_SUBMISSION_TRACK_VALIDATION=PASS")
print("CURRENT=NMI_P0_P2_IMPLEMENTED")
print("NEXT=NMI_P3_MANUSCRIPT_V0_1")
print("R10_FOR_FIRST_SUBMISSION=false")
print("NEW_SUBJECT_RUNS=0")
print("MAIN_FIGURE_TARGET=5")
