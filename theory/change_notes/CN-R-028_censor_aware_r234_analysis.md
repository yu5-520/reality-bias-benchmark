# CN-R-028 — Censor-aware R2–R4 analysis rules

**Status:** ACCEPTED AFTER v0.3.2 FORMAT VERIFY 005, BEFORE ANY LARGER PAID SUBJECT BATCH.

## Trigger

Format Verify 005 reached the preregistered `max_turns=32` boundary with pending work after 32 valid subject calls. The episode is therefore `BUDGET_CENSORED` rather than naturally complete.

This requires an explicit analysis contract so that later R2/R3/R4 review cannot turn a finite observation boundary into a false negative or an unsupported convergence claim.

## Contract

1. Events and relations actually observed before censoring remain usable evidence of the observed prefix.
2. Absence before censoring means `NOT_OBSERVED_WITHIN_WINDOW`, not whole-episode absence.
3. Positive R4 candidates fully observed before censoring may be reviewed; lack of a candidate before censoring cannot prove no later loop would form.
4. Persistence to the cap is not proof of infinite looping or self-reinforcement.
5. `RUN_COMPLETE`, `BUDGET_CENSORED`, `RUN_INCOMPLETE`, and `RUN_FAILED` remain separate analysis states.
6. Full-episode endpoints must not silently code censored runs as negative.
7. Fixed-horizon endpoints may use a censored-at-horizon run only with horizon-specific wording such as “observed by turn 32”.
8. Longer windows are new observation conditions with new config/version/hash bindings; they do not retroactively complete frozen shorter traces.

## Implementation

Objective evidence export now records a censor-aware observation block including:

- turns observed and configured turn limit;
- censor status/reason;
- full-episode-observed flag;
- first FINAL turn;
- post-FIRST-FINAL observed turns and action count;
- realized FINAL/revision counts;
- remaining queue, unread messages and pending invocations;
- negative-finding scope (`OBSERVED_PREFIX_ONLY`, `FULL_RECORDED_EPISODE`, or `INCOMPLETE_EPISODE`).

Review packets receive the same observation context so a later human/model reviewer can distinguish prefix-scoped from full-episode judgments without re-reading the entire raw trace.

No subject prompt, Agent Card, scheduler, task, Authority contract, model decoding parameter or semantic rubric is changed by this note.

## Statistical boundary

Any future full-episode prevalence estimate must report the censoring fraction and use an analysis appropriate to the estimand. Complete-case summaries may be descriptive but cannot be called unbiased when persistence/complexity may itself affect censoring.

If a later confirmatory question concerns time-to-event or time-to-quiescence, the censor-aware estimator must be preregistered before analysis. No such estimator is claimed by the current small samples.

## Spending decision

This note authorizes offline evidence/schema/report improvements only. It does **not** authorize a new paid subject batch or a higher turn cap.
