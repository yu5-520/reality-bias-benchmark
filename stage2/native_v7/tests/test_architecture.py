import json
import tempfile
import unittest
from pathlib import Path

from stage2.native_v7.collect import validate_request
from stage2.native_v7.freeze import artifact
from stage2.native_v7.observer import PassiveEventObserver, verify_observer
from stage2.native_v7.policy import load_registry, validate_registry


ROOT = Path(__file__).resolve().parents[3]


class NativeV7Architecture(unittest.TestCase):
    def test_registry_is_heterogeneous_and_external(self):
        registry = load_registry()
        self.assertEqual(set(registry["probes"]), {f"X{i}" for i in range(1, 8)})
        self.assertEqual(
            len({spec["environment_id"] for spec in registry["probes"].values()}), 7
        )
        for spec in registry["probes"].values():
            self.assertEqual(spec["runtime_scope"], "independent")
            self.assertEqual(spec["observer"]["mode"], "external")
            self.assertFalse(spec["observer"]["may_mutate_execution"])

    def test_probe_specs_contain_no_v6_shared_execution_contract(self):
        registry = load_registry()
        for pid, spec in registry["probes"].items():
            raw = json.dumps(spec, sort_keys=True)
            for marker in ("CodingArena", "RoleMailboxTransport", "context_adapter", "available_actions"):
                with self.subTest(probe=pid, marker=marker):
                    self.assertNotIn(marker, raw)

    def test_all_cells_closed_before_verified_native_runners(self):
        matrix = artifact()
        self.assertEqual(len(matrix["cells"]), 21)
        self.assertEqual({row["subject_trajectory_count"] for row in matrix["cells"]}, {0})
        self.assertEqual({row["status"] for row in matrix["cells"]}, {"PENDING_NATIVE_RUNNER"})
        for probe in (f"X{i}" for i in range(1, 8)):
            with self.subTest(probe=probe), self.assertRaisesRegex(
                ValueError, "native runner is not verified"
            ):
                validate_request(probe, "T1")

    def test_pending_runner_cannot_smuggle_launch_command(self):
        registry = load_registry()
        registry["probes"]["X1"]["launch"]["argv_template"] = ["python", "anything.py"]
        with self.assertRaisesRegex(ValueError, "pending runner"):
            validate_registry(registry)

    def test_verified_state_requires_explicit_native_entrypoint(self):
        registry = load_registry()
        registry["probes"]["X1"]["collection_state"] = "RUNNER_VERIFIED"
        with self.assertRaisesRegex(ValueError, "verified runner lacks"):
            validate_registry(registry)

    def test_x1_candidate_source_does_not_import_v6_execution_scaffold(self):
        raw = (ROOT / "stage2/native_v7/x1_autogen/runner.py").read_text()
        for marker in ("stage2.coding_arena", "RoleMailboxTransport", "context_adapter"):
            self.assertNotIn(marker, raw)

    def test_passive_event_observer_returns_identical_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            observer = PassiveEventObserver(Path(directory) / "observer", probe="X1")
            raw = b'{"native":"event"}'
            returned = observer.observe(raw, surface="unit-test")
            self.assertIs(returned, raw)
            observer.seal()
            self.assertGreaterEqual(verify_observer(observer.root), 2)


if __name__ == "__main__":
    unittest.main()
