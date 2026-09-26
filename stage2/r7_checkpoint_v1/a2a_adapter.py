from __future__ import annotations

import copy
from typing import Any

from stage2.native_v7.x3_a2a.service import RoleRuntime
from stage2.r7_checkpoint_v1.common import CheckpointRegistry, digest


A2A_PROTOCOL_COMMIT = "173695755607e884aa9acf8ce4feed90e32727a1"
A2A_SDK_COMMIT = "0d5473ca4fa6d40034a6a7c8d65bce5cd85d8167"
ADAPTER_ID = "stage2-r7-a2a-role-service-checkpoint-v1"


class CheckpointableRoleRuntime(RoleRuntime):
    """Prospective Stage-II role-service state API.

    This adds no A2A message, method, field, route, or protocol semantic. The
    checkpoint API belongs to the Stage-II role-service application and is used
    out-of-band at quiescent boundaries.
    """

    def save_stage2_state(self) -> dict[str, Any]:
        return {
            "schema": "stage2-r7-a2a-role-runtime-state-v1",
            "role": self.role,
            "directory": copy.deepcopy(self.directory),
            "mode": self.mode,
            "sessions": copy.deepcopy(self.sessions),
        }

    def load_stage2_state(self, state: dict[str, Any]) -> None:
        if state.get("schema") != "stage2-r7-a2a-role-runtime-state-v1":
            raise ValueError("unexpected A2A role runtime checkpoint schema")
        if state.get("role") != self.role:
            raise ValueError("A2A checkpoint role mismatch")
        if state.get("directory") != self.directory:
            raise ValueError("A2A service directory mismatch")
        if state.get("mode") != self.mode:
            raise ValueError("A2A runtime mode mismatch")
        sessions = state.get("sessions")
        if not isinstance(sessions, dict):
            raise ValueError("A2A sessions checkpoint must be a mapping")
        self.sessions = copy.deepcopy(sessions)


class A2ANativeCheckpointAdapter:
    framework_binding = {
        "framework": "A2A",
        "protocol_version": "1.0",
        "protocol_commit": A2A_PROTOCOL_COMMIT,
        "sdk_commit": A2A_SDK_COMMIT,
        "state_api": "Stage-II role-service application save/load; A2A protocol unchanged",
    }

    def aggregate_role_states(self, role_runtimes: dict[str, CheckpointableRoleRuntime]) -> dict[str, Any]:
        return {
            "schema": "stage2-r7-a2a-global-role-state-v1",
            "roles": {
                role: role_runtimes[role].save_stage2_state()
                for role in sorted(role_runtimes)
            },
        }

    def restore_role_states(
        self,
        *,
        role_runtimes: dict[str, CheckpointableRoleRuntime],
        state: dict[str, Any],
    ) -> None:
        if state.get("schema") != "stage2-r7-a2a-global-role-state-v1":
            raise ValueError("unexpected A2A global checkpoint schema")
        role_states = state.get("roles")
        if set(role_states or {}) != set(role_runtimes):
            raise ValueError("A2A global checkpoint role set mismatch")
        for role in sorted(role_runtimes):
            role_runtimes[role].load_stage2_state(role_states[role])
        round_trip = self.aggregate_role_states(role_runtimes)
        if digest(round_trip) != digest(state):
            raise RuntimeError("A2A role-service checkpoint did not round-trip")

    def capture(
        self,
        *,
        role_runtimes: dict[str, CheckpointableRoleRuntime],
        registry: CheckpointRegistry,
        application_root,
        group_id: str,
        run_id: str,
        task_id: str,
        event_ref: str,
        model_visible_context: Any,
        remaining_horizon: Any,
        external_carrier_refs: list[dict[str, Any]] | None = None,
        replication_binding: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = self.aggregate_role_states(role_runtimes)
        return registry.capture(
            system_id="X3_A2A",
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
