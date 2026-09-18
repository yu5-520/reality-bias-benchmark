#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json


SCHEMA = "RB-V5-CROSS-DOMAIN-FIRST-ROUND-REGISTRY-v0.2"


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
    authorization_event_ids = {batch["authorization_event_id"] for batch in batches}
    if len(first_round_ids) != 1:
        raise ValueError("cross_domain_registry_first_round_id_mismatch")
    if len(code_shas) != 1:
        raise ValueError("cross_domain_registry_execution_sha_mismatch")
    if len(plan_hashes) != 1:
        raise ValueError("cross_domain_registry_plan_hash_mismatch")
    if len(authorization_event_ids) != 1:
        raise ValueError("cross_domain_registry_authorization_event_mismatch")

    if any(int(batch["selected_run_count"]) != 15 for batch in batches):
        raise ValueError("cross_domain_registry_each_wave_must_plan_15_runs")
    planned = sum(int(batch["selected_run_count"]) for batch in batches)
    if planned != 90:
        raise ValueError("cross_domain_registry_planned_run_count_mismatch")

    expected_wave_domain = {
        1: "finance",
        2: "finance",
        3: "supply_chain",
        4: "supply_chain",
        5: "software_engineering",
        6: "software_engineering",
    }
    expected_wave_key = {
        1: "finance-w1",
        2: "finance-w2",
        3: "supply_chain-w1",
        4: "supply_chain-w2",
        5: "software_engineering-w1",
        6: "software_engineering-w2",
    }

    domain_counts: Counter[str] = Counter()
    wave_rows = []
    for batch in sorted(batches, key=lambda x: int(x["selected_wave_id"])):
        wave_id = int(batch["selected_wave_id"])
        if batch["selected_domain_id"] != expected_wave_domain[wave_id]:
            raise ValueError("cross_domain_registry_wave_domain_mismatch:" + str(wave_id))
        if batch["selected_wave_key"] != expected_wave_key[wave_id]:
            raise ValueError("cross_domain_registry_wave_key_mismatch:" + str(wave_id))
        domain_counts.update(batch.get("domain_trace_counts") or {})
        wave_rows.append({
            "wave_id": wave_id,
            "wave_key": batch["selected_wave_key"],
            "domain_id": batch["selected_domain_id"],
            "evidence_batch_hash": batch["evidence_batch_hash"],
            "selected_run_count": int(batch["selected_run_count"]),
            "preserved_trace_count": int(batch["preserved_trace_count"]),
            "runner_error_count": int(batch["runner_error_count"]),
            "domain_trace_counts": batch.get("domain_trace_counts") or {},
        })

    out = {
        "schema": SCHEMA,
        "first_round_id": next(iter(first_round_ids)),
        "authorization_event_id": next(iter(authorization_event_ids)),
        "wave_count": 6,
        "all_waves_present": True,
        "same_execution_sha": True,
        "same_plan_hash": True,
        "same_authorization_event": True,
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
    print("AUTHORIZATION_EVENT_ID=" + registry["authorization_event_id"])
    print("PLANNED_SELECTED_RUN_COUNT=90")
    print("PRESERVED_TRACE_COUNT=" + str(registry["preserved_trace_count"]))
    print("RUNNER_ERROR_COUNT=" + str(registry["runner_error_count"]))
    print("SEMANTIC_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
