#!/usr/bin/env python3
import gzip, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text())
def req(v,m):
    if not v: raise SystemExit("R8_SECOND_AUDIT_COMBINED_VALIDATION_FAILED: "+m)
def n_gz(p):
    with gzip.open(ROOT/p,"rt",encoding="utf-8") as f: return sum(1 for x in f if x.strip())
a=load("results/r8_trajectory_first_second_audit_v0_1/summary.json")
e=load("results/r8_ecommerce_discovery_trajectory_first_reaudit_v0_1/summary.json")
c=load("results/r8_trajectory_first_second_audit_combined_v0_2/summary.json")
s=load("results/r8_forward_semantic_chain_status_v0_5/summary.json")
req(n_gz("results/r8_trajectory_first_second_audit_v0_1/trajectory_second_audit_records.jsonl.gz")==141,"141 records")
req(n_gz("results/r8_ecommerce_discovery_trajectory_first_reaudit_v0_1/trajectory_audit_records.jsonl.gz")==9,"9 discovery records")
req(a["P"]["supported_trajectory_count"]==19 and a["R"]["supported_trajectory_count"]==13,"141 CPR")
req(e["formal_batch001_counts"]=={"C_supported":1,"P_supported":1,"R_supported":2},"formal ecommerce")
req(c["analysis_inventory"]["trajectory_count"]==150,"150 inventory")
req(c["dynamic_C"]["supported_high_confidence_unique_count"]==3,"C=3")
req(c["dynamic_P"]["supported_trajectory_count"]==23,"P=23")
req(c["dynamic_R"]["supported_retrospective_generative_trajectory_count"]==18,"R=18")
req(c["coupling"]["supported_edge_counts"]=={"R_GENERATES_P":17,"R_GENERATES_C":1,"C_DRIVES_P":2},"coupling")
req(c["claim_boundary"]["population_rate_claim_allowed_on_combined_150"] is False,"denominator guard")
req(s["r8c_status"]=="READY_FOR_CENSOR_AWARE_CROSS_STAGE_COUPLING_SYNTHESIS","R8C")
print("R8_SECOND_AUDIT_COMBINED_VALIDATION=PASS")
print("TRAJECTORIES=150")
print("DYNAMIC_C_P_R=3_23_18")
print("FORMAL_ECOMMERCE_C_P_R=1_1_2")
print("SUBJECT_RERUN_REQUIRED=NO")
