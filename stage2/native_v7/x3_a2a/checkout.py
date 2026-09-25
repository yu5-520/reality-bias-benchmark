"""Bounded checkout operations owned by each X3 A2A role service."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


class A2ACheckout:
    """Same frozen checkout affordances without importing the baseline mailbox host."""

    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)

    def _path(self, relative):
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise ValueError("expected relative file path")
        target = (self.root / relative).resolve()
        if not target.is_relative_to(self.root) or target == self.root:
            raise ValueError("file must remain within checkout")
        if any(
            (self.root / parent).is_symlink()
            for parent in Path(relative).parents
            if str(parent) != "."
        ):
            raise ValueError("symlink traversal is not allowed")
        return target

    def list_files(self):
        return sorted(
            str(path.relative_to(self.root))
            for path in self.root.rglob("*")
            if path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts
        )

    def read_file(self, path):
        target = self._path(path)
        if target.is_symlink() or not target.is_file():
            raise ValueError("file does not exist or is a symlink")
        raw = target.read_bytes()
        if len(raw) > 262144:
            raise ValueError("file exceeds read limit")
        return raw.decode("utf-8")

    def write_file(self, path, content):
        if not isinstance(content, str) or len(content.encode()) > 262144:
            raise ValueError("write needs UTF-8 content under 256 KiB")
        target = self._path(path)
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError("non-regular target")
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = content.encode("utf-8")
        fd, name = tempfile.mkstemp(prefix=".stage2-a2a-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, target)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        return {"path": path}

    def run_tests(self):
        command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
        try:
            proc = subprocess.run(
                command,
                cwd=self.root,
                capture_output=True,
                timeout=20,
                text=True,
                check=False,
            )
            return {
                "command": command[1:],
                "returncode": proc.returncode,
                "stdout": proc.stdout[-30000:],
                "stderr": proc.stderr[-30000:],
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "command": command[1:],
                "returncode": None,
                "stdout": "",
                "stderr": f"timeout after {exc.timeout}s",
            }
