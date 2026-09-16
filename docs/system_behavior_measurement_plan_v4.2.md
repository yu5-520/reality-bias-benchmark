# Reality Bias System Behavior Measurement Plan v4.2

Date: 2026-09-17  
Status: FORWARD / PROCESS-REALITY INERTIA MEASUREMENT  
Depends on: `docs/R_Plan_v4.2.md`, `theory/theory_contract_v0.6.md`.

## 1. Measurement hierarchy

```text
SystemTrajectory
  -> raw BehaviorEvent / StateTransition
  -> natural Jump candidate
  -> source-backed lineage
  -> inherited inertia
  -> post-reorganization inertia transition
  -> structured recovery/control evidence
  -> CPR semantic candidate/adjudication
```

Terminal outcome remains an auxiliary measurement.

## 2. Raw facts and derived structure

### Raw observable layer

Record, where supported by the runtime version:

- actor / role / turn;
- model input and raw output identity;
- parsed action;
- message send/delivery/read;
- invocation and execution;
- shared-state read/write/revision;
- before/after state identity or hash;
- FINAL/reopen/revision operations;
- error, censoring and remaining-work state.

### Derived structural layer

Derive only from recorded evidence:

- Jump candidates;
- source-backed lineage;
- descendant relation;
- affected actor/field relation;
- branch / merge / re-entry;
- path family;
- inherited inertia;
- dependency closure;
- affected/preserved recovery scope.

Derived structure must preserve evidence refs back to raw facts.

## 3. R2 — emergence

For each natural Jump candidate record:

- event / turn / actor;
- boundary and state diff;
- source refs;
- candidate structural family;
- pre/post state identity where available;
- whether the candidate was naturally realized or directly exposed to an experimental variable.

Do not infer semantic C/P/R from structural detection alone.

## 4. R3 — inheritance / propagation

Trace exact source-backed inheritance through message, invocation, shared-state visibility, state revision, read-to-turn and action relations.

Measure:

- descendants;
- affected actors;
- field lineage;
- role crossings;
- depth and reach;
- branch points;
- merge points;
- loops / re-entry;
- path-family continuation.

Activity volume alone is not inertia.

## 5. R4 — retrospective dynamics

Locate challenge/reopen/review/correction windows and derive structural candidate outcomes without prematurely assigning CPR truth.

Record:

- prior lineage entering the retrospective boundary;
- correction/challenge operation;
- downstream persistence;
- disappearance;
- regeneration;
- secondary Jump formation;
- re-entry and later inheritance.

## 6. R5 — one-shot evidence boundary

The direct experimental record must preserve:

- same parent/start-state identity for matched A/B;
- target J0/state key/source event;
- original and one-shot experimental state;
- exactly one experiment-origin exposure in B;
- zero direct experiment-origin exposure in A;
- consumption immediately after that exposure;
- zero experiment-origin reinjection;
- `persistent_state_mutation = false`;
- free downstream continuation after consumption.

R5 primary endpoint: **paired structural reorganization**, not persistent control.

## 7. R5 structural scales

### 7.1 Jump recurrence

Classify downstream Jump candidates as:

- `DESCENDANT_REJUMP`;
- `INDEPENDENT_NEW_JUMP`;
- `LINEAGE_UNRESOLVED`.

Record count, first distance, actor/role/boundary distance, candidate-family continuity/transformation, and direct-exposure status.

### 7.2 Inherited path response

Record:

- shared structural prefix;
- first structural divergence;
- first reconvergence if observed;
- post-exposure path overlap;
- root reach/depth;
- role/Agent activation continuity;
- observed path-family changes.

### 7.3 Path topology

Compare branch, merge, re-entry, cross-Agent relation, reachable descendants and canonical path-family structure.

A realized path is not an exhaustive possibility space.

## 8. R6 — post-reorganization inertia dynamics

R6 retains the detailed historical questions but groups them under a higher-order inertia construct.

### 8.1 Jump continuation state

For each post-J0 / post-divergence window record:

- no later Jump observed within uncensored horizon;
- descendant Jump observed;
- delayed descendant Jump observed;
- independent new Jump observed;
- lineage unresolved.

### 8.2 Jump-family continuity

Where a later Jump is source-backed, classify:

- `SAME_FAMILY_CONTINUATION`;
- `TRANSFORMED_FAMILY_CONTINUATION`;
- `INDEPENDENT_FAMILY`;
- `UNRESOLVED`.

### 8.3 Inheritance state

Measure whether the J0-derived or reorganized state is:

- directly inherited;
- indirectly inherited through another field/message/Agent;
- transferred to another actor/field lineage;
- no longer source-backed downstream;
- censored before resolution.

### 8.4 Retrospective return

At a valid retrospective/challenge/reopen boundary record:

- whether prior Jump-derived structure returns;
- whether return is same-family or transformed;
- whether return is source-backed to the prior lineage;
- whether the returned state is inherited again;
- whether it produces further descendant Jumps.

Do not call every return R-positive; semantic R remains an R8 adjudication question.

### 8.5 Higher-order inertia summaries

The following labels are deterministic structural summaries only when their preregistered conditions are met:

- `RETAINED`;
- `DECAYED_OR_EXTINCT`;
- `DEFLECTED`;
- `TRANSFERRED`;
- `TRANSFORMED`;
- `REPLACED`;
- `RECONSTRUCTED_OR_HYBRID`;
- `DELAYED_REEMERGENCE`;
- `REBOUND_OR_REGENERATION`;
- `RECONVERGED`;
- `UNRESOLVED_OR_CENSORED`.

These summaries must be backed by the lower-level Jump/lineage/topology record; they are not semantic value judgments.

### 8.6 Matched A/B inertia comparison

Compare original/control inertia and altered/intervention inertia at matched downstream distance where possible:

- turn distance;
- descendant generation/depth;
- event distance;
- equivalent retrospective boundary.

Report asymmetry when horizons differ or a branch terminates early. Do not convert censoring to extinction.

## 9. R7 — structured inertia recovery/control measurement

R7 uses the same passive observability layer across conditions. Measurement capacity must not differ merely because one condition activates ALR recovery.

### 9.1 Recovery-scope identity

Record:

- localization Jump `J0`;
- target risk-bearing field(s);
- source evidence refs;
- derived affected dependency closure;
- affected nodes/fields/Agents;
- preserved nodes/fields/Agents;
- recovery-routing identity/version;
- revision identity/hash for repaired field states where implemented.

### 9.2 Iterative recovery loop

For every recovery round record:

- round index;
- observed residual/recurrence trigger;
- repaired field/state;
- structured handoff/routing action;
- downstream descendants reached after repair;
- new residual/recurrence state;
- secondary Jump if any;
- decision to continue recovery or release.

A single repair round is not automatically evidence of inertia control.

### 9.3 Risk-control metrics

Candidate deterministic measurements include:

- risk-bearing descendant count;
- risk-bearing reach/depth;
- affected Agent count;
- residual field count;
- recurrence/rebound count;
- secondary Jump count;
- recovery rounds;
- structural distance to containment/release;
- old-inertia lineage survival after each round.

### 9.4 Freedom-preservation metrics

Also record:

- unaffected node preservation ratio/count;
- unaffected branch preservation;
- unnecessary reopened node count;
- full-rerun avoided / invoked;
- non-risk Agent participation retained;
- non-risk path families retained;
- structured-recovery scope as a fraction of observed graph.

Risk suppression without preservation evidence cannot alone support a useful localized-control claim.

### 9.5 Release condition

A forward R7 run must preregister a release rule. The rule may combine structural conditions such as:

- no source-backed risk-bearing descendant remains within the active affected closure;
- required field revisions have propagated to all currently reachable affected descendants;
- no recurrence trigger is observed within a preregistered observation window;
- remaining uncertainty is explicitly censored/unresolved rather than declared absent.

After release, later recurrence remains measurable evidence.

## 10. Passive field persistence and ALR-governed propagation

If a persistent-field comparator is used, distinguish:

- `EXPERIMENT_MAINTAINED_FIELD_PERSISTENCE` — a field/signal is continuously present due to experimental delivery;
- `ALR_GOVERNED_FIELD_PROPAGATION` — repaired/revised field state propagates with explicit lineage/provenance under structured recovery routing;
- `ENDOGENOUS_INHERITED_INERTIA` — downstream continuation after the experimental mark has left active context.

Do not merge these evidence types.

## 11. R8 — semantic layer

CPR is applied after structural evidence is frozen.

Required statuses:

- `STRUCTURAL_CANDIDATE_ONLY`;
- `ADJUDICATED_C` / `ADJUDICATED_P` / `ADJUDICATED_R` as permitted by the review contract;
- `ADJUDICATED_NON_CPR`;
- `REVIEW_DISAGREEMENT`;
- `UNRESOLVED`;
- `NOT_ADJUDICATED`.

Reviewer packets should contain bounded candidate windows plus the necessary source-backed lineage, not require unrestricted rediscovery of the entire trajectory.

## 12. Terminal outcome and engineering diagnostics

Retain separately:

- terminal task outcome;
- final-state equivalence/difference;
- turns/calls/tokens/spend;
- latency;
- reopened nodes;
- recovery execution cost.

These are auxiliary unless explicitly preregistered as secondary engineering outcomes.

## 13. Missingness and censoring

- censored != zero;
- missing != no;
- no descendant Jump in a censored window != extinction;
- no retrospective opportunity != failed recovery;
- no recurrence within a bounded post-release window != proof of permanent elimination;
- fields absent from historical source versions remain `NOT_RECORDED_IN_SOURCE_VERSION`.

## 14. Discovery / validation / semantic separation

- Discovery evidence may motivate Jump/inertia/CPR definitions.
- Structural definitions and detectors must be frozen before prospective validation.
- Semantic adjudication must not retroactively create structural events.
- Existing formal evidence protected by a no-new-adjudication freeze remains unchanged.
