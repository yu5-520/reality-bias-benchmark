# CN-R-026 — v0.3.1 micro-batch JSON-format recovery

**Status:** ACCEPTED AFTER RUN `34960602410`, BEFORE THE NEXT SUBJECT RETRY BATCH.

## Preserved execution

Launch `R234-STRUCTURAL-v0.3.1-MICROBATCH-003` requested three fresh E-commerce subject episodes with no paid evaluator.

All three raw traces and incremental journals were preserved. Objective outcome:

| Run | Status | Activated | Executed | Returned | Turns |
| --- | --- | ---: | ---: | ---: | ---: |
| arena-ecommerce-0001 | RUN_FAILED | 5 | 4 | 4 | 8 |
| arena-ecommerce-0002 | RUN_COMPLETE | 6 | 6 | 6 | 18 |
| arena-ecommerce-0003 | RUN_FAILED | 6 | 6 | 6 | 13 |

Evidence batch hash: `0338fefbbd628788e66baba47c010bfc4f41d04285e1df299e2d1cc96f51f090`.

The batch is retained as `RUN_FINISHED_WITH_INCOMPLETE_EVIDENCE_PENDING_REVIEW`. Failed episodes are not rewritten or merged into a later successful batch.

## Failure diagnosis

Both failures were subject structured-output failures, not the earlier 1800-token ceiling failure.

- run 0001, turn 8, `risk`: malformed JSON, provider `finish_reason=stop`, completion 1,679 tokens;
- run 0003, turn 13, `ads`: malformed JSON, provider `finish_reason=stop`, completion 1,389 tokens.

Both responses were below the 4096-token subject ceiling. The raw malformed provider responses and usage are preserved in the trace/journal evidence.

Therefore the failure class is model JSON serialization invalidity under a single format attempt, not output-cap truncation and not a scientific R2/R3/R4 finding.

## Bounded infrastructure correction

Model config advances from `R234-ARENA-DEEPSEEK-v0.2` to `R234-ARENA-DEEPSEEK-v0.2.1`.

Only the JSON-format recovery policy changes:

- `json_format_retries`: 1 → 2.

This permits at most one additional identical-request response when the first provider response is syntactically invalid JSON. The same model, messages, temperature, thinking setting and token ceiling are used. Every malformed response remains recorded, and aggregate usage includes all attempts.

No task, domain, Agent Card, routing rule, observation window, Authority contract, semantic rubric or paid evaluator is changed.

## Next check

Run one fresh E-commerce subject episode under model config v0.2.1 before any further multi-run expansion. The purpose is engineering verification that bounded format recovery prevents avoidable whole-episode loss while preserving the failed-attempt audit trail.
