#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arena.core import stable_hash
from arena.r5r6_specificity_atomic_v0_2 import S0, S1, S2


def load(rel: str):
    with (ROOT / rel).open("r", encoding="utf-8") as f:
        return json.load(f)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def without(row, key):
    return {k: v for k, v in row.items() if k != key}


def main() -> None:
    domain = load("arena/domains/ecommerce.json")
    contract = load("configs/r5r6_specificity_field_selection_contract_v0.2.json")
    binding = load("configs/r5r6_specificity_exact_source_binding_v0.2.json")
    selection = load("manifests/r5r6_specificity_s1_selection_2026-09-17_v0_2.json")
    source_slice = load("manifests/r5r6_specificity_source_slice_2026-09-17_v0_2.json")
    atomic_plan_schema = load("schemas/r5r6_specificity_atomic_plan_v0.2.schema.json")
    atomic_preflight_schema = load("schemas/r5r6_specificity_atomic_preflight_v0.2.schema.json")

    require(contract["schema"] == "RB-R5R6-SPECIFICITY-FIELD-SELECTION-CONTRACT-v0.2", "selection_contract_schema_invalid")
    require(binding["schema"] == "RB-R5R6-SPECIFICITY-EXACT-SOURCE-BINDING-v0.2", "exact_source_binding_schema_invalid")
    require(selection["schema"] == "RB-R5R6-SPECIFICITY-S1-SELECTION-RECORD-v0.2", "selection_record_schema_invalid")
    require(source_slice["schema"] == "RB-R5R6-SPECIFICITY-SOURCE-SLICE-v0.2", "source_slice_schema_invalid")
    require(atomic_plan_schema["$id"] == "RB-R5R6-SPECIFICITY-ATOMIC-PLAN-v0.2", "atomic_plan_schema_invalid")
    require(atomic_preflight_schema["$id"] == "RB-R5R6-SPECIFICITY-ATOMIC-PREFLIGHT-v0.2", "atomic_preflight_schema_invalid")

    require([S0, S1, S2] == [
        "S0_NATURAL_REFERENCE",
        "S1_MATCHED_OR_ORDINARY_FACTUAL_INFORMATION_DOWNGRADE",
        "S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL",
    ], "canonical_r6d_condition_ids_invalid")

    statuses = source_slice["parent_shared_state_metadata_statuses"]
    facts = sorted(k for k, v in statuses.items() if v == "fact")
    require(facts == ["inventory_stockout_assessment_v1"], "exact_parent_fact_audit_invalid")
    require(contract["exact_source_constraint"]["alternative_top_level_non_j0_shared_state_fact_exists"] is False, "v0_1_control_availability_must_be_false")

    pool = selection["eligible_pool"]
    require(pool["candidate_count"] == len(pool["candidates"]) == 9, "selection_pool_size_invalid")
    require(pool["pool_hash"] == stable_hash(without(pool, "pool_hash")), "selection_pool_hash_mismatch")
    locators = [x["locator"] for x in pool["candidates"]]
    require(locators == sorted(locators), "selection_pool_must_be_lexicographically_sorted")
    require(all(".stock" not in x and ".daily_units" not in x for x in locators), "inventory_family_leaked_into_first_s1_pool")

    parent_hash = selection["source_binding"]["common_parent_state_hash"]
    contract_schema = selection["selection_contract"]
    seed = hashlib.sha256(f"{parent_hash}|{contract_schema}".encode()).hexdigest()
    rule = selection["selection_rule"]
    require(rule["seed_hash"] == seed, "selection_seed_hash_mismatch")
    require(rule["selected_index_zero_based"] == int(seed, 16) % len(locators), "selection_index_mismatch")
    require(rule["selection_rule_hash"] == stable_hash(without(rule, "selection_rule_hash")), "selection_rule_hash_mismatch")

    selected = selection["selected_s1_target"]
    require(selected["locator"] == pool["candidates"][rule["selected_index_zero_based"]]["locator"], "selected_target_not_from_deterministic_index")
    require(selected["selected_target_hash"] == stable_hash(without(selected, "selected_target_hash")), "selected_target_hash_mismatch")
    require(selection["selector_outcome_blind_attestation"] is True, "selection_must_be_outcome_blind")
    require(selection["scientific_s_arm_outputs_available_at_selection_time"] is False, "scientific_s_outputs_must_not_exist_at_selection")
    require(selection["selection_record_hash"] == stable_hash(without(selection, "selection_record_hash")), "selection_record_hash_mismatch")

    s1 = binding["s1"]
    s2 = binding["s2"]
    require(s1["condition"] == S1, "s1_condition_id_mismatch")
    require(s2["condition"] == S2, "s2_condition_id_mismatch")
    require(s1["target_locator"] == selected["locator"], "s1_binding_locator_mismatch")
    require(s1["original_value"] == selected["value"], "s1_binding_value_mismatch")
    require(domain["task"]["public_context"]["products"]["C"]["gross_margin_pct"] == 35, "domain_s1_value_mismatch")
    require(s2["target_locator"] == source_slice["j0_source"]["atomic_target_locator"], "s2_binding_locator_mismatch")
    require(s2["original_value"] == source_slice["j0_source"]["atomic_target_value"] == 1520, "s2_binding_value_mismatch")
    require(s2["source_origin_status"] == "preliminary_unreconciled", "s2_source_origin_must_be_preliminary")
    require(s2["acquired_status_at_intervention"] == "fact", "s2_acquired_authority_must_be_fact")
    require(binding["j0"]["container_acquired_status"] == "fact", "j0_container_fact_status_missing")

    op = binding["common_operator"]
    require(op["from_status"] == "fact" and op["to_status"] == "unconfirmed", "atomic_status_transform_invalid")
    require(op["direct_exposure_limit"] == 1, "atomic_exposure_limit_invalid")
    require(op["persistent_state_mutation"] is False, "atomic_persistent_mutation_forbidden")
    require(op["experiment_origin_reinjection_count"] == 0, "atomic_reinjection_forbidden")
    require(op["original_target_value_mutation"] is False, "atomic_target_value_mutation_forbidden")
    require(op["opposite_fact_supplied"] is False, "atomic_opposite_fact_forbidden")
    require(op["replacement_conclusion_supplied"] is False, "atomic_replacement_conclusion_forbidden")
    require(op["desired_terminal_answer_supplied"] is False, "atomic_terminal_target_forbidden")

    hist = binding["historical_boundary"]
    require(hist["prospective_s2_is_exact_historical_operator_replay"] is False, "prospective_atomic_s2_must_not_be_misreported_as_exact_historical_replay")
    require(hist["historical_ab_evidence_remains_unchanged"] is True, "historical_ab_must_remain_unchanged")

    for auth in (contract["authorization"], binding["authorization"], selection["authorization"]):
        require(auth.get("paid_provider_run", auth.get("scientific_subject_provider_call", False)) is False, "paid_provider_must_not_be_authorized")
        require(auth.get("paid_evaluator_run", auth.get("paid_evaluator_call", False)) is False, "paid_evaluator_must_not_be_authorized")
        require(auth.get("semantic_cpr_adjudication") is False, "semantic_cpr_must_not_be_authorized")

    required_files = [
        "docs/R5_R6_specificity_source_audit_2026-09-17.md",
        "docs/R5_R6_specificity_protocol_v0.3.md",
        "arena/r5r6_specificity_atomic_v0_2.py",
        "arena/r5r6_specificity_atomic_preflight_v0_2.py",
        "schemas/r5r6_specificity_atomic_plan_v0.2.schema.json",
        "schemas/r5r6_specificity_atomic_preflight_v0.2.schema.json",
    ]
    for rel in required_files:
        require((ROOT / rel).is_file(), f"required_file_missing:{rel}")

    print("R5R6_SPECIFICITY_SOURCE_AUDIT_V0_2=PASS")
    print("R6_D_NAMESPACE=S")
    print("EXACT_PARENT_SECOND_TOP_LEVEL_FACT=NO")
    print("S1_CONDITION=" + S1)
    print("S1_TARGET=" + selected["locator"])
    print("S2_CONDITION=" + S2)
    print("S2_TARGET=" + s2["target_locator"])
    print("S2_SOURCE_ORIGIN_STATUS=preliminary_unreconciled")
    print("S2_ACQUIRED_STATUS_AT_J0=fact")
    print("PAID_PROVIDER_AUTHORIZED=NO")
    print("SEMANTIC_CPR_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
