"""X4 runner: frozen Software Engineering host with official MCP stdio tools.

MCP owns the tool/resource protocol boundary only. The explicitly frozen
software_engineering_host_v1 continues to own role scheduling and communication.
No MCP implementation source is modified and no experiment-wide X adapter is used.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

from arena.providers import DeepSeekArenaProvider
from stage2.native_v7.software_host_v1 import ROLES, TASKS, SoftwareEngineeringHost

ROOT = Path(__file__).resolve().parents[3]
STAGE2 = ROOT / "stage2"


class MCPCheckoutProxy:
    """Probe-specific host attachment that crosses the official MCP stdio boundary."""

    def __init__(self, checkout, observer_root=None):
        self.checkout = str(Path(checkout).resolve(strict=True))
        self.observer_root = str(Path(observer_root).resolve()) if observer_root else None
        self.sequence = 0

    def _invoke(self, tool, arguments):
        self.sequence += 1
        prefix = f"{self.sequence:04d}-{tool}"
        command = [
            sys.executable,
            "-m",
            "stage2.native_v7.x4_mcp.client_call",
            "--checkout",
            self.checkout,
            "--tool",
            tool,
            "--arguments-json",
            json.dumps(arguments, ensure_ascii=False, sort_keys=True),
            "--capture-prefix",
            prefix,
        ]
        if self.observer_root:
            command += ["--observer-root", self.observer_root]
        proc = subprocess.run(command, capture_output=True, text=True, check=False, timeout=60)
        if proc.returncode != 0:
            raise RuntimeError(
                f"MCP {tool} call failed with {proc.returncode}: {proc.stderr[-4000:]}"
            )
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"MCP {tool} client returned non-JSON stdout") from exc
        if payload.get("tool") != tool:
            raise RuntimeError("MCP client result does not match requested tool")
        return payload.get("result")

    def list_files(self):
        return self._invoke("list_files", {})

    def read_file(self, path):
        return self._invoke("read_file", {"path": path})

    def write_file(self, path, content):
        return self._invoke("write_file", {"path": path, "content": content})

    def run_tests(self):
        return self._invoke("run_tests", {})


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
    active_provider = provider if provider is not None else build_subject_provider(subject)
    host = SoftwareEngineeringHost(
        task_id=task["id"],
        checkout=checkout,
        provider=active_provider,
        max_turns=int(subject["limits"]["max_turns"]),
    )
    host.checkout = MCPCheckoutProxy(checkout, observer_root=observer_root)
    result = await host.run()
    result["mcp_calls"] = host.checkout.sequence
    if observer_root:
        root = Path(observer_root)
        result["mcp_wire_files"] = len(list(root.glob("*.bin"))) if root.exists() else 0
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
