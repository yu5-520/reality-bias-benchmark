from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Mapping


def stable_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(value: Any) -> str:
    if isinstance(value, bytes):
        raw = value
    else:
        raw = stable_json_bytes(value)
    return hashlib.sha256(raw).hexdigest()


def file_tree_manifest(root: str | Path) -> dict[str, str]:
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("checkpoint application root must be a directory")
    rows: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"checkpoint tree may not contain symlinks: {path}")
        if not path.is_file():
            continue
        rel = str(path.relative_to(root))
        if "__pycache__" in path.parts or rel.endswith(".pyc"):
            continue
        rows[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return rows


def file_tree_digest(root: str | Path) -> str:
    return digest(file_tree_manifest(root))


def copy_tree_verified(source: str | Path, destination: str | Path) -> dict[str, str]:
    source = Path(source).resolve(strict=True)
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    shutil.copytree(source, destination)
    src = file_tree_manifest(source)
    dst = file_tree_manifest(destination)
    if src != dst:
        raise RuntimeError("checkpoint application snapshot copy mismatch")
    return src


def restore_tree_verified(snapshot: str | Path, destination: str | Path) -> dict[str, str]:
    snapshot = Path(snapshot).resolve(strict=True)
    destination = Path(destination)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(snapshot, destination)
    src = file_tree_manifest(snapshot)
    dst = file_tree_manifest(destination)
    if src != dst:
        raise RuntimeError("checkpoint application restore mismatch")
    return dst


class CheckpointRegistry:
    """Content-addressed checkpoint registry.

    The registry stores only experiment-owned runtime state, application state,
    and read-only references to foreign information carriers. It never mutates a
    studied framework, protocol, RAG index, memory store, or compressor.
    """

    SCHEMA = "RB-STAGE2-R7-CHECKPOINT-MANIFEST-v1"

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def capture(
        self,
        *,
        system_id: str,
        group_id: str,
        run_id: str,
        task_id: str,
        event_ref: str,
        adapter_id: str,
        framework_binding: Mapping[str, Any],
        native_state: Mapping[str, Any],
        application_root: str | Path,
        model_visible_context: Any,
        remaining_horizon: Any,
        external_carrier_refs: list[dict[str, Any]] | None = None,
        restore_capability: str,
        replication_binding: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if restore_capability not in {"FULL_NATIVE", "PARTIAL_NATIVE", "UNSUPPORTED"}:
            raise ValueError("invalid restore capability")
        native_state_obj = dict(native_state)
        native_state_hash = digest(native_state_obj)
        context_hash = digest(model_visible_context)
        app_manifest = file_tree_manifest(application_root)
        app_hash = digest(app_manifest)
        external = list(external_carrier_refs or [])
        payload = {
            "schema": self.SCHEMA,
            "system_id": system_id,
            "group_id": group_id,
            "run_id": run_id,
            "task_id": task_id,
            "event_ref": event_ref,
            "adapter_id": adapter_id,
            "framework_binding": dict(framework_binding),
            "native_state_sha256": native_state_hash,
            "application_state_sha256": app_hash,
            "model_visible_context_sha256": context_hash,
            "remaining_horizon": remaining_horizon,
            "external_carrier_refs": external,
            "restore_capability": restore_capability,
            "replication_binding": dict(replication_binding or {}),
        }
        checkpoint_hash = digest(payload)
        checkpoint_id = f"rbcp:{system_id}:{checkpoint_hash[:24]}"
        checkpoint_dir = self.root / checkpoint_hash
        if checkpoint_dir.exists():
            existing = json.loads((checkpoint_dir / "manifest.json").read_text(encoding="utf-8"))
            if existing.get("checkpoint_hash") != checkpoint_hash:
                raise RuntimeError("checkpoint id collision")
            return existing

        checkpoint_dir.mkdir()
        (checkpoint_dir / "native_state.json").write_bytes(stable_json_bytes(native_state_obj) + b"\n")
        (checkpoint_dir / "model_context.json").write_bytes(stable_json_bytes(model_visible_context) + b"\n")
        copy_tree_verified(application_root, checkpoint_dir / "application")
        manifest = {
            **payload,
            "checkpoint_id": checkpoint_id,
            "checkpoint_hash": checkpoint_hash,
            "application_file_hashes": app_manifest,
        }
        (checkpoint_dir / "manifest.json").write_bytes(stable_json_bytes(manifest) + b"\n")
        self._verify_checkpoint_dir(checkpoint_dir, manifest)
        return manifest

    def _verify_checkpoint_dir(self, checkpoint_dir: Path, manifest: Mapping[str, Any]) -> None:
        native = json.loads((checkpoint_dir / "native_state.json").read_text(encoding="utf-8"))
        context = json.loads((checkpoint_dir / "model_context.json").read_text(encoding="utf-8"))
        if digest(native) != manifest["native_state_sha256"]:
            raise RuntimeError("native checkpoint state hash mismatch")
        if digest(context) != manifest["model_visible_context_sha256"]:
            raise RuntimeError("model-visible context hash mismatch")
        app_manifest = file_tree_manifest(checkpoint_dir / "application")
        if digest(app_manifest) != manifest["application_state_sha256"]:
            raise RuntimeError("application checkpoint hash mismatch")
        if app_manifest != manifest["application_file_hashes"]:
            raise RuntimeError("application checkpoint file manifest mismatch")
        base = {
            key: manifest[key]
            for key in [
                "schema",
                "system_id",
                "group_id",
                "run_id",
                "task_id",
                "event_ref",
                "adapter_id",
                "framework_binding",
                "native_state_sha256",
                "application_state_sha256",
                "model_visible_context_sha256",
                "remaining_horizon",
                "external_carrier_refs",
                "restore_capability",
                "replication_binding",
            ]
        }
        if digest(base) != manifest["checkpoint_hash"]:
            raise RuntimeError("checkpoint manifest content address mismatch")

    def checkpoint_dir(self, checkpoint_hash: str) -> Path:
        path = self.root / checkpoint_hash
        if not path.is_dir():
            raise FileNotFoundError(path)
        return path

    def load_manifest(self, checkpoint_hash: str) -> dict[str, Any]:
        path = self.checkpoint_dir(checkpoint_hash)
        manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        self._verify_checkpoint_dir(path, manifest)
        return manifest

    def load_native_state(self, checkpoint_hash: str) -> dict[str, Any]:
        path = self.checkpoint_dir(checkpoint_hash)
        manifest = self.load_manifest(checkpoint_hash)
        state = json.loads((path / "native_state.json").read_text(encoding="utf-8"))
        if digest(state) != manifest["native_state_sha256"]:
            raise RuntimeError("native state changed after checkpoint freeze")
        return state

    def load_model_context(self, checkpoint_hash: str) -> Any:
        path = self.checkpoint_dir(checkpoint_hash)
        manifest = self.load_manifest(checkpoint_hash)
        value = json.loads((path / "model_context.json").read_text(encoding="utf-8"))
        if digest(value) != manifest["model_visible_context_sha256"]:
            raise RuntimeError("model context changed after checkpoint freeze")
        return value

    def restore_application(self, checkpoint_hash: str, destination: str | Path) -> dict[str, str]:
        path = self.checkpoint_dir(checkpoint_hash)
        manifest = self.load_manifest(checkpoint_hash)
        restored = restore_tree_verified(path / "application", destination)
        if digest(restored) != manifest["application_state_sha256"]:
            raise RuntimeError("restored application state differs from checkpoint")
        return restored


def verify_foreign_carrier_refs(
    frozen_refs: list[dict[str, Any]],
    current_refs: list[dict[str, Any]],
) -> bool:
    """Compare carrier references only.

    A mismatch is a checkpoint-environment mismatch. This helper intentionally
    exposes no mutation path for the carrier itself.
    """
    return stable_json_bytes(frozen_refs) == stable_json_bytes(current_refs)
