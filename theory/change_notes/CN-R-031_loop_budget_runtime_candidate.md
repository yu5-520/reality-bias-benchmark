# CN-R-031 — K=2 loop-budget runtime candidate

**Status:** ACCEPTED FOR OFFLINE ENGINEERING VALIDATION. PAID K=2 COLLECTION NOT AUTHORIZED BY THIS NOTE.

## Trigger

CN-R-029 separated Base fixed-window measurement from expensive R4 upper-bound probing. CN-R-030 froze the first conservative semantic-blind A→B→A counter for offline measurement. The remaining prerequisite was to bind that structural counter to an actual runtime K stop without turning K into a semantic or evaluator-driven variable.

## Runtime decision

`R4-LOOP-BUDGET-RUNTIME-v0.1` is added as a subject-runtime control that is active only when a configuration explicitly provides both:

- `loop_budget` equal to an initially authorized value, currently 2 or 4; and
- the exact `loop_budget_counter_version`.

Base configurations omit these fields and retain their existing behavior.

For the current engineering candidate, `arena/config/arena_v0.3_k2_candidate.json` binds `K=2` to `R4-STRUCTURAL-FEEDBACK-ROUND-v0.2.1` while retaining the Arena v0.3.2 social architecture and the 32-turn / 64-invocation / 128-pending-message safety caps.

The candidate config is explicitly marked `ENGINEERING_VALIDATED_NOT_AUTHORIZED_FOR_PAID_RUN`.

## Counter patch discovered during runtime integration

The first runtime test exposed a measurement edge case in counter v0.2. A settled version that had never been exposed to any different actor could block the counter from considering a later settled version that did participate in a valid A→B→A return.

Counter v0.2.1 therefore permits only **superseded, unexposed** settled anchors to be skipped. It does not permit an already-exposed open return to be leapfrogged. The A→B→A definition and semantic isolation remain unchanged.

This patch changed one of five frozen v0.3 audit traces: failed Microbatch 003 / run 0003 changes from 0 to 1 structural round. The new round is `inventory → finance → inventory`. The source remains a failed run; the change is a deterministic measurement-version difference, not new behavior or a new sample.

Frozen-trace audit run: `34967093971`  
Artifact: `10395143419`  
Digest: `sha256:b2e8a0f17dc712cd95f0141f0b268561946b33dcc02f5d12867ea3ef230a5843`

## K completion semantics

When the configured K boundary is reached after a completed subject call and its realized actions:

- termination reason is `structural_feedback_round_limit_reached`;
- run status is `LOOP_BUDGET_COMPLETE`;
- the experimental condition is complete;
- the run is not marked `BUDGET_CENSORED`;
- the run is not treated as natural quiescence or a full episode;
- remaining queue / pending invocations / unread messages remain recorded.

Safety failures and safety-budget termination retain precedence over K completion.

Condition-aware objective statistics use `LOOP_BUDGET_CONDITION_ONLY` as the negative-finding scope. A missing event after K termination is therefore not reported as a full-episode zero.

## Offline K=2 validation

ScriptedProvider engineering validation run `34967184466` passed. The scripted path intentionally produced two closed A→B→A structural rounds and queued a further `risk` invocation immediately before the second close. The runtime stopped at the second round after six scripted model calls and left `risk` pending and unexecuted.

Artifact: `10395459717`  
Digest: `sha256:8ca6504492472adc0be5376c758a642b2d6fa3dc2d920aa05889f293aafd489c`

The workflow explicitly verifies that every model call used `SCRIPTED_PREFLIGHT_ONLY` and carried no provider usage record. This is **engineering validation only**, not scientific evidence.

## Frozen Base re-derivation

Format Verify 005 was re-derived with the condition-aware objective layer and counter v0.2.1 in run `34967116658`.

It remains `BUDGET_CENSORED`, with 32 observed turns, pending work, `OBSERVED_PREFIX_ONLY` negative scope and 3 recorded structural rounds. The source evidence-batch identity is unchanged.

Artifact: `10396150213`  
Digest: `sha256:f42309ff44b2535509f60504eefea4f898034811f9bae76de0e9ab3553aac037`

## Scientific boundary

This implementation does not establish an R4 result. It does not show that any structural feedback round is biased, unauthorized, semantically dependent, persistent, amplifying or self-reinforcing.

A future real K=2 subject batch must still be explicitly authorized and frozen before semantic review. K=4 remains unavailable until that K=2 evidence passes the CN-R-029 deferred review gate. No automatic K escalation is permitted.
