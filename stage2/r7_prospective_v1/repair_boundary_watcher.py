from __future__ import annotations

import copy
from typing import Any

from stage2.r7_checkpoint_v1.common import digest


class RepairBoundaryViolation(RuntimeError):
    pass


FORBIDDEN_MUTATION_CLASSES = {
    "FRAMEWORK_SOURCE_MODIFICATION",
    "PROTOCOL_MODIFICATION",
    "PRIVATE_RUNTIME_STATE_MUTATION",
    "MCP_BACKEND_DIRECT_MUTATION",
    "RAG_INTERNAL_MUTATION",
    "MEMORYBANK_INTERNAL_MUTATION",
    "LONGLMLINGUA_INTERNAL_MUTATION",
    "WHOLE_SYSTEM_RESET",
}

ALLOWED_MUTATION_CLASSES = {
    "APPLICATION_WRITE",
    "PROCESS_REVISION",
    "NATIVE_MESSAGE",
    "DEPENDENT_REOPEN",
}


def verify_package_hash(package: dict[str, Any]) -> bool:
    if not package.get("package_hash"):
        return False
    payload = copy.deepcopy(package)
    expected = payload.pop("package_hash")
    return digest(payload) == expected


class RepairBoundaryWatcher:
    """Fail-closed boundary watcher around one frozen repair package."""

    def __init__(
        self,
        *,
        package: dict[str, Any],
        preserve_hashes: dict[str, str],
    ):
        self.package = copy.deepcopy(package)
        if not verify_package_hash(self.package):
            raise RepairBoundaryViolation("PACKAGE_HASH_MISMATCH")
        if self.package.get("repair_gate_status") != "COMPLETE_FOR_STRUCTURED_REPAIR":
            raise RepairBoundaryViolation(
                "PACKAGE_NOT_COMPLETE_FOR_STRUCTURED_REPAIR:"
                + str(self.package.get("repair_gate_status"))
            )
        declared_preserve = set(self.package.get("preserve_refs") or [])
        if declared_preserve != set(preserve_hashes):
            raise RepairBoundaryViolation("PRESERVE_SET_BINDING_MISMATCH")
        self.initial_preserve_hashes = dict(preserve_hashes)
        self.actions: list[dict[str, Any]] = []
        self.violations: list[str] = []
        self.closed = False
        self.post_repair_events: list[dict[str, Any]] = []

    def _fail(self, code: str):
        self.violations.append(code)
        raise RepairBoundaryViolation(code)

    def _check_preserve(self, current: dict[str, str]):
        if set(current) != set(self.initial_preserve_hashes):
            self._fail("PRESERVE_SET_MEMBERSHIP_MISMATCH")
        for ref, frozen_hash in self.initial_preserve_hashes.items():
            if current.get(ref) != frozen_hash:
                self._fail("PRESERVE_SET_MISMATCH:" + ref)

    def record_action(
        self,
        action: dict[str, Any],
        *,
        current_preserve_hashes: dict[str, str],
    ) -> dict[str, Any]:
        if self.closed:
            self._fail("REPAIR_EXECUTOR_ALREADY_EXITED")
        required = {
            "action_ref",
            "native_interface",
            "target_ref",
            "mutation_class",
            "before_hash",
            "after_hash",
        }
        missing = required - set(action)
        if missing:
            self._fail("REPAIR_ACTION_FIELDS_MISSING:" + ",".join(sorted(missing)))

        mutation_class = action["mutation_class"]
        if mutation_class in FORBIDDEN_MUTATION_CLASSES:
            self._fail("FORBIDDEN_MUTATION_CLASS:" + mutation_class)
        if mutation_class not in ALLOWED_MUTATION_CLASSES:
            self._fail("UNKNOWN_MUTATION_CLASS:" + str(mutation_class))

        target = action["target_ref"]
        affected = set(self.package.get("affected_closure_refs") or [])
        preserve = set(self.package.get("preserve_refs") or [])
        if target in preserve:
            self._fail("REPAIR_TARGET_INSIDE_PRESERVE_SET:" + target)
        if target not in affected:
            self._fail("REPAIR_TARGET_OUTSIDE_AFFECTED_CLOSURE:" + target)

        allowed_surfaces = self.package.get("allowed_repair_surface") or []
        if not any(surface.endswith(":" + target) for surface in allowed_surfaces):
            self._fail("NO_FROZEN_NATIVE_REPAIR_SURFACE:" + target)

        interface = str(action["native_interface"])
        if not interface or interface.startswith(("private:", "direct-backend:", "framework-patch:")):
            self._fail("INVALID_NATIVE_INTERFACE:" + interface)

        self._check_preserve(current_preserve_hashes)
        row = copy.deepcopy(action)
        row["package_id"] = self.package["package_id"]
        row["package_hash"] = self.package["package_hash"]
        row["boundary_status"] = "PASS"
        row["action_hash"] = digest(
            {k: v for k, v in row.items() if k != "action_hash"}
        )
        self.actions.append(row)
        return copy.deepcopy(row)

    def finish(
        self,
        *,
        current_preserve_hashes: dict[str, str],
    ) -> dict[str, Any]:
        if self.closed:
            self._fail("REPAIR_EXECUTOR_ALREADY_EXITED")
        self._check_preserve(current_preserve_hashes)
        self.closed = True
        result = {
            "schema": "RB-STAGE2-R7-G1-REPAIR-BOUNDARY-RESULT-v1",
            "package_id": self.package["package_id"],
            "package_hash": self.package["package_hash"],
            "action_count": len(self.actions),
            "repair_executor_exited": True,
            "preserve_set_intact": True,
            "boundary_violations": list(self.violations),
            "status": "PASS",
        }
        result["result_hash"] = digest(
            {k: v for k, v in result.items() if k != "result_hash"}
        )
        return result

    def observe_post_repair(self, event: dict[str, Any]) -> dict[str, Any]:
        if not self.closed:
            self._fail("POST_REPAIR_WATCH_BEFORE_EXECUTOR_EXIT")
        row = copy.deepcopy(event)
        row["repair_action_allowed"] = False
        row["watch_index"] = len(self.post_repair_events) + 1
        row["watch_hash"] = digest(
            {k: v for k, v in row.items() if k != "watch_hash"}
        )
        self.post_repair_events.append(row)
        return copy.deepcopy(row)

    def attempt_post_repair_action(self, _action: dict[str, Any]):
        self._fail("POST_REPAIR_CONTINUOUS_REPAIR_FORBIDDEN")
