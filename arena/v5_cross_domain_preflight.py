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
    assert len(rows) == 90

    domain_counts = Counter(row["domain_id"] for row in rows)
    assert domain_counts == {
        "finance": 30,
        "supply_chain": 30,
        "software_engineering": 30,
    }
    assert "ecommerce" not in domain_counts

    wave_counts = Counter(row["wave_id"] for row in rows)
    assert wave_counts == {1:15,2:15,3:15,4:15,5:15,6:15}
    wave_domains = {
        wave_id: {row["domain_id"] for row in rows if row["wave_id"] == wave_id}
        for wave_id in range(1, 7)
    }
    assert wave_domains == {
        1: {"finance"},
        2: {"finance"},
        3: {"supply_chain"},
        4: {"supply_chain"},
        5: {"software_engineering"},
        6: {"software_engineering"},
    }

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
        "schema": "RB-V5-CROSS-DOMAIN-PREFLIGHT-SUMMARY-v0.2",
        "status": "PASS",
        "planned_natural_trajectories": len(rows),
        "method_development_reference": "ecommerce",
        "method_development_reference_in_new_sample": False,
        "replication_domain_counts": dict(sorted(domain_counts.items())),
        "wave_counts": {str(k): v for k, v in sorted(wave_counts.items())},
        "wave_domains": {str(k): sorted(v) for k, v in wave_domains.items()},
        "six_waves_preregistered": True,
        "six_waves_single_authorization_event_required": True,
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
    print("PLANNED_NEW_NATURAL_TRAJECTORIES=90")
    print("HELD_OUT_DOMAINS=3")
    print("WAVES=6")
    print("RUNS_PER_WAVE=15")
    print("ECOMMERCE_IN_NEW_SAMPLE=NO")
    print("PROVIDER_CALLS=0")
    print("R5_PROBE_CALLS=0")
    print("R7_REPAIR_CALLS=0")


if __name__ == "__main__":
    main()
