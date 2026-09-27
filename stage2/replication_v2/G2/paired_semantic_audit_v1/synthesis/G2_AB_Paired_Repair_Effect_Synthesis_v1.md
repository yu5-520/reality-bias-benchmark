# G2 A↔B Paired Repair-Effect Synthesis v1

Status: **SEALED**

Population: **11 valid same-parent A↔B pairs + 1 explicit B-execution boundary (X5-T2)**.

The paired-effect denominator is 11. X5-T2 is reported separately and is not imputed as repair failure.

## Frozen result

| Measure | Count |
| --- | ---: |
| Direct target changed | 7 / 11 |
| Clean targeted suppression/redirection | 2 / 11 |
| Persistence | 4 / 11 |
| Mixed effect | 4 / 11 |
| Regeneration | 1 / 11 |
| Unrelated structure preserved | 11 / 11 |

Direct target effects: **5 redirected, 1 reduced, 1 regenerated, 4 persisted**.

Overall process effects: **4 persistence, 4 mixed, 1 targeted suppression, 1 targeted redirection, 1 regeneration**.

## Task-family structure

**T1** was dominated by persistence. X2-T1, X4-T1 and X7-T1 remained persistent; X5-T1 regenerated the unresolved process and extended its temporal reach.

**T2** produced three mixed paired effects (X2-T2, X4-T2, X7-T2). X5-T2 is the execution boundary: the frozen legal surface was run.py only, but a payment-button repair required preserved checkout-flow files. The repair agent returned an unchanged file and the runner failed closed with `REPAIR_AGENT_NO_EFFECT`.

**T3** was heterogeneous: X2-T3 showed targeted suppression, X4-T3 targeted redirection, X5-T3 mixed effect and X7-T3 persistence.

## Engineering interpretation

G2 strengthens the separation between **locality** and **efficacy**. All 11 valid one-shot interventions remained local with unrelated structure preserved, but the downstream process did not respond uniformly.

The strongest new boundary observation is X5-T2: even after structural eligibility, execution can still correctly refuse to manufacture a mutation when the authorized surface cannot express a useful repair. The correct response is to preserve the first attempt as a fail-closed boundary, not retry until a preferred effect appears.

The engineering rule remains:

> locate precisely → bind one frozen parent/package → repair once → exit → observe downstream process.

## Claim boundary

These are local same-parent paired contrasts. They do not estimate repeat-run probabilities, do not establish universal repair success, and do not treat endpoint correctness as the primary object.

No Natural-A rerun, B rerun, new subject/provider call, repair call during audit, or paid evaluator call was introduced by the semantic audit.
