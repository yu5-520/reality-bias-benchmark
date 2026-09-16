# R5 / R6 Branch Intervention & Recovery Protocol v0.1

Date: 2026-09-16  
Status: PROTOCOL FREEZE CANDIDATE  
Scope: first-paper mechanism experiments only  
Depends on:

- `docs/R_Plan_v3.2.md`
- `theory/theory_contract_v0.3.md`
- `docs/trajectory_dynamics_measurement_plan_v3.md`
- `docs/experimental_control_layer_v0.1.md`

## 1. Scientific purpose

R5/R6 test whether a hypothesized trajectory dependency is causally important after a recorded Jump candidate.

Preferred form:

`same frozen parent history + one preregistered intervention → branched continuation`

The original trajectory is immutable.

The protocol does not assume that an intervention eliminates model-level proposal generation. Proposal generation and operational realization are measured separately.

## 2. Selection order

The required order is:

1. freeze source evidence and deterministic structural indices;
2. define the structural anchor-selection rule;
3. enumerate the eligible candidate set;
4. select the anchor without viewing future branch outcomes;
5. freeze an `RB-ANCHOR-SELECTION-v0.1` record;
6. freeze the intervention spec and branch manifest;
7. run branch replicates;
8. freeze branch evidence;
9. derive deterministic trajectory metrics;
10. append semantic review later where required;
11. only then create recovery records and compare recurrence/reconstruction.

Semantic reviewer labels must not be used to cherry-pick the branch anchor unless a later protocol explicitly declares a semantic-enriched exploratory analysis. Confirmatory R5 selection is structural-only.

## 3. Eligible anchor conditions

A confirmatory anchor must satisfy all of the following:

- source trace/evidence hash is frozen;
- a deterministic structural candidate exists under the frozen measurement version;
- a complete replayable state snapshot was captured at or immediately before the selected boundary;
- required queue/inbox/state/version fields are present rather than reconstructed;
- the anchor is not terminal unless the intervention explicitly studies terminal recovery;
- the selected state hash verifies;
- provider-internal state replay is not claimed.

Historical traces lacking complete replay state may be used to design candidate rules but are not silently upgraded into replayable anchors.

## 4. Selection rule examples

Allowed rule style:

- first structurally realized epistemic-status jump candidate;
- first goal-scope change candidate followed by at least one downstream read;
- first Jump candidate before the first operational commit;
- first Jump candidate with at least N structurally recorded descendants;
- first feedback-return anchor under the frozen semantic-blind counter.

Tie-breakers must be deterministic, such as lowest event index or lowest stable event hash.

The selection rule and candidate set are frozen in `RB-ANCHOR-SELECTION-v0.1` before branch outcomes are visible.

## 5. R5 intervention families

v0.1 allows only narrow one-variable interventions.

### I. Epistemic-status intervention

Examples:

- FACT/current → provisional;
- remove one unsupported state key;
- restore one provenance marker.

### II. Authority/commit intervention

Examples:

- require expected parent-state hash;
- require source reference for one state write;
- block one named transition that lacks its frozen conversion condition.

### III. Invocation/routing intervention

Examples:

- block one named invocation edge;
- prevent dynamic invocation under a system-owned routing condition.

### IV. Temporal intervention

Examples:

- block one reopen/revision without a qualifying trigger;
- force new version identity rather than mutation of the settled state.

Each confirmatory branch changes only the named variable. Additional changes require a new intervention ID.

## 6. Branch identity

Every branch uses `RB-EXPERIMENTAL-BRANCH-v0.1` and binds:

- branch ID;
- parent trace hash;
- parent state hash;
- anchor reference;
- intervention spec + hash;
- replicate index;
- model/config/code identity;
- explicit `provider_internal_state_replayed = false`.

A branch is new behavior evidence. It never overwrites source evidence.

## 7. Replicates and Escape hazard

Because model continuation is probabilistic, a single replay is not sufficient to estimate Escape/Jump propensity.

For one frozen parent and one frozen condition:

`h_hat = branches with preregistered Jump / valid branch continuations`

Provider/transport failures are excluded from the denominator and reported separately. Censored branches remain censored.

Branches from one parent are clustered repeated continuations and are not automatically treated as independent task samples.

## 8. R5 primary outcomes

Primary structural outcomes are kept separate:

- proposal Jump incidence;
- realized Jump incidence;
- first operational commit location;
- penetration depth;
- affected descendant count;
- affected Agent count;
- post-Jump persistence/inertia;
- calls / turns / tokens.

A valid containment result may have:

`proposal Jump incidence ≈ unchanged`

while:

`realized Jump / penetration / descendants ↓`

This supports containment rather than generation suppression.

## 9. R6 recovery conditions

Recovery experiments begin from frozen states at different distances after a Jump candidate:

- pre-Jump checkpoint;
- post-Jump / pre-commit;
- post-first-commit;
- shallow propagated state;
- multi-descendant state;
- post-challenge/retrospective state.

Supported recovery strategies in v0.1 records:

- `FULL_RERUN`
- `CHECKPOINT_RECOVERY`
- `LOCAL_STATE_CORRECTION`
- `VERSIONED_STATE_ADVANCE`

No recovery path may rewrite the original source trajectory.

## 10. R6 outcomes

Every recovery condition records, where available:

- recovery anchor distance;
- recovery status: recovered / partial / failed / censored;
- residual descendant count;
- recurrence detected structurally;
- regeneration semantic status, default `NOT_ADJUDICATED`;
- recovery turns / calls / tokens;
- provenance reconstruction status.

A structural recurrence is not automatically semantic R regeneration. Semantic R remains a later adjudication layer.

## 11. Recovery distance

For v0.1 exploratory work, recovery distance may be recorded as the number of frozen operational boundaries between the selected Jump anchor and recovery anchor.

A confirmatory paper claim requires a separately frozen exact boundary set before analysis. Do not redefine distance after seeing the result.

## 12. Evidence package

Each R5/R6 experimental package should contain:

- source evidence hash;
- measurement version;
- anchor-selection record;
- parent state snapshot + hash;
- intervention spec;
- branch manifest(s);
- branch trace/journal(s);
- deterministic trajectory metrics;
- recovery record(s), if R6;
- code commit SHA;
- all relevant config hashes;
- failures/censoring/usage;
- semantic review records appended later if used.

## 13. Stop and integrity rules

Stop and audit before scientific interpretation if:

- parent state hash mismatches;
- branch manifest does not bind the parent state;
- intervention code changes more than the frozen variable;
- source evidence is overwritten;
- replay requires fabricating missing queue/inbox/provider state;
- the anchor was selected after branch outcomes were inspected;
- branch failures are silently converted into negatives.

## 14. API boundary

This protocol and all offline validation are zero-provider-call work.

No paid subject or reviewer run is authorized by this file. A real run requires a separate frozen run plan, named provider/model, explicit authorization and explicit spending ceiling.
