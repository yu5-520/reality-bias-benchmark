"""Probe-specific X5 attachment at the frozen retrieval/context boundary."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from stage2.native_v7.observer import PassiveEventObserver, native_bytes
from stage2.retrieval import INDEX_PATHS, retrieve

ROOT = Path(__file__).resolve().parents[3]
STAGE2 = ROOT / "stage2"


class FrozenRAGContext:
    """Run the frozen retriever and expose returned hits to the current role prompt.

    Observation happens only after the retrieval call has returned. The observer
    copies a serialization of the already-used query and already-returned hits and
    never supplies data back into ranking or prompt construction.
    """

    def __init__(self, observer_root=None, *, limit=3):
        if not 1 <= int(limit) <= len(INDEX_PATHS):
            raise ValueError("invalid frozen retrieval limit")
        self.limit = int(limit)
        self.corpus_root = STAGE2 / "fixtures/project"
        matrix = json.loads((STAGE2 / "matrix.json").read_text())
        prefix = "stage2/fixtures/project/"
        self.frozen_hashes = {
            path.removeprefix(prefix): digest
            for path, digest in matrix["files_sha256"].items()
            if path.startswith(prefix)
        }
        for relative in INDEX_PATHS:
            current = hashlib.sha256((self.corpus_root / relative).read_bytes()).hexdigest()
            if self.frozen_hashes.get(relative) != current:
                raise ValueError(f"frozen RAG corpus mismatch: {relative}")
        self.observer = (
            PassiveEventObserver(observer_root, probe="X5") if observer_root is not None else None
        )
        self.sequence = 0
        self.last_hits = []

    def enrich(self, messages, *, role, task):
        self.sequence += 1
        query = task["user_request"]
        hits = retrieve(self.corpus_root, query, limit=self.limit)
        for hit in hits:
            if self.frozen_hashes.get(hit["path"]) != hit["sha256"]:
                raise ValueError(f"retrieval hit differs from frozen corpus: {hit['path']}")

        if self.observer is not None:
            query_bytes = native_bytes({"query": query, "limit": self.limit})
            returned_query = self.observer.observe(
                query_bytes, surface="stage2.retrieval.retrieve.query.post_return_copy"
            )
            if returned_query is not query_bytes or returned_query != query_bytes:
                raise RuntimeError("RAG observer altered query evidence bytes")
            hits_bytes = native_bytes(hits)
            returned_hits = self.observer.observe(
                hits_bytes, surface="stage2.retrieval.retrieve.hits.post_return_copy"
            )
            if returned_hits is not hits_bytes or returned_hits != hits_bytes:
                raise RuntimeError("RAG observer altered result evidence bytes")

        payload = json.loads(messages[-1]["content"])
        payload["retrieved_context"] = hits
        self.last_hits = hits
        return [
            *messages[:-1],
            {**messages[-1], "content": json.dumps(payload, ensure_ascii=False)},
        ]

    def seal(self):
        if self.observer is None:
            return None
        return self.observer.seal()
