"""One-shot Stage-II subject collection after a separate subject-readiness gate.

This entry point never runs an engineering script or an automatic evaluator.
Any occupied cell remains occupied after an error; adjudication can distinguish
an infrastructure failure from a natural censored trajectory using the seal.
"""
import argparse
import asyncio
import importlib.metadata
import json
import os
import subprocess
from pathlib import Path

from arena.providers import DeepSeekArenaProvider

from .coding_arena import CodingArena
from .evidence import NativeCapture, check_capture
from .freeze import BASE, ROOT, artifact, hash_file
from .preflight import blockers
from .target_coding_smoke import frozen_target
from .transports import AutoGenTransport, RoleMailboxTransport
from .workspace import new_workspace

SUPPORTED = {"X1", "X3", "X4", "X5"}
PACKAGES = {"X1": "autogen-core", "X3": "a2a-sdk", "X4": "mcp"}


def validate_request(*, probe, task, manifest, captures, upstream):
    cell = f"{probe}-{task}"
    if cell not in {row["cell"] for row in artifact()["cells"]}:
        raise ValueError("cell is not in the frozen 7 × 3 matrix")
    if probe not in SUPPORTED:
        raise ValueError(f"{probe}: exact architecture remains engineering-blocked")
    if (BASE / "matrix.json").read_text() != json.dumps(artifact(), ensure_ascii=False,
                                                        indent=2, sort_keys=True) + "\n":
        raise ValueError("prospective matrix or frozen code hashes differ")
    code_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    runtime = json.loads(Path(manifest).read_text())
    if runtime.get("code_commit") != code_commit:
        raise ValueError("subject readiness was not established on this exact code commit")
    problems = blockers(manifest, captures, probe)
    if problems:
        raise ValueError("subject readiness gate is closed: " + "; ".join(problems))
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("frozen DeepSeek subject credential is unavailable")
    target = frozen_target(probe, upstream)
    bound = runtime["probes"][probe]
    installed = importlib.metadata.version(PACKAGES[probe]) if probe in PACKAGES else "in-repo"
    if installed != bound["installed_version"]:
        raise ValueError("installed SDK differs from the subject-ready implementation")
    frozen = json.loads((BASE / "subject.json").read_text())
    config = json.loads((ROOT / frozen["source_config"]).read_text())
    if (config["provider"] != frozen["provider"] or config["model_alias"] != frozen["model_alias"]
            or config["expected_model_version"] != frozen["expected_model_version"]
            or config["subject"] != frozen["subject"]
            or config["transport"]["timeout_seconds"] != frozen["limits"]["transport_timeout_seconds"]
            or config["transport"]["max_retries"] != frozen["limits"]["transport_max_retries"]):
        raise ValueError("live provider differs from the frozen subject profile")
    binding = {"probe": probe, "code_commit": code_commit,
               "source_commit": target.get("source_commit") or target.get("protocol_commit") or code_commit,
               "sdk_commit": target.get("sdk_commit"), "native_hook": target["hook_id"],
               "protocol_version": target.get("protocol_version"),
               "implementation_sha256": target.get("implementation_sha256"),
               "installed_version": installed, "provider": frozen["provider"],
               "expected_model_version": frozen["expected_model_version"]}
    return cell, binding, config


async def collect(*, probe, task, manifest, captures, out_root, upstream=None):
    cell, binding, config = validate_request(probe=probe, task=task, manifest=manifest,
                                              captures=captures, upstream=upstream)
    destination = Path(out_root) / cell
    # Exclusive mkdir reserves the cell before any provider call. Never retry an
    # occupied cell, even if the first attempt later fails or is censored.
    destination.mkdir(parents=True, exist_ok=False)
    result, error = None, None
    try:
        capture = NativeCapture(destination / "evidence", probe, f"STAGE2-NATURAL-{cell}", binding)
        checkout = new_workspace(destination / "checkout")
        provider = DeepSeekArenaProvider(config)
        transport = AutoGenTransport(capture) if probe == "X1" else RoleMailboxTransport(capture)
        workspace = context = None
        if probe == "X3":
            from .a2a_transport import A2AProtocolTransport
            transport = A2AProtocolTransport(capture, remote_mode="subject")
        elif probe == "X4":
            from .mcp_workspace import MCPWorkspace
            workspace = MCPWorkspace(checkout, capture)
        elif probe == "X5":
            from .rag_context import RAGContext
            context = RAGContext(capture)
        arena = CodingArena(task_id=task, checkout=checkout, capture=capture, transport=transport,
                            provider=provider, workspace=workspace, context_adapter=context)
        result = await arena.run()
    except BaseException as exc:
        error = type(exc).__name__
        raise
    finally:
        evidence = destination / "evidence"
        count, integrity_error = 0, None
        outputs = []
        if (evidence / "events.jsonl").exists():
            try:
                count = check_capture(evidence)
                rows = [json.loads(line) for line in (evidence / "events.jsonl").read_text().splitlines()]
                outputs = [json.loads((evidence / row["raw_path"]).read_text())
                           for row in rows if row["operation"] == "model_output"]
            except (OSError, ValueError, KeyError, AssertionError) as exc:
                integrity_error = type(exc).__name__
        subject_identity_ok = bool(outputs) and all(
            response.get("model") == binding["expected_model_version"]
            and isinstance(response.get("provider_response"), dict)
            and response["provider_response"].get("model") == binding["expected_model_version"]
            for response in outputs if isinstance(response, dict)) and all(
                isinstance(response, dict) for response in outputs)
        seal = {"schema": "stage2-natural-cell-seal-v1", "cell": cell,
                "probe": probe, "task": task, "code_commit": binding["code_commit"],
                "binding": binding,
                "status": ("RECORDED_PENDING_R6" if result is not None and not integrity_error
                           and subject_identity_ok
                           else "FAILED_ATTEMPT_PRESERVED"),
                "stop_reason": result["stop_reason"] if result else None,
                "error_type": error, "integrity_error": integrity_error, "events": count,
                "subject_identity_ok": subject_identity_ok, "model_outputs": len(outputs),
                "sha256": {str(path.relative_to(destination)): hash_file(path)
                           for path in sorted(destination.rglob("*")) if path.is_file()}}
        path = destination / "seal.json"
        with path.open("x") as stream:
            json.dump(seal, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        fd = os.open(destination, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    return seal


def verify_seal(destination):
    destination = Path(destination)
    seal = json.loads((destination / "seal.json").read_text())
    observed = {str(path.relative_to(destination)): hash_file(path)
                for path in destination.rglob("*") if path.is_file() and path != destination / "seal.json"}
    if observed != seal["sha256"]:
        raise ValueError("sealed natural evidence or checkout was altered")
    if seal["integrity_error"]:
        raise ValueError("original native event chain failed the integrity check")
    if seal["events"]:
        if check_capture(destination / "evidence") != seal["events"]:
            raise ValueError("sealed event chain was altered")
    return seal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", required=True, choices=[f"X{i}" for i in range(1, 8)])
    parser.add_argument("--task", required=True, choices=[f"T{i}" for i in range(1, 4)])
    parser.add_argument("--runtime-manifest", required=True)
    parser.add_argument("--captures-root", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--upstream")
    args = parser.parse_args()
    seal = asyncio.run(collect(probe=args.probe, task=args.task, manifest=args.runtime_manifest,
                               captures=args.captures_root, out_root=args.out_root, upstream=args.upstream))
    print(json.dumps({key: seal[key] for key in ("cell", "status", "stop_reason", "events")}, sort_keys=True))


if __name__ == "__main__":
    main()
