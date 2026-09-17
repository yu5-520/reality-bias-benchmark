#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .core import stable_hash
from .engine import run_arena_once
from .io_utils import load_json, write_jsonl
from .prepare_r6d_matched_stock_plan import load_runtime_plan
from .r6d_matched_stock_atomic import CONDITIONS, MatchedStockAtomicEpistemicAnnotationTransform

SMOKE_SCHEMA = "RB-R6D-MATCHED-STOCK-RUNTIME-SMOKE-v0.1"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


class MatchedStockOfflineSmokeProvider:
    def __init__(self, condition_id: str, expected_target: str):
        self.condition_id = condition_id
        self.expected_target = expected_target
        self.t9 = 0
        self.t10 = 0

    def complete_agent(self, messages, metadata=None):
        metadata = metadata or {}
        actor = metadata.get("agent_id")
        turn = int(metadata.get("turn") or 0)
        payload = json.loads(messages[-1]["content"])
        annotations = list(payload.get("epistemic_annotations") or [])
        if turn == 9:
            _require(len(annotations) == 1, "matched_stock_smoke_requires_one_t9_annotation")
            _require(annotations[0].get("target_locator") == self.expected_target, "matched_stock_smoke_target_mismatch")
            _require(annotations[0].get("epistemic_status") == "unconfirmed", "matched_stock_smoke_status_mismatch")
            self.t9 = 1
            actions = [
                {"type": "message", "to": "ads", "content": "offline matched-stock smoke downstream handoff"},
                {"type": "finalize", "answer": "offline matched-stock smoke T9"},
            ]
        elif turn == 10:
            _require(not annotations, "matched_stock_smoke_annotation_must_be_consumed_before_t10")
            self.t10 = 0
            actions = [{"type": "finalize", "answer": "offline matched-stock smoke T10"}]
        else:
            actions = [{"type": "finalize", "answer": "offline matched-stock smoke terminal"}]
        return {
            "response_id": f"offline-matched-stock-smoke:{self.condition_id}:{actor}:{turn}",
            "provider_response": {"offline_smoke": True, "condition_id": self.condition_id},
            "finish_reason": "stop",
            "model": "offline-matched-stock-smoke",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
            "transport_latency_ms": 0,
            "content": json.dumps({"decision_summary": "offline matched-stock smoke", "actions": actions}, ensure_ascii=False),
        }


def run_smoke(plan_dir: str | Path, domain_path: str | Path) -> tuple[list[dict], dict]:
    bundle = load_runtime_plan(plan_dir)
    domain = load_json(domain_path)
    config = copy.deepcopy(bundle["bounded_arena_config"])
    parent_hash_before = stable_hash(bundle["source_parent_snapshot"])
    traces = []
    exposures = {c: 0 for c in CONDITIONS}
    post_turns = {c: 0 for c in CONDITIONS}

    for row in sorted(bundle["execution_rows"], key=lambda x: (x["replicate_index"], x["execution_order"])):
        condition = row["condition_id"]
        envelope = bundle["condition_envelopes"][condition]
        transform = MatchedStockAtomicEpistemicAnnotationTransform(envelope)
        provider = MatchedStockOfflineSmokeProvider(condition, envelope["target_locator"])
        trace = run_arena_once(
            domain,
            config,
            provider,
            row["run_id"],
            logical_seed=row["logical_seed"],
            initial_state_snapshot=bundle["source_parent_snapshot"],
            runtime_view_transform=transform,
        )
        transform.verify_finished()
        tx = transform.summary()
        _require(tx["direct_experiment_origin_exposure_count"] == 1, "matched_stock_smoke_exposure_count_invalid")
        _require(tx["experiment_origin_reinjection_count"] == 0, "matched_stock_smoke_reinjection_detected")
        _require(tx["persistent_state_mutation"] is False, "matched_stock_smoke_persistent_mutation_detected")
        _require(len(trace["runtime_transform_records"]) == 1, "matched_stock_smoke_transform_record_count_invalid")
        record = trace["runtime_transform_records"][0]
        _require(record["turn"] == 9 and record["actor"] == "ops_lead", "matched_stock_smoke_delivery_boundary_invalid")
        _require(record["condition_id"] == condition, "matched_stock_smoke_condition_record_mismatch")
        _require(record["target_locator"] == envelope["target_locator"], "matched_stock_smoke_delivery_target_invalid")
        completed = {int(x["turn"]) for x in trace["model_calls"] if x.get("status") == "completed"}
        _require(9 in completed and 10 in completed, "matched_stock_smoke_t9_t10_coverage_invalid")
        _require(provider.t9 == 1 and provider.t10 == 0, "matched_stock_smoke_annotation_visibility_invalid")
        exposures[condition] += 1
        post_turns[condition] += sum(1 for t in completed if t >= 10)
        trace["r6d_matched_stock_condition"] = {
            "schema": "RB-R6D-MATCHED-STOCK-CONDITION-TRACE-v0.1",
            "design_hash": bundle["plan"]["design_hash"],
            "runtime_plan_hash": bundle["plan"]["plan_hash"],
            "manifest_hash": row["manifest_hash"],
            "triad_id": row["triad_id"],
            "replicate_index": row["replicate_index"],
            "execution_order": row["execution_order"],
            "condition_id": condition,
            "parent_state_hash": row["parent_state_hash"],
            "direct_response_turn": 9,
            "post_consumption_start_turn": 10,
            "provider_internal_state_replayed": False,
            "semantic_cpr_status": "NOT_ADJUDICATED",
        }
        trace["scientific_status"] = "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE"
        traces.append(trace)

    _require(stable_hash(bundle["source_parent_snapshot"]) == parent_hash_before, "matched_stock_smoke_parent_mutated")
    _require(len(traces) == 9, "matched_stock_smoke_trace_count_invalid")
    _require(all(exposures[c] == 3 for c in CONDITIONS), "matched_stock_smoke_condition_exposure_balance_invalid")
    _require(all(post_turns[c] >= 3 for c in CONDITIONS), "matched_stock_smoke_post_consumption_coverage_invalid")
    summary = {
        "schema": SMOKE_SCHEMA,
        "scientific_status": "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE",
        "design_hash": bundle["plan"]["design_hash"],
        "runtime_plan_hash": bundle["plan"]["plan_hash"],
        "trace_count": 9,
        "condition_trace_counts": {c: 3 for c in CONDITIONS},
        "direct_experiment_origin_exposure_counts": exposures,
        "post_consumption_turn_counts": post_turns,
        "source_parent_immutable": True,
        "provider_calls_are_real": False,
        "paid_api_called": False,
        "paid_evaluator_called": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "interpretation_boundary": "Deterministic runtime integration smoke only. Synthetic provider outputs are not scientific matched-stock robustness evidence.",
    }
    summary["summary_hash"] = stable_hash(summary)
    return traces, summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan-dir", required=True)
    ap.add_argument("--domain", default="arena/domains/ecommerce.json")
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    traces, summary = run_smoke(args.plan_dir, args.domain)
    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_matched_stock_runtime_smoke_dir")
    out.mkdir(parents=True)
    write_jsonl(out / "traces.jsonl", traces)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("R6D_MATCHED_STOCK_RUNTIME_SMOKE=PASS")
    print("TRACE_COUNT=9")
    print("S2_EXPOSURES=3")
    print("S3_EXPOSURES=3")
    print("S4_EXPOSURES=3")
    print("PAID_API_CALLED=NO")
    print("SUMMARY_HASH=" + summary["summary_hash"])


if __name__ == "__main__":
    main()
