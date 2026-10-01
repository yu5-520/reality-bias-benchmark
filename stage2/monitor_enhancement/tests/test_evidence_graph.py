import unittest

from stage2.monitor_enhancement.evidence_graph import EvidenceGraph
from stage2.monitor_enhancement.observation_adapter import (
    adapt_relation_evidence,
    adapt_structural_event,
)
from stage2.monitor_enhancement.route_export import export_route_map


class EnhancedEvidenceGraphTest(unittest.TestCase):
    def event(self):
        return {
            "sequence": 1,
            "event_ref": "G2-X4-T2:struct:000001",
            "actor": "coder",
            "kind": "ACTION_WRITE_FILE",
            "object_refs": ["file:a.py"],
            "written_refs": ["file:a.py"],
            "downstream_legal_refs": ["file:b.py"],
            "preserve_refs": ["file:c.py"],
        }

    def test_structural_adapter_does_not_infer_downstream_dependency(self):
        graph = EvidenceGraph()
        graph.add_observation(
            adapt_structural_event(
                self.event(),
                trajectory_id="G2-X4-T2",
                evidence_ref="raw:1",
            )
        )
        snapshot = graph.snapshot()
        pairs = {(e["source_ref"], e["destination_ref"]) for e in snapshot["edges"]}
        self.assertIn(("event:G2-X4-T2:struct:000001", "file:a.py"), pairs)
        self.assertNotIn(("file:a.py", "file:b.py"), pairs)
        self.assertTrue(snapshot["laws"]["temporal_proximity_is_not_dependency"])

    def test_relation_status_is_preserved_and_conflict_is_visible(self):
        graph = EvidenceGraph()
        supported = adapt_relation_evidence({
            "relation_id": "r1",
            "source_ref": "file:a.py",
            "destination_ref": "state:plan",
            "relation_type": "ADOPTED_AS_DECISION_PREMISE",
            "evidence_level": "ADOPTED_CARRIER",
            "evidence_refs": ["audit:1"],
            "semantic_scope_status": "IN_TARGET_LINEAGE",
            "semantic_use_status": "ADOPTED_AS_PREMISE",
        })
        rejected = dict(supported)
        rejected["relation_id"] = "r2"
        rejected["status"] = "REJECTED"
        rejected["basis"] = "SEMANTIC_REVIEW"
        graph.add_relation_evidence(supported)
        graph.add_relation_evidence(rejected)
        snapshot = graph.snapshot()
        self.assertEqual(len(snapshot["contradictions"]), 1)

    def test_route_map_separates_visibility_from_write_authority(self):
        graph = EvidenceGraph()
        graph.add_observation(
            adapt_structural_event(
                self.event(),
                trajectory_id="G2-X4-T2",
                evidence_ref="raw:1",
            )
        )
        graph.add_edge({
            "source_ref": "file:a.py",
            "destination_ref": "file:b.py",
            "relation_type": "PROPAGATED_TO_DESCENDANT",
            "status": "CANDIDATE",
            "basis": "SEMANTIC_CANDIDATE",
            "evidence_refs": ["audit:candidate:1"],
        })
        route = export_route_map(
            graph.snapshot(),
            ["file:a.py"],
            authorized_write_refs=["file:b.py"],
            preserve_refs=["file:c.py"],
        )
        self.assertIn("file:b.py", route["visible_refs"])
        self.assertEqual(route["authorized_write_refs"], ["file:b.py"])
        self.assertNotIn("file:b.py", route["supported_reachable_refs"])
        self.assertTrue(route["laws"]["graph_reachability_is_not_repair_eligibility"])


if __name__ == "__main__":
    unittest.main()
