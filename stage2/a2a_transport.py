"""A2A v1.0.0 SDK client to a distinct local HTTP agent service."""
import asyncio
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

from .coding_arena import DIRECTORY


class A2AProtocolTransport:
    probe = "X3"

    def __init__(self, capture):
        if capture.probe != self.probe:
            raise ValueError("A2A requires X3 capture")
        self.capture = capture
        self.serial = 0

    async def open(self, inbox):
        import httpx
        from a2a.client import ClientConfig, create_client

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        self.base_url = f"http://127.0.0.1:{port}"
        env = {"PATH": os.getenv("PATH", ""), "STAGE2_A2A_PORT": str(port),
               "PYTHONPATH": str(Path(__file__).resolve().parent.parent)}
        self.process = subprocess.Popen([sys.executable, "-m", "stage2.a2a_remote_service"],
                                        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        self.http = httpx.AsyncClient(timeout=8, trust_env=False)
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
