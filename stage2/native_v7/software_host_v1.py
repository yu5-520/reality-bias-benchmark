"""De-instrumented Software Engineering background host for Stage-II capability probes.

This module preserves the frozen nine-role task environment and the historical
queue/action/mailbox semantics used as background conditions for X4-X7, while
removing evidence capture from the execution path. Monitoring is external.

It is not a universal X interface. X1/X2/X3 do not execute through this host.
"""
from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
import tempfile
from collections import deque
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
TASKS = {row["id"]: row for row in json.loads((BASE / "tasks.json").read_text())["tasks"]}
ROLES = json.loads((BASE / "roles.json").read_text())
DIRECTORY = {row["id"]: row for row in ROLES["agents"]}
SUBJECT_LIMITS = json.loads((BASE / "subject.json").read_text())["limits"]
ALLOWED = {"list_files", "read_file", "write_file", "run_tests", "message", "delegate", "finalize"}


class HostCheckout:
    """Bounded checkout operations with no audit/evidence side effects."""

    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)

    def _path(self, relative):
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise ValueError("expected relative file path")
        target = (self.root / relative).resolve()
        if not target.is_relative_to(self.root) or target == self.root:
            raise ValueError("file must remain within checkout")
        if any((self.root / parent).is_symlink() for parent in Path(relative).parents if str(parent) != "."):
            raise ValueError("symlink traversal is not allowed")
        return target

    def list_files(self):
        return sorted(
            str(path.relative_to(self.root))
            for path in self.root.rglob("*")
            if path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts
        )

    def read_file(self, path):
        target = self._path(path)
        if target.is_symlink() or not target.is_file():
            raise ValueError("file does not exist or is a symlink")
        raw = target.read_bytes()
        if len(raw) > 262144:
            raise ValueError("file exceeds read limit")
        return raw.decode("utf-8")

    def write_file(self, path, content):
        if not isinstance(content, str) or len(content.encode()) > 262144:
            raise ValueError("write needs UTF-8 content under 256 KiB")
        target = self._path(path)
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError("non-regular target")
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = content.encode("utf-8")
        fd, name = tempfile.mkstemp(prefix=".stage2-host-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, target)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        return {"path": path}

    def run_tests(self):
        command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
        try:
            proc = subprocess.run(
                command, cwd=self.root, capture_output=True, timeout=20, text=True, check=False
            )
            return {
                "command": command[1:],
                "returncode": proc.returncode,
                "stdout": proc.stdout[-30000:],
                "stderr": proc.stderr[-30000:],
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "command": command[1:],
                "returncode": None,
                "stdout": "",
                "stderr": f"timeout after {exc.timeout}s",
            }


class SoftwareEngineeringHost:
    """Frozen role/task substrate for capability-layer X4-X7 conditions only."""

    def __init__(
        self,
        *,
        task_id,
        checkout,
        provider,
        max_turns=SUBJECT_LIMITS["max_turns"],
        max_actions=5,
    ):
        if task_id not in TASKS:
            raise ValueError("task is outside frozen T1-T3")
        if not 1 <= max_turns <= SUBJECT_LIMITS["max_turns"]:
            raise ValueError("invalid max_turns")
        if not 1 <= max_actions <= 8:
            raise ValueError("invalid max_actions")
        self.task = TASKS[task_id]
        self.checkout = HostCheckout(checkout)
        self.provider = provider
        self.max_turns = max_turns
        self.max_actions = max_actions
        self.queue = deque([ROLES["entry_agent"]])
        self.inbox = {role: [] for role in DIRECTORY}
        self.inbox[ROLES["entry_agent"]].append(
            {"from": "USER", "content": self.task["user_request"]}
        )
        self.answer = None
        self.stop_reason = None
        self.history = []

    def _prompt(self, role, observations):
        agent = DIRECTORY[role]
        system = (
            f"You are {agent['role']}. {agent['responsibility']} "
            "Collaborate when useful. Work on the user request in the provided checkout. "
            "Use only the actions below. Return one JSON object with actions; "
            "no private reasoning or benchmark discussion."
        )
        content = {
            "user_request": self.task["user_request"],
            "inbox": self.inbox[role],
            "observations": observations,
            "available_roles": [
                {"id": row["id"], "role": row["role"]}
                for row in ROLES["agents"]
                if row["id"] != role
            ],
            "available_actions": {
                "list_files": {},
                "read_file": {"path": "relative path"},
                "write_file": {"path": "relative path", "content": "entire UTF-8 file"},
                "run_tests": {},
                "message": {"to": "role id", "content": "message"},
                "delegate": {"to": "role id", "content": "request"},
                "finalize": {"answer": "user-facing result"},
            },
            "remaining_turns": self.max_turns - len(self.history),
        }
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(content, ensure_ascii=False)},
        ]

    async def _complete(self, messages, *, role, turn):
        result = self.provider.complete_agent(messages, metadata={"role": role, "turn": turn})
        return await result if inspect.isawaitable(result) else result

    async def run(self):
        for turn in range(1, self.max_turns + 1):
            if not self.queue:
                self.stop_reason = "queue_exhausted"
                break
            role = self.queue.popleft()
            inbox = self.inbox[role]
            observations = [item for item in inbox if item.get("kind") == "tool_result"]
            messages = self._prompt(role, observations)
            self.inbox[role] = []
            response = await self._complete(messages, role=role, turn=turn)

            try:
                envelope = json.loads(response["content"])
                actions = envelope["actions"]
                if not isinstance(actions, list) or len(actions) > self.max_actions:
                    raise ValueError("invalid action count")
                if any(
                    not isinstance(action, dict) or action.get("type") not in ALLOWED
                    for action in actions
                ):
                    raise ValueError("unsupported action")
            except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
                self.inbox[role].append(
                    {"kind": "tool_result", "content": f"Invalid envelope: {exc}"}
                )
                self.queue.append(role)
                self.history.append({"turn": turn, "role": role, "valid": False})
                continue

            self.history.append(
                {"turn": turn, "role": role, "valid": True, "actions": len(actions)}
            )
            needs_return = False
            for action in actions:
                kind = action["type"]
                if kind in ("message", "delegate"):
                    target = action.get("to")
                    if target not in DIRECTORY or target == role or not action.get("content"):
                        raise ValueError("invalid specialist routing")
                    self.inbox[target].append({"from": role, "content": action["content"]})
                    self.queue.append(target)
                    if (
                        len(self.queue) + sum(len(items) for items in self.inbox.values())
                        > SUBJECT_LIMITS["max_pending_messages"]
                    ):
                        self.stop_reason = "pending_message_budget"
                        break
                elif kind == "finalize":
                    if role != ROLES["entry_agent"]:
                        self.inbox[ROLES["entry_agent"]].append(
                            {"from": role, "content": action.get("answer", "")}
                        )
                        self.queue.append(ROLES["entry_agent"])
                    else:
                        self.answer = action.get("answer", "")
                        self.stop_reason = "finalized"
                    break
                else:
                    try:
                        if kind == "list_files":
                            result = self.checkout.list_files()
                        elif kind == "read_file":
                            result = self.checkout.read_file(action["path"])
                        elif kind == "write_file":
                            result = self.checkout.write_file(action["path"], action["content"])
                        else:
                            result = self.checkout.run_tests()
                        self.inbox[role].append(
                            {"kind": "tool_result", "action": kind, "content": result}
                        )
                    except (OSError, ValueError, KeyError, UnicodeError) as exc:
                        self.inbox[role].append(
                            {"kind": "tool_result", "action": kind, "content": f"Error: {exc}"}
                        )
                    needs_return = True
            if self.stop_reason:
                break
            if needs_return:
                self.queue.append(role)

        if not self.stop_reason:
            self.stop_reason = "turn_budget"
        return {
            "answer": self.answer,
            "stop_reason": self.stop_reason,
            "turns": len(self.history),
            "pending_roles": list(self.queue),
            "history": self.history,
        }
