# R6-D Matched-Stock Robustness Protocol v0.1

Date: 2026-09-17  
Status: **DESIGN FROZEN / NOT RUNTIME READY / NOT AUTHORIZED**  
Parent protocol: `docs/R5_R6_specificity_protocol_v0.4.md`

## 1. Purpose

This is an append-only **R6-D robustness extension**, not a new R stage and not a replacement for the first S0/S1/S2 batch.

The first real R6-D batch established a stable **Frozen Target Response Contrast** between the preregistered S2 and S1 targets, while also showing that S1 and S2 were not exchangeable on structural position, provenance, task relevance and downstream opportunity.

This robustness design narrows that target-matching gap by comparing the original J0 target against **all eligible ordinary stock facts in the same frozen source container**.

## 2. Timing disclosure

This design is frozen **after the first S0/S1/S2 batch and before any second-batch output**.

Therefore:

- first-batch outcomes are known;
- this design is not described as globally outcome-blind relative to the first batch;
- the eligibility rule is defined only from the frozen `after_turn:8` parent structure;
- first-batch response values are forbidden as an eligibility criterion;
- all eligible candidates under the rule are included;
- the original S1 remains part of the evidence and is never replaced.

Machine-readable timing label:

`POST_FIRST_BATCH_PRE_SECOND_BATCH`

## 3. Frozen source

Common parent:

- anchor: `after_turn:8`
- state hash: `aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c`
- source event: `E32`
- source writer: `inventory`
- source container: `shared_state.inventory_stockout_assessment_v1`
- container authority metadata: `status=fact`

The original S2 target remains:

`shared_state.inventory_stockout_assessment_v1.A.preliminary_stock = 1520`

Its special source provenance is `preliminary_unreconciled`.

## 4. Eligibility rule

An ordinary matched-stock control must satisfy all of the following on the frozen parent:

1. reside under exactly `shared_state.inventory_stockout_assessment_v1`;
2. originate from the same E32 inventory state object;
3. inherit the same **container-level** `status=fact` authority context;
4. be a prompt-visible integer scalar;
5. have the direct semantic role **stock quantity**;
6. use the ordinary leaf name `stock`;
7. not be the original J0 target;
8. not be a preliminary/unreconciled field;
9. not be a derived metric, recommendation, trigger, boolean policy field, daily-rate field or lead-time field.

This yields exactly two eligible ordinary stock facts:

- `shared_state.inventory_stockout_assessment_v1.B.stock = 900`
- `shared_state.inventory_stockout_assessment_v1.C.stock = 3400`

Both are included. No post-outcome choice between them is permitted.

## 5. Authority-scope boundary

The parent records `status=fact` at the **container level**, not separate fact labels on every nested leaf.

Accordingly, S2/S3/S4 are matched on the same container authority context. This protocol does **not** claim independent proposition-level fact metadata for A/B/C stock leaves.

## 6. Conditions

### S2 — J0 anchor rerun

`S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL`

Target:

`shared_state.inventory_stockout_assessment_v1.A.preliminary_stock = 1520`

Role: contemporaneous rerun anchor for the original J0 target.

### S3 — matched ordinary stock B

`S3_MATCHED_ORDINARY_STOCK_B_DOWNGRADE`

Target:

`shared_state.inventory_stockout_assessment_v1.B.stock = 900`

### S4 — matched ordinary stock C

`S4_MATCHED_ORDINARY_STOCK_C_DOWNGRADE`

Target:

`shared_state.inventory_stockout_assessment_v1.C.stock = 3400`

## 7. Common operator

All three conditions use the same atomic primitive:

`ONE_SHOT_TARGET_SCOPED_EPISTEMIC_STATUS_ANNOTATION`

with:

- `fact -> unconfirmed`;
- original value preserved;
- one direct experiment-origin exposure;
- zero experiment-origin reinjection;
- zero experiment-origin persistent state mutation;
- no opposite fact;
- no replacement conclusion;
- no desired terminal answer;
- free continuation after consumption.

Endogenous Agent state remains observable and may become carrier evidence.

## 8. Execution geometry

Second batch:

- 3 conditions × 3 repeated realizations = 9 branches;
- same frozen parent;
- same task/model/Agent environment;
- same T9 direct-response window;
- same T10+ post-consumption window;
- same absolute cap T16;
- natural early termination remains right-censoring.

Cyclic order:

- replicate 1: `S2 -> S3 -> S4`
- replicate 2: `S3 -> S4 -> S2`
- replicate 3: `S4 -> S2 -> S3`

Same-parent repeats remain repeated realizations, not independent population samples.

## 9. Analysis freeze

Historical first-batch primary contrast remains:

`S2 - S1`

It is not replaced.

Second-batch primary robustness contrasts:

- `S2 - S3`
- `S2 - S4`

Matched ordinary-target spread:

- `S3 - S4`

There is **no fresh S0** in this robustness batch. The first-batch S0 evidence remains an external auxiliary natural-variability reference; therefore this second batch does not independently re-estimate the natural baseline.

Report separately:

- T9 local response;
- structural distance;
- information-inheritance distance;
- epistemic-authority distance;
- experiment-annotation persistence;
- source-container authority persistence;
- target reference/state/action propagation;
- censoring.

No post-hoc total scalar is permitted.

## 10. Interpretation boundary

A consistent S2 response relative to both S3 and S4 would strengthen target-specific robustness under a substantially better matched same-container stock comparison.

It would still need to be read together with the first-batch natural baseline before any stronger Escape-derived specificity claim.

Pre-run status remains:

- `FROZEN_TARGET_RESPONSE_CONTRAST`: historical evidence retained;
- matched-stock robustness: **NOT YET RUN**;
- intervention-related inertia beyond natural variability: **NOT ESTABLISHED**;
- Escape-derived specificity: **NOT ESTABLISHED**;
- CPR: `NOT_ADJUDICATED`.

## 11. Evidence ordering

Any later scientific execution must preserve:

`subject run -> raw freeze -> immutable package/upload -> derivation`

No automatic paid evaluator is part of the subject run.

## 12. Budget and authorization

Frozen ceiling:

- 64 calls / branch;
- USD 0.25 / branch;
- 9 branches;
- USD 2.25 global ceiling.

This protocol does **not** bind a real runner or real workflow and does **not** authorize provider, evaluator, recovery or semantic-adjudication calls.

Design hash:

`5064e255da26949a152a2300fe659ebdddddc9b44f1a97a4b31d7796005a959d`
