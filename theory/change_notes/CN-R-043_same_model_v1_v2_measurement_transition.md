# CN-R-043 — Same-Model v1→v2 Measurement-Contract Sensitivity

Date: 2026-09-15  
Status: **COMPLETE — STRONG MEASUREMENT SENSITIVITY OBSERVED; V2 CONSENSUS STILL OPEN**

## Decision

Treat the historical DeepSeek Reviewer-B v1 → DeepSeek Reviewer-v2 transition as an explicit measurement-validity result.

Do not collapse it into ordinary inter-rater reliability and do not interpret it as proof that one annotation layer is semantic truth.

The comparison holds the model family and frozen event population approximately constant while changing the operational definitions, packet/window design, prompt and output contract.

## Offline analysis

Workflow `34995630944` completed successfully.

- compared event population: 70 / 70
- same frozen evidence batch: `94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`
- artifact ID: `10407228786`
- artifact digest: `sha256:1135b79bf99fc7aa57d65c46f36665d64205f8dbeeab3f1051f3ca4e34cca47b`
- provider calls: 0

## Headline result

Historical DeepSeek-v1:

- any C/P/R label: 61 / 70
- C: 24
- P: 25
- R: 25
- primary realized + unauthorized + mechanism-coded: 26

DeepSeek Reviewer-v2 deterministic synthesis:

- C positive: 0 / 70
- P positive: 0 / 70
- event-level R positive: 0 / 70

The magnitude of this transition establishes that semantic operationalization is not a passive reporting choice. It changes the measured phenomenon.

## Mechanism-specific transition

### C

Of 24 v1 C-positive events:

- 22 → `NO_PROMOTION`
- 2 → `SUPPORTED_PROMOTION`
- 0 → `UNSUPPORTED_PROMOTION`

Interpretation: v1 completion-style reasoning was broader than v2's unsupported epistemic/execution promotion construct.

### P

Of 25 v1 P-positive events:

- 22 → `NECESSARY_DECOMPOSITION`
- 3 → `ORIGINAL_GOAL`
- 0 → `UNAUTHORIZED_EXPANSION`

Interpretation: v1 collaboration/confirmation/completeness judgments were broader than v2's unauthorized goal-scope/focus construct.

### R

Of 25 v1 R-positive events:

- 15 → `NOT_REWORK`
- 10 → `CORRECTION`
- 0 → C/P regeneration

Interpretation: v1 revision/reopening behavior was broader than v2's second-order regeneration/laundering/normalization construct.

## Historical primary-26 stress test

The 26 strongest DeepSeek-v1 primary events produce **zero** v2 synthesized C/P/R positives.

Under v2 they are classified as:

- epistemic: 16 N/A, 7 no promotion, 3 supported promotion;
- goal: 21 necessary decomposition, 5 original-goal work;
- goal focus: 26 no material shift;
- retrospective: 21 not rework, 3 correction, 1 legitimation candidate, 1 N/A;
- authorization: 26 authorized.

This is the clearest evidence that the old and new systems are measuring materially different boundaries rather than merely applying different labels to the same fixed construct.

## Authorization transition

Historical v1 → v2:

- 42 AUTHORIZED → AUTHORIZED
- 27 UNAUTHORIZED → AUTHORIZED
- 1 NOT_APPLICABLE → AUTHORIZED

The v2 architecture therefore keeps role/action authorization separate from semantic mechanism synthesis more aggressively than v1.

## Reliability-statistic boundary

Binary raw agreement between v1 and v2 is approximately:

- C: 0.6571
- P: 0.6429
- R: 0.6429

Cohen κ is 0 for each mechanism because v2 has a zero-positive marginal. This is prevalence-degenerate and must not be advertised as a meaningful reliability score.

The scientific object is the **transition matrix**, not κ.

## Interpretation

This result strengthens the methodological case for:

> **freeze behavior first, version semantic measurement later.**

The trace remains the experimental object. C/P/R annotations are measurement outputs whose definitions and versions must remain explicit.

The result also supports the machine/reviewer split:

- machine structure still successfully identifies the relevant state writes, invocations, revisions, lineages and feedback windows;
- semantic review determines whether those structural events actually instantiate the refined CPR boundary.

## Limitations

Do not claim that v2 has been validated merely because it produces fewer positives.

The transition changes several measurement components together:

- semantic definitions;
- prompt;
- packet/window construction;
- output schema;
- review timing/provider call context.

Therefore this is measurement-contract sensitivity, not a clean one-factor rubric experiment.

The same DeepSeek family also means this is not independent Reviewer-v2 replication.

## Current gate

Keep v2 definitions frozen. Do not loosen them to recover historical prevalence.

K=2 remains blocked.

Next scientifically useful work must resolve whether the zero-positive Base result reflects:

1. corrected over-counting in v1; or
2. insufficient Base occurrence / an over-tightened or reviewer-specific v2 measurement boundary.

Resolve that through independent Reviewer-v2 replication and/or additional unchanged-Base subject sampling before upper-bound loop-budget escalation.
