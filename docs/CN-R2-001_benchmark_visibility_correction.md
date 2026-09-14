# CN-R2-001 — Benchmark visibility / executability correction

## Trigger

Real-model Wave 1 attempt 2 completed 252/252 cells but produced a global floor effect: target Bias Generation and Bias Realization were essentially zero across the benchmark.

Inspection of raw subject outputs identified an implementation error rather than evidence against the theory:

1. the runner exposes the field named `hidden_gap` to the subject model as `AVAILABLE CONTEXT`;
2. benchmark v0.2 stored explicit authority prohibitions in that field (for example, that a value must not be promoted or a stage must not be reopened);
3. several P/R tasks also lacked the operational data needed to complete the task, producing refusals instead of scope/reopen decisions.

The supposed Baseline therefore received substantial boundary information and, in several items, an under-specified task. It was not the intended no-extra-Authority-control baseline.

## Decision

**Attempt 2 is retained as an implementation-diagnostic run and is not eligible for R2 PASS/FAIL inference.**

This is not a theory-driven exclusion. The defect affects the treatment itself and is visible directly in the frozen prompts/raw outputs.

## Correction: R2-BENCH-v0.2.1

All 12 items are revised symmetrically under the already-frozen weak / medium / strong / adversarial-boundary gradient.

- The legacy code field `hidden_gap` now contains only subject-visible operational context/data.
- The actual authority contract is represented in `authorized_behavior`, which is visible to the blinded evaluator/harness but not to the subject model.
- Baseline/I-only/V-only/T-only/Full receive the same subject-facing task/context; only the harness gates differ.
- Prompt-only remains the explicit natural-language boundary comparator.
- Each task now contains enough operational data to be completed without asking for missing reports/catalogs/check outputs.
- No item is added or removed after seeing its individual outcome; the complete 12-item set is revised by one common visibility/executability rule.

## What did not change

- R0/R1 theory contract;
- C↔I, P↔V, R↔T primary-mapping hypothesis;
- seven R2 conditions;
- subject model and decoding configuration;
- evaluator model and blinded-to-condition design;
- 3-repeat Wave 1 policy;
- R2 Gate.

## Provenance

Attempt 2 Git commit: `35a828d646ad6f09ee1884215536affbd4f865d9`.
Its raw artifact is preserved by GitHub Actions and should be cited only as benchmark/harness diagnostic evidence, not as a scientific R2 result.
