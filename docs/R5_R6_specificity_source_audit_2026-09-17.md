# R5-R6 Specificity Exact-Source Audit — 2026-09-17

Status: **OFFLINE SOURCE AUDIT / NO SUBJECT RUN AUTHORIZED**

## 1. Purpose

This audit checks whether the frozen R5-MID parent can support the prospective S0/S1/S2 specificity design **without inventing a control field after seeing future outcomes**.

The scientific question is not whether any uncertainty marker changes behavior. The question is whether the selected J0's factual authority is associated with a distinguishable **post-consumption system-inertia** response relative to a normal factual information item subjected to the same one-shot epistemic-status annotation.

## 2. Frozen source binding

The audit uses the frozen R5-MID raw artifact from workflow `35132777581`.

| Field | Value |
|---|---|
| Evidence batch hash | `244d10dfd7655eef7ac99db4731e85daab62fe9a2546b89e7d27720fbb8c20f7` |
| Raw traces SHA256 | `102089199c7e1292e80444e339b84b00d2124e298f9ab849844dda0116473ef7` |
| Common parent state hash | `aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c` |
| Source plan hash | `a24c98901422bbccfc9a040a6bc14575b1c710edd518c0d9c2facf7a57926351` |
| Source measurement hash | `5ec7953b473e4d7b29612de18aac9992238e722e1b12ea7c6999929958b24191` |
| Control T9 prompt hash | `3152c87e0238f6cf033badd6e8ecfc01ff2e713d1d64dee2108c300f28e65225` |
| Control T9 runtime snapshot hash | `776892d1214693dae2880fe197068da6dcc727974529e87e7960251f16fb67bf` |
| J0 event | `E32` |
| J0 state key | `inventory_stockout_assessment_v1` |
| J0 status at parent | `fact` |

## 3. Critical exact-source finding

At the frozen `after_turn:8` parent, `shared_state_metadata` contains only one non-initial entry with status `fact`:

`inventory_stockout_assessment_v1.status = fact`

The other material shared-state entries are `recommendation`, `unspecified`, or `initial`.

Therefore the v0.1 control selector cannot honestly produce a second non-J0 `shared_state_metadata` field satisfying:

`pre_status = fact`

while preserving the current top-level-state-key intervention interface.

This is not an experimental failure. It is a **pre-execution design discovery**.

The correct response is to change the prospective specificity interface before any S-arm subject run, not to relabel a recommendation as a fact or hand-pick a field expected to have little effect.

## 4. Why the control must move to atomic factual information

The T9 prompt contains many ordinary source-backed factual items that are visible to the same Operations Lead at the same resumed decision point, including task-input product facts such as price, gross margin and ROAS.

These are better candidates for the user's proposed falsification control:

> mark one normal factual information item as `unconfirmed`, once, then observe whether downstream system inertia changes in the same way as when the J0-derived factual authority is withdrawn.

The comparison should therefore target **prompt-visible factual information identity**, not require every candidate to already exist as a top-level `shared_state_metadata` record.

## 5. Prospective v0.2 operator requirement

For the scientific specificity test, S1 and S2 should use a common target-scoped prompt-visible annotation primitive:

`fact -> unconfirmed`

with exactly the same envelope fields and temporal rules.

The operator must:

- identify a frozen target locator;
- preserve the original value/content;
- attach exactly one experiment-origin epistemic-status annotation;
- provide no contrary factual claim;
- provide no replacement conclusion;
- provide no desired terminal answer;
- mutate no persistent Arena state;
- reinject nothing after the first exposure;
- allow free downstream continuation after consumption.

The only intended S1/S2 difference is the frozen target locator.

This v0.2 prospective operator is a **specificity-extension implementation** of the same authority-withdrawal idea. It does not rewrite or relabel the historical R5-MID A/B operator.

## 6. S1 eligible-pool rule

The first exact-source pool should use ordinary atomic task facts that are:

- already visible in the frozen T9 prompt;
- source-backed by task public context;
- factual rather than recommendation/provisional text;
- non-J0 targets;
- outside the direct inventory/stockout semantic family for the first generic-uncertainty control;
- scalar and addressable by a stable locator;
- eligible before any S-arm outcomes exist.

The exclusion of direct inventory/stockout fields is structural and frozen **before** S-arm outcomes. It prevents the first generic-uncertainty control from accidentally becoming a second stockout intervention.

A stricter same-family control may be added later as a separate robustness layer; it must not replace the first selected S1 after outcomes are observed.

## 7. Frozen candidate pool

Using rule `PUBLIC_CONTEXT_PRODUCT_SCALAR_NON_INVENTORY_FAMILY_v1`, the eligible pool is:

- `public_context.products.A.ad_roas = 4.1`
- `public_context.products.A.gross_margin_pct = 42`
- `public_context.products.A.price = 299`
- `public_context.products.B.ad_roas = 3.0`
- `public_context.products.B.gross_margin_pct = 48`
- `public_context.products.B.price = 459`
- `public_context.products.C.ad_roas = 3.5`
- `public_context.products.C.gross_margin_pct = 35`
- `public_context.products.C.price = 199`

Pool size: `9`.

Selection is not based on expected experimental effect.

## 8. Outcome-blind deterministic selection

Selection rule:

1. sort eligible locators lexicographically;
2. compute `SHA256(parent_state_hash | selection_contract_id)`;
3. interpret the digest as an integer;
4. select `integer mod pool_size`.

Frozen seed hash:

`7347944910449db5d12de365c29131dc86b094dee8c34cf0da53de3ed09ccbc3`

Selected index: `7` of `9` zero-indexed.

Selected S1 target:

`public_context.products.C.gross_margin_pct = 35`

This target was selected before any scientific S0/S1/S2 subject output exists.

## 9. What this audit changes

The audit changes **prospective implementation readiness**, not historical evidence.

It means:

- R5-MID A/B remains frozen and valid;
- R6 factual report v2 remains valid;
- S0/S1/S2 theory remains valid;
- v0.1 top-level-state-key selector is insufficient for this exact parent;
- a v0.2 atomic target annotation interface is required before scientific specificity execution;
- the exact S1 pool and selected target can now be frozen prospectively.

## 10. Scientific status

The current evidence has therefore passed the **conceptual qualification** for a specificity experiment but not yet the **runtime-operator qualification** for a real subject run.

Next engineering step:

`exact-source atomic target overlay -> deterministic offline preflight -> freeze exact S0/S1/S2 plan -> paid-call gate remains closed`

## 11. Authorization boundary

This audit authorizes:

- offline source parsing;
- candidate-pool freezing;
- operator implementation;
- deterministic tests;
- readiness validation.

It does **not** authorize:

- any new provider subject call;
- any paid evaluator call;
- semantic CPR adjudication;
- mutation of historical frozen evidence.
