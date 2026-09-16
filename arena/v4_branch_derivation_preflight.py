from __future__ import annotations

import argparse
import json
from pathlib import Path

from .derive_branch_measurements_v4 import derive_v4_bundle
from .engine import run_arena_once
from .io_utils import load_json, sha256_file, write_jsonl
from .system_behavior import content_hash
from .v4_binding_preflight import _write_plan_dir, build_fixture_bundle
from .v4_experiment_binding import prepare_v4_binding


ROOT = Path(__file__).resolve().parents[1]
CODE_SHA = "V4_BINDING_PREFLIGHT_CODE_SHA"


class BranchV4FixtureProvider:
    def __init__(self, label: str):
        self.label = label
        self.calls = 0

    def complete_agent(self, messages, metadata=None):
        self.calls += 1
        payload = json.loads(messages[-1]["content"])
        status = ((payload.get("shared_state_metadata") or {}).get("inventory_view") or {}).get("status")
        if self.calls == 1:
            envelope = {
                "decision_summary": f"record branch-visible fixture state from inventory status={status}",
                "actions": [
                    {
                        "type": "write_state",
                        "key": "branch_fixture_view",
                        "value": {"condition_status": status, "label": self.label},
                        "status": "fact",
                        "basis": "engineering-only v4 post-freeze derivation fixture",
                    },
                    {
                        "type": "finalize",
                        "answer": f"{self.label}:first-final:{status}",
                    },
                ],
            }
        else:
            envelope = {
                "decision_summary": "revise settled fixture state after recorded late event",
                "actions": [
                    {
                        "type": "revise_final_state",
                        "patch": {"late_event_reviewed": True, "fixture_label": self.label},
                        "reason": "engineering-only late-event revision fixture",
                    },
                    {
                        "type": "finalize",
                        "answer": f"{self.label}:late-final:{status}",
                    },
                ],
            }
        return {
            "content": json.dumps(envelope, ensure_ascii=False),
            "response_id": f"{self.label}-{self.calls}",
            "model": "V4_BRANCH_DERIVATION_FIXTURE_ONLY",
            "usage": {},
        }


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="results/v4_branch_derivation_preflight")
    args = parser.parse_args()
    outdir = Path(args.outdir)
    if outdir.exists():
        raise ValueError("refusing_to_overwrite_v4_branch_derivation_preflight")
    outdir.mkdir(parents=True, exist_ok=False)

    plan_bundle = build_fixture_bundle()
    plan_dir = outdir / "plan"
    _write_plan_dir(plan_dir, plan_bundle)
    binding = prepare_v4_binding(plan_dir=plan_dir, code_sha=CODE_SHA)

    domain = load_json(ROOT / "arena/domains/ecommerce.json")
    arena_config = load_json(ROOT / "arena/config/arena_v0.3.json")
    manifests = {row["branch_hash"]: row for row in plan_bundle["branch_manifests"]}
    traces = []
    for row in plan_bundle["branch_rows"]:
        start_snapshot = (
            plan_bundle["parent_snapshot"]
            if row["condition_id"] == "CONTROL_CONTINUATION"
            else plan_bundle["intervention_start_snapshot"]
        )
        trace = run_arena_once(
            domain,
            arena_config,
            BranchV4FixtureProvider(row["condition_id"]),
            row["run_id"],
            row["logical_seed"],
            initial_state_snapshot=start_snapshot,
            branch_manifest=manifests[row["branch_hash"]],
        )
        trace.update(
            {
                "pair_id": row["pair_id"],
                "replicate_index": row["replicate_index"],
                "condition_id": row["condition_id"],
                "pair_order_pattern": row["pair_order_pattern"],
                "execution_order": row["execution_order"],
                "branch_plan_hash": plan_bundle["plan"]["plan_hash"],
                "v4_research_binding_hash": binding["binding_hash"],
                "v4_experimental_variable_id": binding["experimental_variable_id"],
                "code_commit_sha": CODE_SHA,
                "domain_hash": row["domain_hash"],
                "arena_config_path": row["arena_config_path"],
                "arena_config_hash": row["arena_config_hash"],
                "model_config_path": row["model_config_path"],
                "model_config_hash": row["model_config_hash"],
                "provider": row["model_provider"],
                "review_status": "PENDING_REVIEW",
            }
        )
        traces.append(trace)

    traces_path = outdir / "traces.jsonl"
    write_jsonl(traces_path, traces)
    evidence = {
        "version": "R2-EVIDENCE-BATCH-v0.2",
        "evidence_batch_hash": content_hash(
            {
                "fixture": "v4_branch_derivation_preflight",
                "traces_sha256": sha256_file(traces_path),
                "code_sha": CODE_SHA,
            }
        ),
        "status": "RUN_COMPLETE_PENDING_REVIEW",
        "review_status": "PENDING_REVIEW",
        "manifest_sha256": "ENGINEERING_FIXTURE_ONLY",
        "traces_sha256": sha256_file(traces_path),
        "errors_sha256": None,
        "code_commit_sha": CODE_SHA,
        "manifest_bindings": [],
    }
    evidence_path = outdir / "evidence_batch.json"
    _write_json(evidence_path, evidence)

    derived = derive_v4_bundle(
        plan_dir=plan_dir,
        traces_path=traces_path,
        evidence_batch_path=evidence_path,
    )
    if len(derived["measurements"]) != len(traces):
        raise RuntimeError("v4_branch_derivation_measurement_count_mismatch")
    if derived["summary"]["measurement_v3_replaced"] is not False:
        raise RuntimeError("v4_branch_derivation_replaced_v3")
    if derived["summary"]["automatic_paid_evaluator_called"] is not False:
        raise RuntimeError("v4_branch_derivation_paid_evaluator_called")
    if derived["summary"]["bounded_review_packet_count"] <= 0:
        raise RuntimeError("v4_branch_derivation_expected_review_packets")
    if any(row.get("semantic_status") != "NOT_ADJUDICATED" for row in derived["measurements"]):
        raise RuntimeError("v4_branch_derivation_semantic_promotion")

    write_jsonl(outdir / "trajectory_measurements_v4.jsonl", derived["measurements"])
    write_jsonl(outdir / "bounded_review_packets_v4.jsonl", derived["review_packets"])
    _write_json(outdir / "summary.json", derived["summary"])
    summary_text = (
        "V4_BRANCH_DERIVATION_PREFLIGHT=PASS\n"
        "SCIENTIFIC_EVIDENCE=NO\n"
        "PAID_API_CALLS=0\n"
        "PAID_EVALUATOR_CALLED=NO\n"
        "MEASUREMENT_V3_REPLACED=NO\n"
        "SEMANTIC_STATUS=NOT_ADJUDICATED\n"
        f"TRACE_COUNT={len(traces)}\n"
        f"MEASUREMENT_V4_COUNT={len(derived['measurements'])}\n"
        f"BOUNDED_REVIEW_PACKET_COUNT={len(derived['review_packets'])}\n"
        f"V4_RESEARCH_BINDING_HASH={binding['binding_hash']}\n"
        f"SUMMARY_HASH={derived['summary']['summary_hash']}\n"
    )
    (outdir / "SUMMARY.txt").write_text(summary_text, encoding="utf-8")
    print(summary_text, end="")


if __name__ == "__main__":
    main()
