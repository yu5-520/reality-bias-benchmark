#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from collections import Counter
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, sha256_file, write_jsonl

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "RB-V5-CROSS-DOMAIN-SUBJECT-MANIFEST-v0.1"
STATUS = "V5_CROSS_DOMAIN_SUBJECT_CANDIDATE_AWAITING_EXPLICIT_PAID_AUTHORIZATION"


def _shared_bindings(plan: dict, plan_path: str, code_sha: str) -> dict:
    arena_path = ROOT / plan["arena_config_path"]
    model_path = ROOT / plan["model_config_path"]
    theory_path = ROOT / plan["theory_contract_path"]
    measurement_path = ROOT / plan["measurement_contract_path"]
    scout_path = ROOT / plan["scout_config_path"]
    profile_path = ROOT / plan["experiment_profile_path"]
    arena = load_json(arena_path)
    model = load_json(model_path)

    if plan.get("status") != "FROZEN_PROTOCOL_CANDIDATE_NOT_PROVIDER_AUTHORIZED":
        raise ValueError("cross_domain_plan_status_invalid")
    if plan.get("paid_subject_execution_authorized") is not False:
        raise ValueError("cross_domain_plan_must_not_authorize_paid_subject")
    if plan.get("active_probe_authorized") is not False or plan.get("active_repair_authorized") is not False:
        raise ValueError("cross_domain_plan_must_not_authorize_probe_or_repair")
    if plan.get("subject_condition") != "NATURAL_UNMANIPULATED":
        raise ValueError("cross_domain_natural_subject_condition_required")
    if model.get("provider") != "deepseek":
        raise ValueError("cross_domain_provider_binding_changed")

    domains = plan.get("domains") or []
    domain_ids = [row.get("domain_id") for row in domains]
    if len(domain_ids) != 4 or len(set(domain_ids)) != 4:
        raise ValueError("cross_domain_exact_four_unique_domains_required")
    if set(domain_ids) != set(arena.get("default_domains") or []):
        raise ValueError("cross_domain_plan_must_match_registered_arena_domains")
    if plan.get("method_development_domain") != "ecommerce":
        raise ValueError("cross_domain_method_development_domain_changed")

    repeats = plan.get("planned_repeats_per_domain")
    wave_size = plan.get("wave_size_per_domain")
    wave_count = plan.get("wave_count")
    if type(repeats) is not int or type(wave_size) is not int or type(wave_count) is not int:
        raise ValueError("cross_domain_sample_plan_invalid")
    if repeats < 1 or wave_size < 1 or wave_count < 1 or repeats != wave_size * wave_count:
        raise ValueError("cross_domain_wave_partition_mismatch")

    protocol_lock = plan.get("protocol_lock") or {}
    required_true = (
        "same_arena_runtime_all_domains",
        "same_agent_prompt_protocol_all_domains",
        "same_model_provider_all_domains",
        "same_recording_schema_all_domains",
        "same_execution_code_sha_across_waves_required",
        "domain_fixtures_frozen_before_first_provider_call",
        "no_outcome_aware_rerun",
        "no_domain_specific_method_change_after_first_provider_call",
    )
    if any(protocol_lock.get(key) is not True for key in required_true):
        raise ValueError("cross_domain_protocol_lock_incomplete")
    if protocol_lock.get("historical_method_development_path_replayed_in_replication_domains") is not False:
        raise ValueError("cross_domain_replication_must_not_replay_method_history")
    if protocol_lock.get("automatic_paid_evaluator") is not False:
        raise ValueError("cross_domain_paid_evaluator_forbidden")
    if protocol_lock.get("cpr_adjudication_in_first_round") is not False:
        raise ValueError("cross_domain_r8_cpr_not_in_first_round")

    return {
        "schema": SCHEMA,
        "experiment_family": plan["experiment_family"],
        "first_round_id": plan["first_round_id"],
        "subject_condition": plan["subject_condition"],
        "code_commit_sha": code_sha,
        "plan_path": plan_path,
        "plan_hash": sha256_file(ROOT / plan_path),
        "arena_config_path": plan["arena_config_path"],
        "arena_config_hash": sha256_file(arena_path),
        "model_config_path": plan["model_config_path"],
        "model_config_hash": sha256_file(model_path),
        "theory_contract_path": plan["theory_contract_path"],
        "theory_contract_hash": sha256_file(theory_path),
        "measurement_contract_path": plan["measurement_contract_path"],
        "measurement_contract_hash": sha256_file(measurement_path),
        "scout_config_path": plan["scout_config_path"],
        "scout_config_hash": sha256_file(scout_path),
        "experiment_profile_path": plan["experiment_profile_path"],
        "experiment_profile_hash": sha256_file(profile_path),
        "automatic_paid_evaluator": False,
        "semantic_review": "DEFERRED_APPEND_ONLY",
        "no_outcome_aware_rerun": True,
        "scientific_status": STATUS,
    }


def build_rows(*, plan_path: str = "configs/v5_cross_domain_first_round_v0.1.json",
               code_sha: str | None = None) -> list[dict]:
    plan = load_json(ROOT / plan_path)
    code_sha = code_sha or os.environ.get("GITHUB_SHA") or "LOCAL_OR_UNRECORDED"
    shared = _shared_bindings(plan, plan_path, code_sha)

    repeats = int(plan["planned_repeats_per_domain"])
    wave_size = int(plan["wave_size_per_domain"])
    rows: list[dict] = []

    for domain_row in plan["domains"]:
        domain_id = domain_row["domain_id"]
        cohort_role = domain_row["cohort_role"]
        domain_path = ROOT / f"arena/domains/{domain_id}.json"
        domain = load_json(domain_path)
        if domain.get("domain_id") != domain_id:
            raise ValueError("cross_domain_fixture_id_mismatch:" + domain_id)

        domain_binding = {
            "domain_id": domain_id,
            "cohort_role": cohort_role,
            "domain_hash": sha256_file(domain_path),
            "task_hash": stable_hash(domain["task"]),
            "agent_pool_hash": stable_hash(domain["agents"]),
        }
        for trial in range(1, repeats + 1):
            wave_id = ((trial - 1) // wave_size) + 1
            rows.append({
                **shared,
                **domain_binding,
                "run_id": f"v5-xd-{domain_id}-fr001-{trial:04d}",
                "trial": trial,
                "logical_seed": trial,
                "wave_id": wave_id,
            })

    verify_manifest(rows, plan=plan)
    return rows


def verify_manifest(rows: list[dict], *, plan: dict | None = None) -> bool:
    if not rows:
        raise ValueError("cross_domain_manifest_empty")
    if len({row["run_id"] for row in rows}) != len(rows):
        raise ValueError("cross_domain_manifest_duplicate_run_id")

    if plan is None:
        plan = load_json(ROOT / rows[0]["plan_path"])

    expected_domains = {row["domain_id"]: row["cohort_role"] for row in plan["domains"]}
    repeats = int(plan["planned_repeats_per_domain"])
    wave_size = int(plan["wave_size_per_domain"])
    wave_count = int(plan["wave_count"])
    expected_total = repeats * len(expected_domains)
    if len(rows) != expected_total:
        raise ValueError("cross_domain_manifest_run_count_mismatch")

    immutable_shared = (
        "experiment_family","first_round_id","subject_condition","code_commit_sha",
        "plan_path","plan_hash","arena_config_path","arena_config_hash",
        "model_config_path","model_config_hash","theory_contract_path","theory_contract_hash",
        "measurement_contract_path","measurement_contract_hash","scout_config_path","scout_config_hash",
        "experiment_profile_path","experiment_profile_hash","automatic_paid_evaluator",
        "semantic_review","no_outcome_aware_rerun","scientific_status",
    )
    for key in immutable_shared:
        if len({row.get(key) for row in rows}) != 1:
            raise ValueError("cross_domain_shared_binding_not_frozen:" + key)

    domain_counts = Counter(row["domain_id"] for row in rows)
    if set(domain_counts) != set(expected_domains):
        raise ValueError("cross_domain_manifest_domain_set_mismatch")
    if any(domain_counts[d] != repeats for d in expected_domains):
        raise ValueError("cross_domain_manifest_domain_count_mismatch")

    wave_counts = Counter(row["wave_id"] for row in rows)
    expected_wave_size = wave_size * len(expected_domains)
    if set(wave_counts) != set(range(1, wave_count + 1)):
        raise ValueError("cross_domain_manifest_wave_set_mismatch")
    if any(wave_counts[w] != expected_wave_size for w in wave_counts):
        raise ValueError("cross_domain_manifest_wave_count_mismatch")

    for domain_id, role in expected_domains.items():
        group = [row for row in rows if row["domain_id"] == domain_id]
        if {row["cohort_role"] for row in group} != {role}:
            raise ValueError("cross_domain_cohort_role_mismatch:" + domain_id)
        if len({row["domain_hash"] for row in group}) != 1:
            raise ValueError("cross_domain_domain_hash_not_frozen:" + domain_id)
        if len({row["task_hash"] for row in group}) != 1:
            raise ValueError("cross_domain_task_hash_not_frozen:" + domain_id)
        if len({row["agent_pool_hash"] for row in group}) != 1:
            raise ValueError("cross_domain_agent_pool_hash_not_frozen:" + domain_id)

    for row in rows:
        if row.get("schema") != SCHEMA or row.get("scientific_status") != STATUS:
            raise ValueError("cross_domain_manifest_schema_or_status_invalid")
        if row.get("automatic_paid_evaluator") is not False:
            raise ValueError("cross_domain_manifest_paid_evaluator_forbidden")
        if row.get("no_outcome_aware_rerun") is not True:
            raise ValueError("cross_domain_manifest_no_outcome_rerun_required")
        if row["wave_id"] != ((row["trial"] - 1) // wave_size) + 1:
            raise ValueError("cross_domain_manifest_wave_assignment_invalid")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="configs/v5_cross_domain_first_round_v0.1.json")
    ap.add_argument("--code-sha")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = build_rows(plan_path=args.plan, code_sha=args.code_sha)
    write_jsonl(args.out, rows)
    print("CROSS_DOMAIN_MANIFEST_ROWS=" + str(len(rows)))
    print("DOMAINS=4")
    print("WAVES=" + str(max(row["wave_id"] for row in rows)))
    print("PAID_API_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
