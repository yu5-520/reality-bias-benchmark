#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arena.core import stable_hash
from arena.io_utils import sha256_file
from arena.r5r6_specificity_atomic_preflight_v0_2 import build_preflight
from arena.r5r6_specificity_atomic_v0_2 import S0, S1, S2

DESIGN_PATH = "manifests/r6d_specificity_preexecution_design_freeze_2026-09-17_v0_1.json"
GATE_PATH = "configs/r6/r6d_specificity_formal_subject_gate_v0.1.json"
SELECTION_PATH = "manifests/r5r6_specificity_s1_selection_2026-09-17_v0_2.json"
BINDING_PATH = "configs/r5r6_specificity_exact_source_binding_v0.2.json"
SOURCE_SLICE_PATH = "manifests/r5r6_specificity_source_slice_2026-09-17_v0_2.json"


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def hash_without(row: dict, key: str) -> str:
    material = copy.deepcopy(row)
    material.pop(key, None)
    return stable_hash(material)


def main() -> None:
    design = load(DESIGN_PATH)
    gate = load(GATE_PATH)
    selection = load(SELECTION_PATH)
    binding = load(BINDING_PATH)
    source_slice = load(SOURCE_SLICE_PATH)

    canonical = [
        "S0_NATURAL_REFERENCE",
        "S1_MATCHED_OR_ORDINARY_FACTUAL_INFORMATION_DOWNGRADE",
        "S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL",
    ]
    require([S0, S1, S2] == canonical, "runtime_condition_namespace_not_canonical")

    require(design["schema"] == "RB-R6D-SPECIFICITY-PREEXECUTION-DESIGN-FREEZE-v0.1", "design_schema_invalid")
    require(design["status"] == "FROZEN_PREEXECUTION_DESIGN_NOT_AUTHORIZED", "design_status_invalid")
    require(design["design_hash"] == hash_without(design, "design_hash"), "design_hash_mismatch")
    require(design["design_hash"] == "d8783a9c3e0a264c3119ee72e63db9b61d51f0d633ff6dde66068751c31701de", "unexpected_design_hash")

    source = design["source_binding"]
    require(source["source_workflow_run_id"] == 35132777581, "source_run_invalid")
    require(source["source_evidence_batch_hash"] == "244d10dfd7655eef7ac99db4731e85daab62fe9a2546b89e7d27720fbb8c20f7", "source_evidence_hash_invalid")
    require(source["source_raw_traces_sha256"] == "102089199c7e1292e80444e339b84b00d2124e298f9ab849844dda0116473ef7", "source_trace_hash_invalid")
    require(source["source_r5_plan_hash"] == "a24c98901422bbccfc9a040a6bc14575b1c710edd518c0d9c2facf7a57926351", "source_plan_hash_invalid")
    require(source["common_parent_state_hash"] == "aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c", "parent_hash_invalid")
    require(source["source_measurement_hash"] == "5ec7953b473e4d7b29612de18aac9992238e722e1b12ea7c6999929958b24191", "source_measurement_hash_invalid")
    require(source["parent_anchor_ref"] == "after_turn:8" and source["parent_turn"] == 8, "parent_anchor_invalid")
    require(source["resumed_actor"] == "ops_lead" and source["resumed_turn"] == 9, "resumed_boundary_invalid")
    require(source["j0_event_ref"] == "E32", "j0_event_invalid")

    require(source_slice["source_binding"]["common_parent_state_hash"] == source["common_parent_state_hash"], "source_slice_parent_mismatch")
    require(source_slice["j0_source"]["event_ref"] == source["j0_event_ref"], "source_slice_j0_mismatch")

    spec = design["specificity_binding"]
    require(spec["conditions"] == canonical, "design_conditions_invalid")
    require(spec["selection_record_hash"] == selection["selection_record_hash"], "selection_record_hash_mismatch")
    require(spec["s1_target_locator"] == selection["selected_s1_target"]["locator"] == binding["s1"]["target_locator"], "s1_target_mismatch")
    require(spec["s1_original_value"] == selection["selected_s1_target"]["value"] == binding["s1"]["original_value"] == 35, "s1_value_mismatch")
    require(spec["s2_target_locator"] == binding["s2"]["target_locator"] == source_slice["j0_source"]["atomic_target_locator"], "s2_target_mismatch")
    require(spec["s2_original_value"] == binding["s2"]["original_value"] == source_slice["j0_source"]["atomic_target_value"] == 1520, "s2_value_mismatch")
    require(spec["s2_source_origin_status"] == binding["s2"]["source_origin_status"] == "preliminary_unreconciled", "s2_source_status_mismatch")
    require(spec["s2_acquired_status_at_j0"] == binding["s2"]["acquired_status_at_intervention"] == "fact", "s2_acquired_status_mismatch")
    require(spec["common_operator"] == "ONE_SHOT_TARGET_SCOPED_EPISTEMIC_STATUS_ANNOTATION", "operator_invalid")
    require(spec["direct_exposure_limit"] == 1, "direct_exposure_limit_invalid")
    require(spec["experiment_origin_reinjection_count"] == 0, "reinjection_not_zero")
    require(spec["persistent_state_mutation"] is False, "persistent_mutation_forbidden")
    require(spec["original_target_value_mutation"] is False, "target_value_mutation_forbidden")
    require(spec["historical_r5_operator_replayed_exactly"] is False, "historical_operator_replay_claim_forbidden")

    preflight = build_preflight()
    p = preflight["plan"]
    s = preflight["summary"]
    e1 = preflight["s1_envelope"]
    e2 = preflight["s2_envelope"]
    offline = design["offline_preflight_binding"]
    require(p["plan_hash"] == offline["atomic_preflight_plan_hash"] == "9850917c8af15a2cbf4209c324b8204e9f43e8923d95b41492b726127c0f9df6", "atomic_preflight_plan_hash_mismatch")
    require(s["summary_hash"] == offline["atomic_preflight_summary_hash"] == "b214f8c38e6857437f11fdb2217d30537b29dfefb043a0de49bf5ca151f6c296", "atomic_preflight_summary_hash_mismatch")
    require(e1["envelope_hash"] == spec["s1_envelope_hash"], "s1_envelope_hash_mismatch")
    require(e2["envelope_hash"] == spec["s2_envelope_hash"], "s2_envelope_hash_mismatch")
    require(s["s1_s2_mechanically_equivalent"] is True, "mechanical_equivalence_failed")
    require(s["s1_direct_exposures"] == s["s2_direct_exposures"] == 1, "offline_exposure_integrity_failed")
    require(s["s1_reinjections"] == s["s2_reinjections"] == 0, "offline_reinjection_integrity_failed")
    require(s["source_runtime_immutable"] is True and s["original_target_values_preserved"] is True, "offline_source_mutation_detected")

    env = design["environment_binding"]
    require(env["provider"] == "deepseek", "provider_invalid")
    require(sha256_file(ROOT / env["model_config_path"]) == env["model_config_hash"], "model_config_hash_mismatch")
    require(sha256_file(ROOT / env["arena_config_path"]) == env["arena_config_hash"], "arena_config_hash_mismatch")
    domain_path = ROOT / "arena/domains/ecommerce.json"
    require(sha256_file(domain_path) == env["domain_hash"], "domain_hash_mismatch")
    domain = load("arena/domains/ecommerce.json")
    require(stable_hash(domain["task"]) == env["task_hash"], "task_hash_mismatch")
    require(stable_hash(domain["agents"]) == env["agent_registry_hash"], "agent_registry_hash_mismatch")
    require(env["provider_internal_state_replayed"] is False, "provider_hidden_state_replay_forbidden")

    matched = design["matched_execution_design"]
    require(matched["replicates"] == 3 and matched["planned_branch_count"] == 9, "three_triad_design_required")
    require(matched["order_policy"] == "THREE_CONDITION_CYCLIC_LATIN_ROTATION", "order_policy_invalid")
    rows = matched["rows"]
    require(len(rows) == 9, "branch_row_count_invalid")
    expected_orders = {
        1: [S0, S1, S2],
        2: [S1, S2, S0],
        3: [S2, S0, S1],
    }
    for row in rows:
        require(row["row_hash"] == hash_without(row, "row_hash"), "row_hash_mismatch:" + row["run_id"])
        require(row["logical_seed"] == row["replicate_index"], "logical_seed_mismatch:" + row["run_id"])
    for rep, expected in expected_orders.items():
        actual = [x["condition_id"] for x in sorted((r for r in rows if r["replicate_index"] == rep), key=lambda x: x["execution_order"])]
        require(actual == expected, f"cyclic_order_invalid:{rep}:{actual}")
    for position in (1, 2, 3):
        at_position = [r["condition_id"] for r in rows if r["execution_order"] == position]
        require(sorted(at_position) == sorted(canonical), f"position_balance_invalid:{position}")
    require(matched["same_parent_repeats_are_independent_samples"] is False, "independence_overclaim_forbidden")

    horizon = design["observation_horizon"]
    require(horizon["branch_start_parent_turn"] == 8, "horizon_parent_turn_invalid")
    require(horizon["direct_response_turn"] == 9, "direct_response_turn_invalid")
    require(horizon["post_consumption_start_turn"] == 10, "post_consumption_origin_invalid")
    require(horizon["max_additional_agent_turns"] == 8, "additional_turn_cap_invalid")
    require(horizon["absolute_turn_cap"] == 16, "absolute_turn_cap_invalid")
    require(horizon["natural_early_termination_allowed"] is True, "natural_termination_must_remain_allowed")
    require(horizon["natural_early_termination_interpretation"] == "RIGHT_CENSORING", "censoring_interpretation_invalid")
    require(horizon["no_later_event_equals_permanent_extinction"] is False, "extinction_overclaim_guard_missing")

    analysis = design["analysis_freeze"]
    require(analysis["primary_readout"] == "POST_CONSUMPTION_R6_INERTIA_PROFILE", "primary_readout_invalid")
    require(analysis["primary_contrast"] == "S2_MINUS_S1", "primary_contrast_invalid")
    require(analysis["auxiliary_contrasts"] == ["S1_MINUS_S0", "S2_MINUS_S0"], "auxiliary_contrasts_invalid")
    require(analysis["process_distance_form"] == "MULTIDIMENSIONAL_VECTOR", "distance_form_invalid")
    expected_distance = [
        "EVENT_SET_DISTANCE",
        "EDGE_SET_DISTANCE",
        "ACTOR_SET_OR_SEQUENCE_DISTANCE",
        "ROOT_REACH_DISTANCE",
        "DEPTH_DISTANCE",
        "BRANCH_MERGE_REENTRY_DISTANCE",
        "CROSS_AGENT_DISTANCE",
        "PATH_FAMILY_DISTANCE",
        "STATE_LINEAGE_DESTINATION_DISTANCE",
        "RECONVERGENCE_DISTANCE",
        "CARRIER_SURVIVAL_DISTANCE",
    ]
    require(analysis["process_distance_components"] == expected_distance, "process_distance_vector_invalid")
    require(analysis["after_outcome_scalar_invention_forbidden"] is True, "posthoc_scalar_guard_missing")
    require(analysis["reachability_implies_semantic_adoption"] is False, "carrier_semantic_guard_missing")
    require(analysis["semantic_cpr_status"] == "NOT_ADJUDICATED", "semantic_status_invalid")

    budget = design["budget_gate"]
    require(budget["per_branch_spending_ceiling"] == 0.25, "per_branch_ceiling_invalid")
    require(budget["global_spending_ceiling"] == 2.25, "global_ceiling_invalid")
    require(budget["per_branch_max_calls"] == 64, "call_cap_invalid")
    require(abs(budget["per_branch_spending_ceiling"] * matched["planned_branch_count"] - budget["global_spending_ceiling"]) < 1e-12, "budget_math_invalid")
    require(budget["automatic_paid_evaluator"] is False, "automatic_paid_evaluator_forbidden")

    freeze = design["freeze_rules"]
    for key in (
        "s1_selection_locked",
        "target_locators_locked",
        "condition_ids_locked",
        "order_policy_locked",
        "observation_horizon_locked",
        "process_distance_components_locked",
        "raw_evidence_freeze_before_derivation_required",
        "raw_artifact_upload_before_derivation_required",
        "semantic_adjudication_deferred",
        "historical_r5mid_mutation_forbidden",
    ):
        require(freeze[key] is True, "freeze_rule_missing:" + key)

    ready = design["runtime_readiness"]
    require(ready["atomic_operator_ready_offline"] is True, "atomic_operator_not_ready")
    require(ready["exact_source_binding_ready"] is True, "source_binding_not_ready")
    require(ready["cross_contract_validation_passed"] is True, "cross_contract_validation_not_ready")
    require(ready["real_subject_runner_bound"] is False, "runner_must_not_be_bound_at_design_freeze")
    require(ready["real_subject_workflow_bound"] is False, "workflow_must_not_be_bound_at_design_freeze")
    require(ready["scientific_run_authorized"] is False, "scientific_run_must_not_be_authorized")

    require(gate["schema"] == "RB-R6D-SPECIFICITY-FORMAL-SUBJECT-GATE-v0.1", "gate_schema_invalid")
    require(gate["status"] == "GATE_CONTRACT_ONLY_NOT_AUTHORIZATION", "gate_status_invalid")
    require(gate["design_freeze"]["design_hash"] == design["design_hash"], "gate_design_hash_mismatch")
    require(gate["default_plan"]["planned_branch_count"] == matched["planned_branch_count"], "gate_branch_count_mismatch")
    require(gate["default_plan"]["replicates"] == matched["replicates"], "gate_replicate_count_mismatch")
    require(gate["default_plan"]["total_spending_ceiling"] == budget["global_spending_ceiling"], "gate_budget_mismatch")
    require(gate["planned_runtime_binding"]["runner_bound"] is False and gate["planned_runtime_binding"]["workflow_bound"] is False, "runtime_must_remain_unbound")
    require(gate["authorization_status"] == "NOT_AUTHORIZED", "gate_must_not_authorize")
    require(gate["scientific_provider_run_authorized"] is False, "provider_gate_must_be_false")
    require(gate["paid_evaluator_run_authorized"] is False, "evaluator_gate_must_be_false")
    require(gate["semantic_cpr_adjudication_authorized"] is False, "semantic_gate_must_be_false")

    auth = design["authorization"]
    require(auth["authorization_status"] == "NOT_AUTHORIZED", "design_authorization_invalid")
    require(auth["scientific_provider_run"] is False, "provider_run_authorized_unexpectedly")
    require(auth["paid_evaluator_run"] is False, "evaluator_run_authorized_unexpectedly")
    require(auth["semantic_cpr_adjudication"] is False, "semantic_adjudication_authorized_unexpectedly")

    print("R6D_SPECIFICITY_EXACT_PLAN_V0_1=PASS")
    print("DESIGN_HASH=" + design["design_hash"])
    print("TRIADS=3")
    print("PLANNED_BRANCHES=9")
    print("ORDER_POLICY=THREE_CONDITION_CYCLIC_LATIN_ROTATION")
    print("PRIMARY_CONTRAST=S2_MINUS_S1")
    print("POST_CONSUMPTION_START=T10")
    print("ABSOLUTE_TURN_CAP=T16")
    print("GLOBAL_SPENDING_CEILING_USD=2.25")
    print("REAL_RUNNER_BOUND=NO")
    print("SCIENTIFIC_PROVIDER_AUTHORIZED=NO")
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
