"""Non-study equivalence smoke for the de-instrumented Software Engineering host."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from arena.providers import ScriptedProvider
from stage2.coding_arena import CodingArena
from stage2.evidence import NativeCapture
from stage2.freeze import BASE as STAGE2_BASE
from stage2.transports import RoleMailboxTransport
from stage2.workspace import new_workspace

from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost


ACTIONS = [
    {"type": "delegate", "to": "frontend", "content": "Inspect the checkout page boundary."},
    {"type": "read_file", "path": "README.md"},
    {
        "type": "write_file",
        "path": "HOST_EQUIVALENCE.txt",
        "content": "software-engineering-host-v1\n",
    },
    {"type": "run_tests"},
    {"type": "finalize", "answer": "Frontend work completed."},
    {"type": "finalize", "answer": "Host equivalence smoke complete."},
]


class RecordingScriptedProvider(ScriptedProvider):
    def __init__(self, scripted):
        super().__init__(scripted)
        self.prompts = []

    def complete_agent(self, messages, metadata=None):
        self.prompts.append(messages)
        return super().complete_agent(messages, metadata)


def _script():
    return [{"actions": [action]} for action in ACTIONS]


def _tree_digest(root):
    root = Path(root)
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            rows.append(
                f"{path.relative_to(root)}\0{hashlib.sha256(path.read_bytes()).hexdigest()}"
            )
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


async def compare(destination):
    destination = Path(destination)
    old_root = destination / "historical"
    new_root = destination / "deinstrumented"

    old_checkout = new_workspace(old_root / "checkout")
    old_provider = RecordingScriptedProvider(_script())
    capture = NativeCapture(
        old_root / "evidence",
        "X5",
        "HOST-EQUIVALENCE-HISTORICAL",
        {
            "probe": "X5",
            "source_commit": "historical-stage2-host",
            "code_commit": "non-study-equivalence",
        },
    )
    old_host = CodingArena(
        task_id="T2",
        checkout=old_checkout,
        capture=capture,
        transport=RoleMailboxTransport(capture),
        provider=old_provider,
    )
    old_result = await old_host.run()

    new_checkout = new_root / "checkout"
    shutil.copytree(STAGE2_BASE / "fixtures/project", new_checkout)
    new_provider = RecordingScriptedProvider(_script())
    new_host = SoftwareEngineeringHost(
        task_id="T2",
        checkout=new_checkout,
        provider=new_provider,
    )
    new_result = await new_host.run()

    comparable_old = {
        "answer": old_result["answer"],
        "stop_reason": old_result["stop_reason"],
        "turns": old_result["turns"],
    }
    comparable_new = {
        "answer": new_result["answer"],
        "stop_reason": new_result["stop_reason"],
        "turns": new_result["turns"],
    }
    if comparable_old != comparable_new:
        raise RuntimeError(
            f"de-instrumented host changed scripted control-flow result: "
            f"{comparable_old!r} != {comparable_new!r}"
        )
    if _tree_digest(old_checkout) != _tree_digest(new_checkout):
        raise RuntimeError("de-instrumented host changed scripted checkout effects")

    prompt_text = json.dumps(new_provider.prompts, ensure_ascii=False, sort_keys=True)
    for marker in ("event_id", "native_locator", "hook_id", "record_hash", "semantic_assessment"):
        if marker in prompt_text:
            raise RuntimeError(f"monitor/audit marker leaked into de-instrumented host prompt: {marker}")

    report = {
        "schema": "stage2-v7-software-host-equivalence-v1",
        "status": "NON_STUDY_DEINSTRUMENTED_HOST_EQUIVALENCE_PASS",
        "task": "T2",
        "turns": comparable_new["turns"],
        "stop_reason": comparable_new["stop_reason"],
        "checkout_sha256": _tree_digest(new_checkout),
        "historical_prompt_contains_audit_ids": (
            "event_id" in json.dumps(old_provider.prompts, ensure_ascii=False, sort_keys=True)
        ),
        "deinstrumented_prompt_contains_audit_ids": False,
    }
    destination.mkdir(parents=True, exist_ok=True)
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
        result = asyncio.run(compare(root))
    else:
        with tempfile.TemporaryDirectory() as directory:
            result = asyncio.run(compare(Path(directory)))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
