"""Non-study X1 AutoGen-native runner/observer smoke."""
from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import tempfile
from pathlib import Path

from autogen_core import FunctionCall
from autogen_core.models import CreateResult, RequestUsage
from autogen_ext.models.replay import ReplayChatCompletionClient

from stage2.native_v7.observer import PassiveEventObserver, verify_observer
from stage2.native_v7.x1_autogen.runner import FINAL_MARKER, run_task


ROOT = Path(__file__).resolve().parents[3]
STAGE2 = ROOT / "stage2"


def _call(name, call_id, arguments):
    return CreateResult(
        finish_reason="function_calls",
        content=[
            FunctionCall(
                id=call_id,
                name=name,
                arguments=json.dumps(arguments, ensure_ascii=False, sort_keys=True),
            )
        ],
        usage=RequestUsage(prompt_tokens=1, completion_tokens=1),
        cached=True,
    )


def _client():
    return ReplayChatCompletionClient(
        [
            _call("transfer_to_frontend", "handoff-1", {}),
            _call("read_file", "read-1", {"path": "README.md"}),
            _call(
                "write_file",
                "write-1",
                {"path": "SMOKE_X1.txt", "content": "AutoGen native runner smoke\n"},
            ),
            _call("run_tests", "tests-1", {}),
            _call("transfer_to_release_lead", "handoff-2", {}),
            f"{FINAL_MARKER}: native AutoGen smoke complete",
        ],
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": "unknown",
            "structured_output": False,
        },
    )


async def smoke(destination: Path):
    checkout = destination / "checkout"
    shutil.copytree(STAGE2 / "fixtures/project", checkout)
    observer = destination / "observer"
    all_tasks = json.loads((STAGE2 / "tasks.json").read_text())["tasks"]
    task_file = destination / "task.json"
    task_file.write_text(
        json.dumps(next(row for row in all_tasks if row["id"] == "T2"), ensure_ascii=False, indent=2) + "\n"
    )
    result = await run_task(
        checkout=checkout,
        task_file=task_file,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=observer,
        model_client=_client(),
    )
    marker = checkout / "SMOKE_X1.txt"
    if marker.read_text() != "AutoGen native runner smoke\n":
        raise RuntimeError("AutoGen native tool path did not modify the isolated checkout")
    if FINAL_MARKER not in str(result.get("answer")):
        raise RuntimeError("AutoGen native Swarm did not return through the frozen entry role")
    if verify_observer(observer) < 3:
        raise RuntimeError("AutoGen passive observer captured too little native stream evidence")

    probe_root = destination / "observer-contract"
    tee = PassiveEventObserver(probe_root, probe="X1")
    raw = b'{"native":"autogen-event"}'
    preserved = tee.observe(raw, surface="contract-smoke")
    if preserved is not raw or preserved != raw:
        raise RuntimeError("observer changed event identity or bytes")
    tee.seal()
    verify_observer(probe_root)
    return {
        "status": "NON_STUDY_X1_NATIVE_RUNNER_SMOKE_PASS",
        "native_events": result["native_events"],
        "messages": result["messages"],
        "stop_reason": result["stop_reason"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root")
    args = parser.parse_args()
    if args.out_root:
        destination = Path(args.out_root)
        destination.mkdir(parents=True, exist_ok=False)
        result = asyncio.run(smoke(destination))
    else:
        with tempfile.TemporaryDirectory() as directory:
            result = asyncio.run(smoke(Path(directory)))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
