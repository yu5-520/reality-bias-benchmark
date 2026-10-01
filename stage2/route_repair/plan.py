"""Authority-bounded route-repair planning.

Diagnosis may use the visible route map. Mutation is limited to the intersection
between diagnosed nodes and the already-authorized task write scope.
"""
from __future__ import annotations

import copy
from typing import Any, Iterable, Mapping

from stage2.r7_checkpoint_v1.common import digest


def _native_surface_for(ref: str) -> str | None:
    if ref.startswith("file:"):
        return "NATIVE_APPLICATION_WRITE_OR_REVISION:" + ref
    if ref.startswith("message:"):
        return "NATIVE_MESSAGE_OR_TASK_SUPERSESSION:" + ref
    if ref.startswith("state:"):
        return "AUTHORIZED_PROCESS_STATE_REVISION:" + ref
    return None


def build_route_repair_plan(
    route_map: Mapping[str, Any],
    *,
    diagnosed_refs: Iterable[str],
    task_authorized_write_refs: Iterable[str],
    checkpoint_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    visible = set(route_map.get("visible_refs") or [])
    diagnosed = set(diagnosed_refs)
    if not diagnosed:
        raise ValueError("diagnosed_refs required")
    outside = diagnosed - visible
    if outside:
        raise ValueError("diagnosis outside visible route: " + ",".join(sorted(outside)))

    preserve = set(route_map.get("preserve_refs") or [])
    unknown = set(route_map.get("unknown_refs") or [])
    supported = set(route_map.get("supported_reachable_refs") or [])
    frozen_authorized = set(route_map.get("authorized_write_refs") or [])
    authorized = set(task_authorized_write_refs) & visible & frozen_authorized
    repairable = diagnosed & authorized & supported
    repairable -= preserve
    repairable -= unknown
    pending = diagnosed - repairable

    surfaces = sorted(
        surface
        for surface in (_native_surface_for(ref) for ref in repairable)
        if surface is not None
    )

    restore_capability = checkpoint_manifest.get("restore_capability")
    checkpoint_bound = bool(
        checkpoint_manifest.get("checkpoint_id")
        and checkpoint_manifest.get("checkpoint_hash")
    )
    if restore_capability != "FULL_NATIVE" or not checkpoint_bound:
        gate_status = "PARENT_RECONSTRUCTION_BLOCKED"
    elif not repairable:
        gate_status = "NO_AUTHORIZED_REPAIR_ROUTE"
    elif len(surfaces) != len(repairable):
        gate_status = "NATIVE_CAPABILITY_BLOCKED"
    else:
        gate_status = "COMPLETE_FOR_ROUTE_REPAIR"

    payload = {
        "schema": "RB-STAGE2-ROUTE-REPAIR-PLAN-v1",
        "route_map_hash": route_map.get("route_map_hash"),
        "parent_checkpoint_id": checkpoint_manifest.get("checkpoint_id"),
        "parent_checkpoint_hash": checkpoint_manifest.get("checkpoint_hash"),
        "parent_event_ref": checkpoint_manifest.get("event_ref"),
        "restore_capability": restore_capability,
        "visible_refs": sorted(visible),
        "diagnosed_refs": sorted(diagnosed),
        "task_authorized_write_refs": sorted(authorized),
        "supported_reachable_refs": sorted(supported),
        "repairable_refs": sorted(repairable),
        "pending_verification_refs": sorted(pending),
        "preserve_refs": sorted(preserve),
        "allowed_repair_surface": surfaces,
        "repair_gate_status": gate_status,
        "laws": {
            "history_is_immutable": True,
            "graph_reachability_does_not_grant_write_authority": True,
            "only_scope_intersection_is_repairable": True,
            "repair_executor_must_exit_before_post_repair_watch": True,
        },
    }
    payload["plan_hash"] = digest(payload)
    return payload


def validate_agent_route_choice(
    agent_choice: Mapping[str, Any],
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    if plan.get("schema") != "RB-STAGE2-ROUTE-REPAIR-PLAN-v1":
        raise ValueError("route repair plan schema invalid")
    if plan.get("plan_hash") != digest({k: v for k, v in plan.items() if k != "plan_hash"}):
        raise ValueError("route repair plan hash mismatch")

    modify = set(agent_choice.get("modify_refs") or [])
    preserve = set(agent_choice.get("preserve_refs") or [])
    verify = set(agent_choice.get("verify_refs") or [])
    repairable = set(plan.get("repairable_refs") or [])
    visible = set(plan.get("visible_refs") or [])
    frozen_preserve = set(plan.get("preserve_refs") or [])

    if not modify:
        raise ValueError("agent route choice requires modify_refs")
    if not modify <= repairable:
        raise ValueError("agent attempted modification outside repairable route")
    if preserve != frozen_preserve:
        raise ValueError("agent preserve set must equal frozen preserve set")
    if not verify <= visible:
        raise ValueError("agent verification target outside visible route")
    if modify & verify:
        raise ValueError("modify_refs and verify_refs must be disjoint")

    row = {
        "schema": "RB-STAGE2-AGENT-ROUTE-CHOICE-v1",
        "plan_hash": plan["plan_hash"],
        "modify_refs": sorted(modify),
        "preserve_refs": sorted(preserve),
        "verify_refs": sorted(verify),
        "reason_by_ref": copy.deepcopy(dict(agent_choice.get("reason_by_ref") or {})),
    }
    row["choice_hash"] = digest(row)
    return row


def build_boundary_package(plan: Mapping[str, Any]) -> dict[str, Any]:
    if plan.get("repair_gate_status") != "COMPLETE_FOR_ROUTE_REPAIR":
        raise ValueError("route plan is not repair eligible")
    package = {
        "schema": "RB-STAGE2-ROUTE-REPAIR-BOUNDARY-PACKAGE-v1",
        "package_id": "route:" + str(plan["plan_hash"])[:24],
        "source_cell": "ROUTE_REPAIR",
        "prefix_cutoff_ref": plan.get("parent_event_ref"),
        "repair_anchor_ref": plan.get("parent_event_ref"),
        "affected_closure_refs": list(plan.get("repairable_refs") or []),
        "preserve_refs": list(plan.get("preserve_refs") or []),
        "allowed_repair_surface": list(plan.get("allowed_repair_surface") or []),
        "native_capability_requirements": list(plan.get("allowed_repair_surface") or []),
        "repair_gate_status": "COMPLETE_FOR_STRUCTURED_REPAIR",
        "route_plan_hash": plan["plan_hash"],
    }
    package["package_hash"] = digest(package)
    return package
