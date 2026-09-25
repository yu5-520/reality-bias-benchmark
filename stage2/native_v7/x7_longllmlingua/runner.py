"""X7 runner: frozen Software Engineering host plus official LongLLMLingua.

The common capability-layer host retains role scheduling and communication. X7
changes only the historical context presented to the subject model. The official
pinned llmlingua package performs compression from a locally frozen checkpoint.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from arena.providers import DeepSeekArenaProvider
from stage2.native_v7.software_host_v1 import ROLES, TASKS, SoftwareEngineeringHost
from stage2.native_v7.x7_longllmlingua.context import (
    FrozenLongLLMLinguaContext,
    checkpoint_hashes,
)

ROOT = Path(__file__).resolve().parents[3]
STAGE2 = ROOT / "stage2"


class LongLLMLinguaSoftwareEngineeringHost(SoftwareEngineeringHost):
    """Frozen host with the X7 context-compression hook only."""

    def __init__(self, *, compressor_context, **kwargs):
        super().__init__(**kwargs)
        self.compressor_context = compressor_context

    def _prompt(self, role, observations):
        messages = super()._prompt(role, observations)
        return self.compressor_context.enrich(messages, role=role, task=self.task)


def _load_inputs(task_file, roles_file, subject_file):
    task = json.loads(Path(task_file).read_text())
    roles = json.loads(Path(roles_file).read_text())
    subject = json.loads(Path(subject_file).read_text())
    if task.get("id") not in TASKS or task != TASKS[task["id"]]:
        raise ValueError("task file differs from frozen T1-T3")
    if roles != ROLES:
        raise ValueError("roles file differs from frozen nine-role roster")
    canonical_subject = json.loads((STAGE2 / "subject.json").read_text())
    if subject != canonical_subject:
        raise ValueError("subject file differs from frozen subject profile")
    return task, subject


def _load_checkpoint_manifest(path):
    payload = json.loads(Path(path).read_text())
    if payload.get("schema") != "stage2-x7-checkpoint-manifest-v1":
        raise ValueError("unexpected X7 checkpoint manifest schema")
    hashes = payload.get("files_sha256")
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("X7 checkpoint manifest must contain file hashes")
    return hashes


def build_subject_provider(subject):
    source = ROOT / subject["source_config"]
    config = json.loads(source.read_text())
    if (
        config["provider"] != subject["provider"]
        or config["model_alias"] != subject["model_alias"]
        or config["expected_model_version"] != subject["expected_model_version"]
        or config["subject"] != subject["subject"]
    ):
        raise ValueError("DeepSeek source configuration differs from frozen subject")
    return DeepSeekArenaProvider(config)


async def run_task(
    *,
    checkout,
    task_file,
    roles_file,
    subject_file,
    checkpoint,
    checkpoint_manifest,
    observer_root=None,
    provider=None,
):
    task, subject = _load_inputs(task_file, roles_file, subject_file)
    expected_hashes = _load_checkpoint_manifest(checkpoint_manifest)
    # Recheck before model loading so the compression condition is content-addressed.
    if checkpoint_hashes(checkpoint) != expected_hashes:
        raise ValueError("X7 checkpoint differs from supplied frozen manifest")
    compressor = FrozenLongLLMLinguaContext(
        checkpoint=checkpoint,
        expected_hashes=expected_hashes,
        observer_root=observer_root,
        rate=0.5,
    )
    active_provider = provider if provider is not None else build_subject_provider(subject)
    host = LongLLMLinguaSoftwareEngineeringHost(
        compressor_context=compressor,
        task_id=task["id"],
        checkout=checkout,
        provider=active_provider,
        max_turns=int(subject["limits"]["max_turns"]),
    )
    try:
        result = await host.run()
    finally:
        compressor.seal()
    result["compression_calls"] = compressor.count
    if compressor.last_result is not None:
        result["last_compression"] = {
            key: compressor.last_result.get(key)
            for key in ("origin_tokens", "compressed_tokens", "ratio", "rate")
        }
    return result


def _checkpoint_from_args_or_env(args):
    checkpoint = args.checkpoint or os.environ.get("STAGE2_X7_CHECKPOINT")
    manifest = args.checkpoint_manifest or os.environ.get("STAGE2_X7_CHECKPOINT_MANIFEST")
    if not checkpoint or not manifest:
        raise SystemExit(
            "X7 requires --checkpoint/--checkpoint-manifest or "
            "STAGE2_X7_CHECKPOINT/STAGE2_X7_CHECKPOINT_MANIFEST"
        )
    return checkpoint, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--roles-file", required=True)
    parser.add_argument("--subject-file", required=True)
    parser.add_argument("--observer-root", required=True)
    parser.add_argument("--checkpoint")
    parser.add_argument("--checkpoint-manifest")
    args = parser.parse_args()
    checkpoint, checkpoint_manifest = _checkpoint_from_args_or_env(args)
    result = asyncio.run(
        run_task(
            checkout=args.checkout,
            task_file=args.task_file,
            roles_file=args.roles_file,
            subject_file=args.subject_file,
            checkpoint=checkpoint,
            checkpoint_manifest=checkpoint_manifest,
            observer_root=args.observer_root,
        )
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
