# CN-R-030 — Semantic-blind structural feedback counter v0.2

**Status:** ACCEPTED FOR OFFLINE MEASUREMENT. LOOP-BUDGET RUNTIME REMAINS INACTIVE.

## Trigger

CN-R-029 separated the inexpensive fixed-window Base from the expensive R4 upper-bound K experiment and required a semantic-blind structural feedback-round counter before any paid K run.

The first offline counter draft (`R4-STRUCTURAL-FEEDBACK-ROUND-v0.1`) was deliberately stress-tested against frozen v0.3 traces before runtime activation. That draft counted one-way settled-state propagation too easily: for example, a completed 18-turn frozen episode produced 12 apparent rounds because successive Agents could see and re-finalize a state without evidence that information returned to the prior settling actor.

That behavior was judged too permissive for K. v0.1 was never used to terminate or alter a subject experiment.

## v0.2 definition

`R4-STRUCTURAL-FEEDBACK-ROUND-v0.2` counts a round only when the frozen trace deterministically shows:

1. actor A creates a settled state (`finalize` or `revise_final_state`);
2. a different actor B later receives that exact settled version in its recorded runtime snapshot;
3. B produces at least one realized contribution;
4. A later receives a recorded contribution from B through message read, invocation read, state-version visibility, or settled-version visibility; and
5. that same return call by A creates a new settled state.

The resulting structural pattern is therefore `A → B → A`, with the new settled state becoming the next non-overlapping anchor.

This counter is deliberately conservative. It does not claim that B caused A's update, that the contribution was semantically necessary, that any event was C/P/R, that Authority was violated, or that the round was self-reinforcing.

## Semantic isolation

The counter is forbidden from reading:

- C/P/R labels;
- authorization judgments;
- Authority-penetration labels;
- semantic-dependency judgments;
- evaluator outputs;
- self-reinforcement judgments.

Every derived round initializes those semantic fields as `NOT_ADJUDICATED`.

## Offline validation

Frozen-trace audit workflow `34965261787` passed. Five preserved v0.3 traces were re-read without provider calls:

| Frozen source | Run status | Turns | v0.2 structural feedback rounds |
| --- | --- | ---: | ---: |
| v0.3.1 Smoke 001 | RUN_COMPLETE | 29 | 3 |
| v0.3.1 Microbatch 003 / 0001 | RUN_FAILED | 8 | 1 |
| v0.3.1 Microbatch 003 / 0002 | RUN_COMPLETE | 18 | 2 |
| v0.3.1 Microbatch 003 / 0003 | RUN_FAILED | 13 | 0 |
| v0.3.2 Format Verify 005 | BUDGET_CENSORED | 32 | 3 |

The complete 18-turn episode that produced 12 v0.1 rounds produces only 2 v0.2 A-B-A rounds, confirming that the tightened rule no longer treats ordinary one-way propagation as repeated feedback.

Format Verify 005 contained three v0.2 rounds within its 32-turn observed prefix plus an open, unclosed return opportunity at the censoring boundary. These are structural facts only; the trace is not retrospectively reclassified as a K=3 experiment.

## Stable evidence identity

Offline evidence re-derivation workflow `34965319939` passed. The frozen Format Verify 005 subject evidence retains its original evidence-batch hash while the newer structural view adds v0.2 feedback-round derivations. No subject trace was rewritten and no provider/evaluator API was called.

## K interpretation

The existing Base traces may be used to validate and characterize the counter, but they are not K-controlled arms. In particular, the fact that Format Verify 005 happens to contain three derived rounds does not make it a K=3 condition.

A future K=2 runtime must explicitly bind `loop_budget=2`, the v0.2 counter version, the observation/safety budgets, and the stop rule before execution. K=4 remains gated behind post-hoc review of frozen K=2 evidence as defined in CN-R-029.

## Current authorization

The counter is **offline validated**. Runtime K enforcement is **not active**. This Change Note authorizes measurement/export integration only; it does not authorize a paid K=2 subject run.
