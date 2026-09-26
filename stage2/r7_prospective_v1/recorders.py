from __future__ import annotations

from typing import Any

from stage2.r7_checkpoint_v1.common import CheckpointRegistry
from stage2.r7_checkpoint_v1.controller import (
    CheckpointBoundary,
    ProspectiveCheckpointController,
)
from stage2.r7_checkpoint_v1.host_adapter import SoftwareHostCheckpointAdapter
from stage2.r7_checkpoint_v1.metagpt_adapter import MetaGPTNativeCheckpointAdapter


def _host_application_root(host):
    root = getattr(host.checkout, "root", None)
    if root is not None:
        return root
    proxy_root = getattr(host.checkout, "checkout", None)
    if proxy_root is not None:
        return proxy_root
    raise ValueError("prospective host checkout does not expose an application root")


def _replication_binding() -> dict[str, Any]:
    return {
        "checkpoint_schema_version": "RB-STAGE2-R7-CHECKPOINT-MANIFEST-v1",
        "monitor_rule_version": "RB-STAGE2-R7-STRUCTURAL-MONITOR-RULES-v1",
        "repair_package_version": "RB-STAGE2-R7-MONITOR-DERIVED-REPAIR-PACKAGE-v1",
        "repair_contract_version": "RB-STAGE2-R7-G1-PROSPECTIVE-REPAIR-CONTRACT-v1",
    }


class HostBoundaryCheckpointRecorder:
    def __init__(
        self,
        *,
        registry: CheckpointRegistry,
        controller: ProspectiveCheckpointController,
        system_id: str,
        group_id: str,
        run_id: str,
        task_id: str,
        external_carrier_refs: list[dict[str, Any]] | None = None,
    ):
        self.registry = registry
        self.controller = controller
        self.system_id = system_id
        self.group_id = group_id
        self.run_id = run_id
        self.task_id = task_id
        self.external_carrier_refs = list(external_carrier_refs or [])
        self.adapter = SoftwareHostCheckpointAdapter()
        self.manifests: list[dict[str, Any]] = []

    def __call__(self, *, boundary: str, event_ref: str, host, turn: int):
        if boundary == "BEFORE_HOST_TURN":
            kind = CheckpointBoundary.TASK_START
        elif boundary == "AFTER_HOST_TURN_RETURNS":
            self.controller.record_model_decision()
            kind = CheckpointBoundary.AFTER_NATIVE_MODEL_TURN
        elif boundary == "TERMINAL":
            kind = CheckpointBoundary.TERMINAL
        else:
            raise ValueError("unregistered host checkpoint boundary")

        manifest = self.adapter.capture(
            system_id=self.system_id,
            host=host,
            registry=self.registry,
            application_root=_host_application_root(host),
            group_id=self.group_id,
            run_id=self.run_id,
            task_id=self.task_id,
            event_ref=event_ref,
            model_visible_context={
                "boundary": boundary,
                "turn": turn,
                "queue": list(host.queue),
                "inbox_counts": {
                    role: len(items) for role, items in sorted(host.inbox.items())
                },
            },
            remaining_horizon=host.max_turns - len(host.history),
            external_carrier_refs=self.external_carrier_refs,
            replication_binding=_replication_binding(),
        )
        self.controller.register_manifest(
            boundary=kind,
            event_ref=event_ref,
            manifest=manifest,
        )
        self.manifests.append(manifest)
        return manifest


class MetaGPTBoundaryCheckpointRecorder:
    def __init__(
        self,
        *,
        registry: CheckpointRegistry,
        controller: ProspectiveCheckpointController,
        group_id: str,
        run_id: str,
        task_id: str,
    ):
        self.registry = registry
        self.controller = controller
        self.group_id = group_id
        self.run_id = run_id
        self.task_id = task_id
        self.adapter = MetaGPTNativeCheckpointAdapter()
        self.manifests: list[dict[str, Any]] = []

    def __call__(
        self,
        *,
        boundary: str,
        event_ref: str,
        env,
        runtime,
        checkout_api,
        rounds: int,
    ):
        if boundary == "BEFORE_FIRST_ENV_RUN":
            kind = CheckpointBoundary.TASK_START
        elif boundary == "AFTER_EACH_ENV_RUN_K1_RETURN":
            self.controller.record_model_decision()
            kind = CheckpointBoundary.AFTER_NATIVE_MODEL_TURN
        elif boundary == "TERMINAL":
            kind = CheckpointBoundary.TERMINAL
        else:
            raise ValueError("unregistered MetaGPT checkpoint boundary")

        manifest = self.adapter.capture_stage2(
            environment=env,
            runtime=runtime,
            registry=self.registry,
            application_root=checkout_api.root,
            group_id=self.group_id,
            run_id=self.run_id,
            task_id=self.task_id,
            event_ref=event_ref,
            model_visible_context={
                "boundary": boundary,
                "rounds": rounds,
                "environment_messages": len(env.history.get()),
                "pending_messages": sum(
                    role.rc.msg_buffer._queue.qsize()
                    for role in env.get_roles().values()
                ),
            },
            remaining_horizon=runtime.max_turns - runtime.turns,
            replication_binding=_replication_binding(),
        )
        self.controller.register_manifest(
            boundary=kind,
            event_ref=event_ref,
            manifest=manifest,
        )
        self.manifests.append(manifest)
        return manifest
