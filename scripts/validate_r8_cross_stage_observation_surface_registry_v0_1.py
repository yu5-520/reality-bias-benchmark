#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"configs/r8_cross_stage_observation_surface_registry_v0.1.json"
SUMMARY=ROOT/"results/r8_cross_stage_observation_surface_registry_v0_1/summary.json"
STAGES=ROOT/"results/r8_cross_stage_observation_surface_registry_v0_1/stage_observation_registry.jsonl"


def require(v,msg):
    if not v:
        raise SystemExit("R8_CROSS_STAGE_VALIDATION_FAILED: "+msg)


def main():
    cfg=json.loads(CFG.read_text())
    s=json.loads(SUMMARY.read_text())
    stages=[json.loads(x) for x in STAGES.read_text().splitlines() if x.strip()]

    require(cfg["schema"]=="RB-R8-CROSS-STAGE-OBSERVATION-SOURCE-BINDING-v0.1","config schema")
    require(len(cfg["natural_artifacts"])==6,"six natural artifacts")
    require(cfg["expected"]["natural_trajectory_count"]==90,"natural count")
    require(cfg["expected"]["r5_r6_target_bound_case_count"]==29,"B1 count")
    require(cfg["expected"]["r7_trace_count"]==8,"R7 trace count")

    require(s["semantic_cpr_status"]=="PARTIAL_B1_ONLY","overall semantic status")
    require(s["b1_status"]=="FROZEN_COMPLETE","B1 status")
    require(s["b2_status"]=="READY_FOR_SEMANTIC_WINDOW_EXTRACTION","B2 status")
    require(s["b3_status"]=="READY_FOR_MECHANISM_WINDOW_ADJUDICATION","B3 status")
    require(s["b4_status"]=="READY_FOR_RETROSPECTIVE_PERMISSION_ADJUDICATION","B4 status")
    require(s["r8c_status"]=="BLOCKED_UNTIL_B2_B3_B4_SEMANTIC_RESULTS","R8-C must remain blocked")

    n=s["natural_structural_summary"]
    require(n["trace_count"]==90,"natural traces")
    require(n["role_reentry_trace_count"]==90,"role reentry traces")
    require(n["reviewer_present_trace_count"]==45,"reviewer trace count")
    require(n["post_review_reentry_trace_count"]==44,"post-review reentry count")
    require(n["post_review_new_agent_trace_count"]==15,"post-review new-agent count")
    require(n["invoke_agent_event_count"]==1301,"invoke count")
    require(n["write_state_event_count"]==2398,"state write count")

    require(len(stages)==4,"four observation branches")
    ids={x["stage_surface_id"] for x in stages}
    require(ids=={
        "R8-B1:R5-R6-TARGET-BOUND",
        "R8-B2:R2-R4-NATURAL",
        "R8-B3:R6-MECHANISM",
        "R8-B4:R7-RETROSPECTIVE",
    },"stage identities")

    b1=next(x for x in stages if x["stage_surface_id"].startswith("R8-B1"))
    require(b1["frozen_semantic_result"]["P_supported_within_B1_scope"]==0,"B1 P count")
    require(b1["frozen_semantic_result"]["R_supported_within_B1_scope"]==0,"B1 R count")
    require("not a cross-stage" in b1["guard"],"B1 P/R scope guard")

    e=s["execution_boundary"]
    require(e["new_provider_calls"]==0 and e["new_paid_evaluator_calls"]==0 and e["subject_reruns"]==0,"zero-call boundary")
    require(e["raw_evidence_mutated"] is False,"raw evidence immutable")

    for rel in [
        "docs/R_Plan_v5.6.md",
        "theory/theory_contract_v0.17.md",
        "docs/R8_Dynamic_CPR_Permission_Penetration_Protocol_v0.4.md",
        "docs/reports/2026-09-20/R8B1_Target_Bound_Repositioning_Note_v1.md",
        "docs/reports/2026-09-20/R8_Cross_Stage_Observation_Surface_Registry_Result_v1.md",
    ]:
        require((ROOT/rel).exists(),"missing "+rel)

    print("R8_CROSS_STAGE_VALIDATION=PASS")
    print("OVERALL_SEMANTIC_STATUS=PARTIAL_B1_ONLY")
    print("R8C_STATUS=BLOCKED")
    print("SUBJECT_RERUN_REQUIRED=NO")


if __name__=="__main__":
    main()
