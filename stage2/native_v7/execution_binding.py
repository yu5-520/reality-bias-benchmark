"""Content-address the exact per-probe Stage-II forward execution surface.

Control-plane metadata may be reviewed after a live readiness receipt without
changing the scientific execution surface. Natural collection recomputes this
digest immediately before reserving a cell.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "stage2/native_v7"
STAGE2 = ROOT / "stage2"

COMMON_FILES = (
    "adapters/deepseek_chat.py",
    "arena/providers.py",
    "arena/config/model_deepseek_v0.2.json",
    "stage2/tasks.json",
    "stage2/roles.json",
    "stage2/subject.json",
    "stage2/native_v7/collect.py",
    "stage2/native_v7/policy.py",
    "stage2/native_v7/observer.py",
    "stage2/native_v7/execution_binding.py",
)

PROBE_FILES = {
    "X1": ("stage2/native_v7/x1_autogen/runner.py",),
    "X2": (
        "stage2/native_v7/x2_metagpt/checkout.py",
        "stage2/native_v7/x2_metagpt/runner.py",
    ),
    "X3": (
        "stage2/native_v7/x3_a2a/checkout.py",
        "stage2/native_v7/x3_a2a/proxy.py",
        "stage2/native_v7/x3_a2a/runner.py",
        "stage2/native_v7/x3_a2a/service.py",
    ),
    "X4": (
        "stage2/native_v7/software_host_v1.py",
        "stage2/native_v7/x4_mcp/client_call.py",
        "stage2/native_v7/x4_mcp/runner.py",
        "stage2/native_v7/x4_mcp/server.py",
        "stage2/native_v7/x4_mcp/wire_proxy.py",
    ),
    "X5": (
        "stage2/native_v7/software_host_v1.py",
        "stage2/retrieval.py",
        "stage2/native_v7/x5_rag/context.py",
        "stage2/native_v7/x5_rag/runner.py",
    ),
    "X6": (
        "stage2/native_v7/software_host_v1.py",
        "stage2/native_v7/x6_memorybank/context.py",
        "stage2/native_v7/x6_memorybank/runner.py",
    ),
    "X7": (
        "stage2/native_v7/software_host_v1.py",
        "stage2/native_v7/x7_longllmlingua/context.py",
        "stage2/native_v7/x7_longllmlingua/runner.py",
    ),
}

REF_KEYS = (
    "environment_id",
    "integration_kind",
    "background_substrate_id",
    "source_repo",
    "source_commit",
    "sdk_repo",
    "sdk_commit",
    "protocol_version",
    "package_version",
    "implementation_sha256",
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixture_tree():
    rows = []
    files = {}
    for path in sorted((STAGE2 / "fixtures/project").rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and not path.name.startswith("."):
            rel = str(path.relative_to(ROOT))
            digest = sha256(path)
            files[rel] = digest
            rows.append(f"{rel}\0{digest}")
    return {
        "files": files,
        "tree_sha256": hashlib.sha256("\n".join(rows).encode()).hexdigest(),
    }


def _probe_refs(spec):
    refs = {key: spec.get(key) for key in REF_KEYS if spec.get(key) is not None}
    refs["launch_argv_template"] = spec.get("launch", {}).get("argv_template")
    return refs


def execution_surface(probe, registry=None):
    if probe not in PROBE_FILES:
        raise ValueError("probe is outside frozen X1-X7")
    if registry is None:
        registry = json.loads((BASE / "registry.json").read_text())
    spec = registry["probes"][probe]
    paths = sorted(set(COMMON_FILES + PROBE_FILES[probe]))
    files = {}
    for rel in paths:
        path = ROOT / rel
        if not path.is_file():
            raise ValueError(f"execution-surface file is missing: {rel}")
        files[rel] = sha256(path)
    return {
        "schema": "stage2-forward-execution-surface-v1",
        "probe": probe,
        "files_sha256": files,
        "fixture": fixture_tree(),
        "probe_refs": _probe_refs(spec),
    }


def execution_surface_digest(probe, registry=None):
    payload = execution_surface(probe, registry=registry)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()
