"""Isolated, evidence-producing code workspace shared by all Stage-II probes."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .freeze import BASE, artifact, hash_file

PROJECT = BASE / "fixtures/project"


def new_workspace(destination):
    """Copy the exact frozen starting tree; refuse a preexisting checkout."""
    destination = Path(destination)
    frozen = artifact()["files_sha256"]
    paths = {path.removeprefix("stage2/fixtures/project/"): digest
             for path, digest in frozen.items() if path.startswith("stage2/fixtures/project/")}
    if destination.exists():
        raise FileExistsError(destination)
    shutil.copytree(PROJECT, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    observed = {str(path.relative_to(destination)): hash_file(path)
                for path in destination.rglob("*") if path.is_file()}
    if observed != paths:
        shutil.rmtree(destination)
        raise ValueError("starting checkout differs from the frozen 21-cell fixture")
    return destination


class CodeWorkspace:
    def __init__(self, root, capture):
        self.root = Path(root).resolve(strict=True)
        self.capture = capture
        self.sequence = 0

    def _path(self, relative):
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise ValueError("expected relative file path")
        target = (self.root / relative).resolve()
        if not target.is_relative_to(self.root) or target == self.root:
            raise ValueError("file must remain within the task checkout")
        if any((self.root / parent).is_symlink() for parent in Path(relative).parents if str(parent) != "."):
            raise ValueError("symlink traversal is not allowed")
        return target

    def _record(self, operation, data, path, actor, source, parents, phase="returned", status="success"):
        self.sequence += 1
        return self.capture.capture(
            event_id=f"fs-{self.sequence}", operation=operation, phase=phase,
            native_locator=f"workspace:{path}", hook_id="stage2.workspace.v1",
            raw=data, actor=actor, carrier_id=f"workspace:{path}:{hashlib.sha256(data).hexdigest()}",
            carrier_type="checkout-file" if operation != "test_run" else "test-process",
            source_id=source, parent_ids=parents, status=status,
        )

    def list_files(self, actor, source, parents=()):
        paths = sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*")
                       if p.is_file() and not p.is_symlink() and "__pycache__" not in p.parts)
        raw = json.dumps(paths, ensure_ascii=False).encode()
        row = self._record("file_list", raw, ".", actor, source, parents)
        return paths, row["event_id"]

    def read_file(self, path, actor, source, parents=()):
        target = self._path(path)
        if target.is_symlink() or not target.is_file():
            raise ValueError("file does not exist or is a symlink")
        raw = target.read_bytes()
        if len(raw) > 262144:
            raise ValueError("file exceeds read limit")
        row = self._record("file_read", raw, path, actor, source, parents)
        return raw.decode("utf-8"), row["event_id"]

    def write_file(self, path, content, actor, source, parents=()):
        if not isinstance(content, str) or len(content.encode()) > 262144:
            raise ValueError("write needs UTF-8 content under 256 KiB")
        target = self._path(path)
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError("non-regular target")
        target.parent.mkdir(parents=True, exist_ok=True)
        before = target.read_bytes() if target.exists() else b""
        payload = content.encode("utf-8")
        fd, name = tempfile.mkstemp(prefix=".stage2-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, target)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        row = self._record("file_change", payload, path, actor,
                           f"{source};previous_sha256={hashlib.sha256(before).hexdigest()}", parents,
                           phase="executed")
        return {"path": path, "before_sha256": hashlib.sha256(before).hexdigest(),
                "after_sha256": hashlib.sha256(payload).hexdigest()}, row["event_id"]

    def run_tests(self, actor, source, parents=()):
        # The agent can choose when to check the task. The fixed command avoids
        # giving a model arbitrary shell access to the host research repository.
        command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
        try:
            proc = subprocess.run(command, cwd=self.root, capture_output=True,
                                  timeout=20, text=True, check=False)
            output = {"command": command[1:], "returncode": proc.returncode,
                      "stdout": proc.stdout[-30000:], "stderr": proc.stderr[-30000:]}
        except subprocess.TimeoutExpired as exc:
            output = {"command": command[1:], "returncode": None, "stdout": "",
                      "stderr": f"timeout after {exc.timeout}s"}
        raw = json.dumps(output, ensure_ascii=False, sort_keys=True).encode()
        row = self._record("test_run", raw, "tests/", actor, source, parents,
                           status="success" if output["returncode"] == 0 else "error")
        return output, row["event_id"]
