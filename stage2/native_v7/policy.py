"""Fail-closed architectural checks for Stage-II v7.

The checks guard the experimental boundary. They do not adapt an X runtime.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROBES = {f"X{i}" for i in range(1, 8)}
CAPABILITY_PROBES = {"X4", "X5", "X6", "X7"}
NATIVE_COMMUNICATION_PROBES = {"X1", "X2", "X3"}
FORBIDDEN_KEYS = {
    "adapter",
    "common_actions",
    "common_runtime",
    "context_adapter",
    "shared_mailbox",
    "transport_contract",
}
RUNNER_STATES = {"NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING", "SUBJECT_READY"}
READINESS_AUTHORIZATION = "CALL_REAL_STAGE2_SUBJECT_READINESS_API"


def load_registry(path=None):
    path = Path(path) if path else BASE / "registry.json"
    data = json.loads(path.read_text())
    validate_registry(data)
    return data


def validate_registry(data):
    if data.get("schema") != "stage2-native-execution-registry-v2":
        raise ValueError("unexpected v7 registry schema")
    probes = data.get("probes", {})
    if set(probes) != PROBES:
        raise ValueError("v7 registry must contain exactly X1-X7")

    substrates = data.get("background_substrates", {})
    host = substrates.get("software_engineering_host_v1")
    if not isinstance(host, dict) or set(host.get("applies_to", [])) != CAPABILITY_PROBES:
        raise ValueError("capability-layer background host must be explicit for X4-X7")
    if not isinstance(data.get("forbidden_global_normalization"), list):
        raise ValueError("global-normalization prohibitions must be explicit")

    readiness_gate = data.get("subject_readiness_gate")
    if not isinstance(readiness_gate, dict):
        raise ValueError("subject readiness gate must be explicit")
    if readiness_gate.get("state") not in {
        "IMPLEMENTED_NO_LIVE_RECEIPT",
        "COMMON_PROVIDER_HANDSHAKE_RECORDED",
    }:
        raise ValueError("subject readiness gate has an invalid state")
    if readiness_gate.get("authorization_phrase") != READINESS_AUTHORIZATION:
        raise ValueError("subject readiness authorization phrase differs from frozen policy")
    if readiness_gate.get("max_provider_calls") != 1:
        raise ValueError("subject readiness must be a one-call provider handshake")
    if readiness_gate.get("automatic_paid_evaluator") is not False:
        raise ValueError("subject readiness must never call a paid evaluator")
    if readiness_gate.get("natural_task_allowed") is not False:
        raise ValueError("subject readiness must not execute T1-T3")
    if readiness_gate.get("registry_mutation") != "REVIEWED_COMMIT_ONLY":
        raise ValueError("subject readiness workflow must not auto-open collection")

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

        background = spec.get("background_substrate_id")
        if pid in CAPABILITY_PROBES:
            if background != "software_engineering_host_v1":
                raise ValueError(f"{pid}: capability-layer background host must be declared")
        elif pid in NATIVE_COMMUNICATION_PROBES and background is not None:
            raise ValueError(f"{pid}: native communication condition must not inherit the baseline mailbox")

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
            if background and host.get("status") != "FROZEN_DEINSTRUMENTED_HOST":
                raise ValueError(f"{pid}: capability runner cannot verify before background host is frozen")
            argv = launch.get("argv_template")
            if (
                launch.get("state") != "VERIFIED_NATIVE_ENTRYPOINT"
                or not isinstance(argv, list)
                or not argv
            ):
                raise ValueError(f"{pid}: verified runner lacks a native entrypoint")
            if state == "SUBJECT_READY":
                readiness = spec.get("subject_readiness")
                if not isinstance(readiness, dict) or readiness.get("state") != "VERIFIED":
                    raise ValueError(f"{pid}: SUBJECT_READY requires frozen readiness evidence")
                for key in (
                    "execution_code_sha",
                    "common_receipt_sha256",
                    "execution_surface_sha256",
                    "subject_config_sha256",
                    "model_config_sha256",
                    "workflow_run_id",
                ):
                    if not readiness.get(key):
                        raise ValueError(f"{pid}: readiness evidence lacks {key}")
                if pid == "X6" and spec.get("study_embedding", {}).get("state") != "FROZEN_MANIFEST_VERIFIED":
                    raise ValueError("X6: SUBJECT_READY requires frozen study embedding manifest")
                if pid == "X7" and spec.get("study_checkpoint", {}).get("state") != "FROZEN_MANIFEST_VERIFIED":
                    raise ValueError("X7: SUBJECT_READY requires frozen study checkpoint manifest")
        elif state == "PENDING_NATIVE_RUNNER":
            if launch.get("argv_template") is not None:
                raise ValueError(f"{pid}: pending runner must not expose an executable collection command")
        else:
            raise ValueError(f"{pid}: unrecognized collection state: {state}")
    return True
