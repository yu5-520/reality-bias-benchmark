#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "semantic_audit_and_reporting_contract_v0.1.md"
SCHEMA = ROOT / "schemas" / "semantic_audit_record_v0.1.schema.json"
FROZEN_ANALYSIS = ROOT / "schemas" / "first_paper_analysis_contract_v0.1.schema.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> None:
    require(DOC.is_file(), f"missing {DOC.relative_to(ROOT)}")
    require(SCHEMA.is_file(), f"missing {SCHEMA.relative_to(ROOT)}")
    require(FROZEN_ANALYSIS.is_file(), f"missing existing frozen analysis contract: {FROZEN_ANALYSIS.relative_to(ROOT)}")

    doc = DOC.read_text(encoding="utf-8")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    frozen = json.loads(FROZEN_ANALYSIS.read_text(encoding="utf-8"))

    required_doc_fragments = [
        "System computation establishes structural facts",
        "Semantic audit interprets what those structural facts mean",
        "Evidence / Integrity Audit",
        "Structural Audit",
        "Semantic Audit",
        "Claim / Boundary Audit",
        "hash or lineage != semantic adoption",
        "persistent visibility != System Inertia",
        "turn/Agent/message count != semantic propagation strength",
        "event order != causal origin",
        "semantic origin != initial driving event != coupling event != authority materialization != Jump != inertia carrier",
        "failure of perturbation response != failure of Jump localization",
        "R2–R4",
        "R5",
        "R6",
        "R7",
        "semantic claim -> structural evidence -> raw evidence pointer -> boundary/alternative interpretation",
        "Raw subject evidence: immutable",
        "Semantic audits: append-only",
        "CPR remains separately adjudicated",
        "first_paper_analysis_contract_v0.1.schema.json",
    ]
    for fragment in required_doc_fragments:
        require(fragment in doc, f"method contract missing required boundary text: {fragment!r}")

    props = schema.get("properties", {})
    required_schema_props = {
        "audit_id",
        "auditor",
        "scope",
        "evidence_binding",
        "source_proposition",
        "semantic_role",
        "relation_type",
        "structural_facts_used",
        "interpretation",
        "claim_status",
        "causal_design_support",
        "boundary",
    }
    require(required_schema_props.issubset(props), "semantic audit schema missing required properties")
    require(schema.get("additionalProperties") is False, "semantic audit schema must reject undeclared top-level fields")

    claim_values = set(props["claim_status"].get("enum", []))
    require(
        claim_values == {"SUPPORTED", "SUPPORTED_CANDIDATE", "NOT_ESTABLISHED", "CONTRADICTED"},
        "claim status vocabulary drifted",
    )

    relation_values = set(props["relation_type"].get("enum", []))
    for relation in {
        "SUPPORTS",
        "CAUSES",
        "CONSTRAINS",
        "DEPENDS_ON",
        "ENABLES",
        "CONFLICTS_WITH",
        "REFRAMES",
        "DROPS",
        "RECONSTRUCTS",
        "MERE_VISIBILITY",
        "MERE_RELAY",
        "NOT_ESTABLISHED",
    }:
        require(relation in relation_values, f"missing semantic relation: {relation}")

    semantic_roles = set(props["semantic_role"].get("enum", []))
    for role in {
        "OBSERVATION",
        "ADOPTION",
        "COUPLING",
        "AUTHORITY_MATERIALIZATION",
        "AMPLIFICATION",
        "JUMP",
        "PERTURBATION_RESPONSE",
        "INERTIA",
        "RECOVERY",
        "NOT_ESTABLISHED",
    }:
        require(role in semantic_roles, f"missing semantic role: {role}")

    evidence = props["evidence_binding"]
    require(
        set(evidence.get("required", [])) >= {"raw_evidence_ref", "evidence_pointers"},
        "semantic audit must bind raw evidence and exact evidence pointers",
    )

    forbidden_top_level = {"confidence", "confidence_score", "score", "total_scalar", "overall_score"}
    require(not (forbidden_top_level & set(props)), "post-hoc numeric confidence/scalar field introduced")

    causal_guard = json.dumps(schema.get("allOf", []), ensure_ascii=False)
    require('"CAUSES"' in causal_guard, "schema lacks causal-claim boundary")
    require('"causal_design_support"' in causal_guard, "causal claim is not conditioned on causal design support")
    require('"SUPPORTED_CANDIDATE"' in causal_guard, "unsupported causal claims are not forced to candidate/boundary status")

    # Existing preregistered/frozen analysis contract remains present and structurally recognizable.
    require(
        frozen.get("properties", {}).get("schema", {}).get("const") == "RB-FIRST-PAPER-ANALYSIS-CONTRACT-v0.1",
        "existing first-paper analysis contract identity changed unexpectedly",
    )
    require(
        "primary_confirmatory_structural" in frozen.get("properties", {}).get("outcomes", {}).get("properties", {}),
        "existing frozen structural estimand contract no longer recognizable",
    )

    print("PASS: semantic audit responsibility boundaries are explicit")
    print("PASS: blind semantic records require evidence binding")
    print("PASS: structural metrics cannot silently adjudicate semantics")
    print("PASS: causal claims are bounded when causal design support is absent")
    print("PASS: semantic-first reporting order is frozen in the method contract")
    print("PASS: existing first-paper frozen structural analysis contract remains separate")
    print("PASS: raw evidence immutability / append-only semantic audit rules are present")


if __name__ == "__main__":
    main()
