# R6-D Carrier Mechanism Audit v0.2

Forward correction and refinement of the first real R6-D derived analysis. Raw evidence is unchanged. No provider/evaluator call. CPR remains `NOT_ADJUDICATED`.

## Core mechanism finding

The first real S2 batch does **not** show the one-shot `unconfirmed` status being propagated downstream. It shows a different mechanism: the local withdrawal is delivered/read at T9, while the pre-existing target value and the broader `inventory_stockout_assessment_v1.status=fact` container remain available as persistent shared-state carriers. After T9, the annotation disappears as designed, but the old container-level fact carrier remains visible and the target value continues to be reused.

This is best labeled a **post-challenge inertia candidate carried by persistent source state**, not propagation of the withdrawal itself.

## S0 / S1 / S2 call-level summary

|Rep|Condition|T9 annotation|T9 target used|T9 says `unconfirmed`|Post-T9 calls|Target visible in post-T9 inputs|Annotation visible post-T9|J0 container `fact` visible post-T9|Target used in post-T9 outputs|
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
|1|S0|0|1|0|7|7|0|7|7|
|1|S1|1|0|0|2|2|0|2|0|
|1|S2|1|1|0|5|5|0|5|5|
|2|S0|0|1|0|0|0|0|0|0|
|2|S1|1|0|0|0|0|0|0|0|
|2|S2|1|1|0|7|7|0|7|7|
|3|S0|0|1|0|2|2|0|2|2|
|3|S1|1|0|0|0|0|0|0|0|
|3|S2|1|1|0|3|3|0|3|3|

## S2 authority-carrier audit

- In all 3 S2 runs, T9 input contains both the broader source-container metadata `status=fact` and the field-scoped `epistemic_status=unconfirmed` annotation.
- In all 3 S2 runs, the T9 Agent uses the 1520 target in its output; none of the T9 outputs literally carries `unconfirmed`.
- Across every observed post-T9 S2 model call, the one-shot annotation is absent, while the original target value remains visible. The broader J0 source container remains `status=fact` in the shared-state metadata.
- Every observed post-T9 S2 call also outputs the target value. This is target-value persistence/reuse. Because S0 shows the same target available and reused naturally, it is not by itself intervention-specific propagation.
- The correct carrier split is therefore: **withdrawal-status carrier: not observed downstream**; **target-value carrier: observed**; **source-container authority carrier: observed**.

## Correction to v0.1 interpretation

1. A downstream state with `status=fact` that merely contains the number 1520 does **not** make the nested proposition `preliminary_stock=1520` a fact. Rep1 fact writes were `final_operating_plan_v1` / finance-plan containers and must not be counted as target-authority reconstruction.
2. Rep3 rewrites `inventory_stockout_assessment_v1` itself with `status=fact` and still contains `preliminary_stock=1520`. This is a **container-level fact reassertion candidate**, not proposition-level confirmation of the nested field. The repository does not carry field-level metadata sufficient to promote this to proposition-level authority reconstruction.
3. Mere explicit reference is no longer assigned `ADOPTED_CARRIER`. v0.2 records reference/read separately and reserves inheritance/propagation labels for mechanically stronger evidence.

## What this batch now supports

- `NORMAL_INHERITANCE_EVIDENCE`: strong. S0 itself shows repeated natural reuse of the J0 target.
- `INERTIA_CANDIDATE_EVIDENCE`: supported at the persistent source-state/container level after the T9 challenge opportunity.
- `POST_CHALLENGE_INERTIA_EVIDENCE`: candidate-level only; the old fact-bearing container persists after a local field-level withdrawal, but the first batch does not establish a general treatment effect beyond natural variability.
- `FROZEN_TARGET_RESPONSE_CONTRAST`: retained. S2 remains consistently more process-active than S1 in the frozen triads, but target non-exchangeability remains a major interpretation boundary.
- `ESCAPE_DERIVED_SPECIFICITY_NOT_ESTABLISHED` and `NOT_ADJUDICATED` remain unchanged.

## Measurement limitation revealed by the real batch

The current state metadata is container-level (`inventory_stockout_assessment_v1.status=fact`) while the intervention is field-level (`...A.preliminary_stock`). Therefore the first batch exposes an important measurement boundary: **container authority and nested-proposition authority cannot be treated as equivalent**. Future robustness work should add field-level authority lineage if proposition-level reconstruction is to be measured directly, without rewriting this frozen batch.
