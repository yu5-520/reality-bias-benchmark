import json, unittest
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]

class RuntimeBindingTests(unittest.TestCase):
    def test_subject_profile_is_frozen_and_bounded(self):
        s=json.loads((BASE/"subject.json").read_text())
        self.assertEqual(s["provider"],"deepseek")
        self.assertEqual(s["model_alias"],"deepseek-flash")
        self.assertEqual(s["expected_model_version"],"DeepSeek-V4.1-Flash")
        self.assertEqual(s["limits"]["max_turns"],32)
        self.assertEqual(s["limits"]["max_total_model_invocations"],64)
        self.assertFalse(s["limits"]["automatic_paid_evaluator"])
        self.assertTrue(s["limits"]["one_natural_trajectory_per_cell"])

    def test_all_seven_targets_locked(self):
        b=json.loads((BASE/"runtime_bindings.json").read_text())
        self.assertEqual(set(b["probes"]),{f"X{i}" for i in range(1,8)})
        self.assertTrue(all(p["state"] in {"TARGET_LOCKED","IMPLEMENTATION_LOCKED","ENGINEERING_BLOCKED"} for p in b["probes"].values()))
        self.assertEqual(b["probes"]["X3"]["protocol_version"],"1.0.0")
        self.assertEqual(b["probes"]["X4"]["protocol_version"],"2026-07-28")
        self.assertEqual(b["probes"]["X2"]["state"],"ENGINEERING_BLOCKED")
        self.assertIn("lancedb==0.4.0",b["probes"]["X2"]["block_reason"])
        self.assertNotEqual(b["probes"]["X3"]["protocol_commit"],b["probes"]["X3"]["sdk_commit"])
        self.assertNotEqual(b["probes"]["X4"]["protocol_commit"],b["probes"]["X4"]["sdk_commit"])

    def test_target_lock_does_not_claim_native_smoke(self):
        b=json.loads((BASE/"runtime_bindings.json").read_text())
        self.assertEqual(b["status"],"TARGETS_LOCKED_WITH_ENGINEERING_BLOCK_NATIVE_SMOKE_PENDING")
        for p in b["probes"].values():
            self.assertNotIn("NATIVE_SMOKE_PASS",p.values())

if __name__=="__main__":
    unittest.main()
