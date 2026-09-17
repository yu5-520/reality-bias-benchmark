#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .core import stable_hash
from .engine import run_arena_once
from .io_utils import load_json, write_jsonl
from .prepare_r6d_specificity_plan import load_r6d_runtime_plan
from .r5r6_specificity_atomic_v0_2 import S0, S1, S2, AtomicEpistemicAnnotationTransform

SMOKE_SCHEMA = "RB-R6D-SPECIFICITY-RUNTIME-SMOKE-v0.1"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


class R6DOfflineSmokeProvider:
    """Deterministic provider for plumbing validation only.

    It validates that the expected annotation is visible on T9 and absent on T10.
    Its outputs are synthetic engineering evidence and must never be treated as
    scientific S-arm subject evidence.
    """

    def __init__(self, *, condition_id: str, expected_target: str | None):
        self.condition_id = condition_id
        self.expected_target = expected_target
        self.observed_t9_annotation_count = 0
        self.observed_t10_annotation_count = 0

    def complete_agent(self, messages, metadata=None):
        metadata = metadata or {}
        actor = metadata.get("agent_id")
        turn = int(metadata.get("turn") or 0)
        payload = json.loads(messages[-1]["content"])
        annotations = list(payload.get("epistemic_annotations") or [])

        if turn == 9:
            if self.condition_id == S0:
                _require(not annotations, "r6d_smoke_s0_must_have_no_annotation_t9")
            else:
                _require(len(annotations) == 1, "r6d_smoke_treated_must_have_one_annotation_t9")
                _require(annotations[0].get("target_locator") == self.expected_target, "r6d_smoke_target_locator_mismatch")
                _require(annotations[0].get("epistemic_status") == "unconfirmed", "r6d_smoke_status_mismatch")
            self.observed_t9_annotation_count = len(annotations)
            envelope = {
                "decision_summary": "offline R6-D smoke: create a downstream handoff",
                "actions": [
                    {"type": "message", "to": "ads", "content": "offline R6-D smoke downstream handoff"},
                    {"type": "finalize", "answer": "offline R6-D smoke T9"},
                ],
            }
        elif turn == 10:
            _require(not annotations, "r6d_smoke_annotation_must_be_consumed_before_t10")
            self.observed_t10_annotation_count = len(annotations)
            envelope = {
                "decision_summary": "offline R6-D smoke: quiesce after one post-consumption turn",
                "actions": [{"type": "finalize", "answer": "offline R6-D smoke T10"}],
            }
        else:
            envelope = {
                "decision_summary": "offline R6-D smoke: quiesce",
                "actions": [{"type": "finalize", "answer": "offline R6-D smoke terminal"}],
            }

        return {
            "response_id": f"offline-r6d-smoke:{self.condition_id}:{actor}:{turn}",
            "provider_response": {"offline_smoke": True, "condition_id": self.condition_id},
            "finish_reason": "stop",
            "model": "offline-r6d-smoke",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
            "transport_latency_ms": 0,
            "content": json.dumps(envelope, ensure_ascii=False),
        }


def _transform_for(row: dict, bundle: dict):
    cond = row["condition_id"]
    if cond == S0:
        return None, None
    envelope = bundle["s1_envelope"] if cond == S1 else bundle["s2_envelope"]
    return AtomicEpistemicAnnotationTransform(envelope), envelope["target_locator"]


def run_smoke(plan_dir: str | Path, domain_path: str | Path) -> tuple[list[dict], dict]:
    bundle = load_r6d_runtime_plan(plan_dir)
    domain = load_json(domain_path)
    config = copy.deepcopy(bundle["bounded_arena_config"])
    parent_hash_before = stable_hash(bundle["source_parent_snapshot"])

    traces: list[dict] = []
    condition_exposure_counts = {S0: 0, S1: 0, S2: 0}
    post_consumption_turn_counts = {S0: 0, S1: 0, S2: 0}

    rows = sorted(bundle["execution_rows"], key=lambda x: (x["replicate_index"], x["execution_order"]))
    for row in rows:
        transform, target = _transform_for(row, bundle)
        provider = R6DOfflineSmokeProvider(condition_id=row["condition_id"], expected_target=target)
        trace = run_arena_once(
            domain,
            config,
            provider,
            row["run_id"],
            logical_seed=row["logical_seed"],
            initial_state_snapshot=bundle["source_parent_snapshot"],
            runtime_view_transform=transform,
        )
        trace["r6d_condition"] = {
            "schema": "RB-R6D-SPECIFICITY-CONDITION-TRACE-v0.1",
            "design_hash": bundle["plan"]["design_hash"],
            "runtime_plan_hash": bundle["plan"]["plan_hash"],
            "manifest_hash": row["manifest_hash"],
            "triad_id": row["triad_id"],
            "replicate_index": row["replicate_index"],
            "execution_order": row["execution_order"],
            "condition_id": row["condition_id"],
            "parent_state_hash": row["parent_state_hash"],
            "direct_response_turn": 9,
            "post_consumption_start_turn": 10,
            "provider_internal_state_replayed": False,
            "semantic_cpr_status": "NOT_ADJUDICATED",
        }
        trace["scientific_status"] = "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE"

        if transform is None:
            _require(not trace["runtime_transform_records"], "r6d_smoke_s0_transform_forbidden")
            exposure_count = 0
        else:
            transform.verify_finished()
            summary = transform.summary()
            exposure_count = summary["direct_experiment_origin_exposure_count"]
            _require(exposure_count == 1, "r6d_smoke_treated_exposure_count_invalid")
            _require(summary["experiment_origin_reinjection_count"] == 0, "r6d_smoke_reinjection_detected")
            _require(summary["persistent_state_mutation"] is False, "r6d_smoke_persistent_mutation_detected")
            _require(len(trace["runtime_transform_records"]) == 1, "r6d_smoke_runtime_record_count_invalid")
            record = trace["runtime_transform_records"][0]
            _require(record["turn"] == 9 and record["actor"] == "ops_lead", "r6d_smoke_delivery_boundary_invalid")
            _require(record["target_locator"] == target, "r6d_smoke_delivery_target_invalid")

        condition_exposure_counts[row["condition_id"]] += exposure_count
        completed_turns = {int(x["turn"]) for x in trace["model_calls"] if x.get("status") == "completed"}
        _require(9 in completed_turns, "r6d_smoke_missing_direct_response_turn")
        _require(10 in completed_turns, "r6d_smoke_missing_post_consumption_turn")
        post_consumption_turn_counts[row["condition_id"]] += sum(1 for t in completed_turns if t >= 10)
        _require(provider.observed_t10_annotation_count == 0, "r6d_smoke_post_consumption_annotation_leak")
        traces.append(trace)

    _require(stable_hash(bundle["source_parent_snapshot"]) == parent_hash_before, "r6d_smoke_source_parent_mutated")
    _require(len(traces) == 9, "r6d_smoke_trace_count_invalid")
    _require(condition_exposure_counts[S0] == 0, "r6d_smoke_s0_exposure_total_invalid")
    _require(condition_exposure_counts[S1] == 3, "r6d_smoke_s1_exposure_total_invalid")
    _require(condition_exposure_counts[S2] == 3, "r6d_smoke_s2_exposure_total_invalid")
    _require(all(v >= 3 for v in post_consumption_turn_counts.values()), "r6d_smoke_post_consumption_coverage_invalid")

    summary = {
        "schema": SMOKE_SCHEMA,
        "scientific_status": "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE",
        "design_hash": bundle["plan"]["design_hash"],
        "runtime_plan_hash": bundle["plan"]["plan_hash"],
        "trace_count": len(traces),
        "condition_trace_counts": {S0: 3, S1: 3, S2: 3},
        "direct_experiment_origin_exposure_counts": condition_exposure_counts,
        "post_consumption_turn_counts": post_consumption_turn_counts,
        "source_parent_immutable": True,
        "provider_calls_are_real": False,
        "paid_api_called": False,
        "paid_evaluator_called": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "interpretation_boundary": "Deterministic runtime integration smoke only. Synthetic provider outputs are not scientific specificity evidence.",
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
        raise ValueError("refusing_to_overwrite_r6d_runtime_smoke_dir")
    out.mkdir(parents=True)
    write_jsonl(out / "traces.jsonl", traces)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("R6D_RUNTIME_SMOKE=PASS")
    print("TRACE_COUNT=9")
    print("S0_EXPOSURES=0")
    print("S1_EXPOSURES=3")
    print("S2_EXPOSURES=3")
    print("POST_CONSUMPTION_TURNS_PRESENT=YES")
    print("PAID_API_CALLED=NO")
    print("SUMMARY_HASH=" + summary["summary_hash"])


if __name__ == "__main__":
    main()
