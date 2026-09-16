from __future__ import annotations

import argparse
import json
from pathlib import Path

from .system_behavior_adapter import adapt_arena_trace_v03
from .system_behavior_dynamics_v4 import build_system_dynamics_view
from .system_behavior_lineage_preflight import build_trace
from .system_behavior_lineage_v4 import build_system_lineage_view
from .v4_review_contract import build_review_record
from .v4_review_packets import build_bounded_review_packets


ENGINEERING_EVIDENCE_HASH = "ENGINEERING_ONLY_V4_REVIEW_PREFLIGHT_EVIDENCE"
ENGINEERING_BINDING_HASH = "ENGINEERING_ONLY_V4_REVIEW_PREFLIGHT_BINDING"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="results/v4_review_preflight")
    args = parser.parse_args()
    outdir = Path(args.outdir)
    if outdir.exists():
        raise ValueError("refusing_to_overwrite_v4_review_preflight")
    outdir.mkdir(parents=True, exist_ok=False)

    trace = build_trace()
    adapted = adapt_arena_trace_v03(trace)
    dynamics = build_system_dynamics_view(adapted)
    lineage = build_system_lineage_view(adapted, dynamics_view=dynamics)
    packets = build_bounded_review_packets(
        trace,
        adapted,
        dynamics,
        lineage,
        evidence_batch_hash=ENGINEERING_EVIDENCE_HASH,
        v4_research_binding_hash=ENGINEERING_BINDING_HASH,
    )
    if not packets:
        raise RuntimeError("v4_review_preflight_expected_packets")
    if any(packet.get("semantic_status") != "NOT_ADJUDICATED" for packet in packets):
        raise RuntimeError("v4_review_preflight_packet_semantic_promotion")
    if any(packet["omission_report"].get("full_trajectory_included") for packet in packets):
        raise RuntimeError("v4_review_preflight_full_trajectory_leak")
    if any(packet["omission_report"].get("raw_model_output_included") for packet in packets):
        raise RuntimeError("v4_review_preflight_raw_output_leak")

    contract_fixture = build_review_record(
        review_record_id="V4-REVIEW-CONTRACT-PREFLIGHT-ONLY",
        record_kind="independent",
        packet=packets[0],
        reviewer={"id": "ENGINEERING_PREFLIGHT_ONLY", "type": "contract_validator"},
        judgments={
            "completion_bias": "UNCERTAIN",
            "perfection_bias": "UNCERTAIN",
            "bias_realization": "UNCERTAIN",
            "semantic_adoption": "UNCERTAIN",
            "decision_effect": "UNCERTAIN",
            "operational_force": "UNCERTAIN",
            "authority_condition_status": "UNCERTAIN",
            "authority_penetration": "UNCERTAIN",
            "prior_cp_status": "UNCERTAIN",
            "retrospective_bias": "UNCERTAIN",
            "retrospective_outcomes": [],
            "recovery_status": "UNCERTAIN",
            "evidence_sufficiency": "INSUFFICIENT",
        },
        rationale="Engineering-only schema fixture. No semantic scientific judgment is made.",
        confidence=0.0,
        uncertainties=["ENGINEERING_FIXTURE_NOT_SCIENTIFIC_REVIEW"],
        evidence_refs=[],
        created_at="2026-09-16T00:00:00Z",
    )

    with (outdir / "bounded_review_packets_v4.jsonl").open("w", encoding="utf-8") as fh:
        for packet in packets:
            fh.write(json.dumps(packet, ensure_ascii=False, sort_keys=True) + "\n")
    (outdir / "review_contract_fixture.json").write_text(
        json.dumps(contract_fixture, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = (
        "V4_BOUNDED_REVIEW_PREFLIGHT=PASS\n"
        "SCIENTIFIC_EVIDENCE=NO\n"
        "SEMANTIC_REVIEW_PERFORMED=NO\n"
        "PAID_EVALUATOR_CALLED=NO\n"
        "FULL_TRAJECTORY_IN_PACKET=NO\n"
        "RAW_MODEL_OUTPUT_IN_PACKET=NO\n"
        "HIDDEN_CHAIN_OF_THOUGHT_IN_PACKET=NO\n"
        f"PACKET_COUNT={len(packets)}\n"
        f"CONTRACT_FIXTURE_RECORD_HASH={contract_fixture['record_hash']}\n"
    )
    (outdir / "SUMMARY.txt").write_text(summary, encoding="utf-8")
    print(summary, end="")


if __name__ == "__main__":
    main()
