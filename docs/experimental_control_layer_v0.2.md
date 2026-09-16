# Minimal Experimental State-Control Layer v0.2

Status: OFFLINE ENGINEERING / NOT SUBJECT EVIDENCE  
Date: 2026-09-16  
Supersedes for forward branch work: `docs/experimental_control_layer_v0.1.md`

Historical v0.1 documents and manifests remain preserved.

## 1. Purpose

The control layer turns recorded Arena state into a branchable experimental object:

`Observe → Freeze → Replay deterministic Arena state → Intervene → Branch → Freeze new evidence`

It is an experiment instrument only. It is not a Reality Bias category, a production control plane, or a semantic evaluator.

## 2. Critical v0.2 correction — parent state is not branch-start state

v0.1 bound a branch to a `parent_state_hash`, but after a deterministic intervention the actual continuation may begin from a different state.

That created an ambiguity:

`frozen parent S_t → intervention ΔX → branch start S_t'`

where:

`hash(S_t) != hash(S_t')`

v0.2 therefore records both identities explicitly:

- `parent_state_hash` — the immutable state selected before intervention;
- `branch_start_state_hash` — the exact state supplied to the continuation runtime;
- `intervention_applied_before_continuation` — true iff those hashes differ.

This preserves the causal form:

`same parent history + one explicit intervention → changed branch start → continuation`

without relabeling the post-intervention state as if it were the original parent.

## 3. State Snapshot

`capture_state(...)` freezes deterministic Arena runtime state including:

- shared state and metadata;
- FINAL state;
- active Agents;
- inboxes and queue;
- recorded events;
- invocation/message/execution ledgers;
- turn/sequence counters;
- late-event state;
- termination/failure/budget state.

Every snapshot receives a content-derived `state_hash`.

Provider-internal randomness or hidden model state is not captured.

## 4. Branch Manifest v0.2

Forward branch manifests use:

`RB-EXPERIMENTAL-BRANCH-v0.2`

and bind:

- parent trace hash;
- parent state hash;
- branch-start state hash;
- parent and branch-start anchor refs;
- intervention spec/hash;
- whether the intervention changed the start state;
- branch ID and replicate index;
- optional model/config/code identity;
- explicit `provider_internal_state_replayed = false`.

Schema:

- `schemas/experimental_branch_manifest_v0.2.schema.json`

The historical v0.1 schema remains preserved for old engineering records.

## 5. Runtime validation

`run_arena_once(...)` validates the supplied continuation snapshot against `branch_start_state_hash` while preserving the original `parent_state_hash` in branch evidence.

A post-intervention branch trace therefore exposes both:

- where the branch came from;
- what exact state the model actually received when the branch resumed.

This distinction is required for R5 causal interpretation.

## 6. Offline R5/R6 preflight

Current offline implementation:

- `arena/branch_recovery_preflight.py`
- `arena/tests/test_branch_recovery_preflight.py`

The deterministic fixture:

1. creates a baseline multi-Agent trajectory;
2. freezes a structural-only anchor after a recorded state write;
3. creates a control branch from the unchanged parent;
4. creates an intervention branch by changing exactly one state-status marker;
5. continues both branches with an engineering-only state-responsive provider;
6. verifies that both branches retain the same parent hash but have different branch-start hashes;
7. verifies that the downstream continuation can observe the changed state;
8. emits a recovery record with semantic R status left `NOT_ADJUDICATED`.

This proves instrumentation behavior only. It does not estimate real-model Jump probability or intervention effectiveness.

## 7. Scientific boundary

- Existing frozen subject traces are never rewritten.
- New branch behavior is new evidence.
- Structural anchor selection remains frozen before branch outcomes are visible.
- Semantic Reviewer labels do not select confirmatory anchors.
- A deterministic state replay is not a claim of provider-randomness replay.
- The baseline Free-Agent condition remains intervention-off unless a named protocol activates a branch condition.
- Paid provider execution remains separately authorized.

## 8. Forward R5 use

The preferred confirmatory form remains:

`same frozen parent + one preregistered ΔX → repeated branch continuations`

Candidate ΔX classes:

- epistemic-status downgrade;
- one source/provenance restoration/removal;
- one Authority/commit gate;
- one invocation-edge block;
- one temporal reopen/version rule.

Primary measurements must keep proposal generation separate from operational realization.

## 9. Forward R6 use

Recovery branches can be created at increasing distances after a Jump candidate while preserving parent/start identity separately.

The recovery layer records structural recurrence and provenance reconstruction separately from semantic R regeneration. Semantic regeneration remains deferred unless independently adjudicated.
