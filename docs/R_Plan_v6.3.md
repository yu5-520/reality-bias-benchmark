# Stage-II Day-1 native binding execution — R Plan v6.3

Date: 2026-09-25. Status: **NATIVE ENGINEERING GATE IN EXECUTION / NO SUBJECT EVIDENCE**.

Predecessors: `R_Plan_v6.0.md`, `R_Plan_v6.1.md`, and `R_Plan_v6.2.md` remain unchanged. Stage-I raw evidence remains immutable.

## 1. What is now bound

The common subject condition is frozen in `stage2/subject_lock.json`: DeepSeek `deepseek-flash`, expected provider model `DeepSeek-V4.1-Flash`, thinking disabled, temperature 0.2, 1200 maximum output tokens per call, and at most 18 provider calls per natural trajectory. Across the fixed 21-cell first group this creates a hard ceiling of 378 provider calls. Scientific retries of an identical prompt are zero. This lock does **not** authorize provider or evaluator execution.

The seven engineering bindings are frozen in `stage2/runtime_lock.json`. X1/X2/X6/X7 retain their exact upstream commits from v6.2. X3 A2A additionally binds the official Python SDK commit `0d5473ca4fa6d40034a6a7c8d65bce5cd85d8167`; X4 MCP additionally binds the official Python SDK commit `f1b6589088534632fef92238ee9750951e3c0185`. X5 remains the content-addressed in-repository retrieval implementation and is identified by implementation SHA rather than a fabricated source commit.

## 2. Native smoke is engineering evidence, not study evidence

`stage2/native_smoke.py` exercises deterministic provider-free native boundaries and writes the same hash-linked evidence interface used by the Stage-II gate:

- X1: AutoGen `SingleThreadedAgentRuntime.send_message`;
- X2: MetaGPT native `Memory.add/get` shared-state boundary;
- X3: official A2A Python SDK JSON-RPC client/server task-return boundary;
- X4: official MCP Python SDK tool-call and resource-read boundary;
- X5: the frozen in-repository retrieval boundary;
- X6: exact MemoryBank source checkout and its write/retrieval source locations;
- X7: exact LLMLingua package plus an explicitly revision-bound compressor checkpoint.

The workflow `.github/workflows/stage2-native-binding-smoke.yml` performs these checks without a subject-model secret. Every probe must yield exactly one of two receipts: `NATIVE_SMOKE_PASS` or `ENGINEERING_BLOCKED`. A blocker is retained as a first-group engineering outcome; it is never replaced by another framework or by renamed Common Pool traffic.

X6 must not be marked passed merely because the repository can be cloned or its JSON memory file can be written: the native retrieval path must also be proven without silently replacing the legacy MemoryBank stack. X7 must not download a floating model: the compressor checkpoint revision must be frozen before its native compression smoke can pass.

## 3. Evidence-gate strengthening

`NativeCapture` now accepts either an immutable upstream source commit or an immutable in-repository implementation hash. This closes the prior X5 contradiction where the frozen RAG implementation had a SHA-256 identity but the capture constructor required a non-null source commit.

The full preflight additionally binds:

- `runtime_lock.json` hash;
- `subject_lock.json` hash;
- official A2A/MCP SDK commits where applicable;
- X7 compressor checkpoint and revision;
- native event provenance to the runtime binding.

No structural event is promoted to C/P/R or semantic use by these engineering checks.

## 4. Handoff rule

Day 2 remains closed until the seven native smoke receipts are collected, all passing probes have valid native evidence, blocker reasons are frozen, and a runtime manifest passes `stage2.preflight`. Only passed probes may make their one T1/T2/T3 natural subject call sequence. Blocked probe cells remain `ENGINEERING_BLOCKED` in the 21-cell first-group inventory.

No new R5 is introduced. R6 remains passive semantic audit of frozen natural evidence. R7 remains limited to at most four eligible local repair continuations after natural-parent qualification.
