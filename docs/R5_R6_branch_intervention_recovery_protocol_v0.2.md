# R5 / R6 Branch Intervention & Recovery Protocol v0.2

Date: 2026-09-16  
Status: PROTOCOL FREEZE CANDIDATE / OFFLINE INSTRUMENTATION VALIDATED  
Scope: first-paper mechanism experiments only  
Supersedes for forward work: `docs/R5_R6_branch_intervention_recovery_protocol_v0.1.md`

Depends on:

- `docs/R_Plan_v3.2.md`
- `theory/theory_contract_v0.3.md`
- `docs/trajectory_dynamics_measurement_plan_v3.md`
- `docs/experimental_control_layer_v0.2.md`

Historical v0.1 protocol/records remain preserved.

## 1. Scientific purpose

R5/R6 test whether a hypothesized trajectory dependency is causally important after a recorded Jump candidate.

Preferred form:

`same frozen parent history + one preregistered intervention → branched continuation`

The original trajectory is immutable.

The protocol does not assume that an intervention eliminates model-level proposal generation. Proposal generation and operational realization are measured separately.

## 2. Required execution order

1. freeze source evidence and deterministic structural indices;
2. define the structural anchor-selection rule;
3. enumerate the eligible candidate set;
4. select the anchor without viewing future branch outcomes;
5. freeze an `RB-ANCHOR-SELECTION-v0.1` record;
6. freeze the parent state snapshot;
7. freeze intervention spec;
8. construct control/intervention `RB-EXPERIMENTAL-BRANCH-v0.2` manifests;
9. verify parent/start hashes plus turn/event boundaries;
10. run branch replicates;
11. freeze branch traces/journals;
12. derive deterministic Measurement-v3 branch records/comparison;
13. append semantic review later where required;
14. only then create recovery records and compare recurrence/reconstruction.

Semantic Reviewer labels must not select the confirmatory R5 anchor. A later exploratory semantic-enriched analysis must be separately labeled.

## 3. Eligible anchor conditions

A confirmatory anchor must satisfy all of the following:

- source trace/evidence hash is frozen;
- a deterministic structural candidate exists under the frozen measurement version;
- a complete replayable state snapshot was captured at or immediately before the selected boundary;
- queue/inbox/state/version/event/turn fields needed for continuation are present rather than reconstructed;
- the anchor is not terminal unless the intervention explicitly studies terminal recovery;
- selected state hash verifies;
- provider-internal state replay is not claimed.

Historical traces lacking complete replay state may inform design but are not silently upgraded into replayable anchors.

## 4. Selection rules

Allowed confirmatory rule style includes:

- first structurally realized epistemic-status jump candidate;
- first goal-scope change candidate followed by at least one downstream read;
- first Jump candidate before first operational commit;
- first Jump candidate with at least N structurally recorded descendants;
- first feedback-return anchor under the frozen semantic-blind counter.

Tie-breakers must be deterministic, such as lowest event index or stable event hash.

The selection rule and eligible candidate set are frozen before branch outcomes are visible.

## 5. R5 intervention families

v0.2 keeps interventions narrow and one-variable-first.

### I. Epistemic-status intervention

Examples:

- FACT/current → provisional;
- remove one unsupported state key;
- restore one provenance marker.

### II. Authority/commit intervention

Examples:

- require expected parent-state hash;
- require source reference for one state write;
- block one named transition lacking its frozen conversion condition.

### III. Invocation/routing intervention

Examples:

- block one named invocation edge;
- prevent dynamic invocation under a system-owned routing condition.

### IV. Temporal intervention

Examples:

- block one reopen/revision without qualifying trigger;
- force new version identity instead of mutating settled state.

Each confirmatory branch changes only the named variable. Additional changes require a new intervention ID/protocol condition.

## 6. Branch identity v0.2

Every forward branch uses `RB-EXPERIMENTAL-BRANCH-v0.2` and binds:

- branch ID;
- parent trace hash;
- parent state hash;
- branch-start state hash;
- parent turn / branch-start turn;
- parent event count / branch-start event count;
- parent/start anchor refs;
- intervention spec + hash;
- `intervention_applied_before_continuation`;
- replicate index;
- model/config/code identity;
- explicit `provider_internal_state_replayed = false`.

For a changed state intervention:

`parent_state_hash != branch_start_state_hash`

The parent identity must remain unchanged across control/intervention branches, while the branch-start state may differ by exactly the frozen intervention.

A branch is new behavior evidence. It never overwrites source evidence.

## 7. Replicates and Escape hazard

Because continuation is probabilistic, a single replay is insufficient to estimate Escape/Jump propensity.

For one frozen parent and one frozen condition:

`h_hat = branches with preregistered Jump / valid branch continuations`

Provider/transport failures are excluded from the denominator and reported separately. Censored branches remain censored.

Branches from one parent are clustered repeated continuations and are not automatically independent task samples.

The exact Jump-positive detector must be frozen before confirmatory hazard estimation.

## 8. Measurement v3 branch records

Each valid branch produces a deterministic continuation-only record under:

`RB-TRAJECTORY-MEASUREMENT-v3.0.1`

The adapter slices from `branch_start_event_count` / `branch_start_turn` and currently records:

- continuation turn/call/event counts;
- realized event/action counts;
- continuation actors;
- realized Authority-class events;
- realized operational events;
- Measurement-v2 structural candidates restricted to continuation;
- final-state/final-answer hashes;
- usage summary.

Control/intervention branch comparison requires identical parent trace/state hashes before computing structural deltas.

These machine records leave C/P/R, Authority Penetration, semantic adoption, recovery and causal effect as `NOT_ADJUDICATED`.

## 9. R5 primary outcomes

The confirmatory run-freeze must distinguish primary versus secondary metrics before provider calls.

Candidate outcomes include:

- proposal Jump incidence;
- realized Jump incidence;
- first operational commit location;
- penetration depth;
- affected descendant count;
- affected Agent count;
- post-Jump persistence/inertia;
- calls / turns / tokens.

A valid containment pattern may have:

`proposal Jump incidence ≈ unchanged`

while:

`realized Jump / penetration / descendants ↓`

This would support containment rather than generation suppression, subject to the preregistered semantic/causal criteria.

Generic branch event-count differences must not be substituted for these outcomes post hoc.

## 10. R6 recovery conditions

Recovery experiments may begin from frozen states at different distances after a Jump candidate:

- pre-Jump checkpoint;
- post-Jump / pre-commit;
- post-first-commit;
- shallow propagated state;
- multi-descendant state;
- post-challenge/retrospective state.

Supported recovery strategies in the current record schema:

- `FULL_RERUN`
- `CHECKPOINT_RECOVERY`
- `LOCAL_STATE_CORRECTION`
- `VERSIONED_STATE_ADVANCE`

No recovery path may rewrite original source trajectory.

## 11. R6 outcomes

Every recovery condition records, where available:

- recovery anchor distance;
- recovered / partial / failed / censored status;
- residual descendant count;
- recurrence detected structurally;
- regeneration semantic status, default `NOT_ADJUDICATED`;
- recovery turns / calls / tokens;
- provenance reconstruction status.

Structural recurrence is not automatically semantic R regeneration. Semantic R remains a later adjudication layer.

## 12. Recovery distance

For exploratory work, recovery distance may be recorded as the number of frozen operational boundaries between selected Jump anchor and recovery anchor.

A confirmatory paper claim requires a separately frozen exact boundary set before analysis. Do not redefine distance after seeing results.

## 13. Evidence package

Each R5/R6 package should contain:

- source evidence hash;
- measurement version;
- anchor-selection record;
- parent state snapshot/hash;
- intervention spec;
- branch-start snapshot/hash where changed;
- branch manifest(s);
- branch trace/journal(s);
- deterministic branch measurement record(s);
- branch structural comparison;
- recovery record(s), if R6;
- code commit SHA;
- config hashes;
- failures/censoring/usage;
- semantic review records appended later if used.

## 14. Stop and integrity rules

Stop and audit before scientific interpretation if:

- parent state hash mismatches;
- control/intervention no longer share the same frozen parent identity;
- branch-start hash does not match the actual continuation snapshot;
- turn/event cut boundary does not match the frozen branch manifest;
- intervention code changes more than the named variable;
- source evidence is overwritten;
- replay requires fabricating missing queue/inbox/provider state;
- anchor was selected after branch outcomes were inspected;
- failures/censoring are silently converted into negatives;
- deterministic structural outputs are presented as semantic C/P/R/penetration conclusions.

## 15. Offline validation status

The current zero-provider-call preflight validates:

`baseline → frozen anchor → control branch`

and:

`same frozen parent → one state-status ΔX → changed branch start → continuation`

It also verifies Measurement-v3 continuation slicing and recovery-record plumbing.

This is engineering validation only, not scientific evidence of intervention effectiveness.

## 16. API boundary

This protocol and all offline validation authorize zero paid provider calls.

A real R5/R6 run requires a separate frozen real-model run plan containing provider/model, exact or bounded repeats, primary metric set, call budget, explicit spending ceiling/currency, and explicit paid-run authorization.
