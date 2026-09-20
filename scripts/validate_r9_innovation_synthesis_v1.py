#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text())
def req(v,m):
    if not v: raise SystemExit("R9_INNOVATION_VALIDATION_FAILED: "+m)
c=load("configs/r9_innovation_boundary_contract_v1.json")
l=load("configs/r9_literature_registry_v1.json")
m=load("manifests/r9_innovation_synthesis_2026-09-20_v1.json")
req(c["role"]=="INNOVATION_SYNTHESIS_PRIOR_ART_BOUNDARY_OUTLOOK","role")
req(c["no_new_subject_evidence"] is True,"evidence boundary")
req(len(c["core_claims"])==5,"core claim count")
req("FIRST_STORED_VS_SUPPORTED_DISTINCTION" in c["forbidden_novelty_phrases"],"F1 guard")
req("FIRST_TASK_LEVEL_AUTHORITY_MODEL" in c["forbidden_novelty_phrases"],"F2 guard")
req(l["source_count"]==15,"literature count")
req(l["peer_reviewed_anchor_count"]==12,"peer reviewed count")
ids={x["id"] for x in l["sources"]}
req({"L1","L3","L7","L9","L10","F1","F2","F3"}.issubset(ids),"anchor presence")
req(m["execution_boundary"]=={"subject_runs":0,"provider_calls":0,"paid_evaluator_calls":0,"raw_evidence_mutated":False},"execution boundary")
for p in m["outputs"].values():
    req((ROOT/p).exists(),"missing "+p)
print("R9_INNOVATION_VALIDATION=PASS")
print("LITERATURE_SOURCES=15")
print("PEER_REVIEWED_ANCHORS=12")
print("NEW_SUBJECT_RUNS=0")
print("PAPER_LEVEL_FREEZE=NOT_YET")
