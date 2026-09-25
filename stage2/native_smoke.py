"""Non-study native-boundary smoke for Stage-II probes.

This module never calls a subject/evaluator model. It exercises the installed
framework/protocol boundary with deterministic local payloads and writes either
a hash-linked native capture or an explicit ENGINEERING_BLOCKED receipt.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .evidence import NativeCapture, canonical_bytes
from .retrieval import retrieve

BASE = Path(__file__).resolve().parent


@dataclass
class AutoGenPing:
    content: str


@dataclass
class AutoGenPong:
    content: str


class EngineeringBlocked(RuntimeError):
    pass


def _native_bytes(value: Any) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    for name in ("SerializeToString", "model_dump_json", "json"):
        method = getattr(value, name, None)
        if method:
            data = method()
            return data if isinstance(data, bytes) else str(data).encode("utf-8")
    if isinstance(value, (dict, list, tuple)):
        return canonical_bytes(value)
    return repr(value).encode("utf-8")


def _package_version(*names: str) -> str:
    for name in names:
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    raise EngineeringBlocked("installed package version unavailable: " + ", ".join(names))


def _binding(lock: dict, probe: str) -> dict:
    row = next(x for x in lock["probes"] if x["id"] == probe)
    return {
        "probe": probe,
        "installed_version": None,
        "native_hook": row["native_hook"],
        "source_commit": row.get("source_commit"),
        "implementation_sha256": row.get("implementation_sha256"),
        "protocol_version": row.get("protocol_version"),
        "sdk_source": row.get("sdk_source"),
        "sdk_source_commit": row.get("sdk_source_commit"),
        "checkpoint": row.get("checkpoint"),
        "checkpoint_revision": row.get("checkpoint_revision"),
    }


async def _x1(binding: dict, cap: NativeCapture) -> None:
    from autogen_core import AgentId, RoutedAgent, SingleThreadedAgentRuntime, message_handler

    class Echo(RoutedAgent):
        def __init__(self) -> None:
            super().__init__("Stage-II deterministic native smoke")

        @message_handler
        async def handle(self, message: AutoGenPing, ctx: Any) -> AutoGenPong:
            return AutoGenPong(content="echo:" + message.content)

    binding["installed_version"] = _package_version("autogen-core")
    runtime = SingleThreadedAgentRuntime()
    await Echo.register(runtime, "stage2_echo", Echo)
    runtime.start()
    request = AutoGenPing("native-boundary")
    cap.capture(
        event_id="x1-send", operation="send_message", phase="emitted",
        native_locator="autogen_core.SingleThreadedAgentRuntime.send_message",
        hook_id=binding["native_hook"], raw=_native_bytes(asdict(request)),
        actor="release_lead", target="backend", carrier_id="autogen-message-1",
        source_id="stage2-smoke-source",
    )
    response = await runtime.send_message(request, AgentId("stage2_echo", "default"))
    cap.capture(
        event_id="x1-receive", operation="receive_message", phase="returned",
        native_locator="autogen_core.SingleThreadedAgentRuntime.send_message:return",
        hook_id=binding["native_hook"], raw=_native_bytes(asdict(response)),
        actor="backend", target="release_lead", carrier_id="autogen-message-2",
        source_id="autogen-message-1", parent_ids=("x1-send",), status="success",
    )
    await runtime.stop_when_idle()


def _x2(binding: dict, cap: NativeCapture) -> None:
    from metagpt.memory.memory import Memory
    from metagpt.schema import Message

    binding["installed_version"] = _package_version("metagpt")
    memory = Memory()
    message = Message(content="stage2 native shared-state smoke", role="Release Lead", cause_by="stage2-smoke", sent_from="release_lead")
    memory.add(message)
    cap.capture(
        event_id="x2-write", operation="shared_state", phase="executed",
        native_locator="metagpt.memory.memory.Memory.add",
        hook_id=binding["native_hook"], raw=_native_bytes(message),
        actor="release_lead", target="shared-memory", carrier_id="metagpt-memory-1",
        source_id="stage2-smoke-source", status="success",
    )
    observed = memory.get(k=1)
    if not observed or observed[-1].content != message.content:
        raise EngineeringBlocked("MetaGPT Memory.add/get did not preserve the native message")
    cap.capture(
        event_id="x2-read", operation="shared_state", phase="exposed",
        native_locator="metagpt.memory.memory.Memory.get",
        hook_id=binding["native_hook"], raw=_native_bytes(observed[-1]),
        actor="backend", target="shared-memory", carrier_id="metagpt-memory-1",
        source_id="stage2-smoke-source", parent_ids=("x2-write",), status="success",
    )


async def _x3(binding: dict, cap: NativeCapture) -> None:
    import httpx
    from uuid import uuid4
    from starlette.applications import Starlette
    from a2a.client.client import ClientConfig
    from a2a.client.client_factory import ClientFactory
    from a2a.server.agent_execution import AgentExecutor, RequestContext
    from a2a.server.events import EventQueue
    from a2a.server.events.in_memory_queue_manager import InMemoryQueueManager
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
    from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
    from a2a.types import AgentCapabilities, AgentCard, AgentInterface, Message, Part, Role, SendMessageRequest
    from a2a.utils import TransportProtocol

    binding["installed_version"] = _package_version("a2a-sdk")

    class Executor(AgentExecutor):
        async def execute(self, ctx: RequestContext, eq: EventQueue) -> None:
            await eq.enqueue_event(
                Message(
                    role=Role.ROLE_AGENT,
                    message_id=str(uuid4()),
                    parts=[Part(text="artifact:stage2")],
                    context_id=ctx.context_id,
                    task_id=ctx.task_id,
                )
            )

        async def cancel(self, ctx: RequestContext, eq: EventQueue) -> None:
            return None

    card = AgentCard(
        name="Stage-II Smoke",
        description="Local deterministic A2A native smoke",
        version="1",
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        supported_interfaces=[
            AgentInterface(protocol_binding=TransportProtocol.JSONRPC, url="http://stage2")
        ],
    )
    handler = DefaultRequestHandler(
        agent_executor=Executor(),
        task_store=InMemoryTaskStore(),
        agent_card=card,
        queue_manager=InMemoryQueueManager(),
    )
    app = Starlette(routes=[
        *create_agent_card_routes(agent_card=card, card_url="/card"),
        *create_jsonrpc_routes(request_handler=handler, rpc_url="/"),
    ])
    client = ClientFactory(
        config=ClientConfig(httpx_client=httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://stage2"
        ))
    ).create(card)
    message = Message(
        role=Role.ROLE_USER, message_id=f"msg-{uuid4()}",
        parts=[Part(text="inspect checkout")]
    )
    request = SendMessageRequest(message=message)
    cap.capture(
        event_id="x3-task", operation="remote_task", phase="emitted",
        native_locator="a2a.client.BaseClient.send_message",
        hook_id=binding["native_hook"], raw=_native_bytes(request),
        actor="release_lead", target="remote-agent", carrier_id="a2a-task-1",
        source_id="stage2-smoke-source",
    )
    try:
        events = [event async for event in client.send_message(request=request)]
        if not events:
            raise EngineeringBlocked("A2A returned no native event")
        cap.capture(
            event_id="x3-return", operation="artifact_return", phase="returned",
            native_locator="a2a.client.BaseClient.send_message:return",
            hook_id=binding["native_hook"], raw=_native_bytes(events[0]),
            actor="remote-agent", target="release_lead", carrier_id="a2a-return-1",
            source_id="a2a-task-1", parent_ids=("x3-task",), status="success",
        )
    finally:
        await client.close()


async def _x4(binding: dict, cap: NativeCapture) -> None:
    from mcp.client import Client
    from mcp.server.mcpserver import MCPServer

    binding["installed_version"] = _package_version("mcp")
    server = MCPServer("Stage-II Smoke")

    @server.tool()
    def inspect_path(path: str) -> dict[str, str]:
        return {"path": path, "state": "current"}

    @server.resource("repo://legacy")
    def legacy_resource() -> str:
        return "legacy compatibility path"

    async with Client(server) as client:
        tool_input = {"path": "checkout_app/server.py"}
        cap.capture(
            event_id="x4-tool", operation="tool_call", phase="emitted",
            native_locator="mcp.client.Client.call_tool",
            hook_id=binding["native_hook"], raw=_native_bytes(tool_input),
            actor="release_lead", target="mcp-server", carrier_id="mcp-tool-1",
            source_id="stage2-smoke-source",
        )
        tool_result = await client.call_tool("inspect_path", tool_input)
        cap.capture(
            event_id="x4-tool-return", operation="tool_call", phase="returned",
            native_locator="mcp.client.Client.call_tool:return",
            hook_id=binding["native_hook"], raw=_native_bytes(tool_result),
            actor="mcp-server", target="release_lead", carrier_id="mcp-tool-1",
            source_id="stage2-smoke-source", parent_ids=("x4-tool",), status="success",
        )
        resource_result = await client.read_resource("repo://legacy")
        cap.capture(
            event_id="x4-resource", operation="resource_read", phase="returned",
            native_locator="mcp.client.Client.read_resource",
            hook_id=binding["native_hook"], raw=_native_bytes(resource_result),
            actor="release_lead", target="mcp-server", carrier_id="mcp-resource-1",
            source_id="stage2-smoke-source", parent_ids=("x4-tool-return",), status="success",
        )


def _x5(binding: dict, cap: NativeCapture) -> None:
    binding["installed_version"] = "stage2-retrieval-v1"
    fixture = BASE / "fixtures" / "project"
    hits = retrieve(fixture, "legacy compatibility checkout server", limit=3)
    if not hits:
        raise EngineeringBlocked("canonical RAG boundary returned no hit")
    cap.capture(
        event_id="x5-retrieve", operation="retrieve", phase="returned",
        native_locator="stage2.retrieval.retrieve",
        hook_id=binding["native_hook"], raw=_native_bytes(hits),
        actor="release_lead", target="retrieval-index", carrier_id="rag-hit-set-1",
        source_id="stage2-smoke-source", status="success",
    )


def _x6(binding: dict, cap: NativeCapture) -> None:
    source = Path(os.environ.get("STAGE2_X6_SOURCE", ""))
    if not source.is_dir():
        raise EngineeringBlocked("MemoryBank source checkout is not mounted")
    write_path = source / "utils" / "memory_utils.py"
    retrieval_path = source / "memory_bank" / "memory_retrieval" / "local_doc_qa.py"
    if not write_path.is_file() or not retrieval_path.is_file():
        raise EngineeringBlocked("MemoryBank write/retrieval native source paths are absent")
    raise EngineeringBlocked(
        "MemoryBank commit is source-bound, but its native retrieval stack requires the "
        "legacy llama-index/provider dependency chain; no provider-free installed "
        "memory_write+memory_retrieve smoke is proven yet"
    )


def _x7(binding: dict, cap: NativeCapture) -> None:
    from llmlingua import PromptCompressor

    binding["installed_version"] = _package_version("llmlingua")
    if not binding.get("checkpoint") or not binding.get("checkpoint_revision"):
        raise EngineeringBlocked("LongLLMLingua checkpoint and immutable revision are required")
    prompt = (
        "The current checkout server is the active path. "
        "The old compatibility path should not silently remain authoritative."
    )
    cap.capture(
        event_id="x7-input", operation="compress", phase="emitted",
        native_locator="llmlingua.PromptCompressor.compress_prompt:input",
        hook_id=binding["native_hook"], raw=prompt.encode("utf-8"),
        actor="release_lead", target="prompt-compressor", carrier_id="llmlingua-prompt-1",
        source_id="stage2-smoke-source",
    )
    compressor = PromptCompressor(
        model_name=binding["checkpoint"],
        device_map="cpu",
        model_config={"revision": binding["checkpoint_revision"]},
    )
    result = compressor.compress_prompt(prompt, rate=0.7)
    cap.capture(
        event_id="x7-output", operation="compress", phase="returned",
        native_locator="llmlingua.PromptCompressor.compress_prompt:return",
        hook_id=binding["native_hook"], raw=_native_bytes(result),
        actor="prompt-compressor", target="release_lead", carrier_id="llmlingua-prompt-2",
        source_id="llmlingua-prompt-1", parent_ids=("x7-input",), status="success",
    )


async def _run_probe(probe: str, lock: dict, outdir: Path) -> dict:
    binding = _binding(lock, probe)
    root = outdir / probe
    root.mkdir(parents=True, exist_ok=True)
    status = {
        "schema": "stage2-native-smoke-status-v1",
        "probe": probe,
        "status": "ENGINEERING_BLOCKED",
        "binding": binding,
        "reason": None,
    }
    try:
        install_outcome = os.environ.get("STAGE2_INSTALL_OUTCOME", "success")
        if install_outcome != "success":
            raise EngineeringBlocked(f"native dependency installation failed: {install_outcome}")
        cap = NativeCapture(root, probe, f"smoke-{probe}", binding)
        if probe == "X1":
            await _x1(binding, cap)
        elif probe == "X2":
            _x2(binding, cap)
        elif probe == "X3":
            await _x3(binding, cap)
        elif probe == "X4":
            await _x4(binding, cap)
        elif probe == "X5":
            _x5(binding, cap)
        elif probe == "X6":
            _x6(binding, cap)
        elif probe == "X7":
            _x7(binding, cap)
        else:
            raise EngineeringBlocked("unknown probe")
        parent = cap.events[-1]["event_id"] if cap.events else None
        cap.capture(
            event_id=f"{probe.lower()}-termination", operation="termination", phase="returned",
            native_locator=f"stage2.native_smoke:{probe}",
            hook_id=binding["native_hook"], raw=b"native smoke completed",
            actor="stage2-engineering-gate", target=None, carrier_id=f"{probe}-termination",
            source_id="stage2-smoke-source",
            parent_ids=(parent,) if parent else (), status="success",
        )
        status["status"] = "NATIVE_SMOKE_PASS"
    except EngineeringBlocked as exc:
        status["reason"] = str(exc)
    except Exception as exc:
        status["reason"] = f"{type(exc).__name__}: {exc}"
    status["binding"] = binding
    (root / "status.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    return status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", required=True, choices=[f"X{i}" for i in range(1, 8)])
    parser.add_argument("--lock", default=str(BASE / "runtime_lock.json"))
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    lock = json.loads(Path(args.lock).read_text())
    status = asyncio.run(_run_probe(args.probe, lock, Path(args.outdir)))
    print(json.dumps(status, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
