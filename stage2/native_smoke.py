"""Non-study native-boundary smoke probes for Stage-II.

These exercises use each pinned implementation's real runtime/API surface and
write NativeCapture evidence. They never call the subject model and never
adjudicate C/P/R.
"""
import argparse
import asyncio
import importlib.metadata
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .evidence import NativeCapture, check_capture

BASE = Path(__file__).resolve().parent


def _targets():
    return json.loads((BASE / "runtime_bindings.json").read_text())["probes"]


def _bytes(value):
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    if hasattr(value, "SerializeToString"):
        return value.SerializeToString()
    if hasattr(value, "model_dump_json"):
        return value.model_dump_json().encode("utf-8")
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")


def _binding(probe, *, code_commit):
    p = _targets()[probe]
    source_commit = p.get("source_commit") or p.get("protocol_commit") or code_commit
    bind = {
        "probe": probe,
        "source_commit": source_commit,
        "native_hook": p["hook_id"],
        "code_commit": code_commit,
    }
    for key in ("protocol_version", "sdk_commit", "implementation_sha256"):
        if p.get(key):
            bind[key] = p[key]
    return bind


def _finish(cap, hook, parent):
    cap.capture(
        event_id="termination",
        operation="termination",
        phase="returned",
        native_locator="stage2.native_smoke:completed",
        hook_id=hook,
        raw=b"native smoke completed",
        actor="smoke-runner",
        carrier_id="smoke:termination",
        source_id="smoke:runtime",
        parent_ids=(parent,),
        status="success",
    )


async def smoke_x1(root, code_commit):
    from autogen_core import AgentId, MessageContext, RoutedAgent, SingleThreadedAgentRuntime, message_handler

    cfg = _targets()["X1"]
    bind = _binding("X1", code_commit=code_commit)
    cap = NativeCapture(root, "X1", "X1-native-smoke", bind)

    @dataclass
    class SmokeMessage:
        content: str

    class EchoAgent(RoutedAgent):
        def __init__(self):
            super().__init__("Stage-II native smoke echo")

        @message_handler
        async def handle(self, message: SmokeMessage, ctx: MessageContext) -> SmokeMessage:
            cap.capture(
                event_id="receive",
                operation="receive_message",
                phase="delivered",
                native_locator="EchoAgent.handle:message",
                hook_id=cfg["hook_id"],
                raw=_bytes(asdict(message)),
                actor=str(self.id),
                carrier_id="autogen:message:request",
                source_id="smoke:user",
                parent_ids=("send",),
                status="success",
            )
            reply = SmokeMessage("ack:" + message.content)
            cap.capture(
                event_id="reply",
                operation="send_message",
                phase="returned",
                native_locator="EchoAgent.handle:return",
                hook_id=cfg["hook_id"],
                raw=_bytes(asdict(reply)),
                actor=str(self.id),
                target="smoke:user",
                carrier_id="autogen:message:reply",
                source_id="autogen:message:request",
                parent_ids=("receive",),
                status="success",
            )
            return reply

    runtime = SingleThreadedAgentRuntime()
    await EchoAgent.register(runtime, "stage2_echo", EchoAgent)
    runtime.start()
    msg = SmokeMessage("checkout-native-smoke")
    cap.capture(
        event_id="send",
        operation="send_message",
        phase="emitted",
        native_locator="SingleThreadedAgentRuntime.send_message:request",
        hook_id=cfg["hook_id"],
        raw=_bytes(asdict(msg)),
        actor="smoke:user",
        target="stage2_echo/default",
        carrier_id="autogen:message:request",
        source_id="smoke:user",
        status="success",
    )
    result = await runtime.send_message(msg, AgentId("stage2_echo", "default"))
    await runtime.stop()
    if not isinstance(result, SmokeMessage) or result.content != "ack:checkout-native-smoke":
        raise RuntimeError("AutoGen native message roundtrip failed")
    _finish(cap, cfg["hook_id"], "reply")


async def smoke_x3(root, code_commit):
    import httpx
    from a2a.client.transports.rest import RestTransport
    from a2a.helpers.proto_helpers import new_text_message
    from a2a.types import AgentCapabilities, AgentCard, AgentInterface, SendMessageRequest

    cfg = _targets()["X3"]
    bind = _binding("X3", code_commit=code_commit)
    cap = NativeCapture(root, "X3", "X3-native-smoke", bind)
    wire = {}

    response_body = {
        "message": {
            "messageId": "a2a-smoke-response",
            "role": "ROLE_AGENT",
            "parts": [{"text": "checkout-a2a-ack"}],
        }
    }

    async def handler(request):
        wire["request"] = request.content
        raw = json.dumps(response_body, separators=(",", ":")).encode("utf-8")
        wire["response"] = raw
        return httpx.Response(200, content=raw, headers={"content-type": "application/json"}, request=request)

    card = AgentCard(
        name="Stage-II Smoke Agent",
        description="Non-study A2A transport smoke",
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(
                url="http://stage2.invalid/a2a",
                protocol_binding="HTTP+JSON",
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        transport = RestTransport(http, card, "http://stage2.invalid/a2a")
        req = SendMessageRequest(message=new_text_message(text="checkout-a2a-smoke"))
        response = await transport.send_message(request=req)

    if not response.HasField("message") or response.message.parts[0].text != "checkout-a2a-ack":
        raise RuntimeError("A2A native REST roundtrip failed")

    cap.capture(
        event_id="remote-task",
        operation="remote_task",
        phase="emitted",
        native_locator="RestTransport.send_message:/message:send",
        hook_id=cfg["hook_id"],
        raw=wire["request"],
        actor="a2a:client",
        target="a2a:remote-agent",
        carrier_id="a2a:http:request",
        source_id="smoke:user",
        status="success",
    )
    cap.capture(
        event_id="artifact-return",
        operation="artifact_return",
        phase="returned",
        native_locator="RestTransport.send_message:SendMessageResponse",
        hook_id=cfg["hook_id"],
        raw=wire["response"],
        actor="a2a:remote-agent",
        target="a2a:client",
        carrier_id="a2a:http:response",
        source_id="a2a:http:request",
        parent_ids=("remote-task",),
        status="success",
    )
    _finish(cap, cfg["hook_id"], "artifact-return")


async def smoke_x4(root, code_commit):
    from mcp import Client
    from mcp.server import MCPServer

    cfg = _targets()["X4"]
    bind = _binding("X4", code_commit=code_commit)
    cap = NativeCapture(root, "X4", "X4-native-smoke", bind)
    server = MCPServer("Stage-II Native Smoke")

    @server.tool()
    def inspect_checkout(path: str) -> str:
        """Return a deterministic non-study checkout marker."""
        return "current:" + path

    request = {"tool": "inspect_checkout", "arguments": {"path": "checkout_app/server.py"}}
    cap.capture(
        event_id="tool-call",
        operation="tool_call",
        phase="emitted",
        native_locator="mcp.Client.call_tool:inspect_checkout",
        hook_id=cfg["hook_id"],
        raw=_bytes(request),
        actor="mcp:client",
        target="mcp:server",
        carrier_id="mcp:tool-call",
        source_id="smoke:user",
        status="success",
    )
    async with Client(server) as client:
        result = await client.call_tool("inspect_checkout", {"path": "checkout_app/server.py"})
        protocol = str(client.protocol_version)
    raw_result = _bytes(result)
    if b"current:" not in raw_result:
        raise RuntimeError("MCP native tool result missing")
    cap.capture(
        event_id="tool-result",
        operation="receive_message",
        phase="returned",
        native_locator=f"mcp.Client.call_tool:return;protocol={protocol}",
        hook_id=cfg["hook_id"],
        raw=raw_result,
        actor="mcp:server",
        target="mcp:client",
        carrier_id="mcp:tool-result",
        source_id="mcp:tool-call",
        parent_ids=("tool-call",),
        status="success",
    )
    _finish(cap, cfg["hook_id"], "tool-result")


def smoke_x5(root, code_commit):
    from .retrieval import retrieve

    cfg = _targets()["X5"]
    bind = _binding("X5", code_commit=code_commit)
    cap = NativeCapture(root, "X5", "X5-native-smoke", bind)
    query = "legacy compatibility current checkout"
    cap.capture(
        event_id="retrieve-request",
        operation="retrieve",
        phase="emitted",
        native_locator="stage2.retrieval.retrieve:query",
        hook_id=cfg["hook_id"],
        raw=query.encode("utf-8"),
        actor="rag:client",
        carrier_id="rag:query",
        source_id="smoke:user",
        status="success",
    )
    hits = retrieve(BASE / "fixtures/project", query, limit=3)
    if not hits:
        raise RuntimeError("RAG native retrieval returned no hits")
    cap.capture(
        event_id="retrieve-result",
        operation="receive_message",
        phase="returned",
        native_locator="stage2.retrieval.retrieve:hits",
        hook_id=cfg["hook_id"],
        raw=_bytes(hits),
        actor="rag:retriever",
        target="rag:client",
        carrier_id="rag:hits",
        source_id="rag:query",
        parent_ids=("retrieve-request",),
        status="success",
    )
    _finish(cap, cfg["hook_id"], "retrieve-result")


def smoke_x7(root, code_commit):
    from llmlingua import PromptCompressor

    cfg = _targets()["X7"]
    bind = _binding("X7", code_commit=code_commit)
    cap = NativeCapture(root, "X7", "X7-native-smoke", bind)
    model = "microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank"
    context = [
        "The checkout service uses the current checkout_app server route. "
        "The old compatibility route is retained only as historical context and should not drive execution."
    ]
    cap.capture(
        event_id="compress-input",
        operation="compress",
        phase="emitted",
        native_locator="PromptCompressor.compress_prompt:input",
        hook_id=cfg["hook_id"],
        raw=_bytes({"model": model, "context": context, "rate": 0.6}),
        actor="llmlingua:compressor",
        carrier_id="llmlingua:raw-context",
        source_id="smoke:user",
        status="success",
    )
    compressor = PromptCompressor(model_name=model, device_map="cpu", use_llmlingua2=True)
    result = compressor.compress_prompt(context, rate=0.6)
    compressed = result.get("compressed_prompt")
    if not compressed:
        raise RuntimeError("LongLLMLingua native compression returned empty output")
    cap.capture(
        event_id="compress-output",
        operation="compress",
        phase="returned",
        native_locator="PromptCompressor.compress_prompt:return",
        hook_id=cfg["hook_id"],
        raw=_bytes(result),
        actor="llmlingua:compressor",
        target="llmlingua:consumer",
        carrier_id="llmlingua:compressed-context",
        source_id="llmlingua:raw-context",
        parent_ids=("compress-input",),
        status="success",
    )
    _finish(cap, cfg["hook_id"], "compress-output")


def _installed_version(probe):
    package = {
        "X1": "autogen-core",
        "X3": "a2a-sdk",
        "X4": "mcp",
        "X7": "llmlingua",
    }.get(probe)
    if package:
        return importlib.metadata.version(package)
    if probe == "X5":
        return "in-repo"
    if probe == "X6":
        return "source-commit"
    return "blocked"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--probe", required=True, choices=[f"X{i}" for i in range(1, 8)])
    p.add_argument("--out-root", required=True)
    p.add_argument("--code-commit", required=True)
    args = p.parse_args()
    if args.probe in {"X2", "X6"}:
        reason = _targets()[args.probe].get("block_reason", "frozen engineering block")
        raise SystemExit(f"{args.probe} is ENGINEERING_BLOCKED; native smoke intentionally not emulated: {reason}")
    root = Path(args.out_root) / args.probe
    root.mkdir(parents=True, exist_ok=True)
    if args.probe == "X1":
        asyncio.run(smoke_x1(root, args.code_commit))
    elif args.probe == "X3":
        asyncio.run(smoke_x3(root, args.code_commit))
    elif args.probe == "X4":
        asyncio.run(smoke_x4(root, args.code_commit))
    elif args.probe == "X5":
        smoke_x5(root, args.code_commit)
    elif args.probe == "X7":
        smoke_x7(root, args.code_commit)
    count = check_capture(root)
    cfg = _targets()[args.probe]
    report = {
        "probe": args.probe,
        "status": "NATIVE_SMOKE_PASS",
        "event_count": count,
        "installed_version": _installed_version(args.probe),
        "native_hook": cfg["hook_id"],
        "source_commit": _binding(args.probe, code_commit=args.code_commit)["source_commit"],
        "protocol_version": cfg.get("protocol_version"),
        "implementation_sha256": cfg.get("implementation_sha256"),
        "code_commit": args.code_commit,
    }
    (root / "smoke_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
