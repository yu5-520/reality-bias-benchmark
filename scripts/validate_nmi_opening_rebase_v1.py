#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(p):
    return json.loads((ROOT/p).read_text())

def req(c,m):
    if not c:
        raise SystemExit("NMI_OPENING_REBASE_VALIDATION_FAILED: "+m)

c=load("configs/nmi_submission_contract_v1.1.json")
m=load("manifests/nmi_opening_rebase_2026-09-20_v1.json")

req(c["opening"]["primary_case"]=="ec-discovery::formal_batch001::2::arena-ecommerce-0002","opening case")
req(c["opening"]["new_independent_warehouse_reconciliation"] is False,"warehouse evidence boundary")
req(c["opening"]["first_theory"]=="PROCESS_REALITY","first theory")
req(c["opening"]["first_mechanism"]=="SEMANTIC_AUTHORITY_MIGRATION","first mechanism")
req(c["conceptual_order"][0]=="NATURAL_CASE","case first")
req(c["conceptual_order"][1]=="PROCESS_REALITY","process reality second")
req(c["conceptual_order"][2]=="SEMANTIC_AUTHORITY_MIGRATION","authority migration third")
req(c["conceptual_order"][4]=="DYNAMIC_CPR","CPR after phenomenon/mechanism")
req(c["authorization"]["new_subject_runs"]==0,"no new runs")
req(c["authorization"]["raw_evidence_mutation"] is False,"no raw mutation")
req(m["next_gate"]=="NMI_P3_MANUSCRIPT_V0_1","next gate")
for p in m["files"]:
    req((ROOT/p).exists(),"missing "+p)

print("NMI_OPENING_REBASE_VALIDATION=PASS")
print("OPENING_CASE=ec-discovery::formal_batch001::2::arena-ecommerce-0002")
print("FIRST_THEORY=PROCESS_REALITY")
print("FIRST_MECHANISM=SEMANTIC_AUTHORITY_MIGRATION")
print("DYNAMIC_CPR_POSITION=AFTER_OPENING_MECHANISM")
print("NEXT=NMI_P3_MANUSCRIPT_V0_1")
print("NEW_SUBJECT_RUNS=0")
