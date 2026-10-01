"""Bounded inspection over an enhanced evidence graph."""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Iterable, Mapping


def inspect_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    nodes = list(graph.get("nodes") or [])
    edges = list(graph.get("edges") or [])
    statuses = defaultdict(int)
    for edge in edges:
        statuses[str(edge.get("status"))] += 1
    unresolved = sorted(
        node["ref"] for node in nodes if node.get("unresolved") is True
    )
    evidence_refs = {
        ref
        for node in nodes
        for ref in node.get("evidence_refs") or []
        if isinstance(ref, str) and ref
    }
    evidence_refs.update(
        ref
        for edge in edges
        for ref in edge.get("evidence_refs") or []
        if isinstance(ref, str) and ref
    )
    return {
        "schema": "RB-STAGE2-ENHANCED-GRAPH-INSPECTION-v1",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "edge_status_counts": dict(sorted(statuses.items())),
        "unresolved_node_refs": unresolved,
        "contradictions": list(graph.get("contradictions") or []),
        "evidence_ref_count": len(evidence_refs),
    }


def bounded_route(
    graph: Mapping[str, Any],
    seed_refs: Iterable[str],
    *,
    max_depth: int = 8,
    statuses: Iterable[str] = ("SUPPORTED", "CANDIDATE", "UNKNOWN"),
) -> dict[str, Any]:
    """Return a downstream route while preserving edge epistemic status."""
    if max_depth < 0:
        raise ValueError("max_depth must be non-negative")
    allowed = set(statuses)
    nodes = {node["ref"]: node for node in graph.get("nodes") or []}
    adjacency: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in graph.get("edges") or []:
        if edge.get("status") in allowed:
            adjacency[edge["source_ref"]].append(edge)
    seeds = list(dict.fromkeys(seed_refs))
    missing = sorted(ref for ref in seeds if ref not in nodes)
    if missing:
        raise ValueError("seed refs absent from graph: " + ",".join(missing))

    depth = {ref: 0 for ref in seeds}
    queue = deque(seeds)
    selected_edges: dict[str, dict[str, Any]] = {}
    while queue:
        source = queue.popleft()
        current_depth = depth[source]
        if current_depth >= max_depth:
            continue
        for edge in adjacency.get(source, []):
            selected_edges[edge["edge_id"]] = edge
            target = edge["destination_ref"]
            if target not in depth:
                depth[target] = current_depth + 1
                queue.append(target)

    selected_nodes = [nodes[ref] for ref in sorted(depth)]
    return {
        "schema": "RB-STAGE2-ENHANCED-BOUNDED-ROUTE-v1",
        "seed_refs": seeds,
        "max_depth": max_depth,
        "included_statuses": sorted(allowed),
        "nodes": selected_nodes,
        "edges": sorted(selected_edges.values(), key=lambda row: row["edge_id"]),
        "depth_by_ref": dict(sorted(depth.items())),
    }
