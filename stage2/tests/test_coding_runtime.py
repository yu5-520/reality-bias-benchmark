import asyncio
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from arena.providers import ScriptedProvider
from stage2.coding_arena import CodingArena
from stage2.evidence import NativeCapture, check_capture
from stage2.freeze import BASE, hash_file
from stage2.transports import AutoGenTransport, LocalSmokeTransport
from stage2.workspace import CodeWorkspace, new_workspace


class CodingRuntimeSmoke(unittest.TestCase):
    def test_isolated_checkout_and_real_file_lineage(self):
        source = BASE / "fixtures/project/README.md"
        baseline = hash_file(source)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkout = new_workspace(root / "checkout")
            capture = NativeCapture(root / "raw", "X1", "NON_SUBJECT_LOCAL_SMOKE",
                                    {"probe": "X1", "source_commit": "synthetic-smoke"})
            ws = CodeWorkspace(checkout, capture)
            names, listed = ws.list_files("release_lead", "task:T1")
            self.assertIn("versions/before/server.py", names)
            text, read = ws.read_file("README.md", "release_lead", "task:T1", (listed,))
            change, written = ws.write_file("README.md", text + "\nsmoke\n", "release_lead", read, (read,))
            self.assertEqual(change["before_sha256"], baseline)
            self.assertEqual(hash_file(source), baseline)
            self.assertNotEqual(hash_file(checkout / "README.md"), baseline)
            with self.assertRaises(ValueError):
                ws.read_file("../README.md", "backend", read)
            result, _ = ws.run_tests("qa", written, (written,))
            self.assertEqual(result["returncode"], 0)
            self.assertEqual(check_capture(root / "raw"), 4)

    def test_nine_role_native_route_is_not_assumed_for_local_smoke(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkout = new_workspace(root / "checkout")
            capture = NativeCapture(root / "raw", "X1", "NON_SUBJECT_LOCAL_SMOKE",
                                    {"probe": "X1", "source_commit": "synthetic-smoke"})
            provider = ScriptedProvider([
                {"decision_summary": "ask", "actions": [{"type": "delegate", "to": "backend", "content": "Review the checkout service."}]},
                {"decision_summary": "read", "actions": [{"type": "read_file", "path": "checkout_app/checkout.py"}]},
                {"decision_summary": "reply", "actions": [{"type": "finalize", "answer": "Reviewed current checkout."}]},
                {"decision_summary": "finish", "actions": [{"type": "finalize", "answer": "Version review complete."}]},
            ])
            runner = CodingArena(task_id="T1", checkout=checkout, capture=capture,
                                 transport=LocalSmokeTransport(capture), provider=provider)
            outcome = asyncio.run(runner.run())
            self.assertEqual(outcome["turns"], 4)
            self.assertEqual(outcome["stop_reason"], "finalized")
            self.assertEqual(check_capture(root / "raw"), 12)
            rows = [json.loads(line) for line in (root / "raw/events.jsonl").read_text().splitlines()]
            self.assertIn("file_read", [row["operation"] for row in rows])
            self.assertTrue(all(row["semantic_assessment"] == "NOT_ADJUDICATED" for row in rows))

    @unittest.skipUnless(importlib.util.find_spec("autogen_core"), "pinned AutoGen SDK unavailable")
    def test_autogen_native_dispatch_and_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = NativeCapture(root / "raw", "X1", "NON_SUBJECT_AUTOGEN_SMOKE",
                                    {"probe": "X1", "source_commit": "83afbf5857aac683340d4c692194e548b1e8edda"})
            provider = ScriptedProvider([
                {"decision_summary": "delegate", "actions": [{"type": "delegate", "to": "backend", "content": "Inspect service."}]},
                {"decision_summary": "report", "actions": [{"type": "finalize", "answer": "Service inspected."}]},
                {"decision_summary": "finish", "actions": [{"type": "finalize", "answer": "Done."}]},
            ])
            result = asyncio.run(CodingArena(task_id="T1", checkout=new_workspace(root / "checkout"),
                                             capture=capture, transport=AutoGenTransport(capture),
                                             provider=provider).run())
            self.assertEqual(result["stop_reason"], "finalized")
            self.assertEqual(check_capture(root / "raw"), 9)
            rows = [json.loads(line) for line in (root / "raw/events.jsonl").read_text().splitlines()]
            sent = next(row for row in rows if row["event_id"] == "autogen-send-1")
            received = next(row for row in rows if row["event_id"] == "autogen-recv-1")
            self.assertEqual(received["parent_ids"], [sent["event_id"]])
            self.assertEqual(received["carrier_id"], sent["carrier_id"])


if __name__ == "__main__":
    unittest.main()
