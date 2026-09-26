from __future__ import annotations

import inspect
import json

from stage2.native_v7.software_host_v1 import (
    ALLOWED,
    DIRECTORY,
    ROLES,
    SUBJECT_LIMITS,
    SoftwareEngineeringHost,
)


async def _call_hook(hook, **payload):
    if hook is None:
        return None
    value = hook(**payload)
    if inspect.isawaitable(value):
        value = await value
    return value


class ProspectiveCheckpointedSoftwareEngineeringHost(SoftwareEngineeringHost):
    """SoftwareEngineeringHost with passive quiescent-boundary callbacks.

    The run-loop logic is intentionally kept equivalent to the frozen host. The
    only additions are callbacks before the first turn, after a completed turn,
    and at terminal return. The callback is outside the model prompt and action
    contract and receives no authority over host scheduling.
    """

    def __init__(self, *args, checkpoint_hook=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.checkpoint_hook = checkpoint_hook

    async def run(self):
        await _call_hook(
            self.checkpoint_hook,
            boundary="BEFORE_HOST_TURN",
            event_ref="host:task-start",
            host=self,
            turn=0,
        )
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
                await _call_hook(
                    self.checkpoint_hook,
                    boundary="AFTER_HOST_TURN_RETURNS",
                    event_ref=f"host:turn:{turn:04d}:post",
                    host=self,
                    turn=turn,
                )
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
            if not self.stop_reason and needs_return:
                self.queue.append(role)

            await _call_hook(
                self.checkpoint_hook,
                boundary="AFTER_HOST_TURN_RETURNS",
                event_ref=f"host:turn:{turn:04d}:post",
                host=self,
                turn=turn,
            )
            if self.stop_reason:
                break

        if not self.stop_reason:
            self.stop_reason = "turn_budget"

        await _call_hook(
            self.checkpoint_hook,
            boundary="TERMINAL",
            event_ref="host:terminal",
            host=self,
            turn=len(self.history),
        )
        return {
            "answer": self.answer,
            "stop_reason": self.stop_reason,
            "turns": len(self.history),
            "pending_roles": list(self.queue),
            "history": self.history,
        }
