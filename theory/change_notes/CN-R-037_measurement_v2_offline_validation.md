# CN-R-037 — Measurement v2 Offline Validation Gate

Date: 2026-09-15  
Status: **OFFLINE ENGINEERING VALIDATED; SEMANTIC RE-REVIEW NOT YET AUTHORIZED**

## Decision

Measurement Architecture v2 has passed its first frozen Batch001 offline implementation gate.

This Change Note does not change subject behavior, historical Reviewer A/B v1 annotations, or the frozen evidence batch. It records that the new structural-index / semantic-review separation is executable and deterministic on the existing evidence.

## Validated outputs

### Measurement v2 structural layer

Workflow `34987638198` completed successfully.

- evidence batch: `94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`
- output hash: `9a2b966849f8b18fa553b2b425ff9723fe0d66c2b58e88260e29ad43e6f767f6`
- R2 structural targets: 70
- realized targets: 68
- attempt-only targets: 2
- R3 lineage windows: 70
- R4 neutral structural feedback windows: 4
- R2 Reviewer-v2 packets: 70
- paid API calls: 0

The deterministic layer emits candidates and structural facts only. It does not assign semantic C/P/R truth.

### R3/R4 Reviewer-v2 range packets

Workflow `34988452980` completed successfully.

- packet output hash: `e8b7d3cc7d09a2bc629ed95ac130e8d9aac737bb904229171b61f21979fff5f6`
- R3 semantic-range packets: 70
- R4 dynamics packets: 4
- prior Reviewer A/B outputs included: no
- expected C→I / P→V / R→T mapping included: no
- paid API calls: 0

These packets materialize Agent-visible inputs and Agent outputs within machine-defined structural ranges so that a later semantic reviewer can judge effective adoption, decision impact, task-scope/focus penetration, correction, regeneration, laundering and normalization.

## Black-hole boundary

One structural R4 review trigger appears in `arena-ecommerce-0003`, round 2 because tokens/call and tokens/event rose materially relative to round 1.

This is explicitly **not** a black-hole finding. The machine cannot determine whether original-goal progress or verified-evidence gain became insufficient. Therefore the semantic field remains `NOT_ADJUDICATED` and the window is only prioritized for later review.

## Historical v1 alignment

Measurement v2 preserves all 70 historical Authority-bearing targets and all 54 historical A/B disagreement events. This is a coverage diagnostic, not a claim that v1 labels are ground truth.

## Current gate

The next required freeze is the independent **Semantic Review Protocol v2**. It must define R2, R3 and R4 boundary outputs, uncertainty handling, ordering/blinding, retry behavior and a cost ceiling before any paid Reviewer-v2 call.

No new subject collection, K=2 run, or paid semantic review is authorized by this Change Note.
