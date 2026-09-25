import copy
import unittest

from stage2.native_v7.policy import load_registry, validate_registry
from stage2.native_v7.subject_readiness import build_preflight


class Stage2SubjectReadinessGate(unittest.TestCase):
    SHA = "a" * 40

    def test_preflight_is_one_common_non_scientific_handshake(self):
        payload = build_preflight(
            expected_execution_sha=self.SHA,
            actual_execution_sha=self.SHA,
            authorization_phrase="CALL_REAL_STAGE2_SUBJECT_READINESS_API",
            max_subject_calls=1,
            spending_ceiling=0.01,
        )
        self.assertEqual(payload["status"], "READY_FOR_ONE_COMMON_PROVIDER_HANDSHAKE")
        self.assertEqual(payload["max_provider_calls"], 1)
        self.assertFalse(payload["automatic_paid_evaluator"])
        self.assertFalse(payload["scientific_task_used"])
        self.assertFalse(payload["natural_cell_reserved"])
        self.assertFalse(payload["registry_mutation_allowed"])
        self.assertEqual(
            payload["eligible_after_common_handshake"],
            ["X1", "X2", "X3", "X4", "X5"],
        )
        self.assertEqual(
            payload["asset_blockers"],
            {"X6": "PENDING_FROZEN_MANIFEST", "X7": "PENDING_FROZEN_MANIFEST"},
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
                    "subject_config_sha256": "s",
                    "model_config_sha256": "m",
                    "workflow_run_id": 1,
                }
                with self.assertRaisesRegex(ValueError, "frozen study"):
                    validate_registry(mutated)


if __name__ == "__main__":
    unittest.main()
