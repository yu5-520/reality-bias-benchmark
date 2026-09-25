import copy
import unittest

from stage2.native_v7.policy import load_registry, validate_registry
from stage2.native_v7.subject_readiness import build_preflight


class Stage2SubjectReadinessGate(unittest.TestCase):
    SHA = "a" * 40

    def test_recorded_common_handshake_blocks_a_second_paid_preflight(self):
        registry = load_registry()
        gate = registry["subject_readiness_gate"]
        self.assertEqual(gate["state"], "COMMON_PROVIDER_HANDSHAKE_RECORDED")
        self.assertEqual(gate["live_receipt"]["workflow_run_id"], 36145131256)
        self.assertEqual(
            gate["live_receipt"]["receipt_sha256"],
            "93f06cb677b7da3997bcbf38a09cdd10fed650f2e05139e4ac82645a23228464",
        )
        with self.assertRaisesRegex(ValueError, "second paid readiness call is forbidden"):
            build_preflight(
                expected_execution_sha=self.SHA,
                actual_execution_sha=self.SHA,
                authorization_phrase="CALL_REAL_STAGE2_SUBJECT_READINESS_API",
                max_subject_calls=1,
                spending_ceiling=0.01,
            )

    def test_preflight_rejects_nonexact_authorization(self):
        with self.assertRaisesRegex(ValueError, "authorization phrase"):
            build_preflight(
                expected_execution_sha=self.SHA,
                actual_execution_sha=self.SHA,
                authorization_phrase="CALL_REAL_STAGE2_API",
                max_subject_calls=1,
                spending_ceiling=0.01,
            )

    def test_preflight_rejects_sha_drift(self):
        with self.assertRaisesRegex(ValueError, "exact explicitly frozen execution SHA"):
            build_preflight(
                expected_execution_sha=self.SHA,
                actual_execution_sha="b" * 40,
                authorization_phrase="CALL_REAL_STAGE2_SUBJECT_READINESS_API",
                max_subject_calls=1,
                spending_ceiling=0.01,
            )

    def test_preflight_rejects_extra_calls_or_large_budget(self):
        with self.assertRaisesRegex(ValueError, "exactly one provider call"):
            build_preflight(
                expected_execution_sha=self.SHA,
                actual_execution_sha=self.SHA,
                authorization_phrase="CALL_REAL_STAGE2_SUBJECT_READINESS_API",
                max_subject_calls=2,
                spending_ceiling=0.01,
            )
        with self.assertRaisesRegex(ValueError, "spending ceiling"):
            build_preflight(
                expected_execution_sha=self.SHA,
                actual_execution_sha=self.SHA,
                authorization_phrase="CALL_REAL_STAGE2_SUBJECT_READINESS_API",
                max_subject_calls=1,
                spending_ceiling=0.06,
            )

    def test_subject_ready_cannot_be_asserted_from_runner_smoke_alone(self):
        registry = load_registry()
        mutated = copy.deepcopy(registry)
        mutated["probes"]["X1"]["collection_state"] = "SUBJECT_READY"
        with self.assertRaisesRegex(ValueError, "frozen readiness evidence"):
            validate_registry(mutated)

    def test_x6_x7_cannot_open_without_real_study_assets(self):
        registry = load_registry()
        for probe in ("X6", "X7"):
            with self.subTest(probe=probe):
                mutated = copy.deepcopy(registry)
                mutated["probes"][probe]["collection_state"] = "SUBJECT_READY"
                mutated["probes"][probe]["subject_readiness"] = {
                    "state": "VERIFIED",
                    "execution_code_sha": self.SHA,
                    "common_receipt_sha256": "r",
                    "execution_surface_sha256": "e",
                    "subject_config_sha256": "s",
                    "model_config_sha256": "m",
                    "workflow_run_id": 1,
                }
                with self.assertRaisesRegex(ValueError, "frozen study"):
                    validate_registry(mutated)


if __name__ == "__main__":
    unittest.main()
