from __future__ import annotations

import copy
from typing import Any

from stage2.r7_checkpoint_v1.common import digest
from stage2.r7_prospective_v1.runtime_event_adapter import (
    RuntimeStructuralBridge,
    foreign_carrier_refs_from_host,
)


def _application_root(host):
    root = getattr(host.checkout, "root", None)
    if root is not None:
        return root
    proxy_root = getattr(host.checkout, "checkout", None)
    if proxy_root is not None:
        return proxy_root
    raise ValueError("prospective host checkout does not expose an application root")


class HostIntegratedCheckpointMonitorHook:
    """Checkpoint first, then feed the completed turn's passive structural copy."""

    def __init__(self, *, recorder, bridge: RuntimeStructuralBridge):
        self.recorder = recorder
        self.bridge = bridge
        self.boundary_rows: list[dict[str, Any]] = []

    def __call__(self, *, boundary: str, event_ref: str, host, turn: int):
        carrier_refs = foreign_carrier_refs_from_host(host)
        self.recorder.external_carrier_refs = copy.deepcopy(carrier_refs)
        manifest = self.recorder(
            boundary=boundary,
            event_ref=event_ref,
            host=host,
            turn=turn,
        )
        packages = []
        if boundary == "AFTER_HOST_TURN_RETURNS":
            packages = self.bridge.flush_turn(
                checkpoint_manifest=manifest,
                checkout_root=_application_root(host),
                carrier_refs=carrier_refs,
            )
        elif boundary == "TERMINAL":
            packages = self.bridge.feed_terminal(
                checkpoint_manifest=manifest,
                pending_roles=len(host.queue),
                checkout_root=_application_root(host),
            )
        row = {
            "boundary": boundary,
            "event_ref": event_ref,
            "checkpoint_hash": manifest["checkpoint_hash"],
            "carrier_ref_count": len(carrier_refs),
            "new_package_ids": [p["package_id"] for p in packages],
        }
        row["row_hash"] = digest({k: v for k, v in row.items() if k != "row_hash"})
        self.boundary_rows.append(row)
        return manifest


class MetaGPTIntegratedCheckpointMonitorHook:
    def __init__(self, *, recorder, bridge: RuntimeStructuralBridge):
        self.recorder = recorder
        self.bridge = bridge
        self.boundary_rows: list[dict[str, Any]] = []

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
        manifest = self.recorder(
            boundary=boundary,
            event_ref=event_ref,
            env=env,
            runtime=runtime,
            checkout_api=checkout_api,
            rounds=rounds,
        )
        packages = []
        if boundary == "AFTER_EACH_ENV_RUN_K1_RETURN":
            packages = self.bridge.flush_turn(
                checkpoint_manifest=manifest,
                checkout_root=checkout_api.root,
                carrier_refs=[],
            )
        elif boundary == "TERMINAL":
            pending = sum(
                role.rc.msg_buffer._queue.qsize()
                for role in env.get_roles().values()
            )
            packages = self.bridge.feed_terminal(
                checkpoint_manifest=manifest,
                pending_roles=pending,
                checkout_root=checkout_api.root,
            )
        row = {
            "boundary": boundary,
            "event_ref": event_ref,
            "checkpoint_hash": manifest["checkpoint_hash"],
            "carrier_ref_count": 0,
            "new_package_ids": [p["package_id"] for p in packages],
        }
        row["row_hash"] = digest({k: v for k, v in row.items() if k != "row_hash"})
        self.boundary_rows.append(row)
        return manifest
