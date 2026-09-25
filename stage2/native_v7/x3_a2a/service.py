"""One frozen Software Engineering role exposed as an official A2A v1.0 service."""
from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import os
from pathlib import Path

from arena.providers import DeepSeekArenaProvider, ScriptedProvider
from stage2.native_v7.action_contract import apply_model_visible_action_contract
from stage2.native_v7.x3_a2a.checkout import A2ACheckout

ROOT = Path(__file__).resolve().parents[3]
STAGE2 = ROOT / "stage2"
ROLES = json.loads((STAGE2 / "roles.json").read_text())
DIRECTORY = {row["id"]: row for row in ROLES["agents"]}
TASKS = {row["id"]: row for row in json.loads((STAGE2 / "tasks.json").read_text())["tasks"]}
SUBJECT = json.loads((STAGE2 / "subject.json").read_text())
LIMITS = SUBJECT["limits"]
ALLOWED = {"list_files", "read_file", "write_file", "run_tests", "message", "delegate", "finalize"}


def _load_provider(mode, role, script_file=None):
    if mode == "scripted":
        if not script_file:
            raise ValueError("scripted A2A service requires a script file")
        payload = json.loads(Path(script_file).read_text())
        scripted = payload.get(role)
        if not isinstance(scripted, list) or not scripted:
            raise ValueError(f"scripted A2A service lacks actions for role {role}")
        return ScriptedProvider(scripted)
    if mode != "subject":
        raise ValueError("A2A role service mode is not frozen")
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("A2A subject service requires the frozen DeepSeek credential")
    config = json.loads((ROOT / SUBJECT["source_config"]).read_text())
    if (
        config["provider"] != SUBJECT["provider"]
        or config["model_alias"] != SUBJECT["model_alias"]
        or config["expected_model_version"] != SUBJECT["expected_model_version"]
        or config["subject"] != SUBJECT["subject"]
    ):
        raise ValueError("A2A subject configuration differs from frozen subject")
    return DeepSeekArenaProvider(config)


async def _call_agent(url, payload):
    import httpx
    from a2a.client import ClientConfig, create_client
    from a2a.helpers import new_text_message
    from a2a.types import Role, SendMessageRequest

    timeout = LIMITS["transport_timeout_seconds"] * LIMITS["transport_max_retries"] + 10
    async with httpx.AsyncClient(timeout=timeout, trust_env=False) as http:
        client = await create_client(
            agent=url,
            client_config=ClientConfig(streaming=False, httpx_client=http),
        )
        message = new_text_message(
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            role=Role.ROLE_USER,
        )
        request = SendMessageRequest(message=message)
        events = [event async for event in client.send_message(request)]
    if not events:
        raise RuntimeError("A2A role service returned no task event")
    wrapper = events[-1]
    task = wrapper.task if wrapper.HasField("task") else None
    if task is None or not task.artifacts:
        raise RuntimeError("A2A role service returned no result artifact")
    text = "\n".join(
        part.text for part in task.artifacts[-1].parts if part.HasField("text")
    )
    result = json.loads(text)
    if result.get("schema") != "stage2-x3-role-result-v1":
        raise RuntimeError("A2A role artifact has unexpected schema")
    return result


class RoleRuntime:
    def __init__(self, *, role, checkout, directory_file, mode, script_file=None):
        if role not in DIRECTORY:
            raise ValueError("role outside frozen roster")
        self.role = role
        self.agent = DIRECTORY[role]
        self.checkout = A2ACheckout(checkout)
        self.directory = json.loads(Path(directory_file).read_text())
        if set(self.directory) != set(DIRECTORY):
            raise ValueError("A2A service directory differs from frozen nine-role roster")
        self.provider = _load_provider(mode, role, script_file)
        self.mode = mode
        self.sessions = {}

    def _prompt(self, *, task, state, remaining_turns):
        system = (
            f"You are {self.agent['role']}. {self.agent['responsibility']} "
            "Collaborate with other registered Software Engineering roles through A2A when useful. "
            "Work on the user request in the provided checkout. Use only the actions below. "
            "Return one JSON object with actions; no private reasoning or benchmark discussion."
        )
        content = {
            "user_request": task["user_request"],
            "received_a2a": state["messages"],
            "observations": state["observations"],
            "available_roles": [
                {"id": row["id"], "role": row["role"]}
                for row in ROLES["agents"]
                if row["id"] != self.role
            ],
            "available_actions": {
                "list_files": {},
                "read_file": {"path": "relative path"},
                "write_file": {"path": "relative path", "content": "entire UTF-8 file"},
                "run_tests": {},
                "message": {"to": "role id", "content": "message"},
                "delegate": {"to": "role id", "content": "request"},
                "finalize": {"answer": "user-facing or caller-facing result"},
            },
            "remaining_turns": remaining_turns,
        }
        system, content, _ = apply_model_visible_action_contract(
            system,
            content,
            task_id=task["id"],
            max_actions=5,
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(content, ensure_ascii=False)},
        ]

    async def _complete(self, messages, *, turn):
        result = self.provider.complete_agent(
            messages, metadata={"role": self.role, "turn": turn}
        )
        return await result if inspect.isawaitable(result) else result

    async def execute_payload(self, payload):
        if payload.get("schema") != "stage2-x3-role-call-v1":
            raise ValueError("unexpected A2A role-call schema")
        task_id = payload.get("task_id")
        if task_id not in TASKS:
            raise ValueError("task outside frozen T1-T3")
        if payload.get("target") != self.role:
            raise ValueError("A2A role call delivered to the wrong service")
        sender = payload.get("sender")
        if sender != "USER" and sender not in DIRECTORY:
            raise ValueError("A2A sender outside frozen roster")
        if sender == self.role:
            raise ValueError("A2A self-routing is not allowed")
        remaining = int(payload.get("remaining_turns", 0))
        if not 1 <= remaining <= LIMITS["max_turns"]:
            raise ValueError("A2A role call has invalid remaining-turn budget")
        depth = int(payload.get("depth", 0))
        if depth < 0 or depth >= LIMITS["max_turns"]:
            raise ValueError("A2A role-call depth exceeds frozen turn budget")
        session_id = payload.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("A2A role call requires a session id")
        content = payload.get("content")
        if not isinstance(content, str) or not content:
            raise ValueError("A2A role call requires non-empty content")
        if sender == "USER" and content != TASKS[task_id]["user_request"]:
            raise ValueError("initial A2A user request differs from frozen task")

        state = self.sessions.setdefault(session_id, {"messages": [], "observations": []})
        state["messages"].append(
            {
                "from": sender,
                "kind": payload.get("kind", "message"),
                "content": content,
            }
        )
        used = 0
        protocol_calls = 0
        trace = []
        task = TASKS[task_id]

        while used < remaining:
            used += 1
            messages = self._prompt(
                task=task,
                state=state,
                remaining_turns=remaining - used + 1,
            )
            response = await self._complete(messages, turn=used)
            try:
                envelope = json.loads(response["content"])
                actions = envelope["actions"]
                if not isinstance(actions, list) or len(actions) > 5:
                    raise ValueError("invalid action count")
                if any(
                    not isinstance(action, dict) or action.get("type") not in ALLOWED
                    for action in actions
                ):
                    raise ValueError("unsupported action")
            except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
                state["observations"].append(
                    {"kind": "invalid_envelope", "content": f"Invalid envelope: {exc}"}
                )
                trace.append({"role": self.role, "turn": used, "valid": False})
                continue

            trace.append(
                {"role": self.role, "turn": used, "valid": True, "actions": len(actions)}
            )
            needs_return = False
            for action in actions:
                kind = action["type"]
                if kind in ("message", "delegate"):
                    target = action.get("to")
                    message_content = action.get("content")
                    if (
                        target not in DIRECTORY
                        or target == self.role
                        or not isinstance(message_content, str)
                        or not message_content
                    ):
                        raise ValueError("invalid A2A specialist routing")
                    available = remaining - used
                    if available <= 0:
                        return self._result(
                            answer=None,
                            stop_reason="turn_budget",
                            turns_used=used,
                            protocol_calls=protocol_calls,
                            trace=trace,
                            terminal=False,
                        )
                    nested = await _call_agent(
                        self.directory[target],
                        {
                            "schema": "stage2-x3-role-call-v1",
                            "session_id": session_id,
                            "task_id": task_id,
                            "sender": self.role,
                            "target": target,
                            "kind": kind,
                            "content": message_content,
                            "remaining_turns": available,
                            "depth": depth + 1,
                        },
                    )
                    protocol_calls += 1 + int(nested.get("protocol_calls", 0))
                    nested_turns = int(nested.get("turns_used", 0))
                    if nested_turns < 1 or nested_turns > available:
                        raise RuntimeError("nested A2A result has invalid turn accounting")
                    used += nested_turns
                    trace.extend(nested.get("trace", []))
                    state["messages"].append(
                        {
                            "from": target,
                            "kind": "a2a_artifact",
                            "content": nested.get("answer"),
                            "stop_reason": nested.get("stop_reason"),
                        }
                    )
                    if nested.get("terminal"):
                        return self._result(
                            answer=nested.get("answer"),
                            stop_reason=nested.get("stop_reason"),
                            turns_used=used,
                            protocol_calls=protocol_calls,
                            trace=trace,
                            terminal=True,
                        )
                    needs_return = True
                elif kind == "finalize":
                    answer = action.get("answer", "")
                    return self._result(
                        answer=answer,
                        stop_reason="finalized",
                        turns_used=used,
                        protocol_calls=protocol_calls,
                        trace=trace,
                        terminal=self.role == ROLES["entry_agent"],
                    )
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
                        state["observations"].append(
                            {"kind": "tool_result", "action": kind, "content": result}
                        )
                    except (OSError, ValueError, KeyError, UnicodeError) as exc:
                        state["observations"].append(
                            {
                                "kind": "tool_result",
                                "action": kind,
                                "content": f"Error: {exc}",
                            }
                        )
                    needs_return = True
            if not needs_return:
                return self._result(
                    answer=None,
                    stop_reason="no_followup",
                    turns_used=used,
                    protocol_calls=protocol_calls,
                    trace=trace,
                    terminal=False,
                )

        return self._result(
            answer=None,
            stop_reason="turn_budget",
            turns_used=used,
            protocol_calls=protocol_calls,
            trace=trace,
            terminal=False,
        )

    def _result(self, *, answer, stop_reason, turns_used, protocol_calls, trace, terminal):
        return {
            "schema": "stage2-x3-role-result-v1",
            "role": self.role,
            "answer": answer,
            "stop_reason": stop_reason,
            "turns_used": turns_used,
            "protocol_calls": protocol_calls,
            "trace": trace,
            "terminal": bool(terminal),
        }


def build_app(*, runtime, public_url):
    from a2a.server.agent_execution import AgentExecutor
    from a2a.server.events import EventQueue
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
    from a2a.server.tasks import TaskUpdater
    from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
    from a2a.types import (
        AgentCapabilities,
        AgentCard,
        AgentInterface,
        AgentSkill,
        Part,
        Task,
        TaskState,
        TaskStatus,
    )
    from starlette.applications import Starlette

    class RoleExecutor(AgentExecutor):
        async def execute(self, context, event_queue: EventQueue):
            if not context.message or not context.task_id or not context.context_id:
                raise ValueError("A2A role service requires message/task/context")
            await event_queue.enqueue_event(
                Task(
                    id=context.task_id,
                    context_id=context.context_id,
                    status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED),
                    history=[context.message],
                )
            )
            updater = TaskUpdater(event_queue, context.task_id, context.context_id)
            await updater.start_work()
            payload = json.loads(context.get_user_input())
            result = await runtime.execute_payload(payload)
            await updater.add_artifact(
                parts=[Part(text=json.dumps(result, ensure_ascii=False, sort_keys=True))],
                name=f"{runtime.role}-result",
                last_chunk=True,
            )
            await updater.complete()

        async def cancel(self, context, event_queue: EventQueue):
            updater = TaskUpdater(event_queue, context.task_id or "", context.context_id or "")
            await updater.cancel()

    card = AgentCard(
        name=f"Stage-II {runtime.agent['role']}",
        description=f"Frozen Software Engineering role {runtime.role} exposed through A2A.",
        version="stage2-x3-v7.6",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC",
                protocol_version="1.0",
                url=public_url,
            )
        ],
        skills=[
            AgentSkill(
                id=runtime.role,
                name=runtime.agent["role"],
                description=runtime.agent["responsibility"],
                tags=["software-engineering", "a2a"],
            )
        ],
    )
    handler = DefaultRequestHandler(
        agent_executor=RoleExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    return Starlette(
        routes=[
            *create_agent_card_routes(agent_card=card),
            *create_jsonrpc_routes(request_handler=handler, rpc_url="/"),
        ]
    )


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=sorted(DIRECTORY))
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--directory-file", required=True)
    parser.add_argument("--public-url", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--mode", choices=["subject", "scripted"], default="subject")
    parser.add_argument("--script-file")
    args = parser.parse_args()
    runtime = RoleRuntime(
        role=args.role,
        checkout=args.checkout,
        directory_file=args.directory_file,
        mode=args.mode,
        script_file=args.script_file,
    )
    app = build_app(runtime=runtime, public_url=args.public_url)
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=args.port,
        log_level="error",
        access_log=False,
    )


if __name__ == "__main__":
    main()
