"""Scripted, non-study coding smoke through exact v6.4 target SDK checkouts.

The scripted agent deliberately does not solve T2; it verifies that the same
role/action route reaches each architecture and preserves original evidence.
"""
import argparse
import asyncio
import importlib.metadata
import json
import subprocess
from pathlib import Path

from arena.providers import ScriptedProvider

from .coding_arena import CodingArena
from .evidence import NativeCapture, check_capture
from .freeze import BASE
from .rag_context import RAGContext
from .transports import AutoGenTransport, RoleMailboxTransport
from .workspace import new_workspace

SUPPORTED = {"X1", "X3", "X4", "X5"}


def frozen_target(probe, upstream=None):
    if probe not in SUPPORTED:
        raise ValueError("coding smoke only covers the four bound native paths")
    target = json.loads((BASE / "runtime_bindings.json").read_text())["probes"][probe]
    if probe != "X5":
        if upstream is None:
            raise ValueError("exact upstream SDK checkout is required")
        resolved = subprocess.check_output(["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True).strip()
        expected = target.get("sdk_commit") or target.get("source_commit")
        if resolved != expected:
            raise ValueError(f"{probe}: installed SDK checkout differs from frozen target")
    return target


async def run_smoke(probe, destination, *, code_commit, upstream=None):
    target = frozen_target(probe, upstream)
    destination = Path(destination)
    checkout = new_workspace(destination / "checkout")
    package = {"X1": "autogen-core", "X3": "a2a-sdk", "X4": "mcp"}.get(probe)
    binding = {"probe": probe, "code_commit": code_commit,
               "source_commit": target.get("source_commit") or target.get("protocol_commit") or code_commit,
               "sdk_commit": target.get("sdk_commit"), "native_hook": target["hook_id"],
               "protocol_version": target.get("protocol_version"),
               "implementation_sha256": target.get("implementation_sha256"),
               "installed_version": importlib.metadata.version(package) if package else "in-repo",
               "provider": "SCRIPTED_ENGINEERING_ONLY"}
    capture = NativeCapture(destination / "evidence", probe, f"{probe}-TARGET_CODING_SMOKE", binding)
    index = (BASE / "fixtures/project/web/index.html").read_text()
    edited = index.replace('<p id="result"', '<button id="smoke-payment" disabled>Smoke only</button><p id="result"')
    if edited == index:
        raise RuntimeError("frozen checkout edit anchor missing")
    actions = [
        {"type": "delegate", "to": "frontend", "content": "Inspect the checkout page boundary."},
        {"type": "read_file", "path": "README.md"},
        {"type": "read_file", "path": "web/index.html"},
        {"type": "write_file", "path": "web/index.html", "content": edited},
        {"type": "run_tests"},
        {"type": "finalize", "answer": "Engineering boundary exercised."},
        {"type": "finalize", "answer": "Engineering smoke ended."},
    ]
    local_actions = [actions[0], actions[-1]] if probe == "X3" else actions
    provider = ScriptedProvider([{"actions": [action]} for action in local_actions])
    transport = AutoGenTransport(capture) if probe == "X1" else None
    workspace = None
    context = None
    if probe == "X3":
        from .a2a_transport import A2AProtocolTransport
        transport = A2AProtocolTransport(capture, remote_mode="scripted", remote_actions=actions[1:-1])
    elif probe != "X1":
        transport = RoleMailboxTransport(capture)
    if probe == "X4":
        from .mcp_workspace import MCPWorkspace
        workspace = MCPWorkspace(checkout, capture)
    elif probe == "X5":
        context = RAGContext(capture)
    arena = CodingArena(task_id="T2", checkout=checkout, capture=capture, transport=transport,
                        workspace=workspace, context_adapter=context, provider=provider)
    result = await arena.run()
    if (result["stop_reason"] != "finalized" or result["turns"] != len(actions)
            or provider.index != len(local_actions)):
        raise RuntimeError("target-bound coding route did not finish its scripted steps")
    count = check_capture(destination / "evidence")
    operations = {event["operation"] for event in capture.events}
    required = {"model_input", "model_output", "file_change", "test_run", "termination"}
    if probe != "X4":
        required.add("file_read")
    required |= {"delegate", "receive_message"} if probe == "X1" else set()
    required |= {"remote_task", "artifact_return"} if probe == "X3" else set()
    required |= {"resource_read", "tool_call"} if probe == "X4" else set()
    required |= {"retrieve"} if probe == "X5" else set()
    if not required <= operations:
        raise RuntimeError(f"{probe}: native coding operation set incomplete: {required - operations}")
    if probe == "X3" and len([row for row in capture.events if row["hook_id"] == "a2a.native.remote_model"
                              and row["operation"] == "model_output"]) != len(actions) - 2:
        raise RuntimeError("remote specialist model decisions were not executed across A2A")
    report = {"probe": probe, "status": "NON_STUDY_TARGET_CODING_SMOKE_PASS",
              "code_commit": code_commit, "target_sdk_commit": target.get("sdk_commit") or target.get("source_commit"),
              "events": count, "turns": result["turns"], "operations": sorted(operations),
              "subject_ready": False, "provider": "SCRIPTED_ENGINEERING_ONLY",
              "remote_execution": "SCRIPTED_REMOTE_ONLY" if probe == "X3" else None}
    (destination / "report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", required=True, choices=sorted(SUPPORTED))
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--upstream")
    args = parser.parse_args()
    result = asyncio.run(run_smoke(args.probe, Path(args.out_root) / args.probe,
                                   code_commit=args.code_commit, upstream=args.upstream))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
