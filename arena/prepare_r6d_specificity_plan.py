#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Mapping

from .core import stable_hash
from .io_utils import load_json, load_jsonl, sha256_file, write_jsonl
from .r5r6_specificity_atomic_v0_2 import S0, S1, S2, build_atomic_envelope, mechanically_equivalent, verify_atomic_envelope

PLAN_SCHEMA = "RB-R6D-SPECIFICITY-RUNTIME-PLAN-v0.1"
MANIFEST_SCHEMA = "RB-R6D-SPECIFICITY-RUNTIME-BRANCH-MANIFEST-v0.1"
DESIGN_SCHEMA = "RB-R6D-SPECIFICITY-PREEXECUTION-DESIGN-FREEZE-v0.1"
EXPECTED_DESIGN_HASH = "d8783a9c3e0a264c3119ee72e63db9b61d51f0d633ff6dde66068751c31701de"


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


def _load_design(path: str | Path) -> dict[str, Any]:
    design = load_json(path)
    _require(design.get("schema") == DESIGN_SCHEMA, "r6d_design_schema_invalid")
    _require(design.get("status") == "FROZEN_PREEXECUTION_DESIGN_NOT_AUTHORIZED", "r6d_design_status_invalid")
    _require(design.get("design_hash") == _hash_without(design, "design_hash"), "r6d_design_hash_mismatch")
    _require(design.get("design_hash") == EXPECTED_DESIGN_HASH, "r6d_unexpected_design_hash")
    _require(design.get("authorization", {}).get("scientific_provider_run") is False, "r6d_design_must_not_authorize_provider")
    return design


def _load_source_r5_bundle(plan_dir: str | Path) -> dict[str, Any]:
    p = Path(plan_dir)
    branch_plan = load_json(p / "branch_plan.json")
    parent = load_json(p / "parent_snapshot.json")
    _require(branch_plan.get("plan_hash") == _hash_without(branch_plan, "plan_hash"), "source_r5_plan_hash_invalid")
    _require(parent.get("state_hash") == "aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c", "source_parent_state_hash_invalid")
    _require(int(parent.get("turns")) == 8, "source_parent_turn_invalid")
    _require(list(parent.get("queue") or []) == ["ops_lead"], "source_parent_resume_queue_invalid")
    return {"branch_plan": branch_plan, "parent_snapshot": parent}


def _build_envelopes(binding: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    s1 = binding["s1"]
    s2 = binding["s2"]
    e1 = build_atomic_envelope(
        condition_id=S1,
        target_locator=s1["target_locator"],
        original_value=s1["original_value"],
        target_class=s1["target_class"],
        source_refs=s1["source_refs"],
        source_origin_status=s1["source_origin_status"],
        acquired_status_at_intervention=s1["acquired_status_at_intervention"],
    )
    e2 = build_atomic_envelope(
        condition_id=S2,
        target_locator=s2["target_locator"],
        original_value=s2["original_value"],
        target_class=s2["target_class"],
        source_refs=s2["source_refs"],
        source_origin_status=s2["source_origin_status"],
        acquired_status_at_intervention=s2["acquired_status_at_intervention"],
    )
    mechanically_equivalent(e1, e2)
    return e1, e2


def _bounded_arena_config(design: Mapping[str, Any]) -> dict[str, Any]:
    env = design["environment_binding"]
    arena_path = Path(env["arena_config_path"])
    _require(sha256_file(arena_path) == env["arena_config_hash"], "arena_config_hash_mismatch_design")
    config = copy.deepcopy(load_json(arena_path))
    horizon = design["observation_horizon"]
    config["max_turns"] = int(horizon["absolute_turn_cap"])
    config["r6d_observation_horizon"] = {
        "design_hash": design["design_hash"],
        "branch_start_parent_turn": horizon["branch_start_parent_turn"],
        "direct_response_turn": horizon["direct_response_turn"],
        "post_consumption_start_turn": horizon["post_consumption_start_turn"],
        "absolute_turn_cap": horizon["absolute_turn_cap"],
        "natural_early_termination_interpretation": horizon["natural_early_termination_interpretation"],
    }
    return config


def build_runtime_plan(
    *,
    design_path: str | Path,
    source_r5_plan_dir: str | Path,
    binding_path: str | Path,
    plan_code_sha: str,
) -> dict[str, Any]:
    design = _load_design(design_path)
    source = _load_source_r5_bundle(source_r5_plan_dir)
    binding = load_json(binding_path)
    _require(binding.get("schema") == "RB-R5R6-SPECIFICITY-EXACT-SOURCE-BINDING-v0.2", "specificity_binding_schema_invalid")

    source_plan = source["branch_plan"]
    parent = source["parent_snapshot"]
    ds = design["source_binding"]
    _require(source_plan["plan_hash"] == ds["source_r5_plan_hash"], "source_r5_plan_hash_mismatch_design")
    _require(parent["state_hash"] == ds["common_parent_state_hash"], "parent_hash_mismatch_design")

    e1, e2 = _build_envelopes(binding)
    spec = design["specificity_binding"]
    _require(e1["envelope_hash"] == spec["s1_envelope_hash"], "s1_envelope_hash_mismatch_design")
    _require(e2["envelope_hash"] == spec["s2_envelope_hash"], "s2_envelope_hash_mismatch_design")

    bounded_config = _bounded_arena_config(design)
    env = design["environment_binding"]
    _require(sha256_file(env["model_config_path"]) == env["model_config_hash"], "model_config_hash_mismatch_design")
    domain_path = Path("arena/domains") / f"{env['domain_id']}.json"
    _require(sha256_file(domain_path) == env["domain_hash"], "domain_hash_mismatch_design")
    domain = load_json(domain_path)
    _require(stable_hash(domain["task"]) == env["task_hash"], "task_hash_mismatch_design")
    _require(stable_hash(domain["agents"]) == env["agent_registry_hash"], "agent_registry_hash_mismatch_design")

    envelopes = {S1: e1, S2: e2}
    execution_rows: list[dict[str, Any]] = []
    for frozen_row in design["matched_execution_design"]["rows"]:
        condition = frozen_row["condition_id"]
        _require(condition in (S0, S1, S2), "r6d_unknown_condition")
        row = {
            "schema": MANIFEST_SCHEMA,
            "run_id": frozen_row["run_id"],
            "triad_id": frozen_row["triad_id"],
            "replicate_index": frozen_row["replicate_index"],
            "logical_seed": frozen_row["logical_seed"],
            "execution_order": frozen_row["execution_order"],
            "condition_id": condition,
            "frozen_design_row_hash": frozen_row["row_hash"],
            "design_hash": design["design_hash"],
            "parent_state_hash": parent["state_hash"],
            "parent_turn": int(parent["turns"]),
            "branch_start_turn": int(parent["turns"]),
            "envelope_hash": envelopes[condition]["envelope_hash"] if condition in envelopes else None,
            "direct_experiment_origin_exposure_count_expected": 0 if condition == S0 else 1,
            "experiment_origin_reinjection_count_expected": 0,
            "persistent_state_mutation_expected": False,
            "provider_internal_state_replayed": False,
            "semantic_cpr_status": "NOT_ADJUDICATED",
        }
        row["manifest_hash"] = stable_hash(row)
        execution_rows.append(row)

    plan = {
        "schema": PLAN_SCHEMA,
        "version": "0.1",
        "status": "RUNTIME_PLAN_PREPARED_OFFLINE_NOT_AUTHORIZED",
        "design_hash": design["design_hash"],
        "plan_code_sha": plan_code_sha,
        "source_binding": copy.deepcopy(design["source_binding"]),
        "environment_binding": copy.deepcopy(design["environment_binding"]),
        "specificity_binding": copy.deepcopy(design["specificity_binding"]),
        "observation_horizon": copy.deepcopy(design["observation_horizon"]),
        "analysis_freeze": copy.deepcopy(design["analysis_freeze"]),
        "budget_gate": copy.deepcopy(design["budget_gate"]),
        "order_policy": design["matched_execution_design"]["order_policy"],
        "replicates": design["matched_execution_design"]["replicates"],
        "branch_row_count": len(execution_rows),
        "execution_row_hashes": [row["manifest_hash"] for row in execution_rows],
        "bounded_arena_config_hash": stable_hash(bounded_config),
        "s1_envelope_hash": e1["envelope_hash"],
        "s2_envelope_hash": e2["envelope_hash"],
        "real_subject_runner_expected": "arena.run_r6d_specificity_real",
        "real_subject_workflow_expected": ".github/workflows/r6d-specificity-subject-real.yml",
        "real_subject_execution_authorized": False,
        "paid_subject_authorization_status": "NOT_AUTHORIZED",
        "paid_evaluator_authorized": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "same_parent_repeats_are_independent_samples": False,
        "terminal_outcome_is_primary": False,
    }
    plan["plan_hash"] = stable_hash(plan)
    bundle = {
        "plan": plan,
        "source_parent_snapshot": parent,
        "s1_envelope": e1,
        "s2_envelope": e2,
        "bounded_arena_config": bounded_config,
        "execution_rows": execution_rows,
    }
    verify_r6d_runtime_plan(bundle)
    return bundle


def verify_r6d_runtime_plan(bundle: Mapping[str, Any]) -> bool:
    plan = bundle["plan"]
    parent = bundle["source_parent_snapshot"]
    e1 = bundle["s1_envelope"]
    e2 = bundle["s2_envelope"]
    rows = list(bundle["execution_rows"])
    config = bundle["bounded_arena_config"]

    _require(plan.get("schema") == PLAN_SCHEMA, "r6d_runtime_plan_schema_invalid")
    _require(plan.get("plan_hash") == _hash_without(plan, "plan_hash"), "r6d_runtime_plan_hash_mismatch")
    _require(plan.get("design_hash") == EXPECTED_DESIGN_HASH, "r6d_runtime_design_hash_invalid")
    _require(plan.get("real_subject_execution_authorized") is False, "r6d_runtime_plan_must_not_self_authorize")
    _require(plan.get("paid_subject_authorization_status") == "NOT_AUTHORIZED", "r6d_paid_gate_must_remain_external")
    _require(plan.get("paid_evaluator_authorized") is False, "r6d_paid_evaluator_must_be_disabled")
    _require(plan.get("semantic_cpr_status") == "NOT_ADJUDICATED", "r6d_semantic_status_invalid")
    _require(plan.get("same_parent_repeats_are_independent_samples") is False, "r6d_independence_overclaim_forbidden")
    _require(plan.get("terminal_outcome_is_primary") is False, "r6d_terminal_primary_forbidden")
    _require(plan.get("branch_row_count") == 9 and len(rows) == 9, "r6d_runtime_requires_nine_rows")
    _require(plan.get("replicates") == 3, "r6d_runtime_requires_three_triads")
    _require(plan.get("order_policy") == "THREE_CONDITION_CYCLIC_LATIN_ROTATION", "r6d_runtime_order_policy_invalid")
    _require(parent.get("state_hash") == plan["source_binding"]["common_parent_state_hash"], "r6d_runtime_parent_hash_mismatch")
    _require(int(parent.get("turns")) == 8, "r6d_runtime_parent_turn_invalid")
    _require(int(config.get("max_turns")) == 16, "r6d_runtime_turn_cap_invalid")
    _require(plan.get("bounded_arena_config_hash") == stable_hash(config), "r6d_runtime_config_hash_mismatch")
    verify_atomic_envelope(e1)
    verify_atomic_envelope(e2)
    mechanically_equivalent(e1, e2)
    _require(e1["envelope_hash"] == plan["s1_envelope_hash"], "r6d_runtime_s1_envelope_mismatch")
    _require(e2["envelope_hash"] == plan["s2_envelope_hash"], "r6d_runtime_s2_envelope_mismatch")
    _require(plan["execution_row_hashes"] == [row["manifest_hash"] for row in rows], "r6d_runtime_execution_row_hashes_mismatch")
    for row in rows:
        _require(row.get("schema") == MANIFEST_SCHEMA, "r6d_runtime_manifest_schema_invalid")
        _require(row.get("manifest_hash") == _hash_without(row, "manifest_hash"), "r6d_runtime_manifest_hash_mismatch")
        _require(row.get("parent_state_hash") == parent.get("state_hash"), "r6d_runtime_manifest_parent_mismatch")
        _require(row.get("provider_internal_state_replayed") is False, "r6d_runtime_hidden_state_replay_forbidden")
        _require(row.get("semantic_cpr_status") == "NOT_ADJUDICATED", "r6d_runtime_manifest_semantic_status_invalid")
        cond = row.get("condition_id")
        _require(cond in (S0, S1, S2), "r6d_runtime_manifest_condition_invalid")
        expected = None if cond == S0 else (e1["envelope_hash"] if cond == S1 else e2["envelope_hash"])
        _require(row.get("envelope_hash") == expected, "r6d_runtime_manifest_envelope_mismatch")
    return True


def write_runtime_plan(bundle: Mapping[str, Any], outdir: str | Path) -> Path:
    out = Path(outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r6d_runtime_plan_dir")
    out.mkdir(parents=True)
    _write_json(out / "r6d_plan.json", bundle["plan"])
    _write_json(out / "source_parent_snapshot.json", bundle["source_parent_snapshot"])
    _write_json(out / "s1_envelope.json", bundle["s1_envelope"])
    _write_json(out / "s2_envelope.json", bundle["s2_envelope"])
    _write_json(out / "r6d_bounded_arena_config.json", bundle["bounded_arena_config"])
    write_jsonl(out / "execution_rows.jsonl", bundle["execution_rows"])
    return out


def load_r6d_runtime_plan(plan_dir: str | Path) -> dict[str, Any]:
    p = Path(plan_dir)
    bundle = {
        "plan": load_json(p / "r6d_plan.json"),
        "source_parent_snapshot": load_json(p / "source_parent_snapshot.json"),
        "s1_envelope": load_json(p / "s1_envelope.json"),
        "s2_envelope": load_json(p / "s2_envelope.json"),
        "bounded_arena_config": load_json(p / "r6d_bounded_arena_config.json"),
        "execution_rows": load_jsonl(p / "execution_rows.jsonl"),
    }
    verify_r6d_runtime_plan(bundle)
    return bundle


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design-manifest", default="manifests/r6d_specificity_preexecution_design_freeze_2026-09-17_v0_1.json")
    ap.add_argument("--source-r5-plan-dir", required=True)
    ap.add_argument("--binding", default="configs/r5r6_specificity_exact_source_binding_v0.2.json")
    ap.add_argument("--plan-code-sha", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    bundle = build_runtime_plan(
        design_path=args.design_manifest,
        source_r5_plan_dir=args.source_r5_plan_dir,
        binding_path=args.binding,
        plan_code_sha=args.plan_code_sha,
    )
    write_runtime_plan(bundle, args.outdir)
    print("R6D_RUNTIME_PLAN_PREPARE=PASS")
    print("DESIGN_HASH=" + bundle["plan"]["design_hash"])
    print("PLAN_HASH=" + bundle["plan"]["plan_hash"])
    print("BRANCH_ROWS=" + str(bundle["plan"]["branch_row_count"]))
    print("REAL_SUBJECT_AUTHORIZED=NO")
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
