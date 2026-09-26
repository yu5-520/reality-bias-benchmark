from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from stage2.r7_checkpoint_v1.common import CheckpointRegistry
from stage2.r7_prospective_v1.online_monitor import OnlineStructuralMonitor
from stage2.r7_prospective_v1.repair_boundary_watcher import (
    RepairBoundaryViolation,
    RepairBoundaryWatcher,
)

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "stage2"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_checkpoint(root: Path) -> dict:
    checkout = root / "checkout"
    shutil.copytree(STAGE2 / "fixtures/project", checkout)
    registry = CheckpointRegistry(root / "registry")
    return registry.capture(
        system_id="X5_RAG",
        group_id="G1-PREFLIGHT",
        run_id="online-monitor-preflight",
        task_id="T2",
        event_ref="preflight:checkpoint:2",
        adapter_id="synthetic-g1-online-monitor-preflight",
        framework_binding={"type": "non-study-synthetic-runtime"},
        native_state={"turn": 2, "queue": ["reviewer"]},
        application_root=checkout,
        model_visible_context={"boundary": "post-turn-2"},
        remaining_horizon=30,
        external_carrier_refs=[
            {
                "carrier": "RAG",
                "ref": "preflight-rag",
                "sha256": "a" * 64,
                "mutation": "FORBIDDEN",
            }
        ],
        restore_capability="FULL_NATIVE",
        replication_binding={
            "contract": "RB-STAGE2-R7-G1-PROSPECTIVE-REPAIR-CONTRACT-v1"
        },
    )


def event(
    sequence: int,
    *,
    actor: str,
    kind: str,
    object_refs: list[str],
    written_refs: list[str] | None = None,
    downstream: list[str] | None = None,
    preserve: list[str] | None = None,
) -> dict:
    return {
        "sequence": sequence,
        "event_ref": f"preflight:event:{sequence:04d}",
        "cell_id": "X5-T2",
        "actor": actor,
        "kind": kind,
        "object_refs": object_refs,
        "written_refs": written_refs or [],
        "downstream_legal_refs": downstream or [],
        "preserve_refs": preserve or [],
    }


def expect_violation(fn, token: str):
    try:
        fn()
    except RepairBoundaryViolation as exc:
        if token not in str(exc):
            raise RuntimeError(f"expected violation {token}, observed {exc}") from exc
        return str(exc)
    raise RuntimeError("expected RepairBoundaryViolation")


def run(root: Path) -> dict:
    checkpoint = make_checkpoint(root)
    checkout = root / "checkout"
    preserve_ref = "file:tests/test_checkout.py"
    preserve_hash = sha256_file(checkout / "tests/test_checkout.py")
    preserve = [preserve_ref]

    monitor = OnlineStructuralMonitor(mode="PACKAGE_FREEZE")
    if monitor.feed(
        event(1, actor="release_lead", kind="READ", object_refs=["file:README.md"], preserve=preserve),
        checkpoint_manifest=checkpoint,
        checkpoint_fresh=True,
    ):
        raise RuntimeError("package froze before a structural rule triggered")

    packages = monitor.feed(
        event(2, actor="reviewer", kind="READ", object_refs=["file:README.md"], preserve=preserve),
        checkpoint_manifest=checkpoint,
        checkpoint_fresh=True,
    )
    if len(packages) != 1:
        raise RuntimeError("expected first eligible file package at event 2")
    package = packages[0]
    if package["repair_gate_status"] != "COMPLETE_FOR_STRUCTURED_REPAIR":
        raise RuntimeError("file package did not pass repair gate")
    if package["parent_reconstruction"]["parent_hash_refs"] != [checkpoint["checkpoint_hash"]]:
        raise RuntimeError("package did not bind exact checkpoint hash")
    frozen_hash = package["package_hash"]
    frozen_support = list(package["support_refs"])

    later = monitor.feed(
        event(3, actor="qa", kind="READ", object_refs=["file:README.md"], preserve=preserve),
        checkpoint_manifest=checkpoint,
        checkpoint_fresh=True,
    )
    if later:
        raise RuntimeError("already-frozen structural object produced a second package")
    after = monitor.packages()[0]
    if after["package_hash"] != frozen_hash or after["support_refs"] != frozen_support:
        raise RuntimeError("future event expanded or rewrote frozen package")

    guard = RepairBoundaryWatcher(
        package=package,
        preserve_hashes={preserve_ref: preserve_hash},
    )
    action = guard.record_action(
        {
            "action_ref": "repair:1",
            "native_interface": "native:write_file",
            "target_ref": "file:README.md",
            "mutation_class": "APPLICATION_WRITE",
            "before_hash": "b" * 64,
            "after_hash": "c" * 64,
        },
        current_preserve_hashes={preserve_ref: preserve_hash},
    )
    repair_result = guard.finish(
        current_preserve_hashes={preserve_ref: preserve_hash}
    )
    post_watch = guard.observe_post_repair(
        {
            "event_ref": "post:1",
            "kind": "OLD_SUPPORT_REENTRY_CHECK",
            "object_refs": ["file:README.md"],
        }
    )
    post_action_violation = expect_violation(
        lambda: guard.attempt_post_repair_action(
            {"mutation_class": "APPLICATION_WRITE"}
        ),
        "POST_REPAIR_CONTINUOUS_REPAIR_FORBIDDEN",
    )

    forbidden_guard = RepairBoundaryWatcher(
        package=package,
        preserve_hashes={preserve_ref: preserve_hash},
    )
    forbidden_violation = expect_violation(
        lambda: forbidden_guard.record_action(
            {
                "action_ref": "repair:forbidden",
                "native_interface": "native:write_file",
                "target_ref": "file:README.md",
                "mutation_class": "RAG_INTERNAL_MUTATION",
                "before_hash": "b" * 64,
                "after_hash": "c" * 64,
            },
            current_preserve_hashes={preserve_ref: preserve_hash},
        ),
        "FORBIDDEN_MUTATION_CLASS",
    )

    preserve_guard = RepairBoundaryWatcher(
        package=package,
        preserve_hashes={preserve_ref: preserve_hash},
    )
    preserve_violation = expect_violation(
        lambda: preserve_guard.record_action(
            {
                "action_ref": "repair:preserve",
                "native_interface": "native:write_file",
                "target_ref": "file:README.md",
                "mutation_class": "APPLICATION_WRITE",
                "before_hash": "b" * 64,
                "after_hash": "c" * 64,
            },
            current_preserve_hashes={preserve_ref: "d" * 64},
        ),
        "PRESERVE_SET_MISMATCH",
    )

    foreign = OnlineStructuralMonitor(mode="PACKAGE_FREEZE")
    foreign.feed(
        event(1, actor="release_lead", kind="CARRIER", object_refs=["rag-hit:doc-A"], preserve=preserve),
        checkpoint_manifest=checkpoint,
        checkpoint_fresh=True,
    )
    foreign_package = foreign.feed(
        event(2, actor="reviewer", kind="CARRIER", object_refs=["rag-hit:doc-A"], preserve=preserve),
        checkpoint_manifest=checkpoint,
        checkpoint_fresh=True,
    )[0]
    if foreign_package["repair_gate_status"] != "LINEAGE_GAP_BLOCKED":
        raise RuntimeError("immutable foreign carrier unexpectedly became direct repair surface")
    foreign_frozen_hash = foreign_package["package_hash"]
    foreign.feed(
        event(
            3,
            actor="qa",
            kind="CARRIER",
            object_refs=["rag-hit:doc-A"],
            downstream=["file:README.md"],
            preserve=preserve,
        ),
        checkpoint_manifest=checkpoint,
        checkpoint_fresh=True,
    )
    if foreign.packages()[0]["package_hash"] != foreign_frozen_hash:
        raise RuntimeError("future downstream evidence expanded a frozen foreign package")

    stale = OnlineStructuralMonitor(mode="PACKAGE_FREEZE")
    stale.feed(
        event(1, actor="release_lead", kind="READ", object_refs=["state:release"], preserve=preserve),
        checkpoint_manifest=checkpoint,
        checkpoint_fresh=True,
    )
    stale_package = stale.feed(
        event(2, actor="reviewer", kind="READ", object_refs=["state:release"], preserve=preserve),
        checkpoint_manifest=checkpoint,
        checkpoint_fresh=False,
    )[0]
    if stale_package["repair_gate_status"] != "PARENT_RECONSTRUCTION_BLOCKED":
        raise RuntimeError("stale checkpoint did not fail closed")
    if stale_package["g1_block_code"] != "CHECKPOINT_BOUNDARY_BLOCKED":
        raise RuntimeError("stale checkpoint lost G1 boundary code")

    watch_only = OnlineStructuralMonitor(mode="WATCH_ONLY")
    watch_only.feed(
        event(1, actor="release_lead", kind="READ", object_refs=["file:README.md"], preserve=preserve),
        checkpoint_manifest=checkpoint,
        checkpoint_fresh=True,
    )
    watch_only.feed(
        event(2, actor="reviewer", kind="READ", object_refs=["file:README.md"], preserve=preserve),
        checkpoint_manifest=checkpoint,
        checkpoint_fresh=True,
    )
    if watch_only.packages():
        raise RuntimeError("post-repair WATCH_ONLY monitor generated a repair package")
    if len(watch_only.candidates()) != 1:
        raise RuntimeError("WATCH_ONLY monitor failed to retain structural evidence")

    return {
        "schema": "RB-STAGE2-R7-G1-ONLINE-MONITOR-PREFLIGHT-v1",
        "status": "PASS",
        "provider_calls": 0,
        "subject_calls": 0,
        "semantic_audit_input": False,
        "cpr_input": False,
        "first_eligible_prefix_sequence": package["prefix_sequence"],
        "package_checkpoint_hash": checkpoint["checkpoint_hash"],
        "package_hash": package["package_hash"],
        "future_event_package_immutability": "PASS",
        "valid_repair_action_boundary": action["boundary_status"],
        "repair_executor_exit": repair_result["repair_executor_exited"],
        "post_repair_watch_only": post_watch["repair_action_allowed"] is False,
        "post_repair_action_violation": post_action_violation,
        "forbidden_foreign_mutation_violation": forbidden_violation,
        "preserve_set_violation": preserve_violation,
        "foreign_carrier_without_downstream_binding": foreign_package["repair_gate_status"],
        "stale_checkpoint_gate": stale_package["g1_block_code"],
        "watch_only_candidate_count": len(watch_only.candidates()),
        "watch_only_package_count": len(watch_only.packages()),
    }


def main():
    with tempfile.TemporaryDirectory() as td:
        result = run(Path(td))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
