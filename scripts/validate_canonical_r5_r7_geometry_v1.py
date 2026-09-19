from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def require(ok,message):
    if not ok:
        raise SystemExit("FAIL: "+message)


def load_json(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))


def text(path):
    return (ROOT/path).read_text(encoding="utf-8")


def main():
    g=load_json("configs/process_reality_canonical_experiment_geometry_v1.0.json")
    require(g["status"]=="FORWARD_ACTIVE_V5_4","canonical geometry not active")
    require(g["r5"]["new_control_branches_per_case"]==0,"canonical R5 may not add control")
    require(g["r5"]["new_intervention_branches_per_case"]==1,"canonical R5 must add one intervention")
    require(g["r5"]["canonical_replicate_count"]==1,"canonical R5 replicate count must be one")
    require(g["r5"]["natural_reference_must_be_rerun"] is False,"N0 must not be rerun")
    require(g["r6"]["new_subject_provider_branches_per_case"]==0,"R6 must remain passive")
    require(g["r7"]["canonical_arms"]==["R7_P_PERSISTENT_SEMANTIC","R7_S_STRUCTURED_LINEAGE_REPAIR"],"canonical R7 arm set mismatch")
    require(g["r7"]["new_c1_one_shot_branches_per_case"]==0,"R7 may not rerun C1")
    require(g["r7"]["new_provider_branches_per_case"]==2,"R7 must add exactly two branches")
    require(g["r7"]["canonical_replicate_count"]==1,"R7 replicate count must be one")
    require(g["full_case_to_r7_new_provider_trajectory_count"]==3,"full R5-R7 provider geometry must equal three")

    reclass=load_json("manifests/v5_4_r5_r7_canonical_reclassification_2026-09-19_v0_1.json")
    require(reclass["historical_evidence_mutated"] is False,"historical evidence mutation forbidden")
    require(reclass["r5"]["canonical_r5_intervention_count_first_two_waves"]==11,"historical canonical R5 count mismatch")
    require(reclass["r5"]["forward_canonical_rule"]["selection_is_outcome_aware"] is False,"historical canonical selection must be deterministic")
    require(reclass["r7"]["mapping"]["C1_ONE_SHOT"]=="R5_I_REFERENCE_NOT_CANONICAL_R7_EXECUTION","C1 mapping mismatch")
    require(reclass["r7"]["mapping"]["C2_PERSISTENT_FIELD"]=="R7_P_PERSISTENT_SEMANTIC","C2 mapping mismatch")
    require(reclass["r7"]["mapping"]["C3_ALR"]=="R7_S_STRUCTURED_LINEAGE_REPAIR","C3 mapping mismatch")
    require(reclass["r7"]["forward_new_branch_count_per_case"]==2,"historical R7 forward branch geometry mismatch")

    r5prepare=text("arena/prepare_v5_cross_domain_r5_canonical.py")
    for token in [
        '"synthetic_control_branch_count":0',
        '"canonical_replicate_count":1',
        '"new_provider_branches_per_case":1',
        '"natural_reference_rerun_required":False',
        'condition_id=INTERVENTION_CONDITION',
    ]:
        require(token in r5prepare,f"canonical R5 preparer missing {token}")

    r5run=text("arena/run_v5_cross_domain_r5_canonical.py")
    for token in [
        'branch_count")!=plan.get("case_count")',
        'synthetic_control_branch_count")!=0',
        'canonical_replicate_count")!=1',
        'condition_id")!=INTERVENTION_CONDITION',
    ]:
        require(token in r5run,f"canonical R5 runner missing guard {token}")

    r7prepare=text("arena/prepare_r7_dual_intervention_plan.py")
    for token in [
        '"R7_P_PERSISTENT_SEMANTIC"',
        '"R7_S_STRUCTURED_LINEAGE_REPAIR"',
        '"r5_c1_reference_execution_count":0',
        '"canonical_replicate_count":1',
        '"new_provider_branch_count":2',
    ]:
        require(token in r7prepare,f"canonical R7 preparer missing {token}")

    r7run=text("arena/run_r7_dual_intervention_real.py")
    require('branch_count"]!=2' in r7run,"canonical R7 runner must require two branches")
    require('r5_c1_reference_execution_count"]!=0' in r7run,"canonical R7 runner must forbid C1 execution")

    for path in [
        "theory/theory_contract_v0.15.md",
        "docs/R_Plan_v5.4.md",
        "docs/R5_canonical_single_intervention_protocol_v1.0.md",
        "docs/R7_dual_intervention_protocol_v2.0.md",
    ]:
        body=text(path)
        require("replicate" in body.lower() or "repeated" in body.lower(),f"{path} missing repetition boundary")

    print("PASS: v5.4 canonical R5/R7 geometry is synchronized")
    print("R5_NEW_PROVIDER_BRANCHES_PER_CASE=1")
    print("R6_NEW_PROVIDER_BRANCHES_PER_CASE=0")
    print("R7_NEW_PROVIDER_BRANCHES_PER_CASE=2")
    print("FULL_R5_TO_R7_NEW_PROVIDER_TRAJECTORIES_PER_CASE=3")
    print("HISTORICAL_EVIDENCE_MUTATED=NO")
    print("PROVIDER_RUN_AUTHORIZED=NO")


if __name__=="__main__":
    main()
