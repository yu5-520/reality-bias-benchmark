#!/usr/bin/env python3
import copy
import json
from pathlib import Path

from arena.core import stable_hash

ROOT = Path(__file__).resolve().parents[1]
DESIGN_HASH = "5064e255da26949a152a2300fe659ebdddddc9b44f1a97a4b31d7796005a959d"
FORMAL_GATE_V01_HASH = "af62079cf9d0727813095648cb85268895b960f7d14fb5644e3151f6711bbcf9"
RUNTIME_GATE_HASH = "97650361491e310490e18c9598540a5df9c6e3d3ca9ba62a1e6ae7f8cd8ffa90"


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def digest_without(row, key):
    material = copy.deepcopy(row)
    material.pop(key, None)
    return stable_hash(material)


freeze = load("manifests/r6d_matched_stock_robustness_design_freeze_2026-09-17_v0_1.json")
plan = load("configs/r6/r6d_matched_stock_robustness_plan_v0.1.json")
gate1 = load("configs/r6/r6d_matched_stock_robustness_formal_subject_gate_v0.1.json")
gate2 = load("configs/r6/r6d_matched_stock_robustness_formal_subject_gate_v0.2.json")

assert freeze["design_hash"] == DESIGN_HASH
assert plan["design_hash"] == DESIGN_HASH
assert gate1["gate_hash"] == FORMAL_GATE_V01_HASH
assert gate2["schema"] == "RB-R6D-MATCHED-STOCK-ROBUSTNESS-FORMAL-SUBJECT-GATE-v0.2"
assert gate2["status"] == "RUNTIME_BOUND_GATE_CLOSED_NOT_AUTHORIZATION"
assert gate2["gate_hash"] == RUNTIME_GATE_HASH == digest_without(gate2, "gate_hash")
assert gate2["design_freeze"]["design_hash"] == DESIGN_HASH
assert gate2["design_freeze"]["formal_gate_v0_1_hash"] == FORMAL_GATE_V01_HASH

binding = gate2["runtime_binding"]
expected_paths = {
    "runtime_plan_builder_path": "arena/prepare_r6d_matched_stock_plan.py",
    "offline_smoke_path": "arena/r6d_matched_stock_runtime_smoke.py",
    "real_subject_runner_path": "arena/run_r6d_matched_stock_real.py",
    "raw_evidence_freezer_path": "arena/freeze_r6d_matched_stock_raw_evidence.py",
    "real_subject_workflow_path": ".github/workflows/r6d-matched-stock-subject-real.yml",
    "runtime_readiness_workflow_path": ".github/workflows/r6d-matched-stock-runtime-readiness-v0-1.yml",
}
for key, value in expected_paths.items():
    assert binding[key] == value
    assert (ROOT / value).is_file(), "missing_runtime_binding:" + value
assert binding["runtime_plan_builder_bound"] is True
assert binding["offline_smoke_bound"] is True
assert binding["real_subject_runner_bound"] is True
assert binding["raw_evidence_freezer_bound"] is True
assert binding["real_subject_workflow_bound"] is True

x = gate2["exact_execution_gate"]
assert x["authorization_phrase"] == "CALL_REAL_R6D_MATCHED_STOCK_API"
assert x["confirm_design_hash_required"] == DESIGN_HASH
assert x["manual_workflow_dispatch_only"] is True
assert x["preflight_required_before_provider_call"] is True
assert x["raw_evidence_freeze_before_derivation_required"] is True
assert x["raw_artifact_upload_before_derivation_required"] is True
assert x["automatic_retry_or_replacement_authorized"] is False

assert gate2["authorization_status"] == "NOT_AUTHORIZED"
assert gate2["scientific_provider_run_authorized"] is False
assert gate2["paid_evaluator_run_authorized"] is False
assert gate2["semantic_cpr_adjudication_authorized"] is False

real_wf = (ROOT / binding["real_subject_workflow_path"]).read_text(encoding="utf-8")
assert "workflow_dispatch:" in real_wf
assert "\n  push:" not in real_wf
assert "\n  pull_request:" not in real_wf
assert "CALL_REAL_R6D_MATCHED_STOCK_API" in real_wf
assert "confirm_design_hash" in real_wf
assert "--preflight-only" in real_wf
assert "--execute-real-api" in real_wf
assert "secrets.DEEPSEEK_API_KEY" in real_wf
assert "freeze_r6d_matched_stock_raw_evidence" in real_wf
assert "Upload raw scientific subject artifact before derivation" in real_wf
assert "PAID_EVALUATOR_CALLED=NO" in real_wf
assert "SEMANTIC_CPR_STATUS=NOT_ADJUDICATED" in real_wf

ready_wf = (ROOT / binding["runtime_readiness_workflow_path"]).read_text(encoding="utf-8")
expression_prefix = '$' + '{{ secrets.'
for forbidden in (
    "DEEPSEEK_API_KEY: " + expression_prefix,
    "DASHSCOPE_API_KEY: " + expression_prefix,
    "OPENAI_API_KEY: " + expression_prefix,
    "\n            --execute-" + "real-api",
):
    assert forbidden not in ready_wf, "runtime_readiness_contains_real_execution_capability:" + forbidden

print("PASS: matched-stock runtime readiness bindings are complete, content-addressed, and fail-closed")
print("DESIGN_HASH=" + DESIGN_HASH)
print("RUNTIME_GATE_HASH=" + RUNTIME_GATE_HASH)
print("SCIENTIFIC_PROVIDER_RUN_AUTHORIZED=NO")
