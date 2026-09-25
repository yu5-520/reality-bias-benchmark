"""MetaGPT Environment / Role native message and shared history hook.

Requires the exact MetaGPT runtime to import and route messages. No fallback
to a local mailbox exists; the condition remains blocked if the native role
or Environment cannot start.
"""
from importlib.metadata import version

from .coding_arena import DIRECTORY


class MetaGPTTransport:
    probe = "X2"

    def __init__(self, capture):
        if capture.probe != self.probe:
            raise ValueError("MetaGPT requires X2 capture")
        self.capture = capture
        self.serial = 0

    async def open(self, inbox):
        if version("metagpt") != "0.8.1":
            raise RuntimeError("MetaGPT 0.8.1 required; no SDK substitutions")
        from metagpt.environment.base_env import Environment
        from metagpt.roles.role import Role
        from metagpt.schema import Message

        self.Message = Message
        self.env = Environment(desc="Software Engineering")
        self.env.add_roles([Role(name=agent["id"], profile=agent["role"], actions=[])
                            for agent in DIRECTORY.values()])
        if set(self.env.role_names()) != set(DIRECTORY):
            raise RuntimeError("MetaGPT native environment lost a frozen role")

    async def close(self):
        pass

    async def send(self, *, sender, target, content, cause, operation):
        if target not in DIRECTORY or sender not in DIRECTORY:
            raise ValueError("role outside frozen roster")
        self.serial += 1
        message = self.Message(content=content, sent_from=sender, send_to={target},
                               metadata={"source_event": cause, "stage2_carrier": self.serial})
        raw = message.model_dump_json().encode()
        sent = self.capture.capture(event_id=f"metagpt-publish-{self.serial}", operation=operation,
                                    phase="emitted", native_locator=f"MetaGPT.Environment.publish_message:{message.id}",
                                    hook_id="metagpt.Environment.publish_message", raw=raw, actor=sender,
                                    target=target, source_id=cause, carrier_id=message.id,
                                    carrier_type="metagpt-message", parent_ids=(cause,))
        if not self.env.publish_message(message):
            raise RuntimeError("MetaGPT environment refused published message")
        shared = self.capture.capture(event_id=f"metagpt-state-{self.serial}", operation="shared_state",
                                      phase="executed", native_locator=f"MetaGPT.Environment.history:{message.id}",
                                      hook_id="metagpt.Environment.history", raw=message.model_dump_json().encode(),
                                      actor="ENVIRONMENT", source_id=cause, carrier_id=f"environment:{message.id}",
                                      carrier_type="metagpt-shared-history", parent_ids=(sent["event_id"],))
        delivered = self.env.get_role(target).rc.msg_buffer.pop()
        if delivered is None or delivered.id != message.id:
            raise RuntimeError("MetaGPT did not place message in target role buffer")
        receipt = self.capture.capture(event_id=f"metagpt-recv-{self.serial}", operation="receive_message",
                                       phase="delivered", native_locator=f"MetaGPT.Role.msg_buffer:{target}:{message.id}",
                                       hook_id="metagpt.Role.msg_buffer", raw=delivered.model_dump_json().encode(),
                                       actor=target, target=sender, source_id=cause, carrier_id=message.id,
                                       carrier_type="metagpt-message", parent_ids=(shared["event_id"],))
        return receipt["event_id"]
