"""Non-study X5 RAG context-boundary smoke."""
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
from stage2.native_v7.x5_rag.runner import STAGE2, run_task


class RecordingScriptedProvider(ScriptedProvider):
    def __init__(self, scripted):
        super().__init__(scripted)
        self.prompts = []

    def complete_agent(self, messages, metadata=None):
        self.prompts.append(messages)
        return super().complete_agent(messages, metadata)


def _script():
    return [{"actions": [{"type": "finalize", "answer": "X5 RAG smoke complete."}]}]


def _digest(root):
    root = Path(root)
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            rows.append(
                f"{path.relative_to(root)}\0{hashlib.sha256(path.read_bytes()).hexdigest()}"
            )
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


async def smoke(destination):
    destination = Path(destination)
    direct_checkout = destination / "direct-checkout"
    rag_checkout = destination / "rag-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", direct_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", rag_checkout)

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
    observer_root = destination / "observer"
    rag_provider = RecordingScriptedProvider(_script())
    rag_result = await run_task(
        checkout=rag_checkout,
        task_file=task_file,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=observer_root,
        provider=rag_provider,
    )

    comparable_direct = {
        "answer": direct_result["answer"],
        "stop_reason": direct_result["stop_reason"],
        "turns": direct_result["turns"],
    }
    comparable_rag = {
        "answer": rag_result["answer"],
        "stop_reason": rag_result["stop_reason"],
        "turns": rag_result["turns"],
    }
    if comparable_direct != comparable_rag:
        raise RuntimeError(f"RAG context changed scripted host control result: {comparable_direct!r} != {comparable_rag!r}")
    if _digest(direct_checkout) != _digest(rag_checkout):
        raise RuntimeError("RAG context changed checkout effects under the scripted smoke")
    if rag_result["retrieval_calls"] != 1:
        raise RuntimeError(f"expected one retrieval exposure, observed {rag_result['retrieval_calls']}")

    prompt = json.loads(rag_provider.prompts[0][-1]["content"])
    hits = prompt.get("retrieved_context")
    if not isinstance(hits, list) or not hits:
        raise RuntimeError("frozen retrieval hits were not exposed to the model-visible context")
    if not all(hit.get("path") and len(hit.get("sha256", "")) == 64 for hit in hits):
        raise RuntimeError("retrieval hits lack frozen source paths or hashes")
    direct_prompt = json.loads(direct_provider.prompts[0][-1]["content"])
    if "retrieved_context" in direct_prompt:
        raise RuntimeError("baseline host unexpectedly contains X5 retrieval context")

    observer_files = verify_observer(observer_root)
    rows = [json.loads(line) for line in (observer_root / "events.jsonl").read_text().splitlines()]
    surfaces = [row["surface"] for row in rows]
    if surfaces != [
        "stage2.retrieval.retrieve.query.post_return_copy",
        "stage2.retrieval.retrieve.hits.post_return_copy",
    ]:
        raise RuntimeError(f"unexpected X5 observer surfaces: {surfaces!r}")

    report = {
        "schema": "stage2-v7-x5-rag-native-smoke-v1",
        "status": "NON_STUDY_X5_NATIVE_RAG_SMOKE_PASS",
        "task": "T3",
        "turns": comparable_rag["turns"],
        "stop_reason": comparable_rag["stop_reason"],
        "retrieval_calls": rag_result["retrieval_calls"],
        "hit_count": len(hits),
        "hit_paths": [hit["path"] for hit in hits],
        "observer_files": observer_files,
        "checkout_sha256": _digest(rag_checkout),
        "subject_ready": False,
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
