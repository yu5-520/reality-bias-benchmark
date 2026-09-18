#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .core import stable_hash
from .io_utils import load_jsonl, sha256_file
from .r7_runtime_smoke import load_r7_plan_bundle

EVIDENCE_SCHEMA = "RB-R7-THREE-ARM-EVIDENCE-BATCH-v0.2"
ENGINEERING_STATUS = "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE"


def _maybe_sha(path: Path) -> str | None:
    return sha256_file(path) if path.exists() else None


def _journal_manifest(journal_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if journal_dir.exists():
        for path in sorted(journal_dir.glob("*.jsonl")):
            rows.append({"file": path.name, "sha256": sha256_file(path)})
    return rows


def _count(rows: list[dict], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key))
        out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items()))


def freeze_r7_evidence(*, raw_dir: str | Path, plan_dir: str | Path, authorization_record: str | Path | None = None) -> dict[str, Any]:
    raw = Path(raw_dir)
    plan_path = Path(plan_dir)
    bundle = load_r7_plan_bundle(plan_path)
    traces_path = raw / "traces.jsonl"
    if not traces_path.exists():
        raise ValueError("r7_traces_required_for_evidence_freeze")
    traces = load_jsonl(traces_path)
    if not traces:
        raise ValueError("r7_at_least_one_trace_required_for_evidence_freeze")

    planned_ids = {row["run_id"] for row in bundle["execution_rows"]}
    trace_ids = [trace.get("run_id") for trace in traces]
    if len(trace_ids) != len(set(trace_ids)):
        raise ValueError("r7_duplicate_trace_run_id")
    if any(run_id not in planned_ids for run_id in trace_ids):
        raise ValueError("r7_trace_not_in_frozen_plan")

    trace_scientific_statuses = sorted({str(trace.get("scientific_status") or "SUBJECT_PROCESS_EVIDENCE") for trace in traces})
    engineering_only = trace_scientific_statuses == [ENGINEERING_STATUS]
    evidence_role = "ENGINEERING_VALIDATION_EVIDENCE" if engineering_only else "SUBJECT_PROCESS_EVIDENCE"

    arm_ids = set(bundle["plan"]["arm_ids"])
    condition_rows: list[dict[str, Any]] = []
    for trace in traces:
        condition = trace.get("r7_condition") or {}
        arm_id = condition.get("arm_id")
        if arm_id not in arm_ids:
            raise ValueError("r7_trace_missing_or_unknown_condition_arm")
        if condition.get("common_reference_parent_state_hash") != bundle["source_parent_snapshot"]["state_hash"]:
            raise ValueError("r7_trace_reference_parent_mismatch")
        if condition.get("semantic_payload_hash") != bundle["plan"]["semantic_payload_hash"]:
            raise ValueError("r7_trace_semantic_payload_mismatch")
        if condition.get("observation_horizon_id") != bundle["plan"]["matched_horizon"]["horizon_id"]:
            raise ValueError("r7_trace_horizon_mismatch")
        if condition.get("provider_internal_state_replayed") is not False:
            raise ValueError("r7_trace_invalid_provider_hidden_state_replay_claim")
        if condition.get("semantic_cpr_status") != "NOT_ADJUDICATED":
            raise ValueError("r7_trace_semantic_status_must_be_deferred")

        runtime_records = [row for row in trace.get("runtime_transform_records") or [] if row.get("experiment_origin") is True]
        action_records = [row for row in trace.get("action_transform_records") or [] if row.get("experiment_origin") is True]
        revision = trace.get("r7_revision_lineage")
        repair_application = trace.get("r7_repair_application")
        repair_verification = trace.get("r7_semantic_repair_verification")
        if arm_id == "C3_ALR":
            if condition.get("condition_status") != "OBSERVED":
                raise ValueError("r7_c3_direct_repair_condition_must_be_observed")
            if not isinstance(repair_application, dict):
                raise ValueError("r7_c3_repair_application_missing")
            if repair_application.get("repair_application_hash") != bundle["c3_repair_application"].get("repair_application_hash"):
                raise ValueError("r7_c3_repair_application_hash_mismatch")
            if not isinstance(repair_verification, dict):
                raise ValueError("r7_c3_observed_missing_semantic_repair_verification")
            if repair_verification.get("target_integrity_repair_executed") is not True:
                raise ValueError("r7_c3_repair_verification_target_not_executed")
            if repair_verification.get("packet_hash") != bundle["semantic_repair_packet"].get("packet_hash"):
                raise ValueError("r7_c3_repair_packet_hash_mismatch")
        condition_rows.append({
            "run_id": trace.get("run_id"),
            "arm_id": arm_id,
            "condition_status": condition.get("condition_status"),
            "run_status": trace.get("run_status"),
            "scientific_status": trace.get("scientific_status") or "SUBJECT_PROCESS_EVIDENCE",
            "runtime_transform_count": len(runtime_records),
            "action_transform_count": len(action_records),
            "revision_hash": revision.get("revision_hash") if isinstance(revision, dict) else None,
            "repair_application_hash": repair_application.get("repair_application_hash") if isinstance(repair_application, dict) else None,
            "semantic_repair_verification_hash": repair_verification.get("verification_hash") if isinstance(repair_verification, dict) else None,
            "old_lineage_reentry_detected": repair_verification.get("old_lineage_reentry_detected") if isinstance(repair_verification, dict) else None,
            "preserved_unrelated_structure": repair_verification.get("preserved_unrelated_structure") if isinstance(repair_verification, dict) else None,
            "post_repair_watch_result_hash": repair_verification.get("post_repair_watch_result_hash") if isinstance(repair_verification, dict) else None,
            "trace_hash": stable_hash(trace),
        })

    journals = _journal_manifest(raw / "journals")
    plan_files = [
        "r7_plan.json",
        "source_parent_snapshot.json",
        "c3_recovery_checkpoint.json",
        "c1_one_shot_envelope.json",
        "c2_persistent_field_envelope.json",
        "c3_alr_binding.json",
        "semantic_repair_runtime_plan.json",
        "c3_repaired_parent_snapshot.json",
        "c3_repair_application.json",
        "semantic_repair_packet.json",
        "semantic_lineage_package.json",
        "post_repair_watch_contract.json",
        "lineage_completeness_gate.json",
        "r7_bounded_arena_config.json",
        "arm_manifests.jsonl",
        "execution_rows.jsonl",
    ]
    plan_hashes = {name: sha256_file(plan_path / name) for name in plan_files}
    authorization_path = Path(authorization_record) if authorization_record else None
    if evidence_role == "SUBJECT_PROCESS_EVIDENCE" and authorization_path is None:
        raise ValueError("r7_subject_evidence_requires_authorization_record_binding")
    authorization = json.loads(authorization_path.read_text(encoding="utf-8")) if authorization_path else None
    authorization_scope = (authorization or {}).get("execution_scope", "FULL")
    if authorization_scope == "C3_ONLY":
        if any(row.get("arm_id") != "C3_ALR" for row in condition_rows):
            raise ValueError("r7_c3_only_evidence_contains_non_c3_trace")
        selected_branch_count = int((authorization or {}).get("selected_branch_count") or 0)
        if selected_branch_count <= 0:
            raise ValueError("r7_c3_only_authorization_missing_selected_branch_count")
        if len(traces) > selected_branch_count:
            raise ValueError("r7_c3_only_trace_count_exceeds_authorized_branch_count")

    record = {
        "schema": EVIDENCE_SCHEMA,
        "evidence_role": evidence_role,
        "trace_scientific_statuses": trace_scientific_statuses,
        "plan_hash": bundle["plan"]["plan_hash"],
        "protocol_id": bundle["plan"]["protocol_id"],
        "common_reference_parent_state_hash": bundle["source_parent_snapshot"]["state_hash"],
        "c3_recovery_checkpoint_state_hash": bundle["c3_recovery_checkpoint"]["state_hash"],
        "c3_repaired_parent_state_hash": bundle["c3_repaired_parent_snapshot"]["state_hash"],
        "c3_repair_application_hash": bundle["c3_repair_application"]["repair_application_hash"],
        "semantic_payload_hash": bundle["plan"]["semantic_payload_hash"],
        "observation_horizon_id": bundle["plan"]["matched_horizon"]["horizon_id"],
        "measurement_schema": bundle["plan"]["measurement_schema"],
        "semantic_repair_packet_hash": bundle["semantic_repair_packet"].get("packet_hash"),
        "semantic_lineage_package_hash": bundle["semantic_lineage_package"].get("package_hash"),
        "post_repair_watch_contract_hash": bundle["post_repair_watch_contract"].get("watch_hash"),
        "full_lineage_observation_policy": bundle["plan"].get("full_lineage_observation_policy"),
        "lineage_completeness_gate_hash": bundle["lineage_completeness_gate"].get("gate_hash"),
        "planned_branch_count": len(bundle["execution_rows"]),
        "preserved_trace_count": len(traces),
        "missing_planned_run_ids": sorted(planned_ids - set(trace_ids)),
        "run_status_counts": _count(traces, "run_status"),
        "arm_trace_counts": _count(condition_rows, "arm_id"),
        "condition_status_counts": _count(condition_rows, "condition_status"),
        "condition_records": condition_rows,
        "traces_sha256": sha256_file(traces_path),
        "run_summary_sha256": _maybe_sha(raw / "run_summary.json"),
        "smoke_summary_sha256": _maybe_sha(raw / "summary.json"),
        "errors_sha256": _maybe_sha(raw / "errors.jsonl"),
        "journal_manifest": journals,
        "journal_manifest_hash": stable_hash(journals),
        "plan_file_sha256": plan_hashes,
        "plan_file_manifest_hash": stable_hash(plan_hashes),
        "authorization_record_sha256": sha256_file(authorization_path) if authorization_path else None,
        "authorization_record_bound": authorization_path is not None,
        "authorization_execution_scope": authorization_scope,
        "authorization_selected_arm": (authorization or {}).get("selected_arm"),
        "authorization_selected_branch_count": (authorization or {}).get("selected_branch_count"),
        "raw_evidence_frozen_before_derived_analysis": True,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "paid_evaluator_called": False,
        "terminal_outcome_is_primary": False,
        "provider_internal_state_replayed": False,
        "same_parent_repeats_are_independent_samples": False,
        "interpretation_boundary": (
            "This record freezes raw process evidence and integrity metadata only. "
            "Engineering-validation evidence must not be promoted to scientific subject evidence. "
            "The freeze does not adjudicate semantic CPR, recovery success, steering direction, or a causal treatment effect."
        ),
    }
    record["evidence_batch_hash"] = stable_hash(record)
    return record


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--plan-dir", required=True)
    ap.add_argument("--authorization-record")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    record = freeze_r7_evidence(
        raw_dir=args.raw_dir,
        plan_dir=args.plan_dir,
        authorization_record=args.authorization_record,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("R7_RAW_EVIDENCE_FROZEN=YES")
    print("EVIDENCE_ROLE=" + record["evidence_role"])
    print("PRESERVED_TRACE_COUNT=" + str(record["preserved_trace_count"]))
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")
    print("EVIDENCE_BATCH_HASH=" + record["evidence_batch_hash"])


if __name__ == "__main__":
    main()
