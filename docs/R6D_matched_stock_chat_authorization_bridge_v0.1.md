# R6-D Matched-Stock Chat Authorization Bridge v0.1

## Purpose

Restore the operating pattern `explicit human authorization in chat -> automatic matched-stock scientific workflow dispatch` for the second R6-D robustness batch without changing the frozen S2/S3/S4 scientific workflow or design.

## Scientific boundary

This bridge is control-plane infrastructure only. It does not modify the frozen matched-stock design hash, S2/S3/S4 target definitions, intervention operator, cyclic branch order, provider/model configuration, budgets, raw-evidence freeze-before-derivation ordering, evaluator policy, or CPR status.

## Fail-closed authorization record

A dispatch request must be a newly opened issue authored by `yu5-520` with exact title `R6D MATCHED STOCK SCIENTIFIC AUTHORIZATION` and exactly five key/value fields:

- `authorization_phrase=CALL_REAL_R6D_MATCHED_STOCK_API`
- `confirm_design_hash=5064e255da26949a152a2300fe659ebdddddc9b44f1a97a4b31d7796005a959d`
- `expected_main_sha`
- `authorization_id`
- `control_plane=CHAT_AUTHORIZATION_BRIDGE_MATCHED_STOCK_v0.1`

The authorized SHA must equal the default-branch SHA observed by the issue event. A deterministic authorization tag is created at that SHA, making authorization IDs one-shot and replay-resistant.

## Dispatch semantics

The bridge invokes the existing `r6d-matched-stock-subject-real.yml` workflow on the pinned tag. The scientific workflow independently re-validates the exact authorization phrase, frozen design hash, runtime plan, provider-free preflight, budget ceilings, and raw-evidence freeze-before-derivation order.

The bridge is not scientific evidence. Scientific evidence begins only inside the dispatched matched-stock subject workflow.
