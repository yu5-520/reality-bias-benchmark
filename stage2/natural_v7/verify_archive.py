"""Verify frozen natural attempts without interpreting their outcomes."""

import hashlib
import io
import json
import tarfile
from pathlib import Path


BASE = Path(__file__).resolve().parent


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _result_json(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        lines = raw.decode("utf-8", "replace").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and "stop_reason" in payload:
                return payload
        raise ValueError("observer stdout contains no terminal result JSON")


def verify_one(root):
    manifest = json.loads((root / "manifest.json").read_text())
    cell = manifest["cell"]
    assert root.name == cell
    raw = (root / "first_attempt.tar.gz").read_bytes()
    assert digest(raw) == manifest["tar_sha256"]
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        members = {m.name.removeprefix("./"): m for m in archive.getmembers() if m.isfile()}

        def read(name):
            return archive.extractfile(members[name]).read()

        inventory = json.loads(read("archive_inventory.json"))
        assert set(inventory) == set(members) - {"archive_inventory.json"}
        for name, expected in inventory.items():
            assert digest(read(name)) == expected, name

        observer_root = f"{cell}/observer/"
        outer = json.loads(read(observer_root + "inventory.json"))
        assert len(outer) == manifest["observer_files"]
        for name, expected in outer.items():
            assert digest(read(observer_root + name)) == expected, name

        event_count = 0
        for name in members:
            if not name.startswith(observer_root) or not name.endswith("/events.jsonl"):
                continue
            native_root = name.removesuffix("events.jsonl")
            native = json.loads(read(native_root + "inventory.json"))
            for relative, expected in native.items():
                assert digest(read(native_root + relative)) == expected, relative
            events = [json.loads(line) for line in read(name).splitlines()]
            event_count += len(events)
            for number, event in enumerate(events):
                assert event["sequence"] == number
                assert digest(read(native_root + event["raw_path"])) == event["sha256"]
        if "native_event_count" in manifest:
            assert event_count == manifest["native_event_count"]

        seal = json.loads(read(f"{cell}/seal.json"))
        assert seal["cell"] == cell
        assert seal["status"] == manifest["status"]
        expected_runner_returncode = int(manifest.get("runner_returncode", 0))
        assert seal["returncode"] == expected_runner_returncode
        assert seal["observer_files"] == len(outer)
        assert seal["common_receipt_sha256"] == manifest["common_receipt_sha256"]
        assert read("collect_exit_code.txt").strip() == b"0"
        assert read("execution_sha.txt").decode().strip() == manifest["execution_sha"]
        assert int(read("authorization_issue.txt")) == manifest["authorization_issue"]
        outcome = manifest.get("task_outcome")
        if outcome == "TURN_BUDGET_NO_ANSWER":
            result = _result_json(read(observer_root + "stdout.bin"))
            assert result["stop_reason"] == "turn_budget"
            assert result["answer"] is None
            assert expected_runner_returncode == 0
        elif outcome == "FAILED_ATTEMPT_PRESERVED":
            assert expected_runner_returncode != 0
            assert seal["status"] == "FAILED_ATTEMPT_PRESERVED"
        elif outcome == "RECORDED_WITH_ANSWER":
            result = _result_json(read(observer_root + "stdout.bin"))
            assert result.get("answer") is not None
            assert expected_runner_returncode == 0
        elif outcome is not None:
            assert outcome == "RECORDED_OTHER"
    return manifest


def verify():
    roots = sorted(p.parent for p in BASE.glob("*/manifest.json"))
    assert roots
    return [verify_one(root) for root in roots]


if __name__ == "__main__":
    results = verify()
    print(f"PASS: {len(results)} natural attempts hash-verified and sealed")
