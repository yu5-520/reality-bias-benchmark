"""Append to a sealed enhanced graph without changing its historical records.

This extension preserves the exact source implementation used for the frozen
P2 replay. Existing captures and edge identities are loaded, not reconstructed.
"""
import copy
from typing import Any, Mapping
from stage2.monitor_enhancement.evidence_graph import EvidenceGraph, EvidenceGraphError
from stage2.r7_checkpoint_v1.common import digest


class AppendOnlyEvidenceGraph(EvidenceGraph):
    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, Any]) -> "AppendOnlyEvidenceGraph":
        payload = copy.deepcopy(dict(snapshot))
        claimed = payload.pop("graph_hash", None)
        if claimed != digest(payload) or payload.get("schema") != cls.SCHEMA:
            raise EvidenceGraphError("snapshot schema or hash invalid")
        graph = cls()
        graph._nodes = {row["ref"]: copy.deepcopy(row) for row in payload["nodes"]}
        graph._observations = {row["observation_id"]: copy.deepcopy(row) for row in payload["observations"]}
        graph._edges = copy.deepcopy(payload["edges"])
        graph._edge_ids = {row["edge_id"] for row in graph._edges}
        graph._edge_by_id = {row["edge_id"]: row for row in graph._edges}
        if (len(graph._nodes) != len(payload["nodes"])
                or len(graph._observations) != len(payload["observations"])
                or len(graph._edge_ids) != len(graph._edges)):
            raise EvidenceGraphError("duplicate snapshot identities")
        if graph.snapshot() != snapshot:
            raise EvidenceGraphError("snapshot canonical structure invalid")
        return graph
