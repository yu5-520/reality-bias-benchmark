# CN-R-049 — Guarded Real R7 Execution Path

Date: 2026-09-16  
Status: IMPLEMENTED / NOT DISPATCHED / ZERO PAID CALLS IN THIS UPDATE

## 1. Change

The repository now contains a complete guarded execution path for a future real-model R7 paired orchestration batch without converting repository-update approval into paid-run authorization.

Implemented components:

- `arena/build_orchestration_manifest.py` — explicit model binding plus counterbalanced pair order;
- `arena/providers.py` — provider factory and explicit Bailian subject-config boundary;
- `arena/cost_budget.py` — call cap, pre-call monetary reservation and usage-based accounting;
- `arena/run_orchestration_real.py` — sequential paired real-subject runner;
- `.github/workflows/r7-orchestration-paired-real.yml` — prepare-only by default, explicitly authorized subject job;
- `schemas/paid_subject_authorization_v0.1.schema.json`;
- `schemas/r7_paired_run_summary_v0.1.schema.json`;
- updated `schemas/orchestration_comparison_v0.1.schema.json` for real subject evidence pending semantic review.

## 2. Counterbalanced pair order

The manifest no longer runs every pair in one fixed Free→Structured order.

Odd trials use:

`FREE_THEN_STRUCTURED`

Even trials use:

`STRUCTURED_THEN_FREE`

The exact order is frozen in each manifest row as `pair_execution_order` and `pair_order_pattern`.

This reduces a simple systematic time/order confound without claiming to eliminate provider drift.

## 3. Explicit model/provider binding

The R7 manifest builder now accepts an explicit model-config path and records:

- model config path/version/hash;
- provider identity;
- model alias;
- shared task/Agent/Arena/structured-policy bindings.

The guarded runner refuses a provider input that does not match the frozen model config.

Bailian subject execution is accepted only when the selected config has an explicit `subject` block. Existing reviewer-only configs are not silently reused as subject settings.

## 4. Paid-run authorization

A future real run requires all of the following simultaneously:

- `--execute-real-api`;
- exact authorization phrase `CALL_REAL_R7_API`;
- named provider matching the model config;
- positive explicit spending ceiling;
- currency matching the config pricing snapshot;
- positive maximum subject-call count;
- exact paired manifest and file hashes.

The workflow defaults to:

- `confirm = PREPARE_ONLY`;
- `provider = UNRESOLVED`;
- `spending_ceiling = 0`;
- `max_subject_calls = 0`.

Therefore a generic “执行/继续” repository instruction cannot dispatch paid subject calls through this path.

## 5. Budget guard

The budget wrapper uses the selected model-config pricing snapshot.

Before a model call it reserves budget using:

- serialized UTF-8 input bytes as a conservative input proxy;
- configured subject `max_tokens`;
- peak/list price from the frozen config;
- configured DeepSeek JSON-format recovery attempt count where applicable.

After a provider response it recomputes estimated cost from provider-reported usage.

A separate maximum subject-call cap is enforced.

The accounting is an engineering stop guard, not a claim to reproduce the provider's final invoice. HTTP/network retry billing remains provider-dependent.

## 6. Evidence behavior

For every attempted run the real runner preserves:

- authorization hash;
- manifest and config bindings;
- raw trace;
- evidence-compatible journal;
- condition and pair order;
- budget state after the run;
- errors and unattempted run identities if a guard stops execution.

A completed pair produces an orchestration comparison record with:

`SUBJECT_EVIDENCE_PENDING_SEMANTIC_REVIEW`

This is structural subject evidence only. C/P/R semantic interpretation remains deferred.

The standard `arena.evidence` pipeline can then freeze any preserved traces. No paid evaluator is automatically invoked.

## 7. Current execution state

The guarded workflow was added to the repository but was **not dispatched** as part of this change.

No provider/model/repeat count/spending ceiling has been selected by this change note.

No paid subject call or Reviewer call occurred during this implementation step.
