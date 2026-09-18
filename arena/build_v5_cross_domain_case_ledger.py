#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .io_utils import load_jsonl, write_jsonl


SCHEMA = "RB-V5-CROSS-DOMAIN-CASE-QUALIFICATION-v0.1"


def build_rows(index_rows: list[dict], *, first_round_id: str) -> list[dict]:
    out: list[dict] = []
    for idx in index_rows:
        run_id = idx.get("trajectory_id")
        domain_id = idx.get("domain_id")
        candidates = (idx.get("engineering_core") or {}).get("repair_anchor_candidate_refs") or []
        candidate_map = {row.get("candidate_ref"): row for row in idx.get("candidates") or []}
        if not candidates:
            out.append({
                "schema": SCHEMA,
                "first_round_id": first_round_id,
                "domain_id": domain_id or "UNKNOWN",
                "source_run_id": run_id or "UNKNOWN",
                "candidate_ref": None,
                "content_address": None,
                "structural_candidate_status": "NO_ADDRESSABLE_CANDIDATE",
                "semantic_audit_status": "NOT_REQUIRED_NO_CANDIDATE",
                "qualification_status": "NO_QUALIFYING_NATURAL_STRUCTURE",
                "r5_probe_authorized": False,
                "r7_repair_authorized": False,
                "evidence_refs": [],
                "claim_boundary": "No structural repair-anchor candidate was derived; no target may be invented to force R5.",
            })
            continue
        for ref in candidates:
            candidate = candidate_map.get(ref) or {}
            out.append({
                "schema": SCHEMA,
                "first_round_id": first_round_id,
                "domain_id": domain_id or "UNKNOWN",
                "source_run_id": run_id or "UNKNOWN",
                "candidate_ref": ref,
                "content_address": candidate.get("content_address"),
                "structural_candidate_status": "STRUCTURAL_CANDIDATE_OBSERVED",
                "semantic_audit_status": "PENDING_LOCALIZED_SEMANTIC_AUDIT",
                "qualification_status": "AWAITING_LOCALIZED_SEMANTIC_AUDIT",
                "r5_probe_authorized": False,
                "r7_repair_authorized": False,
                "evidence_refs": [ref],
                "claim_boundary": "Structural candidacy does not establish semantic adoption, problematic authority, R5 eligibility or R7 repairability.",
            })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--structural-index", required=True)
    ap.add_argument("--first-round-id", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = build_rows(load_jsonl(args.structural_index), first_round_id=args.first_round_id)
    write_jsonl(args.out, rows)
    print("CROSS_DOMAIN_CASE_LEDGER_ROWS=" + str(len(rows)))
    print("R5_PROBE_AUTHORIZED=NO")
    print("R7_REPAIR_AUTHORIZED=NO")
    print("SEMANTIC_AUDIT=DEFERRED_APPEND_ONLY")


if __name__ == "__main__":
    main()
