#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arena.r5r6_specificity_atomic_v0_2 import S0, S1, S2
from arena.r5r6_specificity_atomic_preflight_v0_2 import build_preflight


def load(rel: str):
    with (ROOT / rel).open("r", encoding="utf-8") as f:
        return json.load(f)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def main() -> None:
    binding = load("configs/r5r6_specificity_exact_source_binding_v0.2.json")
    mechanism = load("configs/first_paper_mechanism_contract_v0.7.json")
    analysis = load("configs/first_paper_analysis_contract_v0.6.json")
    measurement = load("configs/process_reality_measurement_contract_v0.8.json")
    plan_schema = load("schemas/r5r6_specificity_atomic_plan_v0.2.schema.json")
    preflight_schema = load("schemas/r5r6_specificity_atomic_preflight_v0.2.schema.json")

    canonical = [
        "S0_NATURAL_REFERENCE",
        "S1_MATCHED_OR_ORDINARY_FACTUAL_INFORMATION_DOWNGRADE",
        "S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL",
    ]
    require([S0, S1, S2] == canonical, "runtime_condition_ids_not_canonical")
    require(mechanism["r6_specificity"]["conditions"] == canonical, "mechanism_condition_ids_not_canonical")
    require(analysis["r6"]["subanalyses"]["R6_D_TARGET_SPECIFICITY"]["conditions"] == canonical, "analysis_condition_ids_not_canonical")
    require(list(measurement["r6_d_specificity"]["conditions"].keys()) == canonical, "measurement_condition_ids_not_canonical")
    require(binding["s1"]["condition"] == S1, "binding_s1_condition_mismatch")
    require(binding["s2"]["condition"] == S2, "binding_s2_condition_mismatch")

    require(plan_schema["$id"] == "RB-R5R6-SPECIFICITY-ATOMIC-PLAN-v0.2", "plan_schema_id_invalid")
    require(preflight_schema["$id"] == "RB-R5R6-SPECIFICITY-ATOMIC-PREFLIGHT-v0.2", "preflight_schema_id_invalid")
    require(plan_schema["properties"]["conditions"]["const"] == canonical, "plan_schema_condition_ids_not_canonical")

    bundle = build_preflight()
    plan = bundle["plan"]
    summary = bundle["summary"]
    e1 = bundle["s1_envelope"]
    e2 = bundle["s2_envelope"]

    require(plan["conditions"] == canonical, "preflight_plan_condition_ids_not_canonical")
    require(plan["primary_contrast"] == "S2_MINUS_S1", "preflight_primary_contrast_invalid")
    require(plan["primary_readout"] == "POST_CONSUMPTION_R6_INERTIA_PROFILE", "preflight_primary_readout_invalid")
    require(plan["authorization_status"] == "NOT_AUTHORIZED", "preflight_must_not_be_authorized")
    require(plan["semantic_cpr_status"] == "NOT_ADJUDICATED", "preflight_semantic_status_invalid")
    require(plan["paid_provider_authorized"] is False, "provider_must_not_be_authorized")
    require(plan["paid_evaluator_authorized"] is False, "evaluator_must_not_be_authorized")

    require(e1["condition_id"] == S1, "s1_envelope_condition_mismatch")
    require(e2["condition_id"] == S2, "s2_envelope_condition_mismatch")
    require(e1["mechanical_primitive"] == e2["mechanical_primitive"] == "ONE_SHOT_TARGET_SCOPED_EPISTEMIC_STATUS_ANNOTATION", "mechanical_primitive_mismatch")
    require(e1["to_status"] == e2["to_status"] == "unconfirmed", "to_status_mismatch")
    require(e1["target_locator"] != e2["target_locator"], "s1_s2_target_must_differ")

    require(summary["scientific_status"] == "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE", "summary_scientific_status_invalid")
    require(summary["s1_s2_mechanically_equivalent"] is True, "mechanical_equivalence_failed")
    require(summary["source_runtime_immutable"] is True, "source_runtime_mutation_detected")
    require(summary["original_target_values_preserved"] is True, "target_value_mutation_detected")
    require(summary["s1_direct_exposures"] == summary["s2_direct_exposures"] == 1, "direct_exposure_count_invalid")
    require(summary["s1_reinjections"] == summary["s2_reinjections"] == 0, "reinjection_detected")
    require(summary["paid_provider_called"] is False, "provider_call_detected")
    require(summary["paid_evaluator_called"] is False, "evaluator_call_detected")

    print("R6D_ATOMIC_SYNC_V0_1=PASS")
    print("CONDITIONS=" + ",".join(canonical))
    print("PRIMARY_CONTRAST=S2_MINUS_S1")
    print("PRIMARY_READOUT=POST_CONSUMPTION_R6_INERTIA_PROFILE")
    print("PLAN_HASH=" + plan["plan_hash"])
    print("SUMMARY_HASH=" + summary["summary_hash"])
    print("PAID_PROVIDER_AUTHORIZED=NO")
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
