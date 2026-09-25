"""Deterministic in-repository retrieval boundary for the X5 coding fixture.

This implements a retrieval surface only. A subject-side integration must still
record query, ranked hits, source file hashes and the actual downstream exposure.
"""
import re
from pathlib import Path
from .evidence import sha256

INDEX_PATHS = ("README.md", "versions/before.json", "versions/after.json",
               "checkout_app/checkout.py", "checkout_app/server.py", "legacy_compat.py", "run.py")


def tokens(text):
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def retrieve(root, query, limit=3):
    root = Path(root)
    words = tokens(query)
    if not words or not 1 <= limit <= len(INDEX_PATHS):
        raise ValueError("query and limit required")
    items = []
    for relative in INDEX_PATHS:
        raw = (root / relative).read_bytes()
        score = len(words & tokens(raw.decode("utf-8")))
        if score:
            items.append({"path": relative, "sha256": sha256(raw), "score": score,
                          "content": raw.decode("utf-8")})
    return sorted(items, key=lambda item: (-item["score"], item["path"]))[:limit]
