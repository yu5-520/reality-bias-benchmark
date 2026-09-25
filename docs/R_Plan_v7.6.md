# Stage-II X3 native A2A role-service environment — R Plan v7.6

Date: 2026-09-25. Status: **X3 NATIVE RUNNER VERIFIED; SUBJECT GATE CLOSED; ZERO NATURAL TRAJECTORIES**.

v7.6 continues the heterogeneous v7 architecture without changing T1–T3, the nine Software Engineering roles, the frozen checkout, the DeepSeek subject profile, the seven X definitions, or the one-natural-trajectory-per-cell rule.

## 1. X3 is a communication-protocol condition, not a baseline-host attachment

X3 does **not** execute through `software_engineering_host_v1`, `CodingArena`, `RoleMailboxTransport`, or the historical `stage2.a2a_transport` wrapper.

Instead, every one of the nine frozen Software Engineering roles is started as a distinct A2A-native service using the official A2A Python SDK pinned at commit `0d5473ca4fa6d40034a6a7c8d65bce5cd85d8167` and protocol source commit `173695755607e884aa9acf8ce4feed90e32727a1`.

The launcher is deliberately thin: it starts the nine services and submits the frozen user request only once to the `release_lead` Agent Card. After that initial call, role-to-role `message` and `delegate` actions are issued by the role services themselves as official A2A `SendMessage` calls. Returned work comes back as A2A Task/Artifact results. This keeps the protocol condition native instead of rebuilding the old mailbox under an A2A-shaped API.

Each service retains the same frozen role name/responsibility, task, action vocabulary and bounded checkout affordances. Checkout operations are implemented in the X3 service environment itself and contain no monitor/evidence side effects.

## 2. Native A2A execution structure

The service graph uses official v1.0 JSON-RPC surfaces:

`Agent Card discovery → SendMessage → Task state → Artifact → caller continuation`

The role that receives an A2A call performs its own subject-model turn. If that role delegates to another role, it becomes the A2A client for that next service. A specialist `finalize` returns a caller-facing artifact; the frozen entry role remains the only role whose `finalize` is terminal for the overall user task.

The global frozen model-turn budget is propagated through nested A2A calls, so a recursive collaboration path cannot create extra model invocations outside the Stage-II subject ceiling.

## 3. Observation remains outside role execution

Every role service has a separate transparent HTTP relay in front of it. Agent Cards advertise the relay URL, while the relay forwards the original request body to the untouched service backend and returns the backend response body unchanged.

The relay copies:

- Agent Card response bodies;
- A2A v1.0 JSON-RPC `SendMessage` request bodies;
- returned task/artifact response bodies.

Those captures are written outside the checkout. The relay neither parses model decisions nor creates A2A tasks, messages or artifacts. The official SDK and server remain responsible for protocol serialization and semantics.

## 4. Non-study verification

Workflow `36134380842` on candidate commit `ba8b71cd7450007751432df3a54d6e3c62db96b6` passed with no paid subject call.

The scripted T2 smoke exposed all nine roles as A2A services and executed a seven-turn path:

`release_lead → frontend → frontend → release_lead → qa → qa → release_lead`

Three native A2A task calls occurred: the initial user-to-entry call plus two role-to-role delegations. The external relays preserved three JSON-RPC request bodies, three task/artifact response bodies and twelve Agent Card response captures. The A2A-native run and the frozen direct engineering control both finalized in seven turns with the same terminal answer and identical checkout effects. Final checkout digest: `15200a4ce5b6a09127f25371b55d9b4ae3b1f2071af78c3a7f37b6fcad8303e2`.

This comparison is an engineering conformance test only. It does not claim that the A2A and baseline communication processes are scientifically equivalent.

## 5. Forward state

X1, X3, X4, X5 and X7 are now `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`. X2 and X6 remain `PENDING_NATIVE_RUNNER`.

No X3 cell is open until a separate real-provider readiness check passes on the exact forward execution commit.

Stage-II natural trajectory count remains **zero**.
