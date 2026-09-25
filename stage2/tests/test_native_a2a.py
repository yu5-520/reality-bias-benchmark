import asyncio
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from arena.providers import ScriptedProvider
from stage2.coding_arena import CodingArena
from stage2.evidence import NativeCapture, check_capture
from stage2.workspace import new_workspace


@unittest.skipUnless(importlib.util.find_spec("a2a"), "pinned A2A SDK unavailable")
class A2ANativeSmoke(unittest.TestCase):
    def test_http_remote_task_and_artifact(self):
        from stage2.a2a_transport import A2AProtocolTransport
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = NativeCapture(root / "raw", "X3", "NON_SUBJECT_A2A_PROTOCOL_SMOKE",
                                    {"probe": "X3", "source_commit": "24db37ee24c927df936289ad6ffbc8c746a44db8"})
            provider = ScriptedProvider([
                {"decision_summary": "delegate", "actions": [{"type": "delegate", "to": "backend", "content": "Inspect service."}]},
                {"decision_summary": "ack", "actions": [{"type": "finalize", "answer": "Inspected."}]},
                {"decision_summary": "done", "actions": [{"type": "finalize", "answer": "Done."}]},
            ])
            arena = CodingArena(task_id="T1", checkout=new_workspace(root / "checkout"),
                                capture=capture, transport=A2AProtocolTransport(capture), provider=provider)
            self.assertEqual(asyncio.run(arena.run())["stop_reason"], "finalized")
            self.assertEqual(check_capture(root / "raw"), 10)
            rows = [json.loads(line) for line in (root / "raw/events.jsonl").read_text().splitlines()]
            task = next(row for row in rows if row["operation"] == "remote_task")
            artifact = next(row for row in rows if row["operation"] == "artifact_return")
            self.assertEqual(artifact["parent_ids"], [task["event_id"]])
            self.assertNotEqual(artifact["carrier_type"], "common-pool")
