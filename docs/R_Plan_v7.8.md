# Stage-II X2 native MetaGPT Environment/Role runtime — R Plan v7.8

Date: 2026-09-25. Status: **ALL SEVEN NATIVE RUNNERS VERIFIED; ALL SUBJECT GATES CLOSED; ZERO NATURAL TRAJECTORIES**.

v7.8 completes the native-runner construction phase without changing T1–T3, the nine Software Engineering roles, the frozen checkout, the DeepSeek subject profile, the seven X definitions, or the one-natural-trajectory-per-cell rule.

## 1. X2 is a native multi-agent framework condition

X2 does **not** execute through `software_engineering_host_v1`, `CodingArena`, `RoleMailboxTransport`, or the historical `stage2.metagpt_transport` wrapper.

The runner binds the official `FoundationAgents/MetaGPT` source at commit `11cdf466d042aece04fc6cfd13b28e1a70341b1f`, whose package version at that commit is `1.0.0`. The nine frozen Software Engineering roles are instantiated as MetaGPT `Role` objects inside the native MetaGPT `Environment`.

The initial frozen user request is published once to the frozen entry role. Thereafter:

`Environment.run → Role._observe → Role._think/_act → Role.publish_message → Environment.publish_message / Role.msg_buffer`

owns scheduling and message routing. Directed delegation and specialist return messages therefore cross the framework's own message buffers and Environment history instead of being replayed through a common Stage-II mailbox.

The checkout affordances remain bounded to the isolated fixture checkout. They are host capabilities available to roles; they do not replace MetaGPT's scheduler or communication substrate.

## 2. Frozen subject provider without replacing MetaGPT scheduling

MetaGPT at the pinned commit eagerly loads a default LLM configuration during import. X2 therefore creates an isolated temporary HOME containing a dummy, non-network bootstrap config solely so the official framework classes can initialize without reading or modifying the operator's personal MetaGPT configuration.

That bootstrap is not a subject model. Each actual role turn receives a MetaGPT-compatible LLM shell whose completion call is routed into the already frozen Stage-II DeepSeek subject provider. Thus the system condition changes the multi-agent framework while the subject model binding remains the frozen Stage-II subject.

No MetaGPT source file is patched for this behavior.

## 3. Observation remains outside scheduling and routing

After each completed native `Environment.run(k=1)` round, the passive observer copies newly materialized MetaGPT `Environment.history` messages and newly materialized per-role memory messages. Observation occurs only after the framework round returns and does not create, route, reorder, filter, or acknowledge MetaGPT messages.

Self-addressed tool feedback is important here: native `Role.publish_message` places it directly into that role's `msg_buffer` instead of sending it through `Environment.history`. The observer preserves that distinction rather than normalizing both paths into one pre-execution interface.

## 4. Non-study verification

Workflow `36140759337` on candidate commit `2491637e1b6e458a38c6aaeebb6332316843e751` passed with no paid subject call.

The scripted T2 comparison executed this seven-turn native schedule:

`release_lead → frontend → frontend → release_lead → qa → qa → release_lead`

It completed in seven MetaGPT Environment rounds and finalized with the same terminal answer and identical checkout effects as the frozen direct engineering control. MetaGPT `Environment.history` contained six messages: the initial user request, two role delegations, two specialist finalizations, and the terminal entry result. The two self-addressed tool feedback messages remained on the native Role-buffer path rather than being artificially inserted into Environment history. Nine passive observer evidence files were sealed.

Final checkout digest: `15200a4ce5b6a09127f25371b55d9b4ae3b1f2071af78c3a7f37b6fcad8303e2`.

The workflow installs the exact frozen MetaGPT source and its pinned requirements except the unavailable `lancedb==0.4.0`, which is not used by the X2 Environment/Role path; a real `pyarrow==14.0.2` is pinned to avoid a partial namespace-package collision seen during CI import. These are runtime-environment repairs, not framework-source modifications.

This smoke is an engineering conformance test only. It does not claim that MetaGPT and the baseline host are scientifically equivalent.

## 5. Native-runner phase closure

X1 AutoGen, X2 MetaGPT, X3 A2A, X4 MCP, X5 RAG, X6 MemoryBank and X7 LongLLMLingua are now all `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`.

The 21 Stage-II cells remain unopened. A verified engineering runner is not authorization to collect a natural trajectory. Every X must separately satisfy its subject-readiness requirements on the exact forward execution commit; X6 and X7 additionally retain their frozen study-model/checkpoint gates.

Stage-II natural trajectory count remains **zero**.
