"""Non-study X3 nine-role A2A native service smoke."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from arena.providers import ScriptedProvider
from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost
from stage2.native_v7.x3_a2a.runner import ROLES, STAGE2, run_task


ROLE_SCRIPT = {
    "release_lead": [
        {"actions": [{"type": "delegate", "to": "frontend", "content": "Inspect the checkout page boundary."}]},
        {"actions": [{"type": "delegate", "to": "qa", "content": "Run the frozen tests and report."}]},
        {"actions": [{"type": "finalize", "answer": "X3 A2A smoke complete."}]},
    ],
    "frontend": [
        {"actions": [{"type": "list_files"}]},
        {"actions": [{"type": "finalize", "answer": "Frontend inspection completed."}]},
    ],
    "qa": [
        {"actions": [{"type": "run_tests"}]},
        {"actions": [{"type": "finalize", "answer": "Frozen tests completed."}]},
    ],
}


def _flat_script():
    return [
        ROLE_SCRIPT["release_lead"][0],
        ROLE_SCRIPT["frontend"][0],
        ROLE_SCRIPT["frontend"][1],
        ROLE_SCRIPT["release_lead"][1],
        ROLE_SCRIPT["qa"][0],
        ROLE_SCRIPT["qa"][1],
        ROLE_SCRIPT["release_lead"][2],
    ]


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
    a2a_checkout = destination / "a2a-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", direct_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", a2a_checkout)

    direct = SoftwareEngineeringHost(
        task_id="T2",
        checkout=direct_checkout,
        provider=ScriptedProvider(_flat_script()),
    )
    direct_result = await direct.run()

    task = next(
        row for row in json.loads((STAGE2 / "tasks.json").read_text())["tasks"] if row["id"] == "T2"
    )
    task_file = destination / "task.json"
    task_file.write_text(json.dumps(task, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    script_file = destination / "role-script.json"
    # Unused roles still receive a fail-closed one-item finalize script because each service
    # must construct its own provider even when the smoke never routes to that role.
    script = dict(ROLE_SCRIPT)
    for role in [row["id"] for row in ROLES["agents"]]:
        script.setdefault(role, [{"actions": [{"type": "finalize", "answer": f"{role} unused"}]}])
    script_file.write_text(json.dumps(script, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    observer_root = destination / "observer"
    a2a_result = await run_task(
        checkout=a2a_checkout,
        task_file=task_file,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=observer_root,
        mode="scripted",
        script_file=script_file,
    )

    comparable_direct = {
        "answer": direct_result["answer"],
        "stop_reason": direct_result["stop_reason"],
        "turns": direct_result["turns"],
    }
    comparable_a2a = {
        "answer": a2a_result["answer"],
        "stop_reason": a2a_result["stop_reason"],
        "turns": a2a_result["turns_used"],
    }
    if comparable_direct != comparable_a2a:
        raise RuntimeError(
            f"A2A native service graph changed scripted control result: "
            f"{comparable_direct!r} != {comparable_a2a!r}"
        )
    if _digest(direct_checkout) != _digest(a2a_checkout):
        raise RuntimeError("A2A native service graph changed scripted checkout effects")
    if a2a_result["service_count"] != 9:
        raise RuntimeError("X3 did not expose all nine frozen roles as services")
    if a2a_result["a2a_calls"] != 3:
        raise RuntimeError(f"expected three A2A task calls, observed {a2a_result['a2a_calls']}")

    trace_roles = [row["role"] for row in a2a_result["trace"]]
    if trace_roles != [
        "release_lead", "frontend", "frontend", "release_lead", "qa", "qa", "release_lead"
    ]:
        raise RuntimeError(f"unexpected A2A role execution trace: {trace_roles!r}")

    post_requests = sorted((observer_root / "wire").rglob("*-post-request.bin"))
    post_responses = sorted((observer_root / "wire").rglob("*-post-response.bin"))
    if len(post_requests) != 3 or len(post_responses) != 3:
        raise RuntimeError(
            f"expected three captured JSON-RPC exchanges, got "
            f"{len(post_requests)} requests/{len(post_responses)} responses"
        )
    request_bytes = b"".join(path.read_bytes() for path in post_requests)
    response_bytes = b"".join(path.read_bytes() for path in post_responses)
    if b"SendMessage" not in request_bytes or b"task" not in response_bytes:
        raise RuntimeError("captured A2A v1.0 JSON-RPC bodies do not contain native SendMessage/task traffic")

    cards = sorted((observer_root / "wire").rglob("*-get-response.bin"))
    if len(cards) < 9:
        raise RuntimeError("not all nine A2A Agent Cards were observed externally")

    report = {
        "schema": "stage2-v7-x3-a2a-native-smoke-v1",
        "status": "NON_STUDY_X3_NATIVE_A2A_SMOKE_PASS",
        "task": "T2",
        "turns": a2a_result["turns_used"],
        "stop_reason": a2a_result["stop_reason"],
        "service_count": a2a_result["service_count"],
        "a2a_calls": a2a_result["a2a_calls"],
        "jsonrpc_request_captures": len(post_requests),
        "jsonrpc_response_captures": len(post_responses),
        "agent_card_captures": len(cards),
        "checkout_sha256": _digest(a2a_checkout),
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
