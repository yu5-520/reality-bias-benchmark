import unittest

from arena.r5r6_r7_entry_audit import build_audit


class R5R6R7EntryAuditTest(unittest.TestCase):
    def test_all_entry_criteria_pass_for_bounded_r7_experiment(self):
        audit = build_audit()
        self.assertEqual(
            "PASS_R7_ENTRY_FULL_REQUIREMENT_COVERAGE",
            audit["decision"],
        )
        self.assertEqual(audit["criteria_total"], audit["criteria_passed"])
        self.assertTrue(audit["r7_entry_supported"])
        self.assertTrue(audit["framework_coverage_full"])
        self.assertEqual(audit["framework_requirement_count"], audit["framework_coverage_count"])
        self.assertFalse(audit["active_r7_repair_authorized"])
        self.assertTrue(audit["separate_manual_authorization_required"])
        self.assertEqual("NOT_ADJUDICATED", audit["semantic_cpr_status"])

    def test_audit_keeps_scientific_unknowns_open(self):
        audit = build_audit()
        unresolved = "\n".join(audit["unresolved_nonblocking_for_bounded_r7"])
        self.assertIn("first Structural Support", unresolved)
        self.assertIn("first Stable Shared Pool", unresolved)
        self.assertIn("J0-specific semantic inertia", unresolved)
        self.assertIn("Semantic CPR", unresolved)
        self.assertIn("R7 repair efficacy", unresolved)

    def test_r7_framework_covers_all_r5r6_requirements(self):
        audit = build_audit()
        coverage = {row["requirement"]: row["status"] for row in audit["framework_coverage"]}
        self.assertEqual("FULL", coverage["POOL_INVALIDATION"])
        self.assertEqual("FULL", coverage["DESCENDANT_INVALIDATION"])
        self.assertEqual("FULL", coverage["SELECTIVE_RECOMPUTE"])
        self.assertEqual("FULL", coverage["PRESERVE_UNRELATED_STRUCTURE"])
        self.assertEqual("FULL", coverage["OLD_LINEAGE_REENTRY_DETECTION"])

    def test_r7_is_supported_because_repair_question_is_not_already_answered(self):
        audit = build_audit()
        rows = {r["criterion"]: r for r in audit["criteria"]}
        self.assertEqual("PASS", rows["R7_RESEARCH_QUESTION_REMAINS_OPEN"]["status"])
        self.assertEqual(
            "NOT_YET_EXECUTED",
            rows["R7_RESEARCH_QUESTION_REMAINS_OPEN"]["evidence"]["repair_efficacy"],
        )


if __name__ == "__main__":
    unittest.main()
