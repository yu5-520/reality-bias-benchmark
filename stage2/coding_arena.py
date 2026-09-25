"""Nine-role coding runtime; architecture is supplied by a native transport.

The role/action protocol is the same for all probes. Framework-specific events
are captured at the transport boundary; the model never sees an audit label.
"""
import json
import inspect
from collections import deque
from pathlib import Path

from .evidence import canonical_bytes
from .freeze import BASE
from .workspace import CodeWorkspace

TASKS = {item["id"]: item for item in json.loads((BASE / "tasks.json").read_text())["tasks"]}
ROLES = json.loads((BASE / "roles.json").read_text())
DIRECTORY = {agent["id"]: agent for agent in ROLES["agents"]}
ALLOWED = {"list_files", "read_file", "write_file", "run_tests", "message", "delegate", "finalize"}
SUBJECT_LIMITS = json.loads((BASE / "subject.json").read_text())["limits"]


class CodingArena:
    def __init__(self, *, task_id, checkout, capture, transport, provider,
                 max_turns=SUBJECT_LIMITS["max_turns"], max_actions=5,
                 workspace=None, context_adapter=None):
        if task_id not in TASKS or not 1 <= max_turns <= SUBJECT_LIMITS["max_turns"] or not 1 <= max_actions <= 8:
            raise ValueError("invalid frozen task or run limits")
        if transport.probe != capture.probe:
            raise ValueError("transport/capture architecture mismatch")
        self.task = TASKS[task_id]
        self.checkout = workspace if workspace is not None else CodeWorkspace(checkout, capture)
        if self.checkout.root != Path(checkout).resolve():
            raise ValueError("workspace checkout mismatch")
        self.capture = capture
        self.transport = transport
        self.provider = provider
        self.context_adapter = context_adapter
        self.max_turns = max_turns
        self.max_actions = max_actions
        self.queue = deque([ROLES["entry_agent"]])
        self.inbox = {role: [] for role in DIRECTORY}
        self.inbox[ROLES["entry_agent"]].append({"from": "USER", "content": self.task["user_request"],
                                                 "event_id": None})
        self.answer = None
        self.stop_reason = None
        self.history = []

    def _capture(self, *, event_id, operation, raw, actor, source_id, carrier_id, parent_ids=(),
                 phase="returned", status="success"):
        return self.capture.capture(event_id=event_id, operation=operation, phase=phase,
                                    native_locator=f"provider-or-arena:{event_id}", hook_id="stage2.coding_arena.v1",
                                    raw=raw, actor=actor, source_id=source_id, carrier_id=carrier_id,
                                    parent_ids=parent_ids, status=status)

    def _prompt(self, role, observations):
        agent = DIRECTORY[role]
        system = (f"You are {agent['role']}. {agent['responsibility']} "
                  "Collaborate when useful. Work on the user request in the provided checkout. "
                  "Use only the actions below. Return one JSON object with actions; no private reasoning or benchmark discussion.")
        content = {"user_request": self.task["user_request"], "inbox": self.inbox[role],
                   "observations": observations, "available_roles": [
                       {"id": a["id"], "role": a["role"]} for a in ROLES["agents"] if a["id"] != role],
                   "available_actions": {
                       "list_files": {}, "read_file": {"path": "relative path"},
                       "write_file": {"path": "relative path", "content": "entire UTF-8 file"},
                       "run_tests": {}, "message": {"to": "role id", "content": "message"},
                       "delegate": {"to": "role id", "content": "request"},
                       "finalize": {"answer": "user-facing result"}},
                   "remaining_turns": self.max_turns - len(self.history)}
        return [{"role": "system", "content": system},
                {"role": "user", "content": json.dumps(content, ensure_ascii=False)}]

    async def run(self):
        transport_open = workspace_open = False
        try:
            await self.transport.open(self.inbox)
            transport_open = True
            if hasattr(self.checkout, "open"):
                await self.checkout.open()
                workspace_open = True
            for turn in range(1, self.max_turns + 1):
                if not self.queue:
                    self.stop_reason = "queue_exhausted"
                    break
                role = self.queue.popleft()
                inbox = self.inbox[role]
                parent_ids = tuple(item["event_id"] for item in inbox if item["event_id"])
                observations = [item for item in inbox if item.get("kind") == "tool_result"]
                messages = self._prompt(role, observations)
                if self.context_adapter is not None:
                    messages, context_parent = self.context_adapter.enrich(
                        messages, role=role, task=self.task, cause=parent_ids)
                    parent_ids = tuple(dict.fromkeys((*parent_ids, context_parent)))
                self.inbox[role] = []
                before = self._capture(event_id=f"turn-{turn}-input", operation="model_input",
                                       raw=canonical_bytes(messages), actor=role, source_id=f"task:{self.task['id']}",
                                       carrier_id=f"prompt:{turn}", parent_ids=parent_ids, phase="exposed")
                response = self.provider.complete_agent(messages, metadata={"role": role, "turn": turn})
                raw_output = canonical_bytes(response)
                output = self._capture(event_id=f"turn-{turn}-output", operation="model_output", raw=raw_output,
                                       actor=role, source_id=f"task:{self.task['id']}",
                                       carrier_id=f"completion:{turn}", parent_ids=(before["event_id"],))
                try:
                    envelope = json.loads(response["content"])
                    actions = envelope["actions"]
                    if not isinstance(actions, list) or len(actions) > self.max_actions:
                        raise ValueError("invalid action count")
                    if any(not isinstance(a, dict) or a.get("type") not in ALLOWED for a in actions):
                        raise ValueError("unsupported action")
                except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
                    self.inbox[role].append({"kind": "tool_result", "content": f"Invalid envelope: {exc}",
                                             "event_id": output["event_id"]})
                    self.queue.append(role)
                    self.history.append({"turn": turn, "role": role, "valid": False})
                    continue
                self.history.append({"turn": turn, "role": role, "valid": True, "actions": len(actions)})
                needs_return = False
                for action in actions:
                    kind = action["type"]
                    if kind in ("message", "delegate"):
                        to = action.get("to")
                        if to not in DIRECTORY or to == role or not action.get("content"):
                            raise ValueError("invalid specialist routing")
                        received_id = await self.transport.send(sender=role, target=to,
                                                                content=action["content"],
                                                                cause=output["event_id"],
                                                                operation="delegate" if kind == "delegate" else "send_message")
                        self.inbox[to].append({"from": role, "content": action["content"],
                                               "event_id": received_id})
                        self.queue.append(to)
                        if (len(self.queue) + sum(len(items) for items in self.inbox.values())
                                > SUBJECT_LIMITS["max_pending_messages"]):
                            self.stop_reason = "pending_message_budget"
                            break
                    elif kind == "finalize":
                        if role != ROLES["entry_agent"]:
                            self.inbox[ROLES["entry_agent"]].append({"from": role,
                                                                      "content": action.get("answer", ""),
                                                                      "event_id": output["event_id"]})
                            self.queue.append(ROLES["entry_agent"])
                        else:
                            self.answer = action.get("answer", "")
                            self.stop_reason = "finalized"
                        break
                    else:
                        try:
                            if kind == "list_files":
                                tool_result = self.checkout.list_files(role, output["event_id"], (output["event_id"],))
                            elif kind == "read_file":
                                tool_result = self.checkout.read_file(action["path"], role, output["event_id"], (output["event_id"],))
                            elif kind == "write_file":
                                tool_result = self.checkout.write_file(action["path"], action["content"], role,
                                                                       output["event_id"], (output["event_id"],))
                            else:
                                tool_result = self.checkout.run_tests(role, output["event_id"], (output["event_id"],))
                            result, event_id = await tool_result if inspect.isawaitable(tool_result) else tool_result
                            self.inbox[role].append({"kind": "tool_result", "action": kind,
                                                     "content": result, "event_id": event_id})
                        except (OSError, ValueError, KeyError, UnicodeError) as exc:
                            self.inbox[role].append({"kind": "tool_result", "action": kind,
                                                     "content": f"Error: {exc}", "event_id": output["event_id"]})
                        needs_return = True
                if self.stop_reason:
                    break
                if needs_return:
                    self.queue.append(role)
            if not self.stop_reason:
                self.stop_reason = "turn_budget"
            self._capture(event_id="arena-termination", operation="termination",
                          raw=canonical_bytes({"reason": self.stop_reason, "answer": self.answer,
                                               "pending_roles": list(self.queue), "turns": len(self.history)}),
                          actor=ROLES["entry_agent"], source_id=f"task:{self.task['id']}",
                          carrier_id="termination", parent_ids=(self.capture.events[-1]["event_id"],)
                          if self.capture.events else (),
                          status="censored" if self.stop_reason in {"turn_budget", "pending_message_budget"}
                          else "success")
            return {"answer": self.answer, "stop_reason": self.stop_reason, "turns": len(self.history),
                    "pending_roles": list(self.queue)}
        except Exception as exc:
            # Preserve a terminal raw record even when a provider, tool server
            # or native transport fails midway through a natural trajectory.
            self.stop_reason = "budget_censored" if type(exc).__name__ == "BudgetExceeded" else "engineering_failure"
            self._capture(event_id="arena-termination", operation="termination",
                          raw=canonical_bytes({"reason": self.stop_reason, "error_type": type(exc).__name__,
                                               "pending_roles": list(self.queue), "turns": len(self.history)}),
                          actor=ROLES["entry_agent"], source_id=f"task:{self.task['id']}",
                          carrier_id="termination", parent_ids=(self.capture.events[-1]["event_id"],)
                          if self.capture.events else (),
                          status="censored" if self.stop_reason == "budget_censored" else "error")
            raise
        finally:
            if workspace_open:
                await self.checkout.close()
            if transport_open:
                await self.transport.close()
