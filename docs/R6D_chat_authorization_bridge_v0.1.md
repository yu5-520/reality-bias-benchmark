# R6-D Chat Authorization Bridge v0.1

## Purpose

Restore the operating pattern `explicit human authorization in chat -> automatic scientific workflow dispatch` without changing the frozen R6-D scientific subject workflow or experimental design.

## Scientific boundary

This bridge is control-plane infrastructure only. It does not modify:

- the frozen R6-D design hash;
- S0/S1/S2 target definitions or intervention operator;
- branch ordering or replication geometry;
- model/provider configuration;
- budget ceilings;
- raw-evidence freeze-before-derivation ordering;
- evaluator policy;
- CPR adjudication status.

The existing `r6d-specificity-subject-real.yml` remains the scientific execution workflow and retains its exact authorization phrase and design-hash gates.

## Fail-closed authorization record

A dispatch request must be a newly opened issue authored by `yu5-520` with exact title `R6D SCIENTIFIC AUTHORIZATION` and exactly five key/value fields:

- `authorization_phrase`
- `confirm_design_hash`
- `expected_main_sha`
- `authorization_id`
- `control_plane=CHAT_AUTHORIZATION_BRIDGE_v0.1`

The authorized SHA must equal the default-branch SHA observed by the issue event. A deterministic authorization tag is then created at that SHA; reusing an authorization id therefore fails closed.

## Dispatch semantics

The bridge uses GitHub Actions `actions: write` permission to invoke the existing `workflow_dispatch` endpoint on the pinned authorization tag. The scientific workflow re-validates its own authorization phrase, frozen design hash, v4.5.1 methodological gate, exact plan, parent artifact, preflight, budget, and raw-freeze order.

The bridge is not scientific evidence. The scientific evidence begins only inside the dispatched subject workflow.