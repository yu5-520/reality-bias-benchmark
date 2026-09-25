# Stage-II X6 official MemoryBank memory attachment — R Plan v7.7

Date: 2026-09-25. Status: **X6 NATIVE RUNNER VERIFIED; STUDY EMBEDDING + SUBJECT GATES CLOSED; ZERO NATURAL TRAJECTORIES**.

v7.7 continues the heterogeneous v7 architecture without changing T1–T3, the nine Software Engineering roles, the frozen checkout, the DeepSeek subject profile, the seven X definitions, or the one-natural-trajectory-per-cell rule.

## 1. X6 remains a memory capability

The frozen `software_engineering_host_v1` continues to own role scheduling, mailbox behavior, actions and checkout operations. X6 changes only the memory write/retrieve boundary around each role's model turns.

The X6 runner binds the official `zhongwanjun/MemoryBank-SiliconFriend` source at commit `cf61c4196e4cfdb0f2b7a0316249fa40312dc3a9`. Each frozen Software Engineering role receives its own persistent MemoryBank file and FAISS index. After a role model turn, that exchange is written into the role's memory and the upstream MemoryBank loader/index path rebuilds the searchable state. On a later turn by the same role, the upstream `LocalMemoryRetrieval.search_memory` result is exposed under `memorybank_recall` in that role's model-visible prompt.

The upstream MemoryBank mechanism therefore retains ownership of memory-document construction, vector retrieval, forgetting-curve metadata, recall-strength reinforcement and persistence. X6 glue maps the repository's underscore-containing role IDs to reversible hyphenated MemoryBank user keys because the pinned upstream implementation parses its own `memory_id` fields with underscore separators. That boundary mapping changes no frozen role identity presented to the subject or scheduler.

## 2. Study embedding boundary

A working runner does not authorize a natural X6 trajectory. Formal collection additionally requires the exact upstream source checkout plus a local embedding checkpoint and a complete file-level SHA-256 manifest.

The forward runner resolves these through `STAGE2_X6_UPSTREAM`, `STAGE2_X6_EMBEDDING_MODEL`, and `STAGE2_X6_EMBEDDING_MANIFEST`. The study embedding is intentionally not frozen by this engineering PR, so X6 remains `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`.

The engineering smoke constructs a tiny deterministic BERT-format embedding checkpoint solely to exercise the official MemoryBank FAISS write/retrieve/reinforcement path without downloading a study model. That synthetic embedding is never authorized for natural collection.

## 3. Observation remains outside the memory mechanism

The passive observer is called only after upstream memory operations have returned. It copies the already-used query, returned recall result, pre/post recall memory bytes, and post-rebuild memory bytes. Those copies are never fed back into vector ranking, memory-strength updates, role scheduling, or prompt construction.

The memory itself is part of X6 and legitimately changes later role context. Monitoring is not.

## 4. Non-study verification

Workflow `36137509369` on candidate commit `81de62483236f8a74cd09b40668ee1f025b5a7ce` passed with no paid subject call.

The scripted T2 comparison finalized in two turns for both the direct frozen host and the X6 host with the same terminal answer and identical checkout effects. X6 wrote two role exchanges, performed one upstream MemoryBank retrieval on the second turn, recalled one prior memory item, and persisted the recalled item's `memory_strength` increase from 1 to 2 with the frozen recall date. Six passive evidence files were sealed. Final checkout digest: `15200a4ce5b6a09127f25371b55d9b4ae3b1f2071af78c3a7f37b6fcad8303e2`.

This is an engineering conformance test of the native memory path, not evidence about MemoryBank retrieval quality or downstream scientific effects.

## 5. Forward state

X1, X3, X4, X5, X6 and X7 are now `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`. X2 remains `PENDING_NATIVE_RUNNER`.

No X6 cell is open. X6 must first freeze the study embedding manifest and then pass a separate real-provider subject-readiness check on the exact forward execution commit.

Stage-II natural trajectory count remains **zero**.
