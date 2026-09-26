from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import tempfile
from pathlib import Path

from arena.providers import ScriptedProvider
from stage2.r7_checkpoint_v1.common import CheckpointRegistry, file_tree_digest
from stage2.r7_checkpoint_v1.controller import ProspectiveCheckpointController
from stage2.r7_prospective_v1.integration import (
    HostIntegratedCheckpointMonitorHook,
    MetaGPTIntegratedCheckpointMonitorHook,
)
from stage2.r7_prospective_v1.online_monitor import OnlineStructuralMonitor
from stage2.r7_prospective_v1.recorders import (
    HostBoundaryCheckpointRecorder,
    MetaGPTBoundaryCheckpointRecorder,
)
from stage2.r7_prospective_v1.run_manifest import build_run_manifest
from stage2.r7_prospective_v1.runtime_event_adapter import (
    PassiveActionTapProvider,
    RuntimeStructuralBridge,
)

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "stage2"

SCRIPT = [
    {"actions": [{"type": "read_file", "path": "README.md"}]},
    {"actions": [{"type": "delegate", "to": "reviewer", "content": "Independently inspect README.md."}]},
    {"actions": [{"type": "read_file", "path": "README.md"}]},
    {"actions": [{"type": "finalize", "answer": "Reviewer inspected the same file."}]},
    {"actions": [{"type": "finalize", "answer": "Integration preflight complete."}]},
]


def task_file(root: Path, task_id: str = "T2") -> Path:
    task = next(
        row for row in json.loads((STAGE2 / "tasks.json").read_text())["tasks"]
        if row["id"] == task_id
    )
    path = root / f"{task_id}.json"
    path.write_text(json.dumps(task, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return path


def compare_result(a: dict, b: dict, keys: list[str], label: str):
    left = {key: a[key] for key in keys}
    right = {key: b[key] for key in keys}
    if left != right:
        raise RuntimeError(f"{label} changed native scripted result: {left!r} != {right!r}")


def verify_packages(packages: list[dict]) -> dict:
    complete = [
        row for row in packages
        if row["repair_gate_status"] == "COMPLETE_FOR_STRUCTURED_REPAIR"
    ]
    foreign_blocked = [
        row for row in packages
        if row["detection_surface"].startswith("rag-hit:")
        and row["repair_gate_status"] == "LINEAGE_GAP_BLOCKED"
    ]
    file_rows = [row for row in complete if row["detection_surface"] == "file:README.md"]
    if not file_rows:
        raise RuntimeError("native event integration did not produce a repair-eligible repeated file package")
    if not foreign_blocked:
        raise RuntimeError("RAG carrier exposure did not retain fail-closed lineage boundary")
    for row in packages:
        if row["semantic_audit_used"] is not False or row["cpr_label"] is not None:
            raise RuntimeError("semantic/CPR input leaked into runtime package")
        if row["future_evidence_used"] is not False:
            raise RuntimeError("future evidence leaked into runtime package")
    return {
        "complete_count": len(complete),
        "foreign_lineage_gap_count": len(foreign_blocked),
        "file_package": file_rows[0],
    }


def verify_frozen_parent(controller: ProspectiveCheckpointController, file_package: dict) -> dict:
    frozen = controller.repair_parent_at_freeze()
    parent_hash = file_package["parent_reconstruction"]["parent_hash_refs"][0]
    if frozen.checkpoint_hash != parent_hash:
        raise RuntimeError("frozen package parent differs from controller parent")
    if controller.model_decision_sequence <= frozen.model_decision_sequence:
        raise RuntimeError("natural A did not continue after first eligible package")
    strict_current_blocked = False
    try:
        controller.repair_parent()
    except RuntimeError as exc:
        if "uncheckpointed model decision" not in str(exc):
            raise
        strict_current_blocked = True
    if not strict_current_blocked:
        raise RuntimeError("strict current-parent API did not distinguish historical frozen parent")
    return {
        "frozen_parent_hash": frozen.checkpoint_hash,
        "frozen_at_model_decision": frozen.model_decision_sequence,
        "natural_A_final_model_decision": controller.model_decision_sequence,
        "historical_parent_available_after_A": True,
        "strict_current_parent_blocked_after_A": True,
    }


async def rag_host_preflight(root: Path) -> dict:
    from stage2.native_v7.x5_rag.context import FrozenRAGContext
    from stage2.native_v7.x5_rag.runner import RAGSoftwareEngineeringHost
    from stage2.r7_prospective_v1.host import ProspectiveCheckpointedSoftwareEngineeringHost

    class ProspectiveRAGHost(ProspectiveCheckpointedSoftwareEngineeringHost):
        def __init__(self, *, rag_context, **kwargs):
            super().__init__(**kwargs)
            self.rag_context = rag_context

        def _prompt(self, role, observations):
            messages = super()._prompt(role, observations)
            return self.rag_context.enrich(messages, role=role, task=self.task)

    baseline_checkout = root / "baseline-checkout"
    prospective_checkout = root / "prospective-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", baseline_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", prospective_checkout)

    baseline_rag = FrozenRAGContext(observer_root=None, limit=3)
    baseline = RAGSoftwareEngineeringHost(
        rag_context=baseline_rag,
        task_id="T2",
        checkout=baseline_checkout,
        provider=ScriptedProvider(SCRIPT),
    )
    baseline_result = await baseline.run()
    baseline_rag.seal()

    registry = CheckpointRegistry(root / "registry")
    controller = ProspectiveCheckpointController()
    monitor = OnlineStructuralMonitor(mode="PACKAGE_FREEZE")
    tap = PassiveActionTapProvider(ScriptedProvider(SCRIPT))
    recorder = HostBoundaryCheckpointRecorder(
        registry=registry,
        controller=controller,
        system_id="X5_RAG",
        group_id="StageII-R7-G1",
        run_id="preflight-x5-t2",
        task_id="T2",
    )
    bridge = RuntimeStructuralBridge(
        tap=tap,
        monitor=monitor,
        controller=controller,
        cell_id="X5-T2",
    )
    hook = HostIntegratedCheckpointMonitorHook(recorder=recorder, bridge=bridge)
    prospective_rag = FrozenRAGContext(observer_root=None, limit=3)
    prospective = ProspectiveRAGHost(
        rag_context=prospective_rag,
        task_id="T2",
        checkout=prospective_checkout,
        provider=tap,
        checkpoint_hook=hook,
    )
    prospective_result = await prospective.run()
    prospective_rag.seal()

    compare_result(
        baseline_result,
        prospective_result,
        ["answer", "stop_reason", "turns", "pending_roles", "history"],
        "X5 prospective runtime adapter",
    )
    if file_tree_digest(baseline_checkout) != file_tree_digest(prospective_checkout):
        raise RuntimeError("X5 prospective monitor integration changed checkout effects")

    packages = monitor.packages()
    package_summary = verify_packages(packages)
    parent_summary = verify_frozen_parent(controller, package_summary["file_package"])

    manifest = build_run_manifest(
        cell_id="X5-T2",
        framework_binding={
            "system": "X5_RAG",
            "host": "software_engineering_host_v1",
            "retrieval": "stage2.retrieval.retrieve",
            "mode": "NON_STUDY_SCRIPTED_PREFLIGHT",
        },
        checkpoint_ledger=controller.ledger(),
        natural_result=prospective_result,
        monitor_snapshot=bridge.snapshot(),
        packages=packages,
        natural_subject_calls=0,
    )
    if manifest["semantic_audit_state"] != "LOCKED_UNTIL_A_AND_B_FROZEN":
        raise RuntimeError("run manifest opened semantic audit too early")
    if manifest["natural_A"]["repair_actions"] != 0 or not manifest["natural_A"]["frozen"]:
        raise RuntimeError("run manifest natural A accounting invalid")
    if not any(row["B_state"] == "READY" for row in manifest["repair_packages"]):
        raise RuntimeError("run manifest lost repair-ready structural package")
    if not any(row["B_state"] == "LINEAGE_GAP_BLOCKED" for row in manifest["repair_packages"]):
        raise RuntimeError("run manifest lost foreign-carrier lineage boundary")

    return {
        "schema": "RB-STAGE2-R7-G1-X5-NATIVE-EVENT-INTEGRATION-PREFLIGHT-v1",
        "status": "PASS",
        "provider_calls": 0,
        "subject_calls": 0,
        "scripted_model_decisions": prospective_result["turns"],
        "checkpoint_count": len(recorder.manifests),
        "structural_event_count": len(monitor.evidence()),
        "candidate_count": len(monitor.candidates()),
        "package_count": len(packages),
        "complete_package_count": package_summary["complete_count"],
        "foreign_lineage_gap_count": package_summary["foreign_lineage_gap_count"],
        "control_flow_equivalent": True,
        "checkout_equivalent": True,
        "semantic_audit_input": False,
        "cpr_input": False,
        "run_manifest_hash": manifest["manifest_hash"],
        **parent_summary,
    }


async def metagpt_preflight(root: Path) -> dict:
    from stage2.native_v7.x2_metagpt.runner import run_task as native_run_task
    from stage2.r7_prospective_v1.x2_metagpt import run_task_with_checkpoints

    baseline_checkout = root / "baseline-checkout"
    prospective_checkout = root / "prospective-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", baseline_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", prospective_checkout)
    tf = task_file(root, "T2")

    baseline_result = await native_run_task(
        checkout=baseline_checkout,
        task_file=tf,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=None,
        provider=ScriptedProvider(SCRIPT),
    )

    registry = CheckpointRegistry(root / "registry")
    controller = ProspectiveCheckpointController()
    monitor = OnlineStructuralMonitor(mode="PACKAGE_FREEZE")
    tap = PassiveActionTapProvider(ScriptedProvider(SCRIPT))
    recorder = MetaGPTBoundaryCheckpointRecorder(
        registry=registry,
        controller=controller,
        group_id="StageII-R7-G1",
        run_id="preflight-x2-t2",
        task_id="T2",
    )
    bridge = RuntimeStructuralBridge(
        tap=tap,
        monitor=monitor,
        controller=controller,
        cell_id="X2-T2",
    )
    hook = MetaGPTIntegratedCheckpointMonitorHook(recorder=recorder, bridge=bridge)
    prospective_result = await run_task_with_checkpoints(
        checkout=prospective_checkout,
        task_file=tf,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=None,
        provider=tap,
        checkpoint_hook=hook,
    )

    compare_result(
        baseline_result,
        prospective_result,
        [
            "answer",
            "stop_reason",
            "turns",
            "metagpt_rounds",
            "environment_messages",
            "pending_messages",
            "history",
        ],
        "X2 prospective runtime adapter",
    )
    if file_tree_digest(baseline_checkout) != file_tree_digest(prospective_checkout):
        raise RuntimeError("X2 prospective monitor integration changed checkout effects")

    packages = monitor.packages()
    complete = [
        row for row in packages
        if row["repair_gate_status"] == "COMPLETE_FOR_STRUCTURED_REPAIR"
        and row["detection_surface"] == "file:README.md"
    ]
    if not complete:
        raise RuntimeError("X2 native action stream did not produce repeated-file repair package")
    parent_summary = verify_frozen_parent(controller, complete[0])

    manifest = build_run_manifest(
        cell_id="X2-T2",
        framework_binding={
            "system": "X2_METAGPT",
            "framework": "MetaGPT",
            "version": "1.0.0",
            "mode": "NON_STUDY_SCRIPTED_PREFLIGHT",
        },
        checkpoint_ledger=controller.ledger(),
        natural_result=prospective_result,
        monitor_snapshot=bridge.snapshot(),
        packages=packages,
        natural_subject_calls=0,
    )
    if not any(row["B_state"] == "READY" for row in manifest["repair_packages"]):
        raise RuntimeError("X2 run manifest lost repair-ready package")

    return {
        "schema": "RB-STAGE2-R7-G1-X2-NATIVE-EVENT-INTEGRATION-PREFLIGHT-v1",
        "status": "PASS",
        "provider_calls": 0,
        "subject_calls": 0,
        "native_rounds": prospective_result["metagpt_rounds"],
        "checkpoint_count": len(recorder.manifests),
        "structural_event_count": len(monitor.evidence()),
        "candidate_count": len(monitor.candidates()),
        "package_count": len(packages),
        "complete_package_count": len([
            row for row in packages
            if row["repair_gate_status"] == "COMPLETE_FOR_STRUCTURED_REPAIR"
        ]),
        "control_flow_equivalent": True,
        "checkout_equivalent": True,
        "semantic_audit_input": False,
        "cpr_input": False,
        "run_manifest_hash": manifest["manifest_hash"],
        **parent_summary,
    }


def static_boundary_preflight() -> dict:
    boundaries = json.loads(
        (ROOT / "configs/stage2_r7_g1_checkpoint_safe_boundaries_v1.json").read_text()
    )
    parent = json.loads(
        (ROOT / "configs/stage2_r7_g1_parent_freeze_semantics_v1.json").read_text()
    )
    if boundaries["systems"]["X1"]["mid_run_boundary"] != "UNPROVEN":
        raise RuntimeError("X1 in-flight boundary unexpectedly opened")
    if boundaries["systems"]["X3"]["mid_nested_call_boundary"] != "UNPROVEN":
        raise RuntimeError("X3 nested A2A boundary unexpectedly opened")
    if parent["after_package_freeze"]["B_launch_after_A_freeze_may_restore_original_frozen_parent"] is not True:
        raise RuntimeError("G1 parent freeze semantics do not preserve A/B geometry")
    return {
        "schema": "RB-STAGE2-R7-G1-NATIVE-EVENT-STATIC-BOUNDARY-PREFLIGHT-v1",
        "status": "PASS",
        "provider_calls": 0,
        "subject_calls": 0,
        "X1_mid_run": "CHECKPOINT_BOUNDARY_BLOCKED",
        "X3_nested_call": "CHECKPOINT_BOUNDARY_BLOCKED",
        "historical_parent_survives_natural_A_continuation": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", choices=["static", "x2", "x5"], required=True)
    parser.add_argument("--out-root")
    args = parser.parse_args()

    def run(root: Path):
        if args.system == "static":
            return static_boundary_preflight()
        if args.system == "x2":
            return asyncio.run(metagpt_preflight(root))
        return asyncio.run(rag_host_preflight(root))

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
