from __future__ import annotations

import copy
import json
from typing import Any

from stage2.r7_checkpoint_v1.common import CheckpointRegistry, digest


METAGPT_COMMIT = "11cdf466d042aece04fc6cfd13b28e1a70341b1f"
ADAPTER_ID = "stage2-r7-metagpt-native-checkpoint-v1"


def _canonicalize_metagpt_state(value: Any, key: str | None = None) -> Any:
    """Canonicalize only MetaGPT fields whose native type is set-like.

    Message/order-bearing lists remain untouched. Pydantic serializes sets such
    as Role.addresses, RoleContext.watch and Message.send_to as JSON lists whose
    element order depends on Python hash iteration; those lists are sorted only
    for content-address stability.
    """
    if isinstance(value, dict):
        return {k: _canonicalize_metagpt_state(v, k) for k, v in value.items()}
    if isinstance(value, list):
        rows = [_canonicalize_metagpt_state(v, None) for v in value]
        if key in {"addresses", "watch", "send_to"}:
            return sorted(rows, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))
        return rows
    return value


def runtime_state_payload(runtime) -> dict[str, Any]:
    """Serialize Stage-II-owned RuntimeState fields without touching MetaGPT internals."""
    return {
        "max_turns": int(runtime.max_turns),
        "turns": int(runtime.turns),
        "answer": runtime.answer,
        "stop_reason": runtime.stop_reason,
        "history": copy.deepcopy(runtime.history),
        "task": copy.deepcopy(getattr(runtime, "task", None)),
    }


def restore_runtime_state(runtime, payload: dict[str, Any]) -> None:
    runtime.max_turns = int(payload["max_turns"])
    runtime.turns = int(payload["turns"])
    runtime.answer = payload.get("answer")
    runtime.stop_reason = payload.get("stop_reason")
    runtime.history = copy.deepcopy(payload.get("history") or [])
    if payload.get("task") is not None:
        runtime.task = copy.deepcopy(payload["task"])


class MetaGPTNativeCheckpointAdapter:
    """MetaGPT public model serialization plus Stage-II runtime envelope.

    MetaGPT's pinned upstream tests explicitly support Environment.model_dump()
    followed by Environment(**payload, context=context). Stage-II-owned pointers
    such as provider/checkout bindings remain outside that native payload and are
    rebound by the prospective host constructor.
    """

    framework_binding = {
        "framework": "MetaGPT",
        "version": "1.0.0",
        "upstream_commit": METAGPT_COMMIT,
        "state_api": ["Environment.model_dump", "Environment(**state, context=context)"],
    }

    def serialize_environment(self, environment) -> dict[str, Any]:
        state = environment.model_dump(mode="json")
        if not isinstance(state, dict):
            raise TypeError("MetaGPT Environment.model_dump must return a mapping")
        return _canonicalize_metagpt_state(state)

    def restore_environment(self, *, environment_class, state: dict[str, Any], context):
        return environment_class(**copy.deepcopy(state), context=context)

    def validate_environment_round_trip(self, *, environment, environment_class, context) -> dict[str, Any]:
        state = self.serialize_environment(environment)
        restored = self.restore_environment(
            environment_class=environment_class,
            state=state,
            context=context,
        )
        state2 = self.serialize_environment(restored)
        if digest(state) != digest(state2):
            raise RuntimeError("MetaGPT public environment serialization did not round-trip")
        return state


    def serialize_stage2_environment(self, environment) -> dict[str, Any]:
        """Serialize native MetaGPT environment/role state without Stage-II object pointers."""
        env_state = _canonicalize_metagpt_state(environment.model_dump(mode="json"))
        env_state = copy.deepcopy(env_state)
        env_state.pop("roles", None)
        roles = []
        for role in sorted(environment.roles.values(), key=lambda item: item.name):
            roles.append({
                "name": role.name,
                "profile": role.profile,
                "state": _canonicalize_metagpt_state(role.model_dump(mode="json")),
            })
        return {
            "schema": "stage2-r7-metagpt-stage2-environment-state-v1",
            "environment": env_state,
            "roles": roles,
        }

    def restore_stage2_environment(
        self,
        *,
        state: dict[str, Any],
        environment_class,
        role_class,
        context,
        runtime,
        checkout_api,
        directory: dict[str, Any],
        entry: str,
        llm_factory,
    ):
        if state.get("schema") != "stage2-r7-metagpt-stage2-environment-state-v1":
            raise ValueError("unexpected Stage-II MetaGPT checkpoint schema")
        env = environment_class(**copy.deepcopy(state["environment"]), context=context)
        restored_roles = []
        for row in state["roles"]:
            role_state = copy.deepcopy(row["state"])
            role_state.update({
                "llm": llm_factory(row["name"]),
                "stage2_runtime": runtime,
                "stage2_checkout": checkout_api,
                "stage2_directory": directory,
                "stage2_entry": entry,
            })
            restored_roles.append(role_class(**role_state))
        env.add_roles(restored_roles)
        round_trip = self.serialize_stage2_environment(env)
        if digest(round_trip) != digest(state):
            def first_diff(left, right, path="root"):
                if type(left) is not type(right):
                    return f"{path}:type:{type(left).__name__}!={type(right).__name__}"
                if isinstance(left, dict):
                    if set(left) != set(right):
                        return f"{path}:keys:{sorted(set(left)^set(right))}"
                    for key in sorted(left):
                        found = first_diff(left[key], right[key], f"{path}.{key}")
                        if found:
                            return found
                    return None
                if isinstance(left, list):
                    if len(left) != len(right):
                        return f"{path}:len:{len(left)}!={len(right)}"
                    for index, (lv, rv) in enumerate(zip(left, right)):
                        found = first_diff(lv, rv, f"{path}[{index}]")
                        if found:
                            return found
                    return None
                if left != right:
                    return f"{path}:value:{left!r}!={right!r}"
                return None
            raise RuntimeError(
                "Stage-II MetaGPT environment/role state did not round-trip; "
                + str(first_diff(state, round_trip))
            )
        return env

    def capture(
        self,
        *,
        environment,
        runtime,
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
        native_state = {
            "environment": self.serialize_environment(environment),
            "stage2_runtime": runtime_state_payload(runtime),
        }
        return registry.capture(
            system_id="X2_METAGPT",
            group_id=group_id,
            run_id=run_id,
            task_id=task_id,
            event_ref=event_ref,
            adapter_id=ADAPTER_ID,
            framework_binding=self.framework_binding,
            native_state=native_state,
            application_root=application_root,
            model_visible_context=model_visible_context,
            remaining_horizon=remaining_horizon,
            external_carrier_refs=external_carrier_refs,
            restore_capability="FULL_NATIVE",
            replication_binding=replication_binding,
        )
