from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import tempfile
from pathlib import Path

from arena.providers import ScriptedProvider
from stage2.r7_checkpoint_v1.common import file_tree_digest
from stage2.r7_prospective_v1.capability_runner import run_capability_natural_A

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "stage2"

SCRIPT_TWO = [
    {"actions": [{"type": "list_files"}]},
    {"actions": [{"type": "finalize", "answer": "readiness preflight complete"}]},
]
SCRIPT_ONE = [
    {"actions": [{"type": "finalize", "answer": "readiness preflight complete"}]},
]


def _task_file(root: Path, task_id: str) -> Path:
    task = next(
        row for row in json.loads((STAGE2 / "tasks.json").read_text())["tasks"]
        if row["id"] == task_id
    )
    path = root / f"{task_id}.json"
    path.write_text(json.dumps(task, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return path


def _compare(base: dict, prospective: dict, label: str):
    keys = ["answer", "stop_reason", "turns"]
    left = {key: base[key] for key in keys}
    right = {key: prospective[key] for key in keys}
    if left != right:
        raise RuntimeError(f"{label} result mismatch: {left!r} != {right!r}")


def _load_seal(root: Path) -> dict:
    return json.loads((root / "seal.json").read_text())


def _verify_seal(seal: dict, *, expected_decisions: int):
    if seal["status"] != "NATURAL_A_FROZEN_PENDING_REPAIR_GATE":
        raise RuntimeError("unexpected prospective seal status")
    if seal["provider_mode"] != "NON_STUDY_INJECTED":
        raise RuntimeError("preflight must not use scientific subject provider")
    if seal["natural_subject_calls"] != 0:
        raise RuntimeError("preflight leaked subject-call accounting")
    if seal["model_decision_count"] != expected_decisions:
        raise RuntimeError("unexpected prospective decision count")
    if seal["checkpoint_count"] != expected_decisions + 2:
        raise RuntimeError("expected task-start + per-turn + terminal checkpoints")
    if seal["repair_actions_during_A"] != 0:
        raise RuntimeError("natural A contains repair actions")




async def preflight_x1(root: Path) -> dict:
    from stage2.native_v7.x1_autogen.runner import run_task as native_run
    from stage2.native_v7.x1_autogen.smoke import _client

    task = _task_file(root, "T2")
    base_checkout = root / "base-checkout"
    pro_checkout = root / "pro-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", base_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", pro_checkout)

    base = await native_run(
        checkout=base_checkout,
        task_file=task,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=root / "base-observer",
        model_client=_client(),
    )
    out = root / "prospective"
    seal = await run_x1_natural_A(
        checkout=pro_checkout,
        task_file=task,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        out_root=out,
        model_client=_client(),
    )
    prospective = json.loads((out / "natural_A_result.json").read_text())
    keys = ["answer", "stop_reason", "messages", "native_events"]
    if {k: base[k] for k in keys} != {k: prospective[k] for k in keys}:
        raise RuntimeError("X1 prospective wrapper changed native AutoGen result")
    if file_tree_digest(base_checkout) != file_tree_digest(pro_checkout):
        raise RuntimeError("X1 prospective wrapper changed checkout")
    if seal["status"] != "NATURAL_A_FROZEN_REPAIR_MIDRUN_CHECKPOINT_BLOCKED":
        raise RuntimeError("X1 did not retain fail-closed mid-run repair boundary")
    if seal["provider_mode"] != "NON_STUDY_INJECTED" or seal["natural_subject_calls"] != 0:
        raise RuntimeError("X1 readiness smoke leaked scientific provider accounting")
    if seal["checkpoint_count"] != 2 or seal["midrun_checkpoint_status"] != "UNPROVEN_FAIL_CLOSED":
        raise RuntimeError("X1 safe checkpoint geometry changed")
    return {
        "schema": "RB-STAGE2-R7-G1-READINESS-X1-v1",
        "status": "PASS",
        "real_provider_calls": 0,
        "decision_count": seal["model_decision_count"],
        "checkpoint_count": seal["checkpoint_count"],
        "midrun_checkpoint_status": seal["midrun_checkpoint_status"],
        "control_flow_equivalent": True,
        "checkout_equivalent": True,
        "manifest_hash": seal["run_manifest_hash"],
    }


async def preflight_x3(root: Path) -> dict:
    from stage2.native_v7.x3_a2a.runner import ROLES as X3_ROLES, run_task as native_run
    from stage2.native_v7.x3_a2a.smoke import ROLE_SCRIPT

    task = _task_file(root, "T2")
    base_checkout = root / "base-checkout"
    pro_checkout = root / "pro-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", base_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", pro_checkout)

    script = dict(ROLE_SCRIPT)
    for role in [row["id"] for row in X3_ROLES["agents"]]:
        script.setdefault(
            role,
            [{"actions": [{"type": "finalize", "answer": f"{role} unused"}]}],
        )
    script_file = root / "x3-script.json"
    script_file.write_text(
        json.dumps(script, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )

    base = await native_run(
        checkout=base_checkout,
        task_file=task,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=root / "base-observer",
        mode="scripted",
        script_file=script_file,
    )
    out = root / "prospective"
    seal = await run_x3_natural_A(
        checkout=pro_checkout,
        task_file=task,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        out_root=out,
        mode="scripted",
        script_file=script_file,
    )
    prospective = json.loads((out / "natural_A_result.json").read_text())
    keys = ["answer", "stop_reason", "turns_used", "protocol_calls", "terminal", "trace"]
    if {k: base[k] for k in keys} != {k: prospective[k] for k in keys}:
        raise RuntimeError("X3 prospective sidecar wrapper changed native A2A result")
    if file_tree_digest(base_checkout) != file_tree_digest(pro_checkout):
        raise RuntimeError("X3 prospective wrapper changed checkout")
    if seal["status"] != "NATURAL_A_FROZEN_REPAIR_NESTED_CHECKPOINT_BLOCKED":
        raise RuntimeError("X3 did not retain fail-closed nested repair boundary")
    if seal["provider_mode"] != "NON_STUDY_SCRIPTED" or seal["natural_subject_calls"] != 0:
        raise RuntimeError("X3 readiness smoke leaked scientific provider accounting")
    if seal["checkpoint_count"] != 2 or seal["nested_checkpoint_status"] != "UNPROVEN_FAIL_CLOSED":
        raise RuntimeError("X3 safe checkpoint geometry changed")
    if seal["a2a_protocol_modified"] is not False:
        raise RuntimeError("X3 prospective sidecar modified A2A protocol")
    return {
        "schema": "RB-STAGE2-R7-G1-READINESS-X3-v1",
        "status": "PASS",
        "real_provider_calls": 0,
        "decision_count": seal["model_decision_count"],
        "checkpoint_count": seal["checkpoint_count"],
        "nested_checkpoint_status": seal["nested_checkpoint_status"],
        "a2a_protocol_modified": False,
        "control_flow_equivalent": True,
        "checkout_equivalent": True,
        "manifest_hash": seal["run_manifest_hash"],
    }

async def preflight_x2(root: Path) -> dict:
    from stage2.native_v7.x2_metagpt.runner import run_task as native_run
    from stage2.r7_prospective_v1.x1_runner import run_x1_natural_A
from stage2.r7_prospective_v1.x2_runner import run_x2_natural_A
from stage2.r7_prospective_v1.x3_runner import run_x3_natural_A

    task = _task_file(root, "T2")
    base_checkout = root / "base-checkout"
    pro_checkout = root / "pro-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", base_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", pro_checkout)

    base = await native_run(
        checkout=base_checkout,
        task_file=task,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=None,
        provider=ScriptedProvider(SCRIPT_TWO),
    )
    out = root / "prospective"
    seal = await run_x2_natural_A(
        checkout=pro_checkout,
        task_file=task,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        out_root=out,
        provider=ScriptedProvider(SCRIPT_TWO),
    )
    prospective = json.loads((out / "natural_A_result.json").read_text())
    _compare(base, prospective, "X2")
    if file_tree_digest(base_checkout) != file_tree_digest(pro_checkout):
        raise RuntimeError("X2 prospective wrapper changed checkout")
    _verify_seal(seal, expected_decisions=2)
    return {
        "schema": "RB-STAGE2-R7-G1-READINESS-X2-v1",
        "status": "PASS",
        "real_provider_calls": 0,
        "decision_count": seal["model_decision_count"],
        "checkpoint_count": seal["checkpoint_count"],
        "control_flow_equivalent": True,
        "checkout_equivalent": True,
        "manifest_hash": seal["run_manifest_hash"],
    }


async def preflight_x4(root: Path) -> dict:
    from stage2.native_v7.x4_mcp.runner import run_task as native_run

    task = _task_file(root, "T2")
    base_checkout = root / "base-checkout"
    pro_checkout = root / "pro-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", base_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", pro_checkout)

    base = await native_run(
        checkout=base_checkout,
        task_file=task,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=root / "base-mcp-observer",
        provider=ScriptedProvider(SCRIPT_TWO),
    )
    out = root / "prospective"
    seal = await run_capability_natural_A(
        system="X4",
        checkout=pro_checkout,
        task_file=task,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        out_root=out,
        provider=ScriptedProvider(SCRIPT_TWO),
    )
    prospective = json.loads((out / "natural_A_result.json").read_text())
    _compare(base, prospective, "X4")
    if file_tree_digest(base_checkout) != file_tree_digest(pro_checkout):
        raise RuntimeError("X4 prospective wrapper changed checkout")
    _verify_seal(seal, expected_decisions=2)
    return {
        "schema": "RB-STAGE2-R7-G1-READINESS-X4-v1",
        "status": "PASS",
        "real_provider_calls": 0,
        "decision_count": seal["model_decision_count"],
        "checkpoint_count": seal["checkpoint_count"],
        "control_flow_equivalent": True,
        "checkout_equivalent": True,
        "manifest_hash": seal["run_manifest_hash"],
    }


async def preflight_x5(root: Path) -> dict:
    from stage2.native_v7.x5_rag.runner import run_task as native_run

    task = _task_file(root, "T2")
    base_checkout = root / "base-checkout"
    pro_checkout = root / "pro-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", base_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", pro_checkout)
    base = await native_run(
        checkout=base_checkout,
        task_file=task,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=None,
        provider=ScriptedProvider(SCRIPT_TWO),
    )
    out = root / "prospective"
    seal = await run_capability_natural_A(
        system="X5",
        checkout=pro_checkout,
        task_file=task,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        out_root=out,
        provider=ScriptedProvider(SCRIPT_TWO),
    )
    prospective = json.loads((out / "natural_A_result.json").read_text())
    _compare(base, prospective, "X5")
    if file_tree_digest(base_checkout) != file_tree_digest(pro_checkout):
        raise RuntimeError("X5 prospective wrapper changed checkout")
    _verify_seal(seal, expected_decisions=2)
    return {
        "schema": "RB-STAGE2-R7-G1-READINESS-X5-v1",
        "status": "PASS",
        "real_provider_calls": 0,
        "decision_count": seal["model_decision_count"],
        "checkpoint_count": seal["checkpoint_count"],
        "control_flow_equivalent": True,
        "checkout_equivalent": True,
        "manifest_hash": seal["run_manifest_hash"],
    }


async def preflight_x6(root: Path, upstream_root: Path) -> dict:
    from stage2.native_v7.x6_memorybank.runner import run_task as native_run
    from stage2.native_v7.x6_memorybank.smoke import _build_tiny_embedding

    task = _task_file(root, "T2")
    base_checkout = root / "base-checkout"
    pro_checkout = root / "pro-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", base_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", pro_checkout)
    embedding = root / "tiny-embedding"
    hashes = _build_tiny_embedding(embedding)
    manifest = root / "embedding-manifest.json"
    manifest.write_text(json.dumps({
        "schema": "stage2-x6-embedding-manifest-v1",
        "purpose": "G1_NON_STUDY_READINESS_ONLY",
        "files_sha256": hashes,
    }, indent=2, sort_keys=True) + "\n")

    base = await native_run(
        checkout=base_checkout,
        task_file=task,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        observer_root=root / "base-observer",
        memory_root=root / "base-memory",
        upstream_root=upstream_root,
        embedding_model=embedding,
        embedding_manifest=manifest,
        provider=ScriptedProvider(SCRIPT_TWO),
    )
    out = root / "prospective"
    seal = await run_capability_natural_A(
        system="X6",
        checkout=pro_checkout,
        task_file=task,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        out_root=out,
        provider=ScriptedProvider(SCRIPT_TWO),
        x6_upstream=upstream_root,
        x6_embedding_model=embedding,
        x6_embedding_manifest=manifest,
    )
    prospective = json.loads((out / "natural_A_result.json").read_text())
    _compare(base, prospective, "X6")
    if file_tree_digest(base_checkout) != file_tree_digest(pro_checkout):
        raise RuntimeError("X6 prospective wrapper changed checkout")
    _verify_seal(seal, expected_decisions=2)
    return {
        "schema": "RB-STAGE2-R7-G1-READINESS-X6-v1",
        "status": "PASS",
        "real_provider_calls": 0,
        "decision_count": seal["model_decision_count"],
        "checkpoint_count": seal["checkpoint_count"],
        "control_flow_equivalent": True,
        "checkout_equivalent": True,
        "foreign_memory_mutated_by_repair": False,
        "manifest_hash": seal["run_manifest_hash"],
    }


async def preflight_x7(root: Path) -> dict:
    from stage2.native_v7.x7_longllmlingua.runner import run_task as native_run
    from stage2.native_v7.x7_longllmlingua.smoke import _build_tiny_checkpoint

    task = _task_file(root, "T3")
    base_checkout = root / "base-checkout"
    pro_checkout = root / "pro-checkout"
    shutil.copytree(STAGE2 / "fixtures/project", base_checkout)
    shutil.copytree(STAGE2 / "fixtures/project", pro_checkout)
    checkpoint = root / "tiny-checkpoint"
    hashes = _build_tiny_checkpoint(checkpoint)
    manifest = root / "checkpoint-manifest.json"
    manifest.write_text(json.dumps({
        "schema": "stage2-x7-checkpoint-manifest-v1",
        "purpose": "G1_NON_STUDY_READINESS_ONLY",
        "files_sha256": hashes,
    }, indent=2, sort_keys=True) + "\n")

    base = await native_run(
        checkout=base_checkout,
        task_file=task,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        checkpoint=checkpoint,
        checkpoint_manifest=manifest,
        observer_root=root / "base-observer",
        provider=ScriptedProvider(SCRIPT_ONE),
    )
    out = root / "prospective"
    seal = await run_capability_natural_A(
        system="X7",
        checkout=pro_checkout,
        task_file=task,
        roles_file=STAGE2 / "roles.json",
        subject_file=STAGE2 / "subject.json",
        out_root=out,
        provider=ScriptedProvider(SCRIPT_ONE),
        x7_checkpoint=checkpoint,
        x7_checkpoint_manifest=manifest,
    )
    prospective = json.loads((out / "natural_A_result.json").read_text())
    _compare(base, prospective, "X7")
    if file_tree_digest(base_checkout) != file_tree_digest(pro_checkout):
        raise RuntimeError("X7 prospective wrapper changed checkout")
    _verify_seal(seal, expected_decisions=1)
    return {
        "schema": "RB-STAGE2-R7-G1-READINESS-X7-v1",
        "status": "PASS",
        "real_provider_calls": 0,
        "decision_count": seal["model_decision_count"],
        "checkpoint_count": seal["checkpoint_count"],
        "control_flow_equivalent": True,
        "checkout_equivalent": True,
        "compressor_state_mutated_by_repair": False,
        "manifest_hash": seal["run_manifest_hash"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", choices=["X1","X2","X3","X4","X5","X6","X7"], required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--upstream-root")
    args = parser.parse_args()
    root = Path(args.out_root)
    root.mkdir(parents=True, exist_ok=False)
    if args.system == "X1":
        result = asyncio.run(preflight_x1(root))
    elif args.system == "X2":
        result = asyncio.run(preflight_x2(root))
    elif args.system == "X3":
        result = asyncio.run(preflight_x3(root))
    elif args.system == "X4":
        result = asyncio.run(preflight_x4(root))
    elif args.system == "X5":
        result = asyncio.run(preflight_x5(root))
    elif args.system == "X6":
        if not args.upstream_root:
            raise SystemExit("X6 readiness preflight requires --upstream-root")
        result = asyncio.run(preflight_x6(root, Path(args.upstream_root)))
    else:
        result = asyncio.run(preflight_x7(root))
    (root / "readiness_report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
