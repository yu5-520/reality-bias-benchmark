# Process Reality v5 Status — 2026-09-18

Status: **METHOD LAYER IMPLEMENTED ON UPDATE BRANCH / NO NEW SCIENTIFIC SUBJECT RUN**

## Completed modules

### V5-0 / V5-1 — migration + theory rebase

Implemented:

- legacy v4.5.1 freeze boundary;
- Theory Contract v0.11;
- R Plan v5.0;
- first-paper v5 scope;
- v5 concept mapping;
- mechanism/analysis contracts updated forward-only.

### V5-2 — structural observability

Implemented forward interfaces for:

- Structural Support;
- Stable Shared Information Pool;
- Direct Pool Consumption;
- Structural Exposure;
- detection/trace/intervention-surface separation;
- Semantic Audit v0.2 roles;
- Process Integrity event/lineage v0.3.

Legacy Jump detector remains untouched.

### V5-3 — historical re-derivation

Implemented:

- frozen-evidence re-derivation protocol;
- re-derivation record schema;
- J0 reinterpretation boundary;
- R2-R6 historical re-derivation plan.

No new model/evaluator call has been made.

### V5-4 — experimental-chain simplification

Implemented:

- Whole-Process Run as default forward subject profile;
- R5 Structural Scouting + Driver Probe;
- R6 Structural Support / Trace / Control Surface;
- R7 Localized Recovery;
- optional robustness map.

Historical S0-S4 and R6-A/B/C/D remain preserved but are no longer default mandatory future geometry.

### V5-5 — reporting and validation

Implemented:

- Report Standard v1.5;
- Whole-Process report template v2;
- machine report profile;
- offline v5 validator;
- CI synchronization.

## Not yet performed

- no fresh v5 subject provider run;
- no fresh semantic evaluator run;
- no active R7 repair;
- no CPR adjudication;
- no historical raw-evidence mutation;
- no claim that exact first Structural Support or pool-entry event is established.

## Next scientific step

Historical re-derivation is complete and the first fresh Whole-Process Batch001 design is now prepared and offline-preflighted.

Current Batch001 design:

1. ecommerce natural subject only;
2. three fresh repeats;
3. existing Arena v0.3.2 runtime and prompts unchanged;
4. structural support/pool/exposure indexing after freeze;
5. no driver probe, control-surface intervention, recovery, CPR adjudication or paid evaluator.

The remaining gate before any fresh subject evidence is **separate explicit provider authorization** bound to the final batch/code/config hashes.

The next paid run should collect a reusable full-process dataset rather than recreate the old mandatory specificity stack by default.


## Historical re-derivation execution update

The offline v5 historical re-derivation is now implemented as a deterministic frozen-source projection:

- source binding: `configs/v5_historical_rederivation_source_binding_v0.1.json`
- projection spec: `configs/v5_historical_rederivation_spec_v0.1.json`
- derivation script: `scripts/derive_v5_historical_rederivation.py`
- checked-in bundle: `results/v5_historical_rederivation/rederivation_bundle_v0_1.json`
- result report: `docs/reports/2026-09-18/R2-R6_V5_Historical_Rederivation_Result_v1.md`

The derivation validates exact Git blob identities for its repository sources before emitting the bundle. It creates no subject/evaluator calls and mutates no historical raw evidence.

Current re-derived boundaries:

- J0 semantic origin: CONTRADICTED;
- first Structural Support identity: NOT_ESTABLISHED;
- first Stable Shared Pool entry: NOT_ESTABLISHED;
- J0 as Structural Exposure anchor: SUPPORTED_CANDIDATE;
- source/pool status decoupling: OBSERVED;
- structure fully replacing information as driver: NOT_ESTABLISHED.


## Fresh Whole-Process Batch001 preparation update

Offline fresh-run preparation is now implemented:

- design: `docs/v5_fresh_whole_process_design_v0.1.md`
- batch config: `configs/v5_whole_process_ecommerce_batch001_v0.1.json`
- subject gate: `configs/v5_whole_process_subject_gate_v0.1.json`
- manifest builder: `arena/build_v5_whole_process_manifest.py`
- structural index: `arena/v5_whole_process_index.py`
- offline preflight: `arena/v5_whole_process_preflight.py`
- tests: `arena/tests/test_v5_whole_process.py`

Offline preflight status: **PASS**.

The runtime/Agent prompts remain unchanged. The new index intentionally distinguishes mechanically observed shared-state visibility from semantic direct consumption.

Real provider execution remains **NOT AUTHORIZED**.


## Whole-Process runtime guard update

The fresh Batch001 runtime path is now repository-complete but remains non-authorized.

Prepared:

- real subject runner: `arena/run_v5_whole_process_real.py`;
- raw evidence freezer: `arena/freeze_v5_whole_process_evidence.py`;
- deterministic structural derivation: `arena/derive_v5_whole_process_structural.py`;
- paid authorization schema: `schemas/v5_whole_process_paid_authorization_v0.1.schema.json`;
- runtime guard tests: `arena/tests/test_v5_whole_process_runtime_guard.py`;
- workflow-dispatch-only runner: `.github/workflows/v5-whole-process-subject-real.yml`.

The exact phrase `CALL_REAL_V5_WHOLE_PROCESS_API` is necessary but not sufficient: positive call/spending limits are also required. Workflow budget inputs default to zero.

Current provider execution status: **NOT AUTHORIZED**.
