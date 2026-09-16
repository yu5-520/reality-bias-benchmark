# R6 Inertia Transition and Downstream Consequences Protocol v0.1

Date: 2026-09-17  
Status: FORWARD PROTOCOL / STRUCTURAL ANALYSIS FIRST  
Depends on: `docs/R_Plan_v4.2.md`, `theory/theory_contract_v0.6.md`, `docs/system_behavior_measurement_plan_v4.2.md`.

## 1. Purpose

R6 consolidates the existing fine-grained post-Jump questions into a higher-order comparison of **system inertia before and after path reorganization**.

R6 does not replace the prior recovery/residual/recurrence observations. Those remain measurements inside the broader inertia-transition object.

## 2. Entry condition

A forward R6 analysis begins only after a source-backed Jump and a valid downstream observation window exist. For a matched R5 A/B analysis, R6 additionally requires:

- the same frozen parent/start-state identity;
- a valid R5 control and one-shot branch;
- the direct intervention ledger required by the R5 contract;
- frozen structural evidence before semantic review.

R6 may also be applied descriptively to natural non-intervention trajectories where the source-backed lineage is available.

## 3. Core question

> After a local perturbation reorganizes the process path, how does the resulting downstream system inertia differ from the original natural inertia, and what consequences follow from that difference?

R6 does not require a stable directional effect.

## 4. Fine-grained observations retained from the original R6 logic

For every eligible post-J0 trajectory/window, record:

1. whether later Jump candidates appear;
2. whether source-backed later Jumps are descendants of J0 or independent new Jumps;
3. whether descendant Jumps preserve the same structural family/type or transform;
4. whether the prior Jump-derived field/state disappears, persists, transfers or is inherited through another carrier;
5. whether a challenge/reopen/correction boundary causes prior Jump-derived structure to return;
6. whether a returned Jump is same-family, transformed or independent;
7. whether the returned/transformed Jump is inherited again;
8. whether the lineage terminates, reconverges, branches, merges, re-enters an actor/role or crosses Agents;
9. whether the observed window is sufficient to resolve these questions.

## 5. Structural inertia summaries

Lower-level observations may be summarized as:

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

A summary label must point to the event/state/lineage evidence that supports it.

## 6. R-mediated return is a structural observation before semantic adjudication

A retrospective/challenge/reopen/correction boundary may be associated with return of prior Jump-derived structure. Structurally, R6 records the return and its inheritance consequences.

It does **not** automatically label that return semantic `R`.

Semantic `R` requires the separate R8 CPR definition/adjudication contract.

## 7. Matched comparison

For R5-derived matched branches, compare:

- control/original inertia;
- intervention/reorganized inertia.

Where possible, compare at matched downstream distance rather than only at terminal state:

- same turn distance from J0;
- same event distance;
- same descendant generation/depth;
- same retrospective boundary class.

If one branch terminates earlier, report the unequal horizon. Do not infer extinction from censoring.

## 8. Primary outputs

At minimum, an R6 analysis object should include:

- source J0 identity;
- branch/run identity;
- observation horizon;
- descendant Jump count and first distance;
- Jump-family continuity/transformation;
- field/state inheritance status;
- affected Agent/role set;
- root reach/depth;
- branch/merge/re-entry/cross-Agent structure;
- retrospective return state if a valid boundary exists;
- post-return inheritance if observed;
- higher-order inertia summary;
- censoring/missingness status;
- evidence refs.

## 9. Relationship to recovery

Recovery is one possible downstream phenomenon.

R6 may observe:

- successful recovery;
- partial recovery with residual descendants;
- apparent recovery followed by recurrence;
- no recovery opportunity;
- recovery of one field while another inherited path persists;
- replacement of one inertia pattern by another.

Therefore `recovery/residual/recurrence` remains useful vocabulary but cannot define the full R6 object.

## 10. Relationship to R7

R6 is primarily observational/analytical. It establishes what kind of inertia exists after path change and which source-backed carriers remain active.

R7 uses this knowledge to test sustained structured feedback/recovery.

R6 must not silently introduce active ALR routing and then describe the result as natural post-reorganization inertia.

## 11. Semantic and outcome boundaries

- structural same-type/different-type does not automatically mean semantic same-CPR/different-CPR;
- terminal equivalence does not erase inertia differences;
- terminal divergence does not by itself prove inertia transition;
- CPR adjudication is deferred to R8 unless an evidence object was explicitly created under a semantic-review contract.

## 12. Current formal R5-MID compatibility

The existing formal R5-MID batch may serve as a bounded precursor/example for R6 structural analysis where already-frozen measurements permit it. Its finite horizon and frozen no-reanalysis/no-new-adjudication rules must be respected.

A future full R6 subject run may require a longer continuation horizon; such a run requires a new freeze and explicit execution authorization.
