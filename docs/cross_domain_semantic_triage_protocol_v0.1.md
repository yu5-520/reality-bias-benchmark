# Cross-Domain Localized Semantic Triage Protocol v0.1

Date: 2026-09-19  
Status: FORWARD / DETERMINISTIC FROZEN-EVIDENCE TRIAGE

## 1. Purpose

This stage compresses the first held-out cross-domain natural cohort into a bounded localized semantic-audit queue.

It operates only after:

`natural subject -> raw evidence freeze -> structural derivation -> case candidate ledger -> first-round registry`.

It makes zero provider/evaluator calls and does not execute R5, R7 or R8.

## 2. Input boundary

The source must be one completed six-wave first-round workflow with:

- 90 preserved trajectories;
- six frozen wave evidence batches;
- one execution SHA;
- one authorization event;
- zero runner errors for the completed first round.

Raw evidence and structural derivations remain immutable.

## 3. Why triage is required

A structural repair-anchor candidate is an observation surface, not a semantic finding.

The first held-out cohort may contain many addressable candidates per trajectory. Reviewing all candidates equally would overweight long/dense trajectories and turn structural density into an implicit semantic score.

Therefore the audit unit remains the **trajectory**, while deterministic anchor roles nominate a small set of locations inside each trajectory.

## 4. Frozen anchor roles

### FORMATION_ANCHOR

Select the earliest non-control structural repair-anchor candidate.

Purpose: inspect the earliest observed transition into a reusable/exposed shared-state structure.

### PROPAGATION_ANCHOR

Select the non-control candidate maximizing, in order:

1. distinct visible Agent count;
2. later visibility count;
3. activity after visibility;
4. earliest source event as tie-break.

Purpose: inspect the structurally widest downstream observation surface.

### AUTHORITY_REVIEW_ANCHOR

Select the earliest non-control candidate requiring authority review under the frozen status/lexical rule.

Priority:

1. status = `fact` while source basis/value explicitly contains a frozen uncertainty marker;
2. status = `provisional` or `unconfirmed`;
3. status = `unspecified`.

The marker list is frozen in `configs/v5_cross_domain_semantic_triage_v0.1.json`.

This role is **not** an authority-error label. It only marks where an auditor should inspect epistemic status.

## 5. Control-state handling

Generic control/version objects such as `status`, `state`, `decision_version`, `allocation_version`, `release_version`, and keys ending in `_version` / `.version` are down-ranked from primary selection when non-control candidates exist.

They remain in frozen evidence and may still be audited later.

## 6. Case packet

Each selected unique candidate records:

- source workflow lineage and evidence-batch hash;
- source run/domain/wave;
- content address and candidate ref;
- one or more triage roles;
- source event/turn/actor/key/status/basis/value;
- structural visibility counts and visible Agents;
- complete structural visibility rows;
- bounded downstream call summaries with exact turn/Agent/event windows;
- explicit semantic and authorization boundaries.

When multiple roles choose the same candidate, roles are merged into one case packet rather than duplicated.

## 7. Scientific boundary

Triage does **not** establish:

- semantic adoption;
- authority error;
- semantic transformation;
- semantic inheritance;
- System Inertia;
- CPR;
- causality;
- R5 eligibility;
- R7 repairability.

All selected cases remain:

`AWAITING_LOCALIZED_SEMANTIC_AUDIT / NOT_ADJUDICATED`.

## 8. Next stage

Localized semantic audit consumes the triage packets together with exact frozen raw evidence.

Only append-only semantic audit may move a source-bound case to:

- `ELIGIBLE_R5_ATOMIC_PROBE`; or
- `NOT_ELIGIBLE_R5`.

Natural-subject authorization never carries forward automatically.
