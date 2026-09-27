# G4 A↔B Paired Repair-Effect Synthesis v1

Status: **SEALED**

Population: **11 valid same-parent A↔B pairs + 1 explicit B-execution boundary (X5-T2)**.

The paired-effect denominator is 11. X5-T2 is reported separately and is not imputed as repair failure.

## Frozen result

| Measure | Count |
| --- | ---: |
| Direct target changed | 6 / 11 |
| Clean targeted suppression/redirection | 2 / 11 |
| Persistence | 5 / 11 |
| Mixed effect | 3 / 11 |
| Regeneration | 1 / 11 |
| Unrelated structure preserved | 11 / 11 |

Direct target effects: **4 redirected, 1 reduced, 1 regenerated, 5 persisted**.

Overall process effects: **5 persistence, 3 mixed, 1 targeted suppression, 1 targeted redirection, 1 regeneration**.

## Task-family structure

**T1** is uniformly persistent across X2, X4, X5 and X7. Each one-shot process-state revision remained local, yet the unresolved/invalid continuation pattern survived to the turn budget with no repository consequence.

**T2** contains two route-redirection cases (X2-T2, X7-T2), one regeneration case (X4-T2), and one explicit execution boundary (X5-T2). X4-T2 is the strongest mechanism observation: the natural arm finalized after 19 turns with the payment-button changes, while the repaired arm reopened into a 64-turn continuation over the same two application files.

**T3** spans targeted suppression (X2-T3), targeted redirection (X4-T3), mixed response (X5-T3), and persistence (X7-T3).

## Execution boundary

X5-T2 is **REPAIR_AGENT_NO_EFFECT**. The frozen legal surface contained only `file:run.py`; the repair agent returned a byte-identical replacement. The runner stopped before a repair action/post-repair continuation and preserved the first attempt. It is not rerun and is not counted as a repair-effect failure sample.

## Engineering interpretation

G4 reinforces the separation between **repair locality** and **downstream efficacy**. Locality was preserved in all 11 valid pairs, but most downstream trajectories either persisted or remained mixed.

The combination of X4-T2 and X5-T2 is especially informative: a local repair can regenerate broader downstream work even while respecting the repair boundary, while another structurally eligible package can correctly fail closed when its authorized surface cannot express a non-no-op mutation.

## Claim boundary

These are local same-parent paired contrasts. They do not estimate repeat-run probabilities, establish universal repair success, or make endpoint correctness the primary object.

No Natural-A rerun, B rerun, new subject/provider call, repair call during audit, or paid evaluator call was introduced by the semantic audit.
