"""Offline evidence gates. Never adjudicates semantic C/P/R or calls a provider."""

from __future__ import annotations

import json
from pathlib import Path

from .interaction_adapter import validate_interactions

BOUNDARY_REQUIREMENTS = {
    "shared_common_pool": {"shared_state"},
    "direct_peer_messaging": {"send_message", "receive_message"},
    "hierarchical_orchestrator": {"delegate", "artifact_return"},
    "a2a_remote_boundary": {"remote_task", "artifact_return"},
    "mcp_tool_resource_boundary": {"tool_call", "resource_read"},
    "persistent_memory_retrieval": {"memory_write", "memory_retrieve"},
    "graph_state_machine": {"handoff", "shared_state"},
}


def conformance(events: list[dict], *, expected_architecture: str, raw_lookup=None,
                required_carrier_route=False, require_boundary=False, repair_record=None) -> dict:
    base = validate_interactions(events)
    failures = list(base["failures"])
    if not events or any(e.get("architecture_id") != expected_architecture for e in events):
        failures.append("adapter_contract:architecture_or_empty")
    if len({e.get("run_id") for e in events}) != 1 or len({e.get("adapter_version") for e in events}) != 1:
        failures.append("adapter_contract:mixed_run_or_version")
    if expected_architecture not in BOUNDARY_REQUIREMENTS:
        failures.append("adapter_contract:unknown_architecture")
    if require_boundary:
        surfaces = {e.get("surface") for e in events if e.get("observation") not in ("PROPOSED", "FAILED", "UNAVAILABLE")}
        if not BOUNDARY_REQUIREMENTS.get(expected_architecture, set()) <= surfaces:
            failures.append("adapter_contract:native_boundary_unobserved")
        if expected_architecture == "direct_peer_messaging" and any(
            e.get("surface") == "shared_state" and e.get("observation") == "INPUT_EXPOSED" for e in events
        ):
            failures.append("adapter_contract:peer_exposed_common_pool")
        if expected_architecture in ("hierarchical_orchestrator", "a2a_remote_boundary") and not any(
            e.get("surface") == "artifact_return" and e.get("parent_event_ids") for e in events
        ):
            failures.append("lineage_reconstructability:unlinked_return")
    if any(e.get("observation") == "UNAVAILABLE" for e in events):
        failures.append("event_completeness:unavailable_boundary")
    if raw_lookup is None:
        failures.append("raw_reference_resolvability:lookup_required")
    elif any(not raw_lookup(e["raw_ref"]) for e in events):
        failures.append("raw_reference_resolvability:missing")
    if required_carrier_route:
        linked_exposures = [e for e in events if e.get("observation") == "INPUT_EXPOSED" and e.get("parent_event_ids")]
        if not linked_exposures:
            failures.append("lineage_reconstructability:no_linked_exposure")
        # This confirms an exposure path only. Semantic use and downstream effect
        # require independent raw-backed audit records and remain NOT_ASSESSED.
    if repair_record is not None:
        if not (repair_record.get("affected_closure_refs") and repair_record.get("preserved_state_refs")
                and repair_record.get("before_after_evidence_refs") and repair_record.get("reentry_audit_refs")):
            failures.append("repair_locality_non_target_preservation_reentry:incomplete")
    mechanical = "PASS" if not failures else "FAIL"
    gates = {
        "interaction_adapter_contract": mechanical,
        "event_completeness": "FAIL" if any("unavailable_boundary" in f for f in failures) else mechanical,
        "source_carrier_addressability": "FAIL" if any("unaddressable" in f or "raw_ref_missing" in f or "raw_reference_resolvability" in f for f in failures) else mechanical,
        "lineage_reconstructability": "FAIL" if any("lineage_reconstructability" in f or "missing_or_forward_parent" in f for f in failures) else ("PASS" if required_carrier_route and mechanical == "PASS" else "NOT_ASSESSED"),
        "authority_transition_auditability": "NOT_ASSESSED",
        "repair_locality": "NOT_ASSESSED",
        "non_target_preservation": "NOT_ASSESSED",
        "reentry_detection": "NOT_ASSESSED",
        "frozen_evidence_integrity": "EXTERNAL_SHA256_GATE_REQUIRED",
    }
    return {**base, "status": mechanical, "failures": failures, "gates": gates,
            "pilot_natural_completion": "NOT_ASSESSED",
            "source_use_effect": "NOT_ADJUDICATED",
            "repair_portability": "NOT_ASSESSED"}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True, help="append-only normalized event JSONL")
    ap.add_argument("--architecture", required=True)
    ap.add_argument("--raw-index", required=True, help="JSON array of resolvable raw locators")
    args = ap.parse_args()
    events = [json.loads(line) for line in Path(args.events).read_text().splitlines() if line.strip()]
    raw_refs = set(json.loads(Path(args.raw_index).read_text()))
    result = conformance(events, expected_architecture=args.architecture, raw_lookup=lambda ref: ref in raw_refs)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
