#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def load(rel):
    return json.loads((ROOT/rel).read_text(encoding="utf-8"))


def req(v,msg):
    if not v:
        raise SystemExit("R8_TRAJECTORY_FIRST_VALIDATION_FAILED: "+msg)


def main():
    c=load("configs/r8_dynamic_semantic_audit_contract_v0.4.json")
    s=load("results/r8_forward_semantic_chain_status_v0_3/summary.json")
    src=load("configs/r8_trajectory_first_source_registry_v0.1.json")
    schema=load("schemas/r8_trajectory_semantic_audit_packet_v0.1.schema.json")

    req(c["primary_unit"]=="DYNAMIC_SEMANTIC_EPISODE","primary unit")
    req(c["structural_layer_role"]=="EVIDENCE_INDEXING_ONLY","structural role")
    req(c["semantic_reconstruction_required_before_verdict"] is True,"reconstruction gate")
    req(c["C"]["source_wording_continuity_required"] is False,"functional C lineage")
    req(c["P"]["mandatory_alignment"]==[
        "ORIGINAL_GOAL","AUTHORIZED_BOUNDARY","REALIZED_PROCESS_SCOPE","FINAL_RESULT_AND_ACTUAL_CHANGES"
    ],"P alignment")
    req(c["R"]["censored_active_chain_negative_allowed"] is False,"censor R guard")
    req(c["coupling"]["joint_review_required"] is True,"joint CPR review")

    req(s["status"]=="TRAJECTORY_FIRST_CHAIN_REPAIR_COMPLETE_REAUDIT_REQUIRED","status")
    req("C_TOTAL_EQUALS_2" in s["invalid_forward_aggregates"],"C aggregate invalidation")
    req("P_TOTAL_EQUALS_0" in s["invalid_forward_aggregates"],"P aggregate invalidation")
    req("R_TOTAL_EQUALS_0" in s["invalid_forward_aggregates"],"R aggregate invalidation")
    req(s["r8c_status"]=="BLOCKED_UNTIL_TRAJECTORY_FIRST_REAUDIT","R8C blocked")

    req(src["required_censor_inclusion"]["natural_turn_budget_exhausted_known_count"]==42,"42 natural censored")
    req("r7:prospective-ecommerce-natural-0001:triad:0001:c3_alr" in src["required_censor_inclusion"]["explicit_priority_run_ids"],"historical R7 censored inclusion")
    req(len(src["r7_historical_and_canonical"])>=4,"R7 source breadth")

    props=schema["properties"]
    for f in ("model_calls","message_ledger","invocation_ledger","event_ledger","termination_censor_state","remaining_work"):
        req(f in props,"packet missing "+f)

    for rel in [
        "docs/R_Plan_v5.7.md",
        "theory/theory_contract_v0.18.md",
        "docs/R8_Trajectory_First_Dynamic_Semantic_Audit_Protocol_v0.5.md",
        "arena/build_r8_trajectory_first_semantic_packets.py",
        "schemas/r8_dynamic_semantic_episode_v0.1.schema.json",
    ]:
        req((ROOT/rel).exists(),"missing "+rel)

    print("R8_TRAJECTORY_FIRST_VALIDATION=PASS")
    print("STRUCTURE_ROLE=EVIDENCE_INDEX_ONLY")
    print("LEGACY_TOTALS_CANONICAL=NO")
    print("ACTIVE_CENSOR_NEGATIVE_ALLOWED=NO")
    print("SUBJECT_RERUN_REQUIRED=NO")


if __name__=="__main__":
    main()
