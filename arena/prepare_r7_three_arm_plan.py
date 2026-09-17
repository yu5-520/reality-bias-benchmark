#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Mapping

from .branch_plan_one_shot import verify_one_shot_branch_plan
from .core import stable_hash
from .experimental_control import verify_state_snapshot
from .io_utils import load_json, load_jsonl, write_jsonl
from .one_shot_intervention import verify_one_shot_envelope
from .persistent_field_intervention import build_persistent_field_envelope, verify_persistent_field_envelope

PLAN_SCHEMA = "RB-R7-THREE-ARM-EXECUTION-PLAN-v0.2"
ARM_MANIFEST_SCHEMA = "RB-R7-ARM-MANIFEST-v0.2"
ALR_BINDING_SCHEMA = "RB-R7-ALR-RECOVERY-BINDING-v0.2"
ARM_IDS = ("C1_ONE_SHOT", "C2_PERSISTENT_FIELD", "C3_ALR")


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _hash_without(row: Mapping[str, Any], key: str) -> str:
    material = copy.deepcopy(dict(row))
    material.pop(key, None)
    return stable_hash(material)


def _write_json(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(row), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_r5_plan_bundle(plan_dir: str | Path) -> dict[str, Any]:
    p = Path(plan_dir)
    bundle = {
        "plan": load_json(p / "branch_plan.json"),
        "parent_snapshot": load_json(p / "parent_snapshot.json"),
        "one_shot_envelope": load_json(p / "one_shot_intervention_envelope.json"),
        "branch_rows": load_jsonl(p / "branch_execution_manifest.jsonl"),
        "branch_manifests": load_jsonl(p / "branch_manifests.jsonl"),
    }
    verify_one_shot_branch_plan(bundle)
    verify_state_snapshot(bundle["parent_snapshot"])
    verify_one_shot_envelope(bundle["one_shot_envelope"])
    return bundle


def load_recovery_checkpoint(snapshots_path: str | Path, protocol: Mapping[str, Any]) -> dict[str, Any]:
    checkpoint_contract = protocol["recovery_checkpoint"]
    rows = load_jsonl(snapshots_path)
    matches = [row for row in rows if row.get("anchor_ref") == checkpoint_contract["anchor_ref"]]
    _require(len(matches) == 1, "r7_recovery_checkpoint_anchor_not_unique")
    checkpoint = matches[0]
    verify_state_snapshot(checkpoint)
    _require(checkpoint["state_hash"] == checkpoint_contract["state_hash"], "r7_recovery_checkpoint_hash_mismatch")
    _require(checkpoint["turns"] == checkpoint_contract["turns"], "r7_recovery_checkpoint_turn_mismatch")
    _require(len(checkpoint.get("events") or []) == checkpoint_contract["event_count"], "r7_recovery_checkpoint_event_count_mismatch")
    _require(checkpoint.get("queue") and checkpoint["queue"][0] == checkpoint_contract["queue_head"], "r7_recovery_checkpoint_queue_head_mismatch")
    return checkpoint


def _semantic_payload_hash(protocol: Mapping[str, Any]) -> str:
    payload = protocol["semantic_payload"]
    return stable_hash({
        "target_path": payload["target_path"],
        "from": payload["from"],
        "to": payload["to"],
        "semantic_meaning": "selected J0 authority/status is downgraded from factual certainty to unconfirmed",
    })


def validate_source_binding(protocol: Mapping[str, Any], r5: Mapping[str, Any], checkpoint: Mapping[str, Any]) -> dict[str, Any]:
    binding = protocol["frozen_parent"]
    jump = protocol["jump"]
    payload = protocol["semantic_payload"]
    horizon = protocol["matched_horizon"]
    source_plan = r5["plan"]
    parent = r5["parent_snapshot"]
    envelope = r5["one_shot_envelope"]

    _require(source_plan.get("plan_hash") == binding["source_plan_hash"], "r7_source_plan_hash_mismatch")
    _require(parent.get("state_hash") == binding["parent_state_hash"], "r7_parent_state_hash_mismatch")
    _require(source_plan.get("code_identity", {}).get("branch_execution_commit") == binding.get("code_sha"), "r7_source_execution_code_sha_mismatch")
    _require(envelope.get("source_event_index") == jump["source_event_index"], "r7_jump_event_index_mismatch")
    _require(envelope.get("state_key") == jump["state_key"], "r7_jump_state_key_mismatch")
    _require(envelope.get("from_status") == payload["from"], "r7_payload_from_status_mismatch")
    _require(envelope.get("to_status") == payload["to"], "r7_payload_to_status_mismatch")
    _require(parent.get("shared_state_metadata", {}).get(jump["state_key"], {}).get("status") == payload["from"], "r7_parent_jump_status_mismatch")
    _require(parent.get("terminated") is False and parent.get("queue"), "r7_parent_snapshot_not_resumable")
    _require(checkpoint.get("terminated") is False and checkpoint.get("queue"), "r7_recovery_checkpoint_not_resumable")
    _require(checkpoint["turns"] + 1 == parent["turns"], "r7_recovery_checkpoint_must_be_one_turn_before_common_parent")
    _require(len(checkpoint["events"]) == jump["source_event_index"], "r7_recovery_checkpoint_must_stop_before_j0_event")
    _require(len(parent["events"]) > len(checkpoint["events"]), "r7_common_parent_must_contain_j0_turn")
    _require(checkpoint["queue"][0] == jump["actor"], "r7_recovery_checkpoint_must_resume_j0_actor")
    previous_status = checkpoint.get("shared_state_metadata", {}).get(jump["state_key"], {}).get("status")
    _require(previous_status != payload["from"], "r7_checkpoint_already_contains_target_fact_status")

    turn_cap = int(horizon["post_jump_turn_cap"])
    return {
        "source_r5_plan_hash": source_plan["plan_hash"],
        "source_parent_state_hash": parent["state_hash"],
        "source_recovery_checkpoint_hash": checkpoint["state_hash"],
        "source_one_shot_envelope_hash": envelope["envelope_hash"],
        "source_branch_execution_commit": source_plan.get("code_identity", {}).get("branch_execution_commit"),
        "source_measurement_binding": copy.deepcopy(source_plan.get("source_measurement_binding") or {}),
        "common_reference_parent_turn": int(parent["turns"]),
        "common_reference_parent_event_count": len(parent.get("events") or []),
        "recovery_checkpoint_turn": int(checkpoint["turns"]),
        "recovery_checkpoint_event_count": len(checkpoint.get("events") or []),
        "reopened_source_event_range": [len(checkpoint["events"]), len(parent["events"]) - 1],
        "matched_horizon_id": horizon["horizon_id"],
        "post_jump_turn_cap": turn_cap,
        "absolute_turn_cap": int(parent["turns"]) + turn_cap,
        "provider_internal_state_replayed": False,
    }


def _build_bounded_arena_config(source_plan: Mapping[str, Any], parent: Mapping[str, Any], protocol: Mapping[str, Any]) -> dict[str, Any]:
    arena_path = source_plan.get("config_identity", {}).get("arena_config_path")
    _require(isinstance(arena_path, str) and arena_path, "r7_source_arena_config_path_missing")
    source = load_json(arena_path)
    out = copy.deepcopy(source)
    absolute_turn_cap = int(parent["turns"]) + int(protocol["matched_horizon"]["post_jump_turn_cap"])
    _require(int(source["max_turns"]) >= absolute_turn_cap, "r7_common_horizon_exceeds_source_arena_turn_budget")
    out["max_turns"] = absolute_turn_cap
    out["r7_observation_horizon"] = {
        "horizon_id": protocol["matched_horizon"]["horizon_id"],
        "common_reference_parent_turn": int(parent["turns"]),
        "post_jump_turn_cap": int(protocol["matched_horizon"]["post_jump_turn_cap"]),
        "absolute_turn_cap": absolute_turn_cap,
        "termination_policy": protocol["matched_horizon"]["termination_policy"],
        "early_termination_policy": protocol["matched_horizon"]["early_termination_policy"],
    }
    return out


def build_r7_three_arm_plan(*, protocol: Mapping[str, Any], r5: Mapping[str, Any], checkpoint: Mapping[str, Any], replicates: int, plan_code_sha: str) -> dict[str, Any]:
    _require(isinstance(replicates, int) and replicates >= 1, "r7_positive_replicates_required")
    source_binding = validate_source_binding(protocol, r5, checkpoint)
    parent = copy.deepcopy(r5["parent_snapshot"])
    checkpoint = copy.deepcopy(checkpoint)
    one_shot = copy.deepcopy(r5["one_shot_envelope"])
    semantic_hash = _semantic_payload_hash(protocol)
    horizon = protocol["matched_horizon"]

    persistent = build_persistent_field_envelope(
        target_jump_ref=one_shot["target_jump_ref"],
        target_candidate_id=one_shot["target_candidate_id"],
        state_key=one_shot["state_key"],
        source_event_index=one_shot["source_event_index"],
        from_status=one_shot["from_status"],
        to_status=one_shot["to_status"],
        max_direct_exposures=int(horizon["post_jump_turn_cap"]),
    )
    verify_persistent_field_envelope(persistent)

    bounded_arena_config = _build_bounded_arena_config(r5["plan"], parent, protocol)
    bounded_config_hash = stable_hash(bounded_arena_config)
    reopened_range = source_binding["reopened_source_event_range"]
    alr_binding = {
        "schema": ALR_BINDING_SCHEMA,
        "version": "0.2",
        "common_reference_parent_state_hash": parent["state_hash"],
        "recovery_checkpoint_state_hash": checkpoint["state_hash"],
        "recovery_checkpoint_anchor_ref": checkpoint["anchor_ref"],
        "rollback_turn_distance": parent["turns"] - checkpoint["turns"],
        "preserved_prefix_event_count": len(checkpoint["events"]),
        "reopened_source_event_range": reopened_range,
        "reopened_source_event_count": reopened_range[1] - reopened_range[0] + 1,
        "jump_ref": one_shot["target_jump_ref"],
        "jump_source_event_index": one_shot["source_event_index"],
        "target_actor": protocol["jump"]["actor"],
        "target_reexecution_turn": checkpoint["turns"] + 1,
        "state_key": one_shot["state_key"],
        "from_status": one_shot["from_status"],
        "to_status": one_shot["to_status"],
        "semantic_payload_hash": semantic_hash,
        "authority_class": "I",
        "recovery_operator": "ROLLBACK_ONE_AUTHORITY_ANCESTOR_TURN_THEN_TRANSFORM_TARGET_WRITE_STATE_STATUS_ONCE",
        "common_reference_parent_mutated": False,
        "provider_internal_state_replayed": False,
        "active_recovery_transform_status": "READY",
        "revision_lineage_required": True,
        "note": "C3 re-executes the J0-producing turn from the exact source checkpoint. Provider hidden state is not replayed; only the targeted authority-bearing write_state.status commit is transformed fact→unconfirmed, and new descendants are observed prospectively.",
    }
    alr_binding["binding_hash"] = _hash_without(alr_binding, "binding_hash")

    manifests: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    rotations = [ARM_IDS, ("C2_PERSISTENT_FIELD", "C3_ALR", "C1_ONE_SHOT"), ("C3_ALR", "C1_ONE_SHOT", "C2_PERSISTENT_FIELD")]
    for replicate in range(1, replicates + 1):
        order = rotations[(replicate - 1) % len(rotations)]
        triad_id = f"r7:{parent['run_id']}:triad:{replicate:04d}"
        for execution_order, arm_id in enumerate(order, 1):
            branch_id = f"{triad_id}:{arm_id.lower()}"
            if arm_id == "C1_ONE_SHOT":
                start_hash = parent["state_hash"]
                binding_hash = one_shot["envelope_hash"]
                mechanism = "ONE_SHOT_RUNTIME_VIEW_OVERLAY"
            elif arm_id == "C2_PERSISTENT_FIELD":
                start_hash = parent["state_hash"]
                binding_hash = persistent["envelope_hash"]
                mechanism = "PERSISTENT_RUNTIME_VIEW_OVERLAY"
            else:
                start_hash = checkpoint["state_hash"]
                binding_hash = alr_binding["binding_hash"]
                mechanism = "ALR_ROLLBACK_REEXECUTION_AUTHORITY_TRANSFORM"
            manifest = {
                "schema": ARM_MANIFEST_SCHEMA,
                "version": "0.2",
                "branch_id": branch_id,
                "triad_id": triad_id,
                "replicate_index": replicate,
                "execution_order": execution_order,
                "arm_id": arm_id,
                "mechanism": mechanism,
                "common_reference_parent_state_hash": parent["state_hash"],
                "branch_start_state_hash": start_hash,
                "branch_start_is_common_parent": start_hash == parent["state_hash"],
                "jump_ref": one_shot["target_jump_ref"],
                "jump_source_event_index": one_shot["source_event_index"],
                "semantic_payload_hash": semantic_hash,
                "observation_horizon_id": horizon["horizon_id"],
                "post_jump_turn_cap": int(horizon["post_jump_turn_cap"]),
                "absolute_turn_cap": int(parent["turns"]) + int(horizon["post_jump_turn_cap"]),
                "bounded_arena_config_hash": bounded_config_hash,
                "intervention_binding_hash": binding_hash,
                "execution_readiness": "RUNTIME_MECHANISM_READY",
                "provider_internal_state_replayed": False,
                "automatic_paid_evaluator": False,
            }
            manifest["manifest_hash"] = _hash_without(manifest, "manifest_hash")
            manifests.append(manifest)
            rows.append({
                "run_id": branch_id,
                "triad_id": triad_id,
                "replicate_index": replicate,
                "execution_order": execution_order,
                "arm_id": arm_id,
                "manifest_hash": manifest["manifest_hash"],
                "execution_readiness": manifest["execution_readiness"],
            })

    plan = {
        "schema": PLAN_SCHEMA,
        "version": "0.2",
        "protocol_id": protocol["protocol_id"],
        "phase": "R7_EXACT_SOURCE_BOUND_THREE_ARM_PREPARED_ONLY",
        "scientific_status": "PREPARED_NOT_EXECUTED",
        "source_binding": source_binding,
        "semantic_payload": copy.deepcopy(protocol["semantic_payload"]),
        "semantic_payload_hash": semantic_hash,
        "matched_horizon": copy.deepcopy(horizon),
        "measurement_schema": protocol["measurement_schema"],
        "bounded_arena_config_hash": bounded_config_hash,
        "replicates": replicates,
        "arm_ids": list(ARM_IDS),
        "branch_row_count": len(rows),
        "manifest_hashes": [row["manifest_hash"] for row in manifests],
        "condition_isolation": {
            "C1": "same post-J0 parent; one prompt-visible status exposure then free continuation",
            "C2": "same post-J0 parent; same status re-exposed on each eligible downstream turn within common horizon",
            "C3": "same J0/common reference parent; rollback one source turn to exact pre-J0 checkpoint, re-execute that turn, transform only the targeted authority-bearing write status once, then observe new descendants",
        },
        "c1_one_shot_envelope_hash": one_shot["envelope_hash"],
        "c2_persistent_field_envelope_hash": persistent["envelope_hash"],
        "c3_alr_binding_hash": alr_binding["binding_hash"],
        "code_identity": {
            "source_r5_branch_execution_commit": r5["plan"].get("code_identity", {}).get("branch_execution_commit"),
            "r7_plan_code_sha": plan_code_sha,
        },
        "provider_internal_state_replayed": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "paid_subject_authorization_status": "NOT_AUTHORIZED",
        "automatic_paid_evaluator": False,
        "real_three_arm_runtime_mechanisms_ready": True,
        "real_subject_execution_authorized": False,
    }
    plan["plan_hash"] = _hash_without(plan, "plan_hash")
    return {
        "plan": plan,
        "source_parent_snapshot": parent,
        "c3_recovery_checkpoint": checkpoint,
        "c1_one_shot_envelope": one_shot,
        "c2_persistent_field_envelope": persistent,
        "c3_alr_binding": alr_binding,
        "bounded_arena_config": bounded_arena_config,
        "arm_manifests": manifests,
        "execution_rows": rows,
    }


def verify_r7_three_arm_plan(bundle: Mapping[str, Any]) -> bool:
    plan = bundle["plan"]
    parent = bundle["source_parent_snapshot"]
    checkpoint = bundle["c3_recovery_checkpoint"]
    verify_state_snapshot(parent)
    verify_state_snapshot(checkpoint)
    verify_one_shot_envelope(bundle["c1_one_shot_envelope"])
    verify_persistent_field_envelope(bundle["c2_persistent_field_envelope"])
    _require(plan.get("schema") == PLAN_SCHEMA, "r7_plan_schema_invalid")
    _require(plan.get("plan_hash") == _hash_without(plan, "plan_hash"), "r7_plan_hash_mismatch")
    _require(plan.get("source_binding", {}).get("source_parent_state_hash") == parent["state_hash"], "r7_plan_parent_binding_mismatch")
    _require(plan.get("source_binding", {}).get("source_recovery_checkpoint_hash") == checkpoint["state_hash"], "r7_plan_checkpoint_binding_mismatch")
    _require(plan.get("paid_subject_authorization_status") == "NOT_AUTHORIZED", "r7_plan_must_not_self_authorize")
    _require(plan.get("automatic_paid_evaluator") is False, "r7_plan_paid_evaluator_forbidden")
    _require(plan.get("semantic_cpr_status") == "NOT_ADJUDICATED", "r7_plan_semantic_status_invalid")
    _require(plan.get("real_three_arm_runtime_mechanisms_ready") is True, "r7_runtime_mechanisms_not_ready")
    _require(plan.get("real_subject_execution_authorized") is False, "r7_plan_must_not_self_authorize_subject_run")
    manifests = list(bundle["arm_manifests"])
    rows = list(bundle["execution_rows"])
    _require(len(manifests) == len(rows) == plan["branch_row_count"] == plan["replicates"] * 3, "r7_plan_row_count_mismatch")
    _require({m["arm_id"] for m in manifests} == set(ARM_IDS), "r7_plan_missing_arm")
    _require({m["common_reference_parent_state_hash"] for m in manifests} == {parent["state_hash"]}, "r7_reference_parent_not_matched")
    _require({m["semantic_payload_hash"] for m in manifests} == {plan["semantic_payload_hash"]}, "r7_semantic_payload_not_matched")
    _require({m["observation_horizon_id"] for m in manifests} == {plan["matched_horizon"]["horizon_id"]}, "r7_horizon_not_matched")
    c3 = [m for m in manifests if m["arm_id"] == "C3_ALR"]
    _require(c3 and all(m["branch_start_state_hash"] == checkpoint["state_hash"] for m in c3), "r7_c3_checkpoint_start_mismatch")
    _require(all(m["execution_readiness"] == "RUNTIME_MECHANISM_READY" for m in manifests), "r7_runtime_readiness_mismatch")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", default="configs/r7/r7_three_arm_fixture.example.json")
    ap.add_argument("--r5-plan-dir", required=True)
    ap.add_argument("--source-snapshots", required=True)
    ap.add_argument("--replicates", type=int, default=1)
    ap.add_argument("--plan-code-sha", default="LOCAL_OR_UNRECORDED")
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    protocol = load_json(args.protocol)
    r5 = load_r5_plan_bundle(args.r5_plan_dir)
    checkpoint = load_recovery_checkpoint(args.source_snapshots, protocol)
    bundle = build_r7_three_arm_plan(protocol=protocol, r5=r5, checkpoint=checkpoint, replicates=args.replicates, plan_code_sha=args.plan_code_sha)
    verify_r7_three_arm_plan(bundle)

    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r7_three_arm_plan_dir")
    out.mkdir(parents=True)
    _write_json(out / "r7_plan.json", bundle["plan"])
    _write_json(out / "source_parent_snapshot.json", bundle["source_parent_snapshot"])
    _write_json(out / "c3_recovery_checkpoint.json", bundle["c3_recovery_checkpoint"])
    _write_json(out / "c1_one_shot_envelope.json", bundle["c1_one_shot_envelope"])
    _write_json(out / "c2_persistent_field_envelope.json", bundle["c2_persistent_field_envelope"])
    _write_json(out / "c3_alr_binding.json", bundle["c3_alr_binding"])
    _write_json(out / "r7_bounded_arena_config.json", bundle["bounded_arena_config"])
    write_jsonl(out / "arm_manifests.jsonl", bundle["arm_manifests"])
    write_jsonl(out / "execution_rows.jsonl", bundle["execution_rows"])

    print("R7_PLAN=PREPARED_OFFLINE_EXACT_SOURCE_BOUND")
    print("PLAN_HASH=" + bundle["plan"]["plan_hash"])
    print("COMMON_REFERENCE_PARENT=" + bundle["source_parent_snapshot"]["state_hash"])
    print("C3_RECOVERY_CHECKPOINT=" + bundle["c3_recovery_checkpoint"]["state_hash"])
    print("COMMON_HORIZON=" + bundle["plan"]["matched_horizon"]["horizon_id"])
    print("C1_RUNTIME_MECHANISM=READY")
    print("C2_RUNTIME_MECHANISM=READY")
    print("C3_RUNTIME_MECHANISM=READY")
    print("PAID_SUBJECT_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
