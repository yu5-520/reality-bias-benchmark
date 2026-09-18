# reality-bias-benchmark

Research repository for the Reality Bias program and first-paper **Process Reality** mechanism study.

Historical evidence remains append-only. Forward methods are versioned rather than silently rewriting frozen evidence or preregistration.

## Current forward layer

The current forward methodological layer is **Process Reality v5.1**.

v5.0 established the major theory/experiment-chain migration. v5.1 refines the engineering layer around semantic-lineage scoped repair. It does **not** add a new R stage and does **not** mutate historical v4.5.1 evidence, condition IDs or frozen design hashes.

Core forward files:

- \`docs/R_Plan_v5.0.md\`
- \`theory/theory_contract_v0.11.md\`
- \`docs/first_paper_v5_scope.md\`
- \`docs/v5_concept_mapping.md\`
- \`docs/v5_structural_observability_contract_v0.1.md\`
- \`docs/R5_structural_scouting_and_driver_probe_protocol_v1.0.md\`
- \`docs/R6_structural_support_trace_control_surface_protocol_v1.0.md\`
- \`docs/R7_localized_recovery_protocol_v1.0.md\`
- \`docs/v5_whole_process_experiment_protocol_v0.1.md\`
- \`docs/reporting/process_reality_report_standard_v1_7.md\`
- \`manifests/process_reality_v5_methodological_migration_2026-09-18.json\`

The historical v4.5.1 layer remains frozen for evidence already bound to it.

## Current reporting layer

Forward reports now use a trajectory-semantic evidence profile:

- `docs/reporting/process_reality_report_standard_v1_7.md`
- `docs/reporting/process_reality_experiment_report_template_v3.md`
- `docs/reporting/process_reality_theory_experiment_report_standard_v1_0.md`
- `docs/reporting/process_reality_engineering_experiment_report_standard_v1_1.md`

Core rule:

`Frozen structural facts -> realized Agent path -> evidence-bound semantic interpretation -> claim boundary`

Aggregate topology and hashes remain the factual substrate, but they do not replace the realized Agent path when path evidence exists.

Current R7 engineering report:

- `docs/reports/2026-09-18/R7_Process_Integrity_Engineering_Experiment_Report_v2.md`
- `manifests/r7_process_integrity_engineering_report_2026-09-18_v1.json`

## Cross-domain first-round experiment

The next prospective subject layer is a **held-out three-domain replication cohort**.

Ecommerce remains the method-development / deep-mechanism reference domain and is **not included in the new replication sample**.

Held-out replication domains:

- `finance`;
- `supply_chain`;
- `software_engineering`.

The replication rule is:

`replicate the frozen method, not the history of method development`.

Current v0.2 interfaces:

- `docs/cross_domain_first_round_experiment_plan_v0.2.md`
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

Prospective sample geometry:

- 30 natural trajectories per held-out domain;
- 90 new natural trajectories total;
- 2 preregistered waves per domain;
- 15 trajectories per wave;
- 6 domain-pure waves total.

One workflow-dispatch authorization prepares one common 90-row manifest and launches all six waves concurrently under the same execution SHA and authorization event. Each wave freezes its own evidence before structural derivation; a final registry binds all six wave evidence batches.

R2/R3/R4 are simultaneous views of each frozen natural trajectory. R5/R6/R7 are conditional extensions only after evidence-bound case qualification. R8 CPR adjudication is not part of this first-round execution plan.

Repository preparation authorizes no provider, probe, repair or paid evaluator call.

Owner-triggered real execution is fail-closed through:

- `.github/workflows/v5-cross-domain-chat-authorization-bridge.yml`;
- `.github/workflows/v5-cross-domain-first-round-subject-real.yml`.

The bridge pins one exact default-branch SHA to a one-time authorization tag before dispatching the six-wave subject workflow.

## v5 theory chain

\`\`\`text
Multi-source information / pressure / goal / boundary
  -> Unstable Information
  -> Agent-mediated transmission
  -> Escape Structure
  -> Semantic Transformation
  -> Structural Support
  -> Stable Shared Information Pool
  -> Direct Agent Consumption
  -> Constraint / Decision / Action Persistence
\`\`\`

Observation/control:

\`\`\`text
Structural Exposure
  -> Structural Scout
  -> Localized Semantic Audit
  -> Upstream Trace
  -> Downstream Closure
  -> Intervention-Surface Selection
  -> Local Repair
  -> Recovery Verification
\`\`\`

## Core distinctions

\`semantic genesis != structural support != stable-pool entry != structural exposure\`

\`Detection Surface != Trace Root != Intervention Surface\`

A stable shared pool is system-addressable/reusable state. It is **not** automatically true or confirmed information.

Historical \`Jump\`/\`J0\` identifiers remain valid provenance labels but are not automatically semantic origin, first structural-support point or exposure anchor.

## Forward R-stage responsibilities

### R2-R4 — natural formation views

Synchronously record one natural process; audit unstable information, transformations, adoption/coupling, support, pool entry and exposure asynchronously.

### R5 — structural scouting + driver probe

R5 reduces semantic-audit surface and may use a minimal probe to test source-information dependence versus already materialized structural support.

Historical \`fact -> unconfirmed\` remains one probe family, not the definition of R5.

### R6 — structural support / trace / control surface

R6 maps source, transformations, support, pool, exposure, upstream trace, downstream closure and candidate intervention surfaces.

System Inertia remains a downstream property rather than the entire R6 object.

### R7 — localized recovery

R7 repairs an explicitly selected intervention surface/RepairClosure while measuring preservation of unrelated structure.

### R8 / R9

R8 remains CPR semantic closure. R9 remains supplementary reviewer/model/domain replication.

## Whole-Process Run

The default future subject profile is a **Whole-Process Run**:

\`\`\`text
natural subject run
  -> raw evidence freeze
  -> integrity validation
  -> structural indexing
  -> support/pool/exposure scouting
  -> localized semantic audit
  -> reusable evidence bundle
\`\`\`

Optional controlled extensions:

- minimal driver probe;
- control-surface experiment;
- localized recovery;
- CPR adjudication;
- multi-reviewer/cross-model/cross-domain robustness.

The subject should not be rerun merely because a new semantic reviewer or analysis question is added.

## Optional robustness instead of mandatory chain growth

Historical modules remain available but are no longer default mandatory steps:

- S0-S4 specificity;
- matched-stock controls;
- R6-D Escape/J0 specificity;
- re-Jump count/distance;
- separate R6-A/B/C/D subject batches;
- multiple semantic reviewers;
- cross-model/domain replication.

This keeps the base experiment small while allowing later hypotheses to add only the modules they need.

## Process Integrity interfaces

Forward v5 machine-readable interfaces include:

- \`schemas/process_integrity_event_v0.3.schema.json\`
- \`schemas/process_integrity_lineage_record_v0.3.schema.json\`
- \`schemas/structural_support_record_v0.1.schema.json\`
- \`schemas/semantic_audit_record_v0.2.schema.json\`
- \`configs/structural_support_scout_v0.1.json\`
- \`configs/process_reality_measurement_contract_v1.0.json\`

Legacy Jump interfaces remain untouched for historical evidence compatibility.

## Historical re-derivation

Before a fresh v5 scientific run, existing R2-R6 evidence should be re-derived offline under:

- \`docs/v5_historical_rederivation_protocol_v0.1.md\`
- \`docs/v5_legacy_j0_reinterpretation_boundary.md\`
- \`docs/reports/2026-09-18/R2-R6_V5_Historical_Rederivation_Plan_v1.md\`

No historical raw evidence is rewritten.

## Current scientific status

The repository update itself creates no new subject evidence.

Not authorized by the v5 method layer:

- scientific provider run;
- paid evaluator run;
- CPR adjudication;
- active recovery.

CPR remains \`NOT_ADJUDICATED\`.

## Validation

Offline method synchronization:

\`\`\`bash
python scripts/validate_process_reality_v5.py
\`\`\`

Historical validators remain available for their own frozen layers.


## Fresh Whole-Process Batch001 readiness

The first fresh v5 subject design is prepared and has an offline preflight profile:

- `docs/v5_fresh_whole_process_design_v0.1.md`
- `configs/v5_whole_process_ecommerce_batch001_v0.1.json`
- `configs/v5_whole_process_subject_gate_v0.1.json`
- `arena/build_v5_whole_process_manifest.py`
- `arena/v5_whole_process_index.py`
- `arena/v5_whole_process_preflight.py`

Batch001 is three natural ecommerce repeats. The Arena runtime and Agent prompts are unchanged.

The structural index records support/pool/exposure candidates and preserves the boundary:

`POOL_VISIBILITY_OBSERVED != DIRECT_POOL_CONSUMPTION`

No real provider execution is authorized. The future exact authorization phrase is `CALL_REAL_V5_WHOLE_PROCESS_API`.


## v5.1 semantic-lineage scoped repair

v5.1 separates **scientific formation explanation** from **engineering repair control**.

Scientific formation remains dynamic across runs:

```text
Unstable Information
  -> variable Escape Structure
  -> Semantic Transformation
  -> Structural Support
  -> Stable Shared Information Pool
  -> Semantic Descendants
```

Engineering repair does not require the globally first support/pool node. It starts from a sufficiently exposed, addressable, repair-efficient **Structural Repair Anchor**:

```text
Structural Scout
  -> Structural Repair Anchor
  -> Content Address
  -> Semantic Lineage Closure
  -> Lineage Completeness Gate
  -> Localized Semantic Audit
  -> RepairClosure
  -> Invalidate / Revise / Recompute
  -> Verify
```

Key locality rule:

`local = complete relevant semantic lineage + minimal unrelated context`

not:

`local = shallow event window`.

The Repair Agent may interpret recorded lineage but may not invent missing semantic history as fact. `LINEAGE_GAP` blocks automatic repair.

## Paper-layer separation

The first paper now uses three explicit layers:

1. **Theory Experiment Report** — formation, persistence and mechanism boundaries.
2. **Engineering Experiment Report** — Repair Anchor, content addressing, lineage completeness, repair and recovery.
3. **Future Discussion** — portable Process Integrity protocols, cross-runtime/domain work and semantic/epistemic integrity infrastructure.

`Scientific Explanation != Engineering Control != Future Speculation`

## v5.1 Process Integrity interfaces

Forward engineering interfaces now include:

- `schemas/process_integrity_lineage_record_v0.4.schema.json`
- `schemas/process_integrity_relation_evidence_v0.2.schema.json`
- `schemas/semantic_lineage_closure_v0.1.schema.json`
- `schemas/lineage_completeness_gate_v0.1.schema.json`
- `schemas/semantic_repair_packet_v0.1.schema.json`
- `configs/r7_process_integrity_engineering_contract_v0.3.json`

Content address establishes identity/retrieval, not semantic adoption.

## Fresh Whole-Process Batch001 v0.2

The forward natural-batch design is now:

- `docs/v5_fresh_whole_process_design_v0.2.md`
- `configs/v5_whole_process_ecommerce_batch001_v0.2.json`
- `configs/v5_whole_process_subject_gate_v0.2.json`

Engineering core outputs:

- Repair Anchor candidates;
- Content Address Index;
- Pool Visibility Ledger;
- provenance;
- Semantic-Lineage Recoverability;
- downstream structural closure candidates.

First support / first pool / first exposure remain recorded as **optional mechanism observables**, not engineering prerequisites.

Real provider execution remains **NOT AUTHORIZED**.
