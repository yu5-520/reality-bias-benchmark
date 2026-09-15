# CN-R2-022 — Micro-pilot evaluator event-index repair

**Status:** ACCEPTED AFTER RAW MICRO-PILOT GENERATION, BEFORE RE-CODING FAILED TRACES.

## What succeeded

Micro-pilot run `34933874204` generated all five fresh E-commerce Arena traces successfully under the repaired 1800-token subject cap. Activated-agent counts were 4, 4, 4, 4, and 6; turn counts were 2, 2, 2, 2, and 8. The previous subject-output truncation failure therefore did not recur in the five-run pilot.

## What failed

The blinded evaluator successfully coded runs `0004` and `0005`, but rejected `0001`, `0002`, and `0003` because the returned `coded_events` included a non-Authority event index (a finalization event) or otherwise violated the exact Authority-event index set. This is an evaluator output-format/index-selection defect, not a subject-trace failure.

## Repair

Evaluator version advances from `R2-ARENA-EVAL-v0.1.1` to `R2-ARENA-EVAL-v0.1.2`.

No C/P/R definition, Authority contract, task, trace, or scoring rule changes. The only prompt clarification is an explicit `allowed_authority_event_indices` whitelist and the instruction that `coded_events` must contain exactly those indices once each and no other trace event.

The validator remains unchanged and strict.

## Cost-preserving recovery

The five successful raw subject traces are frozen and MUST NOT be regenerated for this repair. The two already-valid v0.1.1 evaluations (`0004`, `0005`) are retained for the engineering micro-pilot. Only the three failed evaluations (`0001`, `0002`, `0003`) are re-coded with v0.1.2, then merged for micro-pilot analysis.

Because this micro-pilot is not a prevalence estimate or final confirmatory dataset, mixed evaluator prompt versions are acceptable for the sole decision of whether the pipeline and natural topology are worth scaling. Any later scientific discovery wave must use one frozen evaluator version uniformly across all traces.
