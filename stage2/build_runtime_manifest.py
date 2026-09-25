"""Build the exact Stage-II engineering runtime manifest from seven smoke receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(summary_path: Path, code_commit: str) -> dict:
    summary = json.loads(summary_path.read_text())
    if not summary.get("all_probes_accounted_for"):
        raise ValueError("native gate summary is incomplete")
    subject = json.loads((BASE / "subject_lock.json").read_text())
    planned = json.loads((BASE / "matrix.json").read_text())
    roles_hash = planned["files_sha256"]["stage2/roles.json"]
    probes = {}
    for row in summary["statuses"]:
        probe = row["probe"]
        binding = dict(row.get("binding") or {})
        binding["execution_status"] = row["status"]
        if row["status"] == "ENGINEERING_BLOCKED":
            binding["blocker_reason"] = row.get("reason")
        probes[probe] = binding
    return {
        "schema": "stage2-runtime-manifest-v1",
        "code_commit": code_commit,
        "matrix_sha256": sha256(BASE / "matrix.json"),
        "runtime_lock_sha256": sha256(BASE / "runtime_lock.json"),
        "subject_lock_sha256": sha256(BASE / "subject_lock.json"),
        "roles_sha256": roles_hash,
        "subject_provider": subject["provider"],
        "subject_model": subject["model_alias"],
        "subject_limits": subject["limits"],
        "provider_execution_authorized": False,
        "probes": probes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    manifest = build(Path(args.summary), args.code_commit)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
