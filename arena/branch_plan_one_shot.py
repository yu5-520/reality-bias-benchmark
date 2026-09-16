#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path

from .branch_plan import validate_phase_a_selection
from .core import stable_hash
from .experimental_control import verify_state_snapshot
from .io_utils import load_json, load_jsonl, write_jsonl
from .one_shot_intervention import (
    CONTROL_CONDITION,
    INTERVENTION_CONDITION,
    build_one_shot_envelope,
    make_branch_manifest_v3,
    verify_branch_manifest_v3,
)

PLAN_SCHEMA = "RB-R5MID-ONE-SHOT-BRANCH-EXECUTION-PLAN-v0.1"
CONDITIONS = (CONTROL_CONDITION, INTERVENTION_CONDITION)


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _hash_without(row, key):
    material = copy.deepcopy(row)
    material.pop(key, None)
    return stable_hash(material)


def _event_index(candidate):
    value = candidate.get("event_index")
    if isinstance(value, int):
        return value
    ref = candidate.get("event_ref")
    if isinstance(ref, str) and ref.startswith("EVENT:"):
        return int(ref.split(":", 1)[1])
    raise ValueError("selected_candidate_event_index_required")


def _contract_hash(path):
    return stable_hash(load_json(path))


def build_one_shot_branch_plan(selection_package, baseline_trace, *, replicates, branch_code_sha=None):
    _require(isinstance(replicates, int) and replicates >= 1, "positive_integer_replicates_required")
    validate_phase_a_selection(selection_package, baseline_trace)
    branch_code_sha = branch_code_sha or os.environ.get("GITHUB_SHA") or "LOCAL_OR_UNRECORDED"
    parent = copy.deepcopy(selection_package["selected_snapshot"])
    verify_state_snapshot(parent)
    record = selection_package["selection_record"]
    candidate = selection_package["selected_candidate"]
    facts = candidate.get("structural_facts") or {}
    state_key = facts.get("state_key")
    original_status = facts.get("status_after")
    _require(state_key in parent.get("shared_state_metadata", {}), "one_shot_state_key_missing_from_parent")
    _require(parent["shared_state_metadata"][state_key].get("status") == original_status, "one_shot_parent_status_mismatch")
    envelope = build_one_shot_envelope(
        target_jump_ref=candidate["event_ref"],
        target_candidate_id=candidate["candidate_id"],
        state_key=state_key,
        source_event_index=_event_index(candidate),
        from_status=original_status,
    )
    source_trace_hash = stable_hash(baseline_trace)
    model_identity = {
        "provider": baseline_trace.get("provider"),
        "model_config_path": baseline_trace.get("model_config_path"),
        "model_config_version": baseline_trace.get("model_config_version"),
        "model_config_hash": baseline_trace.get("model_config_hash"),
    }
    config_identity = {
        "arena_config_path": baseline_trace.get("arena_config_path"),
        "arena_config_version": baseline_trace.get("arena_config_version"),
        "arena_config_hash": baseline_trace.get("arena_config_hash"),
        "domain_id": baseline_trace.get("domain_id"),
        "domain_hash": baseline_trace.get("domain_hash"),
        "task_hash": baseline_trace.get("task_hash"),
        "agent_registry_hash": baseline_trace.get("agent_registry_hash"),
    }
    code_identity = {
        "source_baseline_commit": baseline_trace.get("code_commit_sha"),
        "branch_execution_commit": branch_code_sha,
    }
    common_identity = {
        "baseline_run_id": baseline_trace.get("run_id"),
        "source_trace_hash": source_trace_hash,
        "source_evidence_hash": selection_package.get("evidence_hash"),
        "selection_record_hash": record.get("record_hash"),
        "selected_candidate_id": candidate.get("candidate_id"),
        "selected_candidate_event_ref": candidate.get("event_ref"),
        "selected_candidate_event_index": _event_index(candidate),
        "parent_state_hash": parent["state_hash"],
        "branch_start_state_hash": parent["state_hash"],
        "state_key": state_key,
        "original_status": original_status,
    }
    rows = []
    manifests = []
    for replicate in range(1, replicates + 1):
        pair_id = f"{baseline_trace['run_id']}:oneshot-pair:{replicate:04d}"
        order = CONDITIONS if replicate % 2 else tuple(reversed(CONDITIONS))
        pattern = "CONTROL_FIRST" if replicate % 2 else "INTERVENTION_FIRST"
        for execution_order, condition in enumerate(order, 1):
            branch_id = f"{pair_id}:{condition.lower()}"
            bound_envelope = None if condition == CONTROL_CONDITION else envelope
            manifest = make_branch_manifest_v3(
                branch_id=branch_id,
                condition_id=condition,
                parent_trace_hash=source_trace_hash,
                parent_snapshot=parent,
                envelope=bound_envelope,
                replicate_index=replicate,
                model_identity=model_identity,
                config_identity=config_identity,
                code_identity=code_identity,
            )
            manifests.append(manifest)
            rows.append({
                "run_id": branch_id,
                "pair_id": pair_id,
                "replicate_index": replicate,
                "logical_seed": replicate,
                "execution_order": execution_order,
                "pair_order_pattern": pattern,
                "condition_id": condition,
                "branch_hash": manifest["branch_hash"],
                "parent_state_hash": parent["state_hash"],
                "branch_start_state_hash": parent["state_hash"],
                "one_shot_intervention_envelope_hash": manifest.get("one_shot_intervention_envelope_hash"),
                "source_selection_record_hash": record["record_hash"],
                "branch_execution_code_commit_sha": branch_code_sha,
                "model_provider": baseline_trace.get("provider"),
                "model_config_path": baseline_trace.get("model_config_path"),
                "model_config_hash": baseline_trace.get("model_config_hash"),
                "arena_config_path": baseline_trace.get("arena_config_path"),
                "arena_config_hash": baseline_trace.get("arena_config_hash"),
                "domain_id": baseline_trace.get("domain_id"),
                "domain_hash": baseline_trace.get("domain_hash"),
                "scientific_status": "EXPLORATORY_MECHANISM_COMPATIBILITY_UNTIL_NEW_PROSPECTIVE_EVIDENCE",
                "automatic_paid_evaluator": False,
            })
    plan = {
        "schema": PLAN_SCHEMA,
        "version": "0.1",
        "phase": "ONE_SHOT_BRANCH_CONTINUATION_PREPARED_ONLY",
        "scientific_status": "EXPLORATORY_MECHANISM_COMPATIBILITY_UNTIL_NEW_PROSPECTIVE_EVIDENCE",
        "common_identity": common_identity,
        "model_identity": model_identity,
        "config_identity": config_identity,
        "code_identity": code_identity,
        "replicates": replicates,
        "condition_ids": list(CONDITIONS),
        "execution_order_policy": "ODD_CONTROL_FIRST_EVEN_INTERVENTION_FIRST",
        "parent_snapshot_hash": parent["state_hash"],
        "branch_start_snapshot_hash": parent["state_hash"],
        "one_shot_intervention_envelope_hash": envelope["envelope_hash"],
        "branch_row_count": len(rows),
        "branch_manifest_hashes": [x["branch_hash"] for x in manifests],
        "forward_contract_hashes": {
            "experimental_variable_registry_v0.2": _contract_hash("configs/experimental_variable_registry_v0.2.json"),
            "first_paper_mechanism_contract_v0.3": _contract_hash("configs/first_paper_mechanism_contract_v0.3.json"),
            "first_paper_analysis_contract_v0.2": _contract_hash("configs/first_paper_analysis_contract_v0.2.json"),
        },
        "automatic_paid_evaluator": False,
        "authorization_status": "NOT_AUTHORIZED",
        "prospective_confirmation_status": "NOT_ESTABLISHED_EXISTING_PHASE_A_SOURCE",
    }
    plan["plan_hash"] = _hash_without(plan, "plan_hash")
    bundle = {"plan": plan, "parent_snapshot": parent, "one_shot_envelope": envelope, "branch_rows": rows, "branch_manifests": manifests}
    verify_one_shot_branch_plan(bundle)
    return bundle


def verify_one_shot_branch_plan(bundle):
    plan = bundle["plan"]
    parent = bundle["parent_snapshot"]
    envelope = bundle["one_shot_envelope"]
    rows = bundle["branch_rows"]
    manifests = bundle["branch_manifests"]
    _require(plan.get("schema") == PLAN_SCHEMA, "one_shot_plan_schema_invalid")
    _require(plan.get("authorization_status") == "NOT_AUTHORIZED", "one_shot_plan_must_not_self_authorize")
    _require(plan.get("plan_hash") == _hash_without(plan, "plan_hash"), "one_shot_plan_hash_mismatch")
    verify_state_snapshot(parent)
    _require(plan["parent_snapshot_hash"] == parent["state_hash"] == plan["branch_start_snapshot_hash"], "one_shot_plan_parent_start_mismatch")
    _require(len(rows) == len(manifests) == plan["branch_row_count"] == plan["replicates"] * 2, "one_shot_plan_row_count_mismatch")
    by_hash = {x["branch_hash"]: x for x in manifests}
    for row in rows:
        manifest = by_hash[row["branch_hash"]]
        bound = None if row["condition_id"] == CONTROL_CONDITION else envelope
        verify_branch_manifest_v3(manifest, parent_snapshot=parent, envelope=bound)
        _require(row["parent_state_hash"] == row["branch_start_state_hash"] == parent["state_hash"], "one_shot_row_state_mismatch")
    return True


def _selected_trace(selection_package, traces):
    matches = [x for x in traces if stable_hash(x) == selection_package.get("trace_hash")]
    _require(len(matches) == 1, "selection_package_must_match_one_trace")
    return matches[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selection-package", required=True)
    ap.add_argument("--baseline-traces", required=True)
    ap.add_argument("--replicates", required=True, type=int)
    ap.add_argument("--branch-code-sha")
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    selection = load_json(args.selection_package)
    traces = load_jsonl(args.baseline_traces)
    baseline = _selected_trace(selection, traces)
    bundle = build_one_shot_branch_plan(selection, baseline, replicates=args.replicates, branch_code_sha=args.branch_code_sha)
    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_one_shot_plan_dir")
    out.mkdir(parents=True)
    (out / "branch_plan.json").write_text(json.dumps(bundle["plan"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "parent_snapshot.json").write_text(json.dumps(bundle["parent_snapshot"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "one_shot_intervention_envelope.json").write_text(json.dumps(bundle["one_shot_envelope"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_jsonl(out / "branch_execution_manifest.jsonl", bundle["branch_rows"])
    write_jsonl(out / "branch_manifests.jsonl", bundle["branch_manifests"])
    print("ONE_SHOT_PLAN=PREPARED_OFFLINE")
    print("PLAN_HASH=" + bundle["plan"]["plan_hash"])
    print("PARENT_EQUALS_BRANCH_START=YES")
    print("PAID_API_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
