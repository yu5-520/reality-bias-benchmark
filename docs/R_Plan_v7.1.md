# Stage-II native integration runners — R Plan v7.1

Date: 2026-09-25. Status: **NATIVE RUNNER IMPLEMENTATION; SUBJECT GATE CLOSED; ZERO NATURAL TRAJECTORIES**.

This checkpoint continues v7.0. It does not change T1–T3, the nine Software Engineering roles, the frozen checkout, the DeepSeek subject profile, the seven X targets, the one-natural-trajectory-per-cell rule, or any Stage-I evidence. Stage II still has zero natural trajectories.

The v7.0 rule is retained: **X implementations are not modified to satisfy one experiment-wide runtime interface.** Host-side integration code may connect a frozen upstream X to the software-engineering environment, but that code is probe-specific and must not become an API that every X is required to implement.

## 1. Native topology, not one universal scheduler

The seven X targets occupy different architectural layers, so "native execution" does not mean pretending that every X is a multi-agent scheduler.

- **X1 AutoGen / X2 MetaGPT** are native multi-agent framework conditions. Their own agent/runtime/environment abstractions own communication and scheduling.
- **X3 A2A** is an inter-agent protocol condition. Agents/services communicate through the frozen A2A task/message/artifact protocol.
- **X4 MCP** is a tool/resource protocol condition. The official frozen MCP client/server path attaches to the software-engineering multi-agent host; MCP is not forced to become the host scheduler.
- **X5 RAG**, **X6 MemoryBank**, and **X7 LongLLMLingua** are information/context capability conditions. Their frozen native mechanism attaches at its natural retrieval, memory, or compression boundary while the software-engineering host continues to provide the role environment.

For X4–X7 the background role host is therefore allowed, but **it may not be hidden**. The registry explicitly binds those four probes to `software_engineering_host_v1`, whose historical execution/communication semantics come from `stage2.coding_arena.CodingArena` and `stage2.transports.RoleMailboxTransport`. X1–X3 explicitly do not inherit that substrate. The formal v7 host for X4–X7 remains blocked until the same execution semantics are frozen with monitoring removed from the execution path.

Thus the common condition is the software-engineering task environment, not a shared adapter API. A capability-layer X is allowed to coexist with the host because that is its natural deployment mode; it is not rewritten into a fake communication framework for comparability.

## 2. X1 first native runner

`stage2/native_v7/x1_autogen/runner.py` is the first v7 native-runner implementation. It uses the frozen official AutoGen AgentChat primitives directly:

- nine `AssistantAgent` instances use the frozen role identities and responsibilities;
- `Swarm` owns the handoff-based speaker transition;
- AutoGen-native tool calls expose bounded checkout operations;
- `TextMentionTermination` and the Stage-II turn ceiling bound execution;
- the real-provider path uses AutoGen's official OpenAI-compatible model client against the already frozen DeepSeek endpoint/profile.

The runner does not import the historical `CodingArena`, `RoleMailboxTransport`, or shared `context_adapter`. Other X systems are not required to implement the X1 tool/handoff topology.

## 3. External observation

`PassiveEventObserver` is a one-way content-addressed tee over already-emitted native public events. It copies bytes and returns the input bytes unchanged. X1 observes the public AutoGen team stream rather than inserting a replacement scheduler or mailbox. The process-boundary observer remains outside the child runner and records invocation, stdout, stderr and exit status.

The non-study X1 smoke uses AutoGen's upstream replay model client. It verifies the native handoff/tool path on an isolated checkout and verifies the observer byte-preservation contract without making a paid model call. Passing this smoke establishes only the native runner/observer engineering gate. It does **not** establish real-provider subject readiness and does not open a natural cell.

## 4. State transition

A probe moves through:

`PENDING_NATIVE_RUNNER -> NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING -> SUBJECT_READY`

Only `SUBJECT_READY` may be admitted by `stage2.native_v7.collect`. The middle state records that the exact native entrypoint and non-study observer smoke have passed while the real-provider readiness gate remains closed.

X1 has passed the non-study runner/observer smoke. X2–X3 still need their probe-specific native runners. X4–X7 first require `software_engineering_host_v1` to be de-instrumented and frozen, after which each capability can attach at its own native boundary. Dependency environments remain independent. No Stage-II natural cell is run during runner construction.
