"""X6 runner: frozen software-engineering host plus official MemoryBank mechanism."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from arena.providers import DeepSeekArenaProvider
from stage2.native_v7.software_host_v1 import ROLES, TASKS, SoftwareEngineeringHost
from stage2.native_v7.x6_memorybank.context import OfficialMemoryBankContext

ROOT = Path(__file__).resolve().parents[3]
STAGE2 = ROOT / "stage2"


class MemoryBankSoftwareEngineeringHost(SoftwareEngineeringHost):
    """The frozen capability host with X6 memory retrieval/write hooks only."""

    def __init__(self, *, memory_context, **kwargs):
        super().__init__(**kwargs)
        self.memory_context = memory_context

    def _prompt(self, role, observations):
        messages = super()._prompt(role, observations)
        return self.memory_context.enrich(messages, role=role, task=self.task)

    async def _complete(self, messages, *, role, turn):
        response = await super()._complete(messages, role=role, turn=turn)
        self.memory_context.remember(role=role, response=response)
        return response


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


def _asset(value, env_name, label):
    resolved = value or os.environ.get(env_name)
    if not resolved:
        raise SystemExit(f"X6 requires {label} via argument or {env_name}")
    return resolved


async def run_task(
    *,
    checkout,
    task_file,
    roles_file,
    subject_file,
    observer_root,
    memory_root,
    upstream_root,
    embedding_model,
    embedding_manifest,
    provider=None,
):
    task, subject = _load_inputs(task_file, roles_file, subject_file)
    memory = OfficialMemoryBankContext(
        upstream_root=upstream_root,
        embedding_model=embedding_model,
        embedding_manifest=embedding_manifest,
        memory_root=memory_root,
        observer_root=observer_root,
        top_k=3,
    )
    active_provider = provider if provider is not None else build_subject_provider(subject)
    host = MemoryBankSoftwareEngineeringHost(
        memory_context=memory,
        task_id=task["id"],
        checkout=checkout,
        provider=active_provider,
        max_turns=int(subject["limits"]["max_turns"]),
    )
    try:
        result = await host.run()
    finally:
        memory.seal()
    result["memorybank_retrieval_calls"] = memory.retrieval_calls
    result["memorybank_writes"] = memory.memory_writes
    result["memorybank_recalled_items"] = memory.recalled_items
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--roles-file", required=True)
    parser.add_argument("--subject-file", required=True)
    parser.add_argument("--observer-root", required=True)
    parser.add_argument("--memory-root", required=True)
    parser.add_argument("--upstream-root")
    parser.add_argument("--embedding-model")
    parser.add_argument("--embedding-manifest")
    args = parser.parse_args()
    upstream = _asset(args.upstream_root, "STAGE2_X6_UPSTREAM", "frozen MemoryBank source")
    model = _asset(args.embedding_model, "STAGE2_X6_EMBEDDING_MODEL", "frozen embedding checkpoint")
    manifest = _asset(args.embedding_manifest, "STAGE2_X6_EMBEDDING_MANIFEST", "embedding manifest")
    result = asyncio.run(
        run_task(
            checkout=args.checkout,
            task_file=args.task_file,
            roles_file=args.roles_file,
            subject_file=args.subject_file,
            observer_root=args.observer_root,
            memory_root=args.memory_root,
            upstream_root=upstream,
            embedding_model=model,
            embedding_manifest=manifest,
        )
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
