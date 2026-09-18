#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl
from .process_reality_dynamics_v0_4 import build_process_reality_measurement, compare_process_reality
from .r7_runtime_smoke import load_r7_plan_bundle
from .system_behavior import content_hash
from .system_behavior_adapter import adapt_arena_trace_v03
from .system_behavior_dynamics_v4 import build_system_dynamics_view
from .system_behavior_lineage_v4 import build_system_lineage_view

DERIVATION_SUMMARY_SCHEMA = "RB-R7-PROCESS-REALITY-DERIVATION-SUMMARY-v0.1"
TRIAD_INDEX_SCHEMA = "RB-R7-TRIAD-INDEX-v0.1"
ENGINEERING_ROLE = "ENGINEERING_VALIDATION_EVIDENCE"
SUBJECT_ROLE = "SUBJECT_PROCESS_EVIDENCE"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _verify_evidence_hash(evidence: dict[str, Any]) -> None:
    material = copy.deepcopy(evidence)
    expected = material.pop("evidence_batch_hash", None)
    _require(isinstance(expected, str) and expected, "r7_evidence_batch_hash_required")
    _require(stable_hash(material) == expected, "r7_evidence_batch_hash_mismatch")


def _path_overflow(measurement: dict[str, Any]) -> bool:
    return bool((((measurement.get("root_descendant_topology") or {}).get("observed_path_families") or {}).get("path_family_overflow")))


def _condition_integrity(trace: dict[str, Any], arm_id: str) -> dict[str, Any]:
    condition = trace.get("r7_condition") or {}
    runtime_records = [row for row in trace.get("runtime_transform_records") or [] if row.get("experiment_origin") is True]
    action_records = [row for row in trace.get("action_transform_records") or [] if row.get("experiment_origin") is True]
    failures: list[str] = []
    if condition.get("arm_id") != arm_id:
        failures.append("ARM_ID_MISMATCH")
    if arm_id == "C1_ONE_SHOT":
        if len(runtime_records) != 1:
            failures.append("C1_DIRECT_EXPOSURE_COUNT_NOT_ONE")
        if action_records:
            failures.append("C1_ACTION_TRANSFORM_FORBIDDEN")
    elif arm_id == "C2_PERSISTENT_FIELD":
        if len(runtime_records) < 1:
            failures.append("C2_NO_DIRECT_EXPOSURE")
        if action_records:
            failures.append("C2_ACTION_TRANSFORM_FORBIDDEN")
    elif arm_id == "C3_ALR":
        status = condition.get("condition_status")
        repair_application = trace.get("r7_repair_application")
        repair_verification = trace.get("r7_semantic_repair_verification")
        if status != "OBSERVED":
            failures.append("C3_DIRECT_REPAIR_MUST_BE_OBSERVED")
        if action_records:
            failures.append("C3_ACTION_TRANSFORM_FORBIDDEN")
        if runtime_records:
            failures.append("C3_PROMPT_RUNTIME_OVERLAY_FORBIDDEN")
        if not isinstance(repair_application, dict):
            failures.append("C3_REPAIR_APPLICATION_REQUIRED")
        if not isinstance(repair_verification, dict):
            failures.append("C3_OBSERVED_REQUIRES_SEMANTIC_REPAIR_VERIFICATION")
        if isinstance(repair_verification, dict) and repair_verification.get("target_integrity_repair_executed") is not True:
            failures.append("C3_REPAIR_VERIFICATION_TARGET_NOT_EXECUTED")
        if isinstance(repair_verification, dict) and repair_verification.get("authority_state_repair_applied") is not True:
            failures.append("C3_REPAIR_VERIFICATION_AUTHORITY_STATE_REPAIR_MISSING")
    else:
        failures.append("UNKNOWN_ARM")
    return {
        "ok": not failures,
        "failures": failures,
        "runtime_transform_count": len(runtime_records),
        "action_transform_count": len(action_records),
    }


def derive_r7(*, plan_dir: str | Path, traces_path: str | Path, evidence_batch_path: str | Path, allow_engineering_validation: bool = False):
    bundle = load_r7_plan_bundle(plan_dir)
    evidence = load_json(evidence_batch_path)
    _verify_evidence_hash(evidence)
    _require(evidence.get("raw_evidence_frozen_before_derived_analysis") is True, "r7_raw_evidence_must_be_frozen_before_derivation")
    _require(evidence.get("plan_hash") == bundle["plan"]["plan_hash"], "r7_evidence_plan_hash_mismatch")
    role = evidence.get("evidence_role")
    _require(role in (SUBJECT_ROLE, ENGINEERING_ROLE), "r7_unknown_evidence_role")
    if role == ENGINEERING_ROLE and not allow_engineering_validation:
        raise ValueError("r7_engineering_evidence_derivation_requires_explicit_allow_flag")

    traces = load_jsonl(traces_path)
    rows_by_run = {row["run_id"]: row for row in bundle["execution_rows"]}
    target_event_index = int(bundle["c1_one_shot_envelope"]["source_event_index"])
    target_state_key = bundle["c1_one_shot_envelope"]["state_key"]
    target_candidate_id = bundle["c1_one_shot_envelope"]["target_candidate_id"]
    common_post_jump_turn = int(bundle["source_parent_snapshot"]["turns"])

    measurements: list[dict[str, Any]] = []
    by_run: dict[str, dict[str, Any]] = {}
    integrity_failures: list[dict[str, Any]] = []

    for trace in traces:
        run_id = trace.get("run_id")
        row = rows_by_run.get(run_id)
        _require(row is not None, "r7_trace_not_in_plan:" + str(run_id))
        arm_id = row["arm_id"]
        integrity = _condition_integrity(trace, arm_id)
        for failure in integrity["failures"]:
            integrity_failures.append({"run_id": run_id, "arm_id": arm_id, "type": failure})

        adapted = adapt_arena_trace_v03(trace)
        dynamics = build_system_dynamics_view(adapted)
        lineage = build_system_lineage_view(adapted, dynamics_view=dynamics)
        measurement = build_process_reality_measurement(
            trace=trace,
            adapter_result=adapted,
            dynamics_view=dynamics,
            lineage_view=lineage,
            target_source_event_index=target_event_index,
            target_state_key=target_state_key,
            target_candidate_id=target_candidate_id,
            branch_start_turn=common_post_jump_turn,
        )
        condition = trace.get("r7_condition") or {}
        revision = trace.get("r7_revision_lineage") or {}
        repair_verification = trace.get("r7_semantic_repair_verification") or {}
        measurement.update({
            "r7_protocol_id": bundle["plan"]["protocol_id"],
            "triad_id": row["triad_id"],
            "arm_id": arm_id,
            "replicate_index": row["replicate_index"],
            "execution_order": row["execution_order"],
            "condition_status": condition.get("condition_status"),
            "condition_integrity": integrity,
            "common_reference_parent_state_hash": bundle["source_parent_snapshot"]["state_hash"],
            "branch_start_state_hash": condition.get("branch_start_state_hash"),
            "c3_recovery_checkpoint_state_hash": bundle["c3_recovery_checkpoint"]["state_hash"] if arm_id == "C3_ALR" else None,
            "c3_repaired_parent_state_hash": bundle["c3_repaired_parent_snapshot"]["state_hash"] if arm_id == "C3_ALR" else None,
            "c3_repair_application_hash": (trace.get("r7_repair_application") or {}).get("repair_application_hash") if arm_id == "C3_ALR" else None,
            "semantic_payload_hash": bundle["plan"]["semantic_payload_hash"],
            "observation_horizon_id": bundle["plan"]["matched_horizon"]["horizon_id"],
            "runtime_transform_count": integrity["runtime_transform_count"],
            "action_transform_count": integrity["action_transform_count"],
            "revision_hash": revision.get("revision_hash"),
            "semantic_repair_verification_hash": repair_verification.get("verification_hash"),
            "semantic_repair_packet_hash": repair_verification.get("packet_hash"),
            "old_lineage_reentry_detected": repair_verification.get("old_lineage_reentry_detected"),
            "old_lineage_reentry_refs": list(repair_verification.get("old_lineage_reentry_refs") or []),
            "preserved_unrelated_structure": repair_verification.get("preserved_unrelated_structure"),
            "recomputed_descendant_refs": list(repair_verification.get("recomputed_descendant_refs") or []),
            "semantic_lineage_closure_before_hash": repair_verification.get("semantic_lineage_closure_before_hash"),
            "semantic_lineage_closure_after_hash": repair_verification.get("semantic_lineage_closure_after_hash"),
            "source_raw_evidence_batch_hash": evidence["evidence_batch_hash"],
            "source_evidence_role": role,
            "semantic_status": "NOT_ADJUDICATED",
            "terminal_outcome_is_primary": False,
        })
        measurement["measurement_hash"] = content_hash({k: v for k, v in measurement.items() if k != "measurement_hash"})
        measurements.append(measurement)
        by_run[run_id] = measurement

    comparisons: list[dict[str, Any]] = []
    triad_index: list[dict[str, Any]] = []
    for triad_id in sorted({row["triad_id"] for row in bundle["execution_rows"]}):
        triad_rows = [row for row in bundle["execution_rows"] if row["triad_id"] == triad_id]
        arm_rows = {row["arm_id"]: row for row in triad_rows}
        arm_measurements = {arm: by_run.get(row["run_id"]) for arm, row in arm_rows.items()}
        statuses = {
            arm: {
                "trace_present": measurement is not None,
                "run_status": measurement.get("run_status") if measurement else "MISSING_TRACE",
                "root_status": measurement.get("mechanism_measurement_status") if measurement else "MISSING_TRACE",
                "condition_status": measurement.get("condition_status") if measurement else "MISSING_TRACE",
                "integrity_ok": bool((measurement or {}).get("condition_integrity", {}).get("ok")) if measurement else False,
            }
            for arm, measurement in arm_measurements.items()
        }
        record = {
            "schema": TRIAD_INDEX_SCHEMA,
            "triad_id": triad_id,
            "replicate_index": triad_rows[0]["replicate_index"],
            "arm_statuses": statuses,
            "r7a_comparison_generated": False,
            "r7b_comparison_generated": False,
            "source_raw_evidence_batch_hash": evidence["evidence_batch_hash"],
            "semantic_status": "NOT_ADJUDICATED",
        }

        def comparable(arm: str) -> bool:
            measurement = arm_measurements.get(arm)
            return bool(
                measurement
                and measurement.get("mechanism_measurement_status") == "ROOT_RESOLVED"
                and measurement.get("condition_status") == "OBSERVED"
                and (measurement.get("condition_integrity") or {}).get("ok") is True
            )

        if comparable("C1_ONE_SHOT") and comparable("C2_PERSISTENT_FIELD"):
            c1 = arm_measurements["C1_ONE_SHOT"]
            c2 = arm_measurements["C2_PERSISTENT_FIELD"]
            comparison = compare_process_reality(c1, c2, comparison_id=triad_id + ":R7A:C1_vs_C2:v0.4")
            comparison.update({
                "r7_comparison": "R7-A_ONE_SHOT_VS_PERSISTENT_FIELD",
                "left_arm_id": "C1_ONE_SHOT",
                "right_arm_id": "C2_PERSISTENT_FIELD",
                "source_raw_evidence_batch_hash": evidence["evidence_batch_hash"],
                "path_family_completeness": {
                    "left_overflow": _path_overflow(c1),
                    "right_overflow": _path_overflow(c2),
                },
                "interpretation_boundary": "C2 persistence may be experiment-maintained; structural difference does not by itself establish endogenous inertia or semantic CPR.",
            })
            comparison["comparison_hash"] = content_hash({k: v for k, v in comparison.items() if k != "comparison_hash"})
            comparisons.append(comparison)
            record["r7a_comparison_generated"] = True

        if comparable("C2_PERSISTENT_FIELD") and comparable("C3_ALR"):
            c2 = arm_measurements["C2_PERSISTENT_FIELD"]
            c3 = arm_measurements["C3_ALR"]
            comparison = compare_process_reality(c2, c3, comparison_id=triad_id + ":R7B:C2_vs_C3:v0.4")
            comparison.update({
                "r7_comparison": "R7-B_PERSISTENT_FIELD_VS_ALR_RECOVERY",
                "left_arm_id": "C2_PERSISTENT_FIELD",
                "right_arm_id": "C3_ALR",
                "source_raw_evidence_batch_hash": evidence["evidence_batch_hash"],
                "c3_revision_hash": c3.get("revision_hash"),
                "c3_semantic_repair_verification_hash": c3.get("semantic_repair_verification_hash"),
                "c3_old_lineage_reentry_detected": c3.get("old_lineage_reentry_detected"),
                "c3_preserved_unrelated_structure": c3.get("preserved_unrelated_structure"),
                "path_family_completeness": {
                    "left_overflow": _path_overflow(c2),
                    "right_overflow": _path_overflow(c3),
                },
                "interpretation_boundary": "Observed structural difference is evidence about mechanism response. A single triad does not establish reliable controllability or universal recovery superiority.",
            })
            comparison["comparison_hash"] = content_hash({k: v for k, v in comparison.items() if k != "comparison_hash"})
            comparisons.append(comparison)
            record["r7b_comparison_generated"] = True
        elif arm_measurements.get("C3_ALR") is not None:
            record["r7b_noncomparison_reason"] = "C3_NOT_COMPARABLE_PRESERVED_AS_CENSORED"

        record["triad_status"] = (
            "COMPLETE_NESTED_R7A_R7B_STRUCTURAL_COMPARISON"
            if record["r7a_comparison_generated"] and record["r7b_comparison_generated"]
            else "PRESERVED_PARTIAL_OR_CENSORED_TRIAD"
        )
        triad_index.append(record)

    summary = {
        "schema": DERIVATION_SUMMARY_SCHEMA,
        "source_raw_evidence_batch_hash": evidence["evidence_batch_hash"],
        "source_evidence_role": role,
        "scientific_status": "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE" if role == ENGINEERING_ROLE else "SUBJECT_STRUCTURAL_DERIVATION",
        "measurement_schema": "RB-PROCESS-REALITY-MECHANISM-MEASUREMENT-v0.4",
        "measurement_count": len(measurements),
        "triad_count": len(triad_index),
        "comparison_count": len(comparisons),
        "r7a_comparison_count": sum(1 for row in comparisons if row.get("r7_comparison") == "R7-A_ONE_SHOT_VS_PERSISTENT_FIELD"),
        "r7b_comparison_count": sum(1 for row in comparisons if row.get("r7_comparison") == "R7-B_PERSISTENT_FIELD_VS_ALR_RECOVERY"),
        "semantic_repair_verification_count": sum(1 for row in measurements if row.get("semantic_repair_verification_hash")),
        "old_lineage_reentry_detected_count": sum(1 for row in measurements if row.get("old_lineage_reentry_detected") is True),
        "preserved_unrelated_structure_pass_count": sum(1 for row in measurements if row.get("preserved_unrelated_structure") is True),
        "integrity_failure_count": len(integrity_failures),
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "paid_evaluator_called": False,
        "terminal_outcome_is_primary": False,
        "provider_internal_state_replayed": False,
        "interpretation_boundary": "Mechanical structural derivation only. Directional steering, recovery success, semantic CPR, and reliable control require separate interpretation over frozen evidence.",
    }
    summary["summary_hash"] = content_hash(summary)
    return measurements, comparisons, triad_index, integrity_failures, summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan-dir", required=True)
    ap.add_argument("--traces", required=True)
    ap.add_argument("--evidence-batch", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--allow-engineering-validation", action="store_true")
    args = ap.parse_args()

    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r7_derived_dir")
    out.mkdir(parents=True)
    measurements, comparisons, triad_index, integrity_failures, summary = derive_r7(
        plan_dir=args.plan_dir,
        traces_path=args.traces,
        evidence_batch_path=args.evidence_batch,
        allow_engineering_validation=args.allow_engineering_validation,
    )
    write_jsonl(out / "r7_process_measurements_v0.4.jsonl", measurements)
    write_jsonl(out / "r7_structural_comparisons_v0.4.jsonl", comparisons)
    write_jsonl(out / "r7_triad_index.jsonl", triad_index)
    write_jsonl(out / "integrity_failures.jsonl", integrity_failures)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("R7_PROCESS_MEASUREMENTS=" + str(summary["measurement_count"]))
    print("R7_STRUCTURAL_COMPARISONS=" + str(summary["comparison_count"]))
    print("R7A_COMPARISONS=" + str(summary["r7a_comparison_count"]))
    print("R7B_COMPARISONS=" + str(summary["r7b_comparison_count"]))
    print("SEMANTIC_REPAIR_VERIFICATIONS=" + str(summary["semantic_repair_verification_count"]))
    print("OLD_LINEAGE_REENTRY_DETECTED=" + str(summary["old_lineage_reentry_detected_count"]))
    print("PRESERVED_UNRELATED_PASS=" + str(summary["preserved_unrelated_structure_pass_count"]))
    print("INTEGRITY_FAILURES=" + str(summary["integrity_failure_count"]))
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
