from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl

INTERVENTION = "ONE_SHOT_JUMP_INTERVENTION"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _event_ref(run_id: str, event_index: int) -> str:
    return f"{run_id}:event:{event_index}"


def _call_ref(run_id: str, turn: int, actor: str) -> str:
    return f"{run_id}:turn:{turn}:actor:{actor}"


def _carrier_candidates(trace: dict, first_call: dict) -> list[dict]:
    out = []
    pre_state = (first_call.get("runtime_snapshot") or {}).get("shared_state") or {}
    for event in trace.get("events") or []:
        if not (first_call["event_index_start"] <= event["event_index"] <= first_call["event_index_end"]):
            continue
        if event.get("action_type") not in ("write_state", "revise_final_state"):
            continue
        action = event.get("action") or {}
        ref = _event_ref(trace["run_id"], event["event_index"])
        key = action.get("key")
        preexisting = bool(key is not None and key in pre_state)
        row = {
            "ref": ref,
            "event_index": event["event_index"],
            "turn": event["turn"],
            "actor": event["actor"],
            "action_type": event["action_type"],
            "state_key": key,
            "preexisting_state_key": preexisting,
            "preexisting_value_hash": stable_hash(pre_state.get(key)) if preexisting else None,
            "value_hash": stable_hash(action.get("value")) if key is not None else None,
            "value_changed_from_preexposure": (
                stable_hash(pre_state.get(key)) != stable_hash(action.get("value"))
                if preexisting and key is not None
                else None
            ),
            "patch_hash": stable_hash(action.get("patch")) if action.get("patch") is not None else None,
            "structural_role": "DIRECT_EXPOSURE_TURN_CARRIER_CANDIDATE",
        }
        row["carrier_hash"] = stable_hash(row)
        out.append(row)
    return out


def _target_status(call: dict, target_key: str):
    snapshot = call.get("runtime_snapshot") or {}
    metadata = snapshot.get("shared_state_metadata") or {}
    return (metadata.get(target_key) or {}).get("status")


def _visible_carrier_refs(call: dict, carriers: list[dict]) -> list[str]:
    snapshot = call.get("runtime_snapshot") or {}
    state = snapshot.get("shared_state") or {}
    visible = []
    for carrier in carriers:
        key = carrier.get("state_key")
        if key and key in state:
            visible.append(carrier["ref"])
    return visible


def derive(*, traces_path: str, case_bindings_path: str, evidence_batch_path: str):
    traces = load_jsonl(traces_path)
    case_bindings = load_jsonl(case_bindings_path)
    evidence_batch = load_json(evidence_batch_path)

    _require(len(traces) == 24, "r5r6_structural_audit_requires_24_frozen_r5_traces")
    _require(evidence_batch.get("preserved_trace_count") == 24, "r5r6_evidence_batch_count_mismatch")
    _require(evidence_batch.get("runner_error_count") == 0, "r5r6_source_evidence_has_runner_errors")

    cases = {row["case_id"]: row for row in case_bindings}
    _require(len(cases) == 6, "r5r6_requires_6_source_bound_cases")

    interventions = [row for row in traces if row.get("condition_id") == INTERVENTION]
    _require(len(interventions) == 12, "r5r6_requires_12_intervention_continuations")

    records = []
    for trace in sorted(interventions, key=lambda x: (x["wave_id"], x["replicate_index"])):
        case_id = trace["case_id"]
        _require(case_id in cases, "r5r6_case_binding_missing:" + case_id)
        _require(trace.get("direct_experiment_origin_exposure_count") == 1, "r5r6_direct_exposure_count_mismatch")
        _require(trace.get("experiment_origin_reinjection_count") == 0, "r5r6_reinjection_detected")
        _require(trace.get("persistent_experiment_origin_mutation") is False, "r5r6_persistent_experiment_mutation_detected")

        transform_records = list(trace.get("runtime_transform_records") or [])
        _require(len(transform_records) == 1, "r5r6_requires_exactly_one_runtime_transform_record")
        transform = transform_records[0]
        calls = list(trace.get("model_calls") or [])
        _require(bool(calls), "r5r6_intervention_has_no_model_calls")
        first = calls[0]
        _require(first["agent_id"] == transform["actor"], "r5r6_exposure_actor_mismatch")
        _require(first["turn"] == transform["turn"], "r5r6_exposure_turn_mismatch")
        _require(transform["from_status"] == "fact" and transform["to_status"] == "unconfirmed", "r5r6_operator_mismatch")
        _require(transform.get("persistent_state_mutation") is False, "r5r6_transform_persisted")

        target_key = transform["state_key"]
        carriers = _carrier_candidates(trace, first)
        _require(bool(carriers), "r5r6_exposure_turn_has_no_carrier_candidate:" + trace["run_id"])

        downstream = []
        for call in calls[1:]:
            write_refs = []
            for event in trace.get("events") or []:
                if call["event_index_start"] <= event["event_index"] <= call["event_index_end"]:
                    if event.get("action_type") in ("write_state", "revise_final_state"):
                        write_refs.append(_event_ref(trace["run_id"], event["event_index"]))
            downstream.append({
                "call_ref": _call_ref(trace["run_id"], call["turn"], call["agent_id"]),
                "turn": call["turn"],
                "actor": call["agent_id"],
                "event_range": [call["event_index_start"], call["event_index_end"]],
                "target_status_seen": _target_status(call, target_key),
                "visible_direct_carrier_refs": _visible_carrier_refs(call, carriers),
                "downstream_write_refs": write_refs,
                "decision_summary_hash": stable_hash(call.get("decision_summary")),
            })

        record = {
            "schema": "RB-V5-CROSS-DOMAIN-R5R6-STRUCTURAL-OBSERVATION-v0.1",
            "case_id": case_id,
            "wave_id": trace["wave_id"],
            "domain_id": trace["domain_id"],
            "source_run_id": trace["source_run_id"],
            "source_case_hash": trace["source_case_hash"],
            "r5_run_id": trace["run_id"],
            "replicate_index": trace["replicate_index"],
            "target_state_key": target_key,
            "authority_transition": {
                "from_status": transform["from_status"],
                "to_status": transform["to_status"],
                "direct_exposure_count": 1,
                "experiment_origin_reinjection_count": 0,
                "persistent_experiment_origin_mutation": False,
            },
            "direct_exposure": {
                "call_ref": _call_ref(trace["run_id"], first["turn"], first["agent_id"]),
                "actor": first["agent_id"],
                "turn": first["turn"],
                "event_range": [first["event_index_start"], first["event_index_end"]],
                "decision_summary_hash": stable_hash(first.get("decision_summary")),
            },
            "direct_turn_carrier_candidates": carriers,
            "post_stimulus_call_count": len(downstream),
            "post_stimulus_target_statuses": [
                {"turn": row["turn"], "actor": row["actor"], "status": row["target_status_seen"]}
                for row in downstream
            ],
            "downstream_structural_observations": downstream,
            "structural_claim_status": "READY_FOR_LOCALIZED_SEMANTIC_AUDIT",
            "semantic_adoption_status": "NOT_ADJUDICATED",
            "case_level_system_inertia_status": "NOT_ADJUDICATED",
            "r7_status": "NOT_AUTHORIZED",
            "semantic_cpr_status": "NOT_ADJUDICATED",
        }
        record["structural_observation_hash"] = stable_hash(record)
        records.append(record)

    by_case = defaultdict(list)
    for row in records:
        by_case[row["case_id"]].append(row)

    case_summaries = []
    for case_id in sorted(by_case):
        rows = sorted(by_case[case_id], key=lambda x: x["replicate_index"])
        _require(len(rows) == 2, "r5r6_expected_two_intervention_replicates_per_case:" + case_id)
        case_summaries.append({
            "schema": "RB-V5-CROSS-DOMAIN-R5R6-STRUCTURAL-CASE-SUMMARY-v0.1",
            "case_id": case_id,
            "wave_id": rows[0]["wave_id"],
            "domain_id": rows[0]["domain_id"],
            "source_case_hash": rows[0]["source_case_hash"],
            "intervention_branch_count": 2,
            "direct_exposure_count_total": 2,
            "experiment_origin_reinjection_count_total": 0,
            "persistent_experiment_origin_mutation_present": False,
            "direct_turn_carrier_candidate_count": sum(len(r["direct_turn_carrier_candidates"]) for r in rows),
            "post_stimulus_call_count": sum(r["post_stimulus_call_count"] for r in rows),
            "branch_observation_hashes": [r["structural_observation_hash"] for r in rows],
            "semantic_audit_status": "PENDING",
            "r7_status": "NOT_AUTHORIZED",
        })
    for row in case_summaries:
        row["case_summary_hash"] = stable_hash(row)

    summary = {
        "schema": "RB-V5-CROSS-DOMAIN-R5R6-STRUCTURAL-OBSERVATION-SUMMARY-v0.1",
        "source_r5_evidence_batch_hash": evidence_batch["evidence_batch_hash"],
        "source_trace_count": 24,
        "intervention_trace_count": len(records),
        "case_count": len(case_summaries),
        "domain_case_counts": dict(sorted(Counter(row["domain_id"] for row in case_summaries).items())),
        "all_intervention_direct_exposure_count_exactly_one": True,
        "total_experiment_origin_reinjection_count": 0,
        "persistent_experiment_origin_mutation_present": False,
        "semantic_audit_status": "PENDING",
        "new_provider_calls": 0,
        "new_paid_evaluator_calls": 0,
        "r7_authorized": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
    }
    summary["summary_hash"] = stable_hash(summary)
    return records, case_summaries, summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--traces", required=True)
    ap.add_argument("--case-bindings", required=True)
    ap.add_argument("--evidence-batch", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    records, cases, summary = derive(
        traces_path=args.traces,
        case_bindings_path=args.case_bindings,
        evidence_batch_path=args.evidence_batch,
    )
    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r5r6_structural_observation")
    out.mkdir(parents=True)
    write_jsonl(out / "branch_structural_observations.jsonl", records)
    write_jsonl(out / "case_structural_summaries.jsonl", cases)
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("V5_CROSS_DOMAIN_R5R6_STRUCTURAL_OBSERVATION=COMPLETE")
    print("INTERVENTION_TRACE_COUNT=12")
    print("CASE_COUNT=6")
    print("NEW_PROVIDER_CALLS=0")
    print("SEMANTIC_AUDIT=PENDING")
    print("SUMMARY_HASH=" + summary["summary_hash"])


if __name__ == "__main__":
    main()
