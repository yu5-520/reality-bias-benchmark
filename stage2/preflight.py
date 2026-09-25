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
    runtime_lock_path = BASE / "runtime_lock.json"
    subject_lock_path = BASE / "subject_lock.json"
    runtime_lock = json.loads(runtime_lock_path.read_text())
    subject_lock = json.loads(subject_lock_path.read_text())
    lock_by_probe = {row["id"]: row for row in runtime_lock["probes"]}
    expected_runtime_lock_hash = hashlib.sha256(runtime_lock_path.read_bytes()).hexdigest()
    expected_subject_lock_hash = hashlib.sha256(subject_lock_path.read_bytes()).hexdigest()
    if runtime.get("runtime_lock_sha256") != expected_runtime_lock_hash:
        errors.append("runtime lock hash mismatch")
    if runtime.get("subject_lock_sha256") != expected_subject_lock_hash:
        errors.append("subject lock hash mismatch")
    if runtime.get("matrix_sha256") != hashlib.sha256((BASE / "matrix.json").read_bytes()).hexdigest():
        errors.append("matrix hash mismatch")
    if not runtime.get("subject_provider") or not runtime.get("subject_model") or not runtime.get("subject_limits"):
        errors.append("provider/model/limits unbound")
    if runtime.get("subject_provider") != subject_lock.get("provider"):
        errors.append("subject provider differs from frozen subject lock")
    if runtime.get("subject_model") != subject_lock.get("model_alias"):
        errors.append("subject model differs from frozen subject lock")
    if runtime.get("subject_limits") != subject_lock.get("limits"):
        errors.append("subject limits differ from frozen subject lock")
    if not runtime.get("code_commit") or not runtime.get("roles_sha256") == planned["files_sha256"]["stage2/roles.json"]:
        errors.append("code or roles binding missing")
    bindings = runtime.get("probes", {})
    for probe in json.loads((BASE / "versions.json").read_text())["probes"]:
        pid = probe["id"]
        bind = bindings.get(pid, {})
        execution_status = bind.get("execution_status")
        if execution_status == "ENGINEERING_BLOCKED":
            if not bind.get("blocker_reason"):
                errors.append(f"{pid}: engineering blocker reason missing")
            continue
        if execution_status is None:
            if not bind.get("installed_version") or not bind.get("native_hook"):
                errors.append(f"{pid}: installed implementation/native hook unbound")
            errors.append(f"{pid}: native engineering status unbound")
            continue
        if execution_status != "NATIVE_SMOKE_PASS":
            errors.append(f"{pid}: invalid native engineering status {execution_status}")
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
        locked = lock_by_probe.get(pid, {})
        if locked.get("sdk_source_commit") and bind.get("sdk_source_commit") != locked["sdk_source_commit"]:
            errors.append(f"{pid}: SDK source commit mismatch")
        if locked.get("checkpoint") and bind.get("checkpoint") != locked["checkpoint"]:
            errors.append(f"{pid}: checkpoint mismatch")
        if pid == "X7" and not bind.get("checkpoint_revision"):
            errors.append("X7: compressor checkpoint revision unbound")
        evidence_dir = captures_root / pid
        try:
            rows = [json.loads(line) for line in (evidence_dir / "events.jsonl").read_text().splitlines()]
            if not rows or not any(row["operation"] == "termination" for row in rows):
                raise ValueError("no completed smoke sequence")
            if any(row["hook_id"] == "offline-contract-smoke" or row["binding"].get("source_commit") == "synthetic-smoke" for row in rows):
                raise ValueError("synthetic contract smoke is not a native adapter smoke")
            if any(
                row["probe"] != pid
                or row["hook_id"] != bind["native_hook"]
                or (probe.get("source_commit") and row["binding"].get("source_commit") != bind.get("source_commit"))
                or (
                    probe.get("implementation_sha256")
                    and row["binding"].get("implementation_sha256") != bind.get("implementation_sha256")
                )
                or (
                    locked.get("sdk_source_commit")
                    and row["binding"].get("sdk_source_commit") != bind.get("sdk_source_commit")
                )
                for row in rows
            ):
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
    print("ENGINEERING_GATE=OPEN; passed probes have native evidence, blocked probes are frozen; provider authorization remains separate")


if __name__ == "__main__":
    main()
