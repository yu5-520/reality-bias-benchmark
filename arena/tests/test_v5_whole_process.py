import unittest

from arena.build_v5_whole_process_manifest import build_rows, verify_manifest
from arena.v5_whole_process_index import derive_v5_structural_index
from arena.v5_whole_process_preflight import _fixture_trace


class V5WholeProcessTest(unittest.TestCase):
    def test_manifest_is_three_natural_runs_and_non_authorizing(self):
        rows = build_rows(
            design_path="configs/v5_whole_process_ecommerce_batch001_v0.1.json",
            code_sha="TEST-COMMIT",
        )
        self.assertEqual(3, len(rows))
        self.assertTrue(verify_manifest(rows))
        self.assertTrue(all(r["subject_condition"] == "NATURAL_UNMANIPULATED" for r in rows))
        self.assertTrue(all(r["automatic_paid_evaluator"] is False for r in rows))

    def test_structural_index_separates_visibility_from_semantic_consumption(self):
        out = derive_v5_structural_index(_fixture_trace())
        self.assertEqual(
            "arena_event:0:state:inventory_assessment",
            out["first_support_candidate_ref"],
        )
        self.assertEqual(
            "arena_event:0:state:inventory_assessment",
            out["first_pool_candidate_ref"],
        )
        self.assertEqual(
            "arena_event:0:state:inventory_assessment",
            out["first_exposure_candidate_ref"],
        )
        self.assertEqual("NOT_ADJUDICATED", out["direct_pool_consumption_semantic_status"])


if __name__ == "__main__":
    unittest.main()
