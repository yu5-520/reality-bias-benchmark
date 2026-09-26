from __future__ import annotations

import argparse
import asyncio
import json
import shutil
from pathlib import Path

from arena.providers import ScriptedProvider
from stage2.r7_prospective_v1.replication_contract import resolve_decision_horizon

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "stage2"
SUBJECT = json.loads((STAGE2 / "subject.json").read_text())
HORIZON = 64


def _task_file(root: Path, task_id: str = "T2") -> Path:
    task = next(row for row in json.loads((STAGE2 / "tasks.json").read_text())["tasks"] if row["id"] == task_id)
    path = root / f"{task_id}.json"
    path.write_text(json.dumps(task, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return path


def _invalid_script(n: int):
    return [{"not_actions": [{"index": i}]} for i in range(n)]


def _verify_channel_split(out: Path):
    audit = json.loads((out / "audit_raw_bundle_manifest.json").read_text())
    monitor = json.loads((out / "monitor_runtime_bundle_manifest.json").read_text())
    audit_paths = {row["path"] for row in audit["entries"]}
    monitor_paths = {row["path"] for row in monitor["entries"]}
    if audit_paths & monitor_paths:
        raise RuntimeError(f"audit/monitor evidence channels overlap: {sorted(audit_paths & monitor_paths)!r}")
    forbidden = ("monitor_evidence", "monitor_candidates", "repair_packages", "runtime_bridge", "native_event_index", "wire_index")
    if any(any(token in path for token in forbidden) for path in audit_paths):
        raise RuntimeError("audit raw bundle contains monitor-derived artifact")
    if audit["monitor_runtime_bundle_readable_before_reference_seal"] is not False:
        raise RuntimeError("audit bundle blindness is not frozen")
    if monitor["posthoc_semantic_audit_input"] is not False:
        raise RuntimeError("monitor bundle admits post-hoc audit input")
    return {
        "audit_entries": len(audit_paths),
        "monitor_entries": len(monitor_paths),
        "audit_manifest_sha256": audit["manifest_sha256"],
        "monitor_manifest_sha256": monitor["manifest_sha256"],
    }


def _verify_seal(out: Path, *, expected_decisions: int | None = None):
    seal = json.loads((out / "seal.json").read_text())
    if seal["group_id"] != "G2":
        raise RuntimeError("preflight must exercise the G2-G5 group path")
    if seal["repair_actions_during_A"] != 0:
        raise RuntimeError("natural A preflight contains repair actions")
    if seal["semantic_audit_state"] != "LOCKED_UNTIL_ALL_84_NATURAL_A_AND_REFERENCE_AUDIT_GATE":
        raise RuntimeError("semantic audit opened before the 84-A gate")
    if seal["model_decision_count"] > HORIZON:
        raise RuntimeError("runner exceeded 64 logical decisions")
    if expected_decisions is not None and seal["model_decision_count"] != expected_decisions:
        raise RuntimeError(f"expected {expected_decisions} decisions, observed {seal['model_decision_count']}")
    return seal


async def preflight_x1(root: Path):
    from autogen_core import FunctionCall
    from autogen_core.models import CreateResult, RequestUsage
    from autogen_ext.models.replay import ReplayChatCompletionClient
    from stage2.r7_prospective_v1.x1_runner import run_x1_natural_A

    task = _task_file(root)
    checkout = root / "checkout"
    shutil.copytree(STAGE2 / "fixtures/project", checkout)
    responses = []
    for i in range(HORIZON):
        target = "frontend" if i % 2 == 0 else "release_lead"
        responses.append(CreateResult(
            finish_reason="function_calls",
            content=[FunctionCall(id=f"handoff-{i}", name=f"transfer_to_{target}", arguments="{}")],
            usage=RequestUsage(prompt_tokens=1, completion_tokens=1),
            cached=True,
        ))
    client = ReplayChatCompletionClient(responses, model_info={
        "vision": False, "function_calling": True, "json_output": True,
        "family": "unknown", "structured_output": False,
    })
    out = root / "out"
    await run_x1_natural_A(
        checkout=checkout, task_file=task, roles_file=STAGE2/"roles.json",
        subject_file=STAGE2/"subject.json", out_root=out, model_client=client,
        group_id="G2", decision_horizon=HORIZON,
    )
    seal = _verify_seal(out, expected_decisions=HORIZON)
    channels = _verify_channel_split(out)
    return {"system":"X1","status":"PASS","decision_count":seal["model_decision_count"],**channels}


async def preflight_x2(root: Path):
    from stage2.r7_prospective_v1.x2_runner import run_x2_natural_A
    task = _task_file(root)
    checkout = root / "checkout"
    shutil.copytree(STAGE2 / "fixtures/project", checkout)
    out = root / "out"
    await run_x2_natural_A(
        checkout=checkout, task_file=task, roles_file=STAGE2/"roles.json",
        subject_file=STAGE2/"subject.json", out_root=out,
        provider=ScriptedProvider(_invalid_script(HORIZON)),
        group_id="G2", decision_horizon=HORIZON,
    )
    seal = _verify_seal(out, expected_decisions=HORIZON)
    channels = _verify_channel_split(out)
    return {"system":"X2","status":"PASS","decision_count":seal["model_decision_count"],**channels}


async def preflight_x3(root: Path):
    from stage2.native_v7.x3_a2a.runner import ROLES
    from stage2.r7_prospective_v1.x3_runner import run_x3_natural_A
    task = _task_file(root)
    checkout = root / "checkout"
    shutil.copytree(STAGE2 / "fixtures/project", checkout)
    scripts = {}
    for role in [row["id"] for row in ROLES["agents"]]:
        scripts[role] = _invalid_script(HORIZON if role == ROLES["entry_agent"] else 1)
    script_file = root / "x3-script.json"
    script_file.write_text(json.dumps(scripts, indent=2, sort_keys=True) + "\n")
    out = root / "out"
    await run_x3_natural_A(
        checkout=checkout, task_file=task, roles_file=STAGE2/"roles.json",
        subject_file=STAGE2/"subject.json", out_root=out,
        mode="scripted", script_file=script_file,
        group_id="G2", decision_horizon=HORIZON,
    )
    seal = _verify_seal(out, expected_decisions=HORIZON)
    if seal["a2a_protocol_modified"] is not False:
        raise RuntimeError("A2A protocol changed under horizon extension")
    channels = _verify_channel_split(out)
    return {"system":"X3","status":"PASS","decision_count":seal["model_decision_count"],**channels}


async def preflight_capability(root: Path, system: str, *, upstream_root: Path | None = None):
    from stage2.r7_prospective_v1.capability_runner import run_capability_natural_A
    task_id = "T3" if system == "X7" else "T2"
    task = _task_file(root, task_id)
    checkout = root / "checkout"
    shutil.copytree(STAGE2 / "fixtures/project", checkout)
    kwargs = {}
    if system == "X6":
        from stage2.native_v7.x6_memorybank.smoke import _build_tiny_embedding
        embedding = root / "tiny-embedding"
        hashes = _build_tiny_embedding(embedding)
        manifest = root / "embedding-manifest.json"
        manifest.write_text(json.dumps({"schema":"stage2-x6-embedding-manifest-v1","purpose":"G2_G5_HORIZON_PREFLIGHT_ONLY","files_sha256":hashes},indent=2,sort_keys=True)+"\n")
        kwargs.update(x6_upstream=upstream_root,x6_embedding_model=embedding,x6_embedding_manifest=manifest)
    if system == "X7":
        from stage2.native_v7.x7_longllmlingua.smoke import _build_tiny_checkpoint
        checkpoint = root / "tiny-checkpoint"
        hashes = _build_tiny_checkpoint(checkpoint)
        manifest = root / "checkpoint-manifest.json"
        manifest.write_text(json.dumps({"schema":"stage2-x7-checkpoint-manifest-v1","purpose":"G2_G5_HORIZON_PREFLIGHT_ONLY","files_sha256":hashes},indent=2,sort_keys=True)+"\n")
        kwargs.update(x7_checkpoint=checkpoint,x7_checkpoint_manifest=manifest)

    # X4 proves the shared host can consume the full 64-decision budget.
    # X5-X7 use the same host and run a short native capability smoke at horizon=64.
    script = _invalid_script(HORIZON) if system == "X4" else [{"actions":[{"type":"finalize","answer":"horizon preflight complete"}]}]
    out = root / "out"
    await run_capability_natural_A(
        system=system, checkout=checkout, task_file=task, roles_file=STAGE2/"roles.json",
        subject_file=STAGE2/"subject.json", out_root=out, provider=ScriptedProvider(script),
        group_id="G2", decision_horizon=HORIZON, **kwargs,
    )
    expected = HORIZON if system == "X4" else 1
    seal = _verify_seal(out, expected_decisions=expected)
    channels = _verify_channel_split(out)
    return {"system":system,"status":"PASS","decision_count":seal["model_decision_count"],"shared_host_horizon_proof":system=="X4",**channels}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", choices=["X1","X2","X3","X4","X5","X6","X7"], required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--upstream-root")
    args = parser.parse_args()

    if resolve_decision_horizon(group_id="G2", subject=SUBJECT) != HORIZON:
        raise SystemExit("G2 horizon did not resolve to 64")
    try:
        resolve_decision_horizon(group_id="G2", subject=SUBJECT, requested=65)
    except ValueError:
        pass
    else:
        raise SystemExit("65-decision request did not fail closed")

    root = Path(args.out_root)
    root.mkdir(parents=True, exist_ok=False)
    if args.system == "X1":
        result = asyncio.run(preflight_x1(root))
    elif args.system == "X2":
        result = asyncio.run(preflight_x2(root))
    elif args.system == "X3":
        result = asyncio.run(preflight_x3(root))
    elif args.system in {"X4","X5","X7"}:
        result = asyncio.run(preflight_capability(root, args.system))
    else:
        if not args.upstream_root:
            raise SystemExit("X6 preflight requires --upstream-root")
        result = asyncio.run(preflight_capability(root, "X6", upstream_root=Path(args.upstream_root)))

    report = {
        "schema":"stage2-g2-g5-horizon-channel-preflight-v1",
        "status":"PASS",
        "real_subject_provider_calls":0,
        "logical_decision_ceiling":HORIZON,
        "result":result,
    }
    (root/"preflight_report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,sort_keys=True))


if __name__ == "__main__":
    main()
