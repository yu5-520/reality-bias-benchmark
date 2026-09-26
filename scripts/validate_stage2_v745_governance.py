#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

POLICY = ROOT / "configs/stage2_g2_g5_execution_and_evaluation_policy_v2.json"
AUDIT = ROOT / "configs/stage2_semantic_audit_reference_protocol_v1.json"
MONITOR = ROOT / "configs/stage2_monitor_evaluation_protocol_v1.json"
ADDENDUM = ROOT / "configs/stage2_dual_general_chapter_independent_audit_monitor_eval_addendum_v1.json"
AUDIT_SCHEMA = ROOT / "schemas/stage2_semantic_audit_reference_record_v1.schema.json"
MONITOR_SCHEMA = ROOT / "schemas/stage2_monitor_evaluation_record_v1.schema.json"
PLAN = ROOT / "docs/R_Plan_v7.45.md"


def load(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def require(cond, msg):
    if not cond:
        raise SystemExit(msg)


def main():
    policy = load(POLICY)
    audit = load(AUDIT)
    monitor = load(MONITOR)
    addendum = load(ADDENDUM)
    audit_schema = load(AUDIT_SCHEMA)
    monitor_schema = load(MONITOR_SCHEMA)
    plan_text = PLAN.read_text(encoding="utf-8")

    require(policy["schema"] == "stage2-g2-g5-execution-and-evaluation-policy-v2", "unexpected policy schema")
    require(policy["prospective_natural_cells_total"] == 84, "prospective natural population must be 84")
    require(policy["publication_natural_cells_total_if_complete"] == 105, "five-group natural population must be 105")
    require(policy["first_attempt_only"] is True, "first-attempt-only must be frozen")
    require(policy["natural_phase"]["all_84_before_any_B"] is True, "all 84 A must precede any B")
    require(policy["natural_phase"]["repair_actions"] == 0, "natural A must contain zero repair actions")
    require(policy["semantic_audit"]["monitor_blind_until_seal"] is True, "semantic audit must remain monitor-blind")
    require(policy["monitor_evaluation"]["g1_in_primary_metrics"] is False, "G1 must not enter primary prospective monitor metrics")
    require(policy["engineering_phase"]["begins_after_primary_monitor_evaluation_sealed"] is True, "engineering must begin after primary monitor evaluation seal")
    require(policy["engineering_phase"]["semantic_audit_may_create_primary_repair_candidate"] is False, "audit must not backfill primary repair candidates")
    require(policy["engineering_phase"]["batch_order"] == ["G2", "G3", "G4", "G5"], "engineering batch order must be G2-G5")
    require(policy["x1_x3"]["natural_observation"] is True, "X1/X3 must remain natural-observation members")
    require(policy["x1_x3"]["primary_monitor_benchmark"] is True, "X1/X3 must remain primary monitor-benchmark members")
    require(policy["x1_x3"]["current_active_midrun_B"] is False, "X1/X3 active B must remain fail-closed")

    forbidden_audit = set(audit["forbidden_inputs"])
    require("monitor warning labels" in forbidden_audit, "audit must forbid monitor warning labels")
    require(audit["blindness"]["monitor_blind"] is True, "audit blindness must be explicit")
    require(audit["negative_evidence_rule"]["required"] is True, "negative evidence must be required")

    require(monitor["primary_population"]["natural_trajectories"] == 84, "monitor primary population must be 84")
    require(monitor["primary_population"]["g1_in_primary_metrics"] is False, "G1 must be excluded from primary monitor metrics")
    require(monitor["monitor_freeze"]["same_primary_version_across_g2_g5"] is True, "primary monitor version must be frozen across G2-G5")
    require(monitor["separation_rules"]["detector_miss_vs_unobservable_surface"] == "REQUIRED", "miss vs unobservable separation required")
    require(monitor["separation_rules"]["unsupported_warning_vs_rejected_warning"] == "REQUIRED", "unsupported vs rejected warning separation required")
    require(monitor["denominator_rules"], "monitor denominator rules must be present")
    require("POOLED_G2_G5" in monitor["required_breakdowns"], "pooled G2-G5 view required")
    require("BY_GROUP" in monitor["required_breakdowns"], "by-group monitor view required")
    require(monitor["engineering_relation"]["semantic_audit_may_create_primary_candidate"] is False, "audit may not create primary engineering candidate")

    ids = {p["id"] for p in addendum["principles"]}
    for needed in ("EXP-AU-01", "EXP-AU-04", "ENG-ME-04", "ENG-ME-07", "ENG-SQ-01", "ENG-SQ-03"):
        require(needed in ids, f"missing governing principle {needed}")

    require(audit_schema["title"] == "Stage-II Semantic Audit Reference Record v1", "unexpected audit record schema")
    require(monitor_schema["title"] == "Stage-II Monitor Evaluation Match Record v1", "unexpected monitor evaluation schema")

    for phrase in (
        "G2 21A -> G3 21A -> G4 21A -> G5 21A",
        "independent full semantic audit",
        "within-study prospective monitoring performance",
        "All 84 G2-G5 natural trajectories enter engineering eligibility accounting",
    ):
        require(phrase in plan_text, f"canonical plan missing phrase: {phrase}")

    print("Stage-II v7.45 governance validation PASS")
    print("84 natural A before B: PASS")
    print("monitor-blind semantic audit: PASS")
    print("G1 excluded from primary prospective monitor metrics: PASS")
    print("monitor miss vs unobservable surface separation: PASS")
    print("X1/X3 natural+monitor inclusion with active-B fail-closed: PASS")


if __name__ == "__main__":
    main()
