# Reality Bias System Behavior Measurement Plan v4.1

Date: 2026-09-17  
Status: FORWARD / PROCESS-REALITY MECHANISM MEASUREMENT  
Depends on: R Plan v4.1, Theory Contract v0.5.

## 1. Measurement hierarchy

```text
SystemTrajectory
  -> BehaviorEvent / StateTransition
       -> natural Jump candidate
       -> source-backed lineage
       -> inherited inertia
       -> CPR semantic candidate
       -> recovery / recurrence
```

Outcome validity remains a terminal auxiliary measurement.

## 2. R2

Record natural Jump candidate identity, event/turn, actor, boundary, state diff, source refs and candidate type. Do not infer semantic C/P/R from structural detection alone.

## 3. R3

Trace exact source-backed inheritance through message, invocation, shared-state visibility, read-to-turn, action and state relations.

Measure descendants, affected actors, role crossings, path depth, branch points, loops and re-entry. Activity volume is not inertia by itself.

## 4. R4

Locate retrospective/challenge/reopen windows and derive structural candidate outcomes. Semantic persistence/regeneration/amplification/normalization remains deferred where necessary.

## 5. R5 one-shot evidence boundary

The direct experimental evidence must record:

- same parent/start state hash for A and B;
- target Jump/state key/source event;
- original and one-shot status;
- exactly one experiment-origin delivery;
- delivery actor/turn and prompt-visible delta path;
- consumption immediately after that exposure;
- zero experiment-origin reinjection;
- `persistent_state_mutation = false`.

## 6. Layer 1 — Jump recurrence

For every downstream structural Jump candidate classify lineage as:

- `DESCENDANT_REJUMP`;
- `INDEPENDENT_NEW_JUMP`;
- `LINEAGE_UNRESOLVED`.

Candidate measurements:

- descendant re-jump count;
- first re-jump event/turn distance;
- actor/role/boundary distance;
- candidate-family continuity/transformation;
- whether the node had direct experimental exposure.

## 7. Layer 2 — inherited inertia

Candidate deterministic metrics:

- descendant path depth;
- shared structural prefix;
- first A/B structural divergence;
- first reconvergence;
- post-exposure path overlap;
- descendant-path survival;
- role/Agent activation continuity.

Labels such as retained/deflected/broken/reconverged are structural summaries, not value judgments.

## 8. Layer 3 — path topology

Build typed process graphs from recorded behavior and source-backed lineage.

Canonical node/edge signatures must remove run-specific event IDs while preserving evidence refs separately.

Compare:

- shared path families;
- control-only observed families;
- intervention-only observed families;
- branch/crossing/loop/re-entry/merge changes;
- role/responsibility activation patterns;
- canonical topology overlap/distance.

A single run demonstrates one realized path, not an exhaustive possibility space. Repeated same-parent trajectories estimate an observed path-family distribution conditional on the frozen parent.

## 9. R6

Record natural recovery, residual descendants and recurrence in the same trajectory. Controlled recovery branches may be added later at frozen recovery boundaries.

## 10. CPR semantic layer

CPR is applied after structural evidence is frozen. Reviewer packets should localize candidate transitions and relevant lineage rather than require full-trajectory free search.

## 11. Terminal outcome

Task success, answer quality, turns, calls, tokens and spend are retained as auxiliary diagnostics. They cannot replace process mechanism outcomes.

Of special interest are cases where terminal outcomes match but process topology differs, or terminal effects reverse direction while the same structural mechanism recurs.

## 12. Censoring / missingness

- censored != zero;
- missing != no;
- no descendant re-jump observed in a censored window != full-episode absence;
- no recovery opportunity != failed recovery;
- no-anchor runs remain valid observations and are not rerun to manufacture an anchor.

## 13. Discovery and validation

Metrics/taxonomy developed on discovery evidence must be frozen before confirmatory validation evidence. Historical fields absent from old traces remain `NOT_RECORDED_IN_SOURCE_VERSION`.
