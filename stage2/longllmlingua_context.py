"""X7 binding to the actual LongLLMLingua compressor; no substitute tokenizer."""
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

from .evidence import canonical_bytes


def checkpoint_hashes(checkpoint):
    checkpoint = Path(checkpoint).resolve(strict=True)
    if not checkpoint.is_dir() or not any(checkpoint.iterdir()):
        raise ValueError("nonempty local compressor checkpoint required")
    files = list(checkpoint.rglob("*"))
    if any(path.is_symlink() for path in files):
        raise ValueError("checkpoint symlinks are not allowed")
    return {str(path.relative_to(checkpoint)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files if path.is_file()}


class LongLLMLinguaContext:
    probe = "X7"

    def __init__(self, capture, *, checkpoint, expected_hashes, rate=0.5):
        if capture.probe != self.probe or not 0 < rate < 1:
            raise ValueError("X7 capture and fixed compression rate required")
        if checkpoint_hashes(checkpoint) != expected_hashes:
            raise ValueError("compressor checkpoint differs from frozen weights")
        if version("llmlingua") != "0.2.2":
            raise RuntimeError("llmlingua==0.2.2 required")
        from llmlingua import PromptCompressor
        self.compressor = PromptCompressor(model_name=str(checkpoint), device_map="cpu",
                                           model_config={"local_files_only": True,
                                                         "trust_remote_code": False})
        self.capture = capture
        self.rate = rate
        self.count = 0

    def enrich(self, messages, *, role, task, cause=()):
        payload = json.loads(messages[-1]["content"])
        # Keep the user goal, role identity and action contract intact. Only
        # historical inbox/tool context is compressed by the real model.
        context = json.dumps({"inbox": payload["inbox"], "observations": payload["observations"]},
                             ensure_ascii=False)
        self.count += 1
        before = self.capture.capture(event_id=f"compress-input-{self.count}", operation="compress",
                                      phase="emitted", native_locator=f"llmlingua:compress_prompt:{self.count}",
                                      hook_id="llmlingua.PromptCompressor.compress_prompt", raw=context.encode(),
                                      actor=role, source_id=f"task:{task['id']}", carrier_id=f"input-context:{self.count}",
                                      carrier_type="long-context", parent_ids=cause)
        result = self.compressor.compress_prompt(context=[context], question=task["user_request"],
                                                 rate=self.rate, rank_method="longllmlingua")
        if not isinstance(result, dict) or "compressed_prompt" not in result:
            raise RuntimeError("LongLLMLingua did not produce a compressed context")
        compressed = result["compressed_prompt"]
        after = self.capture.capture(event_id=f"compress-output-{self.count}", operation="compress",
                                     phase="returned", native_locator=f"llmlingua:compress_result:{self.count}",
                                     hook_id="llmlingua.PromptCompressor.compress_prompt",
                                     raw=canonical_bytes(result), actor=role,
                                     source_id=f"task:{task['id']}", carrier_id=f"compressed-context:{self.count}",
                                     carrier_type="longllmlingua-output", parent_ids=(before["event_id"],))
        payload["inbox"] = []
        payload["observations"] = compressed
        messages = [*messages[:-1], {**messages[-1], "content": json.dumps(payload, ensure_ascii=False)}]
        return messages, after["event_id"]
