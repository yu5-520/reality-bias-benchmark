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


PLAN_SCHEMA = "RB-R7-THREE-ARM-EXECUTION-PLAN-v0.1"
ARM_MANIFEST_SCHEMA = "RB-R7-ARM-MANIFEST-v0.1"
ALR_BINDING_SCHEMA = "RB-R7-ALR-BINDING-TEMPLATE-v0.1"
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


def _semantic_payload_hash(protocol: Mapping[str, Any]) -> str:
    payload = protocol["semantic_payload"]
    return stable_hash({
        "target_path": payload["target_path"],
        "operation": payload["operation"],
        "from": payload["from"],
        "to": payload["to"],
    })


def validate_source_binding(protocol: Mapping[str, Any], r5: Mapping[str, Any]) -> dict[str, Any]:
    parent_binding = protocol["frozen_parent"]
    jump = protocol["jump"]
    payload = protocol["semantic_payload"]
    horizon = protocol["matched_horizon"]
    source_plan = r5["plan"]
    parent = r5["parent_snapshot"]
    envelope = r5["one_shot_envelope"]

    _require(source_plan.get("plan_hash") == parent_binding["source_plan_hash"], "r7_source_plan_hash_mismatch")
    _require(parent.get("state_hash") == parent_binding["parent_state_hash"], "r7_parent_state_hash_mismatch")
    _require(source_plan.get("code_identity", {}).get("branch_execution_commit") == parent_binding.get("code_sha"), "r7_source_execution_code_sha_mismatch")
    _require(envelope.get("source_event_index") == jump["source_event_index"], "r7_jump_event_index_mismatch")
    _require(envelope.get("state_key") == jump["state_key"], "r7_jump_state_key_mismatch")
    _require(envelope.get("from_status") == payload["from"], "r7_payload_from_status_mismatch")
    _require(envelope.get("to_status") == payload["to"], "r7_payload_to_status_mismatch")
    _require(parent.get("shared_state_metadata", {}).get(jump["state_key"], {}).get("status") == payload["from"], "r7_parent_jump_status_mismatch")
    _require(parent.get("terminated") is False, "r7_parent_snapshot_must_be_resumable")
    _require(isinstance(parent.get("queue"), list) and parent["queue"], "r7_parent_snapshot_requires_pending_queue")
    _require(isinstance(horizon.get("post_jump_turn_cap"), int) and horizon["post_jump_turn_cap"] >= 1, "r7_horizon_cap_invalid")

    parent_turn = int(parent["turns"])
    turn_cap = int(horizon["post_jump_turn_cap"])
    return {
        "source_r5_plan_hash": source_plan["plan_hash"],
        "source_parent_state_hash": parent["state_hash"],
        "source_one_shot_envelope_hash": envelope["envelope_hash"],
        "source_branch_execution_commit": source_plan.get("code_identity", {}).get("branch_execution_commit"),
        "source_measurement_binding": copy.deepcopy(source_plan.get("source_measurement_binding") or {}),
        "parent_turn": parent_turn,
        "parent_event_count": len(parent.get("events") or []),
        "parent_queue_head": parent["queue"][0],
        "matched_horizon_id": horizon["horizon_id"],
        "post_jump_turn_cap": turn_cap,
        "absolute_turn_cap": parent_turn + turn_cap,
        "early_termination_policy": horizon["early_termination_policy"],
        "provider_internal_state_replayed": False,
    }


def _build_bounded_arena_config(source_plan: Mapping[str, Any], parent: Mapping[str, Any], protocol: Mapping[str, Any]) -> dict[str, Any]:
    arena_path = source_plan.get("config_identity", {}).get("arena_config_path")
    _require(isinstance(arena_path, str) and arena_path, "r7_source_arena_config_path_missing")
    source = load_json(arena_path)
    out = copy.deepcopy(source)
    absolute_turn_cap = int(parent["turns"]) + int(protocol["matched_horizon"]["post_jump_turn_cap"])
    source_max = int(source["max_turns"])
    _require(source_max >= absolute_turn_cap, "r7_common_horizon_exceeds_source_arena_turn_budget")
    out["max_turns"] = absolute_turn_cap
    out["r7_observation_horizon"] = {
        "horizon_id": protocol["matched_horizon"]["horizon_id"],
        "parent_turn": int(parent["turns"]),
        "post_jump_turn_cap": int(protocol["matched_horizon"]["post_jump_turn_cap"]),
        "absolute_turn_cap": absolute_turn_cap,
        "termination_policy": protocol["matched_horizon"]["termination_policy"],
        "early_termination_policy": protocol["matched_horizon"]["early_termination_policy"],
    }
    return out


def build_r7_three_arm_plan(*, protocol: Mapping[str, Any], r5: Mapping[str, Any], replicates: int, plan_code_sha: str) -> dict[str, Any]:
    _require(isinstance(replicates, int) and replicates >= 1, "r7_positive_replicates_required")
    source_binding = validate_source_binding(protocol, r5)
    parent = copy.deepcopy(r5["parent_snapshot"])
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

    alr_binding = {
        "schema": ALR_BINDING_SCHEMA,
        "version": "0.1",
        "jump_ref": one_shot["target_jump_ref"],
        "jump_source_event_index": one_shot["source_event_index"],
        "state_key": one_shot["state_key"],
        "semantic_payload_hash": semantic_hash,
        "authority_anchor_policy": protocol["arms"]["C3_ALR"]["authority_anchor_policy"],
        "closure_policy": protocol["arms"]["C3_ALR"]["closure_policy"],
        "preserve_unaffected": True,
        "revision_required": True,
        "closure_status": "PENDING_SOURCE_BACKED_RUNTIME_LINEAGE",
        "active_recovery_executor_status": "NOT_IMPLEMENTED_FAIL_CLOSED",
        "provider_internal_state_replayed": False,
        "note": (
            "R7 Phase-1 binds C3 to the same parent/J0/payload but intentionally does not fabricate an affected closure. "
            "The real C3 subject path remains blocked until source-backed lineage can drive localized reopen/re-execution and emit revision evidence."
        ),
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
                readiness = "RUNTIME_TRANSFORM_READY"
                intervention_binding_hash = one_shot["envelope_hash"]
            elif arm_id == "C2_PERSISTENT_FIELD":
                readiness = "RUNTIME_TRANSFORM_READY"
                intervention_binding_hash = persistent["envelope_hash"]
            else:
                readiness = "BLOCKED_PENDING_ACTIVE_ALR_EXECUTOR"
                intervention_binding_hash = alr_binding["binding_hash"]
            manifest = {
                "schema": ARM_MANIFEST_SCHEMA,
                "version": "0.1",
                "branch_id": branch_id,
                "triad_id": triad_id,
                "replicate_index": replicate,
                "execution_order": execution_order,
                "arm_id": arm_id,
                "parent_state_hash": parent["state_hash"],
                "branch_start_state_hash": parent["state_hash"],
                "parent_turn": int(parent["turns"]),
                "jump_ref": one_shot["target_jump_ref"],
                "jump_source_event_index": one_shot["source_event_index"],
                "semantic_payload_hash": semantic_hash,
                "observation_horizon_id": horizon["horizon_id"],
                "post_jump_turn_cap": int(horizon["post_jump_turn_cap"]),
                "absolute_turn_cap": int(parent["turns"]) + int(horizon["post_jump_turn_cap"]),
                "bounded_arena_config_hash": bounded_config_hash,
                "intervention_binding_hash": intervention_binding_hash,
                "execution_readiness": readiness,
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
                "execution_readiness": readiness,
            })

    plan = {
        "schema": PLAN_SCHEMA,
        "version": "0.1",
        "protocol_id": protocol["protocol_id"],
        "phase": "R7_PHASE1_REAL_PARENT_BINDING_PREPARED_ONLY",
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
            "C1": "one experiment-origin exposure then free continuation",
            "C2": "same payload re-exposed on each eligible post-Jump turn within common horizon",
            "C3": "same payload bound to lineage-aware localized recovery; subject execution blocked until active executor exists",
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
        "real_three_arm_execution_ready": False,
        "blocking_reason": "C3_ACTIVE_ALR_LOCALIZED_REEXECUTION_NOT_IMPLEMENTED",
    }
    plan["plan_hash"] = _hash_without(plan, "plan_hash")

    return {
        "plan": plan,
        "source_parent_snapshot": parent,
        "c1_one_shot_envelope": one_shot,
        "c2_persistent_field_envelope": persistent,
        "c3_alr_binding_template": alr_binding,
        "bounded_arena_config": bounded_arena_config,
        "arm_manifests": manifests,
        "execution_rows": rows,
    }


def verify_r7_three_arm_plan(bundle: Mapping[str, Any]) -> bool:
    plan = bundle["plan"]
    parent = bundle["source_parent_snapshot"]
    verify_state_snapshot(parent)
    verify_one_shot_envelope(bundle["c1_one_shot_envelope"])
    verify_persistent_field_envelope(bundle["c2_persistent_field_envelope"])
    _require(plan.get("schema") == PLAN_SCHEMA, "r7_plan_schema_invalid")
    _require(plan.get("plan_hash") == _hash_without(plan, "plan_hash"), "r7_plan_hash_mismatch")
    _require(plan.get("source_binding", {}).get("source_parent_state_hash") == parent["state_hash"], "r7_plan_parent_binding_mismatch")
    _require(plan.get("paid_subject_authorization_status") == "NOT_AUTHORIZED", "r7_plan_must_not_self_authorize")
    _require(plan.get("automatic_paid_evaluator") is False, "r7_plan_paid_evaluator_forbidden")
    _require(plan.get("semantic_cpr_status") == "NOT_ADJUDICATED", "r7_plan_semantic_status_invalid")
    _require(plan.get("real_three_arm_execution_ready") is False, "r7_plan_must_fail_closed_until_c3_ready")
    manifests = list(bundle["arm_manifests"])
    rows = list(bundle["execution_rows"])
    _require(len(manifests) == len(rows) == plan["branch_row_count"] == plan["replicates"] * 3, "r7_plan_row_count_mismatch")
    _require({m["arm_id"] for m in manifests} == set(ARM_IDS), "r7_plan_missing_arm")
    parent_hashes = {m["parent_state_hash"] for m in manifests}
    horizon_ids = {m["observation_horizon_id"] for m in manifests}
    semantic_hashes = {m["semantic_payload_hash"] for m in manifests}
    _require(parent_hashes == {parent["state_hash"]}, "r7_manifest_parent_not_matched")
    _require(horizon_ids == {plan["matched_horizon"]["horizon_id"]}, "r7_manifest_horizon_not_matched")
    _require(semantic_hashes == {plan["semantic_payload_hash"]}, "r7_manifest_semantic_payload_not_matched")
    c3 = [m for m in manifests if m["arm_id"] == "C3_ALR"]
    _require(c3 and all(m["execution_readiness"] == "BLOCKED_PENDING_ACTIVE_ALR_EXECUTOR" for m in c3), "r7_c3_fail_closed_required")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", default="configs/r7/r7_three_arm_fixture.example.json")
    ap.add_argument("--r5-plan-dir", required=True)
    ap.add_argument("--replicates", type=int, default=1)
    ap.add_argument("--plan-code-sha", default="LOCAL_OR_UNRECORDED")
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    protocol = load_json(args.protocol)
    r5 = load_r5_plan_bundle(args.r5_plan_dir)
    bundle = build_r7_three_arm_plan(protocol=protocol, r5=r5, replicates=args.replicates, plan_code_sha=args.plan_code_sha)
    verify_r7_three_arm_plan(bundle)

    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r7_three_arm_plan_dir")
    out.mkdir(parents=True)
    _write_json(out / "r7_plan.json", bundle["plan"])
    _write_json(out / "source_parent_snapshot.json", bundle["source_parent_snapshot"])
    _write_json(out / "c1_one_shot_envelope.json", bundle["c1_one_shot_envelope"])
    _write_json(out / "c2_persistent_field_envelope.json", bundle["c2_persistent_field_envelope"])
    _write_json(out / "c3_alr_binding_template.json", bundle["c3_alr_binding_template"])
    _write_json(out / "r7_bounded_arena_config.json", bundle["bounded_arena_config"])
    write_jsonl(out / "arm_manifests.jsonl", bundle["arm_manifests"])
    write_jsonl(out / "execution_rows.jsonl", bundle["execution_rows"])

    print("R7_PHASE1_PLAN=PREPARED_OFFLINE_REAL_PARENT_BOUND")
    print("PLAN_HASH=" + bundle["plan"]["plan_hash"])
    print("PARENT_STATE_HASH=" + bundle["source_parent_snapshot"]["state_hash"])
    print("COMMON_HORIZON=" + bundle["plan"]["matched_horizon"]["horizon_id"])
    print("C1_RUNTIME=READY")
    print("C2_RUNTIME=READY")
    print("C3_RUNTIME=BLOCKED_PENDING_ACTIVE_ALR_EXECUTOR")
    print("PAID_SUBJECT_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
