import unittest

from arena.r5r6_engineering_package import build_package


class R5R6EngineeringPackageTest(unittest.TestCase):
    def test_frozen_sources_build_r7_entry_packet_without_authorizing_repair(self):
        bundle = build_package()
        summary = bundle["summary"]
        gate = bundle["lineage_completeness_gate"]
        packet = bundle["semantic_repair_packet"]

        self.assertEqual("READY_FOR_R7_SEPARATE_AUTHORIZATION", summary["status"])
        self.assertEqual("COMPLETE_FOR_AUTHORIZED_REPAIR", gate["status"])
        self.assertFalse(gate["automatic_repair_allowed"])
        self.assertEqual("READY_FOR_SEPARATE_AUTHORIZATION", packet["repair_authorization_status"])
        self.assertFalse(summary["active_repair_authorized"])
        self.assertEqual(0, summary["new_subject_provider_calls"])
        self.assertEqual(0, summary["new_paid_evaluator_calls"])
        self.assertFalse(summary["raw_evidence_mutated"])
        self.assertEqual("NOT_ADJUDICATED", summary["semantic_cpr_status"])

    def test_relation_layer_does_not_promote_anchor_to_semantic_origin(self):
        bundle = build_package()
        self.assertGreaterEqual(len(bundle["relation_evidence"]), 7)
        self.assertEqual(
            "arena_event:32:state:inventory_stockout_assessment_v1",
            bundle["semantic_lineage_closure"]["repair_anchor_ref"],
        )
        self.assertIn(
            "Exact first Stable Shared Pool entry remains NOT_ESTABLISHED.",
            bundle["semantic_repair_packet"]["unresolved_gaps"],
        )


if __name__ == "__main__":
    unittest.main()
