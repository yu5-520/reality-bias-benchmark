"""A2A v1.0.0 SDK client to a distinct local HTTP agent service."""
import asyncio
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

from .coding_arena import DIRECTORY
from .evidence import canonical_bytes, sha256
from .freeze import BASE


class A2AProtocolTransport:
    probe = "X3"

    def __init__(self, capture, *, remote_mode="echo", remote_actions=None):
        if capture.probe != self.probe:
            raise ValueError("A2A requires X3 capture")
        if remote_mode not in {"echo", "scripted", "subject"}:
            raise ValueError("unrecognized remote execution mode")
        if remote_mode == "scripted" and not remote_actions:
            raise ValueError("remote script required for non-study remote decisions")
        if remote_mode != "scripted" and remote_actions is not None:
            raise ValueError("remote actions are engineering-only")
        self.capture = capture
        self.serial = 0
        self.remote_mode = remote_mode
        self.remote_actions = remote_actions

    async def open(self, inbox):
        import httpx
        from a2a.client import ClientConfig, create_client

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        self.base_url = f"http://127.0.0.1:{port}"
        env = {"PATH": os.getenv("PATH", ""), "STAGE2_A2A_PORT": str(port),
               "STAGE2_A2A_REMOTE_MODE": self.remote_mode,
               "PYTHONPATH": str(Path(__file__).resolve().parent.parent)}
        if self.remote_mode == "scripted":
            env["STAGE2_A2A_SCRIPT"] = json.dumps(self.remote_actions, ensure_ascii=False)
        elif self.remote_mode == "subject":
            if not os.getenv("DEEPSEEK_API_KEY"):
                raise RuntimeError("A2A remote subject requires the frozen DeepSeek credential")
            env["DEEPSEEK_API_KEY"] = os.environ["DEEPSEEK_API_KEY"]
        self.process = subprocess.Popen([sys.executable, "-m", "stage2.a2a_remote_service"],
                                        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        limit = json.loads((BASE / "subject.json").read_text())["limits"]
        timeout = (limit["transport_timeout_seconds"] * limit["transport_max_retries"] + 10
                   if self.remote_mode == "subject" else 8)
        self.http = httpx.AsyncClient(timeout=timeout, trust_env=False)
        try:
            for _ in range(60):
                if self.process.poll() is not None:
                    raise RuntimeError(f"A2A remote exited before discovery: {self.process.stderr.read()[-1200:]!r}")
                try:
                    response = await self.http.get(f"{self.base_url}/.well-known/agent-card.json")
                    if response.status_code == 200:
                        self.card_bytes = response.content
                        break
                except httpx.ConnectError:
                    pass
                await asyncio.sleep(0.1)
            else:
                raise TimeoutError("A2A remote Agent Card did not become available")
            self.client = await create_client(agent=self.base_url,
                                              client_config=ClientConfig(streaming=False, httpx_client=self.http))
        except BaseException:
            await self.close()
            raise

    async def close(self):
        if hasattr(self, "http"):
            await self.http.aclose()
        if hasattr(self, "process") and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
        if hasattr(self, "process") and self.process.stderr:
            self.process.stderr.close()

    async def send(self, *, sender, target, content, cause, operation):
        if target not in DIRECTORY or sender not in DIRECTORY:
            raise ValueError("role outside frozen roster")
        from a2a.helpers import new_text_message
        from a2a.types import Role, SendMessageRequest

        self.serial += 1
        payload = {"sender": sender, "target": target, "content": content, "cause": cause,
                   "operation": operation}
        native_message = new_text_message(json.dumps(payload, ensure_ascii=False), role=Role.ROLE_USER)
        request = SendMessageRequest(message=native_message)
        carrier = f"a2a:{native_message.message_id}"
        sent = self.capture.capture(event_id=f"a2a-task-{self.serial}", operation="remote_task",
                                    phase="emitted", native_locator=f"a2a:message/send:{native_message.message_id}",
                                    hook_id="a2a.native.task_artifact",
                                    raw=request.SerializeToString(), actor=sender, target=target,
                                    source_id=cause, carrier_id=carrier, carrier_type="a2a-remote-task",
                                    parent_ids=(cause,))
        tasks = []
        async for item in self.client.send_message(request):
            tasks.append(item)
        if not tasks:
            raise RuntimeError("A2A returned no task")
        # SDK 1.0.0 yields a protobuf StreamResponse wrapping the final Task.
        wrapper = tasks[-1]
        final = wrapper.task if wrapper.HasField("task") else None
        if not hasattr(final, "artifacts") or not final.artifacts:
            raise RuntimeError(f"A2A remote did not return an artifact: {type(final)}")
        raw = wrapper.SerializeToString()
        artifact = self.capture.capture(event_id=f"a2a-artifact-{self.serial}", operation="artifact_return",
                                        phase="returned", native_locator=f"a2a:task:{final.id}:artifact",
                                        hook_id="a2a.native.task_artifact", raw=raw, actor=target,
                                        target=sender, source_id=cause, carrier_id=f"a2a-artifact:{final.id}",
                                        carrier_type="a2a-remote-artifact", parent_ids=(sent["event_id"],))
        returned = "\n".join(part.text for part in final.artifacts[-1].parts if hasattr(part, "text"))
        if json.loads(returned) != payload:
            raise RuntimeError("remote artifact changed the delegated message")
        received = self.capture.capture(event_id=f"a2a-recv-{self.serial}", operation="receive_message",
                                        phase="delivered", native_locator=f"a2a:task:{final.id}:read",
                                        hook_id="a2a.native.task_artifact", raw=returned.encode(),
                                        actor=target, target=sender, source_id=cause,
                                        carrier_id=artifact["carrier_id"], carrier_type="a2a-remote-artifact",
                                        parent_ids=(artifact["event_id"],))
        return received["event_id"]

    async def complete_remote(self, *, role, messages, turn, cause):
        """Get an action from the remote process and capture its input/output.

        The engineering script has a distinct model label and cannot satisfy
        the subject preflight. In subject mode the same service invokes the
        pinned provider inside the separate A2A process.
        """
        if self.remote_mode == "echo" or role not in DIRECTORY:
            raise ValueError("remote model execution was not bound for this role")
        from a2a.helpers import new_text_message
        from a2a.types import Role, SendMessageRequest

        self.serial += 1
        payload = {"operation": "model_inference", "target": role, "turn": turn, "messages": messages}
        native_message = new_text_message(json.dumps(payload, ensure_ascii=False), role=Role.ROLE_USER)
        request = SendMessageRequest(message=native_message)
        sent = self.capture.capture(
            event_id=f"a2a-model-task-{self.serial}", operation="remote_task", phase="emitted",
            native_locator=f"a2a:message/send:{native_message.message_id}",
            hook_id="a2a.native.task_artifact", raw=request.SerializeToString(),
            actor="release_lead", target=role, source_id=cause,
            carrier_id=f"a2a:{native_message.message_id}", carrier_type="a2a-remote-model-task",
            parent_ids=(cause,))
        tasks = [item async for item in self.client.send_message(request)]
        if not tasks or not tasks[-1].HasField("task") or not tasks[-1].task.artifacts:
            raise RuntimeError("A2A remote returned no model artifact")
        task = tasks[-1].task
        returned = "\n".join(part.text for part in task.artifacts[-1].parts if part.HasField("text"))
        payload = json.loads(returned)
        if (payload.get("schema") != "stage2-a2a-remote-model-artifact-v1"
                or payload.get("remote_mode") != self.remote_mode or payload.get("role") != role
                or payload.get("request_sha256") != sha256(canonical_bytes(messages))):
            raise RuntimeError("A2A remote model artifact failed source/role/mode validation")
        response = payload["response"]
        if not isinstance(response, dict) or not isinstance(response.get("content"), str):
            raise RuntimeError("A2A remote provider response is incomplete")
        remote_input = self.capture.capture(
            event_id=f"a2a-remote-input-{self.serial}", operation="model_input", phase="exposed",
            native_locator=f"a2a:task:{task.id}:remote-model-input", hook_id="a2a.native.remote_model",
            raw=canonical_bytes(messages), actor=role, source_id=cause,
            carrier_id=f"a2a-model-input:{task.id}", parent_ids=(sent["event_id"],))
        remote_output = self.capture.capture(
            event_id=f"a2a-remote-output-{self.serial}", operation="model_output", phase="returned",
            native_locator=f"a2a:task:{task.id}:remote-model-output", hook_id="a2a.native.remote_model",
            raw=canonical_bytes(response), actor=role, source_id=cause,
            carrier_id=f"a2a-model-output:{task.id}", parent_ids=(remote_input["event_id"],))
        artifact = self.capture.capture(
            event_id=f"a2a-model-artifact-{self.serial}", operation="artifact_return", phase="returned",
            native_locator=f"a2a:task:{task.id}:remote-model-artifact",
            hook_id="a2a.native.task_artifact", raw=tasks[-1].SerializeToString(),
            actor=role, target="release_lead", source_id=cause,
            carrier_id=f"a2a-artifact:{task.id}", parent_ids=(remote_output["event_id"],))
        return response, artifact["event_id"]
