# R2–R4 Format Verify 005 — Censor-aware Re-derivation Audit

## Status

**PASS — SAME FROZEN SUBJECT EVIDENCE, NEW DERIVED MEASUREMENT VIEW, NO PROVIDER CALLS.**

Source subject workflow: `34962065864`  
Source subject artifact: `r234-structural-smoke-34962065864`  
Original evidence batch hash: `74812ef2b92417f47d7679c933a44784379ef3c22c76502a6f3144f1823b1eca`

Offline re-derivation workflow: `34963018122`  
Re-derived artifact: `r234-format005-censor-aware-rederived-34963018122`  
Re-derived artifact digest: `sha256:6ba5ddba515a1173e1f859ef66eafbab7196cbf9955a7724181a43fe2b46b702`

## Audit result

The current censor-aware evidence exporter reprocessed the already frozen Format Verify 005 manifest, raw trace and journals without calling any subject or evaluator API.

The audit asserted and passed all of the following:

- the re-derived `evidence_batch_hash` is exactly the original frozen hash;
- the derived measurement layer is versioned as `R234-OBJECTIVE-STATS-v0.3.1-CENSOR-AWARE`;
- the run remains `BUDGET_CENSORED` with 32 observed turns under a 32-turn limit;
- negative-finding scope is `OBSERVED_PREFIX_ONLY`;
- pending work remains visible at the boundary;
- every re-derived review packet remains bound to the same evidence batch hash and carries the censor-aware observation context.

This verifies the intended identity rule:

> **The evidence batch hash identifies the frozen subject behavior. A later deterministic measurement/export version may change without creating a new behavioral evidence identity.**

Derived files and their own integrity hashes are versioned separately, so analysis evolution remains auditable without rewriting the source experiment.

## Scientific boundary

This audit adds no new subject behavior and no semantic R2/R3/R4 judgment. It validates evidence identity and censor-aware measurement plumbing only.

No paid expansion is authorized by this result.
