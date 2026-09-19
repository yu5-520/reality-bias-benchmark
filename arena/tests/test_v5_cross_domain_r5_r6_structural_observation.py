import json
import tempfile
import unittest
from pathlib import Path

from arena.derive_v5_cross_domain_r5_r6_structural_observation import _event_ref, _call_ref


class R5R6StructuralObservationTest(unittest.TestCase):
    def test_refs_are_source_bound(self):
        self.assertEqual("r:event:7", _event_ref("r", 7))
        self.assertEqual("r:turn:3:actor:a", _call_ref("r", 3, "a"))


if __name__ == "__main__":
    unittest.main()
