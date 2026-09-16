# CN-R-051 — Trajectory Measurement v3 Branch Integration

Date: 2026-09-16  
Status: IMPLEMENTED OFFLINE / ZERO PROVIDER CALLS

## 1. Change

The R5/R6 frozen-parent branch path is now connected to a deterministic trajectory-measurement layer rather than stopping at raw branch traces.

Implemented:

- `arena/trajectory_measurement_v3.py`
- `schemas/branch_trajectory_measurement_v3.schema.json`
- `schemas/branch_trajectory_comparison_v3.schema.json`
- Measurement-v3 outputs inside `arena/branch_recovery_preflight.py`
- corresponding unit and CI assertions.

## 2. Branch boundary strengthening

Branch manifest v0.2 now binds not only parent/start state hashes but also:

- parent turn;
- branch-start turn;
- parent event count;
- branch-start event count.

This permits deterministic slicing of the continuation without counting the frozen parent history again as an intervention outcome.

The intended structure is:

`frozen parent history [0:n] → optional ΔX → branch start at n → continuation [n:...]`

## 3. Measurement v3 current scope

For each branch continuation the deterministic adapter records:

- continuation turn/call/event counts;
- realized event counts;
- action-type counts;
- actors participating after the branch start;
- realized Authority-class event counts;
- realized operational event counts;
- Measurement-v2 structural candidate counts/types restricted to the continuation;
- final-state/final-answer hashes;
- usage summary.

The branch comparison requires the same frozen parent trace and parent state, then records structural deltas between control and intervention branches.

## 4. Semantic boundary

The adapter intentionally leaves the following as `NOT_ADJUDICATED`:

- C;
- P;
- R;
- semantic adoption;
- Authority Penetration;
- decision effect;
- recovery;
- general causal effect.

A realized Authority-class event is not automatically Authority Penetration. A structural candidate is not automatically a semantic Reality Bias event. A deterministic branch difference is not automatically a general causal effect.

## 5. Offline validation fixture

The R5/R6 engineering preflight now produces:

- control branch measurement;
- intervention branch measurement;
- branch structural comparison;
- recovery record;
- hashes binding all of the above to the same frozen parent.

The fixture intentionally causes a one-field state-status change so that downstream visibility and final-state divergence can be mechanically verified.

This is instrumentation validation only, not real-model scientific evidence.

## 6. Historical compatibility

- Historical branch-manifest v0.1 records remain preserved.
- Historical subject traces are not modified.
- Measurement v2 remains the frozen Batch001 structural contract.
- Measurement v3 does not retroactively claim that old runs were preregistered branch/hazard experiments.
- Missing replay state remains missing.

## 7. Forward implication

The experiment stack now has an offline executable chain:

`State Anchor → Parent Snapshot → ΔX → Branch Start → Continuation → Deterministic Measurement v3 → Structural Comparison → Recovery Record`

The next scientific step is not to promote these fixture differences into claims. It is to freeze a real-model R5/R6 protocol that specifies anchor rule, intervention family, repeats, Jump criterion, primary metrics, provider/model, and spending boundary before any paid call.

## 8. API boundary

This update performed no paid subject call and no paid Reviewer call.

Generic repository execution approval remains insufficient to dispatch a paid experiment.
