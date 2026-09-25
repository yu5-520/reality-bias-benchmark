"""X2 runner: frozen nine-role Software Engineering task inside native MetaGPT.

MetaGPT Environment owns scheduling and message routing. Each frozen role is a
MetaGPT Role, and inter-role work travels as native MetaGPT Message objects through
Environment.publish_message / Role.msg_buffer. The v6 CodingArena and transport
wrappers are not imported.
"""
from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import os
import tempfile
from importlib.metadata import version
from pathlib import Path

from pydantic import Field

# The pinned MetaGPT package eagerly loads its repository config during import.
# Supply an isolated non-provider bootstrap config so MetaGPT can initialize its
# native Role/Environment classes without reading or modifying a user's config.
# All actual subject calls below use the separately frozen Stage-II provider.
_METAGPT_BOOTSTRAP_HOME = Path(tempfile.mkdtemp(prefix="stage2-x2-metagpt-home-"))
(_METAGPT_BOOTSTRAP_HOME / ".metagpt").mkdir()
(_METAGPT_BOOTSTRAP_HOME / ".metagpt/config2.yaml").write_text(
    "llm:\n"
    "  api_type: openai\n"
    "  model: stage2-bootstrap-unused\n"
    "  base_url: https://api.openai.com/v1\n"
    "  api_key: stage2-bootstrap-unused\n"
)
os.environ["HOME"] = str(_METAGPT_BOOTSTRAP_HOME)

from arena.providers import DeepSeekArenaProvider
from stage2.native_v7.observer import PassiveEventObserver, native_bytes
from stage2.native_v7.x2_metagpt.checkout import MetaGPTCheckout

from metagpt.actions import UserRequirement
from metagpt.configs.llm_config import LLMConfig
from metagpt.environment import Environment
from metagpt.provider.base_llm import BaseLLM
from metagpt.roles import Role
from metagpt.schema import Message

ROOT = Path(__file__).resolve().parents[3]
STAGE2 = ROOT / "stage2"
ROLES = json.loads((STAGE2 / "roles.json").read_text())
DIRECTORY = {row["id"]: row for row in ROLES["agents"]}
TASKS = {row["id"]: row for row in json.loads((STAGE2 / "tasks.json").read_text())["tasks"]}
SUBJECT = json.loads((STAGE2 / "subject.json").read_text())
LIMITS = SUBJECT["limits"]
ALLOWED = {"list_files", "read_file", "write_file", "run_tests", "message", "delegate", "finalize"}
NATIVE_CAUSE = "stage2.native_v7.x2_metagpt.turn"
TERMINAL_ADDRESS = "__stage2_metagpt_terminal__"
IDLE_ADDRESS = "__stage2_metagpt_idle__"


class Stage2ProviderLLM(BaseLLM):
    """MetaGPT-compatible LLM shell over the already frozen subject provider."""

    def __init__(self, provider):
        self.provider = provider
        self.config = LLMConfig(
            api_key="stage2-provider-shell",
            model="stage2-frozen-subject",
            stream=False,
            calc_usage=False,
        )
        self.model = "stage2-frozen-subject"
        self.cost_manager = None
        self.system_prompt = "Stage-II frozen subject provider"

    async def complete_json(self, messages, metadata):
        result = await asyncio.to_thread(self.provider.complete_agent, messages, metadata)
        if inspect.isawaitable(result):
            result = await result
        return result

    async def _achat_completion(self, messages, timeout=None):
        result = await self.complete_json(messages, {"surface": "metagpt-base-llm"})
        return {"choices": [{"message": {"content": result["content"]}}]}

    async def acompletion(self, messages, timeout=None):
        return await self._achat_completion(messages, timeout=timeout)

    async def _achat_completion_stream(self, messages, timeout=None):
        result = await self.complete_json(messages, {"surface": "metagpt-base-llm-stream"})
        return result["content"]


class RuntimeState:
    def __init__(self, *, max_turns):
        self.max_turns = int(max_turns)
        self.turns = 0
        self.lock = asyncio.Lock()
        self.answer = None
        self.stop_reason = None
        self.history = []

    async def reserve_turn(self, role):
        async with self.lock:
            if self.stop_reason:
                return None
            if self.turns >= self.max_turns:
                self.stop_reason = "turn_budget"
                return None
            self.turns += 1
            return self.turns

    async def record(self, row):
        async with self.lock:
            self.history.append(row)

    async def finalize(self, answer):
        async with self.lock:
            if not self.stop_reason:
                self.answer = answer
                self.stop_reason = "finalized"

    async def stop(self, reason):
        async with self.lock:
            if not self.stop_reason:
                self.stop_reason = reason


class Stage2MetaRole(Role):
    stage2_runtime: object = Field(exclude=True)
    stage2_checkout: object = Field(exclude=True)
    stage2_directory: dict = Field(default_factory=dict, exclude=True)
    stage2_entry: str = Field(default="", exclude=True)

    async def _think(self) -> bool:
        return not bool(self.stage2_runtime.stop_reason)

    def _prompt(self, turn):
        agent = self.stage2_directory[self.name]
        inbox = [
            {
                "from": msg.sent_from or "UNKNOWN",
                "kind": (msg.metadata or {}).get("kind", "message"),
                "content": msg.content,
            }
            for msg in self.rc.news
        ]
        observations = [row for row in inbox if row["kind"] == "tool_result"]
        system = (
            f"You are {agent['role']}. {agent['responsibility']} "
            "Collaborate when useful. Work on the user request in the provided checkout. "
            "Use only the actions below. Return one JSON object with actions; "
            "no private reasoning or benchmark discussion."
        )
        content = {
            "user_request": self.stage2_runtime.task["user_request"],
            "inbox": inbox,
            "observations": observations,
            "available_roles": [
                {"id": row["id"], "role": row["role"]}
                for row in ROLES["agents"]
                if row["id"] != self.name
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
            "remaining_turns": self.stage2_runtime.max_turns - turn + 1,
        }
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(content, ensure_ascii=False)},
        ]

    def _message(self, *, content, target, kind, action=None):
        metadata = {"kind": kind}
        if action:
            metadata["action"] = action
        return Message(
            content=content,
            role=self.profile,
            sent_from=self.name,
            send_to={target},
            cause_by=NATIVE_CAUSE,
            metadata=metadata,
        )

    async def _act(self) -> Message:
        turn = await self.stage2_runtime.reserve_turn(self.name)
        if turn is None:
            return self._message(
                content="Stage-II model-turn budget reached.",
                target=IDLE_ADDRESS,
                kind="turn_budget",
            )

        response = await self.llm.complete_json(
            self._prompt(turn), metadata={"role": self.name, "turn": turn}
        )
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
            await self.stage2_runtime.record(
                {"turn": turn, "role": self.name, "valid": False}
            )
            return self._message(
                content=f"Invalid envelope: {exc}",
                target=self.name,
                kind="tool_result",
                action="invalid_envelope",
            )

        await self.stage2_runtime.record(
            {"turn": turn, "role": self.name, "valid": True, "actions": len(actions)}
        )
        outbound = []
        for action in actions:
            kind = action["type"]
            if kind in ("message", "delegate"):
                target = action.get("to")
                content = action.get("content")
                if (
                    target not in self.stage2_directory
                    or target == self.name
                    or not isinstance(content, str)
                    or not content
                ):
                    raise ValueError("invalid MetaGPT specialist routing")
                outbound.append(
                    self._message(content=content, target=target, kind=kind)
                )
            elif kind == "finalize":
                answer = action.get("answer", "")
                if self.name == self.stage2_entry:
                    await self.stage2_runtime.finalize(answer)
                    outbound.append(
                        self._message(
                            content=answer,
                            target=TERMINAL_ADDRESS,
                            kind="finalize",
                        )
                    )
                else:
                    outbound.append(
                        self._message(
                            content=answer,
                            target=self.stage2_entry,
                            kind="specialist_finalize",
                        )
                    )
                break
            else:
                try:
                    if kind == "list_files":
                        result = self.stage2_checkout.list_files()
                    elif kind == "read_file":
                        result = self.stage2_checkout.read_file(action["path"])
                    elif kind == "write_file":
                        result = self.stage2_checkout.write_file(action["path"], action["content"])
                    else:
                        result = self.stage2_checkout.run_tests()
                    content = json.dumps(result, ensure_ascii=False, sort_keys=True)
                except (OSError, ValueError, KeyError, UnicodeError) as exc:
                    content = f"Error: {exc}"
                outbound.append(
                    self._message(
                        content=content,
                        target=self.name,
                        kind="tool_result",
                        action=kind,
                    )
                )

        if not outbound:
            outbound.append(
                self._message(
                    content="No follow-up action emitted.",
                    target=IDLE_ADDRESS,
                    kind="no_followup",
                )
            )

        # Default MetaGPT Role._act remembers its own emitted message. Preserve that
        # behavior for inter-role messages, but do not pre-store self-targeted tool
        # feedback or it would be filtered as already-seen on the next _observe().
        for msg in outbound:
            if self.name not in msg.send_to:
                self.rc.memory.add(msg)
        for msg in outbound[:-1]:
            self.publish_message(msg)
        return outbound[-1]


def _load_inputs(task_file, roles_file, subject_file):
    task = json.loads(Path(task_file).read_text())
    roles = json.loads(Path(roles_file).read_text())
    subject = json.loads(Path(subject_file).read_text())
    if task.get("id") not in TASKS or task != TASKS[task["id"]]:
        raise ValueError("task file differs from frozen T1-T3")
    if roles != ROLES:
        raise ValueError("roles file differs from frozen nine-role roster")
    if subject != SUBJECT:
        raise ValueError("subject file differs from frozen subject profile")
    return task, subject


def build_subject_provider(subject):
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("X2 subject mode requires the frozen DeepSeek credential")
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


def _pending_messages(env):
    return sum(role.rc.msg_buffer._queue.qsize() for role in env.get_roles().values())


def _observe_native(observer, env, env_index, role_indices):
    history = env.history.get()
    for msg in history[env_index:]:
        raw = native_bytes(msg)
        returned = observer.observe(raw, surface="metagpt.Environment.history.post_round_copy")
        if returned is not raw or returned != raw:
            raise RuntimeError("MetaGPT observer altered Environment history bytes")
    env_index = len(history)
    for role_id, role in env.get_roles().items():
        memory = role.rc.memory.get()
        start = role_indices.get(role_id, 0)
        for msg in memory[start:]:
            raw = native_bytes(msg)
            returned = observer.observe(
                raw, surface=f"metagpt.Role.memory.{role_id}.post_round_copy"
            )
            if returned is not raw or returned != raw:
                raise RuntimeError("MetaGPT observer altered Role memory bytes")
        role_indices[role_id] = len(memory)
    return env_index


async def run_task(
    *,
    checkout,
    task_file,
    roles_file,
    subject_file,
    observer_root=None,
    provider=None,
):
    if version("metagpt") != "1.0.0":
        raise RuntimeError("exact frozen MetaGPT package version 1.0.0 required")
    task, subject = _load_inputs(task_file, roles_file, subject_file)
    active_provider = provider if provider is not None else build_subject_provider(subject)
    runtime = RuntimeState(max_turns=int(subject["limits"]["max_turns"]))
    runtime.task = task
    checkout_api = MetaGPTCheckout(checkout)
    env = Environment(desc="Software Engineering")
    roles = []
    for row in ROLES["agents"]:
        roles.append(
            Stage2MetaRole(
                name=row["id"],
                profile=row["role"],
                goal=row["responsibility"],
                llm=Stage2ProviderLLM(active_provider),
                stage2_runtime=runtime,
                stage2_checkout=checkout_api,
                stage2_directory=DIRECTORY,
                stage2_entry=ROLES["entry_agent"],
            )
        )
    env.add_roles(roles)
    if set(env.role_names()) != set(DIRECTORY):
        raise RuntimeError("MetaGPT native Environment lost a frozen role")

    initial = Message(
        content=task["user_request"],
        role="user",
        sent_from="USER",
        send_to={ROLES["entry_agent"]},
        cause_by=UserRequirement,
        metadata={"kind": "user_request"},
    )
    env.publish_message(initial)

    observer = PassiveEventObserver(observer_root, probe="X2") if observer_root else None
    env_index = 0
    role_indices = {}
    rounds = 0
    try:
        while not runtime.stop_reason and not env.is_idle and rounds < runtime.max_turns:
            rounds += 1
            await env.run(k=1)
            if observer is not None:
                env_index = _observe_native(observer, env, env_index, role_indices)
            pending = _pending_messages(env)
            if pending > int(subject["limits"]["max_pending_messages"]):
                await runtime.stop("pending_message_budget")
                break
            if not runtime.stop_reason and env.is_idle:
                await runtime.stop("queue_exhausted")
        if not runtime.stop_reason:
            await runtime.stop("turn_budget" if runtime.turns >= runtime.max_turns else "round_guard")
    finally:
        if observer is not None:
            if env_index < len(env.history.get()):
                _observe_native(observer, env, env_index, role_indices)
            observer.seal()

    return {
        "answer": runtime.answer,
        "stop_reason": runtime.stop_reason,
        "turns": runtime.turns,
        "metagpt_rounds": rounds,
        "environment_messages": len(env.history.get()),
        "pending_messages": _pending_messages(env),
        "history": sorted(runtime.history, key=lambda row: row["turn"]),
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
