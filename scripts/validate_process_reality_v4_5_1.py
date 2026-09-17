from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESIGN_HASH = "d8783a9c3e0a264c3119ee72e63db9b61d51f0d633ff6dde66068751c31701de"


def load_json(path: str):
    with (ROOT / path).open("r", encoding="utf-8") as f:
        return json.load(f)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(f"FAIL: {message}")


def require_text(path: str, tokens: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    for token in tokens:
        require(token in text, f"{path} missing {token!r}")


def main() -> None:
    frozen = load_json("manifests/r6d_specificity_preexecution_design_freeze_2026-09-17_v0_1.json")
    require(frozen["design_hash"] == DESIGN_HASH, "frozen R6-D design hash changed")
    require(frozen["freeze_rules"]["target_locators_locked"] is True, "target lock must remain true")
    require(frozen["freeze_rules"]["process_distance_components_locked"] is True, "distance freeze must remain true")
    require(frozen["specificity_binding"]["persistent_state_mutation"] is False, "legacy operator persistence invariant changed")

    gate = load_json("configs/r6/r6d_methodological_interpretation_gate_v0.1.json")
    require(gate["frozen_design"]["design_hash"] == DESIGN_HASH, "method gate design hash mismatch")
    rules = gate["interpretation_rules"]
    require(rules["normal_inheritance_is_not_inertia_by_default"] is True, "inheritance/inertia boundary missing")
    require(rules["mechanical_equivalence_does_not_imply_target_exchangeability"] is True, "target comparability guard missing")
    require(rules["s2_minus_s1_first_level_interpretation"] == "FROZEN_TARGET_RESPONSE_CONTRAST", "specificity first-level label drift")
    require(rules["same_parent_effect_is_conditional_on_historical_prefix"] is True, "conditionality guard missing")
    require(rules["hash_ancestry_alone_proves_semantic_adoption"] is False, "hash/adoption guard missing")
    require(rules["potential_closure_is_automatic_repair_scope"] is False, "closure locality guard missing")
    require(rules["endogenous_agent_state_mutation_allowed"] is True, "endogenous-state observation guard missing")

    analysis = load_json("configs/first_paper_analysis_contract_v0.7.json")
    require(analysis["r6"]["comparison_domains"] == [
        "STRUCTURAL_DISTANCE",
        "INHERITANCE_DISTANCE",
        "EPISTEMIC_AUTHORITY_DISTANCE",
    ], "three-domain analysis vector mismatch")
    require(analysis["specificity"]["primary_interpretation"] == "FROZEN_TARGET_RESPONSE_CONTRAST", "analysis specificity label mismatch")
    require(analysis["operator_semantics"]["endogenous_agent_state_mutation_allowed"] is True, "analysis operator semantics drift")

    measurement = load_json("configs/process_reality_measurement_contract_v0.9.json")
    require(set(measurement["comparison_domains"]) == {
        "STRUCTURAL_DISTANCE", "INHERITANCE_DISTANCE", "EPISTEMIC_AUTHORITY_DISTANCE"
    }, "measurement domains incomplete")
    require(measurement["relation_evidence"]["hash_or_reachability_alone_is_adoption"] is False, "measurement hash/adoption guard missing")

    eng = load_json("configs/r7_process_integrity_engineering_contract_v0.2.json")
    require(eng["identity_semantics"]["hashes_alone_establish_semantic_adoption"] is False, "engineering hash/adoption guard missing")
    require(eng["closure_model"]["repair"] == "REPAIR_CLOSURE", "repair closure missing")
    require(eng["runtime_modes"]["ACTIVE_RECOVERY"]["requires_native_runtime_recovery_adapter"] is True, "native recovery adapter boundary missing")

    relation = load_json("schemas/process_integrity_relation_evidence_v0.1.schema.json")
    relation_types = relation["properties"]["relation_type"]["enum"]
    require("ADOPTED_AS_DECISION_PREMISE" in relation_types, "relation adoption evidence missing")
    require("REPLAY_DEPENDENCY_ONLY" in relation_types, "replay-only relation missing")

    lineage = load_json("schemas/process_integrity_lineage_record_v0.2.schema.json")
    for field in [
        "potentially_affected_closure",
        "evidence_supported_affected_closure",
        "repair_closure",
        "relation_evidence_refs",
    ]:
        require(field in lineage["required"], f"lineage required field missing: {field}")

    event = load_json("schemas/process_integrity_event_v0.2.schema.json")
    require("semantic_use_status" in event["properties"], "event semantic-use status missing")
    require("endogenous_subject_state" in event["properties"], "event endogenous-subject marker missing")

    manifest = load_json("manifests/process_reality_v4_5_1_methodological_closure_2026-09-17.json")
    require(manifest["frozen_r6d_design"]["design_hash"] == DESIGN_HASH, "closure manifest design hash mismatch")
    require(manifest["frozen_r6d_design"]["mutated"] is False, "closure manifest must not mutate frozen design")
    require(manifest["scientific_evidence_created"] is False, "method closure must not claim scientific evidence")

    require_text("docs/R_Plan_v4.5.1.md", [
        "Normal inheritance versus system inertia",
        "FROZEN_TARGET_RESPONSE_CONTRAST",
        "PotentiallyAffectedClosure",
        "conditional process response",
    ])
    require_text("docs/R7_structural_inertia_control_protocol_v0.5.md", [
        "PotentiallyAffectedClosure",
        "EvidenceSupportedAffectedClosure",
        "RepairClosure",
    ])
    require_text("docs/reporting/process_reality_report_standard_v1_3.md", [
        "Frozen Target Response Contrast",
        "Experiment-origin versus endogenous persistence",
    ])

    real_workflow = (ROOT / ".github/workflows/r6d-specificity-subject-real.yml").read_text(encoding="utf-8")
    require("validate_process_reality_v4_5_1.py" in real_workflow, "real subject workflow does not enforce methodological gate")

    print("PASS: Process Reality v4.5.1 methodological closure is synchronized")
    print(f"FROZEN_R6D_DESIGN_HASH={DESIGN_HASH}")
    print("SCIENTIFIC_PROVIDER_RUN_AUTHORIZED=NO")
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
