"""Verify frozen first-attempt evidence without interpreting its contents."""

import hashlib
import io
import json
import tarfile
from pathlib import Path


BASE = Path(__file__).resolve().parent / "X1-T1"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verify():
    manifest = json.loads((BASE / "manifest.json").read_text())
    raw = (BASE / "first_attempt.tar.gz").read_bytes()
    assert digest(raw) == manifest["tar_sha256"]
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        members = {m.name.removeprefix("./"): m for m in archive.getmembers() if m.isfile()}

        def read(name):
            return archive.extractfile(members[name]).read()

        inventory = json.loads(read("archive_inventory.json"))
        assert set(inventory) == set(members) - {"archive_inventory.json"}
        for name, expected in inventory.items():
            assert digest(read(name)) == expected, name

        root = "X1-T1/observer/"
        outer = json.loads(read(root + "inventory.json"))
        assert len(outer) == manifest["observer_files"]
        for name, expected in outer.items():
            assert digest(read(root + name)) == expected, name

        native = json.loads(read(root + "native/inventory.json"))
        for name, expected in native.items():
            assert digest(read(root + "native/" + name)) == expected, name
        events = [json.loads(line) for line in read(root + "native/events.jsonl").splitlines()]
        assert len(events) == manifest["native_event_count"]
        for number, event in enumerate(events):
            assert event["sequence"] == number
            assert digest(read(root + "native/" + event["raw_path"])) == event["sha256"]

        seal = json.loads(read("X1-T1/seal.json"))
        assert seal["cell"] == "X1-T1"
        assert seal["status"] == "RECORDED_PENDING_POSTHOC_AUDIT"
        assert seal["returncode"] == 0
        assert seal["observer_files"] == len(outer)
        assert seal["common_receipt_sha256"] == manifest["common_receipt_sha256"]
        assert read("collect_exit_code.txt").strip() == b"0"
        assert read("execution_sha.txt").decode().strip() == manifest["execution_sha"]
        assert read("authorization_issue.txt").strip() == b"172"
    return manifest


if __name__ == "__main__":
    result = verify()
    print(f"PASS: {result['cell']} raw attempt frozen, {result['native_event_count']} native events")
