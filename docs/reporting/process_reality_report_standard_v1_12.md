# Process Reality Report Standard v1.12

Date: 2026-09-26  
Status: **FORWARD ACTIVE / INDEPENDENT AUDIT + MONITOR BENCHMARK GOVERNANCE**  
Predecessor: `RB-PROCESS-REALITY-REPORT-STANDARD-v1.11`

Historical reports remain immutable.

This version retains the dual General Chapter structure and adds mandatory separation between:

1. natural execution;
2. online structural monitoring;
3. post-hoc full semantic audit;
4. monitor-performance evaluation;
5. engineering repair.

## 1. Canonical forward sequence

For G2-G5 the reporting sequence is:

`84 prospective natural A`
-> `independent full semantic audit`
-> `monitor evaluation`
-> `engineering eligibility`
-> `G2-G5 engineering batches`.

Per-group A->B reporting is historical and no longer canonical.

## 2. Governing documents

Canonical plan:

`docs/R_Plan_v7.45.md`

Independent semantic audit protocol:

`configs/stage2_semantic_audit_reference_protocol_v1.json`

Monitor evaluation protocol:

`configs/stage2_monitor_evaluation_protocol_v1.json`

Sequencing/evaluation policy:

`configs/stage2_g2_g5_execution_and_evaluation_policy_v2.json`

Dual General Chapter addendum:

`docs/reports/2026-09-26/StageII_Dual_General_Chapter_Independent_Audit_and_Monitor_Evaluation_Addendum_v1.md`

## 3. Natural-run reporting

Every G2-G5 natural-run report must show:

- group/cell ID;
- exact runner/framework/protocol/model versions;
- horizon version;
- first-attempt status;
- termination class;
- raw evidence seal/hash;
- monitor-runtime-bundle seal/hash;
- checkpoint-ledger seal/hash;
- zero repair actions;
- no semantic-audit feedback into execution.

Natural-run reports must not contain post-hoc monitor-performance claims.

## 4. Audit input boundary

The full semantic audit may read only the audit raw bundle.

It may not read:

- monitor warnings;
- monitor candidate labels;
- monitor confidence/severity;
- monitor-generated CPR labels;
- repair eligibility;
- repair package status.

The report must record the hash/list of audit inputs and affirm the monitor-runtime bundle was not read before reference-set sealing.

## 5. Semantic reference reporting

Every reference record should preserve, where observable:

- complete route;
- source;
- carrier;
- semantic before/after/delta;
- producer;
- reader/adopter;
- relation type;
- decision/action link;
- consequence;
- first observable sequence;
- first consequence sequence;
- C/P/R dimensions;
- cross-penetration path;
- closure state;
- evidence-surface availability;
- negative-case status;
- NOT_ESTABLISHED fields;
- source evidence refs.

Positive-only semantic reference sets are prohibited.

## 6. Monitor-performance reporting

Primary monitor performance uses G2-G5 only.

G1 may be shown separately as development/calibration context, never silently pooled into the primary prospective result.

Every metric must show:

- numerator;
- denominator;
- rate;
- scope/population;
- monitor version;
- matching-rule version.

Zero-denominator metrics are reported as NA.

## 7. Required metric families

### Trajectory level

- target-positive trajectories;
- monitor-hit trajectories;
- trajectory detection rate;
- trajectory miss rate.

### Structure/case level

- audit-confirmed structures;
- matched structures;
- structure recall;
- structure miss rate;
- monitor warnings;
- audit-supported warnings;
- warning precision;
- audit-rejected warning rate;
- unsupported-warning rate.

### Localization level

- source localization accuracy;
- carrier localization accuracy;
- consumer localization accuracy where observable;
- decision-link localization accuracy;
- first-warning to first-consequence lead distance.

### Lineage level

- lineage node coverage;
- lineage edge coverage;
- descendant-carrier coverage.

### Observability level

- end-to-end capture rate over the full audit reference set;
- conditional detector recall over legally observable reference structures;
- unobservable-reference rate.

## 8. Required distinction rules

Reports must distinguish:

- detector miss vs unobservable evidence surface;
- unsupported warning vs audit-rejected warning;
- trajectory-level hit vs correct source localization;
- source localization vs lineage localization;
- structural-signature detection vs post-hoc CPR interpretation;
- terminal task outcome vs process closure.

## 9. Required subgroup views

Where denominator permits, report:

- pooled G2-G5;
- each group separately;
- each X separately;
- each task family separately;
- each structural-signature family separately.

Small denominators remain visible.

## 10. Performance claim language

Primary wording:

> **within-study prospective monitoring performance**

Every monitor-performance table/report must state that the metrics apply only to:

- the frozen G2-G5 groups;
- the seven frozen system/layer conditions;
- T1-T3;
- the frozen model/provider configuration;
- the frozen monitor version;
- legally observable evidence surfaces.

Do not convert these metrics into universal product accuracy, SLA, or all-AI-system miss rates.

## 11. Monitor evaluation cannot backfill repair candidates

The independent semantic audit may identify a monitor miss.

That finding may count against monitor recall.

It may not be used to create a primary repair candidate that did not exist prospectively in the monitor/localization pipeline.

Audit-assisted repairs, if later studied, must be reported as a separate secondary engineering experiment.

## 12. Engineering eligibility reporting

Eligibility opens only after:

- all 84 natural A are sealed;
- semantic reference set is sealed;
- primary monitor-performance evaluation is sealed.

Eligibility reports must bind:

- prospectively frozen monitor candidate/package evidence;
- legal parent/checkpoint evidence;
- preserve set;
- mutation surface;
- native-preservation result;
- eligibility verdict.

## 13. Engineering batch reporting

Engineering B is reported by batch:

- G2;
- G3;
- G4;
- G5.

Each batch report includes:

- eligible population;
- launched B population;
- package IDs;
- parent IDs;
- boundary-watcher results;
- intended delta;
- preserve-set audit;
- post-repair CPR/re-entry/migration;
- process closure;
- terminal outcome.

A later engineering version change must be explicit and may not rewrite prior batch evidence.

## 14. Authorization boundary

This reporting standard authorizes no subject/provider calls, active repair, paid evaluator, or rerun.
