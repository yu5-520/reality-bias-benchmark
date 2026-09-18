#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .build_v5_whole_process_manifest import verify_manifest
from .core import stable_hash
from .cost_budget import BudgetedProvider, pricing_policy
from .engine import run_arena_once
from .io_utils import load_json, load_jsonl, sha256_file
from .journal import Journal
from .providers import provider_from_config

ROOT = Path(__file__).resolve().parents[1]
AUTH_PHRASE = "CALL_REAL_V5_WHOLE_PROCESS_API"


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def _write_json(path: Path, row) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_paid_gate(*, execute_real_api: bool, authorization_phrase: str,
                       per_run_max_calls: int, per_run_spending_ceiling: float,
                       global_spending_ceiling: float, run_count: int) -> None:
    if not execute_real_api or authorization_phrase != AUTH_PHRASE:
        raise SystemExit("Refusing provider calls: exact fresh Whole-Process authorization required.")
    if per_run_max_calls <= 0:
        raise SystemExit("positive per-run call cap required")
    if per_run_spending_ceiling <= 0 or global_spending_ceiling <= 0:
        raise SystemExit("positive spending ceilings required")
    if global_spending_ceiling < per_run_spending_ceiling * run_count:
        raise SystemExit("global ceiling must cover all symmetric per-run ceilings")


def _credential_check(model_config: dict) -> None:
    if model_config.get("provider") == "deepseek":
        if not os.environ.get("DEEPSEEK_API_KEY"):
            raise SystemExit("DEEPSEEK_API_KEY is not set")
        return
    raise SystemExit("unsupported v5 Whole-Process provider: " + str(model_config.get("provider")))


def _validate_manifest_bindings(rows: list[dict], provider_name: str) -> tuple[dict, dict]:
    verify_manifest(rows)
    first = rows[0]
    model = load_json(ROOT / first["model_config_path"])
    design = load_json(ROOT / first["batch_design_path"])
    if design.get("status") != "FROZEN_DESIGN_CANDIDATE_NOT_PROVIDER_AUTHORIZED":
        raise ValueError("v5_batch_design_status_invalid")
    if design.get("paid_subject_execution_authorized") is not False:
        raise ValueError("v5_design_file_must_remain_non_authorizing")
    if model.get("provider") != provider_name:
        raise ValueError("v5_provider_mismatch")
    for row in rows:
        for path_key, hash_key in (
            ("batch_design_path", "batch_design_hash"),
            ("arena_config_path", "arena_config_hash"),
            ("model_config_path", "model_config_hash"),
            ("theory_contract_path", "theory_contract_hash"),
            ("measurement_contract_path", "measurement_contract_hash"),
            ("scout_config_path", "scout_config_hash"),
            ("experiment_profile_path", "experiment_profile_hash"),
        ):
            if sha256_file(ROOT / row[path_key]) != row[hash_key]:
                raise ValueError("v5_manifest_binding_hash_mismatch:" + hash_key)
        if row.get("automatic_paid_evaluator") is not False:
            raise ValueError("v5_automatic_evaluator_forbidden")
        if row.get("no_outcome_aware_rerun") is not True:
            raise ValueError("v5_no_outcome_rerun_required")
    return design, model


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--provider", required=True)
    ap.add_argument("--per-run-max-calls", required=True, type=int)
    ap.add_argument("--per-run-spending-ceiling", required=True, type=float)
    ap.add_argument("--global-spending-ceiling", required=True, type=float)
    ap.add_argument("--currency", default="USD")
    ap.add_argument("--authorization-phrase", required=True)
    ap.add_argument("--execute-real-api", action="store_true")
    args = ap.parse_args()

    rows = load_jsonl(args.manifest)
    design, model_config = _validate_manifest_bindings(rows, args.provider)
    validate_paid_gate(
        execute_real_api=args.execute_real_api,
        authorization_phrase=args.authorization_phrase,
        per_run_max_calls=args.per_run_max_calls,
        per_run_spending_ceiling=args.per_run_spending_ceiling,
        global_spending_ceiling=args.global_spending_ceiling,
        run_count=len(rows),
    )
    _credential_check(model_config)

    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_v5_whole_process_output")
    out.mkdir(parents=True)

    first = rows[0]
    auth = {
        "schema": "RB-V5-WHOLE-PROCESS-PAID-AUTHORIZATION-v0.1",
        "batch_id": design["batch_id"],
        "authorization_phrase": args.authorization_phrase,
        "provider": args.provider,
        "run_count": len(rows),
        "per_run_max_calls": args.per_run_max_calls,
        "per_run_spending_ceiling": args.per_run_spending_ceiling,
        "global_spending_ceiling": args.global_spending_ceiling,
        "currency": args.currency.upper(),
        "pricing_policy": pricing_policy(model_config),
        "manifest_sha256": sha256_file(args.manifest),
        "batch_design_hash": first["batch_design_hash"],
        "arena_config_hash": first["arena_config_hash"],
        "model_config_hash": first["model_config_hash"],
        "theory_contract_hash": first["theory_contract_hash"],
        "measurement_contract_hash": first["measurement_contract_hash"],
        "scout_config_hash": first["scout_config_hash"],
        "experiment_profile_hash": first["experiment_profile_hash"],
        "code_commit_sha": first["code_commit_sha"],
        "automatic_paid_evaluator": False,
        "driver_probe_authorized": False,
        "active_recovery_authorized": False,
        "no_outcome_aware_rerun": True,
    }
    auth["authorization_hash"] = stable_hash(auth)
    _write_json(out / "authorization_record.json", auth)

    upstream = provider_from_config(model_config)
    total_estimated_spend = 0.0
    traces_path = out / "traces.jsonl"
    errors = []

    for row in rows:
        provider = BudgetedProvider(
            upstream, model_config,
            spending_ceiling=args.per_run_spending_ceiling,
            currency=args.currency,
            max_calls=args.per_run_max_calls,
        )
        snapshots = []
        snapshot_path = out / "snapshots" / f"{row['run_id']}.jsonl"
        journal_path = out / "journals" / (stable_hash({"run_id": row["run_id"]})[:20] + ".jsonl")

        def save_snapshot(snapshot):
            snapshots.append(snapshot)
            _append_jsonl(snapshot_path, snapshot)

        try:
            domain = load_json(ROOT / f"arena/domains/{row['domain_id']}.json")
            arena_config = load_json(ROOT / row["arena_config_path"])
            with Journal(journal_path) as journal:
                trace = run_arena_once(
                    domain, arena_config, provider,
                    row["run_id"], row["logical_seed"],
                    recorder=journal,
                    state_snapshot_callback=save_snapshot,
                )
            trace.update({
                "v5_whole_process": True,
                "batch_id": row["batch_id"],
                "trial": row["trial"],
                "subject_condition": row["subject_condition"],
                "code_commit_sha": row["code_commit_sha"],
                "batch_design_hash": row["batch_design_hash"],
                "arena_config_hash": row["arena_config_hash"],
                "model_config_hash": row["model_config_hash"],
                "theory_contract_hash": row["theory_contract_hash"],
                "measurement_contract_hash": row["measurement_contract_hash"],
                "scout_config_hash": row["scout_config_hash"],
                "experiment_profile_hash": row["experiment_profile_hash"],
                "provider": args.provider,
                "authorization_hash": auth["authorization_hash"],
                "snapshot_count": len(snapshots),
                "review_status": "PENDING_LOCALIZED_SEMANTIC_AUDIT",
                "semantic_status": "NOT_ADJUDICATED",
                "driver_probe_called": False,
                "active_recovery_called": False,
                "automatic_paid_evaluator_called": False,
            })
            _append_jsonl(traces_path, trace)
            total_estimated_spend += float(provider.estimated_spend)
        except Exception as err:
            error = {"run_id": row["run_id"], "error": repr(err), "snapshot_count_preserved": len(snapshots)}
            errors.append(error)
            _append_jsonl(out / "errors.jsonl", error)

    preserved = len(load_jsonl(traces_path)) if traces_path.exists() else 0
    summary = {
        "schema": "RB-V5-WHOLE-PROCESS-RUN-SUMMARY-v0.1",
        "batch_id": design["batch_id"],
        "planned_run_count": len(rows),
        "preserved_trace_count": preserved,
        "runner_error_count": len(errors),
        "estimated_total_spend": total_estimated_spend,
        "currency": args.currency.upper(),
        "per_run_max_calls": args.per_run_max_calls,
        "per_run_spending_ceiling": args.per_run_spending_ceiling,
        "global_spending_ceiling": args.global_spending_ceiling,
        "automatic_paid_evaluator_called": False,
        "driver_probe_called": False,
        "active_recovery_called": False,
        "outcome_aware_rerun_count": 0,
        "semantic_status": "NOT_ADJUDICATED",
    }
    summary["summary_hash"] = stable_hash(summary)
    _write_json(out / "summary.json", summary)
    _write_json(out / "errors.json", errors)
    if errors:
        raise SystemExit("v5 Whole-Process collection contains runner errors; preserved all available raw evidence")

    print("V5_WHOLE_PROCESS_SUBJECT_COLLECTION_COMPLETE")
    print("PAID_EVALUATOR_CALLED=NO")
    print("DRIVER_PROBE_CALLED=NO")
    print("ACTIVE_RECOVERY_CALLED=NO")


if __name__ == "__main__":
    main()
