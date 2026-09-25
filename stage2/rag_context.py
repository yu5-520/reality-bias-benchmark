"""Prospective X5 retrieval mediation, using the frozen in-repo RAG index."""
import json

from .evidence import canonical_bytes
from .freeze import BASE, artifact
from .retrieval import retrieve


class RAGContext:
    probe = "X5"

    def __init__(self, capture, limit=3):
        if capture.probe != self.probe:
            raise ValueError("RAG context requires X5 capture")
        self.capture = capture
        self.limit = limit
        self.index_root = BASE / "fixtures/project"
        self.frozen_hashes = {path.removeprefix("stage2/fixtures/project/"): sha
                              for path, sha in artifact()["files_sha256"].items()
                              if path.startswith("stage2/fixtures/project/")}
        self.sequence = 0

    def enrich(self, messages, *, role, task, cause=()):
        self.sequence += 1
        query = task["user_request"]
        row = self.capture.capture(event_id=f"rag-query-{self.sequence}", operation="retrieve",
                                   phase="emitted", native_locator=f"stage2.retrieval:query:{self.sequence}",
                                   hook_id="stage2.retrieval.retrieve", raw=canonical_bytes({"query": query, "limit": self.limit}),
                                   actor=role, source_id=f"task:{task['id']}", carrier_id=f"rag-query:{self.sequence}",
                                   carrier_type="retrieval-query", parent_ids=cause)
        hits = retrieve(self.index_root, query, self.limit)
        if any(self.frozen_hashes[hit["path"]] != hit["sha256"] for hit in hits):
            raise ValueError("retrieval corpus differs from frozen fixture")
        returned = self.capture.capture(event_id=f"rag-result-{self.sequence}", operation="retrieve",
                                        phase="returned", native_locator=f"stage2.retrieval:result:{self.sequence}",
                                        hook_id="stage2.retrieval.retrieve", raw=canonical_bytes(hits), actor=role,
                                        source_id=f"task:{task['id']}", carrier_id=f"rag-result:{self.sequence}",
                                        carrier_type="retrieved-document-snippets", parent_ids=(row["event_id"],))
        payload = json.loads(messages[-1]["content"])
        payload["retrieved_context"] = hits
        messages = [*messages[:-1], {**messages[-1], "content": json.dumps(payload, ensure_ascii=False)}]
        return messages, returned["event_id"]
