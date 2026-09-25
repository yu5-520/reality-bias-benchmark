"""Probe-specific X7 attachment at the official LongLLMLingua compression boundary."""
from __future__ import annotations

import hashlib
import json
from importlib.metadata import version
from pathlib import Path

from stage2.native_v7.observer import PassiveEventObserver, native_bytes


def checkpoint_hashes(checkpoint):
    checkpoint = Path(checkpoint).resolve(strict=True)
    if not checkpoint.is_dir() or not any(checkpoint.iterdir()):
        raise ValueError("nonempty local compressor checkpoint required")
    files = list(checkpoint.rglob("*"))
    if any(path.is_symlink() for path in files):
        raise ValueError("checkpoint symlinks are not allowed")
    return {
        str(path.relative_to(checkpoint)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in files
        if path.is_file()
    }


class FrozenLongLLMLinguaContext:
    """Compress only historical inbox/tool context through official PromptCompressor.

    User goal, role identity and the host action contract stay uncompressed. The
    passive observer receives copies only after the compressor has returned, so it
    cannot influence token ranking, compression output or prompt construction.
    """

    def __init__(self, *, checkpoint, expected_hashes, observer_root=None, rate=0.5):
        if not 0 < float(rate) < 1:
            raise ValueError("fixed compression rate must be within (0, 1)")
        observed_hashes = checkpoint_hashes(checkpoint)
        if observed_hashes != expected_hashes:
            raise ValueError("compressor checkpoint differs from frozen manifest")
        if version("llmlingua") != "0.2.2":
            raise RuntimeError("llmlingua==0.2.2 required")
        from llmlingua import PromptCompressor

        self.compressor = PromptCompressor(
            model_name=str(Path(checkpoint).resolve()),
            device_map="cpu",
            model_config={"local_files_only": True, "trust_remote_code": False},
        )
        self.rate = float(rate)
        self.observer = (
            PassiveEventObserver(observer_root, probe="X7") if observer_root is not None else None
        )
        self.count = 0
        self.last_result = None

    def enrich(self, messages, *, role, task):
        payload = json.loads(messages[-1]["content"])
        context_text = json.dumps(
            {"inbox": payload["inbox"], "observations": payload["observations"]},
            ensure_ascii=False,
            sort_keys=True,
        )
        self.count += 1
        result = self.compressor.compress_prompt(
            context=[context_text],
            question=task["user_request"],
            rate=self.rate,
            rank_method="longllmlingua",
        )
        if not isinstance(result, dict) or not isinstance(result.get("compressed_prompt"), str):
            raise RuntimeError("LongLLMLingua did not produce compressed_prompt")

        # Observe only after the native compressor has completed. These bytes are
        # evidence copies; they are never read back into the execution path.
        if self.observer is not None:
            input_bytes = context_text.encode("utf-8")
            returned_input = self.observer.observe(
                input_bytes,
                surface="llmlingua.PromptCompressor.compress_prompt.input.post_return_copy",
            )
            if returned_input is not input_bytes or returned_input != input_bytes:
                raise RuntimeError("LongLLMLingua observer altered input evidence bytes")
            result_bytes = native_bytes(result)
            returned_result = self.observer.observe(
                result_bytes,
                surface="llmlingua.PromptCompressor.compress_prompt.output.post_return_copy",
            )
            if returned_result is not result_bytes or returned_result != result_bytes:
                raise RuntimeError("LongLLMLingua observer altered output evidence bytes")

        payload["inbox"] = []
        payload["observations"] = result["compressed_prompt"]
        self.last_result = result
        return [
            *messages[:-1],
            {**messages[-1], "content": json.dumps(payload, ensure_ascii=False)},
        ]

    def seal(self):
        if self.observer is None:
            return None
        return self.observer.seal()
