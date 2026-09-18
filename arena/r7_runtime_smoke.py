#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .core import stable_hash
from .engine import run_arena_once
from .io_utils import load_json, load_jsonl, write_jsonl
from .one_shot_intervention import OneShotRuntimeViewTransform
from .persistent_field_intervention import PersistentFieldRuntimeViewTransform
from .prepare_r7_three_arm_plan import verify_r7_three_arm_plan
from .r7_semantic_repair_runtime import verify_semantic_repair_trace

SMOKE_SCHEMA = "RB-R7-RUNTIME-SMOKE-v0.3"


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
        "semantic_repair_runtime_plan": load_json(p / "semantic_repair_runtime_plan.json"),
        "c3_repaired_parent_snapshot": load_json(p / "c3_repaired_parent_snapshot.json"),
        "c3_repair_application": load_json(p / "c3_repair_application.json"),
        "semantic_repair_packet": load_json(p / "semantic_repair_packet.json"),
        "semantic_lineage_package": load_json(p / "semantic_lineage_package.json"),
        "post_repair_watch_contract": load_json(p / "post_repair_watch_contract.json"),
        "lineage_completeness_gate": load_json(p / "lineage_completeness_gate.json"),
        "bounded_arena_config": load_json(p / "r7_bounded_arena_config.json"),
        "arm_manifests": load_jsonl(p / "arm_manifests.jsonl"),
        "execution_rows": load_jsonl(p / "execution_rows.jsonl"),
    }
    verify_r7_three_arm_plan(bundle)
    return bundle


class R7OfflineSmokeProvider:
    """Deterministic provider used only to exercise R7 runtime plumbing.

    It is not a model replay and its traces are never scientific evidence.
    C3 starts from the already repaired frozen post-J0 parent, so no synthetic
    J0 reproduction is required.
    """

    def complete_agent(self, messages, metadata=None):
        metadata = metadata or {}
        actor = metadata.get("agent_id")
        turn = int(metadata.get("turn") or 0)
        if actor == "ops_lead" and turn == 9:
            envelope = {
                "decision_summary": "offline smoke: continue from repaired post-J0 parent",
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
    repaired_parent_material_hash = stable_hash(bundle["c3_repaired_parent_snapshot"])
    traces: list[dict] = []
    arm_summaries: dict[str, dict] = {}

    for arm_id in ("C1_ONE_SHOT", "C2_PERSISTENT_FIELD", "C3_ALR"):
        manifest = _manifest_for_arm(bundle, arm_id)
        runtime_transform = None
        if arm_id == "C1_ONE_SHOT":
            start = bundle["source_parent_snapshot"]
            runtime_transform = OneShotRuntimeViewTransform(bundle["c1_one_shot_envelope"])
        elif arm_id == "C2_PERSISTENT_FIELD":
            start = bundle["source_parent_snapshot"]
            runtime_transform = PersistentFieldRuntimeViewTransform(bundle["c2_persistent_field_envelope"])
        else:
            start = bundle["c3_repaired_parent_snapshot"]

        trace = run_arena_once(
            domain,
            config,
            provider,
            manifest["branch_id"],
            logical_seed=1,
            initial_state_snapshot=start,
            runtime_view_transform=runtime_transform,
            action_envelope_transform=None,
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
            _require(len(trace["runtime_transform_records"]) >= 1, "r7_smoke_c2_must_exercise_exposure")
            _require(not trace["action_transform_records"], "r7_smoke_c2_action_transform_forbidden")
            arm_summaries[arm_id] = runtime_transform.summary()
        else:
            _require(not trace["runtime_transform_records"], "r7_smoke_c3_prompt_overlay_forbidden")
            _require(not trace["action_transform_records"], "r7_smoke_c3_action_transform_forbidden")
            _require(
                start["shared_state"] == bundle["source_parent_snapshot"]["shared_state"],
                "r7_smoke_c3_target_value_must_be_preserved",
            )
            key = bundle["semantic_repair_runtime_plan"]["target_state_key"]
            _require(
                start["shared_state_metadata"][key]["status"]
                == bundle["semantic_repair_runtime_plan"]["authority_to_status"],
                "r7_smoke_c3_repaired_authority_status_missing",
            )
            arm_summaries[arm_id] = {
                "repair_application_count": 1,
                "repair_application_hash": bundle["c3_repair_application"]["repair_application_hash"],
                "repaired_parent_state_hash": bundle["c3_repaired_parent_snapshot"]["state_hash"],
                "semantic_repair_runtime_plan_hash": bundle["semantic_repair_runtime_plan"]["plan_hash"],
            }

        trace["r7_condition"] = {
            "schema": "RB-R7-CONDITION-TRACE-v0.2",
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
            "mechanism_summary": copy.deepcopy(arm_summaries[arm_id]),
            "provider_internal_state_replayed": False,
            "semantic_cpr_status": "NOT_ADJUDICATED",
            "terminal_outcome_is_primary": False,
        }

        if arm_id == "C3_ALR":
            repair_verification = verify_semantic_repair_trace(
                trace=trace,
                plan=bundle["semantic_repair_runtime_plan"],
                repair_application=bundle["c3_repair_application"],
            )
            revision = {
                "schema": "RB-R7-C3-REVISION-LINEAGE-v0.2",
                "common_reference_parent_state_hash": bundle["source_parent_snapshot"]["state_hash"],
                "repaired_parent_state_hash": bundle["c3_repaired_parent_snapshot"]["state_hash"],
                "repair_application_hash": bundle["c3_repair_application"]["repair_application_hash"],
                "semantic_repair_runtime_plan_hash": bundle["semantic_repair_runtime_plan"]["plan_hash"],
                "result_trace_hash_before_revision_record": stable_hash(trace),
                "provider_internal_state_replayed": False,
            }
            revision["revision_hash"] = stable_hash(revision)
            trace["r7_revision_lineage"] = revision
            trace["r7_semantic_repair_runtime_plan"] = bundle["semantic_repair_runtime_plan"]
            trace["r7_repair_application"] = bundle["c3_repair_application"]
            trace["r7_semantic_repair_verification"] = repair_verification
            trace["r7_condition"]["semantic_repair_packet_hash"] = bundle["semantic_repair_runtime_plan"]["packet_hash"]
            trace["r7_condition"]["semantic_repair_verification_hash"] = repair_verification["verification_hash"]
            trace["r7_condition"]["old_lineage_reentry_detected"] = repair_verification["old_lineage_reentry_detected"]
            trace["r7_condition"]["preserved_unrelated_structure"] = repair_verification["preserved_unrelated_structure"]
            arm_summaries[arm_id].update({
                "revision_hash": revision["revision_hash"],
                "semantic_repair_verification_hash": repair_verification["verification_hash"],
                "old_lineage_reentry_detected": repair_verification["old_lineage_reentry_detected"],
                "preserved_unrelated_structure": repair_verification["preserved_unrelated_structure"],
            })

        traces.append(trace)

    _require(stable_hash(bundle["source_parent_snapshot"]) == parent_material_hash, "r7_smoke_mutated_common_parent")
    _require(stable_hash(bundle["c3_recovery_checkpoint"]) == checkpoint_material_hash, "r7_smoke_mutated_recovery_checkpoint")
    _require(stable_hash(bundle["c3_repaired_parent_snapshot"]) == repaired_parent_material_hash, "r7_smoke_mutated_repaired_parent")
    summary = {
        "schema": SMOKE_SCHEMA,
        "scientific_status": "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE",
        "plan_hash": bundle["plan"]["plan_hash"],
        "common_reference_parent_state_hash": bundle["source_parent_snapshot"]["state_hash"],
        "c3_recovery_checkpoint_state_hash": bundle["c3_recovery_checkpoint"]["state_hash"],
        "c3_repaired_parent_state_hash": bundle["c3_repaired_parent_snapshot"]["state_hash"],
        "arm_run_statuses": {trace["r7_smoke_arm_id"]: trace["run_status"] for trace in traces},
        "arm_summaries": arm_summaries,
        "c1_direct_exposures": arm_summaries["C1_ONE_SHOT"]["direct_experiment_origin_exposure_count"],
        "c2_direct_exposures": arm_summaries["C2_PERSISTENT_FIELD"]["direct_experiment_origin_exposure_count"],
        "c2_reinjections": arm_summaries["C2_PERSISTENT_FIELD"]["experiment_origin_reinjection_count"],
        "c3_branch_state_repair_count": arm_summaries["C3_ALR"]["repair_application_count"],
        "c3_semantic_repair_packet_consumed": True,
        "c3_old_lineage_reentry_detected": arm_summaries["C3_ALR"]["old_lineage_reentry_detected"],
        "c3_preserved_unrelated_structure": arm_summaries["C3_ALR"]["preserved_unrelated_structure"],
        "source_snapshots_immutable": True,
        "provider_calls_are_real": False,
        "paid_api_called": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "interpretation_boundary": "Deterministic engine integration smoke only. Synthetic envelopes are not subject evidence and cannot support a recovery/control claim.",
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
    print("C3_BRANCH_STATE_REPAIR_COUNT=" + str(summary["c3_branch_state_repair_count"]))
    print("C3_SEMANTIC_REPAIR_PACKET_CONSUMED=YES")
    print("C3_OLD_LINEAGE_REENTRY_DETECTED=" + ("YES" if summary["c3_old_lineage_reentry_detected"] else "NO"))
    print("C3_PRESERVED_UNRELATED_STRUCTURE=" + ("YES" if summary["c3_preserved_unrelated_structure"] else "NO"))
    print("PAID_API_CALLED=NO")
    print("SUMMARY_HASH=" + summary["summary_hash"])


if __name__ == "__main__":
    main()
