from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from arena.providers import ScriptedProvider
from stage2.r7_checkpoint_v1.common import CheckpointRegistry
from stage2.r7_checkpoint_v1.controller import ProspectiveCheckpointController

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "stage2"


SCRIPT = [
    {"actions": [{"type": "delegate", "to": "frontend", "content": "Inspect the checkout boundary."}]},
    {"actions": [{"type": "list_files"}]},
    {"actions": [{"type": "finalize", "answer": "Frontend inspection completed."}]},
    {"actions": [{"type": "delegate", "to": "qa", "content": "Run the frozen tests and report."}]},
    {"actions": [{"type": "run_tests"}]},
    {"actions": [{"type": "finalize", "answer": "Frozen tests completed."}]},
    {"actions": [{"type": "finalize", "answer": "Prospective checkpoint preflight complete."}]},
]


def tree_digest(root: Path) -> str:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            rows.append(
                f"{path.relative_to(root)}\0{hashlib.sha256(path.read_bytes()).hexdigest()}"
            )
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def task_file(root: Path, task_id="T2") -> Path:
    task = next(
        row for row in json.loads((STAGE2 / "tasks.json").read_text())["tasks"]
        if row["id"] == task_id
    )
    path = root / f"{task_id}.json"
    path.write_text(json.dumps(task, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return path


async def host_preflight(root: Path) -> dict:
    from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost
    from stage2.r7_prospective_v1.host import ProspectiveCheckpointedSoftwareEngineeringHost
    from stage2.r7_prospective_v1.recorders import HostBoundaryCheckpointRecorder

    base_checkout = root / "base-checkout"
    prospective_checkout = root / "prospective-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", base_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", prospective_checkout)

    base = SoftwareEngineeringHost(
        task_id="T2",
        checkout=base_checkout,
        provider=ScriptedProvider(SCRIPT),
    )
    base_result = await base.run()

    registry = CheckpointRegistry(root / "registry")
    controller = ProspectiveCheckpointController()
    recorder = HostBoundaryCheckpointRecorder(
        registry=registry,
        controller=controller,
        system_id="X5_RAG",
        group_id="G1-PREFLIGHT",
        run_id="host-preflight",
        task_id="T2",
        external_carrier_refs=[
            {
                "carrier": "RAG",
                "ref": "preflight-read-only-carrier",
                "sha256": "a" * 64,
                "mutation": "FORBIDDEN",
            }
        ],
    )
    prospective = ProspectiveCheckpointedSoftwareEngineeringHost(
        task_id="T2",
        checkout=prospective_checkout,
        provider=ScriptedProvider(SCRIPT),
        checkpoint_hook=recorder,
    )
    prospective_result = await prospective.run()

    comparable_base = {
        "answer": base_result["answer"],
        "stop_reason": base_result["stop_reason"],
        "turns": base_result["turns"],
        "pending_roles": base_result["pending_roles"],
        "history": base_result["history"],
    }
    comparable_prospective = {
        "answer": prospective_result["answer"],
        "stop_reason": prospective_result["stop_reason"],
        "turns": prospective_result["turns"],
        "pending_roles": prospective_result["pending_roles"],
        "history": prospective_result["history"],
    }
    if comparable_base != comparable_prospective:
        raise RuntimeError(
            f"prospective host hook changed scripted control flow: "
            f"{comparable_base!r} != {comparable_prospective!r}"
        )
    if tree_digest(base_checkout) != tree_digest(prospective_checkout):
        raise RuntimeError("prospective host hook changed checkout effects")
    expected = prospective_result["turns"] + 2
    if len(recorder.manifests) != expected:
        raise RuntimeError(
            f"expected task-start + per-turn + terminal checkpoints ({expected}), "
            f"observed {len(recorder.manifests)}"
        )
    if any(row["restore_capability"] != "FULL_NATIVE" for row in recorder.manifests):
        raise RuntimeError("host checkpoint was not FULL_NATIVE")
    if controller.model_decision_sequence != prospective_result["turns"]:
        raise RuntimeError("host model-decision sequence does not match completed turns")

    return {
        "schema": "RB-STAGE2-R7-G1-HOST-HOOK-PREFLIGHT-v1",
        "status": "PASS",
        "provider_calls": 0,
        "subject_calls": 0,
        "scripted_model_decisions": prospective_result["turns"],
        "checkpoint_count": len(recorder.manifests),
        "control_flow_equivalent": True,
        "checkout_equivalent": True,
        "foreign_carrier_mutation": False,
        "first_checkpoint_hash": recorder.manifests[0]["checkpoint_hash"],
        "last_checkpoint_hash": recorder.manifests[-1]["checkpoint_hash"],
    }


async def metagpt_preflight(root: Path) -> dict:
    from stage2.native_v7.x2_metagpt.runner import run_task as native_run_task
    from stage2.r7_prospective_v1.recorders import MetaGPTBoundaryCheckpointRecorder
    from stage2.r7_prospective_v1.x2_metagpt import run_task_with_checkpoints

    base_checkout = root / "base-checkout"
    prospective_checkout = root / "prospective-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", base_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", prospective_checkout)
    tf = task_file(root, "T2")

    base_result = await native_run_task(
        checkout=base_checkout,
        task_file=tf,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=None,
        provider=ScriptedProvider(SCRIPT),
    )

    registry = CheckpointRegistry(root / "registry")
    controller = ProspectiveCheckpointController()
    recorder = MetaGPTBoundaryCheckpointRecorder(
        registry=registry,
        controller=controller,
        group_id="G1-PREFLIGHT",
        run_id="x2-preflight",
        task_id="T2",
    )
    prospective_result = await run_task_with_checkpoints(
        checkout=prospective_checkout,
        task_file=tf,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=None,
        provider=ScriptedProvider(SCRIPT),
        checkpoint_hook=recorder,
    )

    keys = [
        "answer",
        "stop_reason",
        "turns",
        "metagpt_rounds",
        "environment_messages",
        "pending_messages",
        "history",
    ]
    if {k: base_result[k] for k in keys} != {k: prospective_result[k] for k in keys}:
        raise RuntimeError("prospective MetaGPT checkpoint hooks changed native scripted result")
    if tree_digest(base_checkout) != tree_digest(prospective_checkout):
        raise RuntimeError("prospective MetaGPT checkpoint hooks changed checkout effects")
    expected = prospective_result["metagpt_rounds"] + 2
    if len(recorder.manifests) != expected:
        raise RuntimeError(
            f"expected start + per-round + terminal checkpoints ({expected}), "
            f"observed {len(recorder.manifests)}"
        )
    if any(row["restore_capability"] != "FULL_NATIVE" for row in recorder.manifests):
        raise RuntimeError("MetaGPT checkpoint was not FULL_NATIVE")
    if controller.model_decision_sequence != prospective_result["metagpt_rounds"]:
        raise RuntimeError("MetaGPT checkpoint ledger lost a completed native round")

    return {
        "schema": "RB-STAGE2-R7-G1-METAGPT-HOOK-PREFLIGHT-v1",
        "status": "PASS",
        "provider_calls": 0,
        "subject_calls": 0,
        "scripted_model_decisions": prospective_result["turns"],
        "native_rounds": prospective_result["metagpt_rounds"],
        "checkpoint_count": len(recorder.manifests),
        "control_flow_equivalent": True,
        "checkout_equivalent": True,
        "first_checkpoint_hash": recorder.manifests[0]["checkpoint_hash"],
        "last_checkpoint_hash": recorder.manifests[-1]["checkpoint_hash"],
    }


def static_preflight() -> dict:
    boundaries = json.loads(
        (ROOT / "configs/stage2_r7_g1_checkpoint_safe_boundaries_v1.json").read_text()
    )
    x1 = (STAGE2 / "native_v7/x1_autogen/runner.py").read_text()
    x3 = (STAGE2 / "native_v7/x3_a2a/runner.py").read_text()
    autogen_adapter = (STAGE2 / "r7_checkpoint_v1/autogen_adapter.py").read_text()
    a2a_adapter = (STAGE2 / "r7_checkpoint_v1/a2a_adapter.py").read_text()

    if "team.run_stream" not in x1:
        raise RuntimeError("X1 runner geometry changed")
    if "Team.save_state" not in autogen_adapter or "team.load_state" not in autogen_adapter:
        raise RuntimeError("X1 public checkpoint API binding missing")
    if boundaries["systems"]["X1"]["mid_run_boundary"] != "UNPROVEN":
        raise RuntimeError("X1 mid-run checkpoint must remain fail-closed")

    if x3.count("_call_initial(") < 2:
        raise RuntimeError("X3 top-level request geometry changed")
    if "save_stage2_state" not in a2a_adapter or "load_stage2_state" not in a2a_adapter:
        raise RuntimeError("X3 role-service state API binding missing")
    if boundaries["systems"]["X3"]["mid_nested_call_boundary"] != "UNPROVEN":
        raise RuntimeError("X3 nested-call checkpoint must remain fail-closed")
    if "SendMessageRequest" in a2a_adapter or "AgentCard(" in a2a_adapter:
        raise RuntimeError("checkpoint adapter must not modify A2A protocol surface")

    return {
        "schema": "RB-STAGE2-R7-G1-STATIC-BOUNDARY-PREFLIGHT-v1",
        "status": "PASS",
        "provider_calls": 0,
        "subject_calls": 0,
        "x1_mid_run": "UNPROVEN_FAIL_CLOSED",
        "x3_mid_nested_call": "UNPROVEN_FAIL_CLOSED",
        "a2a_protocol_modified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", required=True, choices=["static", "host", "metagpt"])
    parser.add_argument("--out-root")
    args = parser.parse_args()

    def run(root: Path):
        if args.system == "static":
            return static_preflight()
        if args.system == "host":
            return asyncio.run(host_preflight(root))
        return asyncio.run(metagpt_preflight(root))

    if args.out_root:
        root = Path(args.out_root)
        root.mkdir(parents=True, exist_ok=False)
        result = run(root)
        (root / "report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
    else:
        with tempfile.TemporaryDirectory() as td:
            result = run(Path(td))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
