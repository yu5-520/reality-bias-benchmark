# CN-R-047 — Structured Routing and Branch/Recovery Instrumentation

Date: 2026-09-16  
Status: IMPLEMENTED OFFLINE / NO REAL PROVIDER EVIDENCE

## 1. Purpose

This note records the first offline implementation of the v3.2 experimental-control plan.

The repository now contains two additional mechanism-testing capabilities:

1. a minimal structured/system-owned-routing condition for R7;
2. frozen anchor-selection, branch and recovery evidence interfaces for R5/R6.

Neither capability changes historical subject evidence or authorizes paid API execution.

## 2. Structured-routing implementation

Implemented files:

- `arena/structured_routing.py`
- `arena/config/structured_ecommerce_v0.1.json`
- `arena/tests/test_structured_routing.py`
- `docs/R7_orchestration_protocol_v0.1.md`

The v0.1 structured condition keeps the E-commerce domain registry and task substrate but externally owns stage order and executable routing.

Current stage sequence:

`ads → inventory → finance → ops_lead`

Dynamic invocation proposals are not deleted from evidence. The upstream subject envelope is retained under the structured-routing provider record while the realized Arena action set contains only policy-admitted actions.

This creates an explicit experimental separation:

`subject proposal → deterministic routing/action gate → realized system effect`

The condition is not claimed to be universally safer than Free Routing.

## 3. Branch/recovery evidence implementation

Implemented files:

- `arena/branch_protocol.py`
- `arena/tests/test_branch_protocol.py`
- `schemas/experimental_branch_manifest_v0.1.schema.json`
- `schemas/anchor_selection_record_v0.1.schema.json`
- `schemas/recovery_record_v0.1.schema.json`
- `docs/R5_R6_branch_intervention_recovery_protocol_v0.1.md`

Confirmatory branch-anchor selection is structural-only and must be frozen before branch outcomes are visible.

The code rejects records that claim reviewer-driven anchor selection or branch-outcome-aware selection for the confirmatory path.

Recovery records keep structural recurrence separate from semantic R regeneration. Semantic regeneration defaults to `NOT_ADJUDICATED`.

## 4. Important limitation

The R7 v0.1 comparison changes a bundle of orchestration properties together: scheduling, stage-goal exposure and executable routing ownership.

Therefore it is a boundary-condition comparison, not a single-bit routing causal estimate.

If later evidence requires narrower attribution, a follow-up design may separate:

- stage goals;
- scheduling;
- context reset/compression;
- routing ownership;
- action/commit gates.

This limitation is preregistered before any real provider run.

## 5. Validation status

The first structured-routing unit-test run exposed a deterministic classification-order mismatch: a blocked dynamic invocation was recorded as generic `ACTION_TYPE_NOT_ALLOWED_IN_STAGE` before the invocation-specific rule fired.

The implementation was corrected at the actual decision breakpoint so `invoke_agent` under system-owned routing is classified as `SYSTEM_OWNS_INVOCATION_GRAPH` before generic stage-action filtering.

Subsequent offline regression passed with the structured-routing tests, branch/recovery record tests, previous Arena tests, v0.3.2 environment checks and structural preflight all green.

This is engineering validation only, not scientific evidence of a Reality Bias effect.

## 6. Historical and API boundaries

- No historical trace was rewritten.
- No historical semantic review was replaced.
- No provider-internal state replay is claimed.
- No paid subject call was made.
- No paid reviewer call was made.
- A future real R5/R6/R7 run still requires a frozen run plan, explicit provider/model, explicit authorization and spending ceiling.
