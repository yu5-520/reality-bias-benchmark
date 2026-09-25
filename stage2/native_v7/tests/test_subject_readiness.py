import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stage2.native_v7.policy import load_registry, validate_registry
from stage2.native_v7.readiness_evidence import digest, execution_snapshot, verify_receipt, verify_study_manifest
from stage2.native_v7.subject_readiness import build_preflight


class Stage2SubjectReadinessGate(unittest.TestCase):
    SHA = "a" * 40

    def pending_registry(self):
        registry = copy.deepcopy(load_registry())
        registry["subject_readiness_gate"]["state"] = "IMPLEMENTED_NO_LIVE_RECEIPT"
        for pid in ("X1", "X2", "X3", "X4", "X5", "X6", "X7"):
            registry["probes"][pid]["collection_state"] = "NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING"
            registry["probes"][pid].pop("subject_readiness", None)
        registry["probes"]["X6"]["study_embedding"]["state"] = "PENDING_FROZEN_MANIFEST"
        registry["probes"]["X6"]["study_embedding"].pop("manifest_path", None)
        registry["probes"]["X6"]["study_embedding"].pop("manifest_sha256", None)
        registry["probes"]["X7"]["study_checkpoint"]["state"] = "PENDING_FROZEN_MANIFEST"
        registry["probes"]["X7"]["study_checkpoint"].pop("manifest_path", None)
        registry["probes"]["X7"]["study_checkpoint"].pop("manifest_sha256", None)
        return registry

    def test_preflight_is_one_common_non_scientific_handshake(self):
        with patch("stage2.native_v7.subject_readiness.load_registry", return_value=self.pending_registry()):
            payload = build_preflight(
            expected_execution_sha=self.SHA,
            actual_execution_sha=self.SHA,
            authorization_phrase="CALL_REAL_STAGE2_SUBJECT_READINESS_API",
            max_subject_calls=1,
            spending_ceiling=0.01,
            )
        self.assertEqual(payload["status"], "READY_FOR_ONE_COMMON_PROVIDER_HANDSHAKE")
        self.assertEqual(payload["execution_snapshot"], execution_snapshot())
        self.assertNotIn("stage2/native_v7/registry.json", payload["execution_snapshot"]["files_sha256"])
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
        with patch("stage2.native_v7.subject_readiness.load_registry", return_value=self.pending_registry()):
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

    def test_recorded_common_handshake_cannot_be_repeated(self):
        with self.assertRaisesRegex(ValueError, "already been recorded"):
            build_preflight(
                expected_execution_sha=self.SHA,
                actual_execution_sha=self.SHA,
                authorization_phrase="CALL_REAL_STAGE2_SUBJECT_READINESS_API",
                max_subject_calls=1,
                spending_ceiling=0.01,
            )

    def test_subject_ready_cannot_be_asserted_from_runner_smoke_alone(self):
        registry = load_registry()
        mutated = copy.deepcopy(registry)
        mutated["probes"]["X1"].pop("subject_readiness")
        mutated["probes"]["X1"]["collection_state"] = "SUBJECT_READY"
        with self.assertRaisesRegex(ValueError, "frozen readiness evidence"):
            validate_registry(mutated)

    def test_x6_x7_cannot_open_without_real_study_assets(self):
        registry = load_registry()
        for probe in ("X6", "X7"):
            with self.subTest(probe=probe):
                mutated = copy.deepcopy(registry)
                key = "study_embedding" if probe == "X6" else "study_checkpoint"
                mutated["probes"][probe][key]["state"] = "PENDING_FROZEN_MANIFEST"
                mutated["probes"][probe][key].pop("manifest_path", None)
                mutated["probes"][probe][key].pop("manifest_sha256", None)
                with self.assertRaisesRegex(ValueError, "frozen study"):
                    validate_registry(mutated)

    def test_receipt_must_exist_and_match_execution_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "stage2").mkdir()
            (root / "arena/config").mkdir(parents=True)
            (root / "stage2/subject.json").write_text("frozen subject")
            (root / "arena/config/model_deepseek_v0.2.json").write_text("frozen model")
            snapshot = {"files_sha256": {}, "fixture_tree_sha256": "f" * 64}
            receipt = {
                "schema": "stage2-subject-readiness-receipt-v1",
                "status": "COMMON_PROVIDER_HANDSHAKE_RECORDED_NOT_SUBJECT_READY",
                "provider": "deepseek", "provider_call_count": 1,
                "automatic_paid_evaluator": False, "scientific_task_used": False,
                "natural_cell_reserved": False, "registry_mutated": False,
                "natural_trajectories_after_handshake": 0,
                "promotion_required": "REVIEWED_REGISTRY_COMMIT",
                "execution_code_sha": "a" * 40, "workflow_run_id": 12,
                "observed_response_model": "provider-reported-model",
                "raw_response_sha256": "b" * 64,
                "subject_config_sha256": digest(root / "stage2/subject.json"),
                "model_config_sha256": digest(root / "arena/config/model_deepseek_v0.2.json"),
                "execution_snapshot": snapshot,
            }
            path = root / "receipt.json"
            path.write_text(json.dumps(receipt))
            registry = {"subject_readiness_gate": {
                "state": "COMMON_PROVIDER_HANDSHAKE_RECORDED",
                "receipt_path": "receipt.json", "receipt_sha256": digest(path),
            }}
            readiness = {key: receipt[key] for key in (
                "execution_code_sha", "workflow_run_id", "subject_config_sha256", "model_config_sha256"
            )}
            readiness["common_receipt_sha256"] = digest(path)
            with patch("stage2.native_v7.readiness_evidence.ROOT", root), patch(
                "stage2.native_v7.readiness_evidence.execution_snapshot", return_value=snapshot
            ):
                verify_receipt(registry, readiness)
                (root / "stage2/subject.json").write_text("changed subject")
                with self.assertRaisesRegex(ValueError, "subject binding changed"):
                    verify_receipt(registry, readiness)
                (root / "stage2/subject.json").write_text("frozen subject")
                path.write_text(json.dumps({**receipt, "provider_call_count": 2}))
                with self.assertRaisesRegex(ValueError, "frozen file"):
                    verify_receipt(registry, readiness)

    def test_x6_smoke_manifest_cannot_be_promoted_by_state_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "study.json"
            manifest.write_text(json.dumps({
                "schema": "stage2-x6-embedding-manifest-v1",
                "purpose": "NON_STUDY_ENGINEERING_SMOKE_ONLY",
                "files_sha256": {"model.bin": "a" * 64},
            }))
            spec = {"study_embedding": {"state": "FROZEN_MANIFEST_VERIFIED",
                       "manifest_path": "study.json", "manifest_sha256": digest(manifest)}}
            with patch("stage2.native_v7.readiness_evidence.ROOT", root):
                with self.assertRaisesRegex(ValueError, "engineering smoke asset"):
                    verify_study_manifest("X6", spec)


if __name__ == "__main__":
    unittest.main()
