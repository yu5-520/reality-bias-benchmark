import unittest

from arena.r5r6_r7_entry_audit import build_audit


class R5R6R7EntryAuditTest(unittest.TestCase):
    def test_all_entry_criteria_pass_for_bounded_r7_experiment(self):
        audit = build_audit()
        self.assertEqual(
            "PASS_R7_ENTRY_BOUNDED_ENGINEERING_EXPERIMENT",
            audit["decision"],
        )
        self.assertEqual(audit["criteria_total"], audit["criteria_passed"])
        self.assertTrue(audit["r7_entry_supported"])
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
