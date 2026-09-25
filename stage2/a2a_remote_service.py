"""A2A v1.0.0 remote task/artifact boundary for non-subject protocol smoke.

This service exercises a real A2A task and artifact. It deliberately does not
claim that a subject-model decision was executed remotely until a provider is
configured and its raw calls are recorded in the remote service.
"""
import os


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

    class RemoteRoleExecutor(AgentExecutor):
        async def execute(self, context, event_queue):
            task = context.current_task or new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)
            await event_queue.enqueue_event(TaskStatusUpdateEvent(
                task_id=context.task_id, context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING)))
            text = "\n".join(part.text for part in context.message.parts if part.HasField("text"))
            await event_queue.enqueue_event(TaskArtifactUpdateEvent(
                task_id=context.task_id, context_id=context.context_id,
                artifact=new_text_artifact(name="delegated_message", text=text)))
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
