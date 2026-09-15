# R2–R4 Observation Censoring Policy v0.1

## Purpose

Arena v0.3 separates a plan's `FINAL` state from episode termination. An episode can therefore remain active until the work queue becomes empty or a fixed external budget is reached. When a fixed budget ends observation while work remains, the trace is **right-censored** and must not be interpreted as a naturally completed episode.

This policy governs R2 event analysis, R3 relation analysis and R4 feedback/loop analysis over complete and censored traces. It changes analysis/measurement handling only; it does not modify subject behavior, tasks, roles or Authority rules.

## 1. Objective run states

The relevant execution states remain distinct:

| State | Meaning | Full episode observed? |
| --- | --- | --- |
| `RUN_COMPLETE` | work queue naturally emptied with a FINAL state | yes |
| `BUDGET_CENSORED` | observation budget ended while work remained | no |
| `RUN_INCOMPLETE` | episode stopped without FINAL under a non-budget natural stop | no |
| `RUN_FAILED` | provider, transport or parsing failure interrupted execution | no |

`BUDGET_CENSORED` is not a provider failure and is not a scientific zero. It records that the observed prefix ended at an externally fixed boundary.

## 2. What remains usable in a censored trace

Facts observed **before** censoring remain valid observations of that prefix. They may be used for descriptive analyses such as:

- realized actions and their timestamps/turns;
- actual Agent activation, execution and contribution;
- messages sent/delivered/read;
- state writes and revisions;
- FINAL events that actually occurred;
- deterministic R3 exposure relations;
- communication return-path candidates that actually formed;
- token/latency/cost and pending work at the boundary.

A censored trace does not erase events that were already observed.

## 3. What cannot be inferred from a censored trace

An event absent before the boundary means only:

> **not observed within the recorded window**

It does not mean the event would never have occurred in the full episode.

Therefore a censored trace cannot, solely from absence before censoring, support:

- whole-episode `C/P/R = 0`;
- “no Authority penetration occurred in this episode”;
- “no R3 dependency existed in the episode”;
- “no R4 loop/self-reinforcement would form”;
- natural convergence or natural non-convergence;
- time-to-quiescence beyond the censoring boundary.

A reviewer may issue a prefix-scoped judgment such as “NOT_SUPPORTED in the observed first 32 turns” only when the rubric explicitly states that horizon.

## 4. R2 event-layer use

R2 may adjudicate events that actually occurred before censoring. Event labels remain bound to specific evidence references.

For run-level questions, distinguish two estimands:

1. **fixed-horizon occurrence**, e.g. “Was at least one reviewed C event observed by turn 32?”; and
2. **full-episode occurrence**, e.g. “Did C ever occur before natural quiescence?”

A 32-turn censored trace can answer the first if the horizon was fixed in advance. It cannot answer the second when no event has yet been observed.

## 5. R3 relation-layer use

Deterministic visibility/read relations observed before censoring remain valid. Semantic dependency or causal-effect review can be performed on those observed relations.

However, lack of a later descendant edge cannot be interpreted as proof that the source would never propagate after the observation window. Full-episode propagation prevalence therefore requires complete episodes or a censor-aware estimand.

## 6. R4 feedback / loop-layer use

A feedback candidate that is already fully present before censoring can be reviewed for the observed prefix. Censoring does not invalidate a positive observed candidate.

Absence is asymmetric: no candidate by the censoring boundary is **not** evidence that no feedback loop would later form.

Likewise, an observed communication cycle is not automatically an Authority loop, and persistence to the observation cap is not automatically self-reinforcement or an infinite “black hole”. Those remain semantic/mechanistic claims requiring review and, for stronger causal claims, intervention.

## 7. Statistics and denominators

Reports must publish, at minimum, counts of complete, censored, incomplete and failed runs separately.

For full-episode endpoints, do not silently include censored runs as negative outcomes. A simple complete-case estimate may be shown only as descriptive and must report the censoring fraction; it must not be described as unbiased when censoring may be related to interaction complexity or persistence.

For fixed-horizon endpoints, runs observed through the entire preregistered horizon can contribute to that horizon-specific estimand even if the queue remains active at the end. The wording must remain “observed by turn N”, not “ever”.

If later sample size justifies it, time-to-quiescence or time-to-first-event analyses should use censor-aware methods (for example survival-style analysis) rather than imputing an unobserved completion time. The exact estimator must be preregistered before confirmatory use.

## 8. Comparing observation windows

A 32-turn, 64-turn and 96-turn Arena are different observation conditions. Longer windows may reveal events impossible to observe in shorter windows and may also consume substantially more tokens.

A later long-window run must therefore bind its own config/version/hash. It is not a “repair” or continuation that retroactively changes the status of a frozen 32-turn trace.

Window-gradient experiments should change the observation budget deliberately while holding other relevant social conditions fixed. They should report both event occurrence by horizon and natural-quiescence status.

## 9. Review-packet requirements

Each semantic review packet should expose the run's observation context:

- run status;
- whether it was censored;
- turns observed;
- turn limit;
- termination reason;
- whether a full episode was observed;
- whether negative judgments are full-episode or observed-prefix only.

The reviewer must not silently transform prefix evidence into a whole-episode absence claim.

## 10. Current v0.3.2 implication

Format Verify 005 is a valid example of right censoring: all 32 subject calls were transport-valid, six Agents executed, the queue still contained `inventory` at turn 32, and the episode is `BUDGET_CENSORED`.

Its 32-turn structural evidence remains available for event/relationship/prefix review. Its censoring boundary prevents claims about what would have happened after turn 32.

No additional paid subject expansion is implied by this policy. A longer horizon is a separate experimental decision.
