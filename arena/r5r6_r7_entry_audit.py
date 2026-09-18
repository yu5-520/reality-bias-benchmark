from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .core import stable_hash
from .r5r6_engineering_package import build_package

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BINDING = "configs/r5r6_r7_entry_engineering_audit_binding_v0.1.json"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    material = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    return hashlib.sha1(material).hexdigest()


def _verify_bound_sources(binding: dict) -> dict[str, str]:
    verified = {}
    for row in binding["sources"]:
        path = ROOT / row["path"]
        _require(path.exists(), "missing_audit_source:" + row["path"])
        actual = _git_blob_sha(path)
        _require(actual == row["git_blob_sha"], "audit_source_blob_changed:" + row["path"])
        verified[row["role"]] = "git-blob:" + actual + ":" + row["path"]
    return verified


def _require_tokens(path: str, tokens: list[str]) -> None:
    body = (ROOT / path).read_text(encoding="utf-8")
    for token in tokens:
        _require(token in body, path + ":missing_token:" + token)


def build_audit(binding_path: str = DEFAULT_BINDING) -> dict:
    binding = _load_json(ROOT / binding_path)
    _require(binding["schema"] == "RB-R5R6-R7-ENTRY-AUDIT-BINDING-v0.1", "audit_binding_schema_invalid")
    verified_sources = _verify_bound_sources(binding)

    _require_tokens(
        "docs/reports/2026-09-17/R5MID_OneShot_Process_Evidence_Report_v3.md",
        [
            "Direct experiment-origin exposures | 1 per B run",
            "Experiment-origin reinjection      | 0",
            "Persistent state mutation          | false",
            "fact -> unconfirmed",
        ],
    )
    _require_tokens(
        "docs/reports/2026-09-17/R5MID_Matched_AB_Mechanism_Validation_Report_v3.md",
        [
            "Pair 1: local expansion under intervention",
            "Pair 2: cross-agent contraction under intervention",
            "A2 cross-agent path collapses to O in B2",
            "direction of that reorganization is not stable",
        ],
    )
    _require_tokens(
        "docs/reports/2026-09-17/R6_System_Inertia_Factual_Report_v2.md",
        [
            "Immediate/local perturbation response != post-consumption system inertia.",
            "Pair 2 is the strongest frozen inertia-level contrast.",
            "Cross-Agent spread transition | OBSERVED",
            "These facts are sufficient to treat system inertia as a real analysis object",
        ],
    )
    _require_tokens(
        "docs/reports/2026-09-18/R5-R6_Engineering_Experiment_Report_v1.md",
        [
            "Repair Anchor != Semantic Origin",
            "COMPLETE_FOR_AUTHORIZED_REPAIR",
            "R7 READY FOR SEPARATE AUTHORIZATION",
        ],
    )

    semantic = _load_json(ROOT / "reviews/v5_semantic_mechanism_reaudit_2026-09-18/audit_summary.json")
    _require(semantic["findings"]["stable_shared_pool_existence_by_R6_continuation"] == "SUPPORTED", "stable_pool_not_supported")
    _require(semantic["findings"]["semantic_descendant_persistence"] == "SUPPORTED", "semantic_descendant_persistence_not_supported")
    _require(semantic["findings"]["direct_pool_consumption_attribution"] == "SUPPORTED_CANDIDATE", "pool_consumption_boundary_changed")
    _require(semantic["findings"]["J0_specific_semantic_inertia"] == "NOT_ESTABLISHED", "j0_specificity_boundary_changed")
    _require(semantic["cpr_status"] == "NOT_ADJUDICATED", "cpr_must_remain_unadjudicated")

    package = build_package()
    summary = package["summary"]
    gate = package["lineage_completeness_gate"]
    packet = package["semantic_repair_packet"]

    criteria = [
        {
            "criterion": "R5_INTERVENTION_ISOLATED",
            "status": "PASS",
            "evidence": {
                "direct_experiment_origin_exposures": 1,
                "experiment_origin_reinjection": 0,
                "persistent_parent_state_mutation": False,
                "operator": "fact -> unconfirmed",
            },
            "why_it_matters_for_r7": "R7 can reuse a bounded authority manipulation without confusing repair effects with repeated experimental forcing.",
        },
        {
            "criterion": "MATCHED_DOWNSTREAM_REORGANIZATION_OBSERVED",
            "status": "PASS",
            "evidence": {
                "pair1_descendant_rejumps": "1 -> 3",
                "pair1_root_reachable": "5 -> 9",
                "pair2_descendant_rejumps": "5 -> 1",
                "pair2_root_reachable": "34 -> 5",
                "pair2_depth": "6 -> 3",
                "pair2_path_families": "149 -> 2",
                "pair2_cross_agent_relations": "17 -> 1",
                "pair2_role_reentry": "1 -> 0",
                "directionality": "REVERSES_ACROSS_PAIRS",
            },
            "why_it_matters_for_r7": "There is an experimentally observed downstream process surface for a localized recovery experiment to attempt to steer or repair.",
        },
        {
            "criterion": "POST_CONSUMPTION_INERTIA_OBJECT_JUSTIFIED",
            "status": "PASS",
            "evidence": {
                "r6_pair2_inertia_level_contrast": "OBSERVED",
                "cross_agent_spread_transition": "OBSERVED",
                "path_family_transition": "OBSERVED",
                "role_reentry_transition": "OBSERVED",
            },
            "why_it_matters_for_r7": "R7 has a nontrivial post-consumption process object to test; it is not merely repairing an immediate local response.",
        },
        {
            "criterion": "SEMANTIC_CARRIER_OR_DESCENDANT_PERSISTENCE_SUPPORTED",
            "status": "PASS",
            "evidence": {
                "stable_shared_pool_existence": semantic["findings"]["stable_shared_pool_existence_by_R6_continuation"],
                "semantic_descendant_persistence": semantic["findings"]["semantic_descendant_persistence"],
                "direct_pool_consumption": semantic["findings"]["direct_pool_consumption_attribution"],
            },
            "why_it_matters_for_r7": "The repair target can be framed as a persisted shared/descendant structure rather than an isolated text token.",
        },
        {
            "criterion": "REPAIR_ANCHOR_MACHINE_ADDRESSABLE",
            "status": "PASS" if summary["repair_anchor_ref"] and summary["content_address"] else "FAIL",
            "evidence": {
                "repair_anchor_ref": summary["repair_anchor_ref"],
                "content_address": summary["content_address"],
            },
            "why_it_matters_for_r7": "R7 can bind a repair experiment to a stable engineering object rather than a prose description.",
        },
        {
            "criterion": "BOUNDED_SEMANTIC_LINEAGE_COMPLETE_FOR_REPAIR_EXPERIMENT",
            "status": "PASS" if gate["status"] == "COMPLETE_FOR_AUTHORIZED_REPAIR" else "FAIL",
            "evidence": {
                "completeness_scope": summary["completeness_scope"],
                "gate_status": gate["status"],
                "gate_hash": gate["gate_hash"],
                "packet_hash": packet["packet_hash"],
            },
            "why_it_matters_for_r7": "The declared R5-R6 horizon can be carried into R7 without inventing missing semantic history.",
        },
        {
            "criterion": "R7_RESEARCH_QUESTION_REMAINS_OPEN",
            "status": "PASS",
            "evidence": {
                "repair_efficacy": "NOT_YET_EXECUTED",
                "old_lineage_reentry_after_repair": "NOT_ESTABLISHED",
                "preserved_unrelated_structure_after_repair": "NOT_ESTABLISHED",
            },
            "why_it_matters_for_r7": "R7 is necessary rather than redundant: R5-R6 identify the repairable structure but do not answer whether localized recovery works.",
        },
        {
            "criterion": "NO_OVERCLAIM_OR_AUTOMATIC_REPAIR_AUTHORIZATION",
            "status": "PASS" if (
                summary["active_repair_authorized"] is False
                and packet["repair_authorization_status"] == "READY_FOR_SEPARATE_AUTHORIZATION"
                and semantic["cpr_status"] == "NOT_ADJUDICATED"
            ) else "FAIL",
            "evidence": {
                "active_repair_authorized": summary["active_repair_authorized"],
                "repair_authorization_status": packet["repair_authorization_status"],
                "semantic_cpr_status": semantic["cpr_status"],
                "j0_specific_semantic_inertia": semantic["findings"]["J0_specific_semantic_inertia"],
            },
            "why_it_matters_for_r7": "The audit opens only the experimental entry gate and does not convert unresolved scientific claims into engineering facts.",
        },
    ]

    criteria_by_name = {row["criterion"]: row["status"] for row in criteria}
    required = list(binding["entry_criteria"])
    _require(set(required) == set(criteria_by_name), "audit_criteria_binding_mismatch")
    passed = all(criteria_by_name[name] == "PASS" for name in required)

    decision = (
        "PASS_R7_ENTRY_BOUNDED_ENGINEERING_EXPERIMENT"
        if passed
        else "HOLD_R7_ENTRY_INSUFFICIENT_EVIDENCE"
    )

    unresolved = [
        "Exact first Structural Support identity remains NOT_ESTABLISHED.",
        "Exact first Stable Shared Pool entry remains NOT_ESTABLISHED.",
        "Exclusive field-level pool-to-judgment attribution remains incomplete.",
        "J0-specific semantic inertia remains NOT_ESTABLISHED.",
        "Structure-only driving remains NOT_ESTABLISHED.",
        "Semantic CPR remains NOT_ADJUDICATED.",
        "R7 repair efficacy, preservation and old-lineage re-entry remain untested.",
    ]

    out = {
        "schema": "RB-R5R6-R7-ENTRY-ENGINEERING-AUDIT-v0.1",
        "date": "2026-09-18",
        "audit_question": binding["audit_question"],
        "decision": decision,
        "decision_scope": "HISTORICAL_E32_J0_TARGET_WITHIN_FROZEN_DECLARED_R5_R6_OBSERVATION_HORIZON",
        "evidence_sources": verified_sources,
        "criteria": criteria,
        "criteria_passed": sum(row["status"] == "PASS" for row in criteria),
        "criteria_total": len(criteria),
        "r5r6_engineering_package": {
            "summary_hash": summary["summary_hash"],
            "semantic_lineage_closure_hash": summary["semantic_lineage_closure_hash"],
            "lineage_completeness_gate_hash": summary["lineage_completeness_gate_hash"],
            "semantic_repair_packet_hash": summary["semantic_repair_packet_hash"],
        },
        "unresolved_nonblocking_for_bounded_r7": unresolved,
        "r7_entry_supported": passed,
        "active_r7_repair_authorized": False,
        "separate_manual_authorization_required": True,
        "new_subject_provider_calls": 0,
        "new_paid_evaluator_calls": 0,
        "raw_evidence_mutated": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "interpretation_boundary": (
            "PASS means the frozen R5-R6 evidence is sufficient to justify and technically bind a bounded R7 localized-recovery experiment. "
            "It does not mean localized recovery is effective, that J0 is a universal causal origin, that CPR is adjudicated, or that the result generalizes across models/domains."
        ),
    }
    out["audit_hash"] = stable_hash(out)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binding", default=DEFAULT_BINDING)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = build_audit(args.binding)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("R5R6_R7_ENTRY_AUDIT=" + out["decision"])
    print("CRITERIA=" + str(out["criteria_passed"]) + "/" + str(out["criteria_total"]))
    print("R7_ENTRY_SUPPORTED=" + ("YES" if out["r7_entry_supported"] else "NO"))
    print("ACTIVE_R7_REPAIR_AUTHORIZED=NO")
    print("SEPARATE_MANUAL_AUTHORIZATION_REQUIRED=YES")
    print("AUDIT_HASH=" + out["audit_hash"])


if __name__ == "__main__":
    main()
