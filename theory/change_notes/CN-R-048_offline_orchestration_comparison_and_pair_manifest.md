# CN-R-048 — Offline Orchestration Comparison and Paired Manifest

Date: 2026-09-16  
Status: IMPLEMENTED OFFLINE / ZERO PROVIDER CALLS

## 1. Change

The R7 infrastructure now produces a complete offline comparison artifact for:

- `EMERGENT_FREE_ROUTING`
- `STRUCTURED_SYSTEM_OWNED_ROUTING`

and can prepare paired candidate manifests for a future real-model R7 batch.

No paid subject or Reviewer call is authorized or executed by this change.

## 2. Offline comparison adapter

Implemented files:

- `arena/orchestration_compare.py`
- `arena/orchestration_preflight.py`
- `arena/tests/test_orchestration_compare.py`
- `schemas/orchestration_comparison_v0.1.schema.json`

The adapter binds both conditions to the same task hash and Agent-registry hash and records:

- mechanical topology metrics;
- participation metrics;
- raw subject proposal action counts;
- policy-passed actions;
- policy-blocked actions;
- realized Arena actions;
- proposal/blocked/realized invocation counts;
- trace hashes;
- mechanical deltas, explicitly marked engineering-only.

The offline scripted fixtures intentionally differ where necessary to exercise the two runtime mechanisms. Therefore the resulting preflight is a schema/control validation artifact and **not** a scientific A/B estimate.

## 3. Proposal versus realization

The structured condition now demonstrates an evidence path in which:

`invoke_agent proposal exists`

while:

`policy blocks invocation → realized invocation count = 0`

The original proposal remains in evidence. This validates the measurement distinction between generation/attempt and operational realization without claiming any real-model effect size.

## 4. Paired future-run manifest

Implemented files:

- `arena/build_orchestration_manifest.py`
- `arena/tests/test_orchestration_manifest.py`
- `docs/R7_real_run_freeze_template_v0.1.md`

Each candidate trial produces exactly two rows sharing:

- `pair_id`;
- logical seed identity;
- domain/task/Agent-pool bindings;
- Arena config binding;
- model-config binding.

The two rows differ in condition identity and routing owner:

- free: `AGENT_WITHIN_ARENA_POLICY`
- structured: `EXPERIMENT_SYSTEM`

The structured policy hash is bound into both rows as comparison metadata, but only the structured row activates it.

## 5. Paid-run boundary

The prepared rows carry:

`scientific_status = CANDIDATE_UNTIL_EXPLICIT_REAL_RUN_FREEZE_AND_API_AUTHORIZATION`

A real R7 batch still requires unresolved fields to be frozen separately:

- provider;
- model/config;
- paired repeat count;
- concurrency/call budget;
- explicit spending ceiling and currency;
- run-start commit SHA;
- final manifest hash;
- primary metric set/version.

Generic repository-update instructions do not authorize a paid run.

## 6. CI integration

The standard offline Arena validation workflow now additionally:

1. runs all regression/unit tests;
2. emits the Free-vs-Structured scripted comparison bundle;
3. verifies its four output files;
4. builds a two-pair R7 candidate manifest;
5. uploads all offline outputs with the existing preflight artifact.

This keeps R7 infrastructure under the same regression gate as the historical Free-Agent Arena.

## 7. Scientific interpretation rule

Mechanical preflight differences are not evidence that one orchestration architecture is safer, more correct, or lower-bias.

The scientific question remains whether, under a separately frozen real-model protocol, orchestration structure changes preregistered Jump, propagation, Authority Penetration, inertia, feedback, or recovery quantities.
