"""Non-study X7 official LongLLMLingua boundary smoke with a tiny local checkpoint."""
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
from stage2.native_v7.x7_longllmlingua.context import checkpoint_hashes
from stage2.native_v7.x7_longllmlingua.runner import STAGE2, run_task


class RecordingScriptedProvider(ScriptedProvider):
    def __init__(self, scripted):
        super().__init__(scripted)
        self.prompts = []

    def complete_agent(self, messages, metadata=None):
        self.prompts.append(messages)
        return super().complete_agent(messages, metadata)


def _script():
    return [{"actions": [{"type": "finalize", "answer": "X7 LongLLMLingua smoke complete."}]}]


def _digest(root):
    root = Path(root)
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            rows.append(
                f"{path.relative_to(root)}\0{hashlib.sha256(path.read_bytes()).hexdigest()}"
            )
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def _build_tiny_checkpoint(root):
    import torch
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace
    from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast

    root.mkdir(parents=True, exist_ok=False)
    vocab_words = [
        "<pad>", "<eos>", "<unk>", "{", "}", "[", "]", ":", ",", '"',
        "inbox", "observations", "from", "USER", "content", "Update", "checkout",
        "payment", "payload", "version", "without", "breaking", "compatibility",
        "You", "are", "coordinator", "work", "on", "request", "provided", "code",
        "legacy", "current", "server", "tests", "frontend", "backend", "agent", ".",
    ]
    vocab = {word: index for index, word in enumerate(vocab_words)}
    tokenizer = Tokenizer(WordLevel(vocab=vocab, unk_token="<unk>"))
    tokenizer.pre_tokenizer = Whitespace()
    fast = PreTrainedTokenizerFast(
        tokenizer_object=tokenizer,
        unk_token="<unk>",
        pad_token="<pad>",
        eos_token="<eos>",
        bos_token="<eos>",
    )
    fast.save_pretrained(root)
    torch.manual_seed(7)
    config = GPT2Config(
        vocab_size=len(fast),
        n_positions=128,
        n_ctx=128,
        n_embd=32,
        n_layer=1,
        n_head=1,
        bos_token_id=fast.bos_token_id,
        eos_token_id=fast.eos_token_id,
        pad_token_id=fast.pad_token_id,
    )
    model = GPT2LMHeadModel(config)
    model.save_pretrained(root, safe_serialization=True)
    return checkpoint_hashes(root)


async def smoke(destination):
    destination = Path(destination)
    direct_checkout = destination / "direct-checkout"
    compressed_checkout = destination / "compressed-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", direct_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", compressed_checkout)

    direct_provider = RecordingScriptedProvider(_script())
    direct = SoftwareEngineeringHost(
        task_id="T3", checkout=direct_checkout, provider=direct_provider
    )
    direct_result = await direct.run()

    task = next(
        row for row in json.loads((STAGE2 / "tasks.json").read_text())["tasks"] if row["id"] == "T3"
    )
    task_file = destination / "task.json"
    task_file.write_text(json.dumps(task, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    checkpoint = destination / "tiny-checkpoint"
    hashes = _build_tiny_checkpoint(checkpoint)
    manifest = destination / "checkpoint-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "stage2-x7-checkpoint-manifest-v1",
                "purpose": "NON_STUDY_ENGINEERING_SMOKE_ONLY",
                "files_sha256": hashes,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    observer_root = destination / "observer"
    compressed_provider = RecordingScriptedProvider(_script())
    compressed_result = await run_task(
        checkout=compressed_checkout,
        task_file=task_file,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        checkpoint=checkpoint,
        checkpoint_manifest=manifest,
        observer_root=observer_root,
        provider=compressed_provider,
    )

    comparable_direct = {
        "answer": direct_result["answer"],
        "stop_reason": direct_result["stop_reason"],
        "turns": direct_result["turns"],
    }
    comparable_compressed = {
        "answer": compressed_result["answer"],
        "stop_reason": compressed_result["stop_reason"],
        "turns": compressed_result["turns"],
    }
    if comparable_direct != comparable_compressed:
        raise RuntimeError(
            f"LongLLMLingua changed scripted host control result: "
            f"{comparable_direct!r} != {comparable_compressed!r}"
        )
    if _digest(direct_checkout) != _digest(compressed_checkout):
        raise RuntimeError("LongLLMLingua changed checkout effects under scripted smoke")
    if compressed_result["compression_calls"] != 1:
        raise RuntimeError(
            f"expected one compression call, observed {compressed_result['compression_calls']}"
        )

    direct_prompt = json.loads(direct_provider.prompts[0][-1]["content"])
    compressed_prompt = json.loads(compressed_provider.prompts[0][-1]["content"])
    if not direct_prompt["inbox"]:
        raise RuntimeError("baseline prompt unexpectedly lacks inbox context")
    if compressed_prompt["inbox"] != []:
        raise RuntimeError("X7 prompt did not replace historical inbox with compressed context")
    if not isinstance(compressed_prompt["observations"], str) or not compressed_prompt["observations"]:
        raise RuntimeError("X7 model-visible compressed context is missing")
    if compressed_prompt["user_request"] != direct_prompt["user_request"]:
        raise RuntimeError("X7 changed the frozen user request outside compression scope")
    if compressed_prompt["available_actions"] != direct_prompt["available_actions"]:
        raise RuntimeError("X7 changed the host action contract outside compression scope")

    observer_files = verify_observer(observer_root)
    rows = [json.loads(line) for line in (observer_root / "events.jsonl").read_text().splitlines()]
    surfaces = [row["surface"] for row in rows]
    if surfaces != [
        "llmlingua.PromptCompressor.compress_prompt.input.post_return_copy",
        "llmlingua.PromptCompressor.compress_prompt.output.post_return_copy",
    ]:
        raise RuntimeError(f"unexpected X7 observer surfaces: {surfaces!r}")

    last = compressed_result["last_compression"]
    if not isinstance(last.get("origin_tokens"), int) or not isinstance(last.get("compressed_tokens"), int):
        raise RuntimeError("official compressor token accounting is missing")

    report = {
        "schema": "stage2-v7-x7-longllmlingua-native-smoke-v1",
        "status": "NON_STUDY_X7_NATIVE_LONGLINGUA_SMOKE_PASS",
        "task": "T3",
        "turns": comparable_compressed["turns"],
        "stop_reason": comparable_compressed["stop_reason"],
        "compression_calls": compressed_result["compression_calls"],
        "origin_tokens": last["origin_tokens"],
        "compressed_tokens": last["compressed_tokens"],
        "observer_files": observer_files,
        "checkpoint_files": len(hashes),
        "checkout_sha256": _digest(compressed_checkout),
        "subject_ready": False,
        "study_checkpoint_ready": False,
    }
    (destination / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root")
    args = parser.parse_args()
    if args.out_root:
        root = Path(args.out_root)
        root.mkdir(parents=True, exist_ok=False)
        result = asyncio.run(smoke(root))
    else:
        with tempfile.TemporaryDirectory() as directory:
            result = asyncio.run(smoke(Path(directory)))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
