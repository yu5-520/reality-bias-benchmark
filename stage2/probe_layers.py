"""Native Stage-II system-layer adapters for the common coding environment."""
import asyncio
import copy
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .coding_engine import DirectLayer, stable_json
from .evidence import NativeCapture

BASE = Path(__file__).resolve().parent


def _target(probe):
    return json.loads((BASE / "runtime_bindings.json").read_text())["probes"][probe]


def _binding(probe, code_commit):
    cfg = _target(probe)
    source_commit = cfg.get("source_commit") or cfg.get("protocol_commit") or code_commit
    out = {
        "probe": probe,
        "source_commit": source_commit,
        "native_hook": cfg["hook_id"],
        "code_commit": code_commit,
    }
    for key in ("protocol_version", "sdk_commit", "implementation_sha256"):
        if cfg.get(key):
            out[key] = cfg[key]
    return out


class NativeLayer(DirectLayer):
    def __init__(self, probe, *, workdir, native_root, run_id, code_commit):
        self.probe = probe
        self.workdir = Path(workdir)
        self.cfg = _target(probe)
        self.cap = NativeCapture(native_root, probe, run_id, _binding(probe, code_commit))
        self._event_seq = 0
        self._last_event = None

    def _capture(self, operation, phase, raw, *, actor, carrier_id, source_id, target=None, parent_ids=(), locator=None, status="success"):
        event_id = f"N{self._event_seq:05d}"
        self._event_seq += 1
        row = self.cap.capture(
            event_id=event_id,
            operation=operation,
            phase=phase,
            native_locator=locator or self.cfg["hook_id"],
            hook_id=self.cfg["hook_id"],
            raw=raw if isinstance(raw, bytes) else stable_json(raw).encode("utf-8"),
            actor=actor,
            target=target,
            carrier_id=carrier_id,
            source_id=source_id,
            parent_ids=parent_ids,
            status=status,
        )
        self._last_event = event_id
        return row

    def close(self):
        parents = (self._last_event,) if self._last_event else ()
        self._capture(
            "termination",
            "returned",
            b"stage2 subject-layer capture closed",
            actor="stage2:runner",
            carrier_id=f"{self.probe}:termination",
            source_id=f"{self.probe}:runtime",
            parent_ids=parents,
            locator="stage2.probe_layers:close",
        )


class AutoGenLayer(NativeLayer):
    def __init__(self, **kwargs):
        super().__init__("X1", **kwargs)

    def transfer(self, *, sender, target, payload, kind):
        from autogen_core import AgentId, MessageContext, RoutedAgent, SingleThreadedAgentRuntime, message_handler

        layer = self
        request_raw = stable_json(payload).encode("utf-8")
        request_event = self._capture(
            "delegate" if kind == "invoke_agent" else "send_message",
            "emitted",
            request_raw,
            actor=sender,
            target=target,
            carrier_id=f"autogen:{kind}:request",
            source_id=f"agent:{sender}",
            locator="SingleThreadedAgentRuntime.send_message:request",
        )

        @dataclass
        class BridgeMessage:
            content: str

        class Relay(RoutedAgent):
            def __init__(self):
                super().__init__("Stage-II native role-message relay")

            @message_handler
            async def handle(self, message: BridgeMessage, ctx: MessageContext) -> BridgeMessage:
                return BridgeMessage(message.content)

        async def roundtrip():
            runtime = SingleThreadedAgentRuntime()
            await Relay.register(runtime, "stage2_relay", Relay)
            runtime.start()
            try:
                return await runtime.send_message(BridgeMessage(request_raw.decode("utf-8")), AgentId("stage2_relay", "default"))
            finally:
                await runtime.stop()

        returned = asyncio.run(roundtrip())
        value = json.loads(returned.content)
        self._capture(
            "receive_message",
            "delivered",
            returned.content.encode("utf-8"),
            actor=target,
            target=target,
            carrier_id=f"autogen:{kind}:delivered",
            source_id=f"autogen:{kind}:request",
            parent_ids=(request_event["event_id"],),
            locator="RoutedAgent.message_handler:return",
        )
        return value


class A2ALayer(NativeLayer):
    def __init__(self, **kwargs):
        super().__init__("X3", **kwargs)

    def transfer(self, *, sender, target, payload, kind):
        import httpx
        from a2a.client.transports.rest import RestTransport
        from a2a.helpers.proto_helpers import new_text_message
        from a2a.types import AgentCapabilities, AgentCard, AgentInterface, SendMessageRequest

        wire = {}
        text_payload = stable_json(payload)
        response_body = {
            "message": {
                "messageId": f"stage2-{sender}-{target}",
                "role": "ROLE_AGENT",
                "parts": [{"text": text_payload}],
            }
        }

        async def handler(request):
            wire["request"] = request.content
            raw = json.dumps(response_body, separators=(",", ":")).encode("utf-8")
            wire["response"] = raw
            return httpx.Response(200, content=raw, headers={"content-type": "application/json"}, request=request)

        async def roundtrip():
            card = AgentCard(
                name="Stage-II Role Bridge",
                description="Local A2A boundary for one isolated coding trajectory",
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
                req = SendMessageRequest(message=new_text_message(text=text_payload))
                return await transport.send_message(request=req)

        response = asyncio.run(roundtrip())
        request_event = self._capture(
            "remote_task" if kind == "invoke_agent" else "send_message",
            "emitted",
            wire["request"],
            actor=sender,
            target=target,
            carrier_id=f"a2a:{kind}:request",
            source_id=f"agent:{sender}",
            locator="RestTransport.send_message:/message:send",
        )
        self._capture(
            "artifact_return" if kind == "invoke_agent" else "receive_message",
            "returned",
            wire["response"],
            actor=target,
            target=target,
            carrier_id=f"a2a:{kind}:response",
            source_id=f"a2a:{kind}:request",
            parent_ids=(request_event["event_id"],),
            locator="RestTransport.send_message:SendMessageResponse",
        )
        if not response.HasField("message"):
            raise RuntimeError("A2A bridge returned no message")
        return json.loads(response.message.parts[0].text)


class MCPLayer(NativeLayer):
    def __init__(self, **kwargs):
        super().__init__("X4", **kwargs)

    def project_action(self, *, actor, action, tools):
        from mcp import Client
        from mcp.server import MCPServer

        server = MCPServer("Stage-II Checkout Workspace")
        direct = DirectLayer()

        @server.tool()
        def project_action(action_json: str) -> dict:
            """Execute one bounded workspace action in the isolated checkout."""
            parsed = json.loads(action_json)
            return direct.project_action(actor=actor, action=parsed, tools=tools)

        request = {"tool": "project_action", "action": action}
        request_event = self._capture(
            "tool_call",
            "emitted",
            request,
            actor=actor,
            target="mcp:workspace-server",
            carrier_id="mcp:tool-request",
            source_id=f"agent:{actor}",
            locator="mcp.Client.call_tool:project_action",
        )

        async def call():
            async with Client(server) as client:
                result = await client.call_tool("project_action", {"action_json": stable_json(action)})
                return result, str(client.protocol_version)

        result, protocol = asyncio.run(call())
        structured = getattr(result, "structured_content", None)
        if structured is None:
            content = getattr(result, "content", None) or []
            if not content or not getattr(content[0], "text", None):
                raise RuntimeError("MCP project tool returned no structured/text result")
            structured = json.loads(content[0].text)
        self._capture(
            "receive_message",
            "returned",
            structured,
            actor="mcp:workspace-server",
            target=actor,
            carrier_id="mcp:tool-result",
            source_id="mcp:tool-request",
            parent_ids=(request_event["event_id"],),
            locator=f"mcp.Client.call_tool:return;protocol={protocol}",
        )
        operation = action["type"]
        if operation in {"write_file", "delete_file"}:
            self._capture(
                "file_change",
                "executed",
                structured,
                actor="mcp:workspace-server",
                target=actor,
                carrier_id="mcp:file-change",
                source_id="mcp:tool-result",
                parent_ids=(self._last_event,),
                locator="MCPServer.project_action:file_change",
            )
        elif operation == "run_tests":
            self._capture(
                "test_run",
                "executed",
                structured,
                actor="mcp:workspace-server",
                target=actor,
                carrier_id="mcp:test-run",
                source_id="mcp:tool-result",
                parent_ids=(self._last_event,),
                locator="MCPServer.project_action:test_run",
            )
        return structured


class RAGLayer(NativeLayer):
    def __init__(self, **kwargs):
        super().__init__("X5", **kwargs)

    def prepare_context(self, *, actor, turn, context):
        from .retrieval import retrieve

        query = stable_json({"actor": actor, "inbox": context.get("inbox", [])})[:8000]
        request_event = self._capture(
            "retrieve",
            "emitted",
            query.encode("utf-8"),
            actor=actor,
            target="rag:retriever",
            carrier_id=f"rag:query:{turn}",
            source_id=f"agent:{actor}",
            locator="stage2.retrieval.retrieve:query",
        )
        hits = retrieve(self.workdir, query, limit=int(self.cfg.get("retrieval_limit", 4)))
        self._capture(
            "receive_message",
            "returned",
            hits,
            actor="rag:retriever",
            target=actor,
            carrier_id=f"rag:hits:{turn}",
            source_id=f"rag:query:{turn}",
            parent_ids=(request_event["event_id"],),
            locator="stage2.retrieval.retrieve:hits",
        )
        out = copy.deepcopy(context)
        out["retrieved_context"] = hits
        return out


class LongLLMLinguaLayer(NativeLayer):
    def __init__(self, **kwargs):
        super().__init__("X7", **kwargs)
        from llmlingua import PromptCompressor

        model = self.cfg.get("compression_model", "microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank")
        self.rate = float(self.cfg.get("compression_rate", 0.6))
        self.compressor = PromptCompressor(model_name=model, device_map="cpu", use_llmlingua2=True)
        self.model = model

    def prepare_context(self, *, actor, turn, context):
        raw = stable_json(context)
        request_event = self._capture(
            "compress",
            "emitted",
            {"model": self.model, "rate": self.rate, "context": raw},
            actor=actor,
            target="llmlingua:compressor",
            carrier_id=f"llmlingua:input:{turn}",
            source_id=f"agent:{actor}",
            locator="PromptCompressor.compress_prompt:input",
        )
        result = self.compressor.compress_prompt([raw], rate=self.rate)
        compressed = result.get("compressed_prompt")
        if not compressed:
            raise RuntimeError("LongLLMLingua returned empty compressed context")
        self._capture(
            "compress",
            "returned",
            result,
            actor="llmlingua:compressor",
            target=actor,
            carrier_id=f"llmlingua:output:{turn}",
            source_id=f"llmlingua:input:{turn}",
            parent_ids=(request_event["event_id"],),
            locator="PromptCompressor.compress_prompt:return",
        )
        return {
            "compressed_working_context": compressed,
            "compression_metadata": {
                "model": self.model,
                "rate": self.rate,
                "origin_tokens": result.get("origin_tokens"),
                "compressed_tokens": result.get("compressed_tokens"),
            },
        }


def make_layer(probe, *, workdir, native_root, run_id, code_commit):
    target = _target(probe)
    if target.get("state") == "ENGINEERING_BLOCKED":
        raise RuntimeError(f"{probe} ENGINEERING_BLOCKED: {target.get('block_reason')}")
    cls = {
        "X1": AutoGenLayer,
        "X3": A2ALayer,
        "X4": MCPLayer,
        "X5": RAGLayer,
        "X7": LongLLMLinguaLayer,
    }.get(probe)
    if cls is None:
        raise ValueError("unsupported/non-runnable Stage-II probe")
    return cls(workdir=workdir, native_root=native_root, run_id=run_id, code_commit=code_commit)
