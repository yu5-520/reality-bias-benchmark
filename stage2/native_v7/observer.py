"""Passive process-boundary evidence for Stage-II v7.

Framework-specific observers may add native files under ``native/``. This helper
only preserves invocation/stdout/stderr/exit status and hashes what already
exists. It never rewrites a framework message or decides an agent action.
"""
import hashlib
import json
import os
from pathlib import Path


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


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
