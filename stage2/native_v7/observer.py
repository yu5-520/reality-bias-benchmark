"""Passive observation helpers for Stage-II v7.

The process observer records only subprocess-boundary bytes. The event observer
is a one-way tee for framework-native public event streams: it writes immutable
copies and returns the exact input bytes unchanged. Neither helper decides agent
actions, rewrites messages, or participates in scheduling.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
from pathlib import Path


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def native_bytes(value):
    """Serialize one already-emitted native object without changing it."""
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    if hasattr(value, "model_dump_json"):
        return value.model_dump_json().encode("utf-8")
    if dataclasses.is_dataclass(value):
        value = dataclasses.asdict(value)
    elif hasattr(value, "model_dump"):
        value = value.model_dump()
    elif hasattr(value, "__dict__"):
        value = {
            "type": type(value).__name__,
            **{
                key: item
                for key, item in vars(value).items()
                if not key.startswith("_")
            },
        }
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":")
    ).encode("utf-8")


class PassiveEventObserver:
    """Content-addressed one-way tee for a framework's already-emitted events."""

    def __init__(self, root, *, probe):
        self.root = Path(root)
        self.probe = probe
        self.raw_root = self.root / "raw"
        self.root.mkdir(parents=True, exist_ok=False)
        self.raw_root.mkdir()
        self.rows = []

    def observe(self, raw, *, surface):
        if not isinstance(raw, bytes) or not raw:
            raise ValueError("passive observer requires non-empty bytes")
        digest = sha256_bytes(raw)
        target = self.raw_root / digest
        if target.exists():
            if target.read_bytes() != raw:
                raise ValueError("observer content-address collision")
        else:
            with target.open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        self.rows.append(
            {
                "sequence": len(self.rows),
                "probe": self.probe,
                "surface": surface,
                "sha256": digest,
                "bytes": len(raw),
                "raw_path": str(target.relative_to(self.root)),
            }
        )
        return raw

    def seal(self):
        rows = self.root / "events.jsonl"
        with rows.open("xb") as stream:
            for row in self.rows:
                stream.write(
                    json.dumps(
                        row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                    ).encode("utf-8")
                    + b"\n"
                )
            stream.flush()
            os.fsync(stream.fileno())
        inventory = {
            str(path.relative_to(self.root)): sha256_file(path)
            for path in sorted(self.root.rglob("*"))
            if path.is_file() and path.name != "inventory.json"
        }
        target = self.root / "inventory.json"
        with target.open("x") as stream:
            json.dump(inventory, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        return inventory


class ExternalObserver:
    def __init__(self, root, *, probe, cell):
        self.root = Path(root)
        self.probe = probe
        self.cell = cell
        self.root.mkdir(parents=True, exist_ok=False)

    def record_invocation(self, argv, cwd, environment_id):
        payload = {
            "schema": "stage2-v7-process-boundary-v1",
            "probe": self.probe,
            "cell": self.cell,
            "argv": list(argv),
            "cwd": str(cwd),
            "environment_id": environment_id,
        }
        (self.root / "invocation.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )

    def record_process_result(self, *, stdout, stderr, returncode):
        (self.root / "stdout.bin").write_bytes(stdout)
        (self.root / "stderr.bin").write_bytes(stderr)
        (self.root / "exit.json").write_text(
            json.dumps({"returncode": returncode}, sort_keys=True) + "\n"
        )

    def inventory(self):
        return {
            str(path.relative_to(self.root)): sha256_file(path)
            for path in sorted(self.root.rglob("*"))
            if path.is_file() and path.name != "inventory.json"
        }

    def seal(self):
        inventory = self.inventory()
        target = self.root / "inventory.json"
        with target.open("x") as stream:
            json.dump(inventory, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        return inventory


def verify_observer(root):
    root = Path(root)
    expected = json.loads((root / "inventory.json").read_text())
    observed = {
        str(path.relative_to(root)): sha256_file(path)
        for path in root.rglob("*")
        if path.is_file() and path.name != "inventory.json"
    }
    if observed != expected:
        raise ValueError("external observer evidence changed after sealing")
    return len(observed)
