"""Probe-specific X6 attachment using the frozen upstream MemoryBank mechanism."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from stage2.native_v7.observer import PassiveEventObserver, native_bytes

UPSTREAM_COMMIT = "cf61c4196e4cfdb0f2b7a0316249fa40312dc3a9"
FROZEN_MEMORY_DATE = "2026-09-25"


def tree_hashes(root):
    root = Path(root).resolve(strict=True)
    if not root.is_dir() or not any(root.iterdir()):
        raise ValueError("nonempty embedding checkpoint required")
    files = list(root.rglob("*"))
    if any(path.is_symlink() for path in files):
        raise ValueError("embedding checkpoint symlinks are not allowed")
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in files
        if path.is_file()
    }


def verify_upstream(root):
    root = Path(root).resolve(strict=True)
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if head != UPSTREAM_COMMIT:
        raise ValueError(f"MemoryBank upstream differs from frozen commit: {head}")
    required = root / "memory_bank/memory_retrieval/forget_memory.py"
    if not required.is_file():
        raise ValueError("frozen MemoryBank retrieval implementation is missing")
    return root


def load_embedding_manifest(path):
    payload = json.loads(Path(path).read_text())
    if payload.get("schema") != "stage2-x6-embedding-manifest-v1":
        raise ValueError("unexpected X6 embedding manifest schema")
    hashes = payload.get("files_sha256")
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("X6 embedding manifest must contain file hashes")
    return hashes


class OfficialMemoryBankContext:
    """Persistent per-role MemoryBank retrieval/reinforcement around the frozen host.

    The upstream MemoryBank code owns memory loading, FAISS indexing, retrieval,
    forgetting-curve metadata and recall-strength updates. This attachment only maps
    each frozen software-engineering role to its own memory file and exposes returned
    memories to that role's next model prompt.
    """

    def __init__(
        self,
        *,
        upstream_root,
        embedding_model,
        embedding_manifest,
        memory_root,
        observer_root=None,
        top_k=3,
    ):
        self.upstream_root = verify_upstream(upstream_root)
        self.embedding_model = Path(embedding_model).resolve(strict=True)
        expected = load_embedding_manifest(embedding_manifest)
        if tree_hashes(self.embedding_model) != expected:
            raise ValueError("X6 embedding checkpoint differs from frozen manifest")
        if not 1 <= int(top_k) <= 6:
            raise ValueError("invalid MemoryBank top_k")
        self.top_k = int(top_k)
        self.memory_root = Path(memory_root)
        self.memory_root.mkdir(parents=True, exist_ok=False)
        self.observer = (
            PassiveEventObserver(observer_root, probe="X6")
            if observer_root is not None
            else None
        )
        self.retrievers = {}
        self.vector_stores = {}
        self.pending_queries = {}
        self.retrieval_calls = 0
        self.memory_writes = 0
        self.recalled_items = 0

        bank_path = str(self.upstream_root / "memory_bank")
        if bank_path not in sys.path:
            sys.path.insert(0, bank_path)
        from langchain.embeddings.huggingface import HuggingFaceEmbeddings
        from memory_retrieval.forget_memory import LocalMemoryRetrieval

        self.LocalMemoryRetrieval = LocalMemoryRetrieval
        self.embeddings = HuggingFaceEmbeddings(
            model_name=str(self.embedding_model),
            model_kwargs={"device": "cpu"},
        )

    def _memory_file(self, role):
        return self.memory_root / f"{role}.json"

    def _index_root(self, role):
        return self.memory_root / f"{role}-faiss"

    def _ensure_memory_file(self, role):
        path = self._memory_file(role)
        if not path.exists():
            payload = {
                role: {
                    "name": role,
                    "summary": {},
                    "personality": {},
                    "overall_history": "",
                    "history": {},
                }
            }
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            )
        return path

    def _new_retriever(self):
        retriever = self.LocalMemoryRetrieval()
        retriever.language = "en"
        retriever.embeddings = self.embeddings
        retriever.top_k = self.top_k
        return retriever

    def _rebuild(self, role):
        memory_file = self._ensure_memory_file(role)
        index_root = self._index_root(role)
        if index_root.exists():
            shutil.rmtree(index_root)
        retriever = self._new_retriever()
        vs_path, loaded = retriever.init_memory_vector_store(
            filepath=str(memory_file),
            vs_path=str(index_root),
            user_name=role,
            cur_date=FROZEN_MEMORY_DATE,
        )
        if vs_path is None or str(memory_file) not in loaded:
            raise RuntimeError("MemoryBank did not build the role memory index")
        vector_store = retriever.load_memory_index(vs_path)
        self.retrievers[role] = retriever
        self.vector_stores[role] = vector_store

    def _observe(self, raw, surface):
        if self.observer is None:
            return
        returned = self.observer.observe(raw, surface=surface)
        if returned is not raw or returned != raw:
            raise RuntimeError("MemoryBank observer altered evidence bytes")

    def enrich(self, messages, *, role, task):
        payload = json.loads(messages[-1]["content"])
        query_payload = {
            "user_request": task["user_request"],
            "inbox": payload["inbox"],
            "observations": payload["observations"],
        }
        query = json.dumps(query_payload, ensure_ascii=False, sort_keys=True)
        self.pending_queries[role] = query
        recalls = []
        dates = ""
        if role in self.vector_stores:
            memory_file = self._memory_file(role)
            before = memory_file.read_bytes()
            retriever = self.retrievers[role]
            recalls, dates = retriever.search_memory(
                query,
                self.vector_stores[role],
                cur_date=FROZEN_MEMORY_DATE,
            )
            self.retrieval_calls += 1
            self.recalled_items += len(recalls)
            after = memory_file.read_bytes()
            self._observe(query.encode("utf-8"), "memorybank.search_memory.query.post_return_copy")
            self._observe(native_bytes({"recalls": recalls, "dates": dates}), "memorybank.search_memory.result.post_return_copy")
            self._observe(before, "memorybank.memory.before_recall.post_return_copy")
            self._observe(after, "memorybank.memory.after_recall.post_return_copy")
        payload["memorybank_recall"] = {"memories": recalls, "dates": dates}
        return [
            *messages[:-1],
            {**messages[-1], "content": json.dumps(payload, ensure_ascii=False)},
        ]

    def remember(self, *, role, response):
        query = self.pending_queries.pop(role, None)
        if query is None:
            raise RuntimeError("MemoryBank write has no matching role query")
        content = response.get("content") if isinstance(response, dict) else None
        if not isinstance(content, str) or not content:
            raise ValueError("MemoryBank requires a nonempty model response")
        memory_file = self._ensure_memory_file(role)
        payload = json.loads(memory_file.read_text())
        role_memory = payload[role]
        history = role_memory.setdefault("history", {})
        day = history.setdefault(FROZEN_MEMORY_DATE, [])
        day.append({"query": query, "response": content})
        memory_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        # The upstream loader now owns memory metadata, forgetting-curve handling,
        # vector indexing and future recall-strength updates.
        self._rebuild(role)
        self.memory_writes += 1
        self._observe(
            memory_file.read_bytes(),
            "memorybank.memory.after_official_rebuild.post_return_copy",
        )

    def seal(self):
        if self.observer is None:
            return None
        return self.observer.seal()
