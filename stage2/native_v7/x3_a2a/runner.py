"""X3 runner: nine frozen Software Engineering roles as native A2A services.

The runner only starts role services/proxies and submits the initial user task to
release_lead. Inter-role delegation thereafter is performed by the role services
through the official A2A SDK and JSON-RPC task/artifact protocol. The baseline
CodingArena/RoleMailboxTransport are not used.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import socket
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STAGE2 = ROOT / "stage2"
ROLES = json.loads((STAGE2 / "roles.json").read_text())
DIRECTORY = {row["id"]: row for row in ROLES["agents"]}
TASKS = {row["id"]: row for row in json.loads((STAGE2 / "tasks.json").read_text())["tasks"]}
SUBJECT = json.loads((STAGE2 / "subject.json").read_text())


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _load_inputs(task_file, roles_file, subject_file):
    task = json.loads(Path(task_file).read_text())
    roles = json.loads(Path(roles_file).read_text())
    subject = json.loads(Path(subject_file).read_text())
    if task.get("id") not in TASKS or task != TASKS[task["id"]]:
        raise ValueError("task file differs from frozen T1-T3")
    if roles != ROLES:
        raise ValueError("roles file differs from frozen nine-role roster")
    if subject != SUBJECT:
        raise ValueError("subject file differs from frozen subject profile")
    return task, subject


async def _wait_for_cards(directory, processes):
    import httpx

    async with httpx.AsyncClient(timeout=2, trust_env=False) as client:
        for role, url in directory.items():
            for _ in range(120):
                if any(proc.poll() is not None for proc in processes):
                    failed = [proc.args for proc in processes if proc.poll() is not None]
                    raise RuntimeError(f"A2A service/proxy exited before readiness: {failed!r}")
                try:
                    response = await client.get(url.rstrip("/") + "/.well-known/agent-card.json")
                    if response.status_code == 200:
                        card = response.json()
                        if role not in card.get("skills", [{}])[0].get("id", ""):
                            # Skill ids are exact role ids; keep check tolerant of JSON layout.
                            if card.get("skills", [{}])[0].get("id") != role:
                                raise RuntimeError(f"A2A Agent Card role mismatch for {role}")
                        break
                except (httpx.HTTPError, json.JSONDecodeError):
                    pass
                await asyncio.sleep(0.1)
            else:
                raise TimeoutError(f"A2A Agent Card did not become ready for {role}")


async def _call_initial(url, payload):
    import httpx
    from a2a.client import ClientConfig, create_client
    from a2a.helpers import new_text_message
    from a2a.types import Role, SendMessageRequest

    timeout = SUBJECT["limits"]["transport_timeout_seconds"] * SUBJECT["limits"]["transport_max_retries"] + 10
    async with httpx.AsyncClient(timeout=timeout, trust_env=False) as http:
        client = await create_client(
            agent=url,
            client_config=ClientConfig(streaming=False, httpx_client=http),
        )
        request = SendMessageRequest(
            message=new_text_message(
                json.dumps(payload, ensure_ascii=False, sort_keys=True),
                role=Role.ROLE_USER,
            )
        )
        events = [event async for event in client.send_message(request)]
    if not events or not events[-1].HasField("task") or not events[-1].task.artifacts:
        raise RuntimeError("A2A release_lead service returned no final artifact")
    artifact = events[-1].task.artifacts[-1]
    text = "\n".join(part.text for part in artifact.parts if part.HasField("text"))
    result = json.loads(text)
    if result.get("schema") != "stage2-x3-role-result-v1":
        raise RuntimeError("A2A release_lead result has unexpected schema")
    return result


def _start_process(command, env, stderr_path):
    stream = Path(stderr_path).open("wb")
    process = subprocess.Popen(
        command,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=stream,
        cwd=ROOT,
    )
    return process, stream


def _stop_all(processes, streams):
    for proc in reversed(processes):
        if proc.poll() is None:
            proc.terminate()
    for proc in reversed(processes):
        if proc.poll() is None:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
    for stream in streams:
        stream.flush()
        os.fsync(stream.fileno())
        stream.close()


async def run_task(
    *,
    checkout,
    task_file,
    roles_file,
    subject_file,
    observer_root,
    mode="subject",
    script_file=None,
):
    task, subject = _load_inputs(task_file, roles_file, subject_file)
    if mode == "subject" and not os.environ.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("X3 subject mode requires the frozen DeepSeek credential")
    if mode == "scripted" and not script_file:
        raise ValueError("X3 scripted mode requires a script file")
    observer_root = Path(observer_root)
    observer_root.mkdir(parents=True, exist_ok=False)
    logs = observer_root / "process"
    logs.mkdir()
    wire = observer_root / "wire"
    wire.mkdir()

    backend_ports = {role: _free_port() for role in DIRECTORY}
    proxy_ports = {role: _free_port() for role in DIRECTORY}
    public_directory = {
        role: f"http://127.0.0.1:{proxy_ports[role]}" for role in DIRECTORY
    }
    directory_file = observer_root / "service-directory.json"
    directory_file.write_text(
        json.dumps(public_directory, indent=2, sort_keys=True) + "\n"
    )

    env_base = os.environ.copy()
    env_base["PYTHONPATH"] = str(ROOT)
    processes = []
    streams = []
    try:
        for role in DIRECTORY:
            service_cmd = [
                sys.executable,
                "-m",
                "stage2.native_v7.x3_a2a.service",
                "--role",
                role,
                "--checkout",
                str(Path(checkout).resolve()),
                "--directory-file",
                str(directory_file),
                "--public-url",
                public_directory[role],
                "--port",
                str(backend_ports[role]),
                "--mode",
                mode,
            ]
            if script_file:
                service_cmd += ["--script-file", str(Path(script_file).resolve())]
            proc, stream = _start_process(
                service_cmd,
                env_base,
                logs / f"{role}-service.stderr.bin",
            )
            processes.append(proc)
            streams.append(stream)

        for role in DIRECTORY:
            proxy_cmd = [
                sys.executable,
                "-m",
                "stage2.native_v7.x3_a2a.proxy",
                "--backend",
                f"http://127.0.0.1:{backend_ports[role]}",
                "--observer-root",
                str(wire / role),
                "--role",
                role,
                "--port",
                str(proxy_ports[role]),
            ]
            proc, stream = _start_process(
                proxy_cmd,
                env_base,
                logs / f"{role}-proxy.stderr.bin",
            )
            processes.append(proc)
            streams.append(stream)

        await _wait_for_cards(public_directory, processes)
        session_id = f"x3-{task['id']}-{uuid.uuid4()}"
        result = await _call_initial(
            public_directory[ROLES["entry_agent"]],
            {
                "schema": "stage2-x3-role-call-v1",
                "session_id": session_id,
                "task_id": task["id"],
                "sender": "USER",
                "target": ROLES["entry_agent"],
                "kind": "user_request",
                "content": task["user_request"],
                "remaining_turns": int(subject["limits"]["max_turns"]),
                "depth": 0,
            },
        )
        result["a2a_calls"] = 1 + int(result.get("protocol_calls", 0))
        result["service_count"] = len(DIRECTORY)
        result["session_id"] = session_id
        return result
    finally:
        _stop_all(processes, streams)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--roles-file", required=True)
    parser.add_argument("--subject-file", required=True)
    parser.add_argument("--observer-root", required=True)
    parser.add_argument("--mode", choices=["subject", "scripted"], default="subject")
    parser.add_argument("--script-file")
    args = parser.parse_args()
    result = asyncio.run(
        run_task(
            checkout=args.checkout,
            task_file=args.task_file,
            roles_file=args.roles_file,
            subject_file=args.subject_file,
            observer_root=args.observer_root,
            mode=args.mode,
            script_file=args.script_file,
        )
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
