# Minimal Experimental State-Control Layer v0.1

Status: OFFLINE ENGINEERING / NOT SUBJECT EVIDENCE  
Date: 2026-09-16

## Purpose

This layer turns the Arena into a more controllable experimental object without replacing the Free-Agent baseline or importing a production engineering system.

Its job is limited to:

`Observe → Freeze → Replay deterministic Arena state → Branch → Intervene → Freeze branch evidence`

It is an experimental instrument, not a Reality Bias category and not a product framework.

## Scientific boundary

- Subject prompts do not receive Escape/C/P/R labels from this layer.
- Existing frozen traces are not rewritten.
- The baseline remains intervention-off unless a named experimental protocol enables a branch/intervention.
- A deterministic Arena-state replay is **not** a replay of provider-internal randomness or hidden model state.
- New branch behavior is new evidence and must receive its own run/branch identity.

## Objects

### State Snapshot

`arena.experimental_control.capture_state(...)` freezes the deterministic Arena runtime state, including:

- shared state and metadata;
- FINAL state;
- active Agents;
- inboxes and queue;
- recorded events;
- invocation/message/execution ledgers;
- turn and sequence counters;
- late-event state;
- termination/failure/budget state.

Each snapshot has a content-derived `state_hash`.

### State Restore

`restore_state(...)` verifies the snapshot hash and reconstructs recorded Arena state.

Provider state remains external, so repeated continuations from the same parent are treated as repeated probabilistic branches, not byte-identical model replay.

### Branch Manifest

Each branch binds:

- parent trace hash;
- parent state hash;
- anchor reference;
- intervention specification and hash;
- branch ID;
- replicate index;
- optional model/config/code identity.

The original trajectory is immutable.

### Minimal Commit Gate

`decide_commit(...)` provides a fail-closed deterministic gate for R5 experiments. It can check:

- allowed action type;
- Authority class;
- source-ref requirement;
- expected parent-state hash.

The gate is **not enabled in the Free-Agent baseline**. It only exists as an explicit intervention condition.

### State Intervention

v0.1 intentionally supports only narrow deterministic state interventions:

- set one shared-state value;
- remove one shared-state key;
- downgrade/change one state-status marker;
- change explicit termination state for controlled recovery tests.

Broader interventions require a new version and protocol.

## R5 use

Preferred contrast:

`same parent snapshot`

→ branch A: original continuation

→ branch B: exactly one preregistered change

Examples:

- downgrade a candidate FACT to provisional;
- remove one source-derived state key;
- require expected-state-hash commit;
- later versions may block one invocation edge or reopen permission.

Compare proposal Jump, realized Jump, penetration depth, descendants and resource cost separately.

## R6 use

Create recovery branches from several distances after a Jump:

- immediately after Jump;
- after first operational commit;
- after shallow propagation;
- after multiple descendants;
- after a retrospective challenge.

The layer preserves the original lineage so recovery cost can be measured without overwriting history.

## R7 use

This layer is also the control substrate for a later structured/system-owned-routing condition. That condition should be implemented as a small experimental policy over stage/edge/handoff state, not as a production workflow system.

## Validation

Engineering validation is provided by:

- `arena/tests/test_experimental_control.py`
- `arena/config/experimental_control_v0.1.json`

Passing these tests proves deterministic snapshot/hash/branch/gate mechanics only. It is not scientific evidence that Reality Bias exists or that an intervention works on a real model.
