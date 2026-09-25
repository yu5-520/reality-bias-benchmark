import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from arena.providers import ScriptedProvider
from stage2.coding_arena import CodingArena
from stage2.evidence import NativeCapture, check_capture
from stage2.rag_context import RAGContext
from stage2.transports import LocalSmokeTransport
from stage2.workspace import new_workspace


class RAGSmoke(unittest.TestCase):
    def test_frozen_corpus_enters_prompt_with_source_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = NativeCapture(root / "raw", "X5", "NON_SUBJECT_RAG_SMOKE",
                                    {"probe": "X5", "source_commit": "baf19cd7f7dde0a2f7ebfde254bffac6690e018b88d8d9ea4a811d37a53b12c4"})
            provider = ScriptedProvider([{"decision_summary": "complete", "actions": [{"type": "finalize", "answer": "Done."}]}])
            runner = CodingArena(task_id="T3", checkout=new_workspace(root / "checkout"),
                                 capture=capture, transport=LocalSmokeTransport(capture), provider=provider,
                                 context_adapter=RAGContext(capture))
            self.assertEqual(asyncio.run(runner.run())["stop_reason"], "finalized")
            self.assertEqual(check_capture(root / "raw"), 5)
            rows = [json.loads(line) for line in (root / "raw/events.jsonl").read_text().splitlines()]
            retrieval = next(row for row in rows if row["event_id"] == "rag-result-1")
            prompt = next(row for row in rows if row["operation"] == "model_input")
            self.assertIn(retrieval["event_id"], prompt["parent_ids"])
            hits = json.loads((root / "raw" / retrieval["raw_path"]).read_text())
            self.assertTrue(all(hit["path"] and len(hit["sha256"]) == 64 for hit in hits))
