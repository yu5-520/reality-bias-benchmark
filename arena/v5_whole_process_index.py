from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping

from .core import stable_hash


def _state_write_rows(trace: Mapping[str, Any]) -> list[dict]:
    rows = []
    for event in trace.get("events") or []:
        if not event.get("realized_in_baseline"):
            continue
        if event.get("action_type") not in ("write_state", "revise_final_state"):
            continue
        action = event.get("action") or {}
        pairs = []
        if event.get("action_type") == "write_state" and action.get("key"):
            pairs = [(str(action["key"]), action.get("value"))]
        elif event.get("action_type") == "revise_final_state":
            patch = action.get("patch") or {}
            if isinstance(patch, Mapping):
                pairs = [(str(k), v) for k, v in patch.items()]
        for key, value in pairs:
            rows.append({
                "event_index": int(event["event_index"]),
                "turn": int(event["turn"]),
                "actor": event.get("actor"),
                "state_key": key,
                "value_hash": stable_hash(value),
                "status": ((event.get("shared_state_metadata_after") or {}).get(key) or {}).get("status"),
            })
    return rows


def _visibility_rows(trace: Mapping[str, Any]) -> list[dict]:
    rows = []
    for call in trace.get("model_calls") or []:
        turn = call.get("turn")
        actor = call.get("agent_id")
        runtime = call.get("runtime_snapshot") or {}
        metadata = runtime.get("shared_state_metadata") or {}
        if not isinstance(turn, int) or not actor or not isinstance(metadata, Mapping):
            continue
        for key, meta in metadata.items():
            if not isinstance(meta, Mapping):
                continue
            src = meta.get("event_index")
            if not isinstance(src, int):
                continue
            rows.append({
                "turn": turn,
                "actor": str(actor),
                "state_key": str(key),
                "source_event_index": src,
                "source_writer": meta.get("writer"),
                "source_status": meta.get("status"),
                "call_status": call.get("status"),
                "event_index_start": call.get("event_index_start"),
                "event_index_end": call.get("event_index_end"),
            })
    return rows


def derive_v5_structural_index(trace: Mapping[str, Any]) -> dict:
    writes = _state_write_rows(trace)
    visibility = _visibility_rows(trace)
    by_source: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for row in visibility:
        by_source[(row["source_event_index"], row["state_key"])].append(row)

    candidates = []
    visibility_ledger = []
    address_index = []

    for write in writes:
        content_address = stable_hash({
            "state_key": write["state_key"],
            "value_hash": write["value_hash"],
            "source_event_index": write["event_index"],
            "source_actor": write["actor"],
        })
        address_index.append({
            "content_address": content_address,
            "candidate_ref": f"arena_event:{write['event_index']}:state:{write['state_key']}",
            "state_key": write["state_key"],
            "value_hash": write["value_hash"],
            "source_event_index": write["event_index"],
            "source_actor": write["actor"],
        })

        vis = [
            r for r in by_source.get((write["event_index"], write["state_key"]), [])
            if r["turn"] > write["turn"]
        ]
        for r in vis:
            visibility_ledger.append({
                "content_address": content_address,
                "candidate_ref": f"arena_event:{write['event_index']}:state:{write['state_key']}",
                **r,
            })
        if not vis:
            continue

        actors = sorted({r["actor"] for r in vis})
        active_after_visibility = sum(
            1 for r in vis
            if r.get("call_status") == "completed"
            and isinstance(r.get("event_index_start"), int)
            and isinstance(r.get("event_index_end"), int)
            and r["event_index_end"] > r["event_index_start"]
        )
        support = True
        pool = len(vis) >= 2 or len(actors) >= 2
        exposure = pool and active_after_visibility >= 1
        repair_anchor = exposure

        row = {
            "candidate_ref": f"arena_event:{write['event_index']}:state:{write['state_key']}",
            "content_address": content_address,
            "source_event_index": write["event_index"],
            "source_turn": write["turn"],
            "source_actor": write["actor"],
            "state_key": write["state_key"],
            "value_hash": write["value_hash"],
            "source_status": write["status"],
            "later_visibility_count": len(vis),
            "distinct_visible_actor_count": len(actors),
            "visible_actors": actors,
            "first_later_visibility_turn": min(r["turn"] for r in vis),
            "activity_after_visibility_count": active_after_visibility,
            "structural_support_candidate": support,
            "stable_shared_pool_candidate": pool,
            "structural_exposure_candidate": exposure,
            "structural_repair_anchor_candidate": repair_anchor,
            "repair_anchor_qualification": {
                "addressable": True,
                "provenance_bound": True,
                "descendant_visibility_observed": len(vis) > 0,
                "multi_actor_or_repeated_visibility": pool,
                "later_process_activity_observed": active_after_visibility >= 1,
            },
            "semantic_lineage_recoverability_status": (
                "STRUCTURAL_PROVENANCE_READY_SEMANTIC_AUDIT_REQUIRED"
            ),
            "semantic_direct_consumption_status": "NOT_ADJUDICATED",
        }
        row["candidate_hash"] = stable_hash(row)
        candidates.append(row)

    candidates.sort(key=lambda r: (r["source_event_index"], r["state_key"]))
    supports = [r for r in candidates if r["structural_support_candidate"]]
    pools = [r for r in candidates if r["stable_shared_pool_candidate"]]
    exposures = [r for r in candidates if r["structural_exposure_candidate"]]
    repair_anchors = [r for r in candidates if r["structural_repair_anchor_candidate"]]

    first_support = supports[0] if supports else None
    first_pool = pools[0] if pools else None
    first_exposure = exposures[0] if exposures else None
    first_repair_anchor = repair_anchors[0] if repair_anchors else None

    def distance(target):
        if target is None:
            return None
        return {
            "source_event_index": target["source_event_index"],
            "source_turn": target["source_turn"],
            "first_later_visibility_turn": target["first_later_visibility_turn"],
            "turn_distance_to_first_visibility": target["first_later_visibility_turn"] - target["source_turn"],
        }

    mechanism_observables = {
        "engineering_requirement": False,
        "first_support_candidate_ref": (first_support or {}).get("candidate_ref"),
        "first_pool_candidate_ref": (first_pool or {}).get("candidate_ref"),
        "first_exposure_candidate_ref": (first_exposure or {}).get("candidate_ref"),
        "first_support_distance": distance(first_support),
        "first_pool_distance": distance(first_pool),
        "first_exposure_distance": distance(first_exposure),
    }

    engineering_core = {
        "repair_anchor_candidate_refs": [r["candidate_ref"] for r in repair_anchors],
        "first_repair_anchor_candidate_ref": (first_repair_anchor or {}).get("candidate_ref"),
        "content_address_count": len(address_index),
        "pool_visibility_ledger_count": len(visibility_ledger),
        "semantic_lineage_recoverability_status": (
            "STRUCTURAL_PROVENANCE_READY_SEMANTIC_AUDIT_REQUIRED"
            if address_index else "NO_ADDRESSABLE_STATE_OBSERVED"
        ),
        "first_node_localization_required_for_repair": False,
    }

    out = {
        "schema": "RB-V5-WHOLE-PROCESS-STRUCTURAL-INDEX-v0.2",
        "trajectory_id": trace.get("run_id"),
        "run_status": trace.get("run_status"),
        "state_materialization_count": len(writes),
        "pool_visibility_observation_count": len(visibility),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "content_address_index": address_index,
        "pool_visibility_ledger": visibility_ledger,
        "engineering_core": engineering_core,
        "mechanism_observables": mechanism_observables,
        # Backward-compatible first-node fields remain available but are not engineering prerequisites.
        "first_support_candidate_ref": mechanism_observables["first_support_candidate_ref"],
        "first_pool_candidate_ref": mechanism_observables["first_pool_candidate_ref"],
        "first_exposure_candidate_ref": mechanism_observables["first_exposure_candidate_ref"],
        "first_support_distance": mechanism_observables["first_support_distance"],
        "first_pool_distance": mechanism_observables["first_pool_distance"],
        "first_exposure_distance": mechanism_observables["first_exposure_distance"],
        "direct_pool_consumption_semantic_status": "NOT_ADJUDICATED",
        "scientific_boundary": (
            "Shared-state visibility and content address are structural evidence only. "
            "Semantic adoption/direct consumption and complete Semantic Lineage Closure "
            "require relation-level/localized semantic audit."
        ),
    }
    out["index_hash"] = stable_hash(out)
    return out
