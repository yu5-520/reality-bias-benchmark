# Reality Bias System Behavior Measurement Plan v4.3

Date: 2026-09-17  
Status: FORWARD / PROCESS-REALITY STRUCTURAL-CONTROL MEASUREMENT  
Depends on: `docs/R_Plan_v4.3.md`, `theory/theory_contract_v0.7.md`.

## 1. Measurement hierarchy

```text
SystemTrajectory
  -> raw BehaviorEvent / StateTransition
  -> natural Jump candidate
  -> source-backed lineage
  -> inherited inertia
  -> post-reorganization inertia transition
  -> R7 structural-handling contrast
  -> localized recovery evidence
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
- invocation proposal/execution;
- shared-state read/write/revision;
- before/after state identity or hash;
- FINAL/reopen/revision operations;
- queue, pending work, error and censoring state.

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
- affected/preserved recovery scope;
- structural steering direction.

Every derived relation must preserve evidence refs back to raw facts.

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

Record count, first distance, actor/role/boundary distance, candidate-family continuity/transformation and direct-exposure status.

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

Candidate structural summaries:

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

These summaries require source-backed lower-level evidence.

## 9. R7 — structural inertia steering / localized recovery

R7 uses materially equivalent passive observability across all comparison arms. Differences in evidence capacity must not be mistaken for treatment effects.

### 9.1 Common frozen identity

Where feasible, each matched R7 set should retain:

- the same frozen parent state;
- the same J0 / source event;
- the same task and role pool;
- the same model/provider binding;
- the same semantic correction payload;
- the same passive observability schema;
- the same continuation horizon or explicit censoring rule.

### 9.2 C1 — One-Shot Free Continuation

Required direct-exposure fields:

- `experiment_origin_exposure_count = 1`;
- `reinjection_count = 0`;
- `persistent_experiment_field = false`;
- `active_alr = false`.

After consumption, downstream continuation is free.

Evidence type:

`ENDOGENOUS_INHERITED_INERTIA`.

### 9.3 C2 — Persistent Field Propagation

Record:

- field/signal identity;
- semantic payload hash;
- every node/turn at which the field remains available;
- exposure count;
- delivery path;
- whether the field was read/used where runtime support permits;
- downstream Jump/topology changes.

Evidence type:

`EXPERIMENT_MAINTAINED_FIELD_PERSISTENCE`.

Do not call C2 persistence endogenous inertia.

### 9.4 C3 — ALR Authority-Localized Recovery

Record the full recovery operator object:

- named authority/provenance condition;
- earliest authority-violating ancestor `n*`;
- source evidence refs supporting `n*`;
- dependency-closure algorithm/version;
- `Affected` node/field/Agent set;
- `Preserved` node/field/Agent set;
- repaired authority/provenance condition;
- old revision identity;
- new revision identity/hash;
- parent revision ref;
- reopened/re-executed subgraph;
- untouched preserved structure;
- downstream residual/recurrence/re-entry/reconstruction evidence.

Evidence type:

`ALR_LOCALIZED_STRUCTURAL_RECOVERY`.

### 9.5 R7-A — One-Shot vs Persistent Field

Compare at matched downstream distance:

- descendant Jump count/distance;
- root reach/depth;
- actor transition sequence;
- cross-Agent spread;
- branch/merge/re-entry;
- path-family distribution;
- state-lineage destination;
- reconvergence distance;
- terminal/process decoupling.

The objective is to distinguish endogenous path dependence from persistence created by continuous experimental delivery.

### 9.6 R7-B — Persistent Field vs ALR

The semantic payload should be matched as closely as possible.

Compare:

- affected descendant localization precision;
- preserved node/field/branch count or ratio;
- reopened node count;
- old-lineage survival;
- residual/recurrent lineage;
- re-entry topology;
- secondary Jump formation;
- path reconstruction;
- structural steering direction;
- reconvergence/recovery distance;
- terminal/process decoupling.

A difference is attributable to structural handling only to the extent that semantic content, parent/J0, observation and model conditions are matched.

## 10. Operationalizing structural direction

Structural steering direction may be represented through one or more preregistered observables:

- ordered actor transitions;
- edge-frequency or edge-family distribution;
- destination field/state lineage;
- information-flow destination;
- descendant-Jump location;
- re-entry actor/stage;
- path-family transition;
- stage progression;
- reconvergence location/distance.

The first paper may use categorical or graph-based descriptions. Literal vector arithmetic is not required.

## 11. ALR localization metrics

Candidate measurements include:

- `affected_precision` — proportion of reopened/recovered nodes that are inside the frozen source-backed closure;
- `preserved_node_ratio` — preserved nodes divided by total realized nodes in the comparison graph;
- `preserved_branch_ratio`;
- `unnecessary_reopen_count`;
- `recovery_scope_fraction`;
- `old_lineage_survival_count`;
- `post_recovery_reentry_count`;
- `secondary_jump_count`;
- `recovery_distance`;
- `recurrence_within_horizon`.

These metrics describe structure. They do not by themselves establish semantic CPR truth.

## 12. Proposal versus realization

Where ALR or another structural policy blocks, redirects or reopens a subject proposal, retain both:

- the original subject proposal;
- the realized action/state admitted by the structural policy.

Do not erase attempted behavior merely because it was not realized.

## 13. R8 — semantic layer

CPR is applied after structural evidence is frozen.

Required statuses:

- `STRUCTURAL_CANDIDATE_ONLY`;
- `ADJUDICATED_C` / `ADJUDICATED_P` / `ADJUDICATED_R` as permitted by the review contract;
- `ADJUDICATED_NON_CPR`;
- `REVIEW_DISAGREEMENT`;
- `UNRESOLVED`;
- `NOT_ADJUDICATED`.

Reviewer packets should contain bounded candidate windows plus necessary source-backed lineage rather than require unrestricted rediscovery of the entire trajectory.

## 14. Terminal outcome and engineering diagnostics

Retain separately:

- terminal task outcome;
- final-state equivalence/difference;
- turns/calls/tokens/spend;
- latency;
- reopened nodes;
- recovery execution cost.

Full Rerun and Checkpoint Retry may be secondary engineering baselines where useful, but they are not required to define the main R7 mechanism contrast.

## 15. Missingness and censoring

- censored != zero;
- missing != no;
- no descendant Jump in a censored window != extinction;
- no recurrence within a bounded recovery window != proof of permanent elimination;
- failed localization != evidence of no structural carrier;
- fields absent from historical source versions remain `NOT_RECORDED_IN_SOURCE_VERSION`.

## 16. Discovery / validation / semantic separation

- Discovery evidence may motivate Jump/inertia/CPR definitions.
- Structural definitions and detectors must be frozen before prospective validation.
- Semantic adjudication must not retroactively create structural events.
- Existing formal evidence protected by a no-new-adjudication freeze remains unchanged.
