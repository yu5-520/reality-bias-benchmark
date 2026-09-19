import json
import unittest

from arena.run_v5_cross_domain_r5_coverage_extension import _validate_budget


class CrossDomainR5CoverageExtensionTest(unittest.TestCase):
    def test_frozen_coverage_is_exact_remaining_23(self):
        audit=json.load(open("manifests/v5_cross_domain_localized_semantic_audit_review_2026-09-19_v0_1.json"))
        first=json.load(open("configs/v5_cross_domain_r5_first_wave_v0.1.json"))
        coverage=json.load(open("configs/v5_cross_domain_r5_coverage_extension_v0.1.json"))
        all_hashes=set(audit["reviewed_case_hashes"])
        first_hashes={x["source_case_hash"] for x in first["selected_cases"]}
        coverage_hashes=set(coverage["selected_case_hashes"])
        self.assertEqual(29,len(all_hashes))
        self.assertEqual(6,len(first_hashes))
        self.assertEqual(23,len(coverage_hashes))
        self.assertFalse(first_hashes & coverage_hashes)
        self.assertEqual(all_hashes,first_hashes | coverage_hashes)

    def test_geometry_and_budget(self):
        cfg=json.load(open("configs/v5_cross_domain_r5_coverage_extension_v0.1.json"))
        self.assertEqual(23,cfg["geometry"]["case_count"])
        self.assertEqual(46,cfg["geometry"]["total_branch_count"])
        self.assertEqual({"finance":3,"supply_chain":14,"software_engineering":6},cfg["domain_counts"])
        self.assertIsNone(_validate_budget(46,64,0.25,11.50))
        with self.assertRaises(ValueError):
            _validate_budget(46,64,0.25,11.49)


if __name__=="__main__":
    unittest.main()
