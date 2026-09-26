# Stage-II R7 Prospective Checkpoint Conformance Report v1

Date: 2026-09-26  
Status: **ENGINEERING CONFORMANCE PASS / NO SCIENTIFIC SUBJECT RUN / ACTIVE REPAIR CLOSED**

## 1. Purpose

The previous Stage-II R7 readiness audit showed that historical process observability did not automatically provide a legal native same-parent resume point. This phase therefore builds and tests checkpoint infrastructure before any prospective repair experiment.

The original 21 natural trajectories remain immutable and are not retrofitted.

## 2. Test boundary

Conformance was executed against pinned framework versions using deterministic or non-study fixtures only.

- provider calls: **0**;
- evaluator calls: **0**;
- scientific subject trajectories: **0**;
- active repairs: **0**;
- natural reruns: **0**.

The conformance workflow head was `74a67eaedf851ca218dcfcb46aa530043dfce3da`, run `36228005932`.

## 3. Common checkpoint registry

The new registry content-addresses native state, application checkout state, model-visible-context evidence, remaining horizon, framework binding, replication metadata and read-only external-carrier references.

Application snapshots are restored only after hash verification.

Foreign information systems are not restored by mutation. Their references/hashes are compared; mismatch is an environment mismatch rather than permission to rewrite the external system.

Registry/X4-X7 host conformance: **PASS**.

- host runtime state round-trip: PASS;
- application restore: PASS;
- foreign carrier policy: VERIFY_ONLY;
- checkpoint hash: `26671b9de5df13c3a2be598288af46a3dc62ecc29420799edb859315a081a139`.

## 4. X1 AutoGen

AutoGen uses the pinned public AgentChat Team state APIs:

- `Team.save_state`;
- `Team.load_state`.

The smoke populates a non-empty deterministic Swarm state, captures it, constructs a new Swarm, restores through the public API, then re-serializes and compares the native-state hash.

Result: **PASS**.

- native-state round-trip: PASS;
- application-state round-trip: PASS;
- provider calls: 0;
- checkpoint hash: `15ed5ac42a19c459c1056a227aad87f40210327b2f0ae9ba08ac84415c3c7c88`.

Boundary: AutoGen's own documentation cautions against saving an actively running team. Stage-II therefore treats a full AutoGen checkpoint as valid only at a non-running or explicitly proven quiescent native boundary. The prospective experiment must not silently treat an arbitrary in-flight stream event as a resumable parent.

## 5. X2 MetaGPT

MetaGPT uses its public model serialization behavior:

- `Environment.model_dump`;
- `Environment(**state, context=context)`;
- native Role model serialization.

Stage-II additionally freezes its own runtime envelope: turn budget/count, task, terminal state and history. Provider and checkout object bindings are rebound through constructor inputs rather than serialized as hidden framework internals.

Result: **PASS**.

- upstream Environment public round-trip: PASS;
- Stage-II nine-role environment round-trip: PASS;
- Stage-II runtime-envelope round-trip: PASS;
- provider calls: 0;
- checkpoint hash: `0cabc99d26f1e882956ada5ba1ec32c3aa618ed36256db1202acfd3140907796`.

MetaGPT serializes native set-like fields such as role addresses/watch sets and message send targets as JSON lists. Their element order is not process semantics, so the checkpoint adapter canonicalizes only those set-like fields before content addressing. Ordered message/history lists remain ordered and are not sorted.

## 6. X3 A2A

A2A protocol and SDK remain unchanged.

The prospective adapter checkpoints the Stage-II-owned role-service application/session state out-of-band at a quiescent service boundary. It does not add an A2A RPC, Agent Card field, JSON-RPC method, SendMessage semantic, task semantic or artifact semantic.

Result: **PASS**.

- nine role-service states round-trip: PASS;
- A2A protocol modified: **false**;
- provider calls: 0;
- checkpoint hash: `af2c8b5724e00010b587d2214b6d3791fad72cf6ea10194345513dbaa62f4fd8`.

## 7. X4-X7 external-layer boundary

The Stage-II-owned software host may checkpoint its queue, inbox, history, runtime budget and application checkout.

The following remain outside writable repair/checkpoint state:

- MCP protocol/security/resource boundary;
- RAG corpus/index/embedding/retrieval state;
- MemoryBank stored memory/index/strength/recall state;
- LongLLMLingua model/checkpoint/compression behavior.

They may contribute only immutable reference/hash bindings.

## 8. Checkpoint controller

The monitor-side controller now freezes checkpoint references together with a monotonically increasing model-decision sequence.

Pre-registered checkpoint boundaries include task start, safe native turn/action boundaries, first repair-eligible point, pre-repair, post-repair and terminal.

A repair parent is eligible only if it is `FULL_NATIVE` and no uncheckpointed model decision has occurred after the selected checkpoint.

This prevents a stale checkpoint from being relabeled as the exact parent of a later probabilistic decision.

## 9. Reproduction / repeated groups

The manifest binds group id, run id, framework version/commit, task id, checkpoint schema version, monitor-rule version and repair-package version.

Future repeated evidence is therefore organized as new prospective groups such as `StageII-R7-G1`, `G2`, `G3`, rather than as reruns intended to manufacture the same output.

## 10. What is now ready

The infrastructure is now ready to pre-save legal checkpoint state during a new prospective trajectory.

This does **not** yet authorize a scientific subject run.

The next experiment contract must freeze exactly where each native condition is checkpoint-safe, how the external monitor selects the first repair-eligible pressure/support episode, and how natural A and repaired B continue from one already-saved parent without changing framework/protocol/security boundaries.
