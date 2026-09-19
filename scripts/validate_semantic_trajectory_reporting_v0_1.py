#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SEMANTIC_SCHEMA = "RB-SEMANTIC-TRAJECTORY-AUDIT-v0.1"
REPORT_BUNDLE_SCHEMA = "RB-PROCESS-REALITY-REPORT-EVIDENCE-BUNDLE-v0.1"
REPORT_STANDARD = "RB-PROCESS-REALITY-REPORT-STANDARD-v1.8"
HELD_OUT_DOMAINS = {"finance", "supply_chain", "software_engineering"}

SUBSTANTIVE_PROPAGATION = {
    "SEMANTIC_TRANSFORMATION",
    "TRANSFORMED_DESCENDANT",
    "DESCENDANT_INHERITANCE",
    "INDEPENDENT_REANCHOR",
    "PREEXISTING_GATE_REAFFIRMATION",
    "BOUNDARY_PRESERVATION",
    "AUTHORITY_MIGRATION",
    "DECISION_APPLICATION",
}


def fail(message: str) -> None:
    raise ValueError(message)


def require(ok: bool, message: str) -> None:
    if not ok:
        fail(message)


def load(rel_or_abs: str) -> dict[str, Any]:
    p = Path(rel_or_abs)
    if not p.is_absolute():
        p = ROOT / p
    return json.loads(p.read_text(encoding="utf-8"))


def validate_contracts() -> None:
    semantic_rules = load("configs/v5_4_semantic_trajectory_audit_rules_v0.1.json")
    report_rules = load("configs/process_reality_report_write_rules_v1_8.json")
    semantic_schema = load("schemas/semantic_trajectory_audit_v0.1.schema.json")
    report_schema = load("schemas/process_reality_report_evidence_bundle_v0.1.schema.json")

    require(
        semantic_rules["schema"] == "RB-V5.4-SEMANTIC-TRAJECTORY-AUDIT-RULES-v0.1",
        "semantic_rules_schema_invalid",
    )
    require(
        set(semantic_rules["primary_experiment_scope"]["held_out_domains"]) == HELD_OUT_DOMAINS,
        "held_out_domain_set_invalid",
    )
    require(
        semantic_rules["primary_experiment_scope"]["forbidden_primary_domains"] == ["ecommerce"],
        "ecommerce_must_be_forbidden_primary_domain",
    )
    require(
        semantic_rules["audit_unit"]["full_actual_agent_route_required"] is True,
        "complete_route_rule_missing",
    )
    require(
        semantic_rules["audit_unit"]["semantic_lineage_is_overlay_on_full_route"] is True,
        "semantic_overlay_rule_missing",
    )
    require(
        semantic_rules["result_derivation"]["substantive_uniform_decision_forbidden"] is True,
        "uniform_substantive_decision_must_be_forbidden",
    )
    forbidden = set(semantic_rules["result_derivation"]["forbidden_uniform_result_fields"])
    require(
        {"semantic_adoption", "decision_action_dependence", "post_stimulus_persistence", "system_inertia_status"} <= forbidden,
        "uniform_result_forbidden_set_incomplete",
    )

    require(
        report_rules["schema"] == "RB-PROCESS-REALITY-REPORT-WRITE-RULES-v1.8",
        "report_rules_schema_invalid",
    )
    require(
        report_rules["central_visual"]["type"]
        == "TIME_ALIGNED_ACTUAL_AGENT_ROUTE_WITH_SEMANTIC_LINEAGE_OVERLAY",
        "central_visual_must_be_actual_route_semantic_overlay",
    )
    require(
        report_rules["primary_content_rule"].startswith("SEMANTIC_AUDIT_IS_PRIMARY"),
        "semantic_audit_must_be_primary_report_content",
    )
    require(
        report_rules["cross_domain_r2_r4_rule"]["ecommerce_primary_example_forbidden"] is True,
        "ecommerce_primary_example_guard_missing",
    )
    require(
        report_rules["r6_rule"]["if_claiming_persistence_not_equal_system_inertia"]["complete_positive_inertia_candidate_required"] is True
        and report_rules["r6_rule"]["if_claiming_persistence_not_equal_system_inertia"]["complete_negative_or_reanchored_comparator_required"] is True,
        "r6_positive_negative_complete_route_contrast_missing",
    )

    require(semantic_schema["$id"] == SEMANTIC_SCHEMA, "semantic_schema_id_invalid")
    sem_props = semantic_schema["properties"]
    for key in ("actual_agent_route", "semantic_nodes", "semantic_edges", "case_judgement"):
        require(key in sem_props, "semantic_schema_missing:" + key)

    edge_enum = set(
        sem_props["semantic_edges"]["items"]["properties"]["propagation_type"]["enum"]
    )
    for expected in (
        "DIRECT_RELAY",
        "SEMANTIC_TRANSFORMATION",
        "TRANSFORMED_DESCENDANT",
        "DESCENDANT_INHERITANCE",
        "INDEPENDENT_REANCHOR",
        "PREEXISTING_GATE_REAFFIRMATION",
        "BOUNDARY_PRESERVATION",
    ):
        require(expected in edge_enum, "semantic_propagation_vocab_missing:" + expected)

    require(report_schema["$id"] == REPORT_BUNDLE_SCHEMA, "report_bundle_schema_id_invalid")
    domain_enum = set(
        report_schema["properties"]["domain_scope"]["properties"]["primary_experiment_domains"]["items"]["enum"]
    )
    require(domain_enum == HELD_OUT_DOMAINS, "report_primary_domain_enum_invalid")


def validate_semantic_audit(row: dict[str, Any]) -> None:
    require(row.get("schema") == SEMANTIC_SCHEMA, "semantic_audit_schema_invalid")

    scope = row["experiment_scope"]
    if scope["domain_id"] == "ecommerce":
        require(
            scope["evidence_role"] == "HISTORICAL_METHOD_DEVELOPMENT_CONTEXT",
            "ecommerce_may_not_be_primary_first_round_evidence",
        )

    route = row["actual_agent_route"]
    require(route.get("complete_route_verified") is True, "complete_route_not_verified")
    nodes = route.get("nodes") or []
    require(nodes, "actual_agent_route_empty")
    require(route["route_node_count"] == len(nodes), "route_node_count_mismatch")
    require(
        route["executed_agent_turn_count"] == len(nodes),
        "executed_agent_turn_count_mismatch",
    )

    indices = [int(n["route_index"]) for n in nodes]
    require(len(indices) == len(set(indices)), "duplicate_route_index")
    require(sorted(indices) == list(range(len(nodes))), "route_indices_not_contiguous")
    for n in nodes:
        require(n.get("call_ref"), "route_node_missing_call_ref")
        require(n.get("event_refs"), "route_node_missing_event_refs")

    semantic_nodes = row.get("semantic_nodes") or []
    sem_indices = [int(n["route_index"]) for n in semantic_nodes]
    require(len(sem_indices) == len(set(sem_indices)), "duplicate_semantic_node")
    require(set(sem_indices) == set(indices), "semantic_nodes_must_cover_every_actual_route_node")

    for n in semantic_nodes:
        require(str(n.get("semantic_delta", "")).strip(), "semantic_node_missing_semantic_delta")
        require(n.get("evidence_refs"), "semantic_node_missing_evidence_refs")
        if n.get("independent_evidence_introduced") is True:
            require(n.get("independent_evidence_refs"), "independent_evidence_refs_required")

    edges = row.get("semantic_edges") or []
    require(edges, "semantic_edges_empty")
    edge_ids = set()
    for e in edges:
        require(e["edge_id"] not in edge_ids, "duplicate_semantic_edge_id")
        edge_ids.add(e["edge_id"])
        require(int(e["from_route_index"]) in indices, "semantic_edge_from_unknown_route_node")
        require(int(e["to_route_index"]) in indices, "semantic_edge_to_unknown_route_node")
        require(str(e.get("semantic_before", "")).strip(), "semantic_edge_missing_semantic_before")
        require(str(e.get("semantic_after", "")).strip(), "semantic_edge_missing_semantic_after")
        require(str(e.get("semantic_delta", "")).strip(), "semantic_edge_missing_semantic_delta")
        require(e.get("evidence_refs"), "semantic_edge_missing_evidence_refs")
        if e["propagation_type"] == "INDEPENDENT_REANCHOR":
            require(e.get("independent_evidence_refs"), "reanchoring_requires_independent_evidence_refs")

    judgement = row["case_judgement"]
    derivation = judgement.get("derivation_edge_ids") or []
    require(derivation, "case_judgement_requires_derivation_edges")
    require(set(derivation) <= edge_ids, "case_judgement_references_unknown_edge")

    if judgement["semantic_adoption"] == "SUPPORTED":
        require(
            any(e["propagation_type"] in SUBSTANTIVE_PROPAGATION for e in edges),
            "semantic_adoption_supported_without_substantive_edge",
        )

    if judgement["system_inertia_status"] == "CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE":
        require(judgement.get("challenged_source_or_target_ref"), "inertia_candidate_missing_challenged_target")
        require(judgement.get("direct_stimulus_end_ref"), "inertia_candidate_missing_stimulus_end")
        post = judgement.get("post_stimulus_persistence_node_refs") or []
        require(post, "inertia_candidate_missing_post_stimulus_nodes")
        require(set(map(int, post)) <= set(indices), "inertia_candidate_post_nodes_unknown")
        require(
            any(e["propagation_type"] in {"TRANSFORMED_DESCENDANT", "DESCENDANT_INHERITANCE", "AUTHORITY_MIGRATION"} for e in edges),
            "inertia_candidate_missing_descendant_lineage_edge",
        )


def validate_report_bundle(bundle: dict[str, Any], profile: str | None = None) -> None:
    require(bundle.get("schema") == REPORT_BUNDLE_SCHEMA, "report_bundle_schema_invalid")
    require(bundle.get("reporting_standard") == REPORT_STANDARD, "report_standard_binding_invalid")

    primary_domains = set(bundle["domain_scope"]["primary_experiment_domains"])
    require(primary_domains <= HELD_OUT_DOMAINS, "report_primary_domain_outside_held_out_set")
    require("ecommerce" not in primary_domains, "ecommerce_in_primary_report_domain")

    cases = bundle.get("trajectory_cases") or []
    require(cases, "report_bundle_has_no_trajectory_cases")
    case_ids = {c["case_id"] for c in cases}
    for c in cases:
        require(c.get("complete_actual_route") is True, "major_report_case_missing_complete_route")
        require(c.get("semantic_lineage_overlay_present") is True, "major_report_case_missing_semantic_overlay")
        if c["domain_id"] == "ecommerce":
            require(
                c["evidence_role"] == "HISTORICAL_METHOD_DEVELOPMENT_CONTEXT",
                "ecommerce_case_has_illegal_primary_role",
            )

    figures = bundle.get("figure_specs") or []
    require(
        any(
            f.get("figure_type") == "TIME_ALIGNED_ACTUAL_AGENT_ROUTE_WITH_SEMANTIC_LINEAGE_OVERLAY"
            and f.get("all_actual_nodes_required") is True
            and f.get("semantic_overlay_required") is True
            for f in figures
        ),
        "report_missing_primary_actual_route_semantic_overlay_figure",
    )

    require(bundle["semantic_summary"]["role"] == "PRIMARY_INTERPRETIVE_CONTENT", "semantic_summary_not_primary")
    require(bundle["structural_summary"]["role"] == "FACTUAL_SUBSTRATE_AND_SUPPORTING_DISPLAY", "structural_summary_role_invalid")

    profile = profile or ""
    if profile in {"r2r4", "synthesis"}:
        represented = {
            c["domain_id"]
            for c in cases
            if c["evidence_role"] in {
                "PRIMARY_EXPERIMENT_CASE",
                "TYPICAL_POSITIVE_CASE",
                "TYPICAL_NEGATIVE_COMPARATOR",
            }
        }
        require(
            HELD_OUT_DOMAINS <= represented,
            "cross_domain_report_requires_complete_primary_case_from_each_held_out_domain",
        )

    if profile in {"r6", "synthesis"}:
        roles = {c["evidence_role"] for c in cases}
        require("TYPICAL_POSITIVE_CASE" in roles, "r6_report_requires_positive_inertia_candidate_case")
        require("TYPICAL_NEGATIVE_COMPARATOR" in roles, "r6_report_requires_negative_or_reanchored_comparator")
        require(
            any(len(x.get("case_ids") or []) >= 2 for x in bundle.get("contrast_sets") or []),
            "r6_report_requires_explicit_case_contrast",
        )

    if profile == "r5":
        require(bundle.get("contrast_sets"), "r5_report_requires_n0_r5i_realized_contrast")

    for claim in bundle.get("claim_registry") or []:
        require(claim.get("semantic_audit_refs"), "major_claim_missing_semantic_audit_refs")

    require(bundle.get("report_gate_status") == "READY_FOR_REPORT_DRAFT", "report_bundle_not_ready")


def _synthetic_valid_semantic() -> dict[str, Any]:
    return {
        "schema": SEMANTIC_SCHEMA,
        "audit_id": "selftest",
        "reviewer": {"kind": "MODEL", "id": "selftest", "blind_to_prior_semantic_labels": False},
        "evidence_binding": {
            "trace_id": "t",
            "raw_evidence_ref": "raw",
            "raw_evidence_hash": "h",
            "structural_bundle_ref": "struct",
            "structural_bundle_hash": "s",
        },
        "experiment_scope": {
            "stage": "R6",
            "domain_id": "supply_chain",
            "case_id": "c",
            "evidence_role": "TYPICAL_POSITIVE_CASE",
        },
        "actual_agent_route": {
            "complete_route_verified": True,
            "route_node_count": 2,
            "executed_agent_turn_count": 2,
            "nodes": [
                {
                    "route_index": 0, "turn": 1, "agent_role": "inventory", "call_ref": "c0",
                    "event_refs": ["e0"], "input_premises": ["p"], "observed_state_refs": [],
                    "message_or_invoke_refs": [], "output_actions": ["write"], "output_state_refs": ["s0"],
                    "authority_or_status": ["unconfirmed"], "termination_or_censoring": "continue",
                },
                {
                    "route_index": 1, "turn": 2, "agent_role": "risk", "call_ref": "c1",
                    "event_refs": ["e1"], "input_premises": ["p2"], "observed_state_refs": ["s0"],
                    "message_or_invoke_refs": [], "output_actions": ["gate"], "output_state_refs": ["s1"],
                    "authority_or_status": ["recommendation"], "termination_or_censoring": "finalize",
                },
            ],
            "termination": {"run_status": "RUN_COMPLETE", "termination_reason": "finalize"},
        },
        "semantic_nodes": [
            {
                "route_index": 0, "lineage_relevance": "TARGET_LINEAGE",
                "input_semantics": ["capacity uncertain"], "output_semantics": ["1400 ceiling"],
                "semantic_delta": "uncertain capacity -> executable ceiling",
                "semantic_function": "NEW_DESCENDANT_CARRIER",
                "independent_evidence_introduced": False, "independent_evidence_refs": [],
                "evidence_refs": ["e0"], "claim_status": "SUPPORTED",
            },
            {
                "route_index": 1, "lineage_relevance": "TARGET_LINEAGE",
                "input_semantics": ["1400 ceiling"], "output_semantics": ["do not exceed 1400"],
                "semantic_delta": "ceiling -> risk guardrail",
                "semantic_function": "CONSTRAINT_FORMATION",
                "independent_evidence_introduced": False, "independent_evidence_refs": [],
                "evidence_refs": ["e1"], "claim_status": "SUPPORTED",
            },
        ],
        "semantic_edges": [
            {
                "edge_id": "x", "from_route_index": 0, "to_route_index": 1,
                "propagation_type": "DESCENDANT_INHERITANCE", "relation_type": "CONSTRAINS",
                "semantic_before": "1400 ceiling", "semantic_after": "do not exceed 1400",
                "semantic_delta": "operational ceiling -> downstream risk guardrail",
                "independent_evidence_refs": [], "evidence_refs": ["e0", "e1"],
                "claim_status": "SUPPORTED",
            }
        ],
        "case_judgement": {
            "semantic_adoption": "SUPPORTED",
            "decision_action_dependence": "SUPPORTED",
            "post_stimulus_persistence": "SUPPORTED",
            "system_inertia_status": "CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE",
            "semantic_structure_class": "SELFTEST",
            "derivation_edge_ids": ["x"],
            "challenged_source_or_target_ref": "target",
            "direct_stimulus_end_ref": "after-c0",
            "post_stimulus_persistence_node_refs": [1],
            "problematic_bias_status": "NOT_ESTABLISHED",
            "r5_unique_causal_attribution": "NOT_ESTABLISHED",
            "semantic_cpr_status": "NOT_ADJUDICATED",
        },
        "claim_boundaries": ["selftest"],
        "audit_hash": "0123456789abcdef",
    }


def self_test() -> None:
    good = _synthetic_valid_semantic()
    validate_semantic_audit(good)

    bad = copy.deepcopy(good)
    bad["semantic_nodes"] = bad["semantic_nodes"][:1]
    try:
        validate_semantic_audit(bad)
    except ValueError as e:
        require("semantic_nodes_must_cover_every_actual_route_node" in str(e), "selftest_missing_route_node_guard_failed")
    else:
        fail("selftest_missing_route_node_was_not_rejected")

    bad2 = copy.deepcopy(good)
    bad2["experiment_scope"]["domain_id"] = "ecommerce"
    try:
        validate_semantic_audit(bad2)
    except ValueError as e:
        require("ecommerce_may_not_be_primary" in str(e), "selftest_ecommerce_primary_guard_failed")
    else:
        fail("selftest_ecommerce_primary_was_not_rejected")

    bad3 = copy.deepcopy(good)
    bad3["semantic_edges"][0]["propagation_type"] = "INDEPENDENT_REANCHOR"
    bad3["semantic_edges"][0]["independent_evidence_refs"] = []
    try:
        validate_semantic_audit(bad3)
    except ValueError as e:
        require("reanchoring_requires_independent_evidence_refs" in str(e), "selftest_reanchor_guard_failed")
    else:
        fail("selftest_reanchor_without_independent_evidence_was_not_rejected")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--semantic-audit")
    ap.add_argument("--report-bundle")
    ap.add_argument("--profile", choices=["r2r4", "r5", "r6", "synthesis"])
    args = ap.parse_args()

    validate_contracts()
    self_test()

    if args.semantic_audit:
        validate_semantic_audit(load(args.semantic_audit))
        print("SEMANTIC_TRAJECTORY_AUDIT=PASS")

    if args.report_bundle:
        validate_report_bundle(load(args.report_bundle), args.profile)
        print("REPORT_EVIDENCE_BUNDLE=PASS")

    print("SEMANTIC_TRAJECTORY_REPORTING_CONTRACT=PASS")
    print("PRIMARY_EXPERIMENT_DOMAINS=finance,supply_chain,software_engineering")
    print("ECOMMERCE_PRIMARY_EXAMPLE=FORBIDDEN")
    print("COMPLETE_ACTUAL_ROUTE=REQUIRED")
    print("SEMANTIC_BEFORE_AFTER_DELTA=REQUIRED")
    print("UNIFORM_SUBSTANTIVE_DECISION=FORBIDDEN")
    print("PRIMARY_VISUAL=ACTUAL_AGENT_ROUTE_WITH_SEMANTIC_LINEAGE_OVERLAY")


if __name__ == "__main__":
    main()
