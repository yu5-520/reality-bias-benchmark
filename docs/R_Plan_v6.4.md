# Stage-II native evidence smoke — R Plan v6.4

Date: 2026-09-25. Status: **NON-STUDY NATIVE-SMOKE EXECUTION / SUBJECT GATE STILL CLOSED UNTIL VERIFIED MANIFEST**.

This layer follows v6.3. It does not alter the T1–T3 tasks, nine Software Engineering roles, 21-cell prospective matrix, Stage-I evidence, or CPR definitions.

## Purpose

The runtime-surface check in v6.3 proved that pinned implementations can be reached. It did not prove that the common evidence layer can capture a real operation performed through each native API.

v6.4 therefore adds one non-study native smoke for each non-blocked probe. Each smoke must:

- execute the pinned implementation rather than a Common-Pool alias;
- cross the probe's native operation boundary;
- preserve the original request/input and returned/result bytes or native serialization;
- write the common event only after the native object exists;
- end with an explicit termination event;
- pass the hash-chain and lineage validator;
- make no subject-model call and no C/P/R judgment.

The smoke inputs are engineering fixtures only and never enter the Stage-II scientific denominator.

## Frozen block handling

X2 MetaGPT remains `ENGINEERING_BLOCKED` because the pinned upstream commit requires `lancedb==0.4.0`, which is unavailable on the pinned CI package index/runtime. X6 MemoryBank is also `ENGINEERING_BLOCKED`: its pinned source simultaneously requires `llama-index==0.5.23.post1` and `langchain==0.0.146`, and the pinned Python 3.10 resolver reports those exact upstream requirements as mutually conflicting. These blocks are retained as engineering/observability limits. No dependency version, framework or communication implementation is substituted to make either condition pass.

A frozen engineering block does not prevent other preregistered probes from completing their native gates. The runtime manifest must carry the same block state and exact block reason. The three X2 cells and three X6 cells remain visible in the planned denominator as engineering-blocked and receive zero subject trajectories.

## Native smoke surfaces

- X1 AutoGen: actual `SingleThreadedAgentRuntime.send_message` delivery into a `RoutedAgent` handler and native reply.
- X3 A2A: actual official v1.0 Python SDK REST transport request/response plumbing using an in-memory HTTP transport; no bare protobuf deserialization is accepted.
- X4 MCP: actual 2026-07-28 SDK `Client` to `MCPServer` in-memory protocol negotiation and tool call.
- X5 RAG: the frozen repository retrieval implementation executes against the frozen checkout fixture.
- X7 LongLLMLingua: the pinned compressor executes `PromptCompressor.compress_prompt` on CPU with the official LLMLingua-2 small checkpoint.

The in-memory transports in X3/X4 are engineering smoke transports only. They exercise the real native client/runtime APIs without introducing a network service as a new experimental variable.

## Gate output

The workflow builds one runtime manifest from successful smoke reports plus the frozen X2 block. `stage2.preflight` opens execution only for non-blocked probes after verifying native capture provenance, hashes, implementation/protocol identity, subject profile and code binding.

A smoke failure does not trigger framework substitution or a subject run. It remains an engineering failure until repaired prospectively or recorded as another `ENGINEERING_BLOCKED` condition.

No paid subject execution, semantic evaluator, new R5, R6 intervention or R7 repair is authorized by this file alone.
