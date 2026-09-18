#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
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
        raise ValueError("cross_domain_raw_dir_missing")
    rows = load_jsonl(args.manifest)
    traces_path = raw / "traces.jsonl"
    summary_path = raw / "summary.json"
    auth_path = raw / "authorization_record.json"
    for required in (traces_path, summary_path, auth_path):
        if not required.exists():
            raise ValueError("cross_domain_required_raw_evidence_missing:" + str(required))

    traces = load_jsonl(traces_path)
    summary = load_json(summary_path)
    auth = load_json(auth_path)

    wave_id = int(auth["selected_wave_id"])
    selected_rows = [row for row in rows if int(row["wave_id"]) == wave_id]
    if len(selected_rows) != 15:
        raise ValueError("cross_domain_frozen_wave_must_have_15_planned_rows")
    expected_run_ids = {row["run_id"] for row in selected_rows}
    if any(trace.get("run_id") not in expected_run_ids for trace in traces):
        raise ValueError("cross_domain_trace_not_in_authorized_wave")

    domains = {row["domain_id"] for row in selected_rows}
    if len(domains) != 1:
        raise ValueError("cross_domain_frozen_wave_must_be_domain_pure")
    selected_domain_id = next(iter(domains))
    wave_keys = {row["wave_key"] for row in selected_rows}
    if len(wave_keys) != 1:
        raise ValueError("cross_domain_wave_key_not_unique")
    selected_wave_key = next(iter(wave_keys))

    if auth.get("selected_domain_id") != selected_domain_id:
        raise ValueError("cross_domain_authorization_domain_mismatch")
    if auth.get("selected_wave_key") != selected_wave_key:
        raise ValueError("cross_domain_authorization_wave_key_mismatch")

    domain_trace_counts = Counter(trace.get("domain_id") for trace in traces)
    if any(domain_id != selected_domain_id for domain_id in domain_trace_counts):
        raise ValueError("cross_domain_preserved_trace_crossed_wave_domain")

    record = {
        "schema": "RB-V5-CROSS-DOMAIN-EVIDENCE-BATCH-v0.2",
        "first_round_id": rows[0]["first_round_id"],
        "authorization_event_id": auth["authorization_event_id"],
        "selected_wave_id": wave_id,
        "selected_wave_key": selected_wave_key,
        "selected_domain_id": selected_domain_id,
        "manifest_sha256": sha256_file(args.manifest),
        "traces_sha256": sha256_file(traces_path),
        "summary_sha256": sha256_file(summary_path),
        "authorization_record_sha256": sha256_file(auth_path),
        "journal_hashes": _hash_tree(raw / "journals"),
        "snapshot_hashes": _hash_tree(raw / "snapshots"),
        "selected_run_count": len(selected_rows),
        "preserved_trace_count": len(traces),
        "runner_error_count": summary.get("runner_error_count"),
        "domain_trace_counts": dict(sorted(domain_trace_counts.items())),
        "code_commit_sha": rows[0]["code_commit_sha"],
        "plan_hash": rows[0]["plan_hash"],
        "raw_evidence_frozen_before_structural_derivation": True,
        "automatic_paid_evaluator_called": False,
        "driver_probe_called": False,
        "active_recovery_called": False,
        "semantic_status": "NOT_ADJUDICATED",
    }
    record["evidence_batch_hash"] = stable_hash(record)
    Path(args.out).write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("V5_CROSS_DOMAIN_RAW_EVIDENCE_FROZEN=YES")
    print("AUTHORIZATION_EVENT_ID=" + record["authorization_event_id"])
    print("WAVE_ID=" + str(wave_id))
    print("WAVE_KEY=" + selected_wave_key)
    print("DOMAIN_ID=" + selected_domain_id)
    print("EVIDENCE_BATCH_HASH=" + record["evidence_batch_hash"])


if __name__ == "__main__":
    main()
