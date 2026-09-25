"""Freeze the Stage-II v7 registration/observation architecture."""
import hashlib
import json
import difflib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "stage2/native_v7"
STAGE2 = ROOT / "stage2"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixture_tree_digest():
    rows = []
    for path in sorted((STAGE2 / "fixtures/project").rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and not path.name.startswith("."):
            rows.append(f"{path.relative_to(ROOT)}\0{sha256(path)}")
    return hashlib.sha256("\n".join(rows).encode()).hexdigest(), len(rows)


def artifact():
    registry = json.loads((BASE / "registry.json").read_text())
    tasks = json.loads((STAGE2 / "tasks.json").read_text())["tasks"]
    fixture_digest, fixture_count = fixture_tree_digest()
    frozen_files = [
        STAGE2 / "tasks.json",
        STAGE2 / "roles.json",
        STAGE2 / "subject.json",
        BASE / "registry.json",
        BASE / "policy.py",
        BASE / "observer.py",
        BASE / "collect.py",
        ROOT / "docs/R_Plan_v7.0.md",
    ]
    return {
        "schema": "stage2-native-v7-matrix-v1",
        "predecessor": "docs/R_Plan_v7.0.md",
        "architecture": "heterogeneous-native-execution_external-observation",
        "natural_trajectories_collected": 0,
        "execution_gate": "CLOSED_UNTIL_EACH_X_NATIVE_RUNNER_VERIFIED",
        "forbidden_shared_runtime": registry["forbidden_execution_dependencies"],
        "fixture_tree": {
            "path": "stage2/fixtures/project",
            "files": fixture_count,
            "sha256": fixture_digest,
        },
        "files_sha256": {
            str(path.relative_to(ROOT)): sha256(path) for path in frozen_files
        },
        "cells": [
            {
                "cell": f"{pid}-{task['id']}",
                "probe": pid,
                "task": task["id"],
                "status": registry["probes"][pid]["collection_state"],
                "subject_trajectory_count": 0,
            }
            for pid in sorted(registry["probes"])
            for task in tasks
        ],
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    expected = json.dumps(artifact(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    target = BASE / "matrix.json"
    if args.write:
        target.write_text(expected)
    elif target.read_text() != expected:
        actual = target.read_text()
        print("".join(difflib.unified_diff(
            actual.splitlines(True), expected.splitlines(True),
            fromfile="checked-in matrix.json", tofile="derived artifact",
        )))
        raise SystemExit("FAIL: Stage-II v7 matrix differs from frozen native registry/inputs")
    print("PASS: Stage-II v7 has 21 unopened cells; native execution gate remains closed")


if __name__ == "__main__":
    main()
