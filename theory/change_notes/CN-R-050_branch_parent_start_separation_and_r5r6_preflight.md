# CN-R-050 — Branch Parent/Start Separation and R5/R6 Preflight

Date: 2026-09-16  
Status: IMPLEMENTED OFFLINE / ZERO PROVIDER CALLS

## 1. Breakpoint found

While implementing a true R5 state intervention branch, the v0.1 branch contract exposed an ambiguity:

`frozen parent state → intervention → continuation start`

The original manifest recorded only `parent_state_hash` while `run_arena_once(...)` validated the actual continuation snapshot against that same field.

That is only correct when no intervention changes the state before continuation.

For a real state intervention:

`parent_state_hash != branch_start_state_hash`

Treating the modified state as the parent would erase the exact causal boundary the experiment is meant to preserve.

## 2. Correction

Forward branch manifests now use:

`RB-EXPERIMENTAL-BRANCH-v0.2`

with separate fields:

- `parent_state_hash`;
- `branch_start_state_hash`;
- `intervention_applied_before_continuation`.

`run_arena_once(...)` validates the supplied continuation snapshot against the branch-start hash while retaining the frozen parent hash in the resulting trace.

The historical v0.1 schema remains preserved.

## 3. Offline R5/R6 branch preflight

Implemented:

- `arena/branch_recovery_preflight.py`
- `arena/tests/test_branch_recovery_preflight.py`
- `docs/experimental_control_layer_v0.2.md`
- `schemas/experimental_branch_manifest_v0.2.schema.json`

The fixture performs:

`baseline → structural-only anchor → unchanged control branch`

and:

`same parent → one state-status intervention → changed branch start → continuation`

The continuation provider is deterministic and engineering-only. It reacts to the recorded state status so the preflight can verify that the intervention is visible downstream.

## 4. Evidence outcome

The preflight requires:

- both branches bind the same frozen parent state hash;
- the intervention branch has a different branch-start state hash;
- the control branch start equals the parent state;
- the intervention branch start equals the post-intervention snapshot;
- both continuations complete under the scripted fixture;
- downstream output reflects the changed state marker;
- anchor selection remains structural-only and outcome-blind;
- recovery semantic regeneration remains `NOT_ADJUDICATED`.

This is instrumentation evidence only.

## 5. Scientific implication

The correction matters because R5 is intended to approximate:

`Same history + One controlled intervention`

If the parent identity and the post-intervention start identity are collapsed into one field, that statement becomes mechanically unverifiable.

v0.2 makes the intervention boundary explicit and hash-addressable.

## 6. Non-retroactivity and API boundary

- No frozen historical subject trace was rewritten.
- No previous reviewer record was changed.
- No provider-internal state replay is claimed.
- No paid subject call occurred.
- No paid reviewer call occurred.
- Real R5/R6 execution still requires a separately frozen real-model protocol and explicit spending authorization.
