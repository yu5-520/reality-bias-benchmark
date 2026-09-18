#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path

from .alr_recovery import AuthorityLocalizedEnvelopeTransform
from .core import stable_hash
from .cost_budget import BudgetedProvider
from .engine import run_arena_once
from .io_utils import load_json, sha256_file
from .one_shot_intervention import OneShotRuntimeViewTransform
from .persistent_field_intervention import PersistentFieldRuntimeViewTransform
from .providers import provider_from_config
from .r7_runtime_smoke import load_r7_plan_bundle
from .r7_semantic_repair_runtime import build_semantic_repair_runtime_plan, verify_semantic_repair_trace

AUTH_PHRASE = "CALL_REAL_R7_THREE_ARM_API"
RUN_SCHEMA = "RB-R7-THREE-ARM-REAL-RUN-v0.1"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def _write_json(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _credential_check(model_config: dict) -> None:
    provider = model_config.get("provider")
    if provider == "deepseek":
        if not os.environ.get("DEEPSEEK_API_KEY"):
            raise SystemExit("DEEPSEEK_API_KEY is not set")
        return
    if provider == "alibaba_cloud_bailian_business_space":
        if not os.environ.get(model_config.get("credential_env", "BAI")):
            raise SystemExit("Bailian credential is not set")
        return
    raise SystemExit("unsupported provider: " + str(provider))


def _safe_file_id(run_id: str) -> str:
    return stable_hash({"run_id": run_id})[:20]


def validate_symmetric_limits(*, row_count: int, per_branch_max_calls: int, per_branch_spending_ceiling: float, global_spending_ceiling: float) -> bool:
    _require(isinstance(row_count, int) and row_count > 0, "positive_r7_branch_row_count_required")
    _require(per_branch_max_calls > 0, "positive_r7_per_branch_call_cap_required")
    _require(per_branch_spending_ceiling > 0, "positive_r7_per_branch_spending_ceiling_required")
    _require(global_spending_ceiling > 0, "positive_r7_global_spending_ceiling_required")
    _require(
        global_spending_ceiling >= per_branch_spending_ceiling * row_count,
        "r7_global_ceiling_must_cover_all_symmetric_per_branch_ceilings",
    )
    return True


def validate_execution_bindings(*, bundle: dict, source_r5_plan_dir: str | Path, model_config_path: str, provider_name: str, execution_code_sha: str) -> dict:
    plan = bundle["plan"]
    source_r5_plan = load_json(Path(source_r5_plan_dir) / "branch_plan.json")
    _require(source_r5_plan.get("plan_hash") == plan["source_binding"]["source_r5_plan_hash"], "r7_source_r5_plan_hash_mismatch")
    _require(plan.get("real_three_arm_runtime_mechanisms_ready") is True, "r7_runtime_mechanisms_not_ready")
    _require(plan.get("real_subject_execution_authorized") is False, "r7_prepared_plan_must_not_self_authorize")
    _require(plan.get("paid_subject_authorization_status") == "NOT_AUTHORIZED", "r7_paid_gate_must_remain_external")
    _require(plan.get("semantic_cpr_status") == "NOT_ADJUDICATED", "r7_semantic_status_must_be_deferred")
    _require(plan.get("code_identity", {}).get("r7_plan_code_sha") == execution_code_sha, "r7_execution_code_sha_mismatch")

    model_identity = source_r5_plan.get("model_identity") or {}
    config_identity = source_r5_plan.get("config_identity") or {}
    model_config = load_json(model_config_path)
    _require(model_config.get("provider") == provider_name, "r7_provider_model_config_mismatch")
    _require(model_identity.get("provider") == provider_name, "r7_provider_source_plan_mismatch")
    _require(sha256_file(model_config_path) == model_identity.get("model_config_hash"), "r7_model_config_hash_mismatch")

    arena_path = config_identity.get("arena_config_path")
    _require(isinstance(arena_path, str) and arena_path, "r7_source_arena_config_path_missing")
    _require(sha256_file(arena_path) == config_identity.get("arena_config_hash"), "r7_source_arena_config_hash_mismatch")
    domain_id = config_identity.get("domain_id")
    domain_path = Path("arena/domains") / f"{domain_id}.json"
    _require(domain_path.exists(), "r7_domain_file_missing")
    _require(sha256_file(domain_path) == config_identity.get("domain_hash"), "r7_domain_hash_mismatch")
    domain = load_json(domain_path)
    _require(stable_hash(domain.get("task")) == config_identity.get("task_hash"), "r7_task_hash_mismatch")
    _require(stable_hash(domain.get("agents")) == config_identity.get("agent_registry_hash"), "r7_agent_registry_hash_mismatch")

    bounded = bundle["bounded_arena_config"]
    _require(int(bounded["max_turns"]) == int(plan["source_binding"]["absolute_turn_cap"]), "r7_bounded_turn_cap_mismatch")
    _require((bounded.get("r7_observation_horizon") or {}).get("horizon_id") == plan["matched_horizon"]["horizon_id"], "r7_bounded_horizon_id_mismatch")
    return {
        "model_config": model_config,
        "domain": domain,
        "domain_path": str(domain_path),
        "source_r5_plan": source_r5_plan,
    }


def _manifest_by_row(bundle: dict) -> dict[str, dict]:
    manifests = {row["manifest_hash"]: row for row in bundle["arm_manifests"]}
    for row in bundle["execution_rows"]:
        _require(row["manifest_hash"] in manifests, "r7_execution_row_manifest_missing")
    return manifests


def _revision_lineage(bundle: dict, trace: dict, transform: AuthorityLocalizedEnvelopeTransform) -> dict | None:
    if transform.transformed_count != 1:
        return None
    row = {
        "schema": "RB-R7-C3-REVISION-LINEAGE-v0.1",
        "common_reference_parent_state_hash": bundle["source_parent_snapshot"]["state_hash"],
        "recovery_checkpoint_state_hash": bundle["c3_recovery_checkpoint"]["state_hash"],
        "semantic_payload_hash": bundle["c3_alr_binding"]["semantic_payload_hash"],
        "reopened_source_event_range": bundle["c3_alr_binding"]["reopened_source_event_range"],
        "authority_transform_hashes": transform.summary()["transform_hashes"],
        "result_trace_hash_before_revision_record": stable_hash(trace),
        "provider_internal_state_replayed": False,
    }
    row["revision_hash"] = stable_hash(row)
    return row


def execute_real_batch(*, bundle: dict, bindings: dict, upstream, outdir: Path, per_branch_max_calls: int, per_branch_spending_ceiling: float, global_spending_ceiling: float, currency: str, execution_code_sha: str) -> dict:
    if outdir.exists():
        raise ValueError("refusing_to_overwrite_r7_real_output_dir")
    outdir.mkdir(parents=True)
    traces_path = outdir / "traces.jsonl"
    errors_path = outdir / "errors.jsonl"
    journals_dir = outdir / "journals"
    manifests = _manifest_by_row(bundle)
    parent_hash_before = stable_hash(bundle["source_parent_snapshot"])
    checkpoint_hash_before = stable_hash(bundle["c3_recovery_checkpoint"])
    total_estimated_spend = 0.0
    completed = 0
    censored = 0
    failed = 0
    branch_summaries = []

    ordered_rows = sorted(bundle["execution_rows"], key=lambda row: (int(row["replicate_index"]), int(row["execution_order"])))
    for row in ordered_rows:
        if total_estimated_spend >= global_spending_ceiling:
            error = {
                "run_id": row["run_id"],
                "arm_id": row["arm_id"],
                "error": "global_spending_ceiling_reached_before_branch",
                "global_estimated_spend": total_estimated_spend,
            }
            _append_jsonl(errors_path, error)
            failed += 1
            continue

        manifest = manifests[row["manifest_hash"]]
        arm_id = row["arm_id"]
        start = bundle["source_parent_snapshot"] if arm_id in ("C1_ONE_SHOT", "C2_PERSISTENT_FIELD") else bundle["c3_recovery_checkpoint"]
        runtime_transform = None
        action_transform = None
        semantic_repair_runtime_plan = None
        if arm_id == "C1_ONE_SHOT":
            runtime_transform = OneShotRuntimeViewTransform(bundle["c1_one_shot_envelope"])
        elif arm_id == "C2_PERSISTENT_FIELD":
            runtime_transform = PersistentFieldRuntimeViewTransform(bundle["c2_persistent_field_envelope"])
        elif arm_id == "C3_ALR":
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
            semantic_repair_runtime_plan = build_semantic_repair_runtime_plan(
                packet=bundle["semantic_repair_packet"],
                gate=bundle["lineage_completeness_gate"],
                bundle=bundle,
            )
        else:
            raise ValueError("unknown_r7_arm:" + str(arm_id))

        provider = BudgetedProvider(
            upstream,
            bindings["model_config"],
            spending_ceiling=per_branch_spending_ceiling,
            currency=currency,
            max_calls=per_branch_max_calls,
        )
        from .journal import Journal
        journal_path = journals_dir / (_safe_file_id(row["run_id"]) + ".jsonl")
        execution_binding = {
            "schema": "RB-R7-EXECUTION-BINDING-v0.1",
            "run_id": row["run_id"],
            "arm_id": arm_id,
            "triad_id": row["triad_id"],
            "replicate_index": row["replicate_index"],
            "manifest_hash": manifest["manifest_hash"],
            "plan_hash": bundle["plan"]["plan_hash"],
            "common_reference_parent_state_hash": bundle["source_parent_snapshot"]["state_hash"],
            "branch_start_state_hash": start["state_hash"],
            "semantic_payload_hash": manifest["semantic_payload_hash"],
            "observation_horizon_id": manifest["observation_horizon_id"],
            "execution_code_sha": execution_code_sha,
            "provider_internal_state_replayed": False,
            "bound_before_first_provider_call": True,
        }
        execution_binding["binding_hash"] = stable_hash(execution_binding)

        with Journal(journal_path) as journal:
            journal({"record_type": "r7_execution_binding", "record": execution_binding})
            trace = run_arena_once(
                copy.deepcopy(bindings["domain"]),
                copy.deepcopy(bundle["bounded_arena_config"]),
                provider,
                row["run_id"],
                logical_seed=row["replicate_index"],
                recorder=journal,
                initial_state_snapshot=start,
                runtime_view_transform=runtime_transform,
                action_envelope_transform=action_transform,
            )

        if stable_hash(bundle["source_parent_snapshot"]) != parent_hash_before:
            raise ValueError("r7_common_reference_parent_mutated")
        if stable_hash(bundle["c3_recovery_checkpoint"]) != checkpoint_hash_before:
            raise ValueError("r7_recovery_checkpoint_mutated")

        condition_status = "OBSERVED"
        transform_summary = {}
        if arm_id == "C1_ONE_SHOT":
            if runtime_transform.delivered_count == 1:
                runtime_transform.verify_finished()
            else:
                condition_status = "C1_EXPOSURE_NOT_REALIZED"
            transform_summary = runtime_transform.summary()
        elif arm_id == "C2_PERSISTENT_FIELD":
            if runtime_transform.delivered_count >= 1:
                runtime_transform.verify_finished(require_horizon_exhausted=False)
            else:
                condition_status = "C2_EXPOSURE_NOT_REALIZED"
            transform_summary = runtime_transform.summary()
        else:
            transform_summary = action_transform.summary()
            if action_transform.transformed_count == 1:
                action_transform.verify_finished()
            else:
                condition_status = "C3_J0_REPRODUCTION_NOT_OBSERVED"

        trace["r7_condition"] = {
            "schema": "RB-R7-CONDITION-TRACE-v0.1",
            "arm_id": arm_id,
            "triad_id": row["triad_id"],
            "replicate_index": row["replicate_index"],
            "execution_order": row["execution_order"],
            "manifest_hash": manifest["manifest_hash"],
            "condition_status": condition_status,
            "common_reference_parent_state_hash": bundle["source_parent_snapshot"]["state_hash"],
            "branch_start_state_hash": start["state_hash"],
            "semantic_payload_hash": manifest["semantic_payload_hash"],
            "observation_horizon_id": manifest["observation_horizon_id"],
            "transform_summary": transform_summary,
            "provider_internal_state_replayed": False,
            "semantic_cpr_status": "NOT_ADJUDICATED",
            "terminal_outcome_is_primary": False,
        }
        if arm_id == "C3_ALR":
            revision = _revision_lineage(bundle, trace, action_transform)
            if revision is not None:
                trace["r7_revision_lineage"] = revision
            if condition_status == "OBSERVED":
                repair_verification = verify_semantic_repair_trace(
                    trace=trace,
                    plan=semantic_repair_runtime_plan,
                    transform_summary=action_transform.summary(),
                )
                trace["r7_semantic_repair_runtime_plan"] = semantic_repair_runtime_plan
                trace["r7_semantic_repair_verification"] = repair_verification
                trace["r7_condition"]["semantic_repair_packet_hash"] = semantic_repair_runtime_plan["packet_hash"]
                trace["r7_condition"]["semantic_repair_runtime_plan_hash"] = semantic_repair_runtime_plan["plan_hash"]
                trace["r7_condition"]["semantic_repair_verification_hash"] = repair_verification["verification_hash"]
                trace["r7_condition"]["old_lineage_reentry_detected"] = repair_verification["old_lineage_reentry_detected"]
                trace["r7_condition"]["preserved_unrelated_structure"] = repair_verification["preserved_unrelated_structure"]

        budget_summary = provider.summary()
        trace["r7_budget_summary"] = budget_summary
        total_estimated_spend += float(budget_summary["estimated_spend"])
        _append_jsonl(traces_path, trace)
        branch_summary = {
            "run_id": row["run_id"],
            "arm_id": arm_id,
            "condition_status": condition_status,
            "run_status": trace["run_status"],
            "turns": trace["turns"],
            "estimated_spend": budget_summary["estimated_spend"],
            "calls_started": budget_summary["calls_started"],
            "calls_completed": budget_summary["calls_completed"],
        }
        if arm_id == "C3_ALR" and trace.get("r7_semantic_repair_verification"):
            v = trace["r7_semantic_repair_verification"]
            branch_summary.update({
                "semantic_repair_packet_consumed": True,
                "semantic_repair_verification_hash": v["verification_hash"],
                "old_lineage_reentry_detected": v["old_lineage_reentry_detected"],
                "preserved_unrelated_structure": v["preserved_unrelated_structure"],
                "recomputed_descendant_count": len(v["recomputed_descendant_refs"]),
            })
        branch_summaries.append(branch_summary)
        if trace["run_status"] == "RUN_COMPLETE":
            completed += 1
        elif trace["run_status"] == "BUDGET_CENSORED" or condition_status != "OBSERVED":
            censored += 1
        else:
            failed += 1

    summary = {
        "schema": RUN_SCHEMA,
        "plan_hash": bundle["plan"]["plan_hash"],
        "execution_code_sha": execution_code_sha,
        "branch_count": len(ordered_rows),
        "trace_count": len(branch_summaries),
        "run_complete_count": completed,
        "censored_or_nonrealized_count": censored,
        "failed_count": failed,
        "estimated_total_spend": total_estimated_spend,
        "currency": currency,
        "global_spending_ceiling": global_spending_ceiling,
        "automatic_paid_evaluator": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "provider_internal_state_replayed": False,
        "semantic_repair_packet_hash": bundle["semantic_repair_packet"].get("packet_hash"),
        "lineage_completeness_gate_hash": bundle["lineage_completeness_gate"].get("gate_hash"),
        "branch_summaries": branch_summaries,
        "interpretation_boundary": "Subject traces are raw process evidence. Semantic CPR adjudication and structural causal interpretation remain deferred until raw evidence is frozen.",
    }
    summary["summary_hash"] = stable_hash(summary)
    _write_json(outdir / "run_summary.json", summary)
    if not errors_path.exists():
        errors_path.write_text("", encoding="utf-8")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan-dir", required=True)
    ap.add_argument("--source-r5-plan-dir", required=True)
    ap.add_argument("--outdir")
    ap.add_argument("--model-config", required=True)
    ap.add_argument("--provider", required=True)
    ap.add_argument("--execution-code-sha", required=True)
    ap.add_argument("--per-branch-max-calls", type=int, required=True)
    ap.add_argument("--per-branch-spending-ceiling", type=float, required=True)
    ap.add_argument("--global-spending-ceiling", type=float, required=True)
    ap.add_argument("--currency", default="USD")
    ap.add_argument("--authorization-phrase")
    ap.add_argument("--execute-real-api", action="store_true")
    ap.add_argument("--preflight-only", action="store_true")
    args = ap.parse_args()

    if args.preflight_only and args.execute_real_api:
        raise SystemExit("preflight_only_and_execute_real_api_are_mutually_exclusive")
    bundle = load_r7_plan_bundle(args.plan_dir)
    row_count = len(bundle["execution_rows"])
    validate_symmetric_limits(
        row_count=row_count,
        per_branch_max_calls=args.per_branch_max_calls,
        per_branch_spending_ceiling=args.per_branch_spending_ceiling,
        global_spending_ceiling=args.global_spending_ceiling,
    )
    bindings = validate_execution_bindings(
        bundle=bundle,
        source_r5_plan_dir=args.source_r5_plan_dir,
        model_config_path=args.model_config,
        provider_name=args.provider,
        execution_code_sha=args.execution_code_sha,
    )

    if args.preflight_only:
        print("R7_THREE_ARM_REAL_PREFLIGHT=PASS")
        print("PLAN_HASH=" + bundle["plan"]["plan_hash"])
        print("EXECUTION_CODE_SHA=" + args.execution_code_sha)
        print("BRANCH_COUNT=" + str(row_count))
        print("C1_RUNTIME=READY")
        print("C2_RUNTIME=READY")
        print("C3_RUNTIME=READY")
        print("PAID_API_CALLED=NO")
        return

    if not args.execute_real_api or args.authorization_phrase != AUTH_PHRASE:
        raise SystemExit("Refusing provider calls: exact R7 three-arm authorization required.")
    if not args.outdir:
        raise SystemExit("outdir_required_for_real_r7_execution")
    _credential_check(bindings["model_config"])
    upstream = provider_from_config(bindings["model_config"])
    summary = execute_real_batch(
        bundle=bundle,
        bindings=bindings,
        upstream=upstream,
        outdir=Path(args.outdir),
        per_branch_max_calls=args.per_branch_max_calls,
        per_branch_spending_ceiling=args.per_branch_spending_ceiling,
        global_spending_ceiling=args.global_spending_ceiling,
        currency=args.currency,
        execution_code_sha=args.execution_code_sha,
    )
    print("R7_THREE_ARM_SUBJECT_RUN=COMPLETE")
    print("TRACE_COUNT=" + str(summary["trace_count"]))
    print("ESTIMATED_TOTAL_SPEND=" + str(summary["estimated_total_spend"]))
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
