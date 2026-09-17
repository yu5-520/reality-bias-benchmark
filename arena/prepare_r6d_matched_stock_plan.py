#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Mapping

from .core import stable_hash
from .io_utils import load_json, sha256_file, write_jsonl
from .r5r6_specificity_atomic_preflight_v0_2 import build_preflight
from .r5r6_specificity_atomic_v0_2 import mechanically_equivalent, verify_atomic_envelope

S2 = "S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL"
S3 = "S3_MATCHED_ORDINARY_STOCK_B_DOWNGRADE"
S4 = "S4_MATCHED_ORDINARY_STOCK_C_DOWNGRADE"
CONDITIONS = [S2, S3, S4]

PLAN_SCHEMA = "RB-R6D-MATCHED-STOCK-RUNTIME-PLAN-v0.1"
MANIFEST_SCHEMA = "RB-R6D-MATCHED-STOCK-RUNTIME-BRANCH-MANIFEST-v0.1"
EXPECTED_DESIGN_HASH = "5064e255da26949a152a2300fe659ebdddddc9b44f1a97a4b31d7796005a959d"
EXPECTED_PARENT_HASH = "aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c"


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


def _load_source_bundle(plan_dir: str | Path) -> dict[str, Any]:
    p = Path(plan_dir)
    branch_plan = load_json(p / "branch_plan.json")
    parent = load_json(p / "parent_snapshot.json")
    predecessor = load_json("manifests/r6d_specificity_preexecution_design_freeze_2026-09-17_v0_1.json")
    _require(branch_plan.get("plan_hash") == _hash_without(branch_plan, "plan_hash"), "source_r5_plan_hash_invalid")
    _require(branch_plan.get("plan_hash") == predecessor["source_binding"]["source_r5_plan_hash"], "source_r5_plan_not_predecessor_bound")
    _require(parent.get("state_hash") == EXPECTED_PARENT_HASH, "source_parent_state_hash_invalid")
    _require(int(parent.get("turns")) == 8, "source_parent_turn_invalid")
    _require(list(parent.get("queue") or []) == ["ops_lead"], "source_parent_resume_queue_invalid")
    return {"branch_plan": branch_plan, "parent_snapshot": parent}


def _load_envelopes() -> dict[str, dict[str, Any]]:
    preflight = build_preflight()
    s2 = copy.deepcopy(preflight["s2_envelope"])
    s3 = load_json("configs/r6/r6d_s3_matched_stock_b_envelope_v0.1.json")
    s4 = load_json("configs/r6/r6d_s4_matched_stock_c_envelope_v0.1.json")
    for env in (s2, s3, s4):
        verify_atomic_envelope(env)
    mechanically_equivalent(s2, s3)
    mechanically_equivalent(s2, s4)
    return {S2: s2, S3: s3, S4: s4}


def _bounded_arena_config(design: Mapping[str, Any]) -> dict[str, Any]:
    env = design["environment_binding"]
    _require(sha256_file(env["arena_config_path"]) == env["arena_config_hash"], "arena_config_hash_mismatch_design")
    config = copy.deepcopy(load_json(env["arena_config_path"]))
    horizon = design["observation_horizon"]
    config["max_turns"] = int(horizon["absolute_turn_cap"])
    config["r6d_matched_stock_observation_horizon"] = {
        "design_hash": design["design_hash"],
        "branch_start_parent_turn": horizon["branch_start_parent_turn"],
        "direct_response_turn": horizon["direct_response_turn"],
        "post_consumption_start_turn": horizon["post_consumption_start_turn"],
        "absolute_turn_cap": horizon["absolute_turn_cap"],
        "natural_early_termination_interpretation": horizon["natural_early_termination_interpretation"],
    }
    return config


def build_runtime_plan(*, source_r5_plan_dir: str | Path, plan_code_sha: str) -> dict[str, Any]:
    design = load_json("configs/r6/r6d_matched_stock_robustness_plan_v0.1.json")
    gate = load_json("configs/r6/r6d_matched_stock_robustness_formal_subject_gate_v0.2.json")
    _require(design["design_hash"] == EXPECTED_DESIGN_HASH, "matched_stock_design_hash_invalid")
    _require(design["status"] == "DESIGN_FROZEN_NOT_RUNTIME_READY_NOT_AUTHORIZED", "matched_stock_design_status_invalid")
    _require(gate["status"] == "RUNTIME_BOUND_GATE_CLOSED_NOT_AUTHORIZATION", "matched_stock_runtime_gate_status_invalid")
    _require(gate["design_freeze"]["design_hash"] == EXPECTED_DESIGN_HASH, "runtime_gate_design_hash_mismatch")
    _require(gate["authorization_status"] == "NOT_AUTHORIZED", "runtime_gate_must_remain_closed")
    _require(gate["scientific_provider_run_authorized"] is False, "runtime_gate_provider_authorization_forbidden")

    source = _load_source_bundle(source_r5_plan_dir)
    parent = source["parent_snapshot"]
    _require(parent["state_hash"] == design["source_binding"]["common_parent_state_hash"], "parent_hash_mismatch_design")

    envelopes = _load_envelopes()
    frozen = {row["condition_id"]: row for row in design["conditions"]}
    for condition in CONDITIONS:
        _require(condition in frozen, "missing_frozen_condition:" + condition)
        _require(envelopes[condition]["envelope_hash"] == frozen[condition]["envelope_hash"], "envelope_hash_mismatch:" + condition)

    env = design["environment_binding"]
    _require(sha256_file(env["model_config_path"]) == env["model_config_hash"], "model_config_hash_mismatch_design")
    domain_path = Path("arena/domains") / f"{env['domain_id']}.json"
    _require(sha256_file(domain_path) == env["domain_hash"], "domain_hash_mismatch_design")
    domain = load_json(domain_path)
    _require(stable_hash(domain["task"]) == env["task_hash"], "task_hash_mismatch_design")
    _require(stable_hash(domain["agents"]) == env["agent_registry_hash"], "agent_registry_hash_mismatch_design")
    bounded_config = _bounded_arena_config(design)

    execution_rows = []
    for frozen_row in design["matched_execution_design"]["rows"]:
        condition = frozen_row["condition_id"]
        _require(condition in CONDITIONS, "unknown_matched_stock_condition")
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
            "envelope_hash": envelopes[condition]["envelope_hash"],
            "direct_experiment_origin_exposure_count_expected": 1,
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
        "observation_horizon": copy.deepcopy(design["observation_horizon"]),
        "analysis_freeze": copy.deepcopy(design["analysis_freeze"]),
        "budget_gate": copy.deepcopy(design["budget_gate"]),
        "order_policy": design["matched_execution_design"]["order_policy"],
        "replicates": design["matched_execution_design"]["replicates"],
        "branch_row_count": len(execution_rows),
        "execution_row_hashes": [row["manifest_hash"] for row in execution_rows],
        "bounded_arena_config_hash": stable_hash(bounded_config),
        "condition_envelope_hashes": {k: envelopes[k]["envelope_hash"] for k in CONDITIONS},
        "real_subject_runner_expected": "arena.run_r6d_matched_stock_real",
        "real_subject_workflow_expected": ".github/workflows/r6d-matched-stock-subject-real.yml",
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
        "bounded_arena_config": bounded_config,
        "condition_envelopes": envelopes,
        "execution_rows": execution_rows,
    }
    verify_runtime_plan(bundle)
    return bundle


def verify_runtime_plan(bundle: Mapping[str, Any]) -> bool:
    plan = bundle["plan"]
    rows = list(bundle["execution_rows"])
    parent = bundle["source_parent_snapshot"]
    envelopes = bundle["condition_envelopes"]
    _require(plan["schema"] == PLAN_SCHEMA, "runtime_plan_schema_invalid")
    _require(plan["plan_hash"] == _hash_without(plan, "plan_hash"), "runtime_plan_hash_mismatch")
    _require(plan["design_hash"] == EXPECTED_DESIGN_HASH, "runtime_design_hash_invalid")
    _require(plan["branch_row_count"] == 9 and len(rows) == 9, "runtime_requires_nine_rows")
    _require(plan["replicates"] == 3, "runtime_requires_three_triads")
    _require(plan["order_policy"] == "THREE_CONDITION_CYCLIC_LATIN_ROTATION", "runtime_order_policy_invalid")
    _require(parent["state_hash"] == EXPECTED_PARENT_HASH and int(parent["turns"]) == 8, "runtime_parent_invalid")
    _require(plan["bounded_arena_config_hash"] == stable_hash(bundle["bounded_arena_config"]), "runtime_config_hash_mismatch")
    _require(int(bundle["bounded_arena_config"]["max_turns"]) == 16, "runtime_turn_cap_invalid")
    _require(plan["real_subject_execution_authorized"] is False, "runtime_plan_must_not_self_authorize")
    _require(plan["paid_subject_authorization_status"] == "NOT_AUTHORIZED", "runtime_paid_gate_must_remain_external")
    _require(plan["paid_evaluator_authorized"] is False, "runtime_paid_evaluator_must_be_disabled")
    _require(plan["semantic_cpr_status"] == "NOT_ADJUDICATED", "runtime_semantic_status_invalid")
    _require(plan["same_parent_repeats_are_independent_samples"] is False, "runtime_independence_overclaim_forbidden")
    _require(plan["terminal_outcome_is_primary"] is False, "runtime_terminal_primary_forbidden")
    for condition in CONDITIONS:
        verify_atomic_envelope(envelopes[condition])
        _require(plan["condition_envelope_hashes"][condition] == envelopes[condition]["envelope_hash"], "runtime_envelope_hash_mismatch:" + condition)
    _require(plan["execution_row_hashes"] == [r["manifest_hash"] for r in rows], "runtime_execution_hashes_mismatch")
    for row in rows:
        _require(row["schema"] == MANIFEST_SCHEMA, "runtime_manifest_schema_invalid")
        _require(row["manifest_hash"] == _hash_without(row, "manifest_hash"), "runtime_manifest_hash_mismatch")
        _require(row["condition_id"] in CONDITIONS, "runtime_manifest_condition_invalid")
        _require(row["envelope_hash"] == envelopes[row["condition_id"]]["envelope_hash"], "runtime_manifest_envelope_mismatch")
        _require(row["direct_experiment_origin_exposure_count_expected"] == 1, "runtime_exposure_expectation_invalid")
    return True


def write_runtime_plan(bundle: Mapping[str, Any], outdir: str | Path) -> Path:
    out = Path(outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_matched_stock_runtime_plan_dir")
    out.mkdir(parents=True)
    _write_json(out / "r6d_matched_stock_plan.json", bundle["plan"])
    _write_json(out / "source_parent_snapshot.json", bundle["source_parent_snapshot"])
    _write_json(out / "r6d_matched_stock_bounded_arena_config.json", bundle["bounded_arena_config"])
    for key, filename in ((S2, "s2_envelope.json"), (S3, "s3_envelope.json"), (S4, "s4_envelope.json")):
        _write_json(out / filename, bundle["condition_envelopes"][key])
    write_jsonl(out / "execution_rows.jsonl", bundle["execution_rows"])
    return out


def load_runtime_plan(plan_dir: str | Path) -> dict[str, Any]:
    p = Path(plan_dir)
    bundle = {
        "plan": load_json(p / "r6d_matched_stock_plan.json"),
        "source_parent_snapshot": load_json(p / "source_parent_snapshot.json"),
        "bounded_arena_config": load_json(p / "r6d_matched_stock_bounded_arena_config.json"),
        "condition_envelopes": {
            S2: load_json(p / "s2_envelope.json"),
            S3: load_json(p / "s3_envelope.json"),
            S4: load_json(p / "s4_envelope.json"),
        },
        "execution_rows": [json.loads(line) for line in (p / "execution_rows.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()],
    }
    verify_runtime_plan(bundle)
    return bundle


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-r5-plan-dir", required=True)
    ap.add_argument("--plan-code-sha", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    bundle = build_runtime_plan(source_r5_plan_dir=args.source_r5_plan_dir, plan_code_sha=args.plan_code_sha)
    out = write_runtime_plan(bundle, args.outdir)
    print("R6D_MATCHED_STOCK_RUNTIME_PLAN=PASS")
    print("OUTDIR=" + str(out))
    print("DESIGN_HASH=" + bundle["plan"]["design_hash"])
    print("RUNTIME_PLAN_HASH=" + bundle["plan"]["plan_hash"])
    print("PLANNED_BRANCHES=9")
    print("REAL_SUBJECT_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
