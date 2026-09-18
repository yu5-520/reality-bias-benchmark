#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl

SCHEMA = "RB-V5-CROSS-DOMAIN-LOCALIZED-SEMANTIC-AUDIT-RECORD-v0.1"
SUMMARY_SCHEMA = "RB-V5-CROSS-DOMAIN-LOCALIZED-SEMANTIC-AUDIT-SUMMARY-v0.1"


def _eligible_by_frozen_rule(case: dict) -> bool:
    return (
        "AUTHORITY_REVIEW_ANCHOR" in (case.get("triage_roles") or [])
        and str((case.get("source") or {}).get("status")) == "fact"
        and bool(case.get("authority_review_markers"))
    )


def materialize(*, triage_cases_path: str, decisions_path: str):
    cases = load_jsonl(triage_cases_path)
    decisions = load_json(decisions_path)
    by_hash = {row["case_hash"]: row for row in cases}
    if len(by_hash) != len(cases):
        raise ValueError("localized_audit_duplicate_source_case_hash")

    reviewed_hashes = decisions["reviewed_case_hashes"]
    if len(reviewed_hashes) != len(set(reviewed_hashes)):
        raise ValueError("localized_audit_duplicate_review_hash")
    missing = [h for h in reviewed_hashes if h not in by_hash]
    if missing:
        raise ValueError("localized_audit_source_case_missing:" + ",".join(missing))

    frozen_rule_hashes = {
        row["case_hash"] for row in cases if _eligible_by_frozen_rule(row)
    }
    if frozen_rule_hashes != set(reviewed_hashes):
        raise ValueError("localized_audit_review_set_not_equal_frozen_selection_rule")

    decision = decisions["uniform_review_decision"]
    auditor = decisions["auditor"]
    rows = []
    for case_hash in reviewed_hashes:
        case = by_hash[case_hash]
        source = case["source"]
        if source.get("status") != "fact":
            raise ValueError("localized_audit_non_fact_source")
        if not case.get("authority_review_markers"):
            raise ValueError("localized_audit_missing_uncertainty_marker")

        pointers = [{
            "pointer": case["candidate_ref"],
            "kind": "SOURCE_STATE",
            "excerpt": json.dumps({
                "state_key": source.get("state_key"),
                "status": source.get("status"),
                "basis": source.get("basis"),
                "value": source.get("value"),
            }, ensure_ascii=False, sort_keys=True),
        }]
        for call in case.get("downstream_call_summaries") or []:
            pointers.append({
                "pointer": (
                    f"trace:{case['source_run_id']}:turn:{call.get('turn')}:"
                    f"actor:{call.get('actor')}:events:"
                    f"{call.get('event_index_start')}-{call.get('event_index_end')}"
                ),
                "kind": "DOWNSTREAM_CALL",
                "excerpt": call.get("decision_summary") or "",
            })

        row = {
            "schema": SCHEMA,
            "audit_id": "XD-SA1-" + case_hash[:20],
            "source_case_hash": case_hash,
            "source_run_id": case["source_run_id"],
            "domain_id": case["domain_id"],
            "wave_id": int(case["wave_id"]),
            "candidate_ref": case["candidate_ref"],
            "content_address": case["content_address"],
            "auditor": auditor,
            "source": {
                **source,
                "authority_review_markers": case.get("authority_review_markers") or [],
            },
            "evidence_pointers": pointers,
            "semantic_adoption": decision["semantic_adoption"],
            "decision_action_dependence": decision["decision_action_dependence"],
            "authority_handling": decision["authority_handling"],
            "authority_escalation": decision["authority_escalation"],
            "r5_scientific_eligibility": decision["r5_scientific_eligibility"],
            "r5_existing_operator_compatibility": decision["r5_existing_operator_compatibility"],
            "r5_probe_authorized": False,
            "r7_repair_authorized": False,
            "claim_boundary": decision["claim_boundary"],
        }
        row["audit_hash"] = stable_hash(row)
        rows.append(row)

    rows.sort(key=lambda r: (r["domain_id"], r["source_run_id"], r["candidate_ref"]))
    domain_counts = Counter(r["domain_id"] for r in rows)
    summary = {
        "schema": SUMMARY_SCHEMA,
        "status": "PASS1_COMPLETE_R5_ELIGIBLE_NOT_AUTHORIZED",
        "source_triage_workflow_run_id": decisions["source_triage"]["workflow_run_id"],
        "source_triage_summary_hash": decisions["source_triage"]["summary_hash"],
        "reviewed_case_count": len(rows),
        "domain_counts": dict(sorted(domain_counts.items())),
        "semantic_adoption_supported_candidate_count": len(rows),
        "decision_action_dependence_supported_candidate_count": len(rows),
        "uncertainty_preserved_supported_candidate_count": len(rows),
        "authority_escalation_established_count": 0,
        "r5_scientifically_eligible_count": len(rows),
        "r5_existing_fact_to_unconfirmed_compatible_count": len(rows),
        "deferred_authority_case_count": int(decisions["deferred_authority_cases"]["count"]),
        "provider_calls": 0,
        "paid_evaluator_calls": 0,
        "r5_probe_calls": 0,
        "r7_repair_calls": 0,
        "r8_cpr_adjudication": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "claim_boundary": decision["claim_boundary"],
    }
    summary["summary_hash"] = stable_hash(summary)
    return rows, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--triage-cases", required=True)
    ap.add_argument("--decisions", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    rows, summary = materialize(
        triage_cases_path=args.triage_cases,
        decisions_path=args.decisions,
    )
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "localized_semantic_audit_records.jsonl", rows)
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("V5_CROSS_DOMAIN_LOCALIZED_SEMANTIC_AUDIT_PASS1=COMPLETE")
    print("REVIEWED_CASE_COUNT=" + str(summary["reviewed_case_count"]))
    print("R5_SCIENTIFICALLY_ELIGIBLE=" + str(summary["r5_scientifically_eligible_count"]))
    print("R5_PROBE_CALLS=0")
    print("R7_REPAIR_CALLS=0")
    print("CPR=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
