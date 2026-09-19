from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _evidence_refs(structural: dict) -> list[str]:
    refs = [structural["direct_exposure"]["call_ref"]]
    refs += [row["ref"] for row in structural["direct_turn_carrier_candidates"]]
    visible = [
        row for row in structural["downstream_structural_observations"]
        if row.get("visible_direct_carrier_refs")
    ][:4]
    refs += [row["call_ref"] for row in visible]
    for row in visible:
        refs += list(row.get("downstream_write_refs") or [])[:2]
    return list(dict.fromkeys(refs))


def build(*, structural_records_path: str, review_manifest_path: str):
    structural = load_jsonl(structural_records_path)
    review = load_json(review_manifest_path)

    _require(review.get("schema") == "RB-V5-CROSS-DOMAIN-R5R6-SEMANTIC-REVIEW-MANIFEST-v0.1", "semantic_review_manifest_schema_invalid")
    _require(len(structural) == 12, "semantic_audit_requires_12_structural_records")
    _require(len(review.get("branch_decisions") or []) == 12, "semantic_review_requires_12_branch_decisions")
    _require(len(review.get("case_decisions") or []) == 6, "semantic_review_requires_6_case_decisions")

    structural_by_key = {
        (row["case_id"], int(row["replicate_index"])): row for row in structural
    }
    _require(len(structural_by_key) == 12, "structural_record_key_collision")

    decision_by_key = {
        (row["case_id"], int(row["replicate_index"])): row
        for row in review["branch_decisions"]
    }
    _require(set(decision_by_key) == set(structural_by_key), "semantic_review_branch_set_mismatch")

    uniform = review["uniform_decision"]
    audits = []
    for key in sorted(structural_by_key, key=lambda x: (structural_by_key[x]["wave_id"], x[1])):
        s = structural_by_key[key]
        d = decision_by_key[key]
        _require(d["structural_observation_hash"] == s["structural_observation_hash"], "semantic_review_structural_hash_mismatch:" + s["r5_run_id"])
        audit = {
            "schema": "RB-V5-CROSS-DOMAIN-R5R6-SEMANTIC-AUDIT-v0.1",
            "audit_id": f"R5R6-SA-{s['wave_id']}-{s['replicate_index']}",
            "case_id": s["case_id"],
            "wave_id": s["wave_id"],
            "domain_id": s["domain_id"],
            "r5_run_id": s["r5_run_id"],
            "replicate_index": s["replicate_index"],
            "structural_observation_hash": s["structural_observation_hash"],
            "reviewer": review["reviewer"],
            "semantic_response_class": d["semantic_response_class"],
            "direct_carrier_semantic_use": uniform["direct_carrier_semantic_use"],
            "downstream_read_adoption": uniform["downstream_read_adoption"],
            "decision_action_dependence": uniform["decision_action_dependence"],
            "post_stimulus_persistence": uniform["post_stimulus_persistence"],
            "system_inertia_status": d["system_inertia_status"],
            "r5_unique_causal_attribution": uniform["r5_unique_causal_attribution"],
            "problematic_bias_status": uniform["problematic_bias_status"],
            "lineage_completeness_status": uniform["lineage_completeness_status"],
            "interpretation": d["interpretation"],
            "evidence_refs": _evidence_refs(s),
            "r7_status": uniform["r7_status"],
            "semantic_cpr_status": uniform["semantic_cpr_status"],
        }
        audit["audit_hash"] = stable_hash(audit)
        audits.append(audit)

    case_decisions = {row["case_id"]: row for row in review["case_decisions"]}
    _require(len(case_decisions) == 6, "semantic_case_decision_collision")
    structural_cases = sorted(set(row["case_id"] for row in structural))
    _require(set(case_decisions) == set(structural_cases), "semantic_review_case_set_mismatch")

    case_summaries = []
    for case_id in structural_cases:
        rows = [row for row in audits if row["case_id"] == case_id]
        _require(len(rows) == 2, "semantic_case_requires_two_intervention_branches:" + case_id)
        c = case_decisions[case_id]
        item = {
            "schema": "RB-V5-CROSS-DOMAIN-R5R6-SEMANTIC-CASE-SUMMARY-v0.1",
            "case_id": case_id,
            "wave_id": rows[0]["wave_id"],
            "domain_id": rows[0]["domain_id"],
            "branch_audit_count": 2,
            "branch_audit_hashes": [row["audit_hash"] for row in sorted(rows, key=lambda x: x["replicate_index"])],
            "case_structure_class": c["case_structure_class"],
            "semantic_adoption_across_intervention_branches": "SUPPORTED_2_OF_2",
            "decision_action_dependence_across_intervention_branches": "SUPPORTED_2_OF_2",
            "post_stimulus_persistence_across_intervention_branches": "SUPPORTED_2_OF_2",
            "case_level_system_inertia_status": c["case_level_system_inertia_status"],
            "problematic_bias_status": "NOT_ESTABLISHED",
            "r5_unique_causal_attribution": "NOT_ESTABLISHED",
            "lineage_completeness_status": "NOT_ASSESSED_THIS_PASS",
            "r7_status": "NOT_AUTHORIZED",
            "semantic_cpr_status": "NOT_ADJUDICATED",
        }
        item["case_summary_hash"] = stable_hash(item)
        case_summaries.append(item)

    inertia_branches = [row for row in audits if row["system_inertia_status"] == "CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE"]
    inertia_cases = [row for row in case_summaries if row["case_level_system_inertia_status"] == "CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE"]
    summary = {
        "schema": "RB-V5-CROSS-DOMAIN-R5R6-SEMANTIC-AUDIT-SUMMARY-v0.1",
        "date": "2026-09-19",
        "source_structural_workflow_run_id": review["source_structural"]["workflow_run_id"],
        "source_structural_artifact_id": review["source_structural"]["artifact_id"],
        "source_structural_artifact_digest": review["source_structural"]["artifact_digest"],
        "source_structural_summary_hash": review["source_structural"]["summary_hash"],
        "reviewer": review["reviewer"],
        "branch_audit_count": len(audits),
        "case_count": len(case_summaries),
        "domain_case_counts": dict(sorted(Counter(row["domain_id"] for row in case_summaries).items())),
        "semantic_adoption_supported_branch_count": sum(row["downstream_read_adoption"] == "SUPPORTED" for row in audits),
        "decision_action_dependence_supported_branch_count": sum(row["decision_action_dependence"] == "SUPPORTED" for row in audits),
        "post_stimulus_persistence_supported_branch_count": sum(row["post_stimulus_persistence"] == "SUPPORTED" for row in audits),
        "system_inertia_supported_candidate_branch_count": len(inertia_branches),
        "system_inertia_supported_candidate_case_count": len(inertia_cases),
        "normal_or_reanchored_persistence_case_count": len(case_summaries) - len(inertia_cases),
        "problematic_bias_established_case_count": 0,
        "r5_unique_causal_attribution_established_case_count": 0,
        "lineage_completeness_assessed": False,
        "r7_authorized": False,
        "new_provider_calls": 0,
        "new_paid_evaluator_calls": 0,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "claim_boundary": (
            "This pass identifies case-level semantic adoption/persistence structures inside six preselected R5 cases. "
            "It does not estimate domain-level occurrence rates, does not establish problematic bias, and does not establish unique causality of the R5 perturbation."
        ),
    }
    summary["summary_hash"] = stable_hash(summary)
    return audits, case_summaries, summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--structural-records", required=True)
    ap.add_argument("--review-manifest", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    audits, cases, summary = build(
        structural_records_path=args.structural_records,
        review_manifest_path=args.review_manifest,
    )
    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r5r6_semantic_audit")
    out.mkdir(parents=True)
    write_jsonl(out / "semantic_audit_records.jsonl", audits)
    write_jsonl(out / "case_semantic_summaries.jsonl", cases)
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("V5_CROSS_DOMAIN_R5R6_SEMANTIC_AUDIT=MATERIALIZED")
    print("BRANCH_AUDIT_COUNT=" + str(summary["branch_audit_count"]))
    print("CASE_COUNT=" + str(summary["case_count"]))
    print("SYSTEM_INERTIA_CANDIDATE_CASES=" + str(summary["system_inertia_supported_candidate_case_count"]))
    print("NEW_PROVIDER_CALLS=0")
    print("R7_AUTHORIZED=NO")
    print("SUMMARY_HASH=" + summary["summary_hash"])


if __name__ == "__main__":
    main()
