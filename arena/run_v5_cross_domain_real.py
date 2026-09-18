#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from .build_v5_cross_domain_manifest import verify_manifest
from .core import stable_hash
from .cost_budget import BudgetedProvider, pricing_policy
from .engine import run_arena_once
from .io_utils import load_json, load_jsonl, sha256_file
from .journal import Journal
from .providers import provider_from_config

ROOT = Path(__file__).resolve().parents[1]
AUTH_PHRASE = "CALL_REAL_V5_CROSS_DOMAIN_FIRST_ROUND_API"


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
                       global_spending_ceiling: float, selected_run_count: int) -> None:
    if not execute_real_api or authorization_phrase != AUTH_PHRASE:
        raise SystemExit("Refusing provider calls: exact cross-domain first-round authorization required.")
    if per_run_max_calls <= 0:
        raise SystemExit("positive per-run call cap required")
    if per_run_spending_ceiling <= 0 or global_spending_ceiling <= 0:
        raise SystemExit("positive spending ceilings required")
    required_global = per_run_spending_ceiling * selected_run_count
    if global_spending_ceiling + 1e-12 < required_global:
        raise SystemExit("global ceiling must cover all selected symmetric per-run ceilings")


def _credential_check(model_config: dict) -> None:
    if model_config.get("provider") == "deepseek":
        if not os.environ.get("DEEPSEEK_API_KEY"):
            raise SystemExit("DEEPSEEK_API_KEY is not set")
        return
    raise SystemExit("unsupported cross-domain provider: " + str(model_config.get("provider")))


def _validate_bindings(rows: list[dict], *, provider_name: str, expected_execution_sha: str) -> tuple[dict, dict]:
    verify_manifest(rows)
    first = rows[0]
    plan = load_json(ROOT / first["plan_path"])
    model = load_json(ROOT / first["model_config_path"])

    if first["code_commit_sha"] != expected_execution_sha:
        raise ValueError("cross_domain_execution_sha_mismatch")
    if any(row["code_commit_sha"] != expected_execution_sha for row in rows):
        raise ValueError("cross_domain_manifest_mixed_execution_sha")
    if sha256_file(ROOT / first["plan_path"]) != first["plan_hash"]:
        raise ValueError("cross_domain_plan_hash_mismatch")
    if model.get("provider") != provider_name:
        raise ValueError("cross_domain_provider_mismatch")

    for row in rows:
        for path_key, hash_key in (
            ("arena_config_path", "arena_config_hash"),
            ("model_config_path", "model_config_hash"),
            ("theory_contract_path", "theory_contract_hash"),
            ("measurement_contract_path", "measurement_contract_hash"),
            ("scout_config_path", "scout_config_hash"),
            ("experiment_profile_path", "experiment_profile_hash"),
        ):
            if sha256_file(ROOT / row[path_key]) != row[hash_key]:
                raise ValueError("cross_domain_binding_hash_mismatch:" + hash_key)
        domain_path = ROOT / f"arena/domains/{row['domain_id']}.json"
        if sha256_file(domain_path) != row["domain_hash"]:
            raise ValueError("cross_domain_fixture_hash_mismatch:" + row["domain_id"])
        domain = load_json(domain_path)
        if stable_hash(domain["task"]) != row["task_hash"]:
            raise ValueError("cross_domain_task_hash_mismatch:" + row["domain_id"])
        if stable_hash(domain["agents"]) != row["agent_pool_hash"]:
            raise ValueError("cross_domain_agent_pool_hash_mismatch:" + row["domain_id"])
    return plan, model


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--wave-id", required=True, type=int)
    ap.add_argument("--expected-execution-sha", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--provider", required=True)
    ap.add_argument("--per-run-max-calls", required=True, type=int)
    ap.add_argument("--per-run-spending-ceiling", required=True, type=float)
    ap.add_argument("--global-spending-ceiling", required=True, type=float)
    ap.add_argument("--currency", default="USD")
    ap.add_argument("--authorization-phrase", required=True)
    ap.add_argument("--execute-real-api", action="store_true")
    args = ap.parse_args()

    all_rows = load_jsonl(args.manifest)
    plan, model_config = _validate_bindings(
        all_rows,
        provider_name=args.provider,
        expected_execution_sha=args.expected_execution_sha,
    )

    if args.wave_id < 1 or args.wave_id > int(plan["wave_count"]):
        raise ValueError("cross_domain_wave_id_out_of_range")
    rows = [row for row in all_rows if row["wave_id"] == args.wave_id]
    expected_selected = int(plan["wave_size_per_domain"]) * len(plan["domains"])
    if len(rows) != expected_selected:
        raise ValueError("cross_domain_selected_wave_run_count_mismatch")
    selected_domain_counts = Counter(row["domain_id"] for row in rows)
    if any(selected_domain_counts[row["domain_id"]] != int(plan["wave_size_per_domain"]) for row in plan["domains"]):
        raise ValueError("cross_domain_selected_wave_not_balanced")

    validate_paid_gate(
        execute_real_api=args.execute_real_api,
        authorization_phrase=args.authorization_phrase,
        per_run_max_calls=args.per_run_max_calls,
        per_run_spending_ceiling=args.per_run_spending_ceiling,
        global_spending_ceiling=args.global_spending_ceiling,
        selected_run_count=len(rows),
    )
    _credential_check(model_config)

    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_cross_domain_output")
    out.mkdir(parents=True)

    auth = {
        "schema": "RB-V5-CROSS-DOMAIN-PAID-AUTHORIZATION-v0.1",
        "first_round_id": plan["first_round_id"],
        "authorization_phrase": args.authorization_phrase,
        "provider": args.provider,
        "selected_wave_id": args.wave_id,
        "selected_run_count": len(rows),
        "selected_domain_counts": dict(sorted(selected_domain_counts.items())),
        "per_run_max_calls": args.per_run_max_calls,
        "per_run_spending_ceiling": args.per_run_spending_ceiling,
        "global_spending_ceiling": args.global_spending_ceiling,
        "currency": args.currency.upper(),
        "pricing_policy": pricing_policy(model_config),
        "manifest_sha256": sha256_file(args.manifest),
        "plan_hash": all_rows[0]["plan_hash"],
        "code_commit_sha": args.expected_execution_sha,
        "automatic_paid_evaluator": False,
        "driver_probe_authorized": False,
        "active_recovery_authorized": False,
        "no_outcome_aware_rerun": True,
    }
    auth["authorization_hash"] = stable_hash(auth)
    _write_json(out / "authorization_record.json", auth)

    upstream = provider_from_config(model_config)
    traces_path = out / "traces.jsonl"
    traces_path.touch()
    errors = []
    spend_by_domain: dict[str, float] = defaultdict(float)

    for row in rows:
        provider = BudgetedProvider(
            upstream,
            model_config,
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
                    domain,
                    arena_config,
                    provider,
                    row["run_id"],
                    row["logical_seed"],
                    recorder=journal,
                    state_snapshot_callback=save_snapshot,
                )
            trace.update({
                "v5_cross_domain_first_round": True,
                "first_round_id": row["first_round_id"],
                "domain_id": row["domain_id"],
                "cohort_role": row["cohort_role"],
                "trial": row["trial"],
                "wave_id": row["wave_id"],
                "subject_condition": row["subject_condition"],
                "code_commit_sha": row["code_commit_sha"],
                "plan_hash": row["plan_hash"],
                "domain_hash": row["domain_hash"],
                "task_hash": row["task_hash"],
                "agent_pool_hash": row["agent_pool_hash"],
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
            spend_by_domain[row["domain_id"]] += float(provider.estimated_spend)
        except Exception as err:
            error = {
                "run_id": row["run_id"],
                "domain_id": row["domain_id"],
                "wave_id": row["wave_id"],
                "error": repr(err),
                "snapshot_count_preserved": len(snapshots),
            }
            errors.append(error)
            _append_jsonl(out / "errors.jsonl", error)

    preserved_traces = load_jsonl(traces_path) if traces_path.exists() else []
    preserved_domain_counts = Counter(trace.get("domain_id") for trace in preserved_traces)
    summary = {
        "schema": "RB-V5-CROSS-DOMAIN-RUN-SUMMARY-v0.1",
        "first_round_id": plan["first_round_id"],
        "selected_wave_id": args.wave_id,
        "planned_selected_run_count": len(rows),
        "selected_domain_counts": dict(sorted(selected_domain_counts.items())),
        "preserved_trace_count": len(preserved_traces),
        "preserved_domain_counts": dict(sorted(preserved_domain_counts.items())),
        "runner_error_count": len(errors),
        "estimated_spend_by_domain": dict(sorted(spend_by_domain.items())),
        "estimated_total_spend": sum(spend_by_domain.values()),
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
        raise SystemExit("cross-domain wave contains runner errors; preserved all available raw evidence")

    print("V5_CROSS_DOMAIN_SUBJECT_WAVE_COMPLETE")
    print("WAVE_ID=" + str(args.wave_id))
    print("PRESERVED_TRACE_COUNT=" + str(len(preserved_traces)))
    print("PAID_EVALUATOR_CALLED=NO")
    print("DRIVER_PROBE_CALLED=NO")
    print("ACTIVE_RECOVERY_CALLED=NO")


if __name__ == "__main__":
    main()
