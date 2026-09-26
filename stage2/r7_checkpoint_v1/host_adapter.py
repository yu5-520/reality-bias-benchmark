from __future__ import annotations

import copy
from collections import deque
from typing import Any

from stage2.r7_checkpoint_v1.common import CheckpointRegistry, digest


ADAPTER_ID = "stage2-r7-software-host-checkpoint-v1"


class SoftwareHostCheckpointAdapter:
    """Checkpoint the Stage-II-owned queue/mailbox runtime used by X4-X7.

    External MCP/RAG/MemoryBank/LongLLMLingua state is never copied into a
    writable repair object. Those systems are represented only by immutable
    reference/hash bindings in the registry manifest.
    """

    framework_binding = {
        "framework": "Stage-II SoftwareEngineeringHost",
        "scope": "X4-X7 host runtime only",
        "foreign_carrier_policy": "REFERENCE_AND_HASH_ONLY",
    }

    def save_state(self, host) -> dict[str, Any]:
        return {
            "schema": "stage2-r7-software-host-state-v1",
            "task_id": host.task["id"],
            "max_turns": int(host.max_turns),
            "max_actions": int(host.max_actions),
            "queue": list(host.queue),
            "inbox": copy.deepcopy(host.inbox),
            "answer": host.answer,
            "stop_reason": host.stop_reason,
            "history": copy.deepcopy(host.history),
        }

    def load_state(self, host, state: dict[str, Any]) -> None:
        if state.get("schema") != "stage2-r7-software-host-state-v1":
            raise ValueError("unexpected software-host checkpoint schema")
        if state.get("task_id") != host.task["id"]:
            raise ValueError("software-host checkpoint task mismatch")
        if int(state.get("max_turns")) != int(host.max_turns):
            raise ValueError("software-host checkpoint max_turns mismatch")
        if int(state.get("max_actions")) != int(host.max_actions):
            raise ValueError("software-host checkpoint max_actions mismatch")
        host.queue = deque(state["queue"])
        host.inbox = copy.deepcopy(state["inbox"])
        host.answer = state.get("answer")
        host.stop_reason = state.get("stop_reason")
        host.history = copy.deepcopy(state["history"])
        if digest(self.save_state(host)) != digest(state):
            raise RuntimeError("software-host checkpoint did not round-trip")

    def capture(
        self,
        *,
        system_id: str,
        host,
        registry: CheckpointRegistry,
        application_root,
        group_id: str,
        run_id: str,
        task_id: str,
        event_ref: str,
        model_visible_context: Any,
        remaining_horizon: Any,
        external_carrier_refs: list[dict[str, Any]],
        replication_binding: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if system_id not in {"X4_MCP", "X5_RAG", "X6_MEMORYBANK", "X7_LONGLMLINGUA"}:
            raise ValueError("software host checkpoint system outside X4-X7")
        state = self.save_state(host)
        return registry.capture(
            system_id=system_id,
            group_id=group_id,
            run_id=run_id,
            task_id=task_id,
            event_ref=event_ref,
            adapter_id=ADAPTER_ID,
            framework_binding=self.framework_binding,
            native_state=state,
            application_root=application_root,
            model_visible_context=model_visible_context,
            remaining_horizon=remaining_horizon,
            external_carrier_refs=external_carrier_refs,
            restore_capability="FULL_NATIVE",
            replication_binding=replication_binding,
        )
