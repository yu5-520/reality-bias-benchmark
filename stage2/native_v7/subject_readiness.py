"""Manual Stage-II v7 subject-readiness gate.

This module deliberately does not execute T1-T3, reserve a natural cell, call an
evaluator, or mutate registry.json. It supports one common, non-scientific
provider handshake because all seven X conditions share the same frozen subject
binding. A reviewed commit is still required to promote any X to SUBJECT_READY.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
from pathlib import Path

from adapters.deepseek_chat import chat_completion, extract_content
from stage2.native_v7.policy import READINESS_AUTHORIZATION, load_registry
from stage2.native_v7.readiness_evidence import execution_snapshot

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "stage2"
SUBJECT_PATH = STAGE2 / "subject.json"
HANDSHAKE_MAX_COMPLETION_TOKENS = 32


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _natural_attempt_count():
    total = 0
    for path in sorted((STAGE2 / "natural_v7").glob("*/manifest.json")):
        manifest = json.loads(path.read_text())
        total += int(manifest.get("natural_attempts_for_cell", 0))
    return total


def _write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return path


def _require_sha(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError(f"{label} must be an exact 40-character lowercase git SHA")
    return value


def _load_subject_binding():
    subject = json.loads(SUBJECT_PATH.read_text())
    model_path = ROOT / subject["source_config"]
    model = json.loads(model_path.read_text())
    if (
        model.get("provider") != subject.get("provider")
        or model.get("model_alias") != subject.get("model_alias")
        or model.get("expected_model_version") != subject.get("expected_model_version")
        or model.get("subject") != subject.get("subject")
    ):
        raise ValueError("Stage-II subject.json differs from its frozen model source")
    if subject.get("limits", {}).get("automatic_paid_evaluator") is not False:
        raise ValueError("Stage-II subject binding unexpectedly permits a paid evaluator")
    return subject, model, model_path


def _asset_state(registry, probe):
    spec = registry["probes"][probe]
    if probe == "X6":
        return spec.get("study_embedding", {}).get("state")
    if probe == "X7":
        return spec.get("study_checkpoint", {}).get("state")
    return None


def build_preflight(
    *,
    expected_execution_sha,
    actual_execution_sha,
    authorization_phrase,
    max_subject_calls,
    spending_ceiling,
):
    expected_execution_sha = _require_sha(expected_execution_sha, "expected_execution_sha")
    actual_execution_sha = _require_sha(actual_execution_sha, "actual_execution_sha")
    if expected_execution_sha != actual_execution_sha:
        raise ValueError("readiness must run on the exact explicitly frozen execution SHA")
    if authorization_phrase != READINESS_AUTHORIZATION:
        raise ValueError("subject-readiness authorization phrase is not exact")

    registry = load_registry()
    gate = registry["subject_readiness_gate"]
    if gate["state"] != "IMPLEMENTED_NO_LIVE_RECEIPT":
        raise ValueError("common provider handshake has already been recorded")
    max_subject_calls = int(max_subject_calls)
    spending_ceiling = float(spending_ceiling)
    if max_subject_calls != gate["max_provider_calls"] or max_subject_calls != 1:
        raise ValueError("Stage-II readiness permits exactly one provider call")
    if not 0 < spending_ceiling <= float(gate["max_spending_ceiling_usd"]):
        raise ValueError("readiness spending ceiling exceeds frozen policy")

    subject, model, model_path = _load_subject_binding()
    states = {pid: spec["collection_state"] for pid, spec in registry["probes"].items()}
    if any(state not in {"NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING", "SUBJECT_READY"} for state in states.values()):
        raise ValueError("every X must have a verified native runner before subject readiness")

    blockers = {}
    for probe in ("X6", "X7"):
        state = _asset_state(registry, probe)
        if state != "FROZEN_MANIFEST_VERIFIED":
            blockers[probe] = state or "MISSING"

    eligible_after_common_handshake = [
        probe for probe in sorted(registry["probes"])
        if probe not in blockers and states[probe] != "SUBJECT_READY"
    ]
    payload = {
        "schema": "stage2-subject-readiness-preflight-v1",
        "status": "READY_FOR_ONE_COMMON_PROVIDER_HANDSHAKE",
        "execution_code_sha": actual_execution_sha,
        "authorization_phrase_sha256": hashlib.sha256(
            authorization_phrase.encode("utf-8")
        ).hexdigest(),
        "max_provider_calls": 1,
        "spending_ceiling_usd": spending_ceiling,
        "automatic_paid_evaluator": False,
        "scientific_task_used": False,
        "natural_cell_reserved": False,
        "registry_mutation_allowed": False,
        "subject_path": str(SUBJECT_PATH.relative_to(ROOT)),
        "subject_config_sha256": sha256(SUBJECT_PATH),
        "model_config_path": str(model_path.relative_to(ROOT)),
        "model_config_sha256": sha256(model_path),
        "execution_snapshot": execution_snapshot(),
        "provider": subject["provider"],
        "model_alias": subject["model_alias"],
        "expected_model_version": subject["expected_model_version"],
        "subject_parameters": subject["subject"],
        "probe_states_before_handshake": states,
        "eligible_after_common_handshake": eligible_after_common_handshake,
        "asset_blockers": blockers,
        "handshake_max_completion_tokens": HANDSHAKE_MAX_COMPLETION_TOKENS,
        "promotion_rule": gate["promotion_rule"],
        "natural_trajectories_before_handshake": _natural_attempt_count(),
    }
    return payload


def _cost_usd(response, model_config):
    usage = response.get("usage") or {}
    if not usage:
        raise RuntimeError("provider handshake returned no usage accounting")
    prompt = int(usage.get("prompt_tokens") or 0)
    hit = int(usage.get("prompt_cache_hit_tokens") or 0)
    miss_raw = usage.get("prompt_cache_miss_tokens")
    miss = int(miss_raw) if miss_raw is not None else max(prompt - hit, 0)
    completion = int(usage.get("completion_tokens") or 0)
    rates = model_config["pricing_snapshot_usd_per_million_tokens"]["peak"]
    cost = (
        hit * float(rates["input_cache_hit"])
        + miss * float(rates["input_cache_miss"])
        + completion * float(rates["output"])
    ) / 1_000_000
    return round(cost, 9), usage


def execute_handshake(*, preflight_path, out_path):
    preflight = json.loads(Path(preflight_path).read_text())
    if preflight.get("schema") != "stage2-subject-readiness-preflight-v1":
        raise ValueError("unexpected readiness preflight schema")
    if preflight.get("status") != "READY_FOR_ONE_COMMON_PROVIDER_HANDSHAKE":
        raise ValueError("readiness preflight is not executable")
    if preflight.get("max_provider_calls") != 1:
        raise ValueError("readiness preflight does not enforce one provider call")
    if preflight.get("scientific_task_used") is not False:
        raise ValueError("readiness preflight attempted to use a scientific task")
    current_natural_attempts = _natural_attempt_count()
    if current_natural_attempts != int(preflight.get("natural_trajectories_before_handshake", -1)):
        raise RuntimeError("natural evidence count changed after readiness preflight")
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("DEEPSEEK_API_KEY is required for the manual readiness handshake")
    workflow_run_id = int(os.environ.get("GITHUB_RUN_ID", "0"))
    if workflow_run_id <= 0:
        raise RuntimeError("readiness handshake requires a recorded workflow run ID")

    subject, model_config, model_path = _load_subject_binding()
    if sha256(SUBJECT_PATH) != preflight["subject_config_sha256"]:
        raise RuntimeError("subject binding changed after readiness preflight")
    if sha256(model_path) != preflight["model_config_sha256"]:
        raise RuntimeError("model configuration changed after readiness preflight")
    if execution_snapshot() != preflight["execution_snapshot"]:
        raise RuntimeError("execution inputs changed after readiness preflight")

    call_config = copy.deepcopy(model_config)
    call_config["subject"]["max_tokens"] = HANDSHAKE_MAX_COMPLETION_TOKENS
    call_config["transport"]["max_retries"] = 1
    call_config["json_format_retries"] = 1
    messages = [
        {
            "role": "system",
            "content": "This is a non-scientific provider connectivity check. Reply briefly.",
        },
        {
            "role": "user",
            "content": "Return a short readiness acknowledgement. Do not solve any software task.",
        },
    ]

    out_path = Path(out_path)
    failure_path = out_path.with_name(out_path.stem + "_failure.json")
    try:
        response = chat_completion(
            call_config,
            messages,
            evaluator=False,
            response_format_json=False,
        )
        content = extract_content(response)
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("provider handshake returned an empty assistant response")
        cost, usage = _cost_usd(response, model_config)
        if cost > float(preflight["spending_ceiling_usd"]):
            raise RuntimeError(
                f"provider handshake cost {cost} exceeded frozen ceiling "
                f"{preflight['spending_ceiling_usd']}"
            )
        raw_path = out_path.with_name(out_path.stem + "_raw_response.json")
        _write_json(raw_path, response)
        receipt = {
            "schema": "stage2-subject-readiness-receipt-v1",
            "status": "COMMON_PROVIDER_HANDSHAKE_RECORDED_NOT_SUBJECT_READY",
            "execution_code_sha": preflight["execution_code_sha"],
            "workflow_run_id": workflow_run_id,
            "provider": subject["provider"],
            "requested_model_alias": subject["model_alias"],
            "expected_model_version": subject["expected_model_version"],
            "observed_response_model": response.get("model"),
            "response_id": response.get("id"),
            "finish_reason": (response.get("choices") or [{}])[0].get("finish_reason"),
            "usage": usage,
            "estimated_peak_cost_usd": cost,
            "spending_ceiling_usd": preflight["spending_ceiling_usd"],
            "provider_call_count": 1,
            "automatic_paid_evaluator": False,
            "scientific_task_used": False,
            "natural_cell_reserved": False,
            "registry_mutated": False,
            "natural_trajectories_before_handshake": current_natural_attempts,
            "natural_trajectories_after_handshake": _natural_attempt_count(),
            "subject_config_sha256": preflight["subject_config_sha256"],
            "model_config_sha256": preflight["model_config_sha256"],
            "execution_snapshot": preflight["execution_snapshot"],
            "preflight_sha256": sha256(preflight_path),
            "raw_response_sha256": sha256(raw_path),
            "eligible_probes_after_common_handshake": preflight[
                "eligible_after_common_handshake"
            ],
            "remaining_asset_blockers": preflight["asset_blockers"],
            "promotion_required": "REVIEWED_REGISTRY_COMMIT",
        }
        if receipt["natural_trajectories_after_handshake"] != current_natural_attempts:
            raise RuntimeError("natural evidence count changed during provider handshake")
        _write_json(out_path, receipt)
        return receipt
    except Exception as exc:
        _write_json(
            failure_path,
            {
                "schema": "stage2-subject-readiness-failure-v1",
                "status": "PROVIDER_HANDSHAKE_FAILED_PRESERVED",
                "execution_code_sha": preflight.get("execution_code_sha"),
                "error_type": type(exc).__name__,
                "error": str(exc),
                "provider_call_limit": 1,
                "automatic_paid_evaluator": False,
                "scientific_task_used": False,
                "natural_cell_reserved": False,
                "registry_mutated": False,
            },
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    preflight = sub.add_parser("preflight")
    preflight.add_argument("--expected-execution-sha", required=True)
    preflight.add_argument("--actual-execution-sha", required=True)
    preflight.add_argument("--authorization-phrase", required=True)
    preflight.add_argument("--max-subject-calls", required=True, type=int)
    preflight.add_argument("--spending-ceiling", required=True, type=float)
    preflight.add_argument("--out", required=True)

    handshake = sub.add_parser("handshake")
    handshake.add_argument("--preflight", required=True)
    handshake.add_argument("--out", required=True)

    args = parser.parse_args()
    if args.command == "preflight":
        payload = build_preflight(
            expected_execution_sha=args.expected_execution_sha,
            actual_execution_sha=args.actual_execution_sha,
            authorization_phrase=args.authorization_phrase,
            max_subject_calls=args.max_subject_calls,
            spending_ceiling=args.spending_ceiling,
        )
        _write_json(args.out, payload)
    else:
        payload = execute_handshake(preflight_path=args.preflight, out_path=args.out)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
