#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "results/r8b_dynamic_cpr_first_round_v0_1/summary.json"
MANIFEST = ROOT / "manifests/r8b_dynamic_cpr_first_round_2026-09-20_v0_1.json"


def require(cond, msg):
    if not cond:
        raise SystemExit("R8B_VALIDATION_FAILED: " + msg)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    s = load(SUMMARY)
    m = load(MANIFEST)

    require(s["schema"] == "RB-R8B-DYNAMIC-CPR-FIRST-ROUND-SUMMARY-v0.1", "summary schema")
    require(s["case_count"] == 29, "case count")
    require(s["overall_status_counts"] == {"ADJUDICATED_NON_CPR": 27, "ADJUDICATED_C": 2}, "overall counts")
    require(s["C_status_counts"] == {"NOT_ESTABLISHED": 27, "SUPPORTED": 2}, "C counts")
    require(s["P_status_counts"] == {"NOT_ESTABLISHED": 29}, "P counts")
    require(s["R_status_counts"] == {"NOT_ESTABLISHED": 29}, "R counts")
    require(
        set(s["supported_C_case_ids"]) ==
        {"wave-3-56ee79f97f54", "wave-4-cf726639de1d"},
        "supported C identities",
    )
    require(s["supported_coupling_edge_count"] == 0, "coupling count")
    require(s["stronger_system_inertia_candidate_count"] == 4, "stronger candidate count")
    require(s["stronger_candidate_C_supported_count"] == 2, "stronger supported C count")
    require(s["stronger_candidate_C_not_established_count"] == 2, "stronger non-C count")
    require(s["selected_mechanism_set_not_prevalence_denominator"] is True, "prevalence guard")

    i = s["interpretation"]
    require(i["system_inertia_equivalent_to_C"] is False, "System Inertia != C")
    require(i["system_inertia_equivalent_to_R"] is False, "System Inertia != R")
    require(i["extra_agent_call_equivalent_to_P"] is False, "extra calls != P")
    require(i["r5_challenge_equivalent_to_R"] is False, "R5 challenge != R")
    require(i["prevalence_claim_allowed"] is False, "prevalence forbidden")

    e = s["execution_boundary"]
    require(e["new_provider_calls"] == 0, "provider calls")
    require(e["new_paid_evaluator_calls"] == 0, "paid evaluator calls")
    require(e["subject_reruns"] == 0, "subject reruns")
    require(e["raw_evidence_mutated"] is False, "raw evidence mutation")

    require(m["status"] == "FROZEN_APPEND_ONLY_SEMANTIC_ADJUDICATION", "manifest status")
    require(m["result_boundary"]["positive_C_count"] == 2, "manifest C count")
    require(m["result_boundary"]["positive_P_count"] == 0, "manifest P count")
    require(m["result_boundary"]["positive_R_count"] == 0, "manifest R count")

    for rel in [
        "docs/R_Plan_v5.5.md",
        "theory/theory_contract_v0.16.md",
        "docs/R8_Dynamic_CPR_Permission_Penetration_Protocol_v0.3.md",
        "configs/cpr_definition_contract_v0.3.json",
        "configs/cpr_adjudication_contract_v0.3.json",
        "docs/reports/2026-09-20/R8B_Dynamic_CPR_Permission_Penetration_Adjudication_Result_v1.md",
        "theory/change_notes/CN-R-063_r8b_dynamic_cpr_adjudication_freeze.md",
    ]:
        require((ROOT / rel).exists(), "missing " + rel)

    print("R8B_VALIDATION=PASS")
    print("C_SUPPORTED=2")
    print("P_SUPPORTED=0")
    print("R_SUPPORTED=0")
    print("PREVALENCE_CLAIM_ALLOWED=NO")
    print("SUBJECT_RERUN_REQUIRED=NO")


if __name__ == "__main__":
    main()
