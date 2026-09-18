#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, sha256_file


def _hash_tree(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {
        str(p.relative_to(path)): sha256_file(p)
        for p in sorted(path.rglob("*"))
        if p.is_file()
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    raw = Path(args.raw_dir)
    if not raw.exists():
        raise ValueError("v5_whole_process_raw_dir_missing")
    rows = load_jsonl(args.manifest)
    traces_path = raw / "traces.jsonl"
    summary_path = raw / "summary.json"
    auth_path = raw / "authorization_record.json"
    for required in (traces_path, summary_path, auth_path):
        if not required.exists():
            raise ValueError("v5_required_raw_evidence_missing:" + str(required))

    traces = load_jsonl(traces_path)
    summary = load_json(summary_path)
    auth = load_json(auth_path)
    record = {
        "schema": "RB-V5-WHOLE-PROCESS-EVIDENCE-BATCH-v0.1",
        "batch_id": rows[0]["batch_id"],
        "manifest_sha256": sha256_file(args.manifest),
        "traces_sha256": sha256_file(traces_path),
        "summary_sha256": sha256_file(summary_path),
        "authorization_record_sha256": sha256_file(auth_path),
        "journal_hashes": _hash_tree(raw / "journals"),
        "snapshot_hashes": _hash_tree(raw / "snapshots"),
        "planned_run_count": len(rows),
        "preserved_trace_count": len(traces),
        "runner_error_count": summary.get("runner_error_count"),
        "run_status_counts": {},
        "code_commit_sha": rows[0]["code_commit_sha"],
        "batch_design_hash": rows[0]["batch_design_hash"],
        "arena_config_hash": rows[0]["arena_config_hash"],
        "model_config_hash": rows[0]["model_config_hash"],
        "theory_contract_hash": rows[0]["theory_contract_hash"],
        "measurement_contract_hash": rows[0]["measurement_contract_hash"],
        "scout_config_hash": rows[0]["scout_config_hash"],
        "experiment_profile_hash": rows[0]["experiment_profile_hash"],
        "authorization_hash": auth["authorization_hash"],
        "raw_evidence_frozen_before_structural_derivation": True,
        "automatic_paid_evaluator_called": False,
        "driver_probe_called": False,
        "active_recovery_called": False,
        "semantic_status": "NOT_ADJUDICATED",
    }
    for trace in traces:
        status = trace.get("run_status")
        record["run_status_counts"][status] = record["run_status_counts"].get(status, 0) + 1
    record["evidence_batch_hash"] = stable_hash(record)
    Path(args.out).write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V5_WHOLE_PROCESS_RAW_EVIDENCE_FROZEN=YES")
    print("EVIDENCE_BATCH_HASH=" + record["evidence_batch_hash"])


if __name__ == "__main__":
    main()
