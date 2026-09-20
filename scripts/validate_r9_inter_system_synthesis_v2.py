#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(p):
    return json.loads((ROOT/p).read_text())

def req(v,m):
    if not v:
        raise SystemExit("R9_V2_VALIDATION_FAILED: "+m)

c=load("configs/r9_innovation_boundary_contract_v2.json")
m=load("manifests/r9_inter_system_process_reality_synthesis_2026-09-20_v2.json")

req(c["primary_innovation_target"]=="SEMANTIC_PROCESS_INTEGRITY_STACK","primary innovation target")
req(c["experimental_realization"]=="MULTI_AGENT_PROCESS_REALITY","experimental realization")
req(c["broader_outlook"]=="INTER_SYSTEM_PROCESS_REALITY","system outlook")
req(c["reflexive_human_ai_case"]["formal_cpr_evidence"] is False,"reflexive CPR boundary")
req(c["reproducibility"]["independent_external_replication_completed"] is False,"replication boundary")
req(c["authorization"]=={
    "subject_runs":0,
    "provider_calls":0,
    "paid_evaluator_calls":0,
    "raw_evidence_mutation":False,
    "new_cpr_adjudication":False
},"authorization")

for p in [m["canonical_report"], *m["supporting_files"]]:
    req((ROOT/p).exists(),"missing "+p)

req((ROOT/"docs/supplementary/NML_Supplementary_Note_S1_perfection_like_planning_drift.md").exists(),"missing reflexive note")
req((ROOT/"schemas/semantic_lineage_closure_v0.1.schema.json").exists(),"missing lineage closure")
req((ROOT/"schemas/semantic_repair_packet_v0.1.schema.json").exists(),"missing repair packet")

print("R9_V2_VALIDATION=PASS")
print("PRIMARY_INNOVATION=SEMANTIC_PROCESS_INTEGRITY_STACK")
print("EXPERIMENTAL_REALIZATION=MULTI_AGENT")
print("BROADER_OUTLOOK=INTER_SYSTEM_PROCESS_REALITY")
print("REFLEXIVE_CASE_FORMAL_CPR=false")
print("NEW_SUBJECT_RUNS=0")
print("PAPER_LEVEL_FREEZE=NOT_YET")
