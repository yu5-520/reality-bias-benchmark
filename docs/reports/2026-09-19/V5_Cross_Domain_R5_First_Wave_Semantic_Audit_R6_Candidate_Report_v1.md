# V5 Cross-Domain R5 First-Wave Semantic Audit and R6 Candidate Report v1

Date: 2026-09-19  
Status: **R5 FIRST WAVE COMPLETE / SEMANTIC EFFECT NOT REPLICATE-STABLE / ONE R6 MECHANISM CANDIDATE**

## Evidence identity

- workflow: `35381406873`
- execution SHA: `234468dfe5c9dac66cc8b5249c135942a399369e`
- artifact: `10564055226`
- artifact digest: `sha256:a711f507365504bd59ca179bd3d76ea4c57d97caf6f6be85a6f4ef1f88629457`
- preserved traces: **24 / 24**
- runner errors: **0**
- estimated spend: **USD 1.504547232**
- raw evidence batch hash: `26f63b182ca704fbf8119f5c75894e9f219e0c22ce6fadeaa6eb2dd95b06ea68`

Raw evidence was frozen before structural derivation.

## Structural result

Across 12 matched control/intervention pairs:

- first raw response changed: 12 / 12
- first parsed action envelope changed: 12 / 12
- first decision summary changed: 12 / 12
- Agent path changed: 12 / 12
- final state changed: 12 / 12

This is **not** interpreted as 12/12 causal effect.

The provider is stochastic and exact-output inequality is expected even under same-condition repetition. Therefore structural inequality is only a sensitivity observation.

## Semantic audit

The semantic unit is the executable decision/posture, not exact wording or exact JSON structure.

| Wave | Domain | Semantic reading |
| --- | --- | --- |
| 1 | finance | no replicate-stable material response; both conditions converge on CNY 65m staged limit |
| 2 | finance | no replicate-stable material response; both conditions converge on CNY 65m hold |
| 3 | supply_chain | no replicate-stable material response; both conditions release the same 1200-unit West baseline |
| 4 | supply_chain | **mixed material response**: replicate 1 re-plans to no standard transfer; replicate 2 converges with control |
| 5 | software_engineering | no material response; all branches retain HOLD/no expansion |
| 6 | software_engineering | label-level GO/HOLD variation exists, but executable posture converges on frozen 5% rollout |

Strict result:

- replicate-stable material semantic effect: **0 / 6 cases**
- mixed material local response: **1 / 6**
- label-only / operationally convergent variation: **1 / 6**
- no material local semantic response: **4 / 6**

Therefore the first R5 wave does **not** support a general claim that changing the source metadata from `fact` to `unconfirmed` reliably changes downstream meaning or action.

## Why wave 4 remains scientifically important

Wave 4 replicate 1 contains a traceable path-reconfiguration candidate.

Direct intervention:

`logistics_capacity_assessment.status: fact -> unconfirmed`

is visible only once to `inventory` at turn 5.

The direct experimental overlay is then consumed and is never re-injected.

During that first exposed turn, `inventory` creates two new semantic carriers:

1. `inventory_coverage_assessment` — recomputes regional transfer capacity under safety-stock constraints.
2. a `plan_draft` final-state revision — removes the standard transfers.

After the direct stimulus has disappeared:

- `risk` at turn 6 adopts the no-covered-surplus interpretation and recommends no standard transfers;
- `supply_lead` at turn 7 adopts the non-releasable plan and shifts toward procurement/expedite;
- `sales` at turn 8 repeats the no-covered-regional-source interpretation.

The branch finishes with the no-standard-transfer path.

This is exactly the type of carrier/read/adoption/persistence chain R6 is designed to inspect.

## Why it is not yet System Inertia

The same material path reconfiguration is **not reproduced in replicate 2**.

Also, the control branches independently identify the East buffer problem. Thus the semantic ingredients for re-planning exist without the intervention.

Consequently:

- post-consumption persistence in the observed intervention branch: **YES**
- downstream carrier adoption: **YES**
- intervention-specificity: **NOT ESTABLISHED**
- System Inertia: **NOT ESTABLISHED**
- causal effect of the authority withdrawal: **NOT ESTABLISHED**

Provider stochasticity remains a live competing explanation.

## Next experiment

Do not rerun the six-case R5 wave.

Freeze wave 4 as a post-hoc mechanism candidate and run a targeted matched-control specificity extension from the **same frozen parent**.

The new experiment must:

- keep the exact same parent snapshot and one-shot operator;
- add multiple counterbalanced control/intervention pairs;
- estimate the frequency of the material no-transfer reconfiguration under each condition;
- treat this as a targeted mechanism follow-up, not first-round prevalence evidence;
- keep R7 and CPR outside the experiment.

This directly tests the user's probabilistic-risk hypothesis: a rare path transition matters precisely because it may not appear on every run.
