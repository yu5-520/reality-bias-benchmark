from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable


class CheckpointBoundary(str, Enum):
    TASK_START = "TASK_START"
    AFTER_NATIVE_MODEL_TURN = "AFTER_NATIVE_MODEL_TURN_AT_QUIESCENT_BOUNDARY"
    AFTER_STATE_CHANGING_ACTION = "AFTER_STATE_CHANGING_NATIVE_ACTION_AT_QUIESCENT_BOUNDARY"
    FIRST_MONITOR_REPAIR_ELIGIBLE = "FIRST_MONITOR_REPAIR_ELIGIBLE_POINT"
    PRE_REPAIR = "IMMEDIATELY_BEFORE_REPAIR"
    POST_REPAIR = "IMMEDIATELY_AFTER_REPAIR"
    TERMINAL = "TERMINAL"


@dataclass(frozen=True)
class CheckpointPointer:
    boundary: str
    event_ref: str
    checkpoint_hash: str
    checkpoint_id: str
    model_decision_sequence: int
    restore_capability: str


class ProspectiveCheckpointController:
    """External monitor-side checkpoint ledger for the prospective extension.

    The controller does not inspect framework-private state. An adapter callback
    performs the system-specific public/native save. The controller only freezes
    ordering, model-decision sequence, first eligible repair point and checkpoint
    references.
    """

    def __init__(self):
        self.model_decision_sequence = 0
        self.checkpoints: list[CheckpointPointer] = []
        self.first_eligible_event_ref: str | None = None
        self.first_eligible_checkpoint: CheckpointPointer | None = None

    def record_model_decision(self) -> int:
        self.model_decision_sequence += 1
        return self.model_decision_sequence

    def register_manifest(self, *, boundary: CheckpointBoundary, event_ref: str, manifest: dict[str, Any]) -> CheckpointPointer:
        if not manifest.get("checkpoint_hash") or not manifest.get("checkpoint_id"):
            raise ValueError("checkpoint manifest is not content addressed")
        pointer = CheckpointPointer(
            boundary=boundary.value,
            event_ref=event_ref,
            checkpoint_hash=manifest["checkpoint_hash"],
            checkpoint_id=manifest["checkpoint_id"],
            model_decision_sequence=self.model_decision_sequence,
            restore_capability=manifest["restore_capability"],
        )
        self.checkpoints.append(pointer)
        if boundary is CheckpointBoundary.FIRST_MONITOR_REPAIR_ELIGIBLE:
            if self.first_eligible_event_ref is not None:
                raise RuntimeError("first eligible repair point is already frozen")
            self.first_eligible_event_ref = event_ref
            self.first_eligible_checkpoint = pointer
        return pointer

    async def capture_async(
        self,
        *,
        boundary: CheckpointBoundary,
        event_ref: str,
        capture: Callable[[], Awaitable[dict[str, Any]]],
    ) -> CheckpointPointer:
        manifest = await capture()
        return self.register_manifest(boundary=boundary, event_ref=event_ref, manifest=manifest)

    def capture_sync(
        self,
        *,
        boundary: CheckpointBoundary,
        event_ref: str,
        capture: Callable[[], dict[str, Any]],
    ) -> CheckpointPointer:
        manifest = capture()
        return self.register_manifest(boundary=boundary, event_ref=event_ref, manifest=manifest)

    def repair_parent_at_freeze(self) -> CheckpointPointer:
        """Return the parent frozen at first eligibility, even after natural A continues.

        Exactness is established when FIRST_MONITOR_REPAIR_ELIGIBLE is registered.
        Later natural-A model decisions do not rewrite or stale that historical
        checkpoint; they only mean it is no longer the *current* runtime state.
        """
        if self.first_eligible_checkpoint is None:
            raise RuntimeError("no first eligible repair checkpoint has been frozen")
        if self.first_eligible_checkpoint.restore_capability != "FULL_NATIVE":
            raise RuntimeError("first eligible checkpoint is not FULL_NATIVE")
        return self.first_eligible_checkpoint

    def repair_parent(self) -> CheckpointPointer:
        if self.first_eligible_checkpoint is None:
            raise RuntimeError("no first eligible repair checkpoint has been frozen")
        if self.first_eligible_checkpoint.restore_capability != "FULL_NATIVE":
            raise RuntimeError("first eligible checkpoint is not FULL_NATIVE")
        if self.first_eligible_checkpoint.model_decision_sequence != self.model_decision_sequence:
            raise RuntimeError(
                "an uncheckpointed model decision occurred after the frozen first eligible parent"
            )
        return self.first_eligible_checkpoint

    def ledger(self) -> dict[str, Any]:
        return {
            "schema": "RB-STAGE2-R7-PROSPECTIVE-CHECKPOINT-LEDGER-v1",
            "model_decision_sequence": self.model_decision_sequence,
            "first_eligible_event_ref": self.first_eligible_event_ref,
            "first_eligible_checkpoint_hash": (
                self.first_eligible_checkpoint.checkpoint_hash
                if self.first_eligible_checkpoint is not None
                else None
            ),
            "checkpoints": [
                {
                    "boundary": p.boundary,
                    "event_ref": p.event_ref,
                    "checkpoint_hash": p.checkpoint_hash,
                    "checkpoint_id": p.checkpoint_id,
                    "model_decision_sequence": p.model_decision_sequence,
                    "restore_capability": p.restore_capability,
                }
                for p in self.checkpoints
            ],
        }
