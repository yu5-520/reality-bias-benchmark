from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .build_v5_cross_domain_manifest import build_rows, verify_manifest
from .v5_whole_process_index import derive_v5_structural_index
from .v5_whole_process_preflight import _fixture_trace


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="results/v5_cross_domain_preflight")
    ap.add_argument("--code-sha", default="OFFLINE-PREFLIGHT")
    args = ap.parse_args()

    rows = build_rows(code_sha=args.code_sha)
    assert verify_manifest(rows)
    assert len(rows) == 120

    domain_counts = Counter(row["domain_id"] for row in rows)
    assert domain_counts == {
        "ecommerce": 30,
        "finance": 30,
        "supply_chain": 30,
        "software_engineering": 30,
    }
    wave_counts = Counter(row["wave_id"] for row in rows)
    assert wave_counts == {1: 20, 2: 20, 3: 20, 4: 20, 5: 20, 6: 20}

    index = derive_v5_structural_index(_fixture_trace())
    assert index["engineering_core"]["first_repair_anchor_candidate_ref"]
    assert index["engineering_core"]["content_address_count"] >= 1
    assert index["direct_pool_consumption_semantic_status"] == "NOT_ADJUDICATED"

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest_candidate.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    summary = {
        "schema": "RB-V5-CROSS-DOMAIN-PREFLIGHT-SUMMARY-v0.1",
        "status": "PASS",
        "planned_natural_trajectories": len(rows),
        "domain_counts": dict(sorted(domain_counts.items())),
        "wave_counts": {str(k): v for k, v in sorted(wave_counts.items())},
        "provider_calls": 0,
        "evaluator_calls": 0,
        "r5_probe_calls": 0,
        "r7_repair_calls": 0,
        "agent_runtime_modified": False,
        "method_development_history_replayed_in_replication_domains": False,
        "r8_cpr_adjudication": False,
        "structural_index_fixture": "PASS",
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("V5_CROSS_DOMAIN_PREFLIGHT=PASS")
    print("PLANNED_NATURAL_TRAJECTORIES=120")
    print("DOMAINS=4")
    print("WAVES=6")
    print("RUNS_PER_WAVE=20")
    print("PROVIDER_CALLS=0")
    print("R5_PROBE_CALLS=0")
    print("R7_REPAIR_CALLS=0")


if __name__ == "__main__":
    main()
