# R5/R6 v4 Research Binding v0.1

Date: 2026-09-16  
Status: FORWARD FROZEN OFFLINE INTERFACE / NOT PAID AUTHORIZATION

## Purpose

A Phase-B branch plan is not sufficient by itself to identify the measurement system that will later interpret its evidence.

Forward v4 Phase-B preparation therefore creates an additive:

`v4_research_binding.json`

without modifying historical `RB-R5R6-BRANCH-EXECUTION-PLAN-v0.1` records.

The binding answers:

> Which exact research interfaces, code revision and experimental variable were frozen for this future subject batch?

## Bound identities

The v0.1 binding freezes:

- branch plan hash and branch-plan file SHA-256;
- Phase-B execution code SHA;
- experimental variable `EPISTEMIC_STATUS_DOWNGRADE`;
- source trace/evidence/selection identities inherited from the branch plan;
- experimental-variable registry;
- measurement-boundary registry;
- BehaviorEvent schema;
- SystemTrajectory Measurement v4 schema;
- Arena v0.3 → BehaviorEvent source adapter implementation;
- Structural Jump Detector v0.1;
- Operational Boundary Set v0.1;
- Source Lineage Rules v0.1;
- System Behavior Measurement v4 contract.

Each research interface is bound by repository path, declared identity and exact SHA-256 file hash.

## Execution gate

`arena.run_branch_real` now requires a valid `v4_research_binding.json` in the prepared plan directory before credential checks or provider construction.

The binding must match:

- the exact branch plan;
- the exact current repository interface hashes;
- the exact Phase-B code SHA frozen into the plan.

Any drift fails closed before a provider call.

## Evidence binding

A future Phase-B real subject run records the v4 binding hash into:

- the paid-subject authorization record;
- copied run-level binding artifact;
- run-start/run-finish journals;
- each subject trace;
- runner errors;
- batch run summary.

This allows later Measurement v4 / lineage / review outputs to identify the exact research instrument stack used by the subject batch.

## Authorization separation

A valid research binding is **not** paid API authorization.

The binding itself freezes:

- `authorization_status = NOT_AUTHORIZED`;
- `paid_api_authorized = false`;
- `automatic_paid_evaluator = false`;
- `semantic_status = NOT_ADJUDICATED`.

Real Phase-B calls still independently require:

`CALL_REAL_R5R6_BRANCH_API`

plus provider/model match, positive call cap, positive spending ceiling, matching currency and the existing runtime budget guard.

## Scientific boundary

Binding proves version identity and fail-closed reproducibility plumbing only.

It does not establish:

- that the structural anchor is semantic C;
- that the intervention changes Reality Bias;
- semantic adoption;
- Authority Penetration;
- direct Tension or Escape measurement;
- a causal effect before real paired subject evidence exists.

## Offline validation

`arena.v4_binding_preflight` builds a deterministic branch fixture, freezes the binding and verifies that all interfaces are present while paid authorization and semantic labels remain off.

The standard offline CI includes this preflight.