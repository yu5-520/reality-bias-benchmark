"""Non-study X2 MetaGPT-native Environment/Role scheduling smoke."""
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
from stage2.native_v7.x2_metagpt.runner import STAGE2, run_task


class RecordingScriptedProvider(ScriptedProvider):
    def __init__(self, scripted):
        super().__init__(scripted)
        self.prompts = []
        self.metadata = []

    def complete_agent(self, messages, metadata=None):
        self.prompts.append(messages)
        self.metadata.append(metadata)
        return super().complete_agent(messages, metadata)


def _script():
    return [
        {"actions": [{"type": "delegate", "to": "frontend", "content": "Inspect the checkout boundary."}]},
        {"actions": [{"type": "list_files"}]},
        {"actions": [{"type": "finalize", "answer": "Frontend inspection completed."}]},
        {"actions": [{"type": "delegate", "to": "qa", "content": "Run the frozen tests and report."}]},
        {"actions": [{"type": "run_tests"}]},
        {"actions": [{"type": "finalize", "answer": "Frozen tests completed."}]},
        {"actions": [{"type": "finalize", "answer": "X2 MetaGPT smoke complete."}]},
    ]


def _digest(root):
    root = Path(root)
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            rows.append(f"{path.relative_to(root)}\0{hashlib.sha256(path.read_bytes()).hexdigest()}")
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


async def smoke(destination):
    destination = Path(destination)
    direct_checkout = destination / "direct-checkout"
    meta_checkout = destination / "metagpt-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", direct_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", meta_checkout)

    direct = SoftwareEngineeringHost(
        task_id="T2", checkout=direct_checkout, provider=ScriptedProvider(_script())
    )
    direct_result = await direct.run()

    task = next(
        row for row in json.loads((STAGE2 / "tasks.json").read_text())["tasks"] if row["id"] == "T2"
    )
    task_file = destination / "task.json"
    task_file.write_text(json.dumps(task, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    observer_root = destination / "observer"
    provider = RecordingScriptedProvider(_script())
    meta_result = await run_task(
        checkout=meta_checkout,
        task_file=task_file,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=observer_root,
        provider=provider,
    )

    comparable_direct = {
        "answer": direct_result["answer"],
        "stop_reason": direct_result["stop_reason"],
        "turns": direct_result["turns"],
    }
    comparable_meta = {
        "answer": meta_result["answer"],
        "stop_reason": meta_result["stop_reason"],
        "turns": meta_result["turns"],
    }
    if comparable_direct != comparable_meta:
        raise RuntimeError(
            f"MetaGPT native environment changed scripted control result: "
            f"{comparable_direct!r} != {comparable_meta!r}"
        )
    if _digest(direct_checkout) != _digest(meta_checkout):
        raise RuntimeError("MetaGPT native environment changed scripted checkout effects")

    expected_roles = [
        "release_lead", "frontend", "frontend", "release_lead", "qa", "qa", "release_lead"
    ]
    observed_roles = [row["role"] for row in meta_result["history"]]
    if observed_roles != expected_roles:
        raise RuntimeError(f"unexpected MetaGPT native role schedule: {observed_roles!r}")
    if meta_result["metagpt_rounds"] != 7:
        raise RuntimeError(f"expected seven MetaGPT Environment rounds, got {meta_result['metagpt_rounds']}")
    # MetaGPT's native Role.publish_message routes self-addressed tool feedback
    # directly into that Role's msg_buffer rather than through Environment.history.
    # The six cross-role/user/terminal messages belong in Environment.history; the
    # two self tool-feedback messages are checked through Role memory below.
    if meta_result["environment_messages"] != 6:
        raise RuntimeError(
            f"expected six MetaGPT Environment-routed messages, got "
            f"{meta_result['environment_messages']}"
        )

    second_prompt = json.loads(provider.prompts[1][-1]["content"])
    if not second_prompt["inbox"] or second_prompt["inbox"][0]["from"] != "release_lead":
        raise RuntimeError("frontend did not receive release_lead through MetaGPT native routing")
    fifth_prompt = json.loads(provider.prompts[4][-1]["content"])
    if not fifth_prompt["inbox"] or fifth_prompt["inbox"][0]["from"] != "release_lead":
        raise RuntimeError("qa did not receive release_lead through MetaGPT native routing")

    observer_files = verify_observer(observer_root)
    rows = [json.loads(line) for line in (observer_root / "events.jsonl").read_text().splitlines()]
    surfaces = [row["surface"] for row in rows]
    if "metagpt.Environment.history.post_round_copy" not in surfaces:
        raise RuntimeError("external observer did not copy MetaGPT Environment history")
    if not any(surface.startswith("metagpt.Role.memory.") for surface in surfaces):
        raise RuntimeError("external observer did not copy MetaGPT Role memory")

    report = {
        "schema": "stage2-v7-x2-metagpt-native-smoke-v1",
        "status": "NON_STUDY_X2_NATIVE_METAGPT_SMOKE_PASS",
        "task": "T2",
        "turns": meta_result["turns"],
        "metagpt_rounds": meta_result["metagpt_rounds"],
        "environment_messages": meta_result["environment_messages"],
        "observer_files": observer_files,
        "checkout_sha256": _digest(meta_checkout),
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
