#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl

SCHEMA = "RB-V5-CROSS-DOMAIN-SEMANTIC-TRIAGE-CASE-v0.1"
SUMMARY_SCHEMA = "RB-V5-CROSS-DOMAIN-SEMANTIC-TRIAGE-SUMMARY-v0.1"
TRAJECTORY_SCHEMA = "RB-V5-CROSS-DOMAIN-TRAJECTORY-TRIAGE-v0.1"
DEFAULT_CONTRACT = "configs/v5_cross_domain_semantic_triage_v0.1.json"


def _is_control_key(state_key: str, contract: dict) -> bool:
    key = str(state_key or "").lower()
    exact = {str(x).lower() for x in contract["control_state_keys"]}
    suffixes = tuple(str(x).lower() for x in contract["control_state_key_suffixes"])
    return key in exact or key.endswith(suffixes)


def _text_blob(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _source_payload(candidate: dict, trace: dict) -> dict:
    events = {
        e.get("event_index"): e
        for e in trace.get("events") or []
        if isinstance(e.get("event_index"), int)
    }
    event = events.get(candidate["source_event_index"])
    if event is None:
        raise ValueError(
            "triage_source_event_missing:"
            + trace.get("run_id", "UNKNOWN")
            + ":"
            + str(candidate["source_event_index"])
        )
    action = event.get("action") or {}
    action_type = event.get("action_type") or action.get("type")
    state_key = candidate.get("state_key")
    if action_type == "write_state":
        if action.get("key") != state_key:
            raise ValueError("triage_candidate_state_key_mismatch:" + candidate["candidate_ref"])
        basis = action.get("basis")
        value = action.get("value")
        revision_reason = None
    elif action_type == "revise_final_state":
        patch = action.get("patch") or {}
        if not isinstance(patch, dict) or state_key not in patch:
            raise ValueError("triage_candidate_revision_patch_missing:" + candidate["candidate_ref"])
        basis = action.get("reason")
        value = patch[state_key]
        revision_reason = action.get("reason")
    else:
        raise ValueError(
            "triage_candidate_source_not_supported_state_write:"
            + candidate["candidate_ref"]
            + ":"
            + str(action_type)
        )
    return {
        "event_index": candidate["source_event_index"],
        "turn": candidate["source_turn"],
        "actor": candidate["source_actor"],
        "state_key": candidate["state_key"],
        "status": candidate.get("source_status"),
        "mutation_type": action_type,
        "basis": basis,
        "revision_reason": revision_reason,
        "value": value,
    }


def _authority_review(candidate: dict, source: dict, contract: dict) -> tuple[int | None, list[str]]:
    text = (str(source.get("basis") or "") + " " + _text_blob(source.get("value"))).lower()
    markers = [
        marker
        for marker in contract["authority_review"]["explicit_uncertainty_markers"]
        if marker.lower() in text
    ]
    status = str(candidate.get("source_status") or "").lower()
    cfg = contract["authority_review"]
    if status == "fact" and markers:
        return int(cfg["fact_with_marker_priority"]), markers
    if status in {"provisional", "unconfirmed"}:
        return int(cfg["provisional_or_unconfirmed_priority"]), markers
    if status == "unspecified":
        return int(cfg["unspecified_priority"]), markers
    return None, markers


def _pick_cases(index_row: dict, trace: dict, contract: dict) -> tuple[list[dict], dict]:
    candidates = [
        row for row in index_row.get("candidates") or []
        if row.get("structural_repair_anchor_candidate") is True
    ]
    non_control = [
        row for row in candidates
        if not _is_control_key(row.get("state_key", ""), contract)
    ]
    pool = non_control or candidates

    role_picks: list[tuple[str, dict, list[str], str]] = []
    if pool:
        formation = min(
            pool,
            key=lambda c: (int(c["source_event_index"]), str(c.get("state_key") or "")),
        )
        role_picks.append(
            (
                "FORMATION_ANCHOR",
                formation,
                [],
                "earliest non-control structural repair-anchor candidate",
            )
        )

        propagation = max(
            pool,
            key=lambda c: (
                int(c.get("distinct_visible_actor_count") or 0),
                int(c.get("later_visibility_count") or 0),
                int(c.get("activity_after_visibility_count") or 0),
                -int(c.get("source_event_index") or 0),
            ),
        )
        role_picks.append(
            (
                "PROPAGATION_ANCHOR",
                propagation,
                [],
                "max cross-Agent structural observability under frozen tie-breaks",
            )
        )

        authority_rows = []
        for candidate in pool:
            source = _source_payload(candidate, trace)
            priority, markers = _authority_review(candidate, source, contract)
            if priority is not None:
                authority_rows.append(
                    (
                        priority,
                        int(candidate["source_event_index"]),
                        str(candidate.get("state_key") or ""),
                        candidate,
                        markers,
                    )
                )
        if authority_rows:
            _, _, _, authority, markers = min(authority_rows, key=lambda x: (x[0], x[1], x[2]))
            role_picks.append(
                (
                    "AUTHORITY_REVIEW_ANCHOR",
                    authority,
                    markers,
                    "earliest candidate selected by frozen status/lexical authority-review rule",
                )
            )

    merged: dict[str, dict] = {}
    for role, candidate, markers, reason in role_picks:
        ref = candidate["candidate_ref"]
        item = merged.setdefault(
            ref,
            {
                "candidate": candidate,
                "roles": [],
                "markers": set(),
                "reasons": [],
            },
        )
        item["roles"].append(role)
        item["markers"].update(markers)
        item["reasons"].append(reason)

    selected = []
    for ref in sorted(
        merged,
        key=lambda x: (
            int(merged[x]["candidate"]["source_event_index"]),
            str(merged[x]["candidate"].get("state_key") or ""),
        ),
    ):
        item = merged[ref]
        selected.append(
            {
                "candidate": item["candidate"],
                "roles": item["roles"],
                "markers": sorted(item["markers"]),
                "reasons": item["reasons"],
            }
        )

    trajectory = {
        "candidate_count": len(candidates),
        "non_control_candidate_count": len(non_control),
        "selected_unique_case_count": len(selected),
        "selection_roles_present": sorted({role for row in selected for role in row["roles"]}),
        "selected_candidate_refs": [row["candidate"]["candidate_ref"] for row in selected],
    }
    return selected, trajectory


def _sample_calls(rows: list[dict], limit: int) -> tuple[list[dict], bool]:
    if len(rows) <= limit:
        return rows, False
    first_n = limit // 2
    last_n = limit - first_n
    return rows[:first_n] + rows[-last_n:], True


def _packet(
    *,
    index_row: dict,
    trace: dict,
    evidence_batch: dict,
    selected: dict,
    contract: dict,
) -> dict:
    candidate = selected["candidate"]
    source = _source_payload(candidate, trace)

    visibility = [
        row for row in index_row.get("pool_visibility_ledger") or []
        if row.get("content_address") == candidate.get("content_address")
    ]
    visibility.sort(key=lambda r: (int(r.get("turn") or 0), str(r.get("actor") or "")))

    call_index = {
        (int(call.get("turn")), str(call.get("agent_id"))): call
        for call in trace.get("model_calls") or []
        if isinstance(call.get("turn"), int) and call.get("agent_id")
    }
    call_rows = []
    seen_calls = set()
    for row in visibility:
        key = (int(row.get("turn") or 0), str(row.get("actor") or ""))
        if key in seen_calls or key not in call_index:
            continue
        seen_calls.add(key)
        call = call_index[key]
        envelope = call.get("parsed_envelope") or {}
        action_types = [
            action.get("type")
            for action in envelope.get("actions") or []
            if isinstance(action, dict) and action.get("type")
        ]
        call_rows.append(
            {
                "turn": key[0],
                "actor": key[1],
                "event_index_start": call.get("event_index_start"),
                "event_index_end": call.get("event_index_end"),
                "decision_summary": call.get("decision_summary"),
                "parsed_action_types": action_types,
                "input_message_ids": call.get("input_message_ids") or [],
                "input_invocation_ids": call.get("input_invocation_ids") or [],
                "call_status": call.get("status"),
            }
        )
    call_rows.sort(key=lambda r: (r["turn"], r["actor"]))
    sampled_calls, truncated = _sample_calls(
        call_rows,
        int(contract["packet"]["max_downstream_call_summaries"]),
    )

    structural = {
        "later_visibility_count": candidate.get("later_visibility_count"),
        "distinct_visible_actor_count": candidate.get("distinct_visible_actor_count"),
        "visible_actors": candidate.get("visible_actors") or [],
        "first_later_visibility_turn": candidate.get("first_later_visibility_turn"),
        "activity_after_visibility_count": candidate.get("activity_after_visibility_count"),
        "source_status": candidate.get("source_status"),
        "candidate_hash": candidate.get("candidate_hash"),
        "semantic_lineage_recoverability_status": candidate.get(
            "semantic_lineage_recoverability_status"
        ),
    }

    packet = {
        "schema": SCHEMA,
        "first_round_id": index_row["first_round_id"],
        "source_run_id": index_row["trajectory_id"],
        "domain_id": index_row["domain_id"],
        "wave_id": int(index_row["wave_id"]),
        "source_evidence_batch_hash": evidence_batch["evidence_batch_hash"],
        "source_trace_hash": stable_hash(trace),
        "candidate_ref": candidate["candidate_ref"],
        "content_address": candidate["content_address"],
        "triage_roles": selected["roles"],
        "selection_reasons": selected["reasons"],
        "authority_review_markers": selected["markers"],
        "source": source,
        "structural_observability": structural,
        "downstream_visibility": visibility,
        "downstream_call_summaries": sampled_calls,
        "downstream_call_summary_truncated": truncated,
        "semantic_status": "NOT_ADJUDICATED",
        "qualification_status": "AWAITING_LOCALIZED_SEMANTIC_AUDIT",
        "r5_probe_authorized": False,
        "r7_repair_authorized": False,
        "claim_boundary": (
            "This packet is deterministic triage only. Structural visibility, lexical markers and "
            "source status do not establish semantic adoption, authority error, semantic inheritance, "
            "System Inertia, CPR, causality, R5 eligibility or R7 repairability."
        ),
    }
    packet["case_hash"] = stable_hash(packet)
    return packet


def _discover_wave_dirs(root: Path) -> list[Path]:
    dirs = []
    for index_path in sorted(root.rglob("v5_structural_index.jsonl")):
        wave_dir = index_path.parent.parent
        if not (wave_dir / "raw" / "traces.jsonl").exists():
            raise ValueError("triage_raw_trace_missing:" + str(wave_dir))
        if not (wave_dir / "evidence_batch.json").exists():
            raise ValueError("triage_evidence_batch_missing:" + str(wave_dir))
        dirs.append(wave_dir)
    if len(dirs) != 6:
        raise ValueError("triage_requires_exactly_six_wave_directories:" + str(len(dirs)))
    return dirs


def build_triage(*, input_root: str, contract_path: str = DEFAULT_CONTRACT) -> tuple[list[dict], list[dict], dict]:
    contract = load_json(contract_path)
    if contract.get("schema") != "RB-V5-CROSS-DOMAIN-SEMANTIC-TRIAGE-CONTRACT-v0.1":
        raise ValueError("triage_contract_schema_invalid")

    packets: list[dict] = []
    trajectories: list[dict] = []
    wave_ids = set()
    source_batch_hashes = set()

    for wave_dir in _discover_wave_dirs(Path(input_root)):
        evidence_batch = load_json(wave_dir / "evidence_batch.json")
        indexes = load_jsonl(wave_dir / "derived" / "v5_structural_index.jsonl")
        traces = {
            row["run_id"]: row
            for row in load_jsonl(wave_dir / "raw" / "traces.jsonl")
        }
        if len(indexes) != 15 or len(traces) != 15:
            raise ValueError("triage_wave_must_contain_15_frozen_trajectories:" + str(wave_dir))

        wave_ids.add(int(evidence_batch["selected_wave_id"]))
        source_batch_hashes.add(evidence_batch["evidence_batch_hash"])

        for index_row in indexes:
            run_id = index_row["trajectory_id"]
            if run_id not in traces:
                raise ValueError("triage_index_trace_binding_missing:" + run_id)
            trace = traces[run_id]
            selected, trajectory_core = _pick_cases(index_row, trace, contract)
            trajectory_row = {
                "schema": TRAJECTORY_SCHEMA,
                "first_round_id": index_row["first_round_id"],
                "source_run_id": run_id,
                "domain_id": index_row["domain_id"],
                "wave_id": int(index_row["wave_id"]),
                "source_evidence_batch_hash": evidence_batch["evidence_batch_hash"],
                **trajectory_core,
                "semantic_status": "NOT_ADJUDICATED",
                "r5_probe_authorized": False,
                "r7_repair_authorized": False,
            }
            trajectory_row["triage_hash"] = stable_hash(trajectory_row)
            trajectories.append(trajectory_row)
            packets.extend(
                _packet(
                    index_row=index_row,
                    trace=trace,
                    evidence_batch=evidence_batch,
                    selected=row,
                    contract=contract,
                )
                for row in selected
            )

    if wave_ids != set(range(1, 7)):
        raise ValueError("triage_wave_set_invalid")
    if len(source_batch_hashes) != 6:
        raise ValueError("triage_evidence_batch_hash_set_invalid")
    if len(trajectories) != 90:
        raise ValueError("triage_requires_90_frozen_trajectories")

    role_counts = Counter()
    domain_case_counts = Counter()
    domain_trajectory_counts = Counter()
    source_status_counts = Counter()
    authority_trajectory_counts = Counter()
    for row in trajectories:
        domain_trajectory_counts[row["domain_id"]] += 1
        if "AUTHORITY_REVIEW_ANCHOR" in row["selection_roles_present"]:
            authority_trajectory_counts[row["domain_id"]] += 1
    for packet in packets:
        domain_case_counts[packet["domain_id"]] += 1
        source_status_counts[str(packet["source"].get("status"))] += 1
        for role in packet["triage_roles"]:
            role_counts[role] += 1

    summary = {
        "schema": SUMMARY_SCHEMA,
        "status": "COMPLETE_DETERMINISTIC_TRIAGE_AWAITING_LOCALIZED_SEMANTIC_AUDIT",
        "trajectory_count": len(trajectories),
        "selected_unique_case_count": len(packets),
        "source_wave_count": 6,
        "source_evidence_batch_hashes": sorted(source_batch_hashes),
        "domain_trajectory_counts": dict(sorted(domain_trajectory_counts.items())),
        "domain_selected_case_counts": dict(sorted(domain_case_counts.items())),
        "role_assignment_counts": dict(sorted(role_counts.items())),
        "authority_review_trajectory_counts": dict(sorted(authority_trajectory_counts.items())),
        "source_status_counts": dict(sorted(source_status_counts.items())),
        "provider_calls": 0,
        "paid_evaluator_calls": 0,
        "r5_probe_calls": 0,
        "r7_repair_calls": 0,
        "r8_cpr_adjudication": False,
        "semantic_status": "NOT_ADJUDICATED",
        "claim_boundary": contract["claim_boundary"],
    }
    summary["summary_hash"] = stable_hash(summary)

    packets.sort(key=lambda r: (r["domain_id"], r["source_run_id"], r["source"]["event_index"]))
    trajectories.sort(key=lambda r: (r["domain_id"], r["source_run_id"]))
    return packets, trajectories, summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-root", required=True)
    ap.add_argument("--contract", default=DEFAULT_CONTRACT)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    packets, trajectories, summary = build_triage(
        input_root=args.input_root,
        contract_path=args.contract,
    )
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "semantic_triage_cases.jsonl", packets)
    write_jsonl(out / "trajectory_triage_summary.jsonl", trajectories)
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("V5_CROSS_DOMAIN_SEMANTIC_TRIAGE=COMPLETE")
    print("TRAJECTORY_COUNT=" + str(summary["trajectory_count"]))
    print("SELECTED_UNIQUE_CASE_COUNT=" + str(summary["selected_unique_case_count"]))
    print("ROLE_ASSIGNMENTS=" + json.dumps(summary["role_assignment_counts"], sort_keys=True))
    print(
        "AUTHORITY_REVIEW_TRAJECTORIES="
        + json.dumps(summary["authority_review_trajectory_counts"], sort_keys=True)
    )
    print("PROVIDER_CALLS=0")
    print("PAID_EVALUATOR_CALLS=0")
    print("R5_PROBE_CALLS=0")
    print("R7_REPAIR_CALLS=0")
    print("SEMANTIC_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
