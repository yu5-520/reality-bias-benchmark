# Cross-Domain First-Round Status v0.2 — 2026-09-19

Status: **OFFLINE IMPLEMENTED / HELD-OUT SIX-WAVE EXECUTION PREPARED / REAL SUBJECT NOT AUTHORIZED**

## Prospective replication cohort

Historical method-development reference:

- ecommerce — excluded from the new prospective replication sample.

Held-out replication domains:

- finance;
- supply_chain;
- software_engineering.

## Frozen first-round geometry

- 30 natural trajectories per held-out domain;
- 90 new natural trajectories total;
- two preregistered waves per domain;
- 15 trajectories per wave;
- six domain-pure waves total.

Wave assignment:

1. finance-w1 — trials 1-15;
2. finance-w2 — trials 16-30;
3. supply_chain-w1 — trials 1-15;
4. supply_chain-w2 — trials 16-30;
5. software_engineering-w1 — trials 1-15;
6. software_engineering-w2 — trials 16-30.

## Real execution topology

One explicit `workflow_dispatch` event:

`prepare common 90-row manifest -> launch six matrix jobs concurrently -> freeze each wave -> derive each wave -> build each candidate ledger -> aggregate six evidence batches into one first-round registry`

All six wave jobs bind:

- the same execution SHA;
- the same plan hash;
- the same authorization event ID;
- the same model/provider configuration;
- the same Arena/runtime interface;
- the same reporting/evidence contracts.

Each wave remains runtime-independent and domain-pure.

## Implemented interfaces

- `configs/v5_cross_domain_first_round_v0.2.json`
- `configs/v5_cross_domain_subject_gate_v0.2.json`
- `schemas/v5_cross_domain_first_round_plan_v0.2.schema.json`
- `schemas/v5_cross_domain_subject_manifest_v0.2.schema.json`
- `schemas/v5_cross_domain_paid_authorization_v0.2.schema.json`
- `schemas/v5_cross_domain_evidence_batch_v0.2.schema.json`
- `schemas/v5_cross_domain_first_round_registry_v0.2.schema.json`
- `arena/build_v5_cross_domain_manifest.py`
- `arena/v5_cross_domain_preflight.py`
- `arena/run_v5_cross_domain_real.py`
- `arena/freeze_v5_cross_domain_evidence.py`
- `arena/build_v5_cross_domain_case_ledger.py`
- `arena/build_v5_cross_domain_first_round_registry.py`
- `.github/workflows/v5-cross-domain-first-round-offline-validate.yml`
- `.github/workflows/v5-cross-domain-first-round-subject-real.yml`

## Scientific boundary

The real natural-subject workflow still does only:

`Natural -> Raw Freeze -> Structural Derivation -> Candidate Ledger`

It does not automatically execute:

- localized semantic adjudication;
- R5 probe;
- R6 controlled continuation;
- R7 repair;
- R8 CPR adjudication;
- paid evaluator review.

R5/R6/R7 remain conditional case-level extensions after append-only qualification.

## Authorization boundary

This repository update authorizes no provider call.

Future six-wave natural execution requires:

- exact execution SHA;
- exact phrase `CALL_REAL_V5_CROSS_DOMAIN_FIRST_ROUND_API`;
- one shared authorization event ID created by the workflow run;
- positive per-run call ceiling;
- positive per-run spending ceiling;
- per-wave ceiling covering 15 symmetric per-run ceilings;
- first-round ceiling covering all six wave ceilings.

R5 and R7 require separate future case-specific authorization.
