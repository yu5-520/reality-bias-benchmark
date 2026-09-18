import unittest

from arena.build_v5_whole_process_manifest import build_rows, verify_manifest
from arena.v5_whole_process_index import derive_v5_structural_index
from arena.v5_whole_process_preflight import _fixture_trace


class V5WholeProcessTest(unittest.TestCase):
    def test_manifest_is_three_natural_runs_and_non_authorizing(self):
        rows = build_rows(
            design_path="configs/v5_whole_process_ecommerce_batch001_v0.2.json",
            code_sha="TEST-COMMIT",
        )
        self.assertEqual(3, len(rows))
        self.assertTrue(verify_manifest(rows))
        self.assertTrue(all(r["subject_condition"] == "NATURAL_UNMANIPULATED" for r in rows))
        self.assertTrue(all(r["automatic_paid_evaluator"] is False for r in rows))

    def test_structural_index_preserves_mechanism_fields_but_centers_repair_anchor(self):
        out = derive_v5_structural_index(_fixture_trace())
        self.assertEqual("RB-V5-WHOLE-PROCESS-STRUCTURAL-INDEX-v0.2", out["schema"])
        self.assertEqual(
            "arena_event:0:state:inventory_assessment",
            out["engineering_core"]["first_repair_anchor_candidate_ref"],
        )
        self.assertGreaterEqual(out["engineering_core"]["content_address_count"], 1)
        self.assertGreaterEqual(out["engineering_core"]["pool_visibility_ledger_count"], 1)
        self.assertFalse(out["engineering_core"]["first_node_localization_required_for_repair"])
        self.assertFalse(out["mechanism_observables"]["engineering_requirement"])
        self.assertEqual(
            "arena_event:0:state:inventory_assessment",
            out["first_support_candidate_ref"],
        )
        self.assertEqual("NOT_ADJUDICATED", out["direct_pool_consumption_semantic_status"])
        self.assertTrue(out["candidates"][0]["content_address"])

    def test_visibility_is_not_promoted_to_semantic_consumption(self):
        out = derive_v5_structural_index(_fixture_trace())
        self.assertEqual(
            "STRUCTURAL_PROVENANCE_READY_SEMANTIC_AUDIT_REQUIRED",
            out["engineering_core"]["semantic_lineage_recoverability_status"],
        )
        self.assertEqual("NOT_ADJUDICATED", out["candidates"][0]["semantic_direct_consumption_status"])


if __name__ == "__main__":
    unittest.main()
