"""Transport hooks for the shared nine-role coding arena.

Only AutoGenTransport crosses an installed framework boundary. The local
transport is a negative-control plumbing smoke and cannot pass subject preflight.
"""
from dataclasses import asdict, dataclass

from .coding_arena import DIRECTORY
from .evidence import canonical_bytes


@dataclass(frozen=True)
class RoleMessage:
    sender: str
    target: str
    content: str
    carrier_id: str
    cause: str


class LocalSmokeTransport:
    """Never use for a natural trajectory; no framework boundary exists."""
    def __init__(self, capture):
        self.probe = capture.probe
        self.capture = capture
        self.index = 0

    async def open(self, inbox):
        self.inbox = inbox

    async def close(self):
        pass

    async def send(self, *, sender, target, content, cause, operation):
        self.index += 1
        msg = RoleMessage(sender, target, content, f"offline-{self.index}", cause)
        raw = canonical_bytes(asdict(msg))
        sent = self.capture.capture(event_id=f"offline-send-{self.index}", operation=operation,
                                    phase="emitted", native_locator="offline:local", hook_id="offline-contract-smoke",
                                    raw=raw, actor=sender, target=target, source_id=cause,
                                    carrier_id=msg.carrier_id, parent_ids=(cause,))
        received = self.capture.capture(event_id=f"offline-receive-{self.index}", operation="receive_message",
                                        phase="delivered", native_locator="offline:local",
                                        hook_id="offline-contract-smoke", raw=raw, actor=target, target=sender,
                                        source_id=cause, carrier_id=msg.carrier_id, parent_ids=(sent["event_id"],))
        return received["event_id"]


class RoleMailboxTransport(LocalSmokeTransport):
    """Shared local role mailbox underneath non-messaging layer probes X4–X7.

    This mailbox is not a Common Pool or an architectural probe itself. Its
    operations remain observable while MCP/RAG/memory/compression changes the
    separate authority carrier. X1–X3 must use their native communication.
    """

    def __init__(self, capture):
        if capture.probe not in {"X4", "X5", "X6", "X7"}:
            raise ValueError("role mailbox is only for information-layer probes")
        super().__init__(capture)

    async def send(self, *, sender, target, content, cause, operation):
        self.index += 1
        msg = RoleMessage(sender, target, content, f"mailbox-{self.index}", cause)
        raw = canonical_bytes(asdict(msg))
        sent = self.capture.capture(event_id=f"mailbox-send-{self.index}", operation=operation,
                                    phase="emitted", native_locator=f"stage2.mailbox:{msg.carrier_id}",
                                    hook_id="stage2.role_mailbox.v1", raw=raw, actor=sender, target=target,
                                    source_id=cause, carrier_id=msg.carrier_id, parent_ids=(cause,))
        received = self.capture.capture(event_id=f"mailbox-recv-{self.index}", operation="receive_message",
                                        phase="delivered", native_locator=f"stage2.mailbox:{msg.carrier_id}",
                                        hook_id="stage2.role_mailbox.v1", raw=raw, actor=target, target=sender,
                                        source_id=cause, carrier_id=msg.carrier_id, parent_ids=(sent["event_id"],))
        return received["event_id"]


class AutoGenTransport:
    """Actual autogen_core RoutedAgent / SingleThreadedAgentRuntime dispatch.

    The handler, not the caller's optimistic send path, records delivery.
    No shared-pool messages are reused as evidence of this native boundary.
    """
    probe = "X1"

    def __init__(self, capture):
        if capture.probe != self.probe:
            raise ValueError("AutoGen requires X1 capture")
        self.capture = capture
        self.index = 0
        self.delivered = {}

    async def open(self, inbox):
        try:
            from autogen_core import SingleThreadedAgentRuntime, RoutedAgent, AgentId, message_handler
        except ImportError as exc:
            raise RuntimeError("autogen-core==0.7.5 is required") from exc

        self.AgentId = AgentId
        self.runtime = SingleThreadedAgentRuntime()
        parent = self

        class NativeRole(RoutedAgent):
            def __init__(self, role_id):
                super().__init__(f"Stage-II {role_id}")
                self.role_id = role_id

            @message_handler
            async def deliver(self, message: RoleMessage, ctx) -> str:
                parent.delivered[message.carrier_id] = parent._receive(message, self.role_id)
                return parent.delivered[message.carrier_id]

        for role in DIRECTORY:
            await NativeRole.register(self.runtime, role, lambda role=role: NativeRole(role))
        self.runtime.start()

    async def close(self):
        if hasattr(self, "runtime"):
            await self.runtime.stop_when_idle()

    def _receive(self, msg, target):
        raw = canonical_bytes(asdict(msg))
        delivered = self.capture.capture(
            event_id=f"autogen-recv-{self.index}", operation="receive_message", phase="delivered",
            native_locator=f"autogen_core.RoutedAgent:{target}:{msg.carrier_id}",
            hook_id="autogen.native.agentchat",
            raw=raw, actor=target, target=msg.sender, source_id=msg.cause,
            carrier_id=msg.carrier_id, carrier_type="autogen-core-message",
            parent_ids=(f"autogen-send-{self.index}",))
        return delivered["event_id"]

    async def send(self, *, sender, target, content, cause, operation):
        self.index += 1
        message = RoleMessage(sender, target, content, f"autogen-{self.index}", cause)
        raw = canonical_bytes(asdict(message))
        self.capture.capture(event_id=f"autogen-send-{self.index}", operation=operation,
                             phase="emitted", native_locator=f"autogen_core.AgentRuntime.send_message:{target}",
                             hook_id="autogen.native.agentchat", raw=raw, actor=sender,
                             target=target, source_id=cause, carrier_id=message.carrier_id,
                             carrier_type="autogen-core-message", parent_ids=(cause,))
        received_id = await self.runtime.send_message(message, self.AgentId(target, "default"),
                                                      sender=self.AgentId(sender, "default"),
                                                      message_id=message.carrier_id)
        if self.delivered.get(message.carrier_id) != received_id:
            raise RuntimeError("AutoGen runtime did not deliver expected native message")
        return received_id
