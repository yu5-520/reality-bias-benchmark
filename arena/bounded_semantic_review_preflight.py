from __future__ import annotations

import argparse
import json
from pathlib import Path

from arena.bounded_semantic_review_v4 import build_bounded_review_packets, load_review_contract
from arena.io_utils import load_json
from arena.system_behavior_adapter import adapt_arena_trace_v03
from arena.system_behavior_dynamics_v4 import build_system_dynamics_view
from arena.system_behavior_lineage_preflight import build_trace
from arena.system_behavior_lineage_v4 import build_system_lineage_view


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="results/bounded_semantic_review_preflight")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    if outdir.exists():
        raise ValueError("refusing_to_overwrite_bounded_semantic_review_preflight")
    outdir.mkdir(parents=True, exist_ok=False)

    trace = build_trace()
    domain = load_json("arena/domains/ecommerce.json")
    adapted = adapt_arena_trace_v03(trace)
    dynamics = build_system_dynamics_view(adapted)
    lineage = build_system_lineage_view(adapted, dynamics_view=dynamics)
    contract = load_review_contract()
    packets = build_bounded_review_packets(
        trace,
        adapted,
        dynamics,
        lineage,
        domain=domain,
    )
    if not packets:
        raise RuntimeError("bounded_semantic_review_preflight_no_packets")
    for packet in packets:
        if packet.get("review_status") != "PENDING_REVIEW":
            raise RuntimeError("bounded_semantic_review_preflight_status_promoted")
        if any(value != "NOT_ADJUDICATED" for value in packet.get("boundary_fields", {}).values()):
            raise RuntimeError("bounded_semantic_review_preflight_semantic_contamination")
        if packet.get("source_context", {}).get("hidden_chain_of_thought_included") is not False:
            raise RuntimeError("bounded_semantic_review_preflight_hidden_cot_included")
        if packet.get("operational_window", {}).get("authority_penetration_status") != "NOT_ADJUDICATED":
            raise RuntimeError("bounded_semantic_review_preflight_authority_promoted")

    with (outdir / "review_packets_v0.1.jsonl").open("w", encoding="utf-8") as fh:
        for packet in packets:
            fh.write(json.dumps(packet, ensure_ascii=False, sort_keys=True) + "\n")
    (outdir / "review_contract.json").write_text(
        json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (outdir / "SUMMARY.txt").write_text(
        "BOUNDED_SEMANTIC_REVIEW_PREFLIGHT=PASS\n"
        "SCIENTIFIC_EVIDENCE=NO\n"
        "REVIEW_STATUS=PENDING_REVIEW\n"
        "C_P_R_STATUS=NOT_ADJUDICATED\n"
        "AUTHORITY_PENETRATION_STATUS=NOT_ADJUDICATED\n"
        "HIDDEN_CHAIN_OF_THOUGHT_INCLUDED=NO\n"
        f"REVIEW_PACKET_COUNT={len(packets)}\n"
        f"REVIEW_CONTRACT_HASH={packets[0]['review_contract_binding']['hash']}\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "review_packet_count": len(packets),
                "review_contract_hash": packets[0]["review_contract_binding"]["hash"],
                "scientific_evidence": False,
                "semantic_status": "NOT_ADJUDICATED",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
