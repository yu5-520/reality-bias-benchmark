"""Fail-closed architectural checks for Stage-II v7.

The checks guard the experimental boundary. They do not adapt an X runtime.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROBES = {f"X{i}" for i in range(1, 8)}
FORBIDDEN_TEXT = (
    "CodingArena",
    "RoleMailboxTransport",
    "context_adapter",
    "available_actions",
)
FORBIDDEN_KEYS = {
    "adapter",
    "common_actions",
    "common_runtime",
    "context_adapter",
    "shared_mailbox",
    "transport_contract",
}
RUNNER_STATES = {"NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING", "SUBJECT_READY"}


def load_registry(path=None):
    path = Path(path) if path else BASE / "registry.json"
    data = json.loads(path.read_text())
    validate_registry(data)
    return data


def validate_registry(data):
    if data.get("schema") != "stage2-native-execution-registry-v1":
        raise ValueError("unexpected v7 registry schema")
    probes = data.get("probes", {})
    if set(probes) != PROBES:
        raise ValueError("v7 registry must contain exactly X1-X7")
    envs = set()
    for pid, spec in probes.items():
        if FORBIDDEN_KEYS & set(spec):
            raise ValueError(f"{pid}: shared execution adapter key is forbidden")
        if spec.get("runtime_scope") != "independent":
            raise ValueError(f"{pid}: runtime must be independently frozen")
        if not spec.get("execution_owner"):
            raise ValueError(f"{pid}: execution owner must be explicit")
        if not spec.get("integration_kind"):
            raise ValueError(f"{pid}: integration kind must be explicit")
        observer = spec.get("observer", {})
        if observer.get("mode") != "external" or observer.get("may_mutate_execution") is not False:
            raise ValueError(f"{pid}: observer must be external and non-mutating")
        env = spec.get("environment_id")
        if not env or env in envs:
            raise ValueError(f"{pid}: environment_id must be unique")
        envs.add(env)

        launch = spec.get("launch", {})
        state = spec.get("collection_state")
        if state in RUNNER_STATES:
            argv = launch.get("argv_template")
            if (
                launch.get("state") != "VERIFIED_NATIVE_ENTRYPOINT"
                or not isinstance(argv, list)
                or not argv
            ):
                raise ValueError(f"{pid}: verified runner lacks a native entrypoint")
        elif state == "PENDING_NATIVE_RUNNER":
            if launch.get("argv_template") is not None:
                raise ValueError(f"{pid}: pending runner must not expose an executable collection command")
        else:
            raise ValueError(f"{pid}: unrecognized collection state: {state}")

        raw_spec = json.dumps(spec, sort_keys=True)
        for marker in FORBIDDEN_TEXT:
            if marker in raw_spec:
                raise ValueError(f"{pid}: embeds forbidden shared runtime marker: {marker}")
    return True
