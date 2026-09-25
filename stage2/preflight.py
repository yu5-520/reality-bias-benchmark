"""Fail closed before any Stage-II subject/provider call."""
import hashlib
import json
from pathlib import Path
from .freeze import BASE, artifact
from .evidence import check_capture

NATIVE_REQUIRED = {
    "X1": {"delegate", "receive_message"},
    "X2": {"shared_state", "receive_message"},
    "X3": {"remote_task", "artifact_return"},
    "X4": {"resource_read", "tool_call"},
    "X5": {"retrieve"},
    "X6": {"memory_write", "memory_retrieve"},
    "X7": {"compress"},
}
COMMON_HOOKS = {"stage2.coding_arena.v1", "stage2.workspace.v1", "stage2.role_mailbox.v1"}


def blockers(runtime_manifest, captures_root, probe_id=None):
    planned = artifact()
    runtime = json.loads(Path(runtime_manifest).read_text())
    packages = json.loads((BASE / "runtime_packages.json").read_text())["packages"]
    captures_root = Path(captures_root)
    errors = []
    if runtime.get("matrix_sha256") != hashlib.sha256((BASE / "matrix.json").read_bytes()).hexdigest():
        errors.append("matrix hash mismatch")
    if (not runtime.get("subject_provider") or runtime.get("subject_provider") in {"scripted", "offline"}
            or not runtime.get("subject_model") or runtime.get("subject_model") == "SCRIPTED_PREFLIGHT_ONLY"
            or not runtime.get("subject_limits")):
        errors.append("provider/model/limits unbound")
    if not runtime.get("code_commit") or not runtime.get("roles_sha256") == planned["files_sha256"]["stage2/roles.json"]:
        errors.append("code or roles binding missing")
    bindings = runtime.get("probes", {})
    probes = json.loads((BASE / "versions.json").read_text())["probes"]
    if probe_id is not None and probe_id not in {item["id"] for item in probes}:
        raise ValueError("probe is not in the frozen seven-layer matrix")
    for probe in probes:
        pid = probe["id"]
        if probe_id is not None and pid != probe_id:
            continue
        bind = bindings.get(pid, {})
        if not bind.get("installed_version") or not bind.get("source_commit") or not bind.get("native_hooks"):
            errors.append(f"{pid}: installed implementation/native hooks unbound")
            continue
        pinned = packages[pid]
        if pinned.get("sdk_source_commit") and bind["source_commit"] != pinned["sdk_source_commit"]:
            errors.append(f"{pid}: native SDK source tag mismatch")
        if pid == "X5" and bind["source_commit"] != pinned["implementation_sha256"]:
            errors.append("X5: native retrieval implementation mismatch")
        if pid == "X6" and bind["source_commit"] != pinned["reference_commit"]:
            errors.append("X6: native MemoryBank source mismatch")
        if bind["installed_version"] != pinned["distribution"]:
            errors.append(f"{pid}: installed implementation version mismatch")
        if probe.get("source_commit") and bind.get("reference_commit") != probe["source_commit"]:
            errors.append(f"{pid}: frozen reference commit mismatch")
        if probe.get("implementation_sha256") and bind.get("implementation_sha256") != probe["implementation_sha256"]:
            errors.append(f"{pid}: in-repo implementation mismatch")
        if probe.get("protocol_version") and bind.get("protocol_version") != probe["protocol_version"]:
            errors.append(f"{pid}: protocol version mismatch")
        evidence_dir = captures_root / pid
        try:
            rows = [json.loads(line) for line in (evidence_dir / "events.jsonl").read_text().splitlines()]
            if not rows or not any(row["operation"] == "termination" and row["status"] == "success"
                               and json.loads((evidence_dir / row["raw_path"]).read_text()).get("reason") == "finalized"
                               for row in rows):
                raise ValueError("no successfully finalized smoke sequence")
            if any(row["hook_id"] == "offline-contract-smoke" or row["binding"].get("source_commit") == "synthetic-smoke" for row in rows):
                raise ValueError("synthetic contract smoke is not a native adapter smoke")
            if any(row["probe"] != pid or row["binding"].get("source_commit") != bind["source_commit"]
                   or row["hook_id"] not in set(bind["native_hooks"]) | COMMON_HOOKS for row in rows):
                raise ValueError("native smoke provenance differs from runtime binding")
            native_rows = [row for row in rows if row["hook_id"] in bind["native_hooks"]]
            if not NATIVE_REQUIRED[pid] <= {row["operation"] for row in native_rows}:
                raise ValueError("required architecture operations missing from native hook")
            operations = {row["operation"] for row in rows}
            if not {"model_input", "model_output", "file_change", "test_run", "termination"} <= operations:
                raise ValueError("model, code change, test or termination evidence incomplete")
            if any(json.loads((evidence_dir / row["raw_path"]).read_text()).get("model") != runtime.get("subject_model")
                   for row in rows if row["operation"] == "model_output"):
                raise ValueError("smoke provider output differs from bound subject model")
            if pid == "X3" and not bind.get("remote_model_evidence"):
                raise ValueError("remote artifact lacks remote model input/output evidence")
            check_capture(evidence_dir)
        except (OSError, ValueError, KeyError, AssertionError) as exc:
            errors.append(f"{pid}: native evidence gate failed ({exc})")
    return errors


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-manifest", required=True)
    parser.add_argument("--captures-root", required=True)
    parser.add_argument("--probe", choices=[f"X{index}" for index in range(1, 8)],
                        help="gate one frozen architecture without replacing blocked cells")
    args = parser.parse_args()
    errors = blockers(args.runtime_manifest, args.captures_root, args.probe)
    if errors:
        raise SystemExit("SUBJECT_GATE=CLOSED\n" + "\n".join(errors))
    print("SUBJECT_GATE=OPEN; native evidence verified, scientific audit still pending")


if __name__ == "__main__":
    main()
