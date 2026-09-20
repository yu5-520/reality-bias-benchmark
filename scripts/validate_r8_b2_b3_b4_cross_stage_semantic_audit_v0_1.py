#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(rel):
    return json.loads((ROOT/rel).read_text(encoding="utf-8"))

def req(x,msg):
    if not x:
        raise SystemExit("R8_B234_VALIDATION_FAILED: "+msg)

def main():
    b2=load("results/r8_b2_natural_high_risk_window_audit_v0_1/summary.json")
    b3=load("results/r8_b3_r6_mechanism_window_audit_v0_1/summary.json")
    b4=load("results/r8_b4_r7_retrospective_recompute_audit_v0_1/summary.json")
    s=load("results/r8_cross_stage_semantic_status_v0_2/summary.json")
    cfg=load("configs/r8_b2_natural_high_risk_window_selection_v0.1.json")

    req(cfg["source_population"]["natural_trajectory_count"]==90,"natural source count")
    req(cfg["selected_window_counts"]=={"C":21,"P":15,"R":44,"unique_trajectories":52},"B2 selection counts")
    req(cfg["exhaustiveness"]["all_possible_semantic_C_windows_exhaustively_adjudicated"] is False,"B2 C exhaustiveness guard")
    req(b2["adjudication"]["C_supported"]==0 and b2["adjudication"]["P_supported"]==0 and b2["adjudication"]["R_supported"]==0,"B2 selected positives")
    req(b2["interpretation"]["natural_cpr_absence_claim_allowed"] is False,"B2 absence guard")

    req(b3["source_cases"]==29,"B3 source count")
    req(b3["adjudication"]["C_supported"]==2,"B3 C count")
    req(set(b3["adjudication"]["supported_C_case_ids"])=={"wave-3-56ee79f97f54","wave-4-cf726639de1d"},"B3 C identities")
    req(b3["adjudication"]["P_supported"]==0 and b3["adjudication"]["R_supported"]==0,"B3 P/R counts")

    req(b4["source_cases"]==4 and b4["source_traces"]==8,"B4 source geometry")
    req(b4["r7_s_reopened_calls"]==32,"B4 reopen count")
    req(b4["r7_s_recomputed_descendants"]==135,"B4 recompute count")
    req(b4["adjudication"]["new_post_repair_C_supported"]==0,"B4 new C")
    req(b4["adjudication"]["new_post_repair_P_supported"]==0,"B4 new P")
    req(b4["adjudication"]["R_supported"]==0,"B4 R")

    req(s["cross_stage_coupling"]["status"]=="BLOCKED_FOR_FINAL_SYNTHESIS_UNTIL_B2_EXHAUSTIVENESS_OR_PREDECLARED_STOP_RULE","R8-C block")
    req(s["interpretation"]["first_round_P_absence_claim_allowed"] is False,"P absence guard")
    req(s["interpretation"]["first_round_R_absence_claim_allowed"] is False,"R absence guard")

    for rel in [
        "docs/reports/2026-09-20/R8_B2_B3_B4_Cross_Stage_Semantic_Audit_Result_v1.md",
        "theory/change_notes/CN-R-065_b2_b3_b4_cross_stage_semantic_audit_freeze.md",
    ]:
        req((ROOT/rel).exists(),"missing "+rel)

    print("R8_B234_VALIDATION=PASS")
    print("B2_STATUS=NONEXHAUSTIVE_HIGH_RISK_WINDOW_AUDIT_COMPLETE")
    print("B3_C_SUPPORTED=2")
    print("B4_R_SUPPORTED=0")
    print("R8C_STATUS=BLOCKED")
    print("SUBJECT_RERUN_REQUIRED=NO")

if __name__=="__main__":
    main()
