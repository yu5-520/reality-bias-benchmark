# R5-R6 Target-Specificity Protocol v0.3

Date: 2026-09-17  
Status: FORWARD / R6-D SPECIFICITY DESIGN / NO SCIENTIFIC RUN AUTHORIZATION  
Predecessor: `docs/R5_R6_specificity_protocol_v0.2.md`

## 1. Role

This protocol is no longer treated as an extra research stage between R6 and R7.

It is the **R6-D target-specificity design** used to distinguish J0-targeted post-consumption inertia from generic uncertainty response.

R5 still supplies the bounded perturbation primitive. R6 supplies the identification logic and readout.

## 2. Scientific question

> When the same one-shot epistemic-status annotation is applied to an ordinary factual information item and to the J0 escape-derived information, are the resulting post-consumption system-inertia profiles structurally distinguishable beyond natural variability?

## 3. Conditions

### S0 — Natural Reference

No new experiment-origin epistemic annotation.

### S1 — Ordinary / Matched Factual Information Downgrade

One-shot annotation applied to a preregistered ordinary factual target selected outcome-blind before S-arm outcomes exist.

### S2 — J0-Targeted Escape-Derived Authority Withdrawal

The same one-shot annotation applied to the preregistered J0-derived target.

## 4. Exact-source current bindings

Frozen prospective targets:

- S1 locator: `public_context.products.C.gross_margin_pct`;
- S1 original value: `35`;
- S2 locator: `shared_state.inventory_stockout_assessment_v1.A.preliminary_stock`;
- S2 original value: `1520`;
- S2 source origin status: `preliminary_unreconciled`;
- S2 acquired status at J0: `fact` through the containing inventory assessment.

## 5. Common operator

S1 and S2 use:

`ONE_SHOT_TARGET_SCOPED_EPISTEMIC_STATUS_ANNOTATION`

Prompt-visible experimental delta:

```json
{
  "target_locator": "<frozen locator>",
  "epistemic_status": "unconfirmed"
}
```

Required equivalence:

- same envelope schema/version;
- same direct exposure limit = 1;
- same `fact -> unconfirmed` semantics;
- same prompt-visible annotation structure;
- same no-reinjection rule;
- same no-persistent-mutation rule;
- same no-opposite-fact rule;
- same no-replacement-conclusion rule;
- same no-target-answer rule;
- same continuation horizon/censoring rule.

Only target identity/provenance differs.

## 6. Historical boundary

This atomic v0.3 design is a prospective follow-up.

It does not claim to be an exact replay of the historical R5-MID container-level intervention:

`shared_state_metadata.inventory_stockout_assessment_v1.status: fact -> unconfirmed`

Historical A/B evidence remains unchanged and is not relabeled S0/S2.

## 7. Outcome-blind S1 selection

The first S1 pool is frozen under:

`RB-R5R6-SPECIFICITY-FIELD-SELECTION-CONTRACT-v0.2`

Pool rule:

`PUBLIC_CONTEXT_PRODUCT_SCALAR_NON_INVENTORY_FAMILY_v1`

Selection is deterministic from the frozen parent hash and contract identity. S1 may not be replaced after observing S outcomes.

A later same-family robustness control may be added append-only but cannot erase or replace the first S1 result.

## 8. Readout hierarchy

Report separately:

1. exposure integrity;
2. local perturbation response;
3. carrier/inheritance evidence;
4. post-consumption inertia profile;
5. natural-variability comparison;
6. S-arm specificity contrast;
7. terminal outcome.

Do not combine these into one unvalidated score.

## 9. Contrasts

### Generic uncertainty response

`S1 - S0`

### Total J0-targeted response

`S2 - S0`

### Primary target specificity

`S2 - S1`

The primary scientific claim, if supported, concerns structural distinguishability of post-consumption inertia, not merely different first-turn activity.

## 10. Natural variability interface

Specificity must be interpreted relative to repeated natural/condition variability.

A single S0/S1/S2 triplet may demonstrate a concrete matched contrast but should not automatically be described as a stable distribution-level effect.

Where resources permit, repeat matched S triplets from the same parent with frozen order-rotation/randomization and compare within-condition versus cross-condition process distance.

Same-parent repeats remain repeated realizations, not independent population samples.

## 11. Censoring

Natural early termination is right-censoring.

If S1/S2 ends before comparable downstream opportunities occur, the inertia comparison is unresolved for the censored dimensions rather than zero.

## 12. CPR boundary

A positive S2-S1 specificity result does not itself establish semantic C/P/R.

The S2 target may be an escape-derived candidate because a `preliminary_unreconciled` signal entered a fact-status container, but R8 must still determine whether the proposition itself was inappropriately strengthened and how downstream Agents interpreted/used it.

## 13. Current status

Completed offline:

- exact-source audit;
- frozen S1 pool/selection;
- exact S1/S2 target binding;
- common atomic one-shot operator;
- deterministic preflight/tests.

Not yet completed scientifically:

- real S0/S1/S2 subject execution;
- natural-baseline repeated specificity runs;
- post-consumption inertia derivation from new S-arm evidence;
- CPR adjudication.

## 14. Authorization

No scientific provider call or paid evaluator call is authorized by this protocol.
