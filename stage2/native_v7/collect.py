"""One-shot native collection launcher for Stage-II v7.

This launcher does not import the v6 CodingArena or any shared transport. It
reserves a cell only after a probe-specific native runner and real-provider
subject-readiness gate have both been verified.
"""
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

from .execution_binding import execution_surface_digest
from .observer import ExternalObserver, verify_observer
from .policy import load_registry

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "stage2"
TASKS = {row["id"]: row for row in json.loads((STAGE2 / "tasks.json").read_text())["tasks"]}


def _expand(argv_template, values):
    return [part.format_map(values) for part in argv_template]


def validate_request(probe, task, registry_path=None):
    if task not in TASKS:
        raise ValueError("task is outside frozen T1-T3")
    registry = load_registry(registry_path)
    spec = registry["probes"].get(probe)
    if spec is None:
        raise ValueError("probe is outside frozen X1-X7")
    state = spec["collection_state"]
    if state == "PENDING_NATIVE_RUNNER":
        raise ValueError(f"{probe}: native runner is not verified; natural collection remains closed")
    if state == "NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING":
        raise ValueError(
            f"{probe}: native runner is verified but real-provider subject readiness is pending; "
            "natural collection remains closed"
        )
    if state != "SUBJECT_READY":
        raise ValueError(f"{probe}: unrecognized collection state: {state}")
    launch = spec["launch"]
    if launch.get("state") != "VERIFIED_NATIVE_ENTRYPOINT":
        raise ValueError(f"{probe}: native entrypoint is not verified")
    readiness = spec.get("subject_readiness") or {}
    current_surface = execution_surface_digest(probe, registry=registry)
    if readiness.get("execution_surface_sha256") != current_surface:
        raise ValueError(
            f"{probe}: current execution surface differs from the subject-readiness binding"
        )
    return registry, spec


def collect(*, probe, task, out_root, registry_path=None):
    registry, spec = validate_request(probe, task, registry_path)
    cell = f"{probe}-{task}"
    destination = Path(out_root) / cell
    destination.mkdir(parents=True, exist_ok=False)

    checkout = destination / "checkout"
    shutil.copytree(STAGE2 / "fixtures/project", checkout)
    task_file = destination / "task.json"
    task_file.write_text(json.dumps(TASKS[task], ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    observer = ExternalObserver(destination / "observer", probe=probe, cell=cell)
    values = {
        "checkout": str(checkout),
        "task_file": str(task_file),
        "roles_file": str(STAGE2 / "roles.json"),
        "subject_file": str(STAGE2 / "subject.json"),
        "observer_root": str(observer.root),
        "cell_root": str(destination),
    }
    argv = _expand(spec["launch"]["argv_template"], values)
    observer.record_invocation(argv, checkout, spec["environment_id"])

    env = os.environ.copy()
    env["STAGE2_V7_PROBE"] = probe
    env["STAGE2_V7_CELL"] = cell
    env["STAGE2_V7_OBSERVER_ROOT"] = str(observer.root)
    completed = subprocess.run(argv, cwd=checkout, env=env, capture_output=True, check=False)
    observer.record_process_result(
        stdout=completed.stdout, stderr=completed.stderr, returncode=completed.returncode
    )
    observer.seal()

    seal = {
        "schema": "stage2-v7-natural-cell-seal-v1",
        "cell": cell,
        "probe": probe,
        "task": task,
        "registry_schema": registry["schema"],
        "environment_id": spec["environment_id"],
        "runner_state": spec["collection_state"],
        "returncode": completed.returncode,
        "observer_files": verify_observer(observer.root),
        "status": (
            "RECORDED_PENDING_POSTHOC_AUDIT"
            if completed.returncode == 0
            else "FAILED_ATTEMPT_PRESERVED"
        ),
    }
    (destination / "seal.json").write_text(
        json.dumps(seal, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    return seal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", required=True, choices=[f"X{i}" for i in range(1, 8)])
    parser.add_argument("--task", required=True, choices=[f"T{i}" for i in range(1, 4)])
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--registry")
    args = parser.parse_args()
    result = collect(
        probe=args.probe, task=args.task, out_root=args.out_root, registry_path=args.registry
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
