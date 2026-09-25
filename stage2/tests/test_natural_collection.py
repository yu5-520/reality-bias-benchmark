"""Admission and irreversibility checks; never invokes the subject provider."""
import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stage2.collect_natural import collect, validate_request, verify_seal
from stage2.freeze import ROOT, hash_file


class NaturalCollectionGate(unittest.TestCase):
    def test_missing_subject_credential_does_not_reserve_a_cell(self):
        import subprocess
        code = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "runtime.json"
            manifest.write_text(json.dumps({"code_commit": code}))
            with patch("stage2.collect_natural.blockers", return_value=[]), patch.dict(
                    "os.environ", {"DEEPSEEK_API_KEY": ""}):
                with self.assertRaisesRegex(RuntimeError, "credential is unavailable"):
                    asyncio.run(collect(probe="X5", task="T2", manifest=manifest,
                                        captures=root, out_root=root / "natural"))
            self.assertFalse((root / "natural").exists())

    def test_blocked_architecture_is_refused_before_reading_manifest(self):
        for probe in ("X2", "X6", "X7"):
            with self.subTest(probe=probe), self.assertRaisesRegex(ValueError, "engineering-blocked"):
                validate_request(probe=probe, task="T1", manifest="missing", captures="missing",
                                 upstream=None)

    def test_occupied_cell_is_not_entered_again(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "X5-T1"
            destination.mkdir()
            (destination / "prior_attempt").write_bytes(b"keep")
            with patch("stage2.collect_natural.validate_request",
                       return_value=("X5-T1", {"code_commit": "commit"}, {})):
                with self.assertRaises(FileExistsError):
                    asyncio.run(collect(probe="X5", task="T1", manifest="unused",
                                        captures="unused", out_root=directory))
            self.assertEqual((destination / "prior_attempt").read_bytes(), b"keep")

    def test_failed_attempt_is_sealed_and_remains_occupied(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "X5-T3"
            with patch("stage2.collect_natural.validate_request",
                       return_value=("X5-T3", {"probe": "X5", "source_commit": "test",
                                               "code_commit": "test", "expected_model_version": "test"}, {})), \
                    patch("stage2.collect_natural.new_workspace", side_effect=RuntimeError("checkout unavailable")):
                with self.assertRaisesRegex(RuntimeError, "checkout unavailable"):
                    asyncio.run(collect(probe="X5", task="T3", manifest="unused",
                                        captures="unused", out_root=directory))
                sealed = verify_seal(destination)
                self.assertEqual(sealed["status"], "FAILED_ATTEMPT_PRESERVED")
                self.assertEqual(sealed["error_type"], "RuntimeError")
                with self.assertRaises(FileExistsError):
                    asyncio.run(collect(probe="X5", task="T3", manifest="unused",
                                        captures="unused", out_root=directory))

    def test_seal_rejects_mutated_and_added_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file = root / "raw"
            file.write_bytes(b"original")
            (root / "seal.json").write_text(json.dumps({"events": 0, "integrity_error": None,
                                                        "sha256": {"raw": hash_file(file)}}))
            self.assertEqual(verify_seal(root)["events"], 0)
            file.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "altered"):
                verify_seal(root)
            file.write_bytes(b"original")
            (root / "unexpected").write_bytes(b"extra")
            with self.assertRaisesRegex(ValueError, "altered"):
                verify_seal(root)


if __name__ == "__main__":
    unittest.main()
