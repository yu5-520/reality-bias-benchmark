from __future__ import annotations

from typing import Any

from stage2.r7_checkpoint_v1.common import CheckpointRegistry, digest


AUTOGEN_COMMIT = "027ecf0a379bcc1d09956d46d12d44a3ad9cee14"
ADAPTER_ID = "stage2-r7-autogen-native-checkpoint-v1"


class AutoGenNativeCheckpointAdapter:
    """Use AutoGen's public Team save/load state API.

    No AutoGen internal/private field is read or modified by this adapter.
    """

    framework_binding = {
        "framework": "AutoGen AgentChat",
        "upstream_commit": AUTOGEN_COMMIT,
        "state_api": ["Team.save_state", "Team.load_state"],
    }

    async def capture(
        self,
        *,
        team,
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
        state = await team.save_state()
        if not isinstance(state, dict):
            state = dict(state)
        return registry.capture(
            system_id="X1_AUTOGEN",
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

    async def restore_state(self, *, team, registry: CheckpointRegistry, checkpoint_hash: str) -> dict[str, Any]:
        manifest = registry.load_manifest(checkpoint_hash)
        if manifest["system_id"] != "X1_AUTOGEN":
            raise ValueError("checkpoint belongs to another system")
        state = registry.load_native_state(checkpoint_hash)
        await team.load_state(state)
        round_trip = await team.save_state()
        if digest(dict(round_trip)) != manifest["native_state_sha256"]:
            raise RuntimeError("AutoGen native state did not round-trip through public load_state/save_state")
        return manifest
