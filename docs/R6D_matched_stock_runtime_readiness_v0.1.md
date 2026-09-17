# R6-D Matched-Stock Runtime Readiness v0.1

Date: 2026-09-17  
Status: **ENGINEERING RUNTIME READY CANDIDATE / REAL SCIENTIFIC RUN NOT AUTHORIZED**

This layer binds the already frozen matched-stock robustness design to an executable runtime path without changing the scientific design core.

Frozen design hash:

`5064e255da26949a152a2300fe659ebdddddc9b44f1a97a4b31d7796005a959d`

Runtime gate hash:

`97650361491e310490e18c9598540a5df9c6e3d3ca9ba62a1e6ae7f8cd8ffa90`

## Runtime chain

`frozen after_turn:8 parent -> runtime plan builder -> S2/S3/S4 cyclic 3x3 plan -> deterministic offline smoke -> formal runner preflight -> manual-only real workflow -> raw evidence freeze -> raw artifact upload -> later derivation/review`

The three runtime conditions remain exactly:

- `S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL`
- `S3_MATCHED_ORDINARY_STOCK_B_DOWNGRADE`
- `S4_MATCHED_ORDINARY_STOCK_C_DOWNGRADE`

Each condition appears three times in the frozen cyclic order. Every branch starts from the same frozen `after_turn:8` parent, exposes exactly one experiment-origin `fact -> unconfirmed` annotation at T9, performs zero experiment-origin reinjection, does not mutate the original target value, and does not create experiment-origin persistent state.

## Reuse boundary

The matched-stock real runner deliberately reuses the first real R6-D runner's already-tested budget, credential, execution-binding, journal and exposure-integrity utilities. The new code only adds matched-stock plan/envelope routing and matched-stock evidence namespaces. This avoids maintaining two divergent execution-control implementations.

## Offline smoke boundary

The deterministic smoke provider exists only to validate plumbing. It checks:

- one target-scoped annotation is visible at T9;
- the annotation is absent at T10;
- the target locator matches the frozen condition envelope;
- each condition has exactly three direct experiment-origin exposures across the batch;
- post-consumption turns exist for all three conditions;
- the frozen parent snapshot remains unchanged.

Smoke output is labeled `ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE` and must never be interpreted as R6 specificity evidence.

## Real workflow boundary

The real workflow is manual `workflow_dispatch` only. It requires both:

- exact authorization phrase `CALL_REAL_R6D_MATCHED_STOCK_API`;
- exact frozen design hash confirmation.

The workflow runs frozen-design validation and a provider-free runner preflight before the provider credential is exposed to the real execution step. The readiness workflow itself contains no provider credential and cannot invoke `--execute-real-api`.

## Raw evidence rule

If a real batch is later explicitly authorized, raw traces, errors, journals, plan bindings and execution hashes are preserved before any derived R6 analysis. Incomplete branches remain incomplete evidence; they are not silently replaced or converted into zero effects. Automatic retry/replacement remains unauthorized.

## Scientific interpretation boundary

Runtime readiness is engineering evidence only. It does not establish:

- `S2-S3` or `S2-S4` intervention-related specificity;
- Escape-derived specificity;
- System Inertia beyond the already documented evidence boundary;
- CPR;
- R7 recovery efficacy.

CPR remains `NOT_ADJUDICATED`. Paid evaluator execution remains disabled.
