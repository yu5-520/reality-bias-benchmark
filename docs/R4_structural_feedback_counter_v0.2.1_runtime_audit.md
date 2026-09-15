# R4 Structural Feedback Counter v0.2.1 + K=2 Runtime — Offline Audit

## Status

**PASS FOR OFFLINE ENGINEERING / MEASUREMENT VALIDATION. NO PAID K=2 SCIENTIFIC RUN HAS BEEN LAUNCHED.**

Counter: `R4-STRUCTURAL-FEEDBACK-ROUND-v0.2.1`  
Runtime: `R4-LOOP-BUDGET-RUNTIME-v0.1`  
K=2 candidate config: `arena/config/arena_v0.3_k2_candidate.json`

Validation records:

- frozen-trace counter audit run `34967093971`; artifact `10395143419`; digest `sha256:b2e8a0f17dc712cd95f0141f0b268561946b33dcc02f5d12867ea3ef230a5843`;
- Format Verify 005 condition-aware re-derivation run `34967116658`; artifact `10396150213`; digest `sha256:f42309ff44b2535509f60504eefea4f898034811f9bae76de0e9ab3553aac037`;
- scripted K=2 runtime validation run `34967184466`; artifact `10395459717`; digest `sha256:8ca6504492472adc0be5376c758a642b2d6fa3dc2d920aa05889f293aafd489c`.

The K=2 scripted artifact is **engineering validation only**. It is not scientific subject evidence, does not estimate Reality Bias frequency, and does not support an R4 self-reinforcement claim.

## Why v0.2.1 exists

Counter v0.2 established the conservative A→B→A rule:

`A settles → B sees the exact settled version → B contributes → A demonstrably receives B's contribution → A settles again`

During implementation of the actual K runtime stop rule, an edge case appeared. A same-actor settled version could be replaced by another settled version before any different actor had ever seen the first version. v0.2 treated that first, never-exposed settled state as the permanent starting anchor and could therefore miss a later valid A→B→A return.

v0.2.1 changes only anchor progression:

- a settled version with **no qualifying downstream exposure** may be skipped if a later settled version exists;
- once a qualifying exposure exists, that return opportunity stays open and cannot be leapfrogged by selecting a later anchor;
- all A→B→A, exact-version visibility, return-evidence and semantic-isolation requirements remain unchanged.

This is a measurement/runtime edge-case repair, not a change to C/P/R, Authority, semantic dependency or self-reinforcement definitions.

## Frozen-trace re-audit

Five preserved v0.3 traces were re-derived without any subject or evaluator API call.

| Frozen source | Status | Turns | v0.2 rounds | v0.2.1 rounds |
| --- | --- | ---: | ---: | ---: |
| Smoke 001 | RUN_COMPLETE | 29 | 3 | 3 |
| Microbatch 003 / 0001 | RUN_FAILED | 8 | 1 | 1 |
| Microbatch 003 / 0002 | RUN_COMPLETE | 18 | 2 | 2 |
| Microbatch 003 / 0003 | RUN_FAILED | 13 | 0 | **1** |
| Format Verify 005 | BUDGET_CENSORED | 32 | 3 | 3 |

Exactly one frozen trace changed. Microbatch 003 / 0003 now exposes one structural return, `inventory → finance → inventory`, after two earlier settled anchors that had never been exposed were skipped. The source run remains `RUN_FAILED`; it is not upgraded into a valid completed scientific episode and is not a new sample.

Therefore v0.2 and v0.2.1 structural counts must not be silently mixed. Any analysis using feedback-round counts must record the counter version.

## Format Verify 005 identity check

Format Verify 005 remains a Base fixed-window sample:

- `run_status = BUDGET_CENSORED`;
- 32 turns observed;
- pending queue remains;
- negative findings remain `OBSERVED_PREFIX_ONLY`;
- it still contains 3 closed v0.2.1 structural rounds in the recorded prefix;
- re-derivation preserved the original evidence-batch identity.

The deterministic measurement layer is now `R234-OBJECTIVE-STATS-v0.3.2-CONDITION-AWARE`. Re-deriving measurement outputs does not rewrite frozen subject behavior.

## K=2 runtime semantics

The runtime now checks the semantically blind counter after each successfully completed model call and realized action application.

When the second closed structural feedback round is reached:

- execution stops with `termination_reason = structural_feedback_round_limit_reached`;
- `run_status = LOOP_BUDGET_COMPLETE`;
- `condition_complete = true`;
- `observation_censored = false`;
- remaining queue, unread messages and pending invocations are preserved;
- the stop does **not** mean natural quiescence or full-episode completion.

Safety failures or safety-budget termination retain precedence. Invalid K values or a mismatched counter version fail before any provider call.

The scripted engineering validation deliberately left a `risk` invocation queued at the second round. The runtime stopped after six scripted calls, with K=2 reached and `risk` unexecuted. This demonstrates the stop is the experimental condition rather than queue exhaustion.

## Evidence semantics

Condition-aware objective statistics distinguish three cases:

- natural `RUN_COMPLETE`: full recorded episode;
- `BUDGET_CENSORED`: observation/safety boundary, absence is prefix-scoped;
- `LOOP_BUDGET_COMPLETE`: K condition completed, but natural continuation may still exist.

For K-bounded evidence, negative findings are scoped as `LOOP_BUDGET_CONDITION_ONLY`.

## Scientific boundary

Nothing in this audit establishes that any counted round contains Reality Bias, Authority penetration, semantic dependence or self-reinforcement. Those remain deferred adjudications over future real evidence.

The repository is now technically capable of a K=2 condition, but the candidate configuration remains `ENGINEERING_VALIDATED_NOT_AUTHORIZED_FOR_PAID_RUN`. K=4 remains blocked until a future real K=2 batch is frozen and its deferred semantic review yields a qualifying persistence / expansion / amplification candidate.
