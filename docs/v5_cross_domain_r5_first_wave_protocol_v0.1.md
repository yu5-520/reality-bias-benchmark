# V5 Cross-Domain R5 First-Wave Protocol v0.1

Date: 2026-09-19  
Status: FROZEN FIRST-WAVE DESIGN / ACTIVE EXECUTION REQUIRES SEPARATE AUTHORIZATION

## 1. Purpose

This stage tests source-level epistemic-status dependence for a small, pre-frozen subset of the held-out cross-domain cohort.

It starts only after:

`90 natural trajectories -> deterministic triage -> localized semantic audit pass 1 -> R5 scientific eligibility`.

It does not redefine R5, R6, R7 or CPR.

## 2. Sampling unit and first-wave selection

Pass 1 produced 29 cases compatible with the already-frozen `fact -> unconfirmed` operator.

The first R5 wave uses exactly six source-bound cases: one from each original natural wave.

Within each wave, selection is deterministic before any R5 outcome exists:

`min(source_event_index, source_run_id, source_case_hash)`.

The resulting six case hashes are frozen in `configs/v5_cross_domain_r5_first_wave_v0.1.json`.

This gives:

- finance: 2 cases;
- supply_chain: 2 cases;
- software_engineering: 2 cases.

The first wave is therefore not chosen by apparent severity, interestingness, expected effect or R5 outcome.

## 3. Frozen parent

For each case, the branch parent is the exact natural snapshot:

`after_turn:<source_turn>`.

This preserves all realized actions from the source Agent turn, including messages, invocations, state writes and queue ordering.

Required parent checks:

- exact state hash matches the frozen plan;
- target metadata status is `fact`;
- parent is non-terminal;
- queue is non-empty;
- first resumed Agent matches the frozen expected actor.

The natural trace is never rewritten.

## 4. Atomic R5 operator

Control and intervention both resume from the same frozen parent.

Control:

`unchanged frozen parent -> natural continuation`.

Intervention:

`same frozen parent -> first resumed Agent runtime view only: target metadata fact -> unconfirmed -> natural continuation`.

The operator:

- changes no target value;
- changes no persistent Arena state;
- is visible for exactly one direct Agent exposure;
- is never re-injected;
- supplies no opposite fact;
- supplies no replacement conclusion;
- supplies no desired terminal answer.

Natural downstream reconstruction is allowed and measured.

## 5. Geometry

Each of the six cases receives two matched replicate pairs.

- replicate 1: control first, intervention second;
- replicate 2: intervention first, control second.

Total:

`6 cases x 2 pairs x 2 conditions = 24 branches`.

This first wave is a bounded mechanism probe, not a population prevalence estimate.

## 6. Evidence order

Execution order is:

`prepare frozen branch plan -> preflight -> provider branches -> raw evidence freeze -> structural local-response derivation -> semantic review later`.

Raw evidence must be frozen before any derived comparison is interpreted.

The structural derivation may compare:

- first resumed Agent;
- prompt-visible target status;
- first raw response;
- first parsed action envelope;
- first decision summary;
- Agent path;
- turn count;
- termination reason;
- final-state hash.

These are structural/process observations, not semantic inertia conclusions.

## 7. Claim boundary

R5 first-wave evidence may establish local response to a one-shot authority withdrawal.

It does not by itself establish:

- System Inertia;
- CPR;
- causal semantic mechanism beyond the frozen perturbation contrast;
- repairability;
- R7 success;
- cross-model generality;
- population occurrence rate.

R6 remains responsible for downstream persistence/inertia interpretation.

## 8. Authorization and budgets

Exact active authorization phrase:

`CALL_REAL_V5_CROSS_DOMAIN_R5_FIRST_WAVE_API`.

Frozen hard ceilings:

- 64 calls per branch;
- USD 0.25 per branch;
- USD 6.00 global first-wave ceiling.

No paid evaluator, R7 repair or R8 CPR adjudication is authorized.
