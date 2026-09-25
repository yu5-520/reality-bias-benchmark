"""Separate A2A service for delegated messages and explicit remote decisions."""
import asyncio
import hashlib
import json
import os
from pathlib import Path


def _remote_provider():
    mode = os.getenv("STAGE2_A2A_REMOTE_MODE", "echo")
    if mode == "echo":
        return mode, None
    if mode == "scripted":
        actions = json.loads(os.environ["STAGE2_A2A_SCRIPT"])
        if not isinstance(actions, list) or not actions:
            raise ValueError("nonempty non-study remote action script required")
        return mode, iter(actions)
    if mode == "subject":
        if not os.environ.get("DEEPSEEK_API_KEY"):
            raise RuntimeError("frozen remote subject key is unavailable")
        from arena.providers import DeepSeekArenaProvider
        root = Path(__file__).resolve().parent.parent
        frozen = json.loads((root / "stage2/subject.json").read_text())
        config = json.loads((root / frozen["source_config"]).read_text())
        if (config["provider"] != frozen["provider"] or config["model_alias"] != frozen["model_alias"]
                or config["subject"] != frozen["subject"]):
            raise ValueError("remote model configuration differs from frozen subject")
        return mode, DeepSeekArenaProvider(config)
    raise ValueError("A2A remote execution mode is not frozen")


def build_app(base_url):
    from a2a.server.agent_execution import AgentExecutor
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import (AgentCapabilities, AgentCard, AgentInterface, AgentSkill,
                           Task, TaskArtifactUpdateEvent, TaskStatus, TaskState,
                           TaskStatusUpdateEvent)
    from a2a.helpers import new_task_from_user_message, new_text_artifact
    from starlette.applications import Starlette
    mode, provider = _remote_provider()

    class RemoteRoleExecutor(AgentExecutor):
        async def execute(self, context, event_queue):
            task = context.current_task or new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)
            await event_queue.enqueue_event(TaskStatusUpdateEvent(
                task_id=context.task_id, context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING)))
            text = "\n".join(part.text for part in context.message.parts if part.HasField("text"))
            parsed = json.loads(text)
            if parsed.get("operation") == "model_inference":
                if mode == "echo":
                    raise ValueError("remote model execution was not enabled for this A2A service")
                messages = parsed["messages"]
                if not isinstance(messages, list) or not messages:
                    raise ValueError("remote model received no frozen role prompt")
                if mode == "scripted":
                    try:
                        action = next(provider)
                    except StopIteration as exc:
                        raise ValueError("non-study remote script exhausted") from exc
                    response = {"content": json.dumps({"actions": [action]}, ensure_ascii=False),
                                "response_id": f"remote-script-{context.task_id}",
                                "model": "SCRIPTED_REMOTE_PREFLIGHT_ONLY", "usage": {}}
                else:
                    response = await asyncio.to_thread(provider.complete_agent, messages,
                                                       {"role": parsed["target"],
                                                        "turn": parsed["turn"]})
                request_bytes = json.dumps(messages, sort_keys=True, ensure_ascii=False,
                                           separators=(",", ":")).encode()
                text = json.dumps({"schema": "stage2-a2a-remote-model-artifact-v1",
                                   "remote_mode": mode, "role": parsed["target"],
                                   "request_sha256": hashlib.sha256(request_bytes).hexdigest(),
                                   "response": response}, ensure_ascii=False, sort_keys=True)
                artifact_name = "remote_model_result"
            else:
                artifact_name = "delegated_message"
            await event_queue.enqueue_event(TaskArtifactUpdateEvent(
                task_id=context.task_id, context_id=context.context_id,
                artifact=new_text_artifact(name=artifact_name, text=text)))
            await event_queue.enqueue_event(TaskStatusUpdateEvent(
                task_id=context.task_id, context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED)))

        async def cancel(self, context, event_queue):
            raise ValueError("local smoke task is already completed")

    card = AgentCard(name="Stage-II Remote Role Boundary", description="Remote task and artifact transport",
                     version="stage2-a2a-v1", default_input_modes=["text/plain"],
                     default_output_modes=["text/plain"],
                     capabilities=AgentCapabilities(streaming=False),
                     supported_interfaces=[AgentInterface(protocol_binding="JSONRPC", url=base_url)],
                     skills=[AgentSkill(id="delegated_message", name="Delegated message",
                                        description="Returns a remote artifact from a delegated message",
                                        tags=["delegation"])])
    handler = DefaultRequestHandler(agent_executor=RemoteRoleExecutor(),
                                    task_store=InMemoryTaskStore(), agent_card=card)
    return Starlette(routes=[*create_agent_card_routes(card), *create_jsonrpc_routes(handler, "/")])


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ["STAGE2_A2A_PORT"])
    uvicorn.run(build_app(f"http://127.0.0.1:{port}"), host="127.0.0.1", port=port, log_level="error")
