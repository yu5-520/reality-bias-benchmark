#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise SystemExit("R8_DYNAMIC_CPR_VALIDATION_FAILED: " + message)


def main():
    definition = load_json("configs/cpr_definition_contract_v0.3.json")
    adjudication = load_json("configs/cpr_adjudication_contract_v0.3.json")
    schema = load_json("schemas/r8_dynamic_cpr_event_v0.2.schema.json")

    require(
        definition.get("schema") == "RB-CPR-DEFINITION-CONTRACT-v0.3",
        "definition contract id mismatch",
    )
    require(
        adjudication.get("definition_contract") == definition.get("schema"),
        "adjudication contract not bound to definition v0.3",
    )
    require(
        schema.get("$id") == "RB-R8-DYNAMIC-CPR-EVENT-v0.2",
        "dynamic event schema id mismatch",
    )

    defs = definition.get("definitions") or {}
    require(defs.get("C", {}).get("dimension") == "INFORMATION", "C dimension mismatch")
    require(
        defs.get("P", {}).get("dimension") == "COLLABORATION_EXECUTION",
        "P dimension mismatch",
    )
    require(defs.get("R", {}).get("dimension") == "TIME", "R dimension mismatch")

    r_forms = set(defs.get("R", {}).get("forms") or [])
    require(
        {"LINEAGE_PRESERVING_R", "RETROSPECTIVE_GENERATIVE_R"} <= r_forms,
        "R dual-form definition missing",
    )

    coupling = definition.get("coupling") or {}
    require(coupling.get("edge_requires_evidence") is True, "coupling evidence guard missing")
    require(coupling.get("full_loop_required") is False, "full CPR loop must not be required")
    require(coupling.get("fixed_order_required") is False, "fixed CPR order must not be required")

    guards = definition.get("structural_to_semantic_guards") or {}
    for key in (
        "fact_label_to_c_automatic",
        "extra_agent_call_to_p_automatic",
        "reopen_to_r_automatic",
        "multi_agent_agreement_to_independent_evidence_automatic",
        "system_inertia_to_r_automatic",
    ):
        require(guards.get(key) is False, "semantic guard drift: " + key)

    required_paths = [
        "docs/R_Plan_v5.5.md",
        "theory/theory_contract_v0.16.md",
        "docs/R8_Dynamic_CPR_Permission_Penetration_Protocol_v0.3.md",
        "theory/change_notes/CN-R-062_dynamic_cpr_permission_penetration.md",
        "arena/prepare_r8_dynamic_cpr_audit_material.py",
    ]
    for rel in required_paths:
        require((ROOT / rel).exists(), "missing file: " + rel)

    print("R8_DYNAMIC_CPR_VALIDATION=PASS")
    print("C_DIMENSION=INFORMATION")
    print("P_DIMENSION=COLLABORATION_EXECUTION")
    print("R_DIMENSION=TIME")
    print("R_FORMS=LINEAGE_PRESERVING_R,RETROSPECTIVE_GENERATIVE_R")
    print("FIXED_CPR_ORDER_REQUIRED=NO")
    print("SUBJECT_RERUN_REQUIRED=NO")


if __name__ == "__main__":
    main()
