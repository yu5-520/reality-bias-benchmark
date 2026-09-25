"""Non-study X6 official MemoryBank write/retrieve/reinforcement smoke."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from arena.providers import ScriptedProvider
from stage2.native_v7.observer import verify_observer
from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost
from stage2.native_v7.x6_memorybank.context import tree_hashes
from stage2.native_v7.x6_memorybank.runner import STAGE2, run_task


class RecordingScriptedProvider(ScriptedProvider):
    def __init__(self, scripted):
        super().__init__(scripted)
        self.prompts = []

    def complete_agent(self, messages, metadata=None):
        self.prompts.append(messages)
        return super().complete_agent(messages, metadata)


def _script():
    return [
        {"actions": [{"type": "list_files"}]},
        {"actions": [{"type": "finalize", "answer": "X6 MemoryBank smoke complete."}]},
    ]


def _digest(root):
    root = Path(root)
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            rows.append(f"{path.relative_to(root)}\0{hashlib.sha256(path.read_bytes()).hexdigest()}")
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def _build_tiny_embedding(root):
    import torch
    from transformers import BertConfig, BertModel, BertTokenizerFast

    root.mkdir(parents=True, exist_ok=False)
    vocab = [
        "[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]",
        "please", "add", "payment", "button", "checkout", "page", "works", "existing",
        "flow", "user", "request", "list", "files", "finalize", "release", "lead",
        "frontend", "backend", "tests", "current", "version", "python", "compatibility",
        "path", "memory", "role", "tool", "result", "actions", ".", ",", ":", "{", "}", "[", "]",
    ]
    (root / "vocab.txt").write_text("\n".join(vocab) + "\n")
    tokenizer = BertTokenizerFast(vocab_file=str(root / "vocab.txt"), do_lower_case=True)
    tokenizer.save_pretrained(root)
    torch.manual_seed(11)
    config = BertConfig(
        vocab_size=len(tokenizer),
        hidden_size=32,
        num_hidden_layers=1,
        num_attention_heads=1,
        intermediate_size=64,
        max_position_embeddings=256,
        pad_token_id=tokenizer.pad_token_id,
    )
    BertModel(config).save_pretrained(root, safe_serialization=False)
    return tree_hashes(root)


async def smoke(destination, upstream_root):
    destination = Path(destination)
    direct_checkout = destination / "direct-checkout"
    memory_checkout = destination / "memory-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", direct_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", memory_checkout)

    direct_provider = RecordingScriptedProvider(_script())
    direct = SoftwareEngineeringHost(
        task_id="T2", checkout=direct_checkout, provider=direct_provider
    )
    direct_result = await direct.run()

    task = next(
        row for row in json.loads((STAGE2 / "tasks.json").read_text())["tasks"] if row["id"] == "T2"
    )
    task_file = destination / "task.json"
    task_file.write_text(json.dumps(task, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    embedding = destination / "tiny-embedding"
    hashes = _build_tiny_embedding(embedding)
    manifest = destination / "embedding-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "stage2-x6-embedding-manifest-v1",
                "purpose": "NON_STUDY_ENGINEERING_SMOKE_ONLY",
                "files_sha256": hashes,
            },
            indent=2,
            sort_keys=True,
        ) + "\n"
    )

    observer_root = destination / "observer"
    memory_root = destination / "memory-state"
    memory_provider = RecordingScriptedProvider(_script())
    memory_result = await run_task(
        checkout=memory_checkout,
        task_file=task_file,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=observer_root,
        memory_root=memory_root,
        upstream_root=upstream_root,
        embedding_model=embedding,
        embedding_manifest=manifest,
        provider=memory_provider,
    )

    comparable_direct = {
        "answer": direct_result["answer"],
        "stop_reason": direct_result["stop_reason"],
        "turns": direct_result["turns"],
    }
    comparable_memory = {
        "answer": memory_result["answer"],
        "stop_reason": memory_result["stop_reason"],
        "turns": memory_result["turns"],
    }
    if comparable_direct != comparable_memory:
        raise RuntimeError(
            f"MemoryBank changed scripted host control result: {comparable_direct!r} != {comparable_memory!r}"
        )
    if _digest(direct_checkout) != _digest(memory_checkout):
        raise RuntimeError("MemoryBank changed checkout effects under scripted smoke")
    if memory_result["memorybank_writes"] != 2:
        raise RuntimeError("X6 did not write one MemoryBank exchange per model turn")
    if memory_result["memorybank_retrieval_calls"] != 1:
        raise RuntimeError("X6 did not retrieve memory on the second role turn")
    if memory_result["memorybank_recalled_items"] < 1:
        raise RuntimeError("X6 retrieval returned no prior memory")

    first_prompt = json.loads(memory_provider.prompts[0][-1]["content"])
    second_prompt = json.loads(memory_provider.prompts[1][-1]["content"])
    if first_prompt["memorybank_recall"]["memories"]:
        raise RuntimeError("X6 first role turn unexpectedly had prior memory")
    if not second_prompt["memorybank_recall"]["memories"]:
        raise RuntimeError("X6 second role turn did not expose retrieved MemoryBank content")

    role_memory = json.loads((memory_root / "release_lead.json").read_text())["release_lead"]
    day = role_memory["history"]["2026-09-25"]
    if len(day) != 2:
        raise RuntimeError("X6 persistent role memory does not contain both model turns")
    if int(day[0].get("memory_strength", 0)) < 2:
        raise RuntimeError("official MemoryBank recall did not reinforce the recalled memory")
    if day[0].get("last_recall_date") != "2026-09-25":
        raise RuntimeError("official MemoryBank recall date was not persisted")

    observer_files = verify_observer(observer_root)
    rows = [json.loads(line) for line in (observer_root / "events.jsonl").read_text().splitlines()]
    surfaces = [row["surface"] for row in rows]
    if surfaces.count("memorybank.memory.after_official_rebuild.post_return_copy") != 2:
        raise RuntimeError(f"unexpected X6 write observation surfaces: {surfaces!r}")
    if "memorybank.search_memory.result.post_return_copy" not in surfaces:
        raise RuntimeError("X6 retrieval result was not passively observed")

    report = {
        "schema": "stage2-v7-x6-memorybank-native-smoke-v1",
        "status": "NON_STUDY_X6_NATIVE_MEMORYBANK_SMOKE_PASS",
        "task": "T2",
        "turns": comparable_memory["turns"],
        "stop_reason": comparable_memory["stop_reason"],
        "memorybank_writes": memory_result["memorybank_writes"],
        "memorybank_retrieval_calls": memory_result["memorybank_retrieval_calls"],
        "memorybank_recalled_items": memory_result["memorybank_recalled_items"],
        "reinforced_strength": day[0]["memory_strength"],
        "observer_files": observer_files,
        "embedding_files": len(hashes),
        "checkout_sha256": _digest(memory_checkout),
        "subject_ready": False,
        "study_embedding_ready": False,
    }
    (destination / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--upstream-root", required=True)
    args = parser.parse_args()
    root = Path(args.out_root)
    root.mkdir(parents=True, exist_ok=False)
    result = asyncio.run(smoke(root, args.upstream_root))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
