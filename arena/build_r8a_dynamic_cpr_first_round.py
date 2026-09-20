#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


def stable_hash(obj):
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def read_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def write_jsonl(path, rows):
    Path(path).write_text(
        "".join(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for x in rows),
        encoding="utf-8",
    )


def file_sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def invoke_count(actions):
    return sum(1 for x in (actions or []) if isinstance(x, str) and x.startswith("invoke_agent "))


def c_node_surface(fn, relevance):
    if fn == "INDEPENDENT_EVIDENCE_REANCHOR":
        return "HEALTHY_INDEPENDENT_EVIDENCE_COMPARATOR"
    if relevance == "TARGET_LINEAGE" or fn in {
        "SOURCE_OBSERVATION", "NEW_DESCENDANT_CARRIER", "TRANSFORMATION",
        "READ_OR_ADOPTION", "ACTION_APPLICATION", "REAFFIRMATION",
    }:
        return "INFORMATION_PERMISSION_REVIEW_SURFACE"
    return "NO_TARGET_INFORMATION_PERMISSION_SURFACE"


def c_edge_surface(prop):
    if prop == "INDEPENDENT_REANCHOR":
        return "HEALTHY_INDEPENDENT_EVIDENCE_COMPARATOR"
    return "INFORMATION_PERMISSION_REVIEW_SURFACE"


def build(*, r2r6_path, lineage_path, r7_structural_path, r7_semantic_path, outdir):
    audits = read_jsonl(r2r6_path)
    lineages = {}
    for x in read_jsonl(lineage_path):
        m = re.search(r"wave-\d+-[0-9a-f]+", x["closure_id"])
        if m:
            lineages[m.group(0)] = x
    r7s = {x["case_id"]: x for x in read_jsonl(r7_semantic_path)}
    r7struct = {x["case_id"]: x for x in read_jsonl(r7_structural_path)}

    case_index, ledger, packets = [], [], []

    for a in audits:
        scope = a["experiment_scope"]
        route = a["actual_agent_route"]
        judgement = a["case_judgement"]
        cid = scope["case_id"]
        route_by_idx = {x["route_index"]: x for x in route["nodes"]}
        postset = set(judgement.get("post_stimulus_persistence_node_refs") or [])

        seen = Counter()
        role_meta = {}
        all_roles = []
        for node in route["nodes"]:
            role = node.get("agent_role")
            all_roles.append(role)
            role_meta[node["route_index"]] = {
                "role_occurrence_index": seen[role] + 1,
                "is_role_reentry": seen[role] > 0,
            }
            seen[role] += 1

        ci = {
            "schema": "RB-R8A-DYNAMIC-CPR-CASE-INDEX-v0.1",
            "audit_id": a["audit_id"],
            "case_id": cid,
            "stage": scope["stage"],
            "domain_id": scope["domain_id"],
            "evidence_role": scope["evidence_role"],
            "audit_hash": a["audit_hash"],
            "raw_evidence_ref": a["evidence_binding"].get("raw_evidence_ref"),
            "raw_evidence_hash": a["evidence_binding"].get("raw_evidence_hash"),
            "route_node_count": route["route_node_count"],
            "semantic_edge_count": len(a["semantic_edges"]),
            "semantic_structure_class": judgement.get("semantic_structure_class"),
            "system_inertia_status": judgement.get("system_inertia_status"),
            "problematic_bias_status": judgement.get("problematic_bias_status"),
            "historical_semantic_cpr_status": judgement.get("semantic_cpr_status"),
            "r8a_status": "SEMANTIC_EVENT_RECONSTRUCTED_NOT_ADJUDICATED",
        }
        ci["case_index_hash"] = stable_hash(ci)
        case_index.append(ci)

        boundary = {
            "schema": "RB-R8A-SEMANTIC-EVENT-LEDGER-v0.1",
            "ledger_event_id": a["audit_id"] + ":case-boundary",
            "audit_id": a["audit_id"], "case_id": cid, "stage": scope["stage"],
            "domain_id": scope["domain_id"], "event_kind": "CASE_BOUNDARY",
            "route_index": None, "agent_role": None, "lineage_relevance": "CASE_LEVEL",
            "semantic_function": "CASE_CONTEXT", "input_semantics": [], "output_semantics": [],
            "semantic_delta": None, "evidence_refs": [a["audit_hash"]],
            "independent_evidence_refs": [], "authority_or_status": [],
            "message_or_invoke_refs": [], "output_state_refs": [],
            "permission_review_surfaces": {
                "C_information": "CASE_LEVEL_CONTEXT",
                "P_collaboration_execution": "CASE_LEVEL_CONTEXT",
                "R_temporal": "CASE_LEVEL_CONTEXT",
            },
            "semantic_cpr_status": "NOT_ADJUDICATED",
        }
        boundary["ledger_hash"] = stable_hash(boundary)
        ledger.append(boundary)

        if judgement.get("challenged_source_or_target_ref"):
            challenge = {
                "schema": "RB-R8A-SEMANTIC-EVENT-LEDGER-v0.1",
                "ledger_event_id": a["audit_id"] + ":authority-challenge",
                "audit_id": a["audit_id"], "case_id": cid, "stage": scope["stage"],
                "domain_id": scope["domain_id"], "event_kind": "BOUNDED_AUTHORITY_CHALLENGE",
                "route_index": None, "agent_role": None, "lineage_relevance": "TARGET_LINEAGE",
                "semantic_function": "R5_ONE_SHOT_AUTHORITY_CHALLENGE",
                "input_semantics": [str(judgement.get("challenged_source_or_target_ref"))],
                "output_semantics": [str(judgement.get("direct_stimulus_end_ref"))],
                "semantic_delta": "One-shot authority challenge is an observational cut and not a CPR verdict.",
                "evidence_refs": [
                    judgement.get("challenged_source_or_target_ref"),
                    judgement.get("direct_stimulus_end_ref"),
                ],
                "independent_evidence_refs": [],
                "authority_or_status": ["fact->unconfirmed one-shot exposure"],
                "message_or_invoke_refs": [], "output_state_refs": [],
                "permission_review_surfaces": {
                    "C_information": "CHALLENGED_INFORMATION_PERMISSION_SURFACE",
                    "P_collaboration_execution": "POST_CHALLENGE_PROCESS_REVIEW_SURFACE",
                    "R_temporal": "TEMPORAL_BOUNDARY_REVIEW_SURFACE_NOT_R_POSITIVE",
                },
                "semantic_cpr_status": "NOT_ADJUDICATED",
            }
            challenge["evidence_refs"] = [x for x in challenge["evidence_refs"] if x]
            challenge["ledger_hash"] = stable_hash(challenge)
            ledger.append(challenge)

        for sn in a["semantic_nodes"]:
            idx = sn["route_index"]
            rn = route_by_idx.get(idx, {})
            inv = invoke_count(rn.get("output_actions"))
            rm = role_meta.get(idx, {})
            p_surface = (
                "COLLABORATION_BOUNDARY_ACTIVITY"
                if inv or rm.get("is_role_reentry")
                else "NO_EXPLICIT_EXPANSION_SIGNAL_AT_NODE"
            )
            if idx in postset:
                r_surface = "POST_CHALLENGE_WINDOW"
            elif scope["stage"] == "R2-R4":
                r_surface = "NATURAL_TEMPORAL_PROCESS"
            else:
                r_surface = "PRE_OR_DIRECT_CHALLENGE_WINDOW"
            row = {
                "schema": "RB-R8A-SEMANTIC-EVENT-LEDGER-v0.1",
                "ledger_event_id": a["audit_id"] + f":node:{idx}",
                "audit_id": a["audit_id"], "case_id": cid, "stage": scope["stage"],
                "domain_id": scope["domain_id"], "event_kind": "ROUTE_NODE",
                "route_index": idx, "agent_role": rn.get("agent_role"),
                "lineage_relevance": sn.get("lineage_relevance"),
                "semantic_function": sn.get("semantic_function"),
                "input_semantics": sn.get("input_semantics") or [],
                "output_semantics": sn.get("output_semantics") or [],
                "semantic_delta": sn.get("semantic_delta"),
                "evidence_refs": sn.get("evidence_refs") or [],
                "independent_evidence_refs": sn.get("independent_evidence_refs") or [],
                "authority_or_status": rn.get("authority_or_status") or [],
                "message_or_invoke_refs": rn.get("message_or_invoke_refs") or [],
                "output_state_refs": rn.get("output_state_refs") or [],
                "invocation_count": inv,
                "role_occurrence_index": rm.get("role_occurrence_index"),
                "is_role_reentry": bool(rm.get("is_role_reentry")),
                "permission_review_surfaces": {
                    "C_information": c_node_surface(sn.get("semantic_function"), sn.get("lineage_relevance")),
                    "P_collaboration_execution": p_surface,
                    "R_temporal": r_surface,
                },
                "semantic_cpr_status": "NOT_ADJUDICATED",
            }
            row["ledger_hash"] = stable_hash(row)
            ledger.append(row)

        for edge in a["semantic_edges"]:
            fr, to = edge.get("from_route_index"), edge.get("to_route_index")
            row = {
                "schema": "RB-R8A-SEMANTIC-EVENT-LEDGER-v0.1",
                "ledger_event_id": a["audit_id"] + ":edge:" + edge["edge_id"],
                "audit_id": a["audit_id"], "case_id": cid, "stage": scope["stage"],
                "domain_id": scope["domain_id"], "event_kind": "SEMANTIC_EDGE",
                "route_index": to, "agent_role": route_by_idx.get(to, {}).get("agent_role"),
                "lineage_relevance": "TARGET_LINEAGE", "semantic_function": "SEMANTIC_RELATION",
                "from_route_index": fr, "to_route_index": to,
                "propagation_type": edge.get("propagation_type"),
                "relation_type": edge.get("relation_type"),
                "input_semantics": [edge.get("semantic_before")] if edge.get("semantic_before") else [],
                "output_semantics": [edge.get("semantic_after")] if edge.get("semantic_after") else [],
                "semantic_delta": edge.get("semantic_delta"),
                "evidence_refs": edge.get("evidence_refs") or [],
                "independent_evidence_refs": edge.get("independent_evidence_refs") or [],
                "authority_or_status": [], "message_or_invoke_refs": [], "output_state_refs": [],
                "permission_review_surfaces": {
                    "C_information": c_edge_surface(edge.get("propagation_type")),
                    "P_collaboration_execution": "EDGE_REQUIRES_SCOPE_CONTEXT_FOR_P_ADJUDICATION",
                    "R_temporal": "POST_CHALLENGE_WINDOW" if fr in postset or to in postset else "NO_R_PRECLASSIFICATION",
                },
                "semantic_cpr_status": "NOT_ADJUDICATED",
            }
            row["ledger_hash"] = stable_hash(row)
            ledger.append(row)

        if scope["stage"] == "R5-R6":
            target_nodes = [x for x in a["semantic_nodes"] if x.get("lineage_relevance") == "TARGET_LINEAGE"]
            target_edges = a["semantic_edges"]
            independent_refs = sorted(
                {ref for x in target_nodes for ref in (x.get("independent_evidence_refs") or [])}
                | {ref for x in target_edges for ref in (x.get("independent_evidence_refs") or [])}
            )
            lc = lineages.get(cid)
            r7 = r7s.get(cid)
            st = r7struct.get(cid)
            packet = {
                "schema": "RB-R8A-DYNAMIC-CPR-PERMISSION-REVIEW-PACKET-v0.1",
                "packet_id": "R8A:" + cid,
                "case_id": cid, "audit_id": a["audit_id"], "domain_id": scope["domain_id"],
                "source_audit_hash": a["audit_hash"],
                "raw_evidence_ref": a["evidence_binding"].get("raw_evidence_ref"),
                "raw_evidence_hash": a["evidence_binding"].get("raw_evidence_hash"),
                "historical_classification": {
                    "semantic_structure_class": judgement.get("semantic_structure_class"),
                    "system_inertia_status": judgement.get("system_inertia_status"),
                    "problematic_bias_status": judgement.get("problematic_bias_status"),
                    "semantic_cpr_status": judgement.get("semantic_cpr_status"),
                },
                "challenge_boundary": {
                    "challenged_source_or_target_ref": judgement.get("challenged_source_or_target_ref"),
                    "direct_stimulus_end_ref": judgement.get("direct_stimulus_end_ref"),
                    "post_stimulus_route_indices": sorted(postset),
                },
                "information_permission_material": {
                    "target_semantic_node_count": len(target_nodes),
                    "semantic_function_counts": dict(Counter(x.get("semantic_function") for x in target_nodes)),
                    "propagation_type_counts": dict(Counter(x.get("propagation_type") for x in target_edges)),
                    "independent_evidence_refs": independent_refs,
                    "lineage_derived_semantic_edge_ids": [
                        x["edge_id"] for x in target_edges if x.get("propagation_type") != "INDEPENDENT_REANCHOR"
                    ],
                    "shared_pool_refs": (lc or {}).get("pool_state_refs", []),
                    "shared_pool_ref_status": (
                        "EXACT_FROM_R6_LINEAGE_CLOSURE"
                        if lc else "NOT_EXPLICITLY_MATERIALIZED_FOR_THIS_CASE_IN_R8A_SOURCE_SET"
                    ),
                },
                "collaboration_execution_material": {
                    "baseline_task_premises": route["nodes"][0].get("input_premises") or [],
                    "realized_agent_roles": all_roles,
                    "unique_agent_roles": sorted(set(all_roles)),
                    "role_reentry_count": sum(max(0, n - 1) for n in seen.values()),
                    "total_invocation_actions": sum(invoke_count(x.get("output_actions")) for x in route["nodes"]),
                    "result_side_scope_status": "REQUIRES_R8B_SEMANTIC_ADJUDICATION",
                },
                "temporal_permission_material": {
                    "r5_one_shot_challenge_present": True,
                    "post_stimulus_persistence": judgement.get("post_stimulus_persistence"),
                    "r7_overlay_present": bool(r7),
                    "r7_persistent_arm_run_id": (r7 or {}).get("persistent_arm_run_id"),
                    "r7_structured_repair_arm_run_id": (r7 or {}).get("structured_repair_arm_run_id"),
                    "r7_action_plan_relation": (r7 or {}).get("action_plan_relation"),
                    "r7_old_fact_authority_reentry": (r7 or {}).get("structured_repair_old_fact_authority_reentry"),
                    "r7_structural_comparison_hash": (st or {}).get("comparison_hash"),
                    "r_forms_to_test": ["LINEAGE_PRESERVING_R", "RETROSPECTIVE_GENERATIVE_R"],
                },
                "lineage_completeness_material": {
                    "available": bool(lc),
                    "closure_id": (lc or {}).get("closure_id"),
                    "repair_anchor_ref": (lc or {}).get("repair_anchor_ref"),
                    "content_address": (lc or {}).get("content_address"),
                    "closure_hash": (lc or {}).get("closure_hash"),
                },
                "r8b_questions": [
                    "Did operational reality authority grow beyond independently supported evidence?",
                    "Did lineage-derived semantic support accumulate without equivalent independent evidence?",
                    "Did collaboration/execution scope exceed the supported task boundary, including recursive reopening or silent side action?",
                    "Did review/recompute/reopen activity preserve prior C/P or generate new C/P?",
                    "Are apparent multi-Agent supports independent or descendants of one root lineage?",
                ],
                "semantic_cpr_status": "NOT_ADJUDICATED",
            }
            packet["packet_hash"] = stable_hash(packet)
            packets.append(packet)

    for cid, r7 in r7s.items():
        st = r7struct.get(cid)
        lc = lineages.get(cid)
        for arm, key in (
            ("R7_P_PERSISTENT_SEMANTIC", "persistent_arm_run_id"),
            ("R7_S_STRUCTURED_LINEAGE_REPAIR", "structured_repair_arm_run_id"),
        ):
            row = {
                "schema": "RB-R8A-SEMANTIC-EVENT-LEDGER-v0.1",
                "ledger_event_id": f"R8A:{cid}:{arm}",
                "audit_id": None, "case_id": cid, "stage": "R7",
                "domain_id": r7.get("domain_id"), "event_kind": "R7_CONTROL_OVERLAY",
                "route_index": None, "agent_role": None, "lineage_relevance": "TARGET_LINEAGE",
                "semantic_function": arm,
                "input_semantics": [r7.get("semantic_reading")],
                "output_semantics": [r7.get("action_plan_relation")],
                "semantic_delta": r7.get("interpretation_boundary"),
                "evidence_refs": [
                    x for x in [r7.get("audit_hash"), r7.get(key), (st or {}).get("comparison_hash"), (lc or {}).get("closure_hash")] if x
                ],
                "independent_evidence_refs": [],
                "authority_or_status": [
                    str(r7.get("structured_repair_authority_result"))
                    if arm.startswith("R7_S") else str(r7.get("persistent_semantic_status"))
                ],
                "message_or_invoke_refs": [], "output_state_refs": [],
                "permission_review_surfaces": {
                    "C_information": "CONTROLLED_AUTHORITY_REVIEW_SURFACE",
                    "P_collaboration_execution": "CONTROLLED_RECOMPOSITION_REVIEW_SURFACE",
                    "R_temporal": "CONTROLLED_RETROSPECTIVE_REPAIR_REVIEW_SURFACE_NOT_R_POSITIVE",
                },
                "semantic_cpr_status": "NOT_ADJUDICATED",
            }
            row["ledger_hash"] = stable_hash(row)
            ledger.append(row)

        if lc:
            row = {
                "schema": "RB-R8A-SEMANTIC-EVENT-LEDGER-v0.1",
                "ledger_event_id": f"R8A:{cid}:lineage-closure",
                "audit_id": None, "case_id": cid, "stage": "R6-LINEAGE",
                "domain_id": r7.get("domain_id"), "event_kind": "SEMANTIC_LINEAGE_CLOSURE",
                "route_index": None, "agent_role": None, "lineage_relevance": "TARGET_LINEAGE",
                "semantic_function": "ADDRESSABLE_LINEAGE_CLOSURE",
                "input_semantics": [lc.get("target_semantic_id")],
                "output_semantics": [lc.get("completeness_status")],
                "semantic_delta": "Addressable lineage closure is structural evidence and not a CPR verdict.",
                "evidence_refs": lc.get("source_refs", []) + lc.get("transformation_refs", []) + lc.get("adoption_relation_refs", []),
                "independent_evidence_refs": [],
                "authority_or_status": lc.get("authority_transition_refs", []),
                "message_or_invoke_refs": [],
                "output_state_refs": lc.get("pool_state_refs", []),
                "permission_review_surfaces": {
                    "C_information": "LINEAGE_AUTHORITY_HISTORY_REVIEW_SURFACE",
                    "P_collaboration_execution": "DESCENDANT_PROCESS_SCOPE_REVIEW_SURFACE",
                    "R_temporal": "ADDRESSABLE_HISTORY_REVIEW_SURFACE",
                },
                "semantic_cpr_status": "NOT_ADJUDICATED",
            }
            row["ledger_hash"] = stable_hash(row)
            ledger.append(row)

    case_index.sort(key=lambda x: (x["stage"], x["domain_id"], x["case_id"]))
    ledger.sort(key=lambda x: (x["case_id"], x["stage"], str(x.get("route_index")), x["ledger_event_id"]))
    packets.sort(key=lambda x: (x["domain_id"], x["case_id"]))

    out = Path(outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r8a_output_dir")
    out.mkdir(parents=True)

    write_jsonl(out / "case_index.jsonl", case_index)
    write_jsonl(out / "semantic_event_ledger.jsonl", ledger)
    write_jsonl(out / "permission_review_packets.jsonl", packets)

    kinds = Counter(x["event_kind"] for x in ledger)
    functions = Counter(x.get("semantic_function") for x in ledger if x.get("semantic_function"))
    domains = Counter(x["domain_id"] for x in packets)
    summary = {
        "schema": "RB-R8A-DYNAMIC-CPR-FIRST-ROUND-SUMMARY-v0.1",
        "date": "2026-09-20",
        "status": "R8A_SEMANTIC_EVENT_RECONSTRUCTION_COMPLETE_NOT_ADJUDICATED",
        "source_complete_route_audit_count": len(audits),
        "natural_audit_count": sum(1 for x in audits if x["experiment_scope"]["stage"] == "R2-R4"),
        "r5_r6_audit_count": sum(1 for x in audits if x["experiment_scope"]["stage"] == "R5-R6"),
        "permission_review_packet_count": len(packets),
        "r7_overlay_case_count": len(r7s),
        "r6_lineage_closure_case_count": len(lineages),
        "ledger_event_count": len(ledger),
        "ledger_event_kind_counts": dict(kinds),
        "semantic_function_counts": dict(functions),
        "packet_domain_counts": dict(domains),
        "stronger_system_inertia_packet_count": sum(
            1 for x in packets
            if x["historical_classification"]["system_inertia_status"] == "CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE"
        ),
        "semantic_cpr_adjudicated_case_count": 0,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "interpretation_boundary": [
            "R8-A reconstructs evidence-bound semantic events and review surfaces only.",
            "Permission-review surfaces are not positive C/P/R labels.",
            "Independent re-anchoring remains an explicit healthy comparator.",
            "System Inertia is not automatically R.",
            "R7 intervention outcomes are control overlays, not CPR verdicts.",
        ],
        "execution_boundary": {
            "new_provider_calls": 0,
            "new_paid_evaluator_calls": 0,
            "subject_reruns": 0,
            "raw_evidence_mutated": False,
        },
    }
    summary["summary_hash"] = stable_hash(summary)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        "schema": "RB-R8A-DYNAMIC-CPR-FIRST-ROUND-MANIFEST-v0.1",
        "date": "2026-09-20",
        "status": "FROZEN_DERIVATIVE_R8A_MATERIAL",
        "outputs": {},
    }
    for name in ("case_index.jsonl", "semantic_event_ledger.jsonl", "permission_review_packets.jsonl", "summary.json"):
        p = out / name
        manifest["outputs"][name] = {"sha256": file_sha256(p), "size_bytes": p.stat().st_size}
    manifest["manifest_hash"] = stable_hash(manifest)
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r2r6-audits", required=True)
    ap.add_argument("--lineage-closures", required=True)
    ap.add_argument("--r7-structural", required=True)
    ap.add_argument("--r7-semantic", required=True)
    ap.add_argument("--outdir", required=True)
    a = ap.parse_args()
    s = build(
        r2r6_path=a.r2r6_audits,
        lineage_path=a.lineage_closures,
        r7_structural_path=a.r7_structural,
        r7_semantic_path=a.r7_semantic,
        outdir=a.outdir,
    )
    print("R8A_STATUS=" + s["status"])
    print("LEDGER_EVENTS=" + str(s["ledger_event_count"]))
    print("PERMISSION_PACKETS=" + str(s["permission_review_packet_count"]))
    print("SEMANTIC_CPR_STATUS=" + s["semantic_cpr_status"])
    print("SUBJECT_RERUN_REQUIRED=NO")


if __name__ == "__main__":
    main()
