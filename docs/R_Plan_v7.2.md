# Stage-II background host freeze — R Plan v7.2

Date: 2026-09-25. Status: **CAPABILITY-LAYER BACKGROUND HOST FREEZE; SUBJECT GATE CLOSED; ZERO NATURAL TRAJECTORIES**.

v7.2 implements the background software-engineering substrate declared in v7.1 for X4 MCP, X5 RAG, X6 MemoryBank and X7 LongLLMLingua. It does not change the seven X definitions and it does not make X4–X7 look like agent schedulers.

## 1. What is frozen

`stage2/native_v7/software_host_v1.py` preserves the historical Stage-II software-engineering role environment for capability-layer probes:

- T1–T3 and the same nine role identities/responsibilities;
- the same entry role;
- the same queue/mailbox scheduling semantics;
- the same action vocabulary and bounded checkout operations;
- the same turn and pending-message ceilings.

This substrate exists because X4–X7 operate below the role scheduler: tool/resource protocol, retrieval, memory, and context compression respectively. They need a software-engineering multi-agent environment around them, but they do not need to own that environment.

X1 AutoGen and X2 MetaGPT do not use this host. X3 A2A does not use its mailbox transport.

## 2. What was removed

The historical v6 host mixed observation with execution. Message and tool evidence IDs were created during execution and some of those audit fields entered the model-visible inbox/observation objects.

The v7.2 host removes that coupling. It imports no `NativeCapture`, evidence schema, external observer or audit hook, and it creates no event IDs. Monitoring is attached outside this host.

This means the goal is **control-semantic continuity**, not byte-identical prompts with the instrumented v6 scaffold. Audit metadata is intentionally absent from model-visible context.

## 3. Non-study equivalence gate

`stage2/native_v7/software_host_smoke.py` drives the historical v6 substrate and the de-instrumented v7.2 host with the same scripted role/action sequence on separate frozen checkouts. It requires the same terminal result, turn count and checkout effects, and separately verifies that audit identifiers do not occur in the v7.2 model-visible prompts.

Passing this smoke freezes `software_engineering_host_v1` as `FROZEN_DEINSTRUMENTED_HOST`. This is an engineering statement only. It does not make any X4–X7 runner subject-ready and does not open a natural cell.

## 4. Next

With the background host explicit and de-instrumented, X4–X7 can be implemented as separate probe-specific attachments at their natural boundaries. They still do not share a required X adapter API. X2 and X3 proceed through their own native framework/protocol runners.

Stage-II natural trajectory count remains zero.
