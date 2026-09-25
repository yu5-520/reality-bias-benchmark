"""Verify all four exact-target, non-study coding smoke artifacts in CI."""
import argparse
import json
from pathlib import Path

from .evidence import check_capture
from .freeze import BASE, hash_file

EXPECTED = {"X1", "X3", "X4", "X5"}
NATIVE_OPERATIONS = {
    "X1": {"delegate", "receive_message"},
    "X3": {"remote_task", "artifact_return"},
    "X4": {"resource_read", "tool_call"},
    "X5": {"retrieve"},
}


def verify_artifacts(root, code_commit):
    root = Path(root)
    targets = json.loads((BASE / "runtime_bindings.json").read_text())["probes"]
    found = {}
    for artifact in root.glob("stage2-target-coding-X*-*"):
        report = json.loads((artifact / "report.json").read_text())
        pid = report["probe"]
        if pid not in EXPECTED or pid in found:
            raise ValueError("duplicate or unexpected target coding artifact")
        target = targets[pid]
        expected_commit = target.get("sdk_commit") or target.get("source_commit")
        if (report["code_commit"] != code_commit or report["target_sdk_commit"] != expected_commit
                or report["status"] != "NON_STUDY_TARGET_CODING_SMOKE_PASS"
                or report["provider"] != "SCRIPTED_ENGINEERING_ONLY" or report["subject_ready"] is not False):
            raise ValueError(f"{pid}: report does not bind frozen code and target identity")
        evidence = artifact / "evidence"
        count = check_capture(evidence)
        rows = [json.loads(line) for line in (evidence / "events.jsonl").read_text().splitlines()]
        if count != report["events"] or report["turns"] != 7:
            raise ValueError(f"{pid}: incomplete scripted action route")
        native = [row for row in rows if row["hook_id"] == target["hook_id"]]
        if not NATIVE_OPERATIONS[pid] <= {row["operation"] for row in native}:
            raise ValueError(f"{pid}: target SDK did not produce required native operations")
        if any(row["binding"]["code_commit"] != code_commit
               or row["binding"].get("sdk_commit") != target.get("sdk_commit")
               for row in rows):
            raise ValueError(f"{pid}: evidence binding diverges from target checkout")
        operations = {row["operation"] for row in rows}
        if not {"model_input", "model_output", "file_change", "test_run", "termination"} <= operations:
            raise ValueError(f"{pid}: shared coding evidence incomplete")
        allowed_models = {"SCRIPTED_PREFLIGHT_ONLY", "SCRIPTED_REMOTE_PREFLIGHT_ONLY"} if pid == "X3" else {
            "SCRIPTED_PREFLIGHT_ONLY"}
        if any(json.loads((evidence / row["raw_path"]).read_text()).get("model") not in allowed_models
               for row in rows if row["operation"] == "model_output"):
            raise ValueError(f"{pid}: scripted smoke unexpectedly used a subject provider")
        if pid == "X3":
            remote = [row for row in rows if row["hook_id"] == "a2a.native.remote_model"]
            if (report.get("remote_execution") != "SCRIPTED_REMOTE_ONLY" or
                    sum(row["operation"] == "model_input" for row in remote) != 5 or
                    sum(row["operation"] == "model_output" for row in remote) != 5):
                raise ValueError("X3: actual remote role-model input/output evidence is missing")
        if any(row["operation"] == "test_run" and row["status"] != "success" for row in rows):
            raise ValueError(f"{pid}: checkout test did not pass")
        if not (artifact / "checkout/web/index.html").is_file():
            raise ValueError(f"{pid}: checkout missing")
        if hash_file(artifact / "checkout/web/index.html") == hash_file(BASE / "fixtures/project/web/index.html"):
            raise ValueError(f"{pid}: no isolated checkout edit was observed")
        found[pid] = count
    if set(found) != EXPECTED:
        raise ValueError(f"target coding artifacts incomplete: {EXPECTED - set(found)}")
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()
    print("TARGET_CODING_SMOKE=PASS; SUBJECT_GATE=CLOSED; events="
          + json.dumps(verify_artifacts(args.artifact_root, args.code_commit), sort_keys=True))


if __name__ == "__main__":
    main()
