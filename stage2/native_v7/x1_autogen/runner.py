"""X1 AutoGen-native Stage-II runner.

This runner uses the frozen AutoGen AgentChat primitives directly. It does not
import the historical Stage-II CodingArena or any shared transport/context
adapter. The host supplies only the frozen scientific inputs and checkout tools.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Handoff
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import Swarm
from autogen_ext.models.openai import OpenAIChatCompletionClient

from stage2.native_v7.observer import PassiveEventObserver, native_bytes


FINAL_MARKER = "STAGE2_FINAL"


class CheckoutTools:
    """Host-side checkout tools exposed to AutoGen agents without a shared X adapter."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve(strict=True)

    def _path(self, relative: str) -> Path:
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise ValueError("expected a relative checkout path")
        target = (self.root / relative).resolve()
        if not target.is_relative_to(self.root) or target == self.root:
            raise ValueError("path must remain inside checkout")
        return target

    def list_files(self) -> list[str]:
        """List regular checkout files visible to the coding team."""
        return sorted(
            str(path.relative_to(self.root))
            for path in self.root.rglob("*")
            if path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts
        )

    def read_file(self, path: str) -> str:
        """Read one UTF-8 checkout file by relative path."""
        target = self._path(path)
        if target.is_symlink() or not target.is_file():
            raise ValueError("file does not exist or is a symlink")
        raw = target.read_bytes()
        if len(raw) > 262144:
            raise ValueError("file exceeds 256 KiB read limit")
        return raw.decode("utf-8")

    def write_file(self, path: str, content: str) -> str:
        """Replace one UTF-8 checkout file atomically and return its relative path."""
        if not isinstance(content, str) or len(content.encode("utf-8")) > 262144:
            raise ValueError("write content exceeds 256 KiB")
        target = self._path(path)
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError("target must be a regular checkout file")
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".stage2-v7-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(content.encode("utf-8"))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp, target)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        return str(target.relative_to(self.root))

    def run_tests(self) -> str:
        """Run the frozen checkout unit-test command and return its captured result."""
        command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
        try:
            proc = subprocess.run(
                command, cwd=self.root, capture_output=True, text=True, timeout=20, check=False
            )
            payload = {
                "returncode": proc.returncode,
                "stdout": proc.stdout[-30000:],
                "stderr": proc.stderr[-30000:],
            }
        except subprocess.TimeoutExpired as exc:
            payload = {"returncode": None, "stdout": "", "stderr": f"timeout after {exc.timeout}s"}
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _load_inputs(task_file: str | Path, roles_file: str | Path, subject_file: str | Path):
    task = json.loads(Path(task_file).read_text())
    roles = json.loads(Path(roles_file).read_text())
    subject = json.loads(Path(subject_file).read_text())
    if not isinstance(task, dict) or not task.get("user_request"):
        raise ValueError("task file must contain one frozen task object")
    if len(roles.get("agents", [])) != 9 or roles.get("entry_agent") not in {
        row.get("id") for row in roles.get("agents", [])
    }:
        raise ValueError("roles file must contain the frozen nine-role roster")
    return task, roles, subject


def build_deepseek_client(subject: dict):
    """Build the official AutoGen OpenAI-compatible client for the frozen DeepSeek endpoint."""
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY is required for X1 natural execution")
    source = Path(__file__).resolve().parents[3] / subject["source_config"]
    config = json.loads(source.read_text())
    if (
        config["provider"] != subject["provider"]
        or config["model_alias"] != subject["model_alias"]
        or config["expected_model_version"] != subject["expected_model_version"]
        or config["subject"] != subject["subject"]
    ):
        raise ValueError("live DeepSeek configuration differs from frozen subject")
    model_info = {
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "family": "unknown",
        "structured_output": False,
    }
    return OpenAIChatCompletionClient(
        model=config["model_alias"],
        base_url=config["base_url"],
        api_key=key,
        max_tokens=int(config["subject"]["max_tokens"]),
        temperature=float(config["subject"]["temperature"]),
        extra_body={"thinking": {"type": config["subject"]["thinking"]}},
        timeout=float(config["transport"]["timeout_seconds"]),
        max_retries=int(config["transport"]["max_retries"]),
        model_info=model_info,
    )


def build_team(*, model_client, roles: dict, checkout: str | Path, max_turns: int):
    tools = CheckoutTools(checkout)
    agents = []
    roster = roles["agents"]
    entry = roles["entry_agent"]
    for row in roster:
        pid = row["id"]
        handoffs = [
            Handoff(
                target=other["id"],
                description=f"Hand off to {other['role']} when that responsibility is useful.",
            )
            for other in roster
            if other["id"] != pid
        ]
        finish_rule = (
            f"When the requested work is actually complete, return a concise user-facing answer containing "
            f"{FINAL_MARKER}. Only you may use that marker."
            if pid == entry
            else f"Do not use {FINAL_MARKER}. Hand control back to {entry} when your contribution is complete."
        )
        system = (
            f"You are {row['role']}. {row['responsibility']} "
            "Work naturally on the user's software-engineering request in the provided checkout. "
            "Use the checkout tools when useful. Hand off to another listed role when their responsibility "
            "would materially help. Do not discuss the experiment or auditing machinery. "
            + finish_rule
        )
        agents.append(
            AssistantAgent(
                name=pid,
                description=f"{row['role']}: {row['responsibility']}",
                model_client=model_client,
                tools=[tools.list_files, tools.read_file, tools.write_file, tools.run_tests],
                handoffs=handoffs,
                system_message=system,
                reflect_on_tool_use=False,
                max_tool_iterations=1,
            )
        )
    if agents[0].name != entry:
        by_name = {agent.name: agent for agent in agents}
        agents = [by_name[entry], *[agent for agent in agents if agent.name != entry]]
    termination = TextMentionTermination(FINAL_MARKER)
    return Swarm(
        participants=agents,
        termination_condition=termination,
        max_turns=max_turns,
        emit_team_events=True,
    )


async def run_task(
    *,
    checkout: str | Path,
    task_file: str | Path,
    roles_file: str | Path,
    subject_file: str | Path,
    observer_root: str | Path | None = None,
    model_client=None,
):
    task, roles, subject = _load_inputs(task_file, roles_file, subject_file)
    own_client = model_client is None
    client = build_deepseek_client(subject) if own_client else model_client
    max_turns = int(subject["limits"]["max_turns"])
    team = build_team(model_client=client, roles=roles, checkout=checkout, max_turns=max_turns)
    observer = PassiveEventObserver(observer_root, probe="X1") if observer_root else None

    native_events = []
    final = None
    try:
        async for item in team.run_stream(task=task["user_request"]):
            raw = native_bytes(item)
            if observer is not None:
                preserved = observer.observe(raw, surface="autogen_agentchat.run_stream")
                if preserved != raw:
                    raise RuntimeError("observer altered AutoGen event bytes")
            native_events.append(raw)
            if hasattr(item, "stop_reason"):
                final = item
    finally:
        if observer is not None:
            observer.seal()
        if own_client:
            await client.close()

    if final is None:
        raise RuntimeError("AutoGen Swarm did not emit a terminal TaskResult")
    return {
        "stop_reason": getattr(final, "stop_reason", None),
        "messages": len(getattr(final, "messages", []) or []),
        "native_events": len(native_events),
        "answer": (
            getattr(getattr(final, "messages", [None])[-1], "content", None)
            if getattr(final, "messages", None)
            else None
        ),
    }


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
