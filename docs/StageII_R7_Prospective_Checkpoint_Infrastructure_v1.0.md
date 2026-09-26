# Stage-II R7 Prospective Checkpoint Infrastructure v1.0

Date: 2026-09-26  
Status: **ENGINEERING INFRASTRUCTURE FROZEN / NO SCIENTIFIC SUBJECT RUN**

## 1. Why this layer exists

The first Stage-II natural matrix preserved enough evidence for process observability and, in X1, deterministic application-state reconstruction. It did not pre-register framework-native resumable checkpoints at arbitrary historical prefixes.

R7 therefore adds a prospective checkpoint layer before any new repair experiment.

This layer does not retrofit the original 21 trajectories. It prepares a new prospective evidence group in which the monitor can save a legitimate parent before a repair branch is needed.

process observability != application-state reconstructability != framework-native resumability.

## 2. Scientific boundary

The checkpoint system is external experiment infrastructure. It must not modify AutoGen or MetaGPT semantics, alter A2A protocol semantics, bypass MCP boundaries, rewrite RAG/MemoryBank/LongLLMLingua internal information state, call the scientific subject to manufacture a checkpoint, or back-fill a checkpoint into the original 21 natural paths.

The prospective layer may save only public/native framework state, Stage-II-owned host/service application state, application checkout state, model-visible context evidence/hash, remaining-horizon metadata, and immutable references/hashes to foreign information carriers.

## 3. Content-addressed registry

stage2/r7_checkpoint_v1/common.py provides a content-addressed checkpoint registry.

Every checkpoint binds system id, prospective group/run ids, task/event refs, adapter id, framework binding, native-state hash, application-state hash, model-visible-context hash, remaining horizon, external-carrier references, replication metadata and restore capability.

Application snapshots are copied and re-hashed. External carriers are verified but never restored by mutation; a mismatch must become CHECKPOINT_ENVIRONMENT_MISMATCH.

## 4. AutoGen adapter

X1 uses the pinned AutoGen AgentChat public Team.save_state and Team.load_state APIs at upstream commit 027ecf0a379bcc1d09956d46d12d44a3ad9cee14.

The adapter does not inspect or modify AutoGen private state. The engineering smoke populates a non-empty native Swarm history using the deterministic Replay client, freezes native plus checkout state, constructs a fresh Swarm, restores through Team.load_state and verifies the re-serialized state hash. No provider call is used.

## 5. MetaGPT adapter

X2 uses MetaGPT Environment.model_dump, Environment constructor deserialization and Role serialization at upstream commit 11cdf466d042aece04fc6cfd13b28e1a70341b1f.

The Stage-II wrapper adds an experiment-owned runtime envelope containing turn budget, current turn, history, task state and terminal state. Conformance checks both native Environment public serialization and the actual nine-role Stage2MetaRole environment plus runtime envelope. Provider/checkout bindings are rebound through constructor inputs rather than hidden framework mutation.

## 6. A2A adapter

A2A protocol commit 173695755607e884aa9acf8ce4feed90e32727a1 and SDK commit 0d5473ca4fa6d40034a6a7c8d65bce5cd85d8167 remain unchanged.

A2A defines transport, not a universal checkpoint for agent application memory. The prospective Stage-II extension therefore adds an out-of-band save/load API only to the experiment-owned role-service application state. It captures all nine role-service session states at quiescent boundaries. It adds no A2A RPC method and changes no Agent Card, JSON-RPC, SendMessage, task or artifact semantic.

## 7. X4-X7 hosted layers

The common software-engineering host can save/restore its Stage-II-owned queue, inbox, history, answer/stop state and runtime budget.

MCP, RAG, MemoryBank and LongLLMLingua stay outside writable checkpoint state. They contribute only immutable reference/hash bindings.

## 8. Checkpoint controller

stage2/r7_checkpoint_v1/controller.py gives the external monitor a checkpoint ledger.

Pre-registered full boundaries are: task start; after native model turns at quiescent boundaries; after state-changing native actions at quiescent boundaries; first monitor repair-eligible point; immediately before repair; immediately after repair; terminal.

The controller tracks model-decision sequence. A repair parent is valid only when the first eligible checkpoint is FULL_NATIVE and no uncheckpointed model decision occurs after it.

## 9. Repeatability / replication design

The manifest includes group/run/framework/task/role/subject and version bindings so later evidence accumulates as prospective replicate groups instead of manufactured reruns of one old output.

Intended group naming is StageII-R7-G1, StageII-R7-G2, StageII-R7-G3 and so on. The original 21-cell matrix remains immutable.

## 10. Conformance meaning

Checkpoint conformance is an engineering prerequisite, not a scientific result. Passing deterministic smoke tests establishes that the checkpoint/restore mechanism works without subject-model calls. It does not establish future CPR occurrence, repair success, framework ranking or causal effects.

## 11. Next handoff

After checkpoint conformance is frozen, the next operation is Stage-II R7 Prospective Repair Validation Group 1 contract freeze.

The prospective chain is:

new natural prospective path -> checkpoint recorder active from task start -> external structural monitor -> first eligible monitor-derived package -> verified full parent checkpoint -> natural A continues -> one repaired B continuation -> repair executor exits -> external monitor continues -> independent semantic audit -> A/B process comparison.

No prospective scientific subject call is authorized by this infrastructure document alone.
