from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .core import stable_hash

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BINDING = "configs/r5r6_engineering_package_source_binding_v0.1.json"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    material = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    return hashlib.sha1(material).hexdigest()


def _verify_sources(binding: dict) -> list[str]:
    refs = []
    for source in binding["source_files"]:
        path = ROOT / source["path"]
        _require(path.exists(), "missing_bound_source:" + source["path"])
        actual = _git_blob_sha(path)
        _require(actual == source["git_blob_sha"], "bound_source_blob_changed:" + source["path"])
        refs.append("git-blob:" + actual + ":" + source["path"])
    return refs


def _relation(
    relation_id: str,
    source_ref: str,
    destination_ref: str,
    relation_type: str,
    evidence_level: str,
    semantic_use_status: str,
    evidence_refs: list[str],
    target_semantic_id: str,
    content_address: str,
    notes: str,
) -> dict:
    return {
        "schema": "RB-PROCESS-INTEGRITY-RELATION-EVIDENCE-v0.2",
        "relation_id": relation_id,
        "source_ref": source_ref,
        "destination_ref": destination_ref,
        "target_semantic_id": target_semantic_id,
        "content_address": content_address,
        "semantic_scope_status": "IN_TARGET_LINEAGE",
        "relation_type": relation_type,
        "evidence_level": evidence_level,
        "semantic_use_status": semantic_use_status,
        "evidence_refs": evidence_refs,
        "actor": None,
        "turn": None,
        "notes": notes,
    }


def build_package(binding_path: str = DEFAULT_BINDING) -> dict:
    binding = _load_json(ROOT / binding_path)
    _require(binding["schema"] == "RB-R5R6-ENGINEERING-PACKAGE-SOURCE-BINDING-v0.1", "binding_schema_invalid")
    raw_source_refs = _verify_sources(binding)

    audits = _load_jsonl(ROOT / "reviews/v5_semantic_mechanism_reaudit_2026-09-18/audit_records.jsonl")
    by_id = {row["audit_id"]: row for row in audits}
    for audit_id in binding["required_audit_ids"]:
        _require(audit_id in by_id, "required_audit_missing:" + audit_id)

    required_status = {
        "V5-REAUDIT-001-E5-UNSTABLE": "SUPPORTED",
        "V5-REAUDIT-002-E6-TRANSFORMATION": "SUPPORTED",
        "V5-REAUDIT-003-E8-ADOPTION": "SUPPORTED",
        "V5-REAUDIT-004-E11-SUPPORT": "SUPPORTED_CANDIDATE",
        "V5-REAUDIT-005-STABLE-POOL-EXISTENCE": "SUPPORTED",
        "V5-REAUDIT-006-DIRECT-POOL-CONSUMPTION": "SUPPORTED_CANDIDATE",
        "V5-REAUDIT-007-E32-EXPOSURE": "SUPPORTED_CANDIDATE",
        "V5-REAUDIT-008-R5-DRIVER": "SUPPORTED_CANDIDATE",
        "V5-REAUDIT-009-R6-DESCENDANT-PERSISTENCE": "SUPPORTED",
    }
    for audit_id, status in required_status.items():
        _require(by_id[audit_id]["claim_status"] == status, "audit_status_changed:" + audit_id)

    historical = _load_json(ROOT / "results/v5_historical_rederivation/rederivation_bundle_v0_1.json")
    _require(historical["summary"]["j0_is_semantic_origin"] == "CONTRADICTED", "j0_origin_boundary_changed")
    _require(historical["summary"]["source_pool_status_decoupling"] == "OBSERVED", "source_pool_decoupling_missing")
    _require(historical["summary"]["raw_evidence_mutated"] is False, "historical_raw_evidence_mutated")

    target = binding["target"]
    target_id = target["target_semantic_id"]
    content_address = "rbca:" + stable_hash({
        "state_key": target["state_key"],
        "nested_field": target["nested_field"],
        "target_value": target["target_value"],
        "source_event_index": target["source_event_index"],
        "source_actor": target["source_actor"],
        "parent_state_hash": target["parent_state_hash"],
    })

    relations = [
        _relation(
            "R5R6-REL-001-E5-E6",
            "arena_event:5:semantic:A.preliminary_stock=1520",
            "arena_event:6:constraint:A_uplift_monitor_replenish",
            "INHERITED_INTO_STATE_OR_ACTION",
            "INHERITED_CARRIER",
            "ADOPTED_AS_PREMISE",
            ["audit:V5-REAUDIT-001-E5-UNSTABLE", "audit:V5-REAUDIT-002-E6-TRANSFORMATION"],
            target_id,
            content_address,
            "Observed transformation from unresolved source value into an operational planning constraint; not a claim of unique causal origin.",
        ),
        _relation(
            "R5R6-REL-002-E6-E8",
            "arena_event:6:constraint:A_uplift_monitor_replenish",
            "arena_event:8:constraint:advertising_guardrail",
            "ADOPTED_AS_DECISION_PREMISE",
            "ADOPTED_CARRIER",
            "ADOPTED_AS_PREMISE",
            ["audit:V5-REAUDIT-003-E8-ADOPTION"],
            target_id,
            content_address,
            "Cross-Agent semantic adoption is supported; the exact transport channel is not assumed to be a stable pool.",
        ),
        _relation(
            "R5R6-REL-003-E8-E11",
            "arena_event:8:constraint:advertising_guardrail",
            "arena_event:11:state:inventory_risk_support",
            "PROPAGATED_TO_DESCENDANT",
            "PROPAGATED_CARRIER",
            "ADOPTED_AS_PREMISE",
            ["audit:V5-REAUDIT-004-E11-SUPPORT"],
            target_id,
            content_address,
            "E11 materializes source-descended operational meaning into shared state and is a supported Structural Support candidate.",
        ),
        _relation(
            "R5R6-REL-004-E11-E32",
            "arena_event:11:state:inventory_risk_support",
            target["repair_anchor_ref"],
            "POOL_MATERIALIZATION",
            "INHERITED_CARRIER",
            "OBSERVED_REFERENCE_ONLY",
            ["audit:V5-REAUDIT-004-E11-SUPPORT", "audit:V5-REAUDIT-007-E32-EXPOSURE"],
            target_id,
            content_address,
            "J0 is a later machine-addressable Repair Anchor, not semantic origin or proven first pool entry.",
        ),
        _relation(
            "R5R6-REL-005-R5-AUTHORITY",
            target["repair_anchor_ref"],
            "r5:one_shot:fact_to_unconfirmed",
            "AUTHORITY_TRANSITION",
            "DELIVERED_OR_READ_CARRIER",
            "OBSERVED_REFERENCE_ONLY",
            ["audit:V5-REAUDIT-008-R5-DRIVER", "R5_FORMAL_RESULT:intervention-integrity"],
            target_id,
            content_address,
            "One prompt-visible authority withdrawal, zero reinjection and no experiment-origin persistent-state mutation.",
        ),
        _relation(
            "R5R6-REL-006-R6-POOL",
            target["repair_anchor_ref"],
            "r6:s2:stable_shared_pool",
            "POOL_MATERIALIZATION",
            "PROPAGATED_CARRIER",
            "OBSERVED_REFERENCE_ONLY",
            ["audit:V5-REAUDIT-005-STABLE-POOL-EXISTENCE"],
            target_id,
            content_address,
            "Stable shared-state availability is supported in the observed continuation; this does not backdate the first pool-entry event.",
        ),
        _relation(
            "R5R6-REL-007-R6-DESCENDANTS",
            "r6:s2:stable_shared_pool",
            "r6:s2:stock_risk_cap_fallback_descendants",
            "INHERITED_INTO_STATE_OR_ACTION",
            "INHERITED_CARRIER",
            "ADOPTED_AS_PREMISE",
            ["audit:V5-REAUDIT-006-DIRECT-POOL-CONSUMPTION", "audit:V5-REAUDIT-009-R6-DESCENDANT-PERSISTENCE"],
            target_id,
            content_address,
            "Downstream semantic use and descendant persistence are evidence-supported. Exclusive field-level pool-to-reason attribution remains unresolved and is not claimed.",
        ),
    ]

    source_refs = ["arena_event:5:semantic:A.preliminary_stock=1520", "audit:V5-REAUDIT-001-E5-UNSTABLE"]
    transformation_refs = [
        "arena_event:6:constraint:A_uplift_monitor_replenish",
        "arena_event:8:constraint:advertising_guardrail",
        "arena_event:11:state:inventory_risk_support",
    ]
    authority_refs = [
        target["repair_anchor_ref"] + ":status=fact",
        "r5:one_shot:fact_to_unconfirmed",
        "r6:s2:shared_container_status=fact",
    ]
    pool_refs = [
        "arena_event:11:state:inventory_risk_support",
        target["repair_anchor_ref"],
        "r6:s2:stable_shared_pool",
    ]
    descendant_refs = [
        "arena_event:6:constraint:A_uplift_monitor_replenish",
        "arena_event:8:constraint:advertising_guardrail",
        "arena_event:11:state:inventory_risk_support",
        "r6:s2:stock_risk_cap_fallback_descendants",
    ]

    closure = {
        "schema": "RB-SEMANTIC-LINEAGE-CLOSURE-v0.1",
        "closure_id": "R5R6-HISTORICAL-J0-LINEAGE-v0.1",
        "target_semantic_id": target_id,
        "repair_anchor_ref": target["repair_anchor_ref"],
        "content_address": content_address,
        "source_refs": source_refs,
        "transformation_refs": transformation_refs,
        "adoption_relation_refs": ["R5R6-REL-002-E6-E8"],
        "authority_transition_refs": authority_refs,
        "pool_state_refs": pool_refs,
        "revision_refs": [],
        "rejected_or_abandoned_relevant_refs": [],
        "relevant_descendant_refs": descendant_refs,
        "raw_evidence_refs": raw_source_refs,
        "excluded_unrelated_refs": [],
        "missing_required_components": [],
        "completeness_status": "COMPLETE_FOR_AUTHORIZED_REPAIR",
        "closure_hash": None,
    }
    closure["closure_hash"] = stable_hash({k: v for k, v in closure.items() if k != "closure_hash"})

    gate = {
        "schema": "RB-LINEAGE-COMPLETENESS-GATE-v0.1",
        "gate_id": "R5R6-HISTORICAL-J0-GATE-v0.1",
        "semantic_lineage_closure_ref": closure["closure_id"],
        "dimensions": {
            "source_bound": "YES",
            "transformations_bound": "YES",
            "authority_history_bound": "YES",
            "pool_state_bound": "YES",
            "affected_descendants_bound": "YES",
            "evidence_pointers_bound": "YES",
        },
        "missing_components": [],
        "status": "COMPLETE_FOR_AUTHORIZED_REPAIR",
        "automatic_repair_allowed": False,
        "boundary": (
            "Complete for the frozen declared R5-R6 observation horizon and the E32/J0-scoped engineering experiment. "
            "This does not claim global exhaustive lineage, first support/pool identity, exclusive pool-to-reason attribution, "
            "semantic CPR, or active repair authorization."
        ),
        "gate_hash": None,
    }
    gate["gate_hash"] = stable_hash({k: v for k, v in gate.items() if k != "gate_hash"})

    evidenced = [
        target["repair_anchor_ref"],
        "r6:s2:stable_shared_pool",
        "r6:s2:stock_risk_cap_fallback_descendants",
    ]
    repair_refs = [
        target["repair_anchor_ref"] + ":status",
        "r6:s2:stable_shared_pool",
        "r6:s2:stock_risk_cap_fallback_descendants",
    ]
    packet = {
        "schema": "RB-SEMANTIC-REPAIR-PACKET-v0.1",
        "packet_id": "R5R6-HISTORICAL-J0-REPAIR-PACKET-v0.1",
        "repair_anchor_ref": target["repair_anchor_ref"],
        "target_semantic_id": target_id,
        "content_address": content_address,
        "trace_root_ref": target["trace_root_ref"],
        "semantic_lineage_closure_ref": closure["closure_id"],
        "lineage_completeness_gate_ref": gate["gate_id"],
        "evidence_supported_affected_closure_refs": evidenced,
        "mechanically_required_replay_refs": ["r7:exact_pre_j0_checkpoint", "r7:authority_ancestor_turn"],
        "repair_closure_refs": repair_refs,
        "preserved_unrelated_refs": [],
        "raw_evidence_refs": raw_source_refs,
        "allowed_repair_operations": [
            "AUTHORITY_DOWNGRADE",
            "POOL_INVALIDATION",
            "DESCENDANT_INVALIDATION",
            "SELECTIVE_RECOMPUTE",
            "DEPENDENT_DECISION_REOPEN"
        ],
        "unresolved_gaps": [
            "Exact first Structural Support identity remains NOT_ESTABLISHED.",
            "Exact first Stable Shared Pool entry remains NOT_ESTABLISHED.",
            "Exclusive field-level pool-to-judgment attribution remains unresolved."
        ],
        "repair_authorization_status": "READY_FOR_SEPARATE_AUTHORIZATION",
        "packet_hash": None,
    }
    packet["packet_hash"] = stable_hash({k: v for k, v in packet.items() if k != "packet_hash"})

    potentially = list(dict.fromkeys(transformation_refs + pool_refs + descendant_refs))
    lineage_record = {
        "schema": "RB-PROCESS-INTEGRITY-LINEAGE-RECORD-v0.4",
        "record_id": "R5R6-HISTORICAL-J0-LINEAGE-RECORD-v0.1",
        "record_type": "R7_SEMANTIC_REPAIR_PACKET",
        "legacy_root_ref": "E32/J0",
        "repair_anchor_ref": target["repair_anchor_ref"],
        "target_semantic_id": target_id,
        "content_address": content_address,
        "trace_root_ref": target["trace_root_ref"],
        "semantic_lineage_closure_ref": closure["closure_id"],
        "lineage_completeness_status": gate["status"],
        "detection_surface_ref": target["repair_anchor_ref"],
        "selected_intervention_surface_ref": target["repair_anchor_ref"] + ":status",
        "relation_evidence_refs": [r["relation_id"] for r in relations],
        "structural_support_refs": ["arena_event:11:state:inventory_risk_support"],
        "pool_state_refs": pool_refs,
        "exposure_anchor_refs": [target["repair_anchor_ref"]],
        "potentially_affected_closure": {"refs": potentially, "closure_hash": stable_hash(potentially)},
        "evidence_supported_affected_closure": {"refs": evidenced, "closure_hash": stable_hash(evidenced)},
        "mechanically_required_replay_refs": packet["mechanically_required_replay_refs"],
        "candidate_intervention_surface_refs": [target["repair_anchor_ref"] + ":status"],
        "repair_closure": {"refs": repair_refs, "closure_hash": stable_hash(repair_refs)},
        "preserved_unrelated_refs": [],
        "lineage_gap_refs": [],
        "prior_revision_hash": None,
        "repaired_revision_hash": None,
        "old_lineage_reentry_refs": [],
        "scientific_status": "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE",
    }

    summary = {
        "schema": "RB-R5R6-ENGINEERING-PACKAGE-SUMMARY-v0.1",
        "status": "READY_FOR_R7_SEPARATE_AUTHORIZATION",
        "completeness_scope": binding["completeness_scope"],
        "repair_anchor_ref": target["repair_anchor_ref"],
        "target_semantic_id": target_id,
        "content_address": content_address,
        "relation_evidence_count": len(relations),
        "semantic_lineage_closure_id": closure["closure_id"],
        "semantic_lineage_closure_hash": closure["closure_hash"],
        "lineage_completeness_gate_id": gate["gate_id"],
        "lineage_completeness_status": gate["status"],
        "lineage_completeness_gate_hash": gate["gate_hash"],
        "semantic_repair_packet_id": packet["packet_id"],
        "semantic_repair_packet_hash": packet["packet_hash"],
        "active_repair_authorized": False,
        "new_subject_provider_calls": 0,
        "new_paid_evaluator_calls": 0,
        "raw_evidence_mutated": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "boundary": gate["boundary"],
    }
    summary["summary_hash"] = stable_hash(summary)

    return {
        "relation_evidence": relations,
        "semantic_lineage_closure": closure,
        "lineage_completeness_gate": gate,
        "semantic_repair_packet": packet,
        "process_integrity_lineage_record": lineage_record,
        "summary": summary,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-binding", default=DEFAULT_BINDING)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    bundle = build_package(args.source_binding)
    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r5r6_engineering_package_dir")
    out.mkdir(parents=True)

    (out / "relation_evidence.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in bundle["relation_evidence"]),
        encoding="utf-8",
    )
    for key in [
        "semantic_lineage_closure",
        "lineage_completeness_gate",
        "semantic_repair_packet",
        "process_integrity_lineage_record",
        "summary",
    ]:
        _write_json(out / (key + ".json"), bundle[key])

    s = bundle["summary"]
    print("R5R6_ENGINEERING_PACKAGE=" + s["status"])
    print("LINEAGE_COMPLETENESS=" + s["lineage_completeness_status"])
    print("REPAIR_ANCHOR=" + s["repair_anchor_ref"])
    print("SEMANTIC_REPAIR_PACKET_HASH=" + s["semantic_repair_packet_hash"])
    print("ACTIVE_REPAIR_AUTHORIZED=NO")
    print("NEW_PROVIDER_CALLS=0")
    print("NEW_PAID_EVALUATOR_CALLS=0")


if __name__ == "__main__":
    main()
