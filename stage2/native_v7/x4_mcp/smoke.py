"""Non-study X4 MCP attachment smoke against the frozen de-instrumented host."""
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
from stage2.native_v7.x4_mcp.runner import ROOT, STAGE2, run_task

ACTIONS = [
    {"type": "delegate", "to": "frontend", "content": "Inspect the checkout page boundary."},
    {"type": "list_files"},
    {"type": "read_file", "path": "README.md"},
    {
        "type": "write_file",
        "path": "X4_MCP_SMOKE.txt",
        "content": "official MCP stdio attachment\n",
    },
    {"type": "run_tests"},
    {"type": "finalize", "answer": "Frontend MCP work completed."},
    {"type": "finalize", "answer": "X4 MCP smoke complete."},
]


def _script():
    return [{"actions": [action]} for action in ACTIONS]


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
    mcp_checkout = destination / "mcp-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", direct_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", mcp_checkout)

    direct = SoftwareEngineeringHost(
        task_id="T2", checkout=direct_checkout, provider=ScriptedProvider(_script())
    )
    direct_result = await direct.run()

    task = next(row for row in json.loads((STAGE2 / "tasks.json").read_text())["tasks"] if row["id"] == "T2")
    task_file = destination / "task.json"
    task_file.write_text(json.dumps(task, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    observer_root = destination / "observer"
    mcp_result = await run_task(
        checkout=mcp_checkout,
        task_file=task_file,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=observer_root,
        provider=ScriptedProvider(_script()),
    )

    comparable_direct = {
        "answer": direct_result["answer"],
        "stop_reason": direct_result["stop_reason"],
        "turns": direct_result["turns"],
    }
    comparable_mcp = {
        "answer": mcp_result["answer"],
        "stop_reason": mcp_result["stop_reason"],
        "turns": mcp_result["turns"],
    }
    if comparable_direct != comparable_mcp:
        raise RuntimeError(f"MCP attachment changed host control semantics: {comparable_direct!r} != {comparable_mcp!r}")
    if _digest(direct_checkout) != _digest(mcp_checkout):
        raise RuntimeError("MCP attachment changed checkout effects relative to the frozen host")
    if mcp_result["mcp_calls"] != 4:
        raise RuntimeError(f"expected four MCP tool calls, observed {mcp_result['mcp_calls']}")

    c2s = sorted(observer_root.glob("*.client_to_server.bin"))
    s2c = sorted(observer_root.glob("*.server_to_client.bin"))
    if len(c2s) != 4 or len(s2c) != 4:
        raise RuntimeError("MCP wire observer did not preserve one bidirectional capture per host tool call")
    c2s_bytes = b"".join(path.read_bytes() for path in c2s)
    s2c_bytes = b"".join(path.read_bytes() for path in s2c)
    if b"tools/call" not in c2s_bytes or not s2c_bytes:
        raise RuntimeError("MCP stdio wire capture does not contain native tool protocol traffic")

    marker = mcp_checkout / "X4_MCP_SMOKE.txt"
    if marker.read_text() != "official MCP stdio attachment\n":
        raise RuntimeError("MCP tool server did not preserve the scripted checkout write")

    report = {
        "schema": "stage2-v7-x4-mcp-native-smoke-v1",
        "status": "NON_STUDY_X4_NATIVE_MCP_SMOKE_PASS",
        "task": "T2",
        "turns": comparable_mcp["turns"],
        "stop_reason": comparable_mcp["stop_reason"],
        "mcp_calls": mcp_result["mcp_calls"],
        "client_to_server_captures": len(c2s),
        "server_to_client_captures": len(s2c),
        "checkout_sha256": _digest(mcp_checkout),
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
