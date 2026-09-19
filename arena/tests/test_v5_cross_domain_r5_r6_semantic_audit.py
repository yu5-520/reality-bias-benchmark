import json
import unittest

from arena.build_v5_cross_domain_r5_r6_semantic_audit import _evidence_refs


class R5R6SemanticAuditTest(unittest.TestCase):
    def test_evidence_refs_include_direct_and_downstream(self):
        row = {
            "direct_exposure": {"call_ref": "call:0"},
            "direct_turn_carrier_candidates": [{"ref": "event:1"}],
            "downstream_structural_observations": [
                {
                    "call_ref": "call:2",
                    "visible_direct_carrier_refs": ["event:1"],
                    "downstream_write_refs": ["event:3"],
                }
            ],
        }
        self.assertEqual(["call:0","event:1","call:2","event:3"], _evidence_refs(row))


if __name__ == "__main__":
    unittest.main()
