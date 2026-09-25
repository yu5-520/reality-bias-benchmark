"""Verify frozen provider and study-asset evidence before opening a natural cell."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .freeze import artifact

ROOT = Path(__file__).resolve().parents[2]
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
GIT_SHA = re.compile(r"[0-9a-f]{40}\Z")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def execution_snapshot():
    """The promotion commit may update registry/matrix, but not execution inputs."""
    frozen = artifact()
    files = {
        name: value for name, value in frozen["files_sha256"].items()
        if name != "stage2/native_v7/registry.json" and not name.startswith("docs/")
    }
    files["arena/config/model_deepseek_v0.2.json"] = digest(
        ROOT / "arena/config/model_deepseek_v0.2.json"
    )
    return {"files_sha256": files, "fixture_tree_sha256": frozen["fixture_tree"]["sha256"]}


def _frozen_file(name, expected_hash):
    if not isinstance(name, str) or not name or Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError("readiness evidence contains an unsafe file path")
    path = ROOT / name
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("readiness evidence path escapes repository")
    if not path.is_file() or digest(path) != expected_hash:
        raise ValueError(f"readiness evidence differs from frozen file: {name}")
    return path


def verify_receipt(registry, readiness):
    gate = registry["subject_readiness_gate"]
    if gate["state"] != "COMMON_PROVIDER_HANDSHAKE_RECORDED":
        raise ValueError("SUBJECT_READY requires a recorded common provider handshake")
    path_name = gate.get("receipt_path")
    expected = gate.get("receipt_sha256")
    if not isinstance(expected, str) or not SHA256.fullmatch(expected):
        raise ValueError("common receipt hash is missing or malformed")
    receipt_path = _frozen_file(path_name, expected)
    if readiness.get("common_receipt_sha256") != expected:
        raise ValueError("probe readiness does not cite the frozen common receipt")
    receipt = json.loads(receipt_path.read_text())
    required = {
        "schema": "stage2-subject-readiness-receipt-v1",
        "status": "COMMON_PROVIDER_HANDSHAKE_RECORDED_NOT_SUBJECT_READY",
        "provider": "deepseek",
        "provider_call_count": 1,
        "automatic_paid_evaluator": False,
        "scientific_task_used": False,
        "natural_cell_reserved": False,
        "registry_mutated": False,
        "natural_trajectories_after_handshake": 0,
        "promotion_required": "REVIEWED_REGISTRY_COMMIT",
    }
    if any(receipt.get(key) != value for key, value in required.items()):
        raise ValueError("common receipt is not a successful non-scientific handshake")
    if not GIT_SHA.fullmatch(str(receipt.get("execution_code_sha", ""))):
        raise ValueError("common receipt lacks an exact execution commit")
    if not receipt.get("observed_response_model") or not SHA256.fullmatch(
        str(receipt.get("raw_response_sha256", ""))
    ):
        raise ValueError("common receipt lacks raw provider provenance")
    for key in ("execution_code_sha", "subject_config_sha256", "model_config_sha256", "workflow_run_id"):
        if readiness.get(key) != receipt.get(key):
            raise ValueError(f"probe readiness differs from common receipt: {key}")
    if not isinstance(receipt.get("workflow_run_id"), int) or receipt["workflow_run_id"] <= 0:
        raise ValueError("common receipt lacks a workflow run ID")
    if receipt.get("subject_config_sha256") != digest(ROOT / "stage2/subject.json"):
        raise ValueError("subject binding changed after provider handshake")
    if receipt.get("model_config_sha256") != digest(ROOT / "arena/config/model_deepseek_v0.2.json"):
        raise ValueError("model config changed after provider handshake")
    if receipt.get("execution_snapshot") != execution_snapshot():
        raise ValueError("execution inputs changed after provider handshake")


def verify_study_manifest(probe, spec):
    key = "study_embedding" if probe == "X6" else "study_checkpoint"
    study = spec.get(key, {})
    if study.get("state") != "FROZEN_MANIFEST_VERIFIED":
        raise ValueError(f"{probe}: SUBJECT_READY requires frozen study asset manifest")
    expected = study.get("manifest_sha256")
    if not isinstance(expected, str) or not SHA256.fullmatch(expected):
        raise ValueError(f"{probe}: study manifest hash is missing or malformed")
    path = _frozen_file(study.get("manifest_path"), expected)
    manifest = json.loads(path.read_text())
    schema = "stage2-x6-embedding-manifest-v1" if probe == "X6" else "stage2-x7-checkpoint-manifest-v1"
    if manifest.get("schema") != schema or manifest.get("purpose") != "STAGE2_NATURAL_STUDY":
        raise ValueError(f"{probe}: engineering smoke asset cannot be used for natural collection")
    hashes = manifest.get("files_sha256")
    if not isinstance(hashes, dict) or not hashes or any(
        not isinstance(name, str) or not name or Path(name).is_absolute()
        or ".." in Path(name).parts or not isinstance(value, str)
        or not SHA256.fullmatch(value) for name, value in hashes.items()
    ):
        raise ValueError(f"{probe}: study manifest has invalid file hashes")
    return path, hashes
