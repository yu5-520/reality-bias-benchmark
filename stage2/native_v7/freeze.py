"""Freeze the Stage-II v7 registration/observation architecture."""
import difflib
import hashlib
import json
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
        ROOT / "arena/config/model_deepseek_v0.2.json",
        ROOT / "arena/providers.py",
        ROOT / "adapters/deepseek_chat.py",
        STAGE2 / "retrieval.py",
        BASE / "registry.json",
        BASE / "policy.py",
        BASE / "observer.py",
        BASE / "collect.py",
        BASE / "execution_binding.py",
        BASE / "subject_readiness.py",
        BASE / "software_host_v1.py",
        BASE / "software_host_smoke.py",
        BASE / "x1_autogen/__init__.py",
        BASE / "x1_autogen/runner.py",
        BASE / "x1_autogen/smoke.py",
        BASE / "x2_metagpt/__init__.py",
        BASE / "x2_metagpt/checkout.py",
        BASE / "x2_metagpt/runner.py",
        BASE / "x2_metagpt/metagpt_root/config/config2.yaml",
        BASE / "x2_metagpt/smoke.py",
        BASE / "x3_a2a/__init__.py",
        BASE / "x3_a2a/checkout.py",
        BASE / "x3_a2a/service.py",
        BASE / "x3_a2a/proxy.py",
        BASE / "x3_a2a/runner.py",
        BASE / "x3_a2a/smoke.py",
        BASE / "x4_mcp/__init__.py",
        BASE / "x4_mcp/server.py",
        BASE / "x4_mcp/wire_proxy.py",
        BASE / "x4_mcp/client_call.py",
        BASE / "x4_mcp/runner.py",
        BASE / "x4_mcp/smoke.py",
        BASE / "x5_rag/__init__.py",
        BASE / "x5_rag/context.py",
        BASE / "x5_rag/runner.py",
        BASE / "x5_rag/smoke.py",
        BASE / "x6_memorybank/__init__.py",
        BASE / "x6_memorybank/context.py",
        BASE / "x6_memorybank/runner.py",
        BASE / "x6_memorybank/smoke.py",
        BASE / "x7_longllmlingua/__init__.py",
        BASE / "x7_longllmlingua/context.py",
        BASE / "x7_longllmlingua/runner.py",
        BASE / "x7_longllmlingua/smoke.py",
        ROOT / "docs/R_Plan_v7.10.md",
        ROOT / "schemas/stage2_subject_readiness_receipt_v1.schema.json",
    ]
    return {
        "schema": "stage2-native-v7-matrix-v11",
        "predecessor": "docs/R_Plan_v7.10.md",
        "architecture": "heterogeneous-native-execution_external-observation",
        "natural_trajectories_collected": 0,
        "execution_gate": "CLOSED_UNTIL_CELL_X_SUBJECT_READY",
        "forbidden_global_normalization": registry["forbidden_global_normalization"],
        "background_substrates": registry["background_substrates"],
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
    print("PASS: Stage-II v7 has 21 unopened cells; natural collection gate remains closed")


if __name__ == "__main__":
    main()
