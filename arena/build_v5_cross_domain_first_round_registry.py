#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json


SCHEMA = "RB-V5-CROSS-DOMAIN-FIRST-ROUND-REGISTRY-v0.1"


def build_registry(batch_paths: list[str]) -> dict:
    if len(batch_paths) != 6:
        raise ValueError("cross_domain_registry_requires_exactly_six_wave_batches")

    batches = [load_json(path) for path in batch_paths]
    wave_ids = [int(batch["selected_wave_id"]) for batch in batches]
    if set(wave_ids) != set(range(1, 7)) or len(set(wave_ids)) != 6:
        raise ValueError("cross_domain_registry_wave_set_invalid")

    first_round_ids = {batch["first_round_id"] for batch in batches}
    code_shas = {batch["code_commit_sha"] for batch in batches}
    plan_hashes = {batch["plan_hash"] for batch in batches}
    if len(first_round_ids) != 1:
        raise ValueError("cross_domain_registry_first_round_id_mismatch")
    if len(code_shas) != 1:
        raise ValueError("cross_domain_registry_execution_sha_mismatch")
    if len(plan_hashes) != 1:
        raise ValueError("cross_domain_registry_plan_hash_mismatch")

    planned = sum(int(batch["selected_run_count"]) for batch in batches)
    if planned != 120:
        raise ValueError("cross_domain_registry_planned_run_count_mismatch")

    domain_counts: Counter[str] = Counter()
    for batch in batches:
        domain_counts.update(batch.get("domain_trace_counts") or {})

    wave_rows = []
    for batch in sorted(batches, key=lambda x: int(x["selected_wave_id"])):
        wave_rows.append({
            "wave_id": int(batch["selected_wave_id"]),
            "evidence_batch_hash": batch["evidence_batch_hash"],
            "selected_run_count": int(batch["selected_run_count"]),
            "preserved_trace_count": int(batch["preserved_trace_count"]),
            "runner_error_count": int(batch["runner_error_count"]),
            "domain_trace_counts": batch.get("domain_trace_counts") or {},
        })

    out = {
        "schema": SCHEMA,
        "first_round_id": next(iter(first_round_ids)),
        "wave_count": 6,
        "all_waves_present": True,
        "same_execution_sha": True,
        "same_plan_hash": True,
        "planned_selected_run_count": planned,
        "preserved_trace_count": sum(int(batch["preserved_trace_count"]) for batch in batches),
        "runner_error_count": sum(int(batch["runner_error_count"]) for batch in batches),
        "domain_trace_counts": dict(sorted(domain_counts.items())),
        "wave_batches": wave_rows,
        "code_commit_sha": next(iter(code_shas)),
        "plan_hash": next(iter(plan_hashes)),
        "semantic_status": "NOT_ADJUDICATED",
    }
    out["registry_hash"] = stable_hash(out)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-batch", action="append", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    registry = build_registry(args.evidence_batch)
    Path(args.out).write_text(
        json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("CROSS_DOMAIN_FIRST_ROUND_REGISTRY=COMPLETE")
    print("PRESERVED_TRACE_COUNT=" + str(registry["preserved_trace_count"]))
    print("RUNNER_ERROR_COUNT=" + str(registry["runner_error_count"]))
    print("SEMANTIC_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
