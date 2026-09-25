# Stage-II X7 official LongLLMLingua context attachment — R Plan v7.5

Date: 2026-09-25. Status: **X7 NATIVE RUNNER VERIFIED; STUDY CHECKPOINT + SUBJECT GATES CLOSED; ZERO NATURAL TRAJECTORIES**.

v7.5 continues the heterogeneous v7 architecture without changing T1–T3, the nine Software Engineering roles, the frozen checkout, the DeepSeek subject profile, the seven X definitions, or the one-natural-trajectory-per-cell rule.

## 1. X7 remains a context-compression capability

The frozen `software_engineering_host_v1` continues to own role scheduling, mailbox behavior, actions and checkout operations. X7 changes only the historical context supplied to the current role.

The X7 runner binds the official `microsoft/LLMLingua` source at commit `5a4c78ae18ab17a98cf997e8259354e546081d64`, package version `0.2.2`, and calls `PromptCompressor.compress_prompt` with the already frozen Stage-II X7 semantics: rate `0.5`, the frozen task request as `question`, and `rank_method="longllmlingua"`.

The user goal, role identity, available roles and action contract remain outside the compressed region. Only the historical `inbox` and tool `observations` are serialized and compressed; after compression the uncompressed inbox is removed and the compressor output becomes the model-visible historical context.

## 2. Checkpoint boundary

A formal X7 natural run is not authorized merely because the runner works. It also requires a local compressor checkpoint and a complete file-level SHA-256 manifest. The runner checks the manifest before loading the official compressor.

The forward launcher resolves these from `STAGE2_X7_CHECKPOINT` and `STAGE2_X7_CHECKPOINT_MANIFEST`. Those study checkpoint values are intentionally **not** filled by this engineering PR. X7 therefore remains `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`.

The engineering smoke creates a tiny deterministic local GPT-2-format checkpoint solely to exercise the official LLMLingua model-loading and compression code path. That checkpoint is explicitly marked non-study and can never satisfy the future study checkpoint gate.

## 3. External observation

The passive observer is called only after `PromptCompressor.compress_prompt` has returned. It stores immutable copies of the already-used compressor input and already-returned result. It cannot influence token ranking, compressor output or prompt construction.

Compression itself is part of X7 and therefore legitimately changes the model-visible context. Monitoring is not.

## 4. Non-study verification

Workflow `36132656916` on candidate commit `f73b11b1f7136917cd47052c88a296c7b5d9fae5` checked out the exact upstream LLMLingua source commit, installed the official package as version `0.2.2`, created a six-file deterministic tiny local checkpoint and ran the official `PromptCompressor` on CPU.

The scripted T3 comparison finalized in one turn for both the direct frozen host and X7 host with identical checkout effects. X7 performed one official compression call and the passive observer sealed three evidence files. The tiny engineering checkpoint produced 79 origin tokens and 135 output tokens; this smoke is an API/control-boundary test, **not** a compression-efficiency measurement, so the token ratio is not scientific evidence. Final checkout digest: `15200a4ce5b6a09127f25371b55d9b4ae3b1f2071af78c3a7f37b6fcad8303e2`.

## 5. Forward state

X1, X4, X5 and X7 are `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`. X2, X3 and X6 remain `PENDING_NATIVE_RUNNER`.

No natural cell is open. X7 additionally requires the study checkpoint manifest to be frozen before real-provider subject readiness can be considered.

Stage-II natural trajectory count remains **zero**.
