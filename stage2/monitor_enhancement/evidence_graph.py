"""Evidence graph for externally observed Stage-II process evidence."""
from __future__ import annotations

import copy
from collections import defaultdict
from typing import Any, Iterable, Mapping

from stage2.r7_checkpoint_v1.common import digest


EDGE_STATUSES = {"SUPPORTED", "CANDIDATE", "UNKNOWN", "REJECTED"}


class EvidenceGraphError(ValueError):
    pass


def _blank_node(ref: str, node_type: str) -> dict[str, Any]:
    return {
        "ref": ref,
        "node_type": node_type,
        "observation_ids": [],
        "event_refs": [],
        "evidence_refs": [],
        "sequences": [],
        "versions": [],
        "content_hashes": [],
        "actors": [],
        "field_paths": [],
        "visibility_scopes": [],
        "unresolved": node_type == "UNRESOLVED_REF",
    }


def _append_unique(row: dict[str, Any], field: str, value: Any) -> None:
    if value is None:
        return
    values = row[field]
    if value not in values:
        values.append(value)


class EvidenceGraph:
    """Append-only derived graph over frozen evidence.

    Graph reachability is informational only. The graph never grants write
    authority and never treats temporal adjacency as a dependency.
    """

    SCHEMA = "RB-STAGE2-ENHANCED-EVIDENCE-GRAPH-v1"

    def __init__(self):
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: list[dict[str, Any]] = []
        self._edge_ids: set[str] = set()
        self._observations = {}
        self._edge_by_id = {}

    def _node(self, ref: str, node_type: str = "UNRESOLVED_REF") -> dict[str, Any]:
        if not isinstance(ref, str) or not ref:
            raise EvidenceGraphError("node ref required")
        row = self._nodes.get(ref)
        if row is None:
            row = _blank_node(ref, node_type)
            self._nodes[ref] = row
        elif row["node_type"] == "UNRESOLVED_REF" and node_type != "UNRESOLVED_REF":
            row["node_type"] = node_type
            row["unresolved"] = False
        return row

    def add_observation(self, observation: Mapping[str, Any]) -> None:
        row = copy.deepcopy(dict(observation))
        if row.get("schema") != "RB-STAGE2-ENHANCED-OBSERVATION-v1":
            raise EvidenceGraphError("observation schema invalid")
        observation_id = row.get("observation_id") or "obs:" + digest(row)
        row["observation_id"] = observation_id
        if observation_id in self._observations:
            if self._observations[observation_id] != row:
                raise EvidenceGraphError("observation identity rebound")
            return
        self._observations[observation_id] = row
        event_ref = row.get("event_ref")
        event_node = self._node("event:" + str(event_ref), "EVENT")
        for field, value in (
            ("observation_ids", observation_id),
            ("event_refs", event_ref),
            ("evidence_refs", row.get("evidence_ref")),
            ("sequences", row.get("native_sequence")),
            ("versions", row.get("version")),
            ("actors", row.get("actor")),
            ("visibility_scopes", row.get("visibility_scope")),
        ):
            _append_unique(event_node, field, value)

        written = set(row.get("written_refs") or [])
        for ref in row.get("object_refs") or []:
            node = self._node(ref, "OBSERVED_OBJECT")
            for field, value in (
                ("observation_ids", observation_id),
            ("event_refs", event_ref),
                ("evidence_refs", row.get("evidence_ref")),
                ("sequences", row.get("native_sequence")),
                ("versions", row.get("version")),
                ("content_hashes", row.get("content_hash")),
                ("actors", row.get("actor")),
                ("field_paths", row.get("field_path")),
                ("visibility_scopes", row.get("visibility_scope")),
            ):
                _append_unique(node, field, value)
            relation_type = row.get("object_relation") or (
                "EVENT_WRITES_OBJECT" if ref in written else "EVENT_OBSERVES_OBJECT"
            )
            self.add_edge(
                {
                    "source_ref": "event:" + str(event_ref),
                    "destination_ref": ref,
                    "relation_type": relation_type,
                    "status": "SUPPORTED",
                    "basis": "DIRECT_RUNTIME_RECORD",
                    "evidence_refs": [row["evidence_ref"]],
                }
            )
            # Reverse provenance is a query edge, not a causal edge.
            self.add_edge(
                {
                    "source_ref": ref,
                    "destination_ref": "event:" + str(event_ref),
                    "relation_type": "OBJECT_EVIDENCED_BY_EVENT",
                    "status": "SUPPORTED",
                    "basis": "DIRECT_RUNTIME_RECORD_REVERSE_INDEX",
                    "evidence_refs": [row["evidence_ref"]],
                }
            )

    def add_edge(self, relation: Mapping[str, Any]) -> dict[str, Any]:
        row = copy.deepcopy(dict(relation))
        for field in ("source_ref", "destination_ref", "relation_type"):
            if not isinstance(row.get(field), str) or not row[field]:
                raise EvidenceGraphError(f"{field} required")
        status = row.get("status")
        if status not in EDGE_STATUSES:
            raise EvidenceGraphError("invalid edge status")
        evidence_refs = row.get("evidence_refs")
        if not isinstance(evidence_refs, list):
            raise EvidenceGraphError("evidence_refs must be list[str]")
        if status == "SUPPORTED" and not evidence_refs:
            raise EvidenceGraphError("supported edge requires evidence")
        if any(not isinstance(item, str) or not item for item in evidence_refs):
            raise EvidenceGraphError("evidence_refs must contain non-empty strings")

        self._node(row["source_ref"])
        self._node(row["destination_ref"])
        material = {
            "source_ref": row["source_ref"],
            "destination_ref": row["destination_ref"],
            "relation_type": row["relation_type"],
            "status": status,
            "basis": row.get("basis", "UNSPECIFIED"),
            "evidence_refs": sorted(set(evidence_refs)),
            "semantic_scope_status": row.get("semantic_scope_status", "UNRESOLVED"),
            "semantic_use_status": row.get("semantic_use_status", "UNRESOLVED"),
            "judgment_version": row.get("judgment_version"),
        }
        edge_id = row.get("relation_id") or "edge:" + digest(material)[:24]
        if edge_id in self._edge_ids:
            return copy.deepcopy(self._edge_by_id[edge_id])
        edge = {"edge_id": edge_id, **material}
        self._edges.append(edge)
        self._edge_ids.add(edge_id)
        self._edge_by_id[edge_id] = edge
        return copy.deepcopy(edge)

    def add_relation_evidence(self, relation: Mapping[str, Any]) -> dict[str, Any]:
        if relation.get("schema") != "RB-STAGE2-ENHANCED-RELATION-v1":
            raise EvidenceGraphError("enhanced relation schema invalid")
        return self.add_edge(relation)

    @property
    def nodes(self) -> dict[str, dict[str, Any]]:
        return copy.deepcopy(self._nodes)

    @property
    def edges(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._edges)

    def contradictions(self) -> list[dict[str, Any]]:
        grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for edge in self._edges:
            grouped[
                (edge["source_ref"], edge["relation_type"], edge["destination_ref"])
            ].append(edge)
        result = []
        for identity, edges in sorted(grouped.items()):
            statuses = {edge["status"] for edge in edges}
            if "SUPPORTED" in statuses and "REJECTED" in statuses:
                result.append(
                    {
                        "source_ref": identity[0],
                        "relation_type": identity[1],
                        "destination_ref": identity[2],
                        "edge_ids": sorted(edge["edge_id"] for edge in edges),
                        "statuses": sorted(statuses),
                    }
                )
        return result

    def snapshot(self) -> dict[str, Any]:
        nodes = []
        for ref in sorted(self._nodes):
            row = copy.deepcopy(self._nodes[ref])
            for field in (
                "observation_ids",
                "event_refs",
                "evidence_refs",
                "sequences",
                "versions",
                "content_hashes",
                "actors",
                "field_paths",
                "visibility_scopes",
            ):
                row[field] = sorted(row[field]) if field == "sequences" else sorted(row[field], key=str)
            nodes.append(row)
        edges = sorted(
            copy.deepcopy(self._edges),
            key=lambda item: (
                item["source_ref"],
                item["relation_type"],
                item["destination_ref"],
                item["edge_id"],
            ),
        )
        payload = {
            "schema": self.SCHEMA,
            "observations": [copy.deepcopy(self._observations[k]) for k in sorted(self._observations)],
            "nodes": nodes,
            "edges": edges,
            "contradictions": self.contradictions(),
            "laws": {
                "temporal_proximity_is_not_dependency": True,
                "graph_reachability_is_not_mutation_authority": True,
                "observation_authority_is_not_mutation_authority": True,
            },
        }
        payload["graph_hash"] = digest(payload)
        return payload


def build_graph(
    observations: Iterable[Mapping[str, Any]],
    relations: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    graph = EvidenceGraph()
    for observation in observations:
        graph.add_observation(observation)
    for relation in relations:
        graph.add_relation_evidence(relation)
    return graph.snapshot()
