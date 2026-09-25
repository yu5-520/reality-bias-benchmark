import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from stage2.evidence import NativeCapture, check_capture
from stage2.freeze import artifact
from stage2.preflight import blockers

BASE = Path(__file__).resolve().parents[1]


class RuntimeGateContractTests(unittest.TestCase):
    def test_runtime_lock_has_exact_seven_probes(self):
        lock = json.loads((BASE / "runtime_lock.json").read_text())
        self.assertEqual([row["id"] for row in lock["probes"]], [f"X{i}" for i in range(1, 8)])
        self.assertTrue(all(row.get("native_hook") for row in lock["probes"]))
        self.assertEqual(lock["status"], "ENGINEERING_SMOKE_AUTHORIZED_NO_SUBJECT_CALLS")

    def test_subject_lock_is_bound_but_not_authorized(self):
        lock = json.loads((BASE / "subject_lock.json").read_text())
        self.assertEqual(lock["provider"], "deepseek")
        self.assertEqual(lock["model_alias"], "deepseek-flash")
        self.assertFalse(lock["provider_execution_authorized"])
        self.assertFalse(lock["evaluator_execution_authorized"])
        limits = lock["limits"]
        self.assertEqual(
            limits["max_provider_calls_first_group"],
            limits["planned_natural_trajectories"] * limits["max_provider_calls_per_trajectory"],
        )
        self.assertEqual(limits["identical_prompt_retries_for_scientific_result"], 0)

    def test_content_addressed_probe_does_not_need_fake_source_commit(self):
        binding = {
            "probe": "X5",
            "source_commit": None,
            "implementation_sha256": "a" * 64,
            "native_hook": "stage2.retrieval.retrieve",
        }
        with tempfile.TemporaryDirectory() as tmp:
            cap = NativeCapture(tmp, "X5", "test-x5", binding)
            cap.capture(
                event_id="retrieve",
                operation="retrieve",
                phase="returned",
                native_locator="stage2.retrieval.retrieve",
                hook_id=binding["native_hook"],
                raw=b"native retrieval result",
                actor="release_lead",
                target="retrieval-index",
                carrier_id="hits",
                source_id="query",
                status="success",
            )
            cap.capture(
                event_id="stop",
                operation="termination",
                phase="returned",
                native_locator="test",
                hook_id=binding["native_hook"],
                raw=b"done",
                actor="gate",
                target=None,
                carrier_id="stop",
                source_id="query",
                parent_ids=("retrieve",),
                status="success",
            )
            self.assertEqual(check_capture(tmp), 2)


    def test_explicit_engineering_blockers_can_close_cells_without_fake_smoke(self):
        subject = json.loads((BASE / "subject_lock.json").read_text())
        planned = artifact()
        runtime = {
            "runtime_lock_sha256": hashlib.sha256((BASE / "runtime_lock.json").read_bytes()).hexdigest(),
            "subject_lock_sha256": hashlib.sha256((BASE / "subject_lock.json").read_bytes()).hexdigest(),
            "matrix_sha256": hashlib.sha256((BASE / "matrix.json").read_bytes()).hexdigest(),
            "subject_provider": subject["provider"],
            "subject_model": subject["model_alias"],
            "subject_limits": subject["limits"],
            "code_commit": "test-code-sha",
            "roles_sha256": planned["files_sha256"]["stage2/roles.json"],
            "probes": {
                f"X{i}": {
                    "execution_status": "ENGINEERING_BLOCKED",
                    "blocker_reason": "test blocker",
                }
                for i in range(1, 8)
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "runtime.json"
            captures = Path(tmp) / "captures"
            captures.mkdir()
            manifest.write_text(json.dumps(runtime))
            self.assertEqual(blockers(manifest, captures), [])

if __name__ == "__main__":
    unittest.main()
