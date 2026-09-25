# Stage-II native heterogeneous execution — R Plan v7.0

Date: 2026-09-25. Status: **ARCHITECTURE REBASE; SUBJECT GATE CLOSED; ZERO NATURAL TRAJECTORIES**.

This checkpoint supersedes the v6.x forward execution scaffold before any Stage-II natural cell is collected. The frozen scientific inputs remain unchanged: T1–T3, the nine Software Engineering role definitions, the checkout fixture, the DeepSeek subject profile, the seven X targets, the one-natural-trajectory-per-cell rule, passive post-hoc audit and bounded local continuation policy.

The architectural correction is strict: **comparability is established after observation, not by forcing heterogeneous systems through one execution interface before observation.**

## 1. Three planes

Stage II now separates three planes.

1. **Registration plane.** A frozen registry records each X's upstream source/commit, independent runtime, native entrypoint, host attachment point, observer locations and evidence destinations. The registry is metadata; it does not define agent actions or framework behavior.
2. **Execution plane.** Each X executes in its own dependency environment using its frozen upstream framework or frozen in-repository mechanism. No X is required to implement a shared `send`, `enrich`, tool, mailbox, scheduler or action contract. The same task, role definitions, model profile and checkout are supplied as experimental conditions, but the framework owns scheduling, communication and native control flow.
3. **Observation plane.** Monitoring is external/passive. Framework-specific observers capture native messages, protocol frames, resources, retrievals, memory events, compression events, provider I/O, file effects and termination where those surfaces naturally exist. A post-hoc normalization step may map observed records into a common evidence schema, but that schema must not determine how the framework runs.

## 2. v6.x boundary

`stage2.coding_arena.CodingArena`, `stage2.transports.RoleMailboxTransport`, shared action JSON and the v6.x `transport/workspace/context_adapter` composition remain historical engineering scaffold only. They are not authorized natural-collection paths under v7.0.

In particular, a passing v6.x target smoke does not establish v7.0 subject readiness. Stage-II still contains zero natural trajectories, so this rebase changes no scientific observation.

## 3. X execution rule

The seven targets remain frozen to the versions already recorded by Stage II. They are now allowed to use mutually incompatible dependency environments. Dependency incompatibility between X systems is not a reason to modify an upstream framework or substitute a common compatibility layer.

- X1 AutoGen: official frozen AutoGen source/runtime.
- X2 MetaGPT: official frozen MetaGPT source/runtime in its own compatible environment.
- X3 A2A: frozen A2A protocol and Python SDK; native remote task/artifact path.
- X4 MCP: frozen MCP protocol and Python SDK; official client/server protocol path.
- X5 RAG: frozen in-repository retrieval implementation.
- X6 MemoryBank: frozen upstream source in its own compatible environment.
- X7 LongLLMLingua: frozen LongLLMLingua source/checkpoint; no LLMLingua-2 substitution.

No source framework is changed merely to conform to the experiment.

## 4. Frozen common conditions

The following remain common because they are scientific inputs, not an execution interface: the checkout bytes, T1–T3 user requests, nine role identities/responsibilities, entry-role identity, DeepSeek subject profile, resource ceilings, one-shot cell reservation and immutable raw evidence sealing.

The role roster is common; the scheduler is not. The task is common; the action grammar is not. The subject model is common; the framework's internal message/control representation is not.

## 5. Monitoring rule

The monitor is an external observer. It may subscribe to native callbacks, protocol logs, subprocess streams, filesystem effects or framework-owned event stores. It may copy raw bytes and create content hashes. It may not rewrite a framework message, replace a framework scheduler, inject a shared mailbox, change tool semantics, or require an X to emit a common action sequence.

The common evidence representation is therefore a **post-observation audit index**, never an upstream runtime contract.

## 6. Forward gate

`stage2/native_v7/registry.json` is the authoritative v7 execution registry. Every X starts `PENDING_NATIVE_RUNNER`. A cell cannot be reserved until that X has:

- an independently reproducible frozen environment;
- an exact native entrypoint;
- a framework-specific passive observer;
- a non-subject smoke showing that the observer does not alter native payload bytes or control flow;
- a real-provider subject-readiness check bound to the exact execution commit.

Only then may one natural trajectory be collected for that X–task cell. No CPR-triggered rerun is allowed.

The immediate implementation target after this checkpoint is therefore not to run a cell. It is to make each X independently runnable without restoring a common execution layer.
