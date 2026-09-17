# Reality Bias System Behavior Measurement Plan v4.4

Date: 2026-09-17  
Status: FORWARD / R5-R6 SPECIFICITY MEASUREMENT  
Depends on: `docs/R_Plan_v4.4.md`, `theory/theory_contract_v0.8.md`.

## 1. Measurement hierarchy

```text
SystemTrajectory
  -> Raw BehaviorEvent / StateTransition
  -> Natural Jump candidate
  -> Source-backed lineage
  -> Inherited inertia
  -> R5 local perturbation response
  -> R6 post-consumption inertia response
  -> R5-R6 target-specificity contrast
  -> R7 risk-control / localized-recovery contrast
  -> R8 CPR semantic adjudication
```

Terminal outcome remains separate.

## 2. Evidence layers

Record raw facts before deriving structure. Preserve actor/role/turn, model input/output identity where permitted, parsed actions, messages, invocations, state reads/writes/revisions, before/after state identity, FINAL/reopen/revision operations, queue/pending/error/censoring state, and intervention-delivery evidence.

Derived relations must preserve evidence refs back to raw facts.

## 3. R2-R4 observational views

R2 measures natural Jump emergence. R3 measures source-backed inheritance/propagation. R4 measures retrospective/challenge/reopen dynamics. These views remain available on both natural and post-R5 continuations.

No structural detector automatically assigns semantic C/P/R.

## 4. R5 local perturbation object

For each R5 one-shot branch record:

- parent/start-state identity;
- natural J0 event ref and target state key;
- pre-intervention factual-status representation;
- one-shot target status;
- research identity of the one-shot operator;
- exact direct exposure count;
- consumption record;
- reinjection count;
- persistent experiment-origin mutation flag;
- prompt-visible/intervention delta hash where available;
- free-continuation start point.

R5 primary endpoint: **local-to-downstream structural reorganization after one bounded exposure**.

## 5. Immediate response is not inertia

The following may be valid local responses but do not alone establish an inertia transition:

- one extra write;
- one extra message;
- one verification action;
- one local reroute;
- temporary hesitation;
- immediate lexical disagreement.

Such events belong to the **Local Perturbation Response** object.

## 6. R6 post-consumption inertia object

R6 begins only after the experiment-origin one-shot mark has been consumed for the relevant treated branch.

Measure, at matched downstream distance where possible:

- descendant Jump count and first distance;
- same-family versus transformed continuation;
- direct/indirect state inheritance;
- transfer to another actor/field lineage;
- root reach and depth;
- branch/merge/re-entry;
- cross-Agent spread;
- path-family continuation/shift/reconstruction;
- delayed re-emergence;
- retrospective return/rebound;
- post-return inheritance;
- reconvergence location/distance;
- extinction/no-longer-source-backed status;
- censoring.

R6 should produce a multidimensional **Inertia Profile**, not a mandatory single scalar.

## 7. R6 higher-order summaries

Permitted structural summaries include:

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

These require source-backed lower-level evidence and remain non-semantic.

## 8. R5-R6 Specificity Triad

Use `S` conditions, never R7 `C` labels.

### S0 — Natural Reference

- new experiment-origin exposure count: `0`;
- no new status downgrade;
- same passive observability and matched horizon/censoring rule.

### S1 — Matched Factual-Field Status Downgrade

- target class: `MATCHED_NON_J0_FACTUAL_FIELD`;
- same one-shot mechanical transform as S2;
- direct experiment-origin exposure count: `1`;
- reinjection count: `0`;
- persistent experiment-origin mutation: `false`;
- no terminal-answer target;
- free continuation after consumption.

### S2 — J0-Targeted Authority Withdrawal

- target class: `SELECTED_J0_FIELD`;
- same one-shot mechanical transform as S1;
- direct experiment-origin exposure count: `1`;
- reinjection count: `0`;
- persistent experiment-origin mutation: `false`;
- no terminal-answer target;
- free continuation after consumption.

## 9. Field-selection evidence

Before subject execution freeze:

- freeze eligible field pool;
- assign pool hash;
- record candidate target refs;
- record each candidate's pre-intervention status;
- record target visibility/timing;
- record state/interface family;
- record actor/role accessibility where relevant;
- record matching features;
- record exclusions with reason;
- freeze deterministic/randomized selection rule;
- freeze selected S1 target and selected-target hash.

Selection must be outcome-blind with respect to future S-arm responses.

## 10. Specificity comparison objects

Create three explicit contrasts:

### Generic uncertainty contrast

`S1 - S0`

Interpretation: response to the same one-shot factual-status downgrade when it is applied to a matched non-J0 factual field.

### Total J0-targeted contrast

`S2 - S0`

Interpretation: total observed response associated with J0-targeted authority withdrawal.

### Target-specificity contrast

`S2 - S1`

Interpretation: whether the J0-targeted inertia profile is distinguishable from the generic uncertainty response under matched intervention mechanics.

The primary specificity contrast is `S2 - S1`.

## 11. Specificity observables

Compare S arms using the same R6 dimensions rather than inventing a separate ontology:

- descendant Jump structure;
- first descendant distance;
- inheritance/transfer status;
- root reach/depth;
- actor-transition structure;
- cross-Agent spread;
- branch/merge/re-entry;
- path-family structure;
- state-lineage destination;
- retrospective return/rebound;
- reconvergence;
- terminal/process decoupling.

Local activity volume may be reported but cannot define specificity by itself.

## 12. Distinguishable inertia response

A later preregistered analysis contract must state what constitutes a structurally distinguishable inertia response. Until then, do not collapse heterogeneous structural dimensions into an unvalidated composite score.

Permitted evidence forms may include:

- non-overlapping realized path-family structure;
- different affected actor/field lineage;
- different source-backed descendant reach/depth;
- different re-entry/branch/merge topology;
- different recurrence/return structure;
- different reconvergence location or absence within uncensored horizon.

Direction need not be monotonic.

## 13. One-shot operator research identity

Every one-shot evidence object must include `research_identity`, for example:

- `R5_J0_PROBE`;
- `R5R6_S1_MATCHED_FACTUAL_FIELD`;
- `R5R6_S2_J0_TARGET`;
- `R7_C1_ONE_SHOT_FREE`.

This prevents identical mechanical primitives from being confused across scientific contrasts.

## 14. R7 namespace remains separate

R7 continues to use:

- `C1_ONE_SHOT_FREE_CONTINUATION`;
- `C2_PERSISTENT_FIELD_PROPAGATION`;
- `C3_ALR_AUTHORITY_LOCALIZED_RECOVERY`.

`S` varies target identity. `C` varies structural handling mode. No forward artifact should alias S1/S2 to C1/C2/C3.

## 15. Missingness and censoring

- censored != zero;
- missing != no;
- no descendant Jump in a censored window != extinction;
- no recurrence within bounded horizon != permanent elimination;
- no difference in one structural dimension != no process difference;
- historical fields absent from older source versions remain `NOT_RECORDED_IN_SOURCE_VERSION`.

## 16. Semantic boundary

Specificity is structural/mechanistic evidence. It does not automatically establish semantic C/P/R.

R8 remains append-only semantic adjudication after structural freeze.

## 17. Authorization boundary

This measurement plan authorizes offline contract/schema/runtime validation only. It authorizes no new paid subject or evaluator call.
