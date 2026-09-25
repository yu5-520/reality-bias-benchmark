"""Fail closed before any Stage-II subject/provider call."""
import hashlib
import json
from pathlib import Path
from .freeze import BASE, artifact
from .evidence import check_capture


def blockers(runtime_manifest, captures_root):
    planned = artifact()
    runtime = json.loads(Path(runtime_manifest).read_text())
    captures_root = Path(captures_root)
    errors = []
    if runtime.get("matrix_sha256") != hashlib.sha256((BASE / "matrix.json").read_bytes()).hexdigest():
        errors.append("matrix hash mismatch")
    if not runtime.get("subject_provider") or not runtime.get("subject_model") or not runtime.get("subject_limits"):
        errors.append("provider/model/limits unbound")
    if not runtime.get("code_commit") or not runtime.get("roles_sha256") == planned["files_sha256"]["stage2/roles.json"]:
        errors.append("code or roles binding missing")
    bindings = runtime.get("probes", {})
    targets = json.loads((BASE / "runtime_bindings.json").read_text())["probes"]
    for probe in json.loads((BASE / "versions.json").read_text())["probes"]:
        pid = probe["id"]
        bind = bindings.get(pid, {})
        frozen_target = targets.get(pid, {})
        target_blocked = frozen_target.get("state") == "ENGINEERING_BLOCKED"
        runtime_blocked = bind.get("engineering_status") == "ENGINEERING_BLOCKED"
        if target_blocked or runtime_blocked:
            if not (target_blocked and runtime_blocked):
                errors.append(f"{pid}: engineering-block state differs from frozen target")
            if not bind.get("block_reason") or bind.get("block_reason") != frozen_target.get("block_reason"):
                errors.append(f"{pid}: engineering-block reason missing or differs from frozen target")
            continue
        if not bind.get("installed_version") or not bind.get("native_hook"):
            errors.append(f"{pid}: installed implementation/native hook unbound")
            continue
        if probe.get("source_commit") and bind.get("source_commit") != probe["source_commit"]:
            errors.append(f"{pid}: upstream source commit mismatch")
        if probe.get("implementation_sha256") and bind.get("implementation_sha256") != probe["implementation_sha256"]:
            errors.append(f"{pid}: in-repo implementation mismatch")
        if probe.get("protocol_version") and bind.get("protocol_version") != probe["protocol_version"]:
            errors.append(f"{pid}: protocol version mismatch")
        evidence_dir = captures_root / pid
        try:
            rows = [json.loads(line) for line in (evidence_dir / "events.jsonl").read_text().splitlines()]
            if not rows or not any(row["operation"] == "termination" for row in rows):
                raise ValueError("no completed smoke sequence")
            if any(row["hook_id"] == "offline-contract-smoke" or row["binding"].get("source_commit") == "synthetic-smoke" for row in rows):
                raise ValueError("synthetic contract smoke is not a native adapter smoke")
            if any(row["probe"] != pid or row["binding"].get("source_commit") != bind.get("source_commit")
                   or row["hook_id"] != bind["native_hook"] for row in rows):
                raise ValueError("native smoke provenance differs from runtime binding")
            check_capture(evidence_dir)
        except (OSError, ValueError, KeyError, AssertionError) as exc:
            errors.append(f"{pid}: native evidence gate failed ({exc})")
    return errors


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-manifest", required=True)
    parser.add_argument("--captures-root", required=True)
    args = parser.parse_args()
    errors = blockers(args.runtime_manifest, args.captures_root)
    if errors:
        raise SystemExit("SUBJECT_GATE=CLOSED\n" + "\n".join(errors))
    runtime = json.loads(Path(args.runtime_manifest).read_text())
    blocked = sorted(pid for pid, bind in runtime.get("probes", {}).items()
                     if bind.get("engineering_status") == "ENGINEERING_BLOCKED")
    suffix = f"; engineering_blocked={','.join(blocked)}" if blocked else ""
    print("SUBJECT_GATE=OPEN_FOR_NONBLOCKED_PROBES; native evidence verified, scientific audit still pending" + suffix)


if __name__ == "__main__":
    main()
