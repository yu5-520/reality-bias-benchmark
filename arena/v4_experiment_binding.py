from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
from typing import Any, Mapping

from .branch_plan import verify_branch_plan
from .core import stable_hash
from .io_utils import load_json, load_jsonl, sha256_file


ROOT = Path(__file__).resolve().parents[1]
BINDING_SCHEMA = "RB-R5R6-V4-RESEARCH-BINDING-v0.1"
EXPERIMENT_FAMILY = "R5R6-FROZEN-PARENT-BRANCH-v0.1"

INTERFACE_SPECS = {
    "experimental_variable_registry": {
        "path": "configs/experimental_variable_registry_v0.1.json",
        "identity": "RB-EXPERIMENTAL-VARIABLE-REGISTRY-v0.1",
    },
    "measurement_boundary_registry": {
        "path": "configs/measurement_boundary_registry_v0.1.json",
        "identity": "RB-MEASUREMENT-BOUNDARY-REGISTRY-v0.1",
    },
    "behavior_event_schema": {
        "path": "schemas/behavior_event_v0.1.schema.json",
        "identity": "RB-BEHAVIOR-EVENT-v0.1",
    },
    "system_trajectory_measurement_schema": {
        "path": "schemas/system_trajectory_measurement_v4.schema.json",
        "identity": "RB-SYSTEM-TRAJECTORY-MEASUREMENT-v4.0",
    },
    "system_behavior_adapter": {
        "path": "arena/system_behavior_adapter.py",
        "identity": "RB-SYSTEM-BEHAVIOR-ADAPTER-v0.1",
    },
    "structural_jump_detector": {
        "path": "configs/structural_jump_detector_v0.1.json",
        "identity": "RB-STRUCTURAL-JUMP-DETECTOR-v0.1",
    },
    "operational_boundary_set": {
        "path": "configs/operational_boundary_set_v0.1.json",
        "identity": "RB-OPERATIONAL-BOUNDARY-SET-v0.1",
    },
    "source_lineage_rules": {
        "path": "configs/source_lineage_rules_v0.1.json",
        "identity": "RB-SOURCE-LINEAGE-RULES-v0.1",
    },
    "measurement_contract": {
        "path": "docs/system_behavior_measurement_plan_v4.md",
        "identity": "SYSTEM-BEHAVIOR-MEASUREMENT-PLAN-v4",
    },
    "first_paper_analysis_contract": {
        "path": "configs/first_paper_analysis_contract_v0.1.json",
        "identity": "RB-FIRST-PAPER-ANALYSIS-CONTRACT-v0.1",
    },
    "first_paper_analysis_contract_schema": {
        "path": "schemas/first_paper_analysis_contract_v0.1.schema.json",
        "identity": "RB-FIRST-PAPER-ANALYSIS-CONTRACT-v0.1",
    },
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _hash_without(record: Mapping[str, Any], key: str) -> str:
    material = copy.deepcopy(dict(record))
    material.pop(key, None)
    return stable_hash(material)


def _load_plan_bundle(plan_dir: str | Path) -> dict[str, Any]:
    plan_dir = Path(plan_dir)
    bundle = {
        "plan": load_json(plan_dir / "branch_plan.json"),
        "parent_snapshot": load_json(plan_dir / "parent_snapshot.json"),
        "intervention_start_snapshot": load_json(plan_dir / "intervention_start_snapshot.json"),
        "branch_rows": load_jsonl(plan_dir / "branch_execution_manifest.jsonl"),
        "branch_manifests": load_jsonl(plan_dir / "branch_manifests.jsonl"),
    }
    verify_branch_plan(bundle)
    return bundle


def _interface_bindings(root: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for name, spec in INTERFACE_SPECS.items():
        path = root / spec["path"]
        _require(path.is_file(), f"v4_interface_missing:{spec['path']}")
        out[name] = {
            "path": spec["path"],
            "sha256": sha256_file(path),
            "identity": spec["identity"],
        }
    return out


def _registered_variable(root: Path, variable_id: str) -> dict[str, Any]:
    registry = load_json(root / INTERFACE_SPECS["experimental_variable_registry"]["path"])
    rows = [row for row in registry.get("variables", []) if row.get("variable_id") == variable_id]
    _require(len(rows) == 1, f"v4_variable_registry_exactly_one_match_required:{variable_id}")
    return rows[0]


def _first_paper_analysis_contract(root: Path) -> dict[str, Any]:
    contract = load_json(root / INTERFACE_SPECS["first_paper_analysis_contract"]["path"])
    _require(contract.get("schema") == "RB-FIRST-PAPER-ANALYSIS-CONTRACT-v0.1", "v4_binding_first_paper_contract_schema_invalid")
    _require(contract.get("status") == "FROZEN_BEFORE_NEW_V4_SUBJECT_EVIDENCE", "v4_binding_first_paper_contract_not_frozen")
    variable = contract.get("experimental_variable") or {}
    _require(variable.get("variable_id") == "EPISTEMIC_STATUS_DOWNGRADE", "v4_binding_first_paper_variable_mismatch")
    _require(variable.get("stage") == "MID", "v4_binding_first_paper_stage_mismatch")
    return contract


def build_v4_research_binding(
    bundle: Mapping[str, Any],
    *,
    code_sha: str,
    branch_plan_file_sha256: str,
    root: Path = ROOT,
    experimental_variable_id: str = "EPISTEMIC_STATUS_DOWNGRADE",
) -> dict[str, Any]:
    verify_branch_plan(bundle)
    _require(isinstance(code_sha, str) and code_sha, "v4_binding_code_sha_required")
    _require(isinstance(branch_plan_file_sha256, str) and len(branch_plan_file_sha256) == 64, "branch_plan_file_sha256_required")

    plan = bundle["plan"]
    plan_code = (plan.get("code_identity") or {}).get("branch_execution_commit")
    _require(code_sha == plan_code, "v4_binding_code_sha_must_match_branch_plan_execution_commit")
    _require(plan.get("authorization_status") == "NOT_AUTHORIZED", "v4_binding_requires_non_authorized_plan")

    variable = _registered_variable(root, experimental_variable_id)
    _require(variable.get("family") == "CONTAINMENT", "v4_binding_variable_family_must_be_containment")
    _require(variable.get("stage") == "MID", "v4_binding_variable_stage_must_be_mid")
    intervention_family = (plan.get("intervention_spec") or {}).get("intervention_family")
    _require(
        intervention_family == "EPISTEMIC_STATUS_DOWNGRADE_TO_PROVISIONAL",
        "v4_binding_intervention_family_unexpected",
    )
    first_paper_contract = _first_paper_analysis_contract(root)
    _require(
        (first_paper_contract.get("experimental_variable") or {}).get("variable_id") == experimental_variable_id,
        "v4_binding_first_paper_variable_does_not_match_binding",
    )
    interfaces = _interface_bindings(root)

    binding = {
        "schema": BINDING_SCHEMA,
        "version": "0.1",
        "experiment_family": EXPERIMENT_FAMILY,
        "branch_plan_hash": plan["plan_hash"],
        "branch_plan_file_sha256": branch_plan_file_sha256,
        "source_trace_hash": (plan.get("common_identity") or {}).get("source_trace_hash"),
        "source_evidence_hash": (plan.get("common_identity") or {}).get("source_evidence_hash"),
        "selection_record_hash": (plan.get("common_identity") or {}).get("selection_record_hash"),
        "parent_state_hash": plan.get("parent_snapshot_hash"),
        "intervention_start_state_hash": plan.get("intervention_start_snapshot_hash"),
        "experimental_variable_id": experimental_variable_id,
        "experimental_variable_family": variable.get("family"),
        "experimental_variable_stage": variable.get("stage"),
        "target_boundary_family": list(variable.get("target_boundary_family") or []),
        "intervention_family": intervention_family,
        "first_paper_analysis_contract_hash": stable_hash(first_paper_contract),
        "first_paper_analysis_contract_file_sha256": interfaces["first_paper_analysis_contract"]["sha256"],
        "code_sha": code_sha,
        "interface_bindings": interfaces,
        "authorization_status": "NOT_AUTHORIZED",
        "semantic_status": "NOT_ADJUDICATED",
        "scientific_status": "CANDIDATE_UNTIL_EXPLICIT_REAL_RUN_FREEZE_AND_API_AUTHORIZATION",
        "paid_api_authorized": False,
        "automatic_paid_evaluator": False,
        "warning": (
            "This binding freezes the research and first-paper analysis interfaces used to interpret a future Phase-B subject batch. "
            "It is not paid-run authorization and does not establish semantic C/P/R, adoption, Authority Penetration, or a causal effect."
        ),
    }
    binding["binding_hash"] = _hash_without(binding, "binding_hash")
    return binding


def verify_v4_research_binding(
    binding: Mapping[str, Any],
    bundle: Mapping[str, Any],
    *,
    code_sha: str,
    branch_plan_file_sha256: str,
    root: Path = ROOT,
) -> bool:
    verify_branch_plan(bundle)
    plan = bundle["plan"]
    _require(binding.get("schema") == BINDING_SCHEMA, "v4_binding_schema_invalid")
    _require(binding.get("version") == "0.1", "v4_binding_version_invalid")
    _require(binding.get("experiment_family") == EXPERIMENT_FAMILY, "v4_binding_experiment_family_invalid")
    _require(binding.get("authorization_status") == "NOT_AUTHORIZED", "v4_binding_must_not_self_authorize")
    _require(binding.get("paid_api_authorized") is False, "v4_binding_paid_api_authorized_must_be_false")
    _require(binding.get("automatic_paid_evaluator") is False, "v4_binding_paid_evaluator_must_be_false")
    _require(binding.get("semantic_status") == "NOT_ADJUDICATED", "v4_binding_semantic_status_invalid")
    _require(binding.get("binding_hash") == _hash_without(binding, "binding_hash"), "v4_binding_hash_mismatch")
    _require(binding.get("branch_plan_hash") == plan.get("plan_hash"), "v4_binding_branch_plan_hash_mismatch")
    _require(
        binding.get("branch_plan_file_sha256") == branch_plan_file_sha256,
        "v4_binding_branch_plan_file_sha256_mismatch",
    )
    _require(binding.get("code_sha") == code_sha, "v4_binding_code_sha_mismatch")
    _require(
        code_sha == (plan.get("code_identity") or {}).get("branch_execution_commit"),
        "v4_binding_code_sha_does_not_match_plan",
    )

    variable_id = binding.get("experimental_variable_id")
    variable = _registered_variable(root, variable_id)
    _require(binding.get("experimental_variable_family") == variable.get("family"), "v4_binding_variable_family_mismatch")
    _require(binding.get("experimental_variable_stage") == variable.get("stage"), "v4_binding_variable_stage_mismatch")
    _require(binding.get("target_boundary_family") == list(variable.get("target_boundary_family") or []), "v4_binding_target_boundary_family_mismatch")

    first_paper_contract = _first_paper_analysis_contract(root)
    _require(binding.get("first_paper_analysis_contract_hash") == stable_hash(first_paper_contract), "v4_binding_first_paper_contract_hash_mismatch")
    expected_interfaces = _interface_bindings(root)
    _require(binding.get("interface_bindings") == expected_interfaces, "v4_binding_research_interface_hash_mismatch")
    _require(
        binding.get("first_paper_analysis_contract_file_sha256") == expected_interfaces["first_paper_analysis_contract"]["sha256"],
        "v4_binding_first_paper_contract_file_sha256_mismatch",
    )
    return True


def prepare_v4_binding(
    *,
    plan_dir: str | Path,
    code_sha: str,
    out_path: str | Path | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    plan_dir = Path(plan_dir)
    bundle = _load_plan_bundle(plan_dir)
    branch_plan_path = plan_dir / "branch_plan.json"
    plan_file_hash = sha256_file(branch_plan_path)
    binding = build_v4_research_binding(
        bundle,
        code_sha=code_sha,
        branch_plan_file_sha256=plan_file_hash,
        root=root,
    )
    verify_v4_research_binding(
        binding,
        bundle,
        code_sha=code_sha,
        branch_plan_file_sha256=plan_file_hash,
        root=root,
    )
    destination = Path(out_path) if out_path else plan_dir / "v4_research_binding.json"
    if destination.exists():
        raise ValueError("refusing_to_overwrite_v4_research_binding")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(binding, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return binding


def load_and_verify_v4_binding(
    plan_dir: str | Path,
    bundle: Mapping[str, Any],
    *,
    code_sha: str,
    root: Path = ROOT,
) -> dict[str, Any]:
    plan_dir = Path(plan_dir)
    binding_path = plan_dir / "v4_research_binding.json"
    _require(binding_path.is_file(), "v4_research_binding_required")
    binding = load_json(binding_path)
    verify_v4_research_binding(
        binding,
        bundle,
        code_sha=code_sha,
        branch_plan_file_sha256=sha256_file(plan_dir / "branch_plan.json"),
        root=root,
    )
    return binding


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-dir", required=True)
    parser.add_argument("--code-sha")
    parser.add_argument("--out")
    args = parser.parse_args()
    code_sha = args.code_sha or os.environ.get("GITHUB_SHA") or "LOCAL_OR_UNRECORDED"
    binding = prepare_v4_binding(
        plan_dir=args.plan_dir,
        code_sha=code_sha,
        out_path=args.out,
    )
    print(f"V4_RESEARCH_BINDING=PASS hash={binding['binding_hash']}")
    print(f"FIRST_PAPER_ANALYSIS_CONTRACT_HASH={binding['first_paper_analysis_contract_hash']}")
    print("AUTHORIZATION_STATUS=NOT_AUTHORIZED")
    print("PAID_API_AUTHORIZED=NO")
    print("SEMANTIC_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
