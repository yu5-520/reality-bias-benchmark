from __future__ import annotations

import inspect

from stage2.native_v7.x2_metagpt.runner import (
    DIRECTORY,
    LIMITS,
    ROLES,
    TERMINAL_ADDRESS,
    Environment,
    Message,
    RuntimeState,
    Stage2MetaRole,
    Stage2ProviderLLM,
    UserRequirement,
    _load_inputs,
    _observe_native,
    _pending_messages,
    build_subject_provider,
    MetaGPTCheckout,
    PassiveEventObserver,
)


async def _call_hook(hook, **payload):
    if hook is None:
        return None
    value = hook(**payload)
    if inspect.isawaitable(value):
        value = await value
    return value


async def run_task_with_checkpoints(
    *,
    checkout,
    task_file,
    roles_file,
    subject_file,
    observer_root=None,
    provider=None,
    checkpoint_hook=None,
    decision_horizon=None,
):
    """MetaGPT-native task with callbacks only between env.run(k=1) rounds."""

    task, subject = _load_inputs(task_file, roles_file, subject_file)
    active_provider = provider if provider is not None else build_subject_provider(subject)
    runtime = RuntimeState(max_turns=int(decision_horizon if decision_horizon is not None else subject["limits"]["max_turns"]))
    runtime.task = task
    checkout_api = MetaGPTCheckout(checkout)
    env = Environment(desc="Software Engineering")
    roles = [
        Stage2MetaRole(
            name=row["id"],
            profile=row["role"],
            goal=row["responsibility"],
            llm=Stage2ProviderLLM(active_provider),
            stage2_runtime=runtime,
            stage2_checkout=checkout_api,
            stage2_directory=DIRECTORY,
            stage2_entry=ROLES["entry_agent"],
        )
        for row in ROLES["agents"]
    ]
    env.add_roles(roles)
    if set(env.role_names()) != set(DIRECTORY):
        raise RuntimeError("MetaGPT native Environment lost a frozen role")

    initial = Message(
        content=task["user_request"],
        role="user",
        sent_from="USER",
        send_to={ROLES["entry_agent"]},
        cause_by=UserRequirement,
        metadata={"kind": "user_request"},
    )
    env.publish_message(initial)

    observer = PassiveEventObserver(observer_root, probe="X2") if observer_root else None
    env_index = 0
    role_indices = {}
    rounds = 0

    await _call_hook(
        checkpoint_hook,
        boundary="BEFORE_FIRST_ENV_RUN",
        event_ref="x2:task-start",
        env=env,
        runtime=runtime,
        checkout_api=checkout_api,
        rounds=0,
    )

    try:
        while not runtime.stop_reason and not env.is_idle and rounds < runtime.max_turns:
            rounds += 1
            await env.run(k=1)
            if observer is not None:
                env_index = _observe_native(observer, env, env_index, role_indices)
            pending = _pending_messages(env)
            if pending > int(subject["limits"]["max_pending_messages"]):
                await runtime.stop("pending_message_budget")
            elif not runtime.stop_reason and env.is_idle:
                await runtime.stop("queue_exhausted")

            await _call_hook(
                checkpoint_hook,
                boundary="AFTER_EACH_ENV_RUN_K1_RETURN",
                event_ref=f"x2:round:{rounds:04d}:post",
                env=env,
                runtime=runtime,
                checkout_api=checkout_api,
                rounds=rounds,
            )
            if runtime.stop_reason:
                break

        if not runtime.stop_reason:
            await runtime.stop(
                "turn_budget" if runtime.turns >= runtime.max_turns else "round_guard"
            )
    finally:
        if observer is not None:
            if env_index < len(env.history.get()):
                _observe_native(observer, env, env_index, role_indices)
            observer.seal()

    await _call_hook(
        checkpoint_hook,
        boundary="TERMINAL",
        event_ref="x2:terminal",
        env=env,
        runtime=runtime,
        checkout_api=checkout_api,
        rounds=rounds,
    )

    return {
        "answer": runtime.answer,
        "stop_reason": runtime.stop_reason,
        "turns": runtime.turns,
        "metagpt_rounds": rounds,
        "environment_messages": len(env.history.get()),
        "pending_messages": _pending_messages(env),
        "history": sorted(runtime.history, key=lambda row: row["turn"]),
    }
