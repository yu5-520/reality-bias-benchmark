#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = "configs/r6/r6d_matched_stock_robustness_formal_subject_gate_v0.1.json"
DESIGN_HASH = "5064e255da26949a152a2300fe659ebdddddc9b44f1a97a4b31d7796005a959d"
PREDECESSOR_HASH = "d8783a9c3e0a264c3119ee72e63db9b61d51f0d633ff6dde66068751c31701de"
AUDIT_HASH = "ffce11ae46a2efa966368c21da610fac967fe5132ccc7dddea80e6caa3f9ec70"
PLAN_HASH = "b0fe89c08c20da61376077e23e484914bd260c2a7e00aa2a6b57c459380dbab9"
FIRST_BATCH_HASH = "0d4dd464d10bfc9a5b4307856e2c070bfaa521951e00cd0f147eeb80063e4beb"
GATE_HASH = "af62079cf9d0727813095648cb85268895b960f7d14fb5644e3151f6711bbcf9"


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def digest_without(obj, key):
    material = dict(obj)
    material.pop(key, None)
    payload = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


gate = load(GATE_PATH)
plan = load("configs/r6/r6d_matched_stock_robustness_plan_v0.1.json")
freeze = load("manifests/r6d_matched_stock_robustness_design_freeze_2026-09-17_v0_1.json")
audit = load("configs/r6/r6d_matched_stock_robustness_candidate_audit_v0.1.json")
predecessor = load("manifests/r6d_specificity_preexecution_design_freeze_2026-09-17_v0_1.json")

assert gate["schema"] == "RB-R6D-MATCHED-STOCK-ROBUSTNESS-FORMAL-SUBJECT-GATE-v0.1"
assert gate["status"] == "GATE_CONTRACT_ONLY_NOT_AUTHORIZATION"
assert gate["gate_hash"] == GATE_HASH == digest_without(gate, "gate_hash")

binding = gate["design_freeze"]
assert binding["design_hash"] == DESIGN_HASH == freeze["design_hash"] == plan["design_hash"]
assert binding["predecessor_design_hash"] == PREDECESSOR_HASH == predecessor["design_hash"]
assert binding["candidate_audit_hash"] == AUDIT_HASH == audit["audit_hash"]
assert binding["plan_hash"] == PLAN_HASH == plan["plan_hash"]
assert binding["first_batch_evidence_hash"] == FIRST_BATCH_HASH == plan["source_binding"]["first_batch_evidence_hash"]

expected_conditions = [
    "S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL",
    "S3_MATCHED_ORDINARY_STOCK_B_DOWNGRADE",
    "S4_MATCHED_ORDINARY_STOCK_C_DOWNGRADE",
]
default = gate["default_plan"]
assert default["conditions"] == expected_conditions
assert default["replicates"] == plan["matched_execution_design"]["replicates"] == 3
assert default["planned_branch_count"] == plan["matched_execution_design"]["planned_branch_count"] == 9
assert default["order_policy"] == plan["matched_execution_design"]["order_policy"] == "THREE_CONDITION_CYCLIC_LATIN_ROTATION"
assert default["parent_anchor_ref"] == plan["source_binding"]["parent_anchor_ref"] == "after_turn:8"
assert default["direct_response_turn"] == plan["observation_horizon"]["direct_response_turn"] == 9
assert default["post_consumption_start_turn"] == plan["observation_horizon"]["post_consumption_start_turn"] == 10
assert default["absolute_turn_cap"] == plan["observation_horizon"]["absolute_turn_cap"] == 16
assert default["per_branch_max_calls"] == plan["budget_gate"]["per_branch_max_calls"] == 64
assert default["per_branch_spending_ceiling"] == plan["budget_gate"]["per_branch_spending_ceiling"] == 0.25
assert default["total_spending_ceiling"] == plan["budget_gate"]["global_spending_ceiling"] == 2.25
assert default["automatic_paid_evaluator"] is False

env = gate["environment_binding"]
for key in ("provider", "domain_id", "arena_config_hash", "model_config_hash", "agent_registry_hash", "domain_hash", "task_hash"):
    assert env[key] == plan["environment_binding"][key]

runtime = gate["planned_runtime_binding"]
assert runtime == {
    "runtime_plan_builder_bound": False,
    "runner_bound": False,
    "workflow_bound": False,
    "raw_evidence_freezer_bound": False,
    "runtime_readiness_status": "NOT_BOUND_AT_DESIGN_FREEZE",
}

required_execution_requirements = {
    "EXACT_FROZEN_DESIGN_HASH_MATCH",
    "EXACT_TARGET_AND_ENVELOPE_MATCH",
    "EXACT_CYCLIC_ORDER_MATCH",
    "RAW_EVIDENCE_FREEZE_BEFORE_DERIVATION",
    "RAW_ARTIFACT_UPLOAD_BEFORE_DERIVATION",
    "EXPLICIT_SEPARATE_HUMAN_AUTHORIZATION_AFTER_RUNTIME_READINESS",
}
assert set(gate["execution_requirements"]) == required_execution_requirements

guards = gate["analysis_guards"]
assert guards["first_batch_outcomes_known"] is True
assert guards["eligibility_rule_uses_first_batch_outcome"] is False
assert guards["all_eligible_candidates_included"] is True
assert guards["historical_s2_minus_s1_replaced"] is False
assert guards["fresh_s0_included"] is False
assert guards["escape_derived_specificity_pre_run"] == "NOT_ESTABLISHED"
assert guards["semantic_cpr_status"] == "NOT_ADJUDICATED"

assert gate["authorization_status"] == "NOT_AUTHORIZED"
assert gate["scientific_provider_run"] is False
assert gate["paid_evaluator_run"] is False
assert gate["semantic_cpr_adjudication"] is False

print("PASS: matched-stock formal subject gate binds the frozen design and remains fail-closed")
print("DESIGN_HASH=" + DESIGN_HASH)
print("GATE_HASH=" + GATE_HASH)
