"""X5 runner: frozen Software Engineering host plus frozen in-repo RAG context.

The shared software-engineering host retains role scheduling and communication.
X5 changes only the retrieval/context boundary by using the frozen
stage2.retrieval.retrieve implementation and corpus. No common X adapter is added.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from arena.providers import DeepSeekArenaProvider
from stage2.native_v7.software_host_v1 import ROLES, TASKS, SoftwareEngineeringHost
from stage2.native_v7.x5_rag.context import FrozenRAGContext

ROOT = Path(__file__).resolve().parents[3]
STAGE2 = ROOT / "stage2"


class RAGSoftwareEngineeringHost(SoftwareEngineeringHost):
    """The frozen host with one X5-specific context exposure hook."""

    def __init__(self, *, rag_context, **kwargs):
        super().__init__(**kwargs)
        self.rag_context = rag_context

    def _prompt(self, role, observations):
        messages = super()._prompt(role, observations)
        return self.rag_context.enrich(messages, role=role, task=self.task)


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


async def run_task(
    *,
    checkout,
    task_file,
    roles_file,
    subject_file,
    observer_root=None,
    provider=None,
):
    task, subject = _load_inputs(task_file, roles_file, subject_file)
    rag = FrozenRAGContext(observer_root=observer_root, limit=3)
    active_provider = provider if provider is not None else build_subject_provider(subject)
    host = RAGSoftwareEngineeringHost(
        rag_context=rag,
        task_id=task["id"],
        checkout=checkout,
        provider=active_provider,
        max_turns=int(subject["limits"]["max_turns"]),
    )
    try:
        result = await host.run()
    finally:
        rag.seal()
    result["retrieval_calls"] = rag.sequence
    result["last_retrieval_hits"] = [
        {"path": hit["path"], "sha256": hit["sha256"], "score": hit["score"]}
        for hit in rag.last_hits
    ]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--roles-file", required=True)
    parser.add_argument("--subject-file", required=True)
    parser.add_argument("--observer-root", required=True)
    args = parser.parse_args()
    result = asyncio.run(
        run_task(
            checkout=args.checkout,
            task_file=args.task_file,
            roles_file=args.roles_file,
            subject_file=args.subject_file,
            observer_root=args.observer_root,
        )
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
