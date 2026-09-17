#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DESIGN_HASH = "5064e255da26949a152a2300fe659ebdddddc9b44f1a97a4b31d7796005a959d"
PREDECESSOR_HASH = "d8783a9c3e0a264c3119ee72e63db9b61d51f0d633ff6dde66068751c31701de"
FIRST_BATCH_HASH = "0d4dd464d10bfc9a5b4307856e2c070bfaa521951e00cd0f147eeb80063e4beb"
PARENT_HASH = "aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c"
SOURCE_MAIN_SHA = "833aac59db6023ed3f197bad00944f7c78072d61"

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()

def digest_without(obj, key):
    cp = dict(obj)
    cp.pop(key, None)
    return digest(cp)

audit = load("configs/r6/r6d_matched_stock_robustness_candidate_audit_v0.1.json")
plan = load("configs/r6/r6d_matched_stock_robustness_plan_v0.1.json")
s3 = load("configs/r6/r6d_s3_matched_stock_b_envelope_v0.1.json")
s4 = load("configs/r6/r6d_s4_matched_stock_c_envelope_v0.1.json")
freeze = load("manifests/r6d_matched_stock_robustness_design_freeze_2026-09-17_v0_1.json")
predecessor = load("manifests/r6d_specificity_preexecution_design_freeze_2026-09-17_v0_1.json")
first_batch = load("manifests/r6d_first_real_subject_2026-09-17_v0_1.json")
selection_v02 = load("configs/r5r6_specificity_field_selection_contract_v0.2.json")
protocol = (ROOT / "docs/R6D_matched_stock_robustness_protocol_v0.1.md").read_text(encoding="utf-8")

assert predecessor["design_hash"] == PREDECESSOR_HASH
assert first_batch["scientific_subject"]["evidence_batch_hash"] == FIRST_BATCH_HASH
assert audit["selection_timing"] == "POST_FIRST_BATCH_PRE_SECOND_BATCH"
assert audit["first_batch_outcomes_known"] is True
assert audit["eligibility_rule_uses_first_batch_outcome"] is False
assert audit["all_eligible_candidates_included"] is True
assert audit["source_binding"]["source_main_sha"] == SOURCE_MAIN_SHA
assert audit["source_binding"]["common_parent_state_hash"] == PARENT_HASH
assert audit["source_binding"]["predecessor_design_hash"] == PREDECESSOR_HASH
assert audit["source_binding"]["first_batch_evidence_hash"] == FIRST_BATCH_HASH
assert audit["source_binding"]["first_batch_evidence_role"] == "KNOWN_PROVENANCE_ONLY_NOT_SELECTION_CRITERION"
assert selection_v02["first_control_pool_rule"]["future_same_family_control_may_be_added_append_only"] is True
assert selection_v02["first_control_pool_rule"]["future_same_family_control_must_not_replace_first_s1_after_outcomes"] is True

expected_controls = [
    "shared_state.inventory_stockout_assessment_v1.B.stock",
    "shared_state.inventory_stockout_assessment_v1.C.stock",
]
assert audit["eligible_candidate_locators"] == expected_controls
assert audit["included_candidate_locators"] == expected_controls
inv = {x["locator"]: x for x in audit["candidate_inventory"]}
assert inv["shared_state.inventory_stockout_assessment_v1.A.preliminary_stock"]["eligible"] is False
assert inv[expected_controls[0]]["eligible"] is True and inv[expected_controls[0]]["value"] == 900
assert inv[expected_controls[1]]["eligible"] is True and inv[expected_controls[1]]["value"] == 3400
assert audit["eligibility_rule"]["selection_mode"] == "INCLUDE_ALL_ELIGIBLE_CANDIDATES"
assert audit["eligibility_rule"]["semantic_role"] == "DIRECT_STOCK_QUANTITY"
assert audit["eligibility_rule"]["container_status_exact"] == "fact"
assert audit["audit_hash"] == digest_without(audit, "audit_hash")

for env, cid, locator in [
    (s3, "S3_MATCHED_ORDINARY_STOCK_B_DOWNGRADE", expected_controls[0]),
    (s4, "S4_MATCHED_ORDINARY_STOCK_C_DOWNGRADE", expected_controls[1]),
]:
    assert env["schema"] == "RB-R5R6-ATOMIC-EPISTEMIC-ANNOTATION-v0.2"
    assert env["condition_id"] == cid
    assert env["target_locator"] == locator
    assert env["mechanical_primitive"] == "ONE_SHOT_TARGET_SCOPED_EPISTEMIC_STATUS_ANNOTATION"
    assert env["from_status"] == "fact" and env["to_status"] == "unconfirmed"
    assert env["direct_exposure_limit"] == 1
    assert env["experiment_origin_reinjection_forbidden"] is True
    assert env["persistent_state_mutation"] is False
    assert env["original_target_value_mutation"] is False
    assert env["opposite_fact_supplied"] is False
    assert env["replacement_conclusion_supplied"] is False
    assert env["desired_terminal_answer_supplied"] is False
    assert env["envelope_hash"] == digest_without(env, "envelope_hash")

assert s3["envelope_hash"] == "7fe7d9af972e9c07d8386c657e6badcdcc2ac499d31e7be652d1e5b81ed1a9cd"
assert s4["envelope_hash"] == "41bafbe740e7bd431033ce124b3e022a6920136a77f6f589e040f6ea9aa12739"

assert freeze["design_hash"] == DESIGN_HASH
assert digest(freeze["design_core"]) == DESIGN_HASH
assert freeze["bindings"]["predecessor_design_hash"] == PREDECESSOR_HASH
assert freeze["bindings"]["first_batch_evidence_hash"] == FIRST_BATCH_HASH
assert freeze["bindings"]["source_main_sha"] == SOURCE_MAIN_SHA
assert freeze["status"] == "DESIGN_FROZEN_NOT_RUNTIME_READY_NOT_AUTHORIZED"
assert freeze["runtime_readiness"]["real_subject_runner_bound"] is False
assert freeze["runtime_readiness"]["real_subject_workflow_bound"] is False
assert freeze["authorization"]["scientific_provider_run"] is False
assert freeze["authorization"]["paid_evaluator_run"] is False
assert freeze["authorization"]["semantic_cpr_adjudication"] is False
assert freeze["manifest_hash"] == digest_without(freeze, "manifest_hash")

assert plan["design_hash"] == DESIGN_HASH
assert plan["status"] == "DESIGN_FROZEN_NOT_RUNTIME_READY_NOT_AUTHORIZED"
assert plan["source_binding"]["common_parent_state_hash"] == PARENT_HASH
assert plan["source_binding"]["predecessor_design_hash"] == PREDECESSOR_HASH
assert plan["source_binding"]["first_batch_evidence_hash"] == FIRST_BATCH_HASH
assert plan["candidate_audit"]["audit_hash"] == audit["audit_hash"]
assert plan["plan_hash"] == digest_without(plan, "plan_hash")

cids = [x["condition_id"] for x in plan["conditions"]]
assert cids == [
    "S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL",
    "S3_MATCHED_ORDINARY_STOCK_B_DOWNGRADE",
    "S4_MATCHED_ORDINARY_STOCK_C_DOWNGRADE",
]
assert not any(x.startswith("S0_") for x in cids)
assert plan["conditions"][0]["envelope_hash"] == predecessor["specificity_binding"]["s2_envelope_hash"]
assert plan["conditions"][1]["envelope_hash"] == s3["envelope_hash"]
assert plan["conditions"][2]["envelope_hash"] == s4["envelope_hash"]
assert all(x["source_authority_scope"] == "CONTAINER_LEVEL_FACT" for x in plan["conditions"])
op = plan["common_operator"]
assert op["mechanical_primitive"] == "ONE_SHOT_TARGET_SCOPED_EPISTEMIC_STATUS_ANNOTATION"
assert op["from_status"] == "fact" and op["to_status"] == "unconfirmed"
assert op["direct_exposure_limit"] == 1
assert op["experiment_origin_reinjection_count"] == 0
assert op["persistent_experiment_origin_state_mutation"] is False

m = plan["matched_execution_design"]
assert m["planned_branch_count"] == 9 and m["replicates"] == 3
assert m["same_parent_repeats_are_independent_population_samples"] is False
rows = m["rows"]
assert len(rows) == 9
expected_orders = {1: cids, 2: [cids[1], cids[2], cids[0]], 3: [cids[2], cids[0], cids[1]]}
for rep in (1, 2, 3):
    rr = sorted([x for x in rows if x["replicate_index"] == rep], key=lambda x: x["execution_order"])
    assert [x["condition_id"] for x in rr] == expected_orders[rep]
for row in rows:
    assert row["row_hash"] == digest_without(row, "row_hash")

h = plan["observation_horizon"]
assert h["branch_start_parent_turn"] == 8
assert h["direct_response_turn"] == 9
assert h["post_consumption_start_turn"] == 10
assert h["absolute_turn_cap"] == 16
assert h["max_additional_agent_turns"] == 8
assert h["natural_early_termination_interpretation"] == "RIGHT_CENSORING"
b = plan["budget_gate"]
assert b["per_branch_max_calls"] == 64
assert b["per_branch_spending_ceiling"] == 0.25
assert b["global_spending_ceiling"] == 2.25
assert b["global_spending_ceiling"] == m["planned_branch_count"] * b["per_branch_spending_ceiling"]
assert b["automatic_paid_evaluator"] is False

a = plan["analysis_freeze"]
assert a["historical_first_batch_primary_contrast"] == "S2_MINUS_S1"
assert a["historical_first_batch_primary_contrast_is_replaced"] is False
assert a["primary_robustness_contrasts"] == ["S2_MINUS_S3", "S2_MINUS_S4"]
assert a["matched_ordinary_target_spread"] == "S3_MINUS_S4"
assert a["fresh_s0_included"] is False
assert a["first_batch_s0_role"] == "EXTERNAL_AUXILIARY_NATURAL_VARIABILITY_REFERENCE"
assert a["first_batch_s0_evidence_hash"] == FIRST_BATCH_HASH
assert a["process_distance_domains"] == ["STRUCTURAL_DISTANCE", "INHERITANCE_DISTANCE", "EPISTEMIC_AUTHORITY_DISTANCE"]
assert a["post_hoc_total_scalar_forbidden"] is True
assert a["escape_derived_specificity_status"] == "NOT_ESTABLISHED_PRE_RUN"
assert a["semantic_cpr_status"] == "NOT_ADJUDICATED"

assert plan["runtime_readiness"] == {"real_subject_runner_bound": False, "real_subject_workflow_bound": False, "runtime_plan_builder_bound": False}
assert plan["authorization"]["authorization_status"] == "NOT_AUTHORIZED"
assert plan["authorization"]["scientific_provider_run"] is False
assert plan["authorization"]["paid_evaluator_run"] is False
assert plan["authorization"]["semantic_cpr_adjudication"] is False

required_text = [
    "POST_FIRST_BATCH_PRE_SECOND_BATCH",
    "first-batch outcomes are known",
    "all eligible candidates",
    "container-level",
    "S2 - S3",
    "S2 - S4",
    "S3 - S4",
    "There is **no fresh S0**",
    "NOT ESTABLISHED",
    "NOT_ADJUDICATED",
]
for token in required_text:
    assert token in protocol, f"protocol missing required boundary: {token}"

print("PASS: R6-D matched-stock robustness v0.1 design is frozen, append-only, runtime-unbound, and not authorized")
print("DESIGN_HASH=" + DESIGN_HASH)
print("CANDIDATE_AUDIT_HASH=" + audit["audit_hash"])
print("PLAN_HASH=" + plan["plan_hash"])
