#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .io_utils import load_json, load_jsonl, write_jsonl
from .v5_whole_process_index import derive_v5_structural_index


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--evidence-batch", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    evidence = load_json(args.evidence_batch)
    if evidence.get("raw_evidence_frozen_before_structural_derivation") is not True:
        raise ValueError("v5_raw_freeze_required_before_structural_derivation")
    if evidence.get("automatic_paid_evaluator_called") is not False:
        raise ValueError("v5_paid_evaluator_must_be_false")

    traces = load_jsonl(Path(args.raw_dir) / "traces.jsonl")
    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_v5_structural_derivation")
    out.mkdir(parents=True)

    indexes = []
    for trace in traces:
        row = derive_v5_structural_index(trace)
        row["evidence_batch_hash"] = evidence["evidence_batch_hash"]
        indexes.append(row)
    write_jsonl(out / "v5_structural_index.jsonl", indexes)

    summary = {
        "schema": "RB-V5-WHOLE-PROCESS-STRUCTURAL-DERIVATION-SUMMARY-v0.2",
        "evidence_batch_hash": evidence["evidence_batch_hash"],
        "trace_count": len(traces),
        "repair_anchor_candidate_run_count": sum(bool((x.get("engineering_core") or {}).get("first_repair_anchor_candidate_ref")) for x in indexes),
        "content_addressable_run_count": sum(bool((x.get("engineering_core") or {}).get("content_address_count")) for x in indexes),
        "semantic_lineage_recoverability_status": "STRUCTURAL_PROVENANCE_READY_SEMANTIC_AUDIT_REQUIRED",
        "optional_mechanism_observables": {
            "support_candidate_run_count": sum(bool(x.get("first_support_candidate_ref")) for x in indexes),
            "pool_candidate_run_count": sum(bool(x.get("first_pool_candidate_ref")) for x in indexes),
            "exposure_candidate_run_count": sum(bool(x.get("first_exposure_candidate_ref")) for x in indexes),
        },
        "direct_pool_consumption_semantic_status": "NOT_ADJUDICATED",
        "new_provider_calls": 0,
        "new_evaluator_calls": 0,
        "raw_evidence_changed": False,
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V5_STRUCTURAL_DERIVATION_COMPLETE")
    print("TRACE_COUNT=" + str(len(traces)))
    print("NEW_PROVIDER_CALLS=0")
    print("NEW_EVALUATOR_CALLS=0")


if __name__ == "__main__":
    main()
