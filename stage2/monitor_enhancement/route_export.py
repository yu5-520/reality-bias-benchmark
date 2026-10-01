"""Route-map export that keeps observation, diagnosis and write scope separate."""
from __future__ import annotations

import copy
from typing import Any, Iterable, Mapping

from stage2.monitor_enhancement.inspection import bounded_route
from stage2.r7_checkpoint_v1.common import digest


def _node_capability(ref: str, authorized: set[str], preserve: set[str], unresolved: bool) -> str:
    if ref in preserve:
        return "PRESERVE"
    if unresolved:
        return "OBSERVE_ONLY_UNRESOLVED"
    if ref in authorized:
        return "AUTHORIZED_WRITE_CANDIDATE"
    return "OBSERVE_ONLY"


def export_route_map(
    graph: Mapping[str, Any],
    seed_refs: Iterable[str],
    *,
    authorized_write_refs: Iterable[str] = (),
    preserve_refs: Iterable[str] = (),
    max_depth: int = 8,
) -> dict[str, Any]:
    route = bounded_route(graph, seed_refs, max_depth=max_depth)
    supported_route = bounded_route(
        graph, seed_refs, max_depth=max_depth, statuses=("SUPPORTED",)
    )
    authorized = set(authorized_write_refs)
    preserve = set(preserve_refs)
    visible = {node["ref"] for node in route["nodes"]}
    supported = {node["ref"] for node in supported_route["nodes"]}

    nodes = []
    for node in route["nodes"]:
        row = copy.deepcopy(node)
        capability = _node_capability(
            row["ref"], authorized, preserve, bool(row.get("unresolved"))
        )
        if capability == "AUTHORIZED_WRITE_CANDIDATE" and row["ref"] not in supported:
            capability = "VERIFY_BEFORE_WRITE"
        row["route_capability"] = capability
        row["supported_reachable"] = row["ref"] in supported
        nodes.append(row)

    payload = {
        "schema": "RB-STAGE2-ENHANCED-ROUTE-MAP-v1",
        "graph_hash": graph.get("graph_hash"),
        "seed_refs": list(route["seed_refs"]),
        "nodes": nodes,
        "edges": list(route["edges"]),
        "depth_by_ref": dict(route["depth_by_ref"]),
        "visible_refs": sorted(visible),
        "authorized_write_refs": sorted(visible & authorized),
        "supported_reachable_refs": sorted(supported),
        "preserve_refs": sorted(preserve),
        "visible_preserve_refs": sorted(visible & preserve),
        "out_of_route_preserve_refs": sorted(preserve - visible),
        "unknown_refs": sorted(
            node["ref"] for node in nodes if node.get("unresolved") is True
        ),
        "laws": {
            "observation_authority_is_not_mutation_authority": True,
            "graph_reachability_is_not_repair_eligibility": True,
            "diagnosis_precedes_scope_intersection": True,
        },
    }
    payload["route_map_hash"] = digest(payload)
    return payload


def render_route_text(route_map: Mapping[str, Any]) -> str:
    lines = [
        f"route_map={route_map.get('route_map_hash')}",
        "OBSERVATION AUTHORITY != MUTATION AUTHORITY",
    ]
    depth = route_map.get("depth_by_ref") or {}
    for node in sorted(route_map.get("nodes") or [], key=lambda row: (depth.get(row["ref"], 0), row["ref"])):
        lines.append(
            f"[{depth.get(node['ref'], '?')}] {node['ref']} :: {node.get('route_capability')}"
        )
    for edge in route_map.get("edges") or []:
        lines.append(
            f"{edge['source_ref']} -[{edge['relation_type']}|{edge['status']}]-> {edge['destination_ref']}"
        )
    return "\n".join(lines) + "\n"
