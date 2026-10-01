"""Execution harness for a frozen route-repair plan.

The harness invokes only an injected native executor. It does not know how to
patch a framework or access framework-private state.
"""
from __future__ import annotations

import copy
from typing import Any, Callable, Mapping

from stage2.r7_prospective_v1.repair_boundary_watcher import RepairBoundaryWatcher
from stage2.route_repair.plan import (
    build_boundary_package,
    validate_agent_route_choice,
)


class RouteRepairSession:
    def __init__(
        self,
        *,
        plan: Mapping[str, Any],
        preserve_hashes: Mapping[str, str],
        native_executor: Callable[[dict[str, Any]], Mapping[str, Any]],
        preserve_hash_provider: Callable[[], Mapping[str, str]],
    ):
        if plan.get("repair_gate_status") != "COMPLETE_FOR_ROUTE_REPAIR":
            raise ValueError("route repair plan is not executable")
        self.plan = copy.deepcopy(dict(plan))
        self.package = build_boundary_package(self.plan)
        self.watcher = RepairBoundaryWatcher(
            package=self.package,
            preserve_hashes=dict(preserve_hashes),
        )
        self.native_executor = native_executor
        self.preserve_hash_provider = preserve_hash_provider
        self.closed = False

    def execute(self, agent_choice: Mapping[str, Any]) -> dict[str, Any]:
        if self.closed:
            raise RuntimeError("route repair session already closed")
        choice = validate_agent_route_choice(agent_choice, self.plan)
        receipts = []
        for index, ref in enumerate(choice["modify_refs"], start=1):
            request = {
                "schema": "RB-STAGE2-NATIVE-ROUTE-REPAIR-REQUEST-v1",
                "route_plan_hash": self.plan["plan_hash"],
                "choice_hash": choice["choice_hash"],
                "target_ref": ref,
                "reason": choice["reason_by_ref"].get(ref),
            }
            response = dict(self.native_executor(copy.deepcopy(request)))
            required = {
                "native_interface",
                "mutation_class",
                "before_hash",
                "after_hash",
            }
            missing = required - set(response)
            if missing:
                raise ValueError(
                    "native executor receipt missing: " + ",".join(sorted(missing))
                )
            action = {
                "action_ref": response.get(
                    "action_ref", f"{choice['choice_hash']}:action:{index}"
                ),
                "native_interface": response["native_interface"],
                "target_ref": ref,
                "mutation_class": response["mutation_class"],
                "before_hash": response["before_hash"],
                "after_hash": response["after_hash"],
            }
            receipts.append(
                self.watcher.record_action(
                    action,
                    current_preserve_hashes=dict(self.preserve_hash_provider()),
                )
            )

        boundary = self.watcher.finish(
            current_preserve_hashes=dict(self.preserve_hash_provider())
        )
        self.closed = True
        return {
            "schema": "RB-STAGE2-ROUTE-REPAIR-RESULT-v1",
            "plan_hash": self.plan["plan_hash"],
            "choice_hash": choice["choice_hash"],
            "native_action_receipts": receipts,
            "boundary_result": boundary,
            "repair_executor_exited": True,
        }

    def observe_post_repair(self, event: Mapping[str, Any]) -> dict[str, Any]:
        if not self.closed:
            raise RuntimeError("repair executor must exit before post-repair observation")
        return self.watcher.observe_post_repair(dict(event))
