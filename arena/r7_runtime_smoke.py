#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .alr_recovery import AuthorityLocalizedEnvelopeTransform
from .core import stable_hash
from .engine import run_arena_once
from .io_utils import load_json, load_jsonl, write_jsonl
from .one_shot_intervention import OneShotRuntimeViewTransform
from .persistent_field_intervention import PersistentFieldRuntimeViewTransform
from .prepare_r7_three_arm_plan import verify_r7_three_arm_plan

SMOKE_SCHEMA = "RB-R7-RUNTIME-SMOKE-v0.2"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def load_r7_plan_bundle(plan_dir: str | Path) -> dict:
    p = Path(plan_dir)
    bundle = {
        "plan": load_json(p / "r7_plan.json"),
        "source_parent_snapshot": load_json(p / "source_parent_snapshot.json"),
        "c3_recovery_checkpoint": load_json(p / "c3_recovery_checkpoint.json"),
        "c1_one_shot_envelope": load_json(p / "c1_one_shot_envelope.json"),
        "c2_persistent_field_envelope": load_json(p / "c2_persistent_field_envelope.json"),
        "c3_alr_binding": load_json(p / "c3_alr_binding.json"),
        "bounded_arena_config": load_json(p / "r7_bounded_arena_config.json"),
        "arm_manifests": load_jsonl(p / "arm_manifests.jsonl"),
        "execution_rows": load_jsonl(p / "execution_rows.jsonl"),
    }
    verify_r7_three_arm_plan(bundle)
    return bundle


class R7OfflineSmokeProvider:
    """Deterministic provider used only to exercise R7 runtime plumbing.

    It is not a model replay and its traces are never scientific evidence. The
    first C3 turn intentionally emits a J0-shaped `fact` write so the ALR action
    transform can be verified inside the real Arena execution loop.
    """

    def complete_agent(self, messages, metadata=None):
        metadata = metadata or {}
        actor = metadata.get("agent_id")
        turn = int(metadata.get("turn") or 0)
        if actor == "inventory" and turn == 8:
            envelope = {
                "decision_summary": "offline smoke: reproduce J0-shaped authority commit",
                "actions": [
                    {
                        "type": "write_state",
                        "key": "inventory_stockout_assessment_v1",
                        "value": {"offline_smoke": True, "turn": 8},
                        "status": "fact",
                        "basis": "offline engineering smoke only",
                    },
                    {
                        "type": "message",
                        "to": "ops_lead",
                        "content": "offline smoke continuation after authority commit",
                    },
                    {"type": "finalize", "answer": "offline smoke turn 8"},
                ],
            }
        elif actor == "ops_lead" and turn == 9:
            envelope = {
                "decision_summary": "offline smoke: keep one downstream turn pending",
                "actions": [
                    {"type": "message", "to": "ads", "content": "offline smoke downstream handoff"},
                    {"type": "finalize", "answer": "offline smoke turn 9"},
                ],
            }
        else:
            envelope = {
                "decision_summary": "offline smoke: quiesce",
                "actions": [{"type": "finalize", "answer": "offline smoke terminal"}],
            }
        return {
            "response_id": f"offline-smoke:{actor}:{turn}",
            "provider_response": {"offline_smoke": True},
            "finish_reason": "stop",
            "model": "offline-r7-smoke",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
            "transport_latency_ms": 0,
            "content": json.dumps(envelope, ensure_ascii=False),
        }


def _manifest_for_arm(bundle: dict, arm_id: str) -> dict:
    rows = [row for row in bundle["arm_manifests"] if row["replicate_index"] == 1 and row["arm_id"] == arm_id]
    _require(len(rows) == 1, f"r7_smoke_requires_one_replicate_manifest:{arm_id}")
    return rows[0]


def run_smoke(plan_dir: str | Path, domain_path: str | Path) -> tuple[list[dict], dict]:
    bundle = load_r7_plan_bundle(plan_dir)
    _require(bundle["plan"]["replicates"] >= 1, "r7_smoke_requires_replicate")
    domain = load_json(domain_path)
    config = copy.deepcopy(bundle["bounded_arena_config"])
    provider = R7OfflineSmokeProvider()

    parent_material_hash = stable_hash(bundle["source_parent_snapshot"])
    checkpoint_material_hash = stable_hash(bundle["c3_recovery_checkpoint"])
    traces: list[dict] = []
    arm_summaries: dict[str, dict] = {}

    for arm_id in ("C1_ONE_SHOT", "C2_PERSISTENT_FIELD", "C3_ALR"):
        manifest = _manifest_for_arm(bundle, arm_id)
        runtime_transform = None
        action_transform = None
        if arm_id == "C1_ONE_SHOT":
            start = bundle["source_parent_snapshot"]
            runtime_transform = OneShotRuntimeViewTransform(bundle["c1_one_shot_envelope"])
        elif arm_id == "C2_PERSISTENT_FIELD":
            start = bundle["source_parent_snapshot"]
            runtime_transform = PersistentFieldRuntimeViewTransform(bundle["c2_persistent_field_envelope"])
        else:
            start = bundle["c3_recovery_checkpoint"]
            alr = bundle["c3_alr_binding"]
            action_transform = AuthorityLocalizedEnvelopeTransform(
                target_actor=alr["target_actor"],
                target_turn=int(alr["target_reexecution_turn"]),
                state_key=alr["state_key"],
                from_status=alr["from_status"],
                to_status=alr["to_status"],
                jump_ref=alr["jump_ref"],
                semantic_payload_hash=alr["semantic_payload_hash"],
            )

        trace = run_arena_once(
            domain,
            config,
            provider,
            manifest["branch_id"],
            logical_seed=1,
            initial_state_snapshot=start,
            runtime_view_transform=runtime_transform,
            action_envelope_transform=action_transform,
        )
        trace["r7_smoke_arm_id"] = arm_id
        trace["r7_smoke_manifest_hash"] = manifest["manifest_hash"]
        trace["scientific_status"] = "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE"

        if arm_id == "C1_ONE_SHOT":
            runtime_transform.verify_finished()
            _require(len(trace["runtime_transform_records"]) == 1, "r7_smoke_c1_exposure_count_invalid")
            _require(not trace["action_transform_records"], "r7_smoke_c1_action_transform_forbidden")
            arm_summaries[arm_id] = runtime_transform.summary()
        elif arm_id == "C2_PERSISTENT_FIELD":
            runtime_transform.verify_finished(require_horizon_exhausted=False)
            _require(len(trace["runtime_transform_records"]) >= 2, "r7_smoke_c2_must_exercise_repeated_exposure")
            _require(not trace["action_transform_records"], "r7_smoke_c2_action_transform_forbidden")
            arm_summaries[arm_id] = runtime_transform.summary()
        else:
            action_transform.verify_finished()
            _require(len(trace["action_transform_records"]) == 1, "r7_smoke_c3_authority_transform_count_invalid")
            _require(not trace["runtime_transform_records"], "r7_smoke_c3_prompt_overlay_forbidden")
            turn8 = next(call for call in trace["model_calls"] if call["agent_id"] == "inventory" and call["turn"] == 8)
            raw_actions = turn8["parsed_envelope"]["actions"]
            applied_actions = turn8["applied_envelope"]["actions"]
            raw_target = [a for a in raw_actions if a.get("type") == "write_state" and a.get("key") == "inventory_stockout_assessment_v1"]
            applied_target = [a for a in applied_actions if a.get("type") == "write_state" and a.get("key") == "inventory_stockout_assessment_v1"]
            _require(len(raw_target) == len(applied_target) == 1, "r7_smoke_c3_target_action_missing")
            _require(raw_target[0]["status"] == "fact", "r7_smoke_c3_raw_authority_status_not_preserved")
            _require(applied_target[0]["status"] == "unconfirmed", "r7_smoke_c3_applied_authority_status_not_recovered")
            _require(
                trace["events"][32]["action_type"] == "write_state"
                and trace["events"][32]["shared_state_metadata_after"]["inventory_stockout_assessment_v1"]["status"] == "unconfirmed",
                "r7_smoke_c3_realized_state_did_not_use_recovered_authority_status",
            )
            revision = {
                "schema": "RB-R7-C3-REVISION-LINEAGE-v0.1",
                "common_reference_parent_state_hash": bundle["source_parent_snapshot"]["state_hash"],
                "recovery_checkpoint_state_hash": bundle["c3_recovery_checkpoint"]["state_hash"],
                "semantic_payload_hash": bundle["c3_alr_binding"]["semantic_payload_hash"],
                "reopened_source_event_range": bundle["c3_alr_binding"]["reopened_source_event_range"],
                "authority_transform_hashes": action_transform.summary()["transform_hashes"],
                "result_trace_hash": stable_hash(trace),
                "provider_internal_state_replayed": False,
            }
            revision["revision_hash"] = stable_hash(revision)
            trace["r7_revision_lineage"] = revision
            arm_summaries[arm_id] = {**action_transform.summary(), "revision_hash": revision["revision_hash"]}

        trace["r7_condition"] = {
            "schema": "RB-R7-CONDITION-TRACE-v0.1",
            "arm_id": arm_id,
            "triad_id": manifest["triad_id"],
            "replicate_index": manifest["replicate_index"],
            "execution_order": manifest["execution_order"],
            "manifest_hash": manifest["manifest_hash"],
            "condition_status": "OBSERVED",
            "common_reference_parent_state_hash": bundle["source_parent_snapshot"]["state_hash"],
            "branch_start_state_hash": start["state_hash"],
            "semantic_payload_hash": manifest["semantic_payload_hash"],
            "observation_horizon_id": manifest["observation_horizon_id"],
            "transform_summary": copy.deepcopy(arm_summaries[arm_id]),
            "provider_internal_state_replayed": False,
            "semantic_cpr_status": "NOT_ADJUDICATED",
            "terminal_outcome_is_primary": False,
        }
        traces.append(trace)

    _require(stable_hash(bundle["source_parent_snapshot"]) == parent_material_hash, "r7_smoke_mutated_common_parent")
    _require(stable_hash(bundle["c3_recovery_checkpoint"]) == checkpoint_material_hash, "r7_smoke_mutated_recovery_checkpoint")
    summary = {
        "schema": SMOKE_SCHEMA,
        "scientific_status": "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE",
        "plan_hash": bundle["plan"]["plan_hash"],
        "common_reference_parent_state_hash": bundle["source_parent_snapshot"]["state_hash"],
        "c3_recovery_checkpoint_state_hash": bundle["c3_recovery_checkpoint"]["state_hash"],
        "arm_run_statuses": {trace["r7_smoke_arm_id"]: trace["run_status"] for trace in traces},
        "arm_summaries": arm_summaries,
        "c1_direct_exposures": arm_summaries["C1_ONE_SHOT"]["direct_experiment_origin_exposure_count"],
        "c2_direct_exposures": arm_summaries["C2_PERSISTENT_FIELD"]["direct_experiment_origin_exposure_count"],
        "c2_reinjections": arm_summaries["C2_PERSISTENT_FIELD"]["experiment_origin_reinjection_count"],
        "c3_authority_transform_count": arm_summaries["C3_ALR"]["transform_count"],
        "source_snapshots_immutable": True,
        "provider_calls_are_real": False,
        "paid_api_called": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "interpretation_boundary": "Deterministic engine integration smoke only. Synthetic envelopes are not subject evidence and cannot support a steering/control claim.",
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
        raise ValueError("refusing_to_overwrite_r7_runtime_smoke_dir")
    out.mkdir(parents=True)
    write_jsonl(out / "traces.jsonl", traces)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("R7_RUNTIME_SMOKE=PASS")
    print("C1_DIRECT_EXPOSURES=" + str(summary["c1_direct_exposures"]))
    print("C2_DIRECT_EXPOSURES=" + str(summary["c2_direct_exposures"]))
    print("C2_REINJECTIONS=" + str(summary["c2_reinjections"]))
    print("C3_AUTHORITY_TRANSFORM_COUNT=" + str(summary["c3_authority_transform_count"]))
    print("PAID_API_CALLED=NO")
    print("SUMMARY_HASH=" + summary["summary_hash"])


if __name__ == "__main__":
    main()
