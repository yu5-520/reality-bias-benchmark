"""Reproducible fixture + 21-cell manifest generation and offline verification."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "stage2"


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact():
    fixture_files = sorted((BASE / "fixtures/project").rglob("*"))
    hashes = {str(p.relative_to(ROOT)): hash_file(p) for p in fixture_files
              if p.is_file() and "__pycache__" not in p.parts and not p.name.startswith(".")}
    versions = json.loads((BASE / "versions.json").read_text())
    tasks = json.loads((BASE / "tasks.json").read_text())
    subject = json.loads((BASE / "subject.json").read_text())
    return {
        "schema": "stage2-first-group-v1", "predecessors": [f"docs/R_Plan_v6.{index}.md" for index in range(9)],
        "files_sha256": {**hashes, **{str(p.relative_to(ROOT)): hash_file(p) for p in
            (BASE / "roles.json", BASE / "tasks.json", BASE / "versions.json",
             BASE / "runtime_bindings.json", BASE / "subject.json", BASE / "eligibility.json",
             BASE / "event_schema.json",
             BASE / "evidence.py", BASE / "retrieval.py", BASE / "workspace.py", BASE / "coding_arena.py",
             BASE / "transports.py", BASE / "metagpt_transport.py", BASE / "rag_context.py",
             BASE / "longllmlingua_context.py", BASE / "a2a_transport.py",
             BASE / "a2a_remote_service.py", BASE / "mcp_checkout_server.py", BASE / "mcp_workspace.py",
             BASE / "preflight.py", BASE / "native_smoke.py", BASE / "build_runtime_manifest.py",
             BASE / "target_coding_smoke.py", BASE / "verify_target_coding.py", BASE / "collect_natural.py",
             ROOT / "docs/R_Plan_v6.2.md", ROOT / "docs/R_Plan_v6.3.md",
             ROOT / "docs/R_Plan_v6.4.md", ROOT / "docs/R_Plan_v6.5.md",
             ROOT / "docs/R_Plan_v6.6.md", ROOT / "docs/R_Plan_v6.7.md",
             ROOT / "docs/R_Plan_v6.8.md")}},
        "cells": [{"cell": f"{probe['id']}-{task['id']}", "probe": probe["id"], "task": task["id"],
                   "starting_fixture": "stage2/fixtures/project", "status": "PENDING_ENGINEERING_GATE",
                   "raw_destination": f"stage2_raw/{probe['id']}-{task['id']}/", "subject_trajectory_count": 0}
                  for probe in versions["probes"] for task in tasks["tasks"]],
        "subject_model": subject["model_alias"], "subject_provider": subject["provider"],
        "subject_limits": subject["limits"],
        "adapter_binding": None, "runtime_code_sha": None,
        "execution_gate": "CLOSED_UNTIL_TARGET_MATCHING_FULL_CODING_SMOKE",
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
        raise SystemExit("FAIL: Stage-II manifest differs from frozen fixture/task/version sources")
    print("PASS: 21 prospective cells pending engineering gate; file hashes match")


if __name__ == "__main__":
    main()
