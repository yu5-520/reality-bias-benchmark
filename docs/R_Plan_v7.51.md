# Stage-II v7.51: Primary 84-Cell Monitor Benchmark Correction and Engineering Eligibility Gate

Date: 2026-09-27  
Status: **FORMAL LAYER C SEALED; 21 SAME-X/T COHORTS SEALED; B↔C AND A↔C SEALED; PRIMARY A↔B BENCHMARK CORRECTED TO 84/84; ENGINEERING ELIGIBILITY IS NEXT.**

Predecessor: `docs/R_Plan_v7.50.md`.

## 1. Correction to v7.50

v7.50 correctly closed the Layer-C and cross-layer semantic block, but it promoted an A↔B monitor evaluation whose population had been aligned to the 80 Layer-C-eligible cells.

That 80-cell result is valid only as a:

`LAYER_C_ALIGNED_SUBSET_DIAGNOSTIC`.

It is not the primary prospective monitor benchmark because the frozen monitor-evaluation protocol preregistered:

`G2-G5 = 84 Natural-A trajectories`

as the primary population.

v7.51 corrects the monitor benchmark denominator without changing any Natural-A trajectory, Layer-B reference record, Layer-C verdict, monitor candidate, matching rule, or repair state.

## 2. Primary A↔B benchmark population

Primary population:

`84/84 G2-G5 Natural-A trajectories`.

The four Layer-C process-surface exclusions remain Layer-C exclusions only:

- G3-X6-T2;
- G5-X3-T1;
- G5-X4-T2;
- G5-X6-T2.

They remain in A↔B primary accounting.

Monitor-output availability across the 84 cells:

- monitor-candidate file present: 83/84;
- monitor-candidate file absent: 1/84;
- monitor-runtime-bundle manifest present: 80/84;
- monitor-runtime-bundle manifest absent: 4/84.

The one cell without a monitor-candidate file is G5-X3-T1. It remains in the denominator as a zero-warning monitor-output boundary rather than being removed.

## 3. Frozen matching rule

The corrected 84-cell benchmark reuses the exact source-bound matching rule frozen before the earlier evaluation:

`configs/stage2_monitor_source_bound_matching_rule_v1.json`

Matching-rule SHA-256:

`cdd292efea6e459de4941916c0921ff2c9865359aff4abd8ae2fccbd9f8048a8`.

No threshold, compatibility family, object-matching rule, temporal rule, or metric definition was tuned after observing the four additional cells.

Layer C is not read or used to define A↔B matches.

## 4. Corrected primary monitor result

### Trajectory level

- reference-positive trajectories: 59;
- monitor-hit trajectories: 36;
- detection: 36/59 = 0.6101694915;
- miss: 23/59 = 0.3898305085.

### Structure level

- reference structures: 97;
- broad matches: 45;
- strict matches: 16;
- broad recall: 45/97 = 0.4639175258;
- strict recall: 16/97 = 0.1649484536.

### Observability-aware level

- observable reference structures: 81;
- conditionally detected observable structures: 36;
- conditional detector recall: 36/81 = 0.4444444444;
- unobservable reference structures: 16;
- unobservable-reference rate: 16/97 = 0.1649484536.

### Warning level

Unique frozen warning IDs across the primary 84-cell population:

- monitor warnings: 955;
- supported warnings: 36;
- audit-rejected warnings: 18;
- unsupported warnings: 901.

Rates:

- warning precision: 36/955 = 0.0376963351;
- rejected-warning rate: 18/955 = 0.0188481675;
- unsupported-warning rate: 901/955 = 0.9434554974.

The structure and trajectory numerators remain unchanged from the 80-cell aligned subset because the four Layer-C boundary cells contain no positive Layer-B reference structures. The warning denominator changes because three of those cells contain prospectively frozen monitor candidates.

## 5. Relationship to the 80-cell result

The prior files under:

`stage2/replication_v2/gpt56sol_full_context_semantic_audit_v1/layer_a_b_monitor_evaluation_v1`

remain immutable.

Their formal role is now:

`LAYER_C_ALIGNED_SUBSET_DIAGNOSTIC`.

They may be used for direct A↔B↔C aligned comparisons over the common 80-cell surface.

They must not be reported as the primary prospective monitor-performance denominator.

The primary benchmark is:

`stage2/replication_v2/primary_monitor_benchmark_84_v1`.

## 6. Formal evidence bindings

Primary benchmark seal:

`stage2/replication_v2/primary_monitor_benchmark_84_v1/benchmark_seal.json`

Git blob:

`faea989fa6ca24ea2ff42c1ca4803832af529c86`.

Evaluation summary blob:

`b08ffdb8e477ccbf199e0626cea459b60067118f`.

Evaluation records blob:

`3560b1cac6caa30b8f24d023ed0f2d718dfdc81b`.

Monitor-source index blob:

`8591239763fea269a0c634695440c9ff35e15f75`.

80-cell disposition blob:

`2b3cb17a5bbdf4be37c32c7f091ad03a65d89762`.

Deterministic validation workflow:

`36304997356`.

Result:

`PRIMARY_84_BENCHMARK_GATE=PASS`.

## 7. Scientific boundary

The correction used:

- Natural-A reruns: 0;
- new subject/provider calls: 0;
- semantic re-audits: 0;
- paid evaluator calls: 0;
- repair calls: 0;
- Layer-C verdict changes: 0;
- Layer-B record changes: 0;
- monitor-candidate changes: 0.

This is a denominator/governance correction over already-frozen evidence.

## 8. Canonical post-natural state

The completed Stage-II post-natural chain is now:

`84 Natural A`
-> `84-cell monitor-blind Layer B`
-> `80-cell full-context Layer C`
-> `21 same-X/T Layer-C cohorts`
-> `B↔C 80-cell mechanism comparison`
-> `A↔C 80-cell explanatory localization comparison`
-> `A↔B 84-cell primary prospective monitor benchmark`.

The three comparison layers keep different populations where required by their scientific object. They must not be forced into one denominator.

## 9. Next gate

The next scientific object is the complete:

`G2-G5 84-cell engineering eligibility ledger`.

Every Natural-A cell must receive an explicit eligibility state using only the prospectively frozen monitor/localization/checkpoint/package pipeline.

Allowed top-level outcomes include:

- ELIGIBLE_FOR_ONE_B;
- NO_PROSPECTIVE_PACKAGE;
- LINEAGE_GAP_BLOCKED;
- PARENT_RECONSTRUCTION_BLOCKED;
- NATIVE_CAPABILITY_BLOCKED;
- SAFETY_OR_PROTOCOL_BLOCKED;
- OBSERVABILITY_ONLY_NON_INTERVENABLE.

The semantic audit may validate or explain the frozen ledger afterward. It may not create a primary repair package that the prospective monitor did not produce.

After the 84-cell ledger is sealed:

`G2 B -> freeze/audit -> G3 B -> freeze/audit -> G4 B -> freeze/audit -> G5 B -> freeze/audit -> final cross-group R7 synthesis`.

No Natural-A, Layer-B, Layer-C, R7-G1, or primary 84-cell monitor benchmark rerun is required.
