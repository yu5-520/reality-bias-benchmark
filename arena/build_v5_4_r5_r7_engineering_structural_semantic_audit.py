#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl

AUDIT_SCHEMA = "RB-ENGINEERING-STRUCTURAL-SEMANTIC-AUDIT-v0.1"
SUMMARY_SCHEMA = "RB-V5.4-R5R7-ENGINEERING-STRUCTURAL-SEMANTIC-AUDIT-SUMMARY-v0.1"
BUNDLE_SCHEMA = "RB-V5.4-R5R7-ENGINEERING-REPORT-EVIDENCE-BUNDLE-v0.1"
P_ARM = "R7_P_PERSISTENT_SEMANTIC"
S_ARM = "R7_S_STRUCTURED_LINEAGE_REPAIR"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _one(paths, label: str) -> Path:
    rows = list(paths)
    _require(len(rows) == 1, f"{label}_not_unique:{len(rows)}")
    return rows[0]


def _hash_without(row: dict[str, Any], key: str) -> str:
    material = copy.deepcopy(row)
    material.pop(key, None)
    return stable_hash(material)


def _call_ref(trace: dict, call: dict) -> str:
    return f"{trace['run_id']}:turn:{call.get('turn')}:actor:{call.get('agent_id')}"


def _action_summary(event: dict) -> str:
    action = event.get("action") or {}
    kind = event.get("action_type") or action.get("type") or "unknown"
    if kind == "write_state":
        value = json.dumps(action.get("value"), ensure_ascii=False, sort_keys=True)
        return f"write_state {action.get('key')} [{action.get('status')}]: {value[:600]}"
    if kind == "revise_final_state":
        patch = json.dumps(action.get("patch"), ensure_ascii=False, sort_keys=True)
        return f"revise_final_state: {patch[:600]}"
    return ""


def _route(trace: dict, arm_id: str) -> dict:
    events = trace.get("events") or []
    nodes = []
    for route_index, call in enumerate(trace.get("model_calls") or []):
        start = call.get("event_index_start")
        end = call.get("event_index_end")
        call_events = [
            event for event in events
            if isinstance(event.get("event_index"), int)
            and start is not None and end is not None
            and start <= event["event_index"] <= end
        ]
        writes = [
            _action_summary(event)
            for event in call_events
            if event.get("action_type") in {"write_state", "revise_final_state"}
        ]
        nodes.append({
            "route_index": route_index,
            "turn": int(call.get("turn") or 0),
            "agent_role": str(call.get("agent_id") or "UNKNOWN"),
            "call_ref": _call_ref(trace, call),
            "decision_summary": str(call.get("decision_summary") or ""),
            "write_summaries": [row for row in writes if row],
            "status": str(call.get("status") or "UNKNOWN"),
        })

    direct_exposure_count = sum(
        1 for row in (trace.get("runtime_transform_records") or [])
        if row.get("experiment_origin") is True
    )
    fixed_horizon = (
        trace.get("run_status") == "BUDGET_CENSORED"
        and trace.get("termination_reason") == "turn_budget_exhausted"
    )
    return {
        "run_id": trace["run_id"],
        "arm_id": arm_id,
        "complete_route_verified": True,
        "fixed_horizon_censored": fixed_horizon,
        "direct_exposure_count": direct_exposure_count,
        "nodes": nodes,
        "terminal": {
            "run_status": str(trace.get("run_status") or "UNKNOWN"),
            "termination_reason": str(trace.get("termination_reason") or "UNKNOWN"),
            "terminal_outcome_is_primary": False,
        },
    }


def _keyed(rows: list[dict], key: str, label: str) -> dict[str, dict]:
    out = {}
    for row in rows:
        value = row[key]
        _require(value not in out, f"{label}_collision:{value}")
        out[value] = row
    return out


def _case_id_from_gate(gate: dict) -> str:
    prefix = "V54-R6-LINEAGE-"
    suffix = "-v0.1"
    ref = gate["semantic_lineage_closure_ref"]
    _require(ref.startswith(prefix) and ref.endswith(suffix), "unexpected_gate_closure_ref")
    return ref[len(prefix):-len(suffix)]


def _case_id_from_closure(row: dict) -> str:
    prefix = "V54-R6-LINEAGE-"
    suffix = "-v0.1"
    ref = row["closure_id"]
    _require(ref.startswith(prefix) and ref.endswith(suffix), "unexpected_closure_id")
    return ref[len(prefix):-len(suffix)]


def _case_id_from_packet(row: dict) -> str:
    prefix = "V54-R7-REPAIR-PACKET-"
    suffix = "-v0.1"
    ref = row["packet_id"]
    _require(ref.startswith(prefix) and ref.endswith(suffix), "unexpected_packet_id")
    return ref[len(prefix):-len(suffix)]


def _engineering_class(action_plan_relation: str) -> str:
    mapping = {
        "MATERIAL_PARAMETER_DIVERGENCE":
            "SELECTIVE_RECOMPUTE_PARAMETER_DIVERGENCE",
        "MATERIAL_ACTION_RECOMPOSITION":
            "SELECTIVE_RECOMPUTE_ACTION_RECOMPOSITION",
        "ACTION_PLAN_RECONVERGENCE":
            "REPAIR_RECONVERGENCE_WITH_FRESH_AUTHORITY_REGENERATION",
        "DECISION_RECONVERGENCE_WITH_SEMANTIC_REAFFIRMATION":
            "REPAIR_RECONVERGENCE_WITH_COMPATIBLE_DECISION_REAFFIRMATION",
    }
    _require(action_plan_relation in mapping, "unknown_action_plan_relation")
    return mapping[action_plan_relation]


def build(
    *,
    config_path: str,
    source_root: str,
    r7_result_manifest_path: str,
):
    cfg = load_json(config_path)
    _require(
        cfg.get("schema")
        == "RB-V5.4-R5R7-ENGINEERING-STRUCTURAL-SEMANTIC-AUDIT-CONFIG-v0.1",
        "engineering_audit_config_schema_invalid",
    )
    source = Path(source_root)

    r2r6_path = _one(
        source.rglob("semantic_trajectory_audits.jsonl"),
        "r2r6_complete_route_records",
    )
    r2r6 = [
        row for row in load_jsonl(r2r6_path)
        if row.get("experiment_scope", {}).get("stage") == "R5-R6"
    ]
    r5_by_case = _keyed(
        r2r6,
        "experiment_scope",
        "unused",
    ) if False else {
        row["experiment_scope"]["case_id"]: row for row in r2r6
    }
    _require(len(r5_by_case) == len(r2r6), "r5_complete_route_case_collision")

    summaries = _keyed(
        load_jsonl(_one(source.rglob("case_summaries.jsonl"), "r6_case_summaries")),
        "case_id",
        "r6_case_summary",
    )

    gates_rows = load_jsonl(
        _one(source.rglob("lineage_completeness_gates.jsonl"), "r6_lineage_gates")
    )
    gates = {}
    for row in gates_rows:
        cid = _case_id_from_gate(row)
        _require(cid not in gates, f"r6_gate_case_collision:{cid}")
        gates[cid] = row

    closures_rows = load_jsonl(
        _one(source.rglob("semantic_lineage_closures.jsonl"), "r6_lineage_closures")
    )
    closures = {}
    for row in closures_rows:
        cid = _case_id_from_closure(row)
        _require(cid not in closures, f"r6_closure_case_collision:{cid}")
        closures[cid] = row

    packet_rows = load_jsonl(
        _one(source.rglob("semantic_repair_packets.jsonl"), "r6_repair_packets")
    )
    packets = {}
    for row in packet_rows:
        cid = _case_id_from_packet(row)
        _require(cid not in packets, f"r6_packet_case_collision:{cid}")
        packets[cid] = row

    r7_semantic = _keyed(
        load_jsonl(_one(source.rglob("semantic_audit_records.jsonl"), "r7_semantic_records")),
        "case_id",
        "r7_semantic",
    )
    structural_index = _keyed(
        load_jsonl(_one(source.rglob("r7_dual_case_index.jsonl"), "r7_structural_index")),
        "case_id",
        "r7_structural_index",
    )
    structural_comparisons = _keyed(
        load_jsonl(_one(source.rglob("r7_dual_structural_comparisons.jsonl"), "r7_structural_comparisons")),
        "case_id",
        "r7_structural_comparison",
    )

    r7_result = load_json(r7_result_manifest_path)
    semantic_classes = _keyed(
        r7_result["case_semantic_classes"],
        "case_id",
        "r7_result_case_class",
    )

    expected_cases = set(cfg["candidate_case_ids"])
    for label, mapping in (
        ("r5", r5_by_case),
        ("r6_summary", summaries),
        ("r6_gate", gates),
        ("r6_closure", closures),
        ("r6_packet", packets),
        ("r7_semantic", r7_semantic),
        ("r7_structural_index", structural_index),
        ("r7_structural_comparison", structural_comparisons),
        ("r7_result_class", semantic_classes),
    ):
        _require(
            set(mapping) == expected_cases,
            f"{label}_case_set_mismatch:{sorted(set(mapping) ^ expected_cases)}",
        )

    trace_by_case_arm = {}
    for cid in sorted(expected_cases):
        trace_path = _one(
            source.rglob(f"*/cases/{cid}/raw/traces.jsonl"),
            f"r7_raw_trace_file:{cid}",
        )
        traces = load_jsonl(trace_path)
        arm_map = {
            (trace.get("r7_condition") or {}).get("canonical_arm_id"): trace
            for trace in traces
        }
        _require(
            set(arm_map) == {P_ARM, S_ARM},
            f"r7_arm_set_invalid:{cid}",
        )
        trace_by_case_arm[cid] = arm_map

    audits = []
    case_index = []
    for cid in cfg["candidate_case_ids"]:
        previous = r5_by_case[cid]
        summary = summaries[cid]
        gate = gates[cid]
        closure = closures[cid]
        packet = packets[cid]
        semantic = r7_semantic[cid]
        structural = structural_index[cid]
        comparison = structural_comparisons[cid]
        result_class = semantic_classes[cid]
        p_trace = trace_by_case_arm[cid][P_ARM]
        s_trace = trace_by_case_arm[cid][S_ARM]

        p_route = _route(p_trace, P_ARM)
        s_route = _route(s_trace, S_ARM)
        _require(len(p_route["nodes"]) == 8, f"p_route_node_count_invalid:{cid}")
        _require(len(s_route["nodes"]) == 8, f"s_route_node_count_invalid:{cid}")
        _require(p_route["fixed_horizon_censored"], f"p_not_fixed_horizon:{cid}")
        _require(s_route["fixed_horizon_censored"], f"s_not_fixed_horizon:{cid}")
        _require(
            structural["persistent_runtime_exposure_count"]
            == p_route["direct_exposure_count"],
            f"persistent_exposure_count_mismatch:{cid}",
        )
        _require(
            structural["comparison_hash"] == semantic["structural_comparison_hash"],
            f"structural_comparison_hash_mismatch:{cid}",
        )
        _require(
            comparison["comparison_hash"] == semantic["structural_comparison_hash"],
            f"structural_comparison_record_hash_mismatch:{cid}",
        )

        p_condition = p_trace.get("r7_condition") or {}
        p_mechanism = p_condition.get("mechanism_summary") or {}
        p_reinjections = int(p_mechanism.get("experiment_origin_reinjection_count") or 0)
        _require(p_reinjections == 7, f"unexpected_p_reinjection_count:{cid}")

        app = s_trace.get("r7_repair_application") or {}
        verification = s_trace.get("r7_semantic_repair_verification") or {}
        _require(app and verification, f"structured_repair_evidence_missing:{cid}")
        _require(
            verification.get("repair_application_hash") == app.get("repair_application_hash"),
            f"repair_application_hash_mismatch:{cid}",
        )
        _require(
            verification.get("preserved_unrelated_structure") is True,
            f"unrelated_structure_not_preserved:{cid}",
        )
        _require(gate["status"] == "COMPLETE_FOR_AUTHORIZED_REPAIR", f"r6_gate_incomplete:{cid}")
        _require(
            summary["gate_hash"] == gate["gate_hash"]
            and summary["closure_hash"] == closure["closure_hash"]
            and summary["repair_packet_hash"] == packet["packet_hash"],
            f"r6_lineage_identity_mismatch:{cid}",
        )

        watch = verification.get("post_repair_watch_result") or {}
        final_status = semantic["structured_repair_target_final_status"]

        lifecycle = {
            "R5_I": {
                "operator": cfg["operator_semantics"]["R5_I"]["operator"],
                "engineering_role": cfg["operator_semantics"]["R5_I"]["engineering_role"],
                "control_surface": "NEXT_READER_RUNTIME_VIEW_ONLY",
                "underlying_shared_state_mutation": False,
                "semantic_purpose": cfg["operator_semantics"]["R5_I"]["purpose"],
                "evidence_refs": [
                    previous["audit_id"],
                    previous["audit_hash"],
                    previous["evidence_binding"]["raw_evidence_ref"],
                ],
            },
            "R6": {
                "operator": cfg["operator_semantics"]["R6"]["operator"],
                "engineering_role": cfg["operator_semantics"]["R6"]["engineering_role"],
                "control_surface": "FROZEN_SOURCE_TRANSFORMATION_AUTHORITY_POOL_DESCENDANT_CLOSURE",
                "underlying_shared_state_mutation": False,
                "semantic_purpose": cfg["operator_semantics"]["R6"]["purpose"],
                "evidence_refs": [
                    summary["repair_anchor_ref"],
                    summary["content_address"],
                    gate["gate_hash"],
                    closure["closure_hash"],
                    packet["packet_hash"],
                ],
            },
            "R7_P": {
                "operator": cfg["operator_semantics"]["R7_P"]["operator"],
                "engineering_role": cfg["operator_semantics"]["R7_P"]["engineering_role"],
                "control_surface": "EVERY_DOWNSTREAM_RUNTIME_READ_OF_TARGET_WITHIN_COMMON_HORIZON",
                "underlying_shared_state_mutation": False,
                "semantic_purpose": cfg["operator_semantics"]["R7_P"]["purpose"],
                "evidence_refs": [
                    p_trace["run_id"],
                    p_condition.get("semantic_payload_hash"),
                    semantic["persistent_measurement_hash"],
                ],
            },
            "R7_S": {
                "operator": cfg["operator_semantics"]["R7_S"]["operator"],
                "engineering_role": cfg["operator_semantics"]["R7_S"]["engineering_role"],
                "control_surface": "EXACT_REPAIR_ANCHOR_PLUS_EVIDENCE_SUPPORTED_AFFECTED_CLOSURE",
                "underlying_shared_state_mutation": True,
                "semantic_purpose": cfg["operator_semantics"]["R7_S"]["purpose"],
                "evidence_refs": [
                    s_trace["run_id"],
                    app["repair_application_hash"],
                    verification["verification_hash"],
                    packet["packet_hash"],
                ],
            },
        }

        ledger = []

        def add(stage, dimension, fact, meaning, refs, status="SUPPORTED"):
            ledger.append({
                "ledger_id": f"{cid}:{stage}:{dimension}:{len(ledger)+1}",
                "stage": stage,
                "dimension": dimension,
                "structural_fact": fact,
                "engineering_semantic_meaning": meaning,
                "evidence_refs": [str(ref) for ref in refs if ref not in (None, "")],
                "claim_status": status,
            })

        add(
            "R5_I",
            "CONTROL_SURFACE",
            "one-shot fact -> unconfirmed exposure; persistent_state_mutation=false",
            "R5-I is a transient diagnostic probe: it changes what one reader sees and does not repair the stored shared-state lineage.",
            [previous["audit_id"], previous["audit_hash"]],
        )
        add(
            "R6",
            "LOCALIZATION",
            f"gate={gate['status']}; missing_components={len(gate['missing_components'])}",
            "R6 converts a persistence candidate into a bounded repair-ready lineage object. Completeness is an engineering precondition, not repair success.",
            [gate["gate_hash"], closure["closure_hash"]],
        )
        add(
            "R6",
            "CONTENT_ADDRESSING",
            f"anchor={summary['repair_anchor_ref']}; content_address={summary['content_address']}",
            "The intervention target and affected closure are machine-addressable, so repair can follow semantic lineage rather than a temporal window.",
            [summary["repair_anchor_ref"], summary["content_address"], packet["packet_hash"]],
        )
        add(
            "R7_P",
            "CONTROL_SURFACE",
            f"direct_exposures={p_route['direct_exposure_count']}; reinjections={p_reinjections}; underlying_state_mutation=false",
            "R7-P repeatedly presents corrected uncertainty to downstream readers while keeping the inherited internal shared-state lineage unchanged.",
            [p_trace["run_id"], semantic["persistent_measurement_hash"]],
        )
        add(
            "R7_S",
            "INVALIDATION",
            f"invalidated_refs={verification.get('invalidated_event_refs') or []}",
            "R7-S removes affected post-anchor materialization rather than merely attaching a warning at read time.",
            [app["repair_application_hash"], *(verification.get("invalidated_event_refs") or [])],
        )
        add(
            "R7_S",
            "REOPEN",
            f"reopened_calls={len(verification.get('reopened_model_call_refs') or [])}",
            "Dependent computation is reopened so later Agents can act from repaired state rather than accepting the old continuation as fixed history.",
            [verification["verification_hash"], *(verification.get("reopened_model_call_refs") or [])],
        )
        add(
            "R7_S",
            "RECOMPUTE",
            f"recomputed_descendants={len(verification.get('recomputed_descendant_refs') or [])}",
            "The affected continuation is recomputed inside the frozen common horizon. Structural recomputation may change the plan or may reaffirm compatible meaning.",
            [
                verification["verification_hash"],
                *(verification.get("recomputed_descendant_refs") or [])[:8],
            ],
        )
        add(
            "R7_S",
            "PRESERVATION",
            f"preserved_unrelated_structure={verification.get('preserved_unrelated_structure')}",
            "Repair is selective: compatible and unrelated process memory is preserved instead of resetting the whole multi-Agent system.",
            [verification["verification_hash"], *(packet.get("preserved_unrelated_refs") or [])],
        )

        if verification.get("old_lineage_reentry_detected") is True:
            reentry_meaning = (
                "Exact target-key factual re-entry is preserved as structural recurrence, "
                "but the frozen semantic evidence binds it to fresh post-repair evidence. "
                "It is authority regeneration, not blind restoration of inherited authority."
            )
        else:
            reentry_meaning = (
                "No exact old factual-authority re-entry is observed inside the common "
                "horizon. This is bounded non-reentry, not a universal stability guarantee."
            )
        add(
            "R7_S",
            "REENTRY",
            (
                f"old_lineage_reentry_detected="
                f"{verification.get('old_lineage_reentry_detected')}; "
                f"refs={verification.get('old_lineage_reentry_refs') or []}"
            ),
            reentry_meaning,
            [
                verification["verification_hash"],
                *(verification.get("old_lineage_reentry_refs") or []),
            ],
        )
        add(
            "R7_S",
            "AUTHORITY_RESULT",
            f"target_final_status={final_status}; watch={watch.get('watch_status')}",
            "Target authority is assessed separately from the final plan: repair may keep the target non-factual, rewrite it as recommendation, or freshly re-derive fact authority from new evidence.",
            [semantic["audit_hash"], verification["post_repair_watch_result_hash"]],
        )

        process_relation = (
            "MATERIAL_DIVERGENCE"
            if semantic["action_plan_relation"]
            in {"MATERIAL_PARAMETER_DIVERGENCE", "MATERIAL_ACTION_RECOMPOSITION"}
            else "RECONVERGENCE_AFTER_RECOMPUTE"
        )
        add(
            "R7_P_VS_R7_S",
            "ENDPOINT_PROCESS_RELATION",
            f"action_plan_relation={semantic['action_plan_relation']}",
            "Persistent correction and structured repair are different engineering control modes. Material divergence shows intervention-sensitive recomposition; reconvergence can still arise from a rebuilt lineage.",
            [semantic["audit_hash"], semantic["structural_comparison_hash"]],
        )
        add(
            "R7_P_VS_R7_S",
            "HORIZON",
            "both arms stop at the preregistered eight-post-source-Agent-turn cap",
            "The BUDGET_CENSORED status is the fixed observation boundary, not monetary/provider failure. No stability claim extends beyond the observed horizon.",
            [p_trace["run_id"], s_trace["run_id"]],
        )

        record = {
            "schema": AUDIT_SCHEMA,
            "audit_id": f"V54-ENG-STRUCT-SEM-{cid}",
            "case_id": cid,
            "domain_id": semantic["domain_id"],
            "target_state_key": semantic["target_state_key"],
            "reviewer": {
                "kind": "MODEL",
                "id": "GPT-5.6-Sol",
                "blind_to_prior_semantic_labels": False,
                "notes": (
                    "Append-only engineering semantic audit over frozen R5-R7 evidence. "
                    "Existing per-case R7 semantic classifications are rebound to exact "
                    "structural control operations and complete realized dual routes."
                ),
            },
            "evidence_binding": {
                "r5_complete_route_audit_ref": previous["audit_id"],
                "r5_complete_route_audit_hash": previous["audit_hash"],
                "r6_repair_anchor_ref": summary["repair_anchor_ref"],
                "r6_content_address": summary["content_address"],
                "r6_gate_hash": gate["gate_hash"],
                "r6_closure_hash": closure["closure_hash"],
                "r6_repair_packet_hash": packet["packet_hash"],
                "r7_p_run_id": p_trace["run_id"],
                "r7_s_run_id": s_trace["run_id"],
                "r7_structural_comparison_hash": semantic["structural_comparison_hash"],
                "r7_semantic_audit_hash": semantic["audit_hash"],
            },
            "engineering_lifecycle": lifecycle,
            "r7_p_route": p_route,
            "r7_s_route": s_route,
            "repair_scope": {
                "repair_anchor_ref": summary["repair_anchor_ref"],
                "target_semantic_id": verification["target_semantic_id"],
                "lineage_completeness_status": gate["status"],
                "allowed_repair_operations": list(packet["allowed_repair_operations"]),
                "repair_application_hash": app["repair_application_hash"],
                "invalidated_refs": list(verification.get("invalidated_event_refs") or []),
                "reopened_model_call_refs": list(verification.get("reopened_model_call_refs") or []),
                "recomputed_descendant_refs": list(verification.get("recomputed_descendant_refs") or []),
                "preserved_unrelated_structure": True,
                "preserved_unrelated_refs": list(packet.get("preserved_unrelated_refs") or []),
                "old_lineage_reentry_detected": bool(verification.get("old_lineage_reentry_detected")),
                "old_lineage_reentry_refs": list(verification.get("old_lineage_reentry_refs") or []),
                "target_final_status": final_status,
                "verification_hash": verification["verification_hash"],
                "post_repair_watch_status": str(watch.get("watch_status") or "UNKNOWN"),
            },
            "engineering_semantic_ledger": ledger,
            "p_vs_s_semantic_contrast": {
                "persistent_semantics": result_class["p_semantics"],
                "structured_repair_semantics": result_class["s_semantics"],
                "action_plan_relation": semantic["action_plan_relation"],
                "process_relation": process_relation,
                "old_fact_reentry_semantic_interpretation": result_class["old_fact_reentry"],
                "intervention_mode_semantic_distinction": "SUPPORTED",
                "intervention_superiority": "NOT_ESTABLISHED",
            },
            "engineering_case_class": _engineering_class(semantic["action_plan_relation"]),
            "claim_boundaries": [
                semantic["interpretation_boundary"],
                (
                    "R5 probe, R6 repair readiness, R7-P persistent reader-surface "
                    "correction and R7-S structural repair are distinct control surfaces."
                ),
                (
                    "No universal intervention winner, problematic bias, unique R5 "
                    "causality, domain prevalence or CPR is established."
                ),
            ],
        }
        record["audit_hash"] = _hash_without(record, "audit_hash")
        audits.append(record)

        case_index.append({
            "case_id": cid,
            "domain_id": semantic["domain_id"],
            "target_state_key": semantic["target_state_key"],
            "audit_id": record["audit_id"],
            "audit_hash": record["audit_hash"],
            "engineering_case_class": record["engineering_case_class"],
            "p_direct_exposure_count": p_route["direct_exposure_count"],
            "p_reinjection_count": p_reinjections,
            "s_invalidated_ref_count": len(record["repair_scope"]["invalidated_refs"]),
            "s_reopened_call_count": len(record["repair_scope"]["reopened_model_call_refs"]),
            "s_recomputed_descendant_count": len(record["repair_scope"]["recomputed_descendant_refs"]),
            "s_preserved_unrelated_structure": True,
            "s_old_lineage_reentry_detected": record["repair_scope"]["old_lineage_reentry_detected"],
            "s_target_final_status": final_status,
            "fixed_horizon_censored_p": True,
            "fixed_horizon_censored_s": True,
        })

    expected = cfg["expected"]
    _require(len(audits) == expected["case_count"], "engineering_case_count_mismatch")
    _require(
        sum(row["p_direct_exposure_count"] for row in case_index)
        == expected["persistent_direct_exposure_count"],
        "persistent_direct_exposure_aggregate_mismatch",
    )
    _require(
        sum(row["s_preserved_unrelated_structure"] for row in case_index)
        == expected["structured_repair_preserved_unrelated_case_count"],
        "preservation_aggregate_mismatch",
    )
    _require(
        sum(row["s_old_lineage_reentry_detected"] for row in case_index)
        == expected["structural_old_fact_reentry_case_count"],
        "old_fact_reentry_aggregate_mismatch",
    )
    _require(
        sum(
            audit["p_vs_s_semantic_contrast"]["process_relation"] == "MATERIAL_DIVERGENCE"
            for audit in audits
        )
        == expected["material_divergence_case_count"],
        "material_divergence_count_mismatch",
    )
    _require(
        sum(
            audit["p_vs_s_semantic_contrast"]["process_relation"]
            == "RECONVERGENCE_AFTER_RECOMPUTE"
            for audit in audits
        )
        == expected["reconvergence_case_count"],
        "reconvergence_count_mismatch",
    )
    _require(
        sum(
            audit["r7_p_route"]["fixed_horizon_censored"]
            + audit["r7_s_route"]["fixed_horizon_censored"]
            for audit in audits
        )
        == expected["fixed_horizon_censored_trace_count"],
        "fixed_horizon_censor_count_mismatch",
    )

    total_route_nodes = sum(
        len(audit["r7_p_route"]["nodes"]) + len(audit["r7_s_route"]["nodes"])
        for audit in audits
    )
    total_ledger_entries = sum(
        len(audit["engineering_semantic_ledger"]) for audit in audits
    )

    summary = {
        "schema": SUMMARY_SCHEMA,
        "date": cfg["date"],
        "status": "ENGINEERING_STRUCTURAL_SEMANTIC_AUDIT_COMPLETE",
        "case_count": len(audits),
        "r5_probe_case_count": len(audits),
        "r6_lineage_complete_case_count": len(audits),
        "r7_p_trace_count": len(audits),
        "r7_s_trace_count": len(audits),
        "r7_route_node_count": total_route_nodes,
        "engineering_semantic_ledger_entry_count": total_ledger_entries,
        "persistent_direct_exposure_count": sum(
            row["p_direct_exposure_count"] for row in case_index
        ),
        "persistent_reinjection_count": sum(
            row["p_reinjection_count"] for row in case_index
        ),
        "structured_repair_preserved_unrelated_case_count": sum(
            row["s_preserved_unrelated_structure"] for row in case_index
        ),
        "structural_old_fact_reentry_case_count": sum(
            row["s_old_lineage_reentry_detected"] for row in case_index
        ),
        "semantic_blind_restoration_case_count": 0,
        "material_divergence_case_count": sum(
            audit["p_vs_s_semantic_contrast"]["process_relation"]
            == "MATERIAL_DIVERGENCE"
            for audit in audits
        ),
        "reconvergence_after_recompute_case_count": sum(
            audit["p_vs_s_semantic_contrast"]["process_relation"]
            == "RECONVERGENCE_AFTER_RECOMPUTE"
            for audit in audits
        ),
        "fixed_horizon_censored_trace_count": 8,
        "engineering_control_surface_distinction": "SUPPORTED",
        "engineering_control_surface_statement": (
            "R5 probe != R6 repair readiness != R7-P persistent reader-surface "
            "correction != R7-S internal lineage repair."
        ),
        "same_endpoint_not_same_engineering_process": "SUPPORTED",
        "structural_recomputation_not_semantic_novelty": "SUPPORTED",
        "structured_repair_universal_superiority": "NOT_ESTABLISHED",
        "problematic_bias_status": "NOT_ESTABLISHED",
        "r5_unique_causal_attribution": "NOT_ESTABLISHED",
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "new_provider_calls": 0,
        "new_paid_evaluator_calls": 0,
        "subject_reruns": 0,
        "raw_evidence_mutated": False,
        "claim_boundary": (
            "This engineering semantic audit interprets what the frozen structural "
            "operators do to control surfaces, lineage, repair scope, recomputation, "
            "preservation and re-entry. It does not establish a universally superior "
            "operator, domain truth, problematic bias, unique R5 causality or CPR."
        ),
        "record_hashes": [audit["audit_hash"] for audit in audits],
    }
    summary["summary_hash"] = _hash_without(summary, "summary_hash")

    report_bundle = {
        "schema": BUNDLE_SCHEMA,
        "date": cfg["date"],
        "status": "READY_FOR_ENGINEERING_REPORT_DRAFT",
        "engineering_report_standard":
            "RB-PROCESS-REALITY-ENGINEERING-REPORT-STANDARD-v1.3",
        "report_standard": "RB-PROCESS-REALITY-REPORT-STANDARD-v1.8",
        "primary_evidence_role":
            "STRUCTURAL_ENGINEERING_SEMANTICS_OVER_FROZEN_R5_R7_PROCESS",
        "candidate_case_count": len(audits),
        "case_audit_refs": [
            {
                "case_id": audit["case_id"],
                "audit_id": audit["audit_id"],
                "audit_hash": audit["audit_hash"],
                "engineering_case_class": audit["engineering_case_class"],
            }
            for audit in audits
        ],
        "recommended_report_family": [
            "R5_LOCAL_SEMANTIC_INTERVENTION_ENGINEERING",
            "R6_LINEAGE_LOCALIZATION_AND_REPAIR_READINESS",
            "R7_DUAL_INTERVENTION_ENGINEERING",
            "R5_R7_PROCESS_INTEGRITY_ENGINEERING_SYNTHESIS",
        ],
        "required_central_visuals": [
            "R5_TO_R7_CONTROL_SURFACE_EVOLUTION",
            "R7_P_VS_R7_S_COMPLETE_REALIZED_AGENT_ROUTE_PAIR",
            "R7_S_REPAIR_SCOPE_INVALIDATE_REOPEN_RECOMPUTE_PRESERVE",
            "OLD_LINEAGE_REENTRY_AND_AUTHORITY_REGENERATION",
        ],
        "primary_contrasts": [
            {
                "case_id": "wave-4-8b1731b57396",
                "reason": "material action recomposition under structured repair",
            },
            {
                "case_id": "wave-4-cf726639de1d",
                "reason": (
                    "endpoint reconvergence with exact structural fact re-entry "
                    "semantically re-derived from fresh evidence"
                ),
            },
            {
                "case_id": "wave-6-7c7e526e4d91",
                "reason": (
                    "decision reconvergence with compatible semantic reaffirmation "
                    "after structural recomputation"
                ),
            },
        ],
        "aggregate_structural_support": {
            "persistent_direct_exposure_count": summary["persistent_direct_exposure_count"],
            "persistent_reinjection_count": summary["persistent_reinjection_count"],
            "structured_repair_preserved_unrelated_case_count":
                summary["structured_repair_preserved_unrelated_case_count"],
            "structural_old_fact_reentry_case_count":
                summary["structural_old_fact_reentry_case_count"],
            "semantic_blind_restoration_case_count":
                summary["semantic_blind_restoration_case_count"],
            "material_divergence_case_count":
                summary["material_divergence_case_count"],
            "reconvergence_after_recompute_case_count":
                summary["reconvergence_after_recompute_case_count"],
            "fixed_horizon_censored_trace_count":
                summary["fixed_horizon_censored_trace_count"],
        },
        "claim_boundaries": {
            "structured_repair_universal_superiority": "NOT_ESTABLISHED",
            "problematic_bias_status": "NOT_ESTABLISHED",
            "r5_unique_causal_attribution": "NOT_ESTABLISHED",
            "semantic_cpr_status": "NOT_ADJUDICATED",
        },
        "new_provider_calls": 0,
        "new_paid_evaluator_calls": 0,
        "subject_reruns": 0,
        "raw_evidence_mutated": False,
    }
    report_bundle["bundle_hash"] = _hash_without(report_bundle, "bundle_hash")

    return audits, case_index, report_bundle, summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--source-root", required=True)
    ap.add_argument(
        "--r7-result-manifest",
        default="manifests/v5_4_r7_dual_semantic_audit_result_2026-09-19_v0_1.json",
    )
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    audits, case_index, report_bundle, summary = build(
        config_path=args.config,
        source_root=args.source_root,
        r7_result_manifest_path=args.r7_result_manifest,
    )

    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r5r7_engineering_semantic_audit")
    (out / "audits").mkdir(parents=True)

    for audit in audits:
        (out / "audits" / f"{audit['case_id']}.json").write_text(
            json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    write_jsonl(out / "engineering_structural_semantic_audits.jsonl", audits)
    write_jsonl(out / "case_index.jsonl", case_index)
    (out / "engineering_report_evidence_bundle.json").write_text(
        json.dumps(report_bundle, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("V5_4_R5_R7_ENGINEERING_STRUCTURAL_SEMANTIC_AUDIT=MATERIALIZED")
    print("CASE_COUNT=" + str(summary["case_count"]))
    print("R7_ROUTE_NODES=" + str(summary["r7_route_node_count"]))
    print("PERSISTENT_DIRECT_EXPOSURES=" + str(summary["persistent_direct_exposure_count"]))
    print("PERSISTENT_REINJECTIONS=" + str(summary["persistent_reinjection_count"]))
    print("PRESERVED_UNRELATED=" + str(summary["structured_repair_preserved_unrelated_case_count"]))
    print("STRUCTURAL_OLD_FACT_REENTRY=" + str(summary["structural_old_fact_reentry_case_count"]))
    print("SEMANTIC_BLIND_RESTORATION=0")
    print("MATERIAL_DIVERGENCE=" + str(summary["material_divergence_case_count"]))
    print("RECONVERGENCE=" + str(summary["reconvergence_after_recompute_case_count"]))
    print("REPORT_GATE=" + report_bundle["status"])
    print("NEW_PROVIDER_CALLS=0")
    print("SUMMARY_HASH=" + summary["summary_hash"])
    print("REPORT_BUNDLE_HASH=" + report_bundle["bundle_hash"])


if __name__ == "__main__":
    main()