import json
import importlib.util
import tempfile
import unittest
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

from stage2.evidence import NativeCapture, check_capture, PROBES
from stage2.freeze import BASE, artifact, hash_file
from stage2.retrieval import retrieve
from stage2.preflight import blockers, native_smoke_blockers
from stage2.longllmlingua_context import checkpoint_hashes


class ProspectiveGate(unittest.TestCase):
    def test_task_matrix_and_historical_roles(self):
        manifest = artifact()
        self.assertEqual(json.loads((BASE / "matrix.json").read_text()), manifest)
        self.assertEqual(len(manifest["cells"]), 21)
        self.assertEqual(len({cell["cell"] for cell in manifest["cells"]}), 21)
        self.assertEqual({cell["subject_trajectory_count"] for cell in manifest["cells"]}, {0})
        self.assertEqual({cell["status"] for cell in manifest["cells"]}, {"PENDING_ENGINEERING_GATE"})
        roles = json.loads((BASE / "roles.json").read_text())
        old = json.loads((BASE.parent / roles["source"]).read_text())
        self.assertEqual([a["id"] for a in roles["agents"]], [a["id"] for a in old["agents"]])
        self.assertEqual(roles["entry_agent"], old["entry_agent"])
        self.assertIn("stage2/evidence.py", manifest["files_sha256"])
        self.assertIn("stage2/a2a_transport.py", manifest["files_sha256"])
        self.assertIn("stage2/mcp_workspace.py", manifest["files_sha256"])
        self.assertEqual(manifest["files_sha256"]["stage2/tasks.json"], hash_file(BASE / "tasks.json"))
        versions = json.loads((BASE / "versions.json").read_text())
        self.assertEqual(versions["probes"][4]["implementation_sha256"], hash_file(BASE / "retrieval.py"))

    def test_seven_native_boundaries_require_native_raw(self):
        for probe, operations in PROBES.items():
            with self.subTest(probe=probe), tempfile.TemporaryDirectory() as directory:
                sink = NativeCapture(directory, probe, "NON_SUBJECT_SMOKE", {"probe": probe, "source_commit": "synthetic-smoke"})
                operation = sorted(operations)[0]
                first = sink.capture(event_id="e1", operation=operation, phase="emitted",
                                     native_locator="mock:0", hook_id="offline-contract-smoke", raw=b"mock frame",
                                     actor="release_lead", carrier_id="carrier-1", source_id="task:T1")
                self.assertEqual(first["semantic_assessment"], "NOT_ADJUDICATED")
                sink.capture(event_id="e2", operation="termination", phase="returned",
                             native_locator="mock:1", hook_id="offline-contract-smoke", raw=b"stopped",
                             actor="release_lead", carrier_id="carrier-2", source_id="task:T1", parent_ids=("e1",), status="success")
                self.assertEqual(check_capture(directory), 2)
                with self.assertRaises(FileExistsError):
                    NativeCapture(directory, probe, "ACCIDENTAL_RERUN",
                                  {"probe": probe, "source_commit": "synthetic-smoke"})
                with self.assertRaises(ValueError):
                    sink.capture(event_id="e3", operation="nonexistent", phase="executed",
                                 native_locator="mock:2", hook_id="mock", raw=b"x",
                                 actor="release_lead", carrier_id="x", source_id="task:T1")
                with self.assertRaises(ValueError):
                    sink.capture(event_id="e3", operation=operation, phase="executed",
                                 native_locator="mock:2", hook_id="mock", raw=b"x",
                                 actor="release_lead", carrier_id="x", source_id="task:T1", parent_ids=("missing",))
                (Path(directory) / first["raw_path"]).write_bytes(b"altered")
                with self.assertRaises(AssertionError):
                    check_capture(directory)

    def test_x5_retrieval_addressed_and_repeatable(self):
        root = BASE / "fixtures/project"
        a = retrieve(root, "old python compatibility checkout", limit=3)
        self.assertEqual(a, retrieve(root, "old python compatibility checkout", limit=3))
        self.assertTrue(a)
        for hit in a:
            self.assertEqual(hit["sha256"], hash_file(root / hit["path"]))

    def test_subject_gate_closed_for_unbound_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "runtime.json"
            manifest.write_text("{}")
            errors = blockers(manifest, directory)
            self.assertIn("frozen subject provider/model/limits mismatch", errors)
            self.assertTrue(any("X1: installed implementation/native hook unbound" in error for error in errors))
            self.assertFalse(any("X2: installed implementation/native hook unbound" in error
                                 for error in blockers(manifest, directory, probe_id="X1")))

    def test_compression_does_not_accept_missing_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                checkpoint_hashes(Path(directory) / "missing")

    def test_native_boundary_smoke_cannot_open_subject_gate(self):
        from stage2.native_smoke import smoke_x5
        code_commit = "f" * 40
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            smoke_x5(root / "X5", code_commit)
            subject = json.loads((BASE / "subject.json").read_text())
            targets = json.loads((BASE / "runtime_bindings.json").read_text())["probes"]
            manifest = {
                "code_commit": code_commit,
                "matrix_sha256": hash_file(BASE / "matrix.json"),
                "roles_sha256": artifact()["files_sha256"]["stage2/roles.json"],
                "subject_provider": subject["provider"], "subject_model": subject["model_alias"],
                "expected_model_version": subject["expected_model_version"],
                "subject_limits": subject["limits"], "probes": {pid: {} for pid in targets},
            }
            manifest["probes"]["X5"] = {
                "source_commit": code_commit, "installed_version": "in-repo",
                "native_hook": targets["X5"]["hook_id"],
                "implementation_sha256": targets["X5"]["implementation_sha256"],
            }
            path = root / "manifest.json"
            path.write_text(json.dumps(manifest))
            self.assertEqual(native_smoke_blockers(path, root, "X5"), [])
            self.assertTrue(any("full coding smoke" in item for item in blockers(path, root, "X5")))

    def test_prior_and_current_version_are_executable(self):
        root = BASE / "fixtures/project"
        for version, path in (("1.9", root / "versions/before/server.py"),
                              ("2.0", root / "checkout_app/server.py")):
            with self.subTest(version=version):
                spec = importlib.util.spec_from_file_location(f"stage2_fixture_{version}", path)
                module = importlib.util.module_from_spec(spec)
                # The current service uses a relative import from checkout_app.
                if version == "2.0":
                    import sys
                    sys.path.insert(0, str(root))
                    try:
                        from checkout_app.server import Handler
                    finally:
                        sys.path.pop(0)
                else:
                    spec.loader.exec_module(module)
                    Handler = module.Handler
                server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    with urlopen(f"http://127.0.0.1:{server.server_port}/api/status") as response:
                        self.assertEqual(json.load(response)["version"], version)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join()


if __name__ == "__main__":
    unittest.main()
