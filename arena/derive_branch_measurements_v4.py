from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Mapping

from .io_utils import load_json, load_jsonl, sha256_file, write_jsonl
from .run_branch_real import load_plan_bundle
from .system_behavior import content_hash
from .system_behavior_adapter import adapt_arena_trace_v03
from .system_behavior_dynamics_v4 import build_system_dynamics_view
from .system_behavior_lineage_v4 import build_system_lineage_view
from .v4_experiment_binding import load_and_verify_v4_binding
from .v4_review_packets import build_bounded_review_packets


SUMMARY_SCHEMA = "RB-R5R6-BRANCH-MEASUREMENT-V4-SUMMARY-v0.1"
VALID_TRACE_STATUSES = {"RUN_COMPLETE", "BUDGET_CENSORED", "RUN_INCOMPLETE", "RUN_FAILED"}


class BranchMeasurementV4Error(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BranchMeasurementV4Error(message)


def _variable_record(binding: Mapping[str, Any], condition_id: str) -> dict[str, Any]:
    registry = load_json("configs/experimental_variable_registry_v0.1.json")
    rows = [
        row
        for row in registry.get("variables") or []
        if row.get("variable_id") == binding.get("experimental_variable_id")
    ]
    _require(len(rows) == 1, "v4_derivation_experimental_variable_not_unique")
    variable = rows[0]
    if condition_id == "CONTROL_CONTINUATION":
        level = variable.get("control_level")
        assignment = "CONTROL"
    elif condition_id == "STATUS_DOWNGRADE_INTERVENTION":
        level = variable.get("manipulation_level")
        assignment = "MANIPULATION"
    else:
        raise BranchMeasurementV4Error(f"unsupported_v4_branch_condition:{condition_id}")
    return {
        "variable_id": variable["variable_id"],
        "family": variable.get("family"),
        "stage": variable.get("stage"),
        "assignment": assignment,
        "level": level,
        "target_boundary_family": list(variable.get("target_boundary_family") or []),
        "registry_hash": binding["interface_bindings"]["experimental_variable_registry"]["sha256"],
    }


def _enrich_measurement(
    measurement: Mapping[str, Any],
    *,
    trace: Mapping[str, Any],
    row: Mapping[str, Any],
    evidence_hash: str,
    binding: Mapping[str, Any],
) -> dict[str, Any]:
    out = copy.deepcopy(dict(measurement))
    out.update(
        {
            "source_evidence_batch_hash": evidence_hash,
            "model_config_hash": trace.get("model_config_hash"),
            "code_sha": trace.get("code_commit_sha"),
            "v4_research_binding_hash": binding["binding_hash"],
            "v4_research_binding_schema": binding["schema"],
            "branch_plan_hash": row.get("branch_plan_hash") or trace.get("branch_plan_hash"),
            "pair_id": row.get("pair_id"),
            "replicate_index": row.get("replicate_index"),
            "condition_id": row.get("condition_id"),
            "pair_order_pattern": row.get("pair_order_pattern"),
            "execution_order": row.get("execution_order"),
            "experimental_variables": [_variable_record(binding, row["condition_id"])],
            "semantic_status": "NOT_ADJUDICATED",
        }
    )
    material = copy.deepcopy(out)
    material.pop("measurement_hash", None)
    out["measurement_hash"] = content_hash(material)
    return out


def _verify_source_freeze(
    *,
    traces_path: str | Path,
    evidence: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> None:
    evidence_hash = evidence.get("evidence_batch_hash")
    _require(isinstance(evidence_hash, str) and evidence_hash, "v4_derivation_evidence_batch_hash_required")
    expected_trace_sha = evidence.get("traces_sha256")
    _require(isinstance(expected_trace_sha, str) and expected_trace_sha, "v4_derivation_traces_sha256_required")
    _require(sha256_file(traces_path) == expected_trace_sha, "v4_derivation_frozen_traces_sha256_mismatch")
    evidence_code_sha = evidence.get("code_commit_sha")
    _require(evidence_code_sha == binding.get("code_sha"), "v4_derivation_evidence_code_sha_mismatch")


def derive_v4_bundle(
    *,
    plan_dir: str | Path,
    traces_path: str | Path,
    evidence_batch_path: str | Path,
) -> dict[str, Any]:
    plan_bundle = load_plan_bundle(plan_dir)
    plan = plan_bundle["plan"]
    code_sha = (plan.get("code_identity") or {}).get("branch_execution_commit")
    _require(isinstance(code_sha, str) and code_sha, "v4_derivation_plan_code_sha_required")
    binding = load_and_verify_v4_binding(plan_dir, plan_bundle, code_sha=code_sha)
    evidence = load_json(evidence_batch_path)
    _verify_source_freeze(traces_path=traces_path, evidence=evidence, binding=binding)
    evidence_hash = evidence["evidence_batch_hash"]
    traces = load_jsonl(traces_path)

    rows_by_run = {row["run_id"]: row for row in plan_bundle["branch_rows"]}
    _require(len(rows_by_run) == len(plan_bundle["branch_rows"]), "v4_derivation_duplicate_plan_run_id")
    _require(len({trace.get("run_id") for trace in traces}) == len(traces), "v4_derivation_duplicate_trace_run_id")

    measurements = []
    dynamics_views = []
    lineage_views = []
    packets = []
    run_index = []

    for trace in traces:
        run_id = trace.get("run_id")
        row = rows_by_run.get(run_id)
        _require(row is not None, f"v4_derivation_trace_not_in_plan:{run_id}")
        _require(trace.get("run_status") in VALID_TRACE_STATUSES, f"v4_derivation_unknown_run_status:{run_id}")
        branch = trace.get("experimental_branch") or {}
        _require(branch.get("branch_hash") == row.get("branch_hash"), f"v4_derivation_branch_hash_mismatch:{run_id}")
        _require(branch.get("parent_state_hash") == row.get("parent_state_hash"), f"v4_derivation_parent_state_hash_mismatch:{run_id}")
        _require(branch.get("branch_start_state_hash") == row.get("branch_start_state_hash"), f"v4_derivation_branch_start_hash_mismatch:{run_id}")
        _require(trace.get("branch_plan_hash") == plan["plan_hash"], f"v4_derivation_plan_hash_mismatch:{run_id}")
        _require(trace.get("v4_research_binding_hash") == binding["binding_hash"], f"v4_derivation_binding_hash_mismatch:{run_id}")
        _require(trace.get("code_commit_sha") == binding["code_sha"], f"v4_derivation_trace_code_sha_mismatch:{run_id}")
        _require(trace.get("model_config_hash") == (plan.get("model_identity") or {}).get("model_config_hash"), f"v4_derivation_model_hash_mismatch:{run_id}")

        branch_start_turn = branch.get("branch_start_turn")
        _require(isinstance(branch_start_turn, int) and branch_start_turn >= 0, f"v4_derivation_branch_start_turn_required:{run_id}")
        adapted = adapt_arena_trace_v03(trace)
        dynamics = build_system_dynamics_view(adapted, branch_start_turn=branch_start_turn)
        lineage = build_system_lineage_view(adapted, dynamics_view=dynamics)
        measurement = _enrich_measurement(
            lineage["system_trajectory_measurement"],
            trace=trace,
            row=row,
            evidence_hash=evidence_hash,
            binding=binding,
        )
        review_packets = build_bounded_review_packets(
            trace,
            adapted,
            dynamics,
            lineage,
            evidence_batch_hash=evidence_hash,
            v4_research_binding_hash=binding["binding_hash"],
        )

        dynamics_out = copy.deepcopy(dynamics)
        dynamics_out["source_evidence_batch_hash"] = evidence_hash
        dynamics_out["v4_research_binding_hash"] = binding["binding_hash"]
        dynamics_out["derived_measurement_hash"] = measurement["measurement_hash"]
        dynamics_out["dynamics_view_hash"] = content_hash(
            {key: value for key, value in dynamics_out.items() if key != "dynamics_view_hash"}
        )

        lineage_out = copy.deepcopy(lineage)
        lineage_out["source_evidence_batch_hash"] = evidence_hash
        lineage_out["v4_research_binding_hash"] = binding["binding_hash"]
        lineage_out["derived_measurement_hash"] = measurement["measurement_hash"]
        lineage_out["lineage_view_hash"] = content_hash(
            {key: value for key, value in lineage_out.items() if key != "lineage_view_hash"}
        )

        measurements.append(measurement)
        dynamics_views.append(dynamics_out)
        lineage_views.append(lineage_out)
        packets.extend(review_packets)
        run_index.append(
            {
                "run_id": run_id,
                "pair_id": row["pair_id"],
                "condition_id": row["condition_id"],
                "run_status": trace.get("run_status"),
                "measurement_hash": measurement["measurement_hash"],
                "jump_candidate_count": measurement["r2"].get("jump_candidate_count"),
                "source_backed_descendant_count": measurement["r3"].get("descendant_event_count"),
                "bounded_review_packet_count": len(review_packets),
                "semantic_status": "NOT_ADJUDICATED",
            }
        )

    summary = {
        "schema": SUMMARY_SCHEMA,
        "version": "0.1",
        "evidence_batch_hash": evidence_hash,
        "traces_sha256": evidence["traces_sha256"],
        "code_sha": binding["code_sha"],
        "branch_plan_hash": plan["plan_hash"],
        "v4_research_binding_hash": binding["binding_hash"],
        "v4_experimental_variable_id": binding["experimental_variable_id"],
        "preserved_trace_count": len(traces),
        "measurement_record_count": len(measurements),
        "dynamics_view_count": len(dynamics_views),
        "lineage_view_count": len(lineage_views),
        "bounded_review_packet_count": len(packets),
        "run_index": run_index,
        "measurement_v3_replaced": False,
        "automatic_paid_evaluator_called": False,
        "semantic_review": "DEFERRED_APPEND_ONLY",
        "C_P_R_status": "NOT_ADJUDICATED",
        "authority_penetration_status": "NOT_ADJUDICATED",
        "causal_effect_status": "NOT_ADJUDICATED",
        "scientific_status": "POST_FREEZE_STRUCTURAL_DERIVATION_FROM_SUBJECT_EVIDENCE",
        "warning": (
            "System Behavior v4 outputs are deterministic post-freeze derivations from the bound subject trace file. "
            "They do not replace Measurement v3 and do not by themselves establish C/P/R, semantic adoption, Authority Penetration, recovery, or causal effect."
        ),
    }
    summary["summary_hash"] = content_hash(summary)
    return {
        "measurements": measurements,
        "dynamics_views": dynamics_views,
        "lineage_views": lineage_views,
        "review_packets": packets,
        "summary": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-dir", required=True)
    parser.add_argument("--traces", required=True)
    parser.add_argument("--evidence-batch", required=True)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    bundle = derive_v4_bundle(
        plan_dir=args.plan_dir,
        traces_path=args.traces,
        evidence_batch_path=args.evidence_batch,
    )
    outdir = Path(args.outdir)
    if outdir.exists():
        raise ValueError("refusing_to_overwrite_branch_measurement_v4_outdir")
    outdir.mkdir(parents=True, exist_ok=False)
    write_jsonl(outdir / "trajectory_measurements_v4.jsonl", bundle["measurements"])
    write_jsonl(outdir / "system_dynamics_views_v4.jsonl", bundle["dynamics_views"])
    write_jsonl(outdir / "system_lineage_views_v4.jsonl", bundle["lineage_views"])
    write_jsonl(outdir / "bounded_review_packets_v4.jsonl", bundle["review_packets"])
    (outdir / "summary.json").write_text(
        json.dumps(bundle["summary"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"derived_v4_measurements={len(bundle['measurements'])} "
        f"review_packets={len(bundle['review_packets'])} "
        "semantic_review=DEFERRED_APPEND_ONLY paid_evaluator=NO measurement_v3_replaced=NO"
    )


if __name__ == "__main__":
    main()
