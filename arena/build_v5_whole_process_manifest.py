#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, sha256_file, write_jsonl

ROOT = Path(__file__).resolve().parents[1]
STATUS = "V5_WHOLE_PROCESS_SUBJECT_CANDIDATE_AWAITING_EXPLICIT_PAID_AUTHORIZATION"
SCHEMA = "RB-V5-WHOLE-PROCESS-SUBJECT-MANIFEST-v0.1"


def build_rows(*, design_path: str, code_sha: str | None = None) -> list[dict]:
    design_file = ROOT / design_path
    design = load_json(design_file)
    if design.get("schema") != "RB-V5-WHOLE-PROCESS-BATCH-DESIGN-v0.1":
        raise ValueError("v5_batch_design_schema_invalid")
    if design.get("paid_subject_execution_authorized") is not False:
        raise ValueError("v5_prepare_design_must_not_authorize_paid_execution")
    if design.get("automatic_paid_evaluator") is not False:
        raise ValueError("v5_automatic_paid_evaluator_must_be_false")
    if design.get("subject_condition") != "NATURAL_UNMANIPULATED":
        raise ValueError("v5_base_subject_must_be_natural_unmanipulated")
    repeats = design.get("planned_repeats")
    if type(repeats) is not int or repeats < 1:
        raise ValueError("v5_planned_repeats_invalid")

    domain_path = ROOT / f"arena/domains/{design['domain_id']}.json"
    arena_path = ROOT / design["arena_config_path"]
    model_path = ROOT / design["model_config_path"]
    theory_path = ROOT / design["theory_contract_path"]
    measurement_path = ROOT / design["measurement_contract_path"]
    scout_path = ROOT / design["scout_config_path"]
    profile_path = ROOT / design["experiment_profile_path"]

    domain = load_json(domain_path)
    arena = load_json(arena_path)
    model = load_json(model_path)

    if design["domain_id"] not in arena.get("default_domains", []):
        raise ValueError("v5_domain_not_registered_in_arena")
    if model.get("provider") != "deepseek":
        raise ValueError("v5_batch001_provider_binding_changed")

    code_sha = code_sha or os.environ.get("GITHUB_SHA") or "LOCAL_OR_UNRECORDED"
    shared = {
        "schema": SCHEMA,
        "experiment_family": design["experiment_family"],
        "batch_id": design["batch_id"],
        "domain_id": design["domain_id"],
        "subject_condition": design["subject_condition"],
        "code_commit_sha": code_sha,
        "batch_design_path": design_path,
        "batch_design_hash": sha256_file(design_file),
        "domain_hash": sha256_file(domain_path),
        "task_hash": stable_hash(domain["task"]),
        "agent_pool_hash": stable_hash(domain["agents"]),
        "arena_config_path": design["arena_config_path"],
        "arena_config_hash": sha256_file(arena_path),
        "model_config_path": design["model_config_path"],
        "model_config_hash": sha256_file(model_path),
        "theory_contract_path": design["theory_contract_path"],
        "theory_contract_hash": sha256_file(theory_path),
        "measurement_contract_path": design["measurement_contract_path"],
        "measurement_contract_hash": sha256_file(measurement_path),
        "scout_config_path": design["scout_config_path"],
        "scout_config_hash": sha256_file(scout_path),
        "experiment_profile_path": design["experiment_profile_path"],
        "experiment_profile_hash": sha256_file(profile_path),
        "automatic_paid_evaluator": False,
        "semantic_review": "DEFERRED_APPEND_ONLY",
        "no_outcome_aware_rerun": True,
        "scientific_status": STATUS,
    }
    rows = []
    for trial in range(1, repeats + 1):
        rows.append({
            **shared,
            "trial": trial,
            "logical_seed": trial,
            "run_id": f"v5-wp-ecommerce-b001-{trial:04d}",
        })
    verify_manifest(rows)
    return rows


def verify_manifest(rows: list[dict]) -> bool:
    if not rows:
        raise ValueError("v5_manifest_empty")
    if len({r["run_id"] for r in rows}) != len(rows):
        raise ValueError("v5_manifest_duplicate_run_id")
    frozen = (
        "batch_id","domain_hash","task_hash","agent_pool_hash","batch_design_hash",
        "arena_config_hash","model_config_hash","theory_contract_hash",
        "measurement_contract_hash","scout_config_hash","experiment_profile_hash",
    )
    for key in frozen:
        if len({r.get(key) for r in rows}) != 1:
            raise ValueError("v5_manifest_binding_not_frozen:" + key)
    for row in rows:
        if row["automatic_paid_evaluator"] is not False:
            raise ValueError("v5_manifest_paid_evaluator_forbidden")
        if row["no_outcome_aware_rerun"] is not True:
            raise ValueError("v5_manifest_no_rerun_required")
        if row["scientific_status"] != STATUS:
            raise ValueError("v5_manifest_status_invalid")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", default="configs/v5_whole_process_ecommerce_batch001_v0.1.json")
    ap.add_argument("--code-sha")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = build_rows(design_path=args.design, code_sha=args.code_sha)
    write_jsonl(args.out, rows)
    print("V5_WHOLE_PROCESS_ROWS=" + str(len(rows)))
    print("PAID_API_AUTHORIZED=NO")
    print("SCIENTIFIC_STATUS=" + STATUS)


if __name__ == "__main__":
    main()
