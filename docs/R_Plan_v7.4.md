# Stage-II X5 frozen RAG context attachment — R Plan v7.4

Date: 2026-09-25. Status: **X5 NATIVE RUNNER VERIFIED; SUBJECT GATE CLOSED; ZERO NATURAL TRAJECTORIES**.

v7.4 continues the heterogeneous v7 architecture. T1–T3, the nine Software Engineering roles, the frozen checkout, the DeepSeek subject profile, the seven X definitions and the one-natural-trajectory-per-cell rule are unchanged.

## 1. X5 stays a retrieval/context capability

X5 is not a scheduler and is not converted into a communication protocol. The frozen `software_engineering_host_v1` continues to own role scheduling, mailbox behavior, actions and checkout operations.

The X5-specific attachment uses the already frozen in-repository implementation `stage2.retrieval.retrieve` with implementation SHA-256 `baf19cd7f7dde0a2f7ebfde254bffac6690e018b88d8d9ea4a811d37a53b12c4`.

For each model turn, the frozen user request is used as the retrieval query, the frozen retrieval limit is three, and the returned ranked hits are exposed under `retrieved_context` in the role's model-visible prompt. This preserves the v6 X5 scientific condition while removing the old capture/evidence machinery from execution.

## 2. Corpus and observation boundary

The RAG corpus remains the frozen `stage2/fixtures/project` source set. Every indexed source is checked against the already frozen fixture hashes before execution, and every returned hit carries its source path and SHA-256.

`PassiveEventObserver` records only post-return copies of the already-used query serialization and already-returned ranked hits. Observation therefore does not participate in ranking, select hits, alter the query, or rewrite the context. The retrieved content itself enters the model prompt because that is the X5 condition; audit metadata does not.

## 3. Non-study verification

Workflow `36131773869` on candidate commit `c8db6e1b3188de7b05e6bfb521aa2a148aa9596e` passed without a paid subject call.

The scripted T3 smoke compared the direct frozen host with the X5-attached host. Both finalized in one turn with identical checkout effects. X5 performed one retrieval, returned three frozen hits — `README.md`, `versions/after.json`, and `checkout_app/checkout.py` — and exposed those hits only in the X5 model-visible prompt. The passive observer sealed three evidence files. Final checkout digest: `15200a4ce5b6a09127f25371b55d9b4ae3b1f2071af78c3a7f37b6fcad8303e2`.

## 4. Forward state

X1, X4 and X5 are now `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`. X2, X3, X6 and X7 remain `PENDING_NATIVE_RUNNER`.

No natural cell is open. X5 must pass a separate real-provider subject-readiness gate on the exact forward execution commit before any X5–T1/T2/T3 cell may be reserved.

Stage-II natural trajectory count remains **zero**.
