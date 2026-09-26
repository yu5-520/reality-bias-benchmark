from __future__ import annotations

import copy
from typing import Any

from stage2.r7_checkpoint_v1.common import digest


FROZEN_INPUT_BLOBS = {
    "tasks_blob": "0c75802fef3532dac794e3b730faa79cc33bf95a",
    "roles_blob": "259f406f81b73da17915f13285cf35ba2c3d0e24",
    "subject_blob": "64135cdd5ae352d3322a96c32432ba1da701a3b5",
    "action_contract_blob": "0432514610b978d62d56680c3c250b3b9276a16c",
}


def build_run_manifest(
    *,
    cell_id: str,
    framework_binding: dict[str, Any],
    checkpoint_ledger: dict[str, Any],
    natural_result: dict[str, Any],
    monitor_snapshot: dict[str, Any],
    packages: list[dict[str, Any]],
    natural_subject_calls: int,
    repair_subject_calls: int = 0,
    paid_evaluator_calls: int = 0,
) -> dict[str, Any]:
    system_id, task_id = cell_id.split("-", 1)
    checkpoint_hash = digest(checkpoint_ledger)
    natural_hash = digest(natural_result)
    monitor_hash = digest(monitor_snapshot)

    package_rows = []
    for package in packages:
        complete = package.get("repair_gate_status") == "COMPLETE_FOR_STRUCTURED_REPAIR"
        parents = package.get("parent_reconstruction", {}).get("parent_hash_refs") or []
        package_rows.append({
            "package_id": package["package_id"],
            "package_sha256": package["package_hash"],
            "gate_status": package["repair_gate_status"],
            "parent_checkpoint_hash": parents[0] if parents else None,
            "B_attempts": 0,
            "B_state": "READY" if complete else (
                package.get("g1_block_code") or "NOT_ELIGIBLE"
            ),
            "B_archive_ref": None,
            "B_sha256": None,
        })

    out = {
        "schema": "RB-STAGE2-R7-G1-RUN-MANIFEST-v1",
        "group_id": "StageII-R7-G1",
        "cell_id": cell_id,
        "system_id": system_id,
        "task_id": task_id,
        "natural_attempt_index": 1,
        "framework_binding": copy.deepcopy(framework_binding),
        "input_bindings": dict(FROZEN_INPUT_BLOBS),
        "checkpoint_ledger": {
            "ref": "inline:checkpoint-ledger",
            "sha256": checkpoint_hash,
            "full_checkpoint_count": len(checkpoint_ledger.get("checkpoints") or []),
            "environment_mismatch": False,
        },
        "natural_A": {
            "archive_ref": "inline:natural-result",
            "sha256": natural_hash,
            "repair_actions": 0,
            "frozen": True,
        },
        "monitor": {
            "future_blind": True,
            "semantic_audit_input": False,
            "cpr_input": False,
            "output_ref": "inline:monitor-snapshot",
            "output_sha256": monitor_hash,
        },
        "repair_packages": package_rows,
        "provider_accounting": {
            "natural_subject_calls": int(natural_subject_calls),
            "repair_subject_calls": int(repair_subject_calls),
            "paid_evaluator_calls": int(paid_evaluator_calls),
        },
        "semantic_audit_state": "LOCKED_UNTIL_A_AND_B_FROZEN",
    }
    out["manifest_hash"] = digest(out)
    return out
