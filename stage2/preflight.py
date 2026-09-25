"""Two fail-closed Stage-II gates: native boundary smoke and subject readiness."""
import hashlib
import json
from pathlib import Path

from .evidence import check_capture
from .freeze import BASE, artifact

NATIVE_REQUIRED = {
    "X1": {"delegate", "receive_message"},
    "X3": {"remote_task", "artifact_return"},
    "X4": {"resource_read", "tool_call"},
    "X5": {"retrieve"},
    "X7": {"compress"},
}
COMMON_HOOKS = {"stage2.coding_arena.v1", "stage2.workspace.v1", "stage2.role_mailbox.v1"}


def _configuration(runtime_manifest, probe_id):
    runtime = json.loads(Path(runtime_manifest).read_text())
    targets = json.loads((BASE / "runtime_bindings.json").read_text())["probes"]
    forward_blocks = json.loads((BASE / "eligibility.json").read_text())["engineering_blocks"]
    for pid, reason in forward_blocks.items():
        if pid not in targets or targets[pid]["state"] == "ENGINEERING_BLOCKED":
            raise ValueError("forward eligibility must identify an existing nonblocked frozen target")
        targets[pid] = {**targets[pid], "state": "ENGINEERING_BLOCKED", "block_reason": reason}
    if probe_id is not None and probe_id not in targets:
        raise ValueError("probe is not in the frozen seven-layer matrix")
    return runtime, targets


def _common_errors(runtime, targets):
    planned = artifact()
    subject = json.loads((BASE / "subject.json").read_text())
    errors = []
    if runtime.get("matrix_sha256") != hashlib.sha256((BASE / "matrix.json").read_bytes()).hexdigest():
        errors.append("matrix hash mismatch")
    if (runtime.get("subject_provider") != subject["provider"]
            or runtime.get("subject_model") != subject["model_alias"]
            or runtime.get("expected_model_version") != subject["expected_model_version"]
            or runtime.get("subject_limits") != subject["limits"]):
        errors.append("frozen subject provider/model/limits mismatch")
    if not runtime.get("code_commit") or runtime.get("roles_sha256") != planned["files_sha256"]["stage2/roles.json"]:
        errors.append("code or roles binding missing")
    if set(runtime.get("probes", {})) != set(targets):
        errors.append("manifest must account for all seven frozen probes")
    return errors


def _blocked_errors(pid, bind, target):
    expected = target.get("state") == "ENGINEERING_BLOCKED"
    actual = bind.get("engineering_status") == "ENGINEERING_BLOCKED"
    errors = []
    if expected != actual:
        errors.append(f"{pid}: engineering-block state differs from frozen target")
    if expected and bind.get("block_reason") != target.get("block_reason"):
        errors.append(f"{pid}: engineering-block reason differs from frozen target")
    return errors


def _identity_errors(pid, bind, target):
    errors = []
    if not bind.get("installed_version") or not bind.get("source_commit") or not bind.get("native_hook"):
        return [f"{pid}: installed implementation/native hook unbound"]
    expected_source = (target.get("source_commit") or target.get("protocol_commit")
                       or bind.get("source_commit"))
    if bind["source_commit"] != expected_source:
        errors.append(f"{pid}: frozen upstream/protocol source mismatch")
    if target.get("sdk_commit") != bind.get("sdk_commit"):
        errors.append(f"{pid}: frozen native SDK commit mismatch")
    if bind["native_hook"] != target["hook_id"]:
        errors.append(f"{pid}: frozen native hook mismatch")
    if target.get("protocol_version") != bind.get("protocol_version"):
        errors.append(f"{pid}: frozen protocol version mismatch")
    if target.get("implementation_sha256") != bind.get("implementation_sha256"):
        errors.append(f"{pid}: frozen retrieval implementation mismatch")
    return errors


def native_smoke_blockers(runtime_manifest, captures_root, probe_id=None):
    """Validate main v6.4 native boundary smoke without claiming subject readiness."""
    runtime, targets = _configuration(runtime_manifest, probe_id)
    errors = _common_errors(runtime, targets)
    for pid, target in targets.items():
        if probe_id is not None and pid != probe_id:
            continue
        bind = runtime.get("probes", {}).get(pid, {})
        errors.extend(_blocked_errors(pid, bind, target))
        if target["state"] == "ENGINEERING_BLOCKED":
            continue
        errors.extend(_identity_errors(pid, bind, target))
        evidence_dir = Path(captures_root) / pid
        try:
            rows = [json.loads(line) for line in (evidence_dir / "events.jsonl").read_text().splitlines()]
            if not rows or not any(row["operation"] == "termination" and row["status"] == "success"
                                   for row in rows):
                raise ValueError("no successful native boundary smoke termination")
            if any(row["hook_id"] != target["hook_id"] or row["probe"] != pid
                   or row["binding"].get("source_commit") != bind.get("source_commit")
                   or row["binding"].get("code_commit") != runtime.get("code_commit")
                   for row in rows):
                raise ValueError("native boundary smoke provenance differs from locked target")
            check_capture(evidence_dir)
        except (OSError, ValueError, KeyError, AssertionError) as exc:
            errors.append(f"{pid}: native evidence gate failed ({exc})")
    return errors


def blockers(runtime_manifest, captures_root, probe_id=None):
    """The paid natural-run gate requires a full coding trace for each target."""
    runtime, targets = _configuration(runtime_manifest, probe_id)
    errors = _common_errors(runtime, targets)
    expected_version = json.loads((BASE / "subject.json").read_text())["expected_model_version"]
    for pid, target in targets.items():
        if probe_id is not None and pid != probe_id:
            continue
        bind = runtime.get("probes", {}).get(pid, {})
        errors.extend(_blocked_errors(pid, bind, target))
        if target["state"] == "ENGINEERING_BLOCKED":
            continue
        errors.extend(_identity_errors(pid, bind, target))
        hooks = bind.get("native_hooks")
        if (not isinstance(hooks, list) or not hooks or target["hook_id"] not in hooks
                or bind.get("full_coding_smoke") is not True):
            errors.append(f"{pid}: full coding smoke and frozen native hooks unbound")
            continue
        evidence_dir = Path(captures_root) / pid
        try:
            rows = [json.loads(line) for line in (evidence_dir / "events.jsonl").read_text().splitlines()]
            if not rows or not any(row["operation"] == "termination" and row["status"] == "success"
                                   and json.loads((evidence_dir / row["raw_path"]).read_text()).get("reason") == "finalized"
                                   for row in rows):
                raise ValueError("no successfully finalized full coding smoke")
            if any(row["probe"] != pid or row["binding"].get("code_commit") != runtime["code_commit"]
                   or row["binding"].get("source_commit") != bind["source_commit"]
                   or row["hook_id"] not in set(hooks) | COMMON_HOOKS
                   or row["hook_id"] == "offline-contract-smoke" for row in rows):
                raise ValueError("full coding smoke provenance differs from native binding")
            native_rows = [row for row in rows if row["hook_id"] in hooks]
            if not NATIVE_REQUIRED[pid] <= {row["operation"] for row in native_rows}:
                raise ValueError("required architecture operations missing from native hook")
            if not {"model_input", "model_output", "file_change", "test_run", "termination"} <= {
                row["operation"] for row in rows
            }:
                raise ValueError("model, code change, test or termination evidence incomplete")
            if any(json.loads((evidence_dir / row["raw_path"]).read_text()).get("model") != expected_version
                   for row in rows if row["operation"] == "model_output"):
                raise ValueError("provider output differs from frozen subject version")
            if pid == "X3":
                remote = [row for row in rows if row["hook_id"] == "a2a.native.remote_model"]
                if (bind.get("remote_model_evidence") is not True
                        or not {"model_input", "model_output"} <= {row["operation"] for row in remote}
                        or any("provider_response" not in json.loads((evidence_dir / row["raw_path"]).read_text())
                               for row in remote if row["operation"] == "model_output")):
                    raise ValueError("A2A artifact lacks actual remote subject model input/output evidence")
            check_capture(evidence_dir)
        except (OSError, ValueError, KeyError, AssertionError) as exc:
            errors.append(f"{pid}: full coding evidence gate failed ({exc})")
    return errors


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-manifest", required=True)
    parser.add_argument("--captures-root", required=True)
    parser.add_argument("--level", choices=("native-smoke", "subject"), default="subject")
    parser.add_argument("--probe", choices=[f"X{index}" for index in range(1, 8)])
    args = parser.parse_args()
    if args.level == "native-smoke":
        errors = native_smoke_blockers(args.runtime_manifest, args.captures_root, args.probe)
    else:
        errors = blockers(args.runtime_manifest, args.captures_root, args.probe)
    if errors:
        raise SystemExit("GATE=CLOSED\n" + "\n".join(errors))
    runtime = json.loads(Path(args.runtime_manifest).read_text())
    blocked = sorted(pid for pid, bind in runtime["probes"].items()
                     if bind.get("engineering_status") == "ENGINEERING_BLOCKED")
    if args.level == "native-smoke":
        print("NATIVE_SMOKE_GATE=PASS; SUBJECT_GATE=CLOSED; engineering_blocked=" + ",".join(blocked))
    else:
        print("SUBJECT_GATE=OPEN_FOR_NONBLOCKED_PROBES; engineering_blocked=" + ",".join(blocked))


if __name__ == "__main__":
    main()
