# Historical README snapshot — R-series development view

Date archived: 2026-09-22  
Source: repository `main` at commit `8c056854f9845952dbf24c0519a5a9a26a5bd60e`

This file preserves the former root README verbatim as a research-development record.

The historical README is intentionally R-series-heavy. It documents how the programme evolved, but it should **not** be read as a strict sequential experimental pipeline. Several R labels describe different analytical layers, views, or later audits of the same frozen trajectories.

The root README has been rebased to present the scientific object, evidence structure, reproducibility path, and open-research interfaces first.

---

# reality-bias-benchmark

Research repository for the Reality Bias program and first-paper **Process Reality** mechanism study.

Historical evidence remains append-only. Forward methods are versioned rather than silently rewriting frozen evidence or preregistration.

## Public frozen raw evidence

Completed raw subject evidence is public and downloadable. Runtime working directories remain ignored only to prevent accidental mutation before a freeze gate.

Public release:

`https://github.com/yu5-520/reality-bias-benchmark/releases/tag/frozen-raw-evidence-v1`

Repository access catalog:

- `evidence/frozen_raw/README.md`
- `evidence/frozen_raw/release_manifest_v1.json`
- `evidence/frozen_raw/SHA256SUMS_v1.txt`
- `evidence/frozen_raw/catalog_v1/`

Current public frozen-raw release: **24 byte-preserved evidence archives** covering discovery history, the held-out natural R2-R4 cohort, canonical R5 batches, R7 raw runs and earlier R2-R6/R5MID/R6D mechanism evidence.

Core evidence rule:

`frozen = public readable/downloadable + SHA-256 locked + append-only versioning`

not:

`frozen = hidden`

The original historical Actions artifact IDs and digests remain in the source registries. Publication verifies downloaded bytes against those frozen digests before exposing them as release assets. Existing release assets are not overwritten; a correction must create a new version.


## Current forward layer

The current forward methodological layer is **Process Reality v5.4**.

v5.3 remains the probability/structure separation predecessor. v5.4 adds the canonical stochastic-realization geometry:

`domain probability != realized case != intervention mode != supplementary repetition`.

No new R stage is added and no frozen historical evidence is mutated.

Canonical case matrix:

`N0 frozen natural -> R5-I one-shot -> R6 passive -> {R7-P persistent, R7-S structured repair} -> R8`.

Core forward files:

- `docs/R_Plan_v5.4.md`
- `theory/theory_contract_v0.15.md`
- `docs/first_paper_v5_4_scope.md`
- `configs/process_reality_canonical_experiment_geometry_v1.0.json`
- `docs/R5_canonical_single_intervention_protocol_v1.0.md`
- `docs/R7_dual_intervention_protocol_v2.0.md`
- `docs/v5_whole_process_experiment_protocol_v0.3.md`
- `docs/canonical_stochastic_realization_principle_v1.0.md`
- `docs/legacy_execution_geometry_registry_v1.0.md`
- `configs/r7_process_integrity_engineering_contract_v0.5.json`

v5.3 source files remain frozen predecessor interfaces, including `docs/R_Plan_v5.3.md`, `theory/theory_contract_v0.14.md` and `configs/process_reality_probability_structure_separation_v1.0.json`.

The historical v4.5.1 layer remains frozen for evidence already bound to it.

## Current reporting layer

Forward reports now use a trajectory-semantic evidence profile:

- `docs/reporting/process_reality_report_standard_v1_7.md`
- `docs/reporting/process_reality_experiment_report_template_v3.md`
- `docs/reporting/process_reality_theory_experiment_report_standard_v1_2.md`
- `docs/reporting/process_reality_engineering_experiment_report_standard_v1_2.md`

Core rule:

`Frozen structural facts -> realized Agent path -> evidence-bound semantic interpretation -> claim boundary`

v5.4 reporting additionally requires separate accounting for canonical new provider trajectories versus supplementary repeated sampling. Historical executed branch totals cannot substitute for canonical case counts.

Aggregate topology and hashes remain the factual substrate, but they do not replace the realized Agent path when path evidence exists.

Current R7 engineering report:

- `docs/reports/2026-09-18/R7_Process_Integrity_Engineering_Experiment_Report_v2.md`
- `manifests/r7_process_integrity_engineering_report_2026-09-18_v1.json`

## Canonical R5 / R7 geometry

Forward subject execution now uses realized-path geometry rather than same-parent resampling as the main experiment.

**R5**

`1 selected case = existing N0 natural reference + exactly 1 new R5-I one-shot continuation`.

Machine boundary:

- new synthetic control branches: **0**;
- new intervention branches per case: **1**;
- canonical replicate count: **1**;
- natural reference rerun: **NO**.

Forward interfaces:

- `arena/prepare_v5_cross_domain_r5_canonical.py`;
- `arena/run_v5_cross_domain_r5_canonical.py`;
- `arena/freeze_v5_cross_domain_r5_canonical.py`.

**R6**

R6 remains passive and adds **0** subject/provider trajectories.

**R7**

R7 now has exactly two canonical intervention modes:

- `R7-P` — persistent semantic correction;
- `R7-S` — structured lineage repair.

R5-I/C1 is a frozen reference and is not rerun inside R7.

Per R7-qualified case:

- R7-P: **1** new trajectory;
- R7-S: **1** new trajectory;
- C1 reruns: **0**;
- canonical replicates: **1**.

Forward interfaces:

- `arena/prepare_r7_dual_intervention_plan.py`;
- `arena/run_r7_dual_intervention_real.py`;
- `arena/freeze_r7_dual_intervention_evidence.py`.

Historical matched-pair R5 and historical C1/C2/C3 R7 runs remain immutable. Their extra same-parent branches are reclassified as supplementary local sensitivity / engineering robustness rather than canonical evidence admission.

Canonical provider geometry for a case reaching R7:

`R5 1 + R6 0 + R7 2 = 3 new provider trajectories`.

## Probability / structure separation

The cross-domain program now uses two different scientific units.

**Probability layer**

`Domain Environment -> natural stochastic trajectory population -> occurrence / distribution`

The held-out three-domain first round is the probability experiment:

- finance: 30 natural trajectories;
- supply_chain: 30 natural trajectories;
- software_engineering: 30 natural trajectories.

**Structure layer**

`realized natural case -> localized semantic audit -> optional R5 probe -> passive R6 structure -> lineage completeness gate -> optional R7`

R5/R6 do not re-estimate domain probability.

Entering R6 does **not** require an additional provider run.

Repeated trials from one frozen parent are only:

`SUPPLEMENTARY_LOCAL_CONDITIONAL_SENSITIVITY`

They cannot estimate domain prevalence, gate R6, gate R7, or erase a carrier/read/adoption/persistence chain already recorded in a realized case.

Interpretation correction:

- `docs/reports/2026-09-19/V5_Cross_Domain_Probability_Structure_Interpretation_Correction_v1.md`;
- `manifests/v5_cross_domain_probability_structure_reclassification_2026-09-19_v0_1.json`.

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

Post-run frozen-evidence triage interfaces:

- `docs/cross_domain_semantic_triage_protocol_v0.1.md`
- `configs/v5_cross_domain_semantic_triage_v0.1.json`
- `schemas/v5_cross_domain_semantic_triage_case_v0.1.schema.json`
- `arena/build_v5_cross_domain_semantic_triage.py`

The triage stage deterministically compresses structural candidates into trajectory-bound localized semantic-audit cases. It does not adjudicate semantic adoption, authority error, System Inertia, CPR, R5 eligibility or R7 repairability.

Completed first-round triage:

- source subject workflow: `35370679448`;
- successful triage workflow: `35377246079`;
- 90 frozen trajectories -> 167 unique localized-audit cases;
- result report: `docs/reports/2026-09-19/V5_Cross_Domain_Semantic_Triage_Report_v1.md`;
- result manifest: `manifests/v5_cross_domain_semantic_triage_2026-09-19_v0_1.json`.

Localized semantic audit pass 1 is now frozen for the 29 authority-review cases that satisfy `source status = fact + explicit uncertainty marker`:

- finance: 5;
- software_engineering: 8;
- supply_chain: 16;
- reviewer: GPT-5.6 Sol;
- adoption / decision-action dependence: `SUPPORTED_CANDIDATE`;
- uncertainty preservation: `SUPPORTED_CANDIDATE`;
- authority escalation: `NOT_ESTABLISHED`;
- scientific R5 eligibility: 29;
- existing `fact -> unconfirmed` operator compatible: 29;
- R5 execution authorized: **NO**.

The other 56 authority-review cases use provisional or unspecified source status and remain deferred until a separate source-status-withdrawal operator is frozen.

Pass-1 interfaces:

- `docs/cross_domain_localized_semantic_audit_protocol_v0.1.md`;
- `manifests/v5_cross_domain_localized_semantic_audit_review_2026-09-19_v0_1.json`;
- `schemas/v5_cross_domain_localized_semantic_audit_record_v0.1.schema.json`;
- `arena/build_v5_cross_domain_localized_semantic_audit.py`.

Completed pass-1 execution:

- workflow: `35378782053`;
- artifact: `10561246944`;
- artifact digest: `sha256:457b4fc91d09dcec0a3dbe609068761d238df24679fb40dd7db26c06e3630e60`;
- summary hash: `b97ae65a2ff3ab808abf7e39aa45ffda320dd6786db6b3369bf82d575057d9a3`;
- 29 unique source-case hashes -> 29 unique audit hashes;
- result report: `docs/reports/2026-09-19/V5_Cross_Domain_Localized_Semantic_Audit_Pass1_Report_v1.md`;
- result manifest: `manifests/v5_cross_domain_localized_semantic_audit_pass1_2026-09-19_v0_1.json`;
- R5 scientific eligibility: **29**;
- R5 execution authorization: **NO**.


Completed cross-domain R5 first wave:

- workflow: `35381406873`;
- artifact: `10564055226`;
- artifact digest: `sha256:a711f507365504bd59ca179bd3d76ea4c57d97caf6f6be85a6f4ef1f88629457`;
- 6 source-bound cases / 12 matched pairs / 24 branches;
- preserved traces: **24 / 24**;
- runner errors: **0**;
- estimated provider spend: **USD 1.504547232**;
- raw evidence batch hash: `26f63b182ca704fbf8119f5c75894e9f219e0c22ce6fadeaa6eb2dd95b06ea68`;
- exact structural inequality: 12 / 12 pairs at first response/action/path/final-state levels;
- replicate-stable material semantic effect: **0 / 6 cases**;
- one mixed material-response case: `wave-4-8b1731b57396`;
- report: `docs/reports/2026-09-19/V5_Cross_Domain_R5_First_Wave_Semantic_Audit_R6_Candidate_Report_v1.md`;
- result manifest: `manifests/v5_cross_domain_r5_first_wave_2026-09-19_v0_1.json`.

The R5 result therefore distinguishes **structural sensitivity** from **semantic/material effect**. Universal exact-output divergence is not treated as causal evidence because provider stochasticity remains a competing explanation.

R6 has one evidence-bound realized structure from supply-chain wave 4. In one R5 intervention continuation, the one-shot authority withdrawal is followed by a new `inventory_coverage_assessment` and plan revision, then downstream read/adoption by risk, supply_lead and sales after the direct stimulus has disappeared.

Under v5.3 this is interpreted at the **case-structure** level:

- carrier/read/adoption/persistence chain: **SUPPORTED IN THE REALIZED BRANCH**;
- R6 entry: **already satisfied from frozen R5 evidence**;
- case-level System Inertia: **SUPPORTED CANDIDATE PENDING LINEAGE COMPLETENESS REVIEW**;
- domain-level occurrence rate: **must be derived from natural supply-chain trajectories**;
- R7 repair authorization: **NO — pending case-level lineage completeness reassessment**.

A later fixed-parent follow-up was executed for the same parent, but is now reclassified as supplementary local conditional sensitivity:

- config: `configs/v5_cross_domain_r6_targeted_specificity_v0.1.json`;
- target: `wave-4-8b1731b57396`;
- workflow: `35423813470`;
- artifact: `10577929510`;
- artifact digest: `sha256:88a85d71b4c7784b7479b36c93c1cdbcf1f52e9a208a3c9e7c28d4553e9b1198`;
- 8 new matched pairs / 16 branches;
- preserved traces: **16 / 16**;
- runner errors: **0**;
- estimated provider spend: **USD 1.43038968**;
- combined target-case evidence: **10 matched pairs**;
- exact `no standard transfer -> procurement / expedite` phenotype: control **0 / 10**, intervention **1 / 10**;
- the eight new intervention branches reproduced that exact phenotype **0 / 8**;
- exact-phenotype local recurrence: control **0 / 10**, intervention **1 / 10**;
- eight new intervention branches reproduced the exact phenotype **0 / 8**;
- forward role: **SUPPLEMENTARY_LOCAL_CONDITIONAL_SENSITIVITY**;
- estimates domain probability: **NO**;
- required for R6 entry: **NO**;
- required for R7 entry: **NO**;
- historical result report: `docs/reports/2026-09-19/V5_Cross_Domain_R6_Targeted_Specificity_Result_v1.md`;
- reclassification: `docs/cross_domain_probability_structure_interpretation_addendum_v0.1.md`.

The follow-up bounds local recurrence of one exact phenotype. It does not negate the original realized carrier/read/adoption/persistence chain. R7 status is now `NOT_AUTHORIZED_PENDING_CASE_LEVEL_LINEAGE_COMPLETENESS_REASSESSMENT`.

Completed v5.3 passive R5-R6 structural + semantic audit wave 1:

- R5 source workflow: `35381406873`;
- passive structural materialization workflow: `35429085193`;
- structural artifact: `10580091785`;
- semantic audit workflow: `35429324484`;
- semantic artifact: `10580655035`;
- semantic summary hash: `d78d411c612afd31f24c6b572c560a619bdcc0c86ee437ab196648cb8af0e823`;
- 12 intervention branches / 6 source-bound cases;
- downstream semantic adoption: **12 / 12**;
- decision/action dependence: **12 / 12**;
- post-stimulus persistence: **12 / 12**;
- stronger case-level System Inertia candidates: **2 / 6 cases** — supply-chain wave 4 and software-engineering wave 6;
- normal / re-anchored / boundary-preserving persistence: **4 / 6 cases**;
- problematic bias established: **0 / 6**;
- R5 unique causal attribution established: **0 / 6**;
- lineage completeness: **not assessed in this pass**;
- R7: **NOT AUTHORIZED**;
- CPR: **NOT_ADJUDICATED**;
- report: `docs/reports/2026-09-19/V5_3_Cross_Domain_R5_R6_Structural_Semantic_Audit_Wave1_Report_v1.md`;
- result manifest: `manifests/v5_cross_domain_r5r6_semantic_audit_wave1_2026-09-19_v0_1.json`.

Key R6 finding:

`post-stimulus semantic persistence != System Inertia by default`.

Normal inheritance, evidence re-anchoring, boundary preservation and pre-existing conservative-gate reinforcement are separated from stronger new-carrier -> downstream-constraint persistence.

Completed v5.3 passive R5-R6 structural + semantic audit wave 2:

- original R5 second-wave workflow: `35436694271`;
- original R5 artifact: `10582866320`;
- balance-recovery workflow: `35438000140`;
- recovery artifact: `10583013224`;
- recovered pre-response HTTP-402 branches: **12 / 12**;
- original failed traces overwritten: **NO**;
- combined effective structural workflow: `35439212051`;
- combined structural artifact: `10583133758`;
- effective evidence hash: `4b1913a678f876b16e86e271a31936eebf2da82937009a61c4188c3ffb000b98`;
- R6 structural summary hash: `1b19fbec44f10182c49e30d645247f51a3e084af035029951660971ec11d8d6e`;
- semantic audit workflow: `35439402409`;
- semantic artifact: `10583382240`;
- semantic artifact digest: `sha256:caa46faa5af4446764a4647485e098e703c946edc28d1ab45558b729287dde4b`;
- semantic summary hash: `208d97ff2d2ab2990cf92cabbb82f55f7be91a8956348807d49c268a54dd4ecb`;
- 10 intervention branches / 5 source-bound cases;
- downstream semantic adoption: **10 / 10**;
- decision/action dependence: **10 / 10**;
- post-stimulus persistence: **10 / 10**;
- stronger case-level System Inertia candidates: **2 / 5 cases** — supply-chain wave 3 and wave 4;
- normal / re-anchored / pre-existing-gate persistence: **3 / 5 cases**;
- problematic bias established: **0 / 5**;
- R5 unique causal attribution established: **0 / 5**;
- lineage completeness: **not assessed in this pass**;
- R7: **NOT AUTHORIZED**;
- CPR: **NOT_ADJUDICATED**;
- report: `docs/reports/2026-09-19/V5_3_Cross_Domain_R5_R6_Structural_Semantic_Audit_Wave2_Report_v1.md`;
- result manifest: `manifests/v5_cross_domain_r5r6_semantic_audit_wave2_2026-09-19_v0_1.json`.

The wave-3 control replicate that encountered HTTP 402 only after 25 completed model calls was **not rerun**. It remains a late-truncated control context because restarting it from the frozen parent would create a new stochastic path rather than recover the realized trajectory.

Canonical v5.4 R5-R6 mechanism-audit pool after exhaustive Wave5 closure:

- Wave1-2 historical evidence was reclassified canonically as **11 N0 references + 11 R5-I continuations**; historical extra same-parent branches remain supplementary sensitivity evidence;
- Wave3: **5 cases = 5 R5-I trajectories**, estimated provider spend **USD 0.2235309**;
- Wave4: **4 cases = 4 R5-I trajectories**, estimated provider spend **USD 0.23939382**;
- Wave5 exhaustive closure: **9 cases = 9 R5-I trajectories**, estimated provider spend **USD 0.608222526**;
- Wave5 R5 workflow: `35447065280`; R6 structural workflow: `35447899994`; semantic workflow: `35448283795`;
- frozen Pass-1 R5-eligible coverage: **29 / 29**;
- intentionally unexecuted Pass-1 eligible cases: **0**;
- total canonical source-bound cases: **29**;
- total canonical R5-I continuations: **29**;
- semantic adoption: **29 / 29**;
- post-stimulus persistence: **29 / 29**;
- stronger System Inertia candidates: **4 / 29 cases**;
- normal / re-anchored persistence: **25 / 29 cases**;
- problematic bias established: **0 / 29**;
- unique R5 causality established: **0 / 29**;
- remaining Pass-1 R5-eligible cases: **0**.

Wave5 is an exhaustive set-difference closure, not a new sampled wave:

`Pass1Eligible29 - CanonicalCompleted20 = 9`.

No random sampling, outcome-aware ranking, replacement or discretionary screening was used inside this final nine-case batch. This closes one avoidable methodological criticism: within the already-frozen 29-case Pass-1 R5-eligible set, the final mechanism pool is not produced by stopping after convenient cases.

All nine Wave5 cases again show downstream semantic adoption and persistence, but each is better explained by independent evidence re-anchoring or a pre-existing plan/gate than by a new source-specific constraint. The stronger distinction therefore remains:

`post-stimulus persistence != System Inertia by default`.

The first Wave4 semantic materialization is retained as a superseded metadata artifact because its reusable summary text still said Wave3/five cases; the corrected materialization changes no case-level semantic decisions.

The complete **4 / 29** classification is still **not a domain-probability denominator**. It describes the exhaustive frozen Pass-1 eligible mechanism-audit set, not the 90 natural-trajectory population.

Wave3 report: `docs/reports/2026-09-19/V5_4_Canonical_R5_R6_Wave3_Result_Report_v1.md`.

Wave4 report: `docs/reports/2026-09-19/V5_4_Canonical_R5_R6_Wave4_Result_Report_v1.md`.

Wave5 exhaustive result report: `docs/reports/2026-09-19/V5_4_Canonical_R5_R6_Wave5_Exhaustive_Result_Report_v1.md`.

Wave5 result manifest: `manifests/v5_4_r5r6_canonical_wave5_exhaustive_2026-09-19_v0_1.json`.

Prospective sample geometry:

- 30 natural trajectories per held-out domain;
- 90 new natural trajectories total;
- 2 preregistered waves per domain;
- 15 trajectories per wave;
- 6 domain-pure waves total.

One workflow-dispatch authorization prepares one common 90-row manifest and launches all six waves concurrently under the same execution SHA and authorization event. Each wave freezes its own evidence before structural derivation; a final registry binds all six wave evidence batches.

R2/R3/R4 are simultaneous views of each frozen natural trajectory. R5/R6/R7 are conditional extensions only after evidence-bound case qualification. R8 CPR adjudication is not part of this first-round execution plan.

Repository preparation authorizes no provider, probe, repair or paid evaluator call.

Owner-triggered real execution is fail-closed through the registered chat-control workflow plus the scientific subject workflow:

- `.github/workflows/r7-chat-authorization-bridge.yml` — also carries the cross-domain authorization job;
- `.github/workflows/v5-cross-domain-first-round-subject-real.yml`.

The control plane pins one exact default-branch SHA to a one-time authorization tag before dispatching the six-wave subject workflow.

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

### R6 — passive case-level structural identification

R6 consumes already-frozen natural/R5 evidence and maps source, carrier/support, downstream read, adoption, persistence, affected closure and candidate intervention surfaces.

Entering R6 does not require an additional provider experiment.

System Inertia may be reported as a case-level property; its domain-level occurrence rate belongs to the natural trajectory population.

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

## R8 Dynamic CPR semantic closure (v5.5)

Forward R8 semantics are now append-only and use a dynamic three-dimensional Process Reality Permission-Penetration model:

- C — information permission penetration;
- P — collaboration/execution boundary permission penetration;
- R — temporal permission penetration.

C/P/R are not treated as three exclusive static task labels. They may overlap, transition and mutually maintain one another through the Shared Process-Reality Layer.

Core forward files:

- `docs/R_Plan_v5.5.md`
- `theory/theory_contract_v0.16.md`
- `docs/R8_Dynamic_CPR_Permission_Penetration_Protocol_v0.3.md`
- `configs/cpr_definition_contract_v0.3.json`
- `configs/cpr_adjudication_contract_v0.3.json`
- `schemas/r8_dynamic_cpr_event_v0.2.schema.json`
- `arena/prepare_r8_dynamic_cpr_audit_material.py`
- `scripts/validate_r8_dynamic_cpr_v0_3.py`

Historical R8/CPR contracts and all frozen R2-R7 evidence remain immutable. This update authorizes no provider subject run and no paid evaluator call.

## R8 Cross-stage Dynamic CPR (v5.6)

Forward R8 now treats R2-R7 as multiple observation contexts rather than using R5 as the sole semantic entry point.

Branch geometry:

- `R8-B1` — frozen R5/R6 target-bound authority audit;
- `R8-B2` — R2-R4 natural Dynamic CPR audit over the 90 frozen trajectories;
- `R8-B3` — R6 carrier/reader/adoption/inertia mechanism windows;
- `R8-B4` — R7 persistent-correction and repair/reopen/recompute windows;
- `R8-C` — cross-stage coupling synthesis after B2/B3/B4 closure.

The historical R8-B result is preserved and repositioned as B1. Its P=0/R=0 findings apply only to the 29 target-bound B1 packets, not to the whole first round.

Core forward files:

- `docs/R_Plan_v5.6.md`
- `theory/theory_contract_v0.17.md`
- `docs/R8_Dynamic_CPR_Permission_Penetration_Protocol_v0.4.md`
- `configs/r8_cross_stage_observation_surface_registry_v0.1.json`
- `results/r8_cross_stage_observation_surface_registry_v0_1/summary.json`
- `docs/reports/2026-09-20/R8_Cross_Stage_Observation_Surface_Registry_Result_v1.md`

Current overall semantic status: `PARTIAL_B1_ONLY`. No new subject runs are authorized by this rebase.

## R8 B2/B3/B4 semantic status

The cross-stage semantic pass now has:

- `B1` — frozen complete: 2 C-supported target-bound lineages;
- `B2` — natural high-risk window audit v0.1 complete but explicitly nonexhaustive: 21 C / 15 P / 44 R selected windows, no supported permission penetration in those selected windows;
- `B3` — frozen complete over 29 R6 complete routes: C=2, P=0, R=0;
- `B4` — frozen complete over four R7 dual cases: 32 reopened calls / 135 recomputed descendants, no new post-repair C/P and no Dynamic R established.

`R8-C` remains blocked for final cross-stage coupling synthesis until B2 reaches exhaustive semantic coverage or a predeclared natural-window stopping rule is frozen.

See:

- `docs/reports/2026-09-20/R8_B2_B3_B4_Cross_Stage_Semantic_Audit_Result_v1.md`
- `results/r8_cross_stage_semantic_status_v0_2/summary.json`
- `manifests/r8_b2_b3_b4_cross_stage_semantic_audit_2026-09-20_v0_1.json`

## R8 Trajectory-First Dynamic Semantic Audit (v5.7)

Forward canonical R8 now audits **complete dynamic semantic trajectories**, not structurally selected screenshots/windows.

Canonical chain:

`full frozen trajectory -> dynamic semantic reconstruction -> functional semantic lineage -> goal/boundary/process/result alignment -> retrospective/censor timeline -> joint C/P/R -> coupling`.

Key rules:

- structure is evidence indexing only;
- source wording may disappear while functional semantic influence persists;
- P requires original-goal vs authorized-boundary vs realized-process vs final-result comparison;
- R requires full post-review/reopen/recompute continuation;
- active censored chains cannot enter a negative pool;
- historical/superseded R7 trajectories remain auditable evidence;
- previous `C=2 / P=0 / R=0` aggregates are not canonical Dynamic CPR totals.

Forward files:

- `docs/R_Plan_v5.7.md`
- `theory/theory_contract_v0.18.md`
- `docs/R8_Trajectory_First_Dynamic_Semantic_Audit_Protocol_v0.5.md`
- `configs/r8_dynamic_semantic_audit_contract_v0.4.json`
- `configs/r8_trajectory_first_source_registry_v0.1.json`
- `arena/build_r8_trajectory_first_semantic_packets.py`
- `schemas/r8_trajectory_semantic_audit_packet_v0.1.schema.json`
- `schemas/r8_dynamic_semantic_episode_v0.1.schema.json`
- `docs/reports/2026-09-20/R8_Audit_Chain_Repair_Result_v1.md`

Current status: `TRAJECTORY_FIRST_CHAIN_REPAIR_COMPLETE_REAUDIT_REQUIRED`.

## R8 Trajectory-First Second Audit — Discovery Included

The canonical R8 second audit now includes the original E-commerce discovery-domain multi-Agent evidence as well as the held-out/mechanism evidence.

Forward frozen state:

- analysis inventory: `150` trajectories (not a prevalence denominator);
- E-commerce formal discovery Batch001 denominator: `n=3`;
- held-out natural replication denominator: `n=90`;
- high-confidence Dynamic C anchors: `3`;
- Dynamic P supported trajectories: `23`;
- retrospective-generative Dynamic R supported trajectories: `18`;
- supported coupling: `R_GENERATES_P=17`, `R_GENERATES_C=1`, `C_DRIVES_P=2`;
- `P_REINFORCES_C=2` remains candidate evidence, not a closed mutual-maintenance loop.

E-commerce discovery formal Batch001 is `C=1, P=1, R=2`; functional semantic continuation is observed in all 9 reviewed discovery-history traces but is reported separately from permission penetration.

Complete per-trajectory adjudication records are frozen as compressed JSONL. Active-censored/failure-prefix tails are never treated as negative evidence.

Forward files:

- `results/r8_trajectory_first_second_audit_v0_1/summary.json`
- `results/r8_ecommerce_discovery_trajectory_first_reaudit_v0_1/summary.json`
- `results/r8_trajectory_first_second_audit_combined_v0_2/summary.json`
- `configs/r8_trajectory_first_source_registry_v0.2.json`
- `results/r8_forward_semantic_chain_status_v0_5/summary.json`
- `docs/reports/2026-09-20/R8_Trajectory_First_Second_Audit_Combined_Result_v1.md`

No subject reruns, new provider calls or paid evaluator calls were used for this audit.

## R8 Dynamic CPR Semantic Closure Report

The canonical trajectory-first R8 theory/phenomenon report is now repository material:

- `docs/reports/2026-09-20/R8_Trajectory_First_Dynamic_CPR_Semantic_Closure_Report_v1.md`

It follows Process Reality Report Standard v1.5 and the Theory Experiment Report Standard v1.0.

The report preserves separate denominators, censor-aware interpretation, and explicit typical chains for Dynamic C, P, R and supported cross-penetration relations. Paper-level freeze remains `NOT_YET`.

## R9 Innovation Synthesis / Prior-Art Boundary / Outlook

R9 is now the first-paper **innovation/contribution closure layer**, not a mandatory compute-heavy replication stage.

Canonical role:

`R2-R8 frozen evidence -> prior-art boundary -> contribution ledger -> synthesis -> research outlook`.

R9 v1 binds 12 peer-reviewed anchor papers plus 3 high-risk/synthesis preprints and explicitly constrains novelty claims against MAS failure taxonomies, communication topology/information propagation, execution/epistemic provenance, memory propagation, rollback/recovery and task-scoped semantic transactions.

Core outputs:

- `docs/R_Plan_v5.8.md`
- `docs/R9_Innovation_Synthesis_Prior_Art_Outlook_Protocol_v1.md`
- `docs/related_work/R9_Prior_Art_Literature_Map_v1.md`
- `docs/related_work/R9_Innovation_Boundary_Matrix_v1.md`
- `docs/related_work/R9_First_Paper_Contribution_Ledger_v1.md`
- `docs/reports/2026-09-20/R9_Innovation_Synthesis_Prior_Art_Boundary_and_Outlook_Report_v1.md`
- `configs/r9_innovation_boundary_contract_v1.json`
- `configs/r9_literature_registry_v1.json`

Cross-model/provider/topology and independent-lab replication remain future **external validation**, not already-established robustness.

No new subject/provider/evaluator execution is authorized by R9.

## R9 v2 — Inter-System Process Reality

R9 v2 sharpens the first-paper innovation layer from component-level novelty defense to a system-level synthesis.

Controlled experimental realization:

`multi-Agent Process Reality`.

Broader research direction:

`Inter-System Process Reality / Semantic Process Integrity`.

Primary integrated innovation target:

`Semantic Object -> Content Address -> Hash/Evidence Lineage -> Functional Semantic Lineage -> Authority History -> Dynamic CPR Audit -> Affected Closure -> Semantic Repair Packet -> Selective Reopen/Recompute -> Preserve Unrelated Semantics -> Re-entry Watch`.

This is treated as a **Semantic Process Integrity Stack**: the same semantic object remains addressable from observation through repair rather than being discarded after diagnosis.

R9 v2 also records three explicit boundaries:

- Supplementary Note S1 is a provenance-backed Human-AI **P-like reflexive illustration**, not formal CPR evidence.
- Open-sourcing the repository provides reproducibility and an external-replication interface; it does **not** mean independent external replication is already complete.
- Inter-System Process Reality, Cross-System Semantic Lineage and Semantic-Authority Interface Contracts are **future research directions**, not experimentally established universal generalizations.

Canonical R9 v2 files:

- `docs/reports/2026-09-20/R9_Inter_System_Process_Reality_Innovation_Synthesis_and_Outlook_Report_v2.md`
- `docs/R_Plan_v5.9.md`
- `docs/related_work/R9_Innovation_Boundary_Matrix_v2.md`
- `docs/related_work/R9_First_Paper_Contribution_Ledger_v2.md`
- `configs/r9_innovation_boundary_contract_v2.json`
- `manifests/r9_inter_system_process_reality_synthesis_2026-09-20_v2.json`
- `theory/change_notes/CN-R-072_r9_inter_system_process_reality_rebase.md`

No new subject/provider/evaluator execution or frozen-evidence mutation is authorized by this synthesis layer.

## R9 outlook application — Character–World Process Reality Protocol

R9 v2 remains frozen and unchanged. A new append-only application-outlook note instantiates **Inter-System Process Reality** inside the existing business-deployment branch:

`Character System <-> Process Reality Protocol <-> World / Social System`.

This does **not** create a third top-level outlook direction. It belongs under:

`Business deployment / persistent operational reality`.

The note distinguishes two persistence problems:

- **Persistent Character Reality** — identity, traits, beliefs, relationships, memory and current behaviour;
- **Persistent World / Social Reality** — world rules, institutions, authority, public state, local environment and historical revisions.

Core protocol principles:

- retrieval is not authorization;
- language is not world-write permission;
- fast state does not automatically rewrite slow state;
- local events do not automatically authorize global structural change;
- historical state re-entry requires a valid re-entry path.

Canonical files:

- `docs/outlook/R9_Character_World_Process_Reality_Protocol_Outlook_v1.md`
- `configs/r9_character_world_process_reality_outlook_v0.1.json`
- `manifests/r9_character_world_outlook_2026-09-20_v0_1.json`
- `theory/change_notes/CN-R-073_character_world_process_reality_protocol_outlook.md`
- `scripts/validate_r9_character_world_outlook_v0_1.py`

Scientific status:

`APPLICATION OUTLOOK / CONCEPTUAL INSTANTIATION / NO NEW EXPERIMENTAL EVIDENCE`.

No formal game-system CPR claim, provider execution, evaluator execution or frozen-evidence mutation is authorized.

## NMI Submission Track

The first-paper programme has transitioned from R-series research construction to **Nature Machine Intelligence submission engineering**.

Current rule:

`R8 scientific closure + R9 innovation/outlook closure -> NMI submission track`

No R10 is created for the first submission.

New experiments are blocked by default unless they repair a concrete scientific or submission defect. New applications and broader system directions default to Discussion / Outlook / future work.

Current implemented stages:

- **NMI-P0 — Paper Freeze**
- **NMI-P1 — Figure Architecture**
- **NMI-P2 — Claim-to-Evidence Map**

Next gate:

- **NMI-P3 — Manuscript v0.1**

Target NMI Article constraints currently bound in the repository:

- 3,500-word main-text maximum;
- 150-word abstract maximum;
- up to 6 figures/tables;
- local target: 3,200-3,350 main-text words and 5 main display items.

The manuscript narrative will not mirror R2-R9 chronology. The forward Results story is:

`endpoint/process separation`
-> `Dynamic CPR`
-> `Functional Semantic Lineage`
-> `local authority perturbation / inertia`
-> `lineage-level semantic repair`.

Canonical submission-engineering files:

- `docs/submission/nmi/NMI_Submission_Track_v1.md`
- `docs/submission/nmi/NMI_P0_Paper_Freeze_v1.md`
- `docs/submission/nmi/NMI_P1_Figure_Architecture_v1.md`
- `docs/submission/nmi/NMI_P2_Claim_Evidence_Map_v1.md`
- `docs/submission/nmi/NMI_Reviewer_Attack_Matrix_v1.md`
- `docs/submission/nmi/NMI_Official_Submission_Requirements_2026-09-20.md`
- `configs/nmi_submission_contract_v1.json`
- `manifests/nmi_submission_track_2026-09-20_v1.json`
- `theory/change_notes/CN-R-074_nmi_submission_track_handoff.md`

No new subject/provider/evaluator execution or frozen-evidence mutation is authorized by this transition.

## NMI Opening Rebase

The submission opening has been sharpened around one natural Dynamic C anchor:

`ec-discovery::formal_batch001::2::arena-ecommerce-0002`.

The first-page anomaly is intentionally simple:

`~1,520 preliminary/unreconciled -> ~1,520 fact/reconciled`

with no new independent warehouse reconciliation in the reviewed trajectory.

Canonical hook:

> **The value remained unchanged. Its permission to count as reality did not.**

The submission theory order is now:

`natural case`
-> `Process Reality`
-> `Semantic Authority Migration`
-> `Dynamic C`
-> `Dynamic C/P/R`
-> `Functional Semantic Lineage`
-> `local perturbation / inertia`
-> `lineage-addressed repair`
-> `Inter-System Process Reality outlook`.

This supersedes the earlier generic Figure-1-first framing for submission purposes while preserving all predecessor files.

Current canonical NMI files:

- `docs/submission/nmi/NMI_Submission_Track_v1.1.md`
- `docs/submission/nmi/NMI_Editorial_Opening_Strategy_v1.md`
- `docs/submission/nmi/NMI_P1_Figure_Architecture_v1.1.md`
- `docs/submission/nmi/NMI_P2_Claim_Evidence_Map_v1.1.md`
- `configs/nmi_submission_contract_v1.1.json`
- `manifests/nmi_opening_rebase_2026-09-20_v1.json`
- `theory/change_notes/CN-R-075_nmi_opening_rebase_natural_authority_migration.md`

Next gate remains:

`NMI-P3 — Manuscript v0.1`.

No new subject run, provider/evaluator call, CPR adjudication or raw-evidence mutation is authorized by this narrative update.

## NMI-P3 Manuscript v0.1

The first complete journal-facing manuscript draft is now frozen for reviewer attack.

Canonical manuscript:

- `docs/submission/nmi/NMI_Manuscript_v0.1.md`

Working title:

> **Process reality in multi-agent AI systems**

Opening:

`~1,520 preliminary/unreconciled -> no new independent warehouse reconciliation -> ~1,520 fact/reconciled`.

Hook:

> **The value remained unchanged. Its permission to count as reality did not.**

Current manuscript budget:

- abstract: ~147 words;
- main text before Methods: ~2,641 words;
- official NMI main-text ceiling: 3,500 words.

The manuscript remains intentionally below the local 3,200-3,350 working target. Remaining space is reserved for reviewer-attack-driven clarification rather than filler.

Current submission stage:

`NMI-P3 COMPLETE -> NMI-P4 REVIEWER ATTACK`.

Canonical P3 files:

- `docs/submission/nmi/NMI_P3_Manuscript_Status_v0.1.md`
- `configs/nmi_submission_contract_v1.2.json`
- `manifests/nmi_p3_manuscript_2026-09-20_v0_1.json`
- `docs/submission/nmi/NMI_Submission_Track_v1.2.md`
- `theory/change_notes/CN-R-076_nmi_p3_manuscript_v0_1.md`

No new experimental execution or frozen-evidence mutation is authorized.

## NMI-P4 Structural Scout Recall Attack

A frozen-data reviewer attack now calibrates whether structural pre-screening can omit later semantic findings.

Same held-out natural cohort:

- trajectories: **90**;
- structural candidate rows: **2,127**;
- deterministic triage cases: **167**;
- candidate-surface compression: **92.1486%**.

Later full-trajectory R8 supports:

- Dynamic P: **13**;
- Dynamic R: **12**;
- unique P-or-R-supported trajectories: **13**.

Earlier narrow B2 high-risk structural selection:

- P selector captures **4/13 = 30.77%**, misses **69.23%**;
- R selector captures **9/12 = 75.00%**, misses **25.00%**;
- union of B2 structural rules captures **10/13 = 76.92%**, misses **3/13 = 23.08%**.

The three union misses are:

- `v5-xd-software_engineering-fr001-0007`;
- `v5-xd-supply_chain-fr001-0019`;
- `v5-xd-supply_chain-fr001-0029`.

All three remain visible in the broader deterministic triage. Across all 13 later P/R-supported trajectories, selected triage packets preserve post-late-event structural evidence in **13/13**. Therefore the main observed failure is a **narrow selector / semantic-proxy miss**, not demonstrated absence of underlying structural evidence.

Methodological consequence:

> **Structural scouting is a localization layer, not the semantic verdict layer.**

The attack also detected a repository-integrity defect in the committed 141-record R8 gzip. A previously frozen external package was recovered and matches the manifest's compressed and uncompressed SHA-256 values exactly. The old repository object remains immutable; P6 must append a valid recovered canonical copy.

Canonical files:

- `docs/submission/nmi/NMI_P4_Structural_Scout_Recall_Attack_Report_v1.md`
- `results/nmi_p4_structural_scout_recall_calibration_v0_2/summary.json`
- `docs/submission/nmi/NMI_Reviewer_Attack_Matrix_v1.1.md`
- `manifests/nmi_p4_structural_scout_recall_attack_2026-09-20_v0_2.json`
- `theory/change_notes/CN-R-078_nmi_p4_structural_scout_recall_calibration.md`

These percentages are conditional calibration values for the frozen selector against later R8 full-trajectory adjudication; they are **not CPR prevalence estimates**.

## NMI-P4 Foundational Attack Expansion

P4 now separates ordinary reviewer attacks from **foundational attacks** that test whether the method or research object survives deeper assumption changes.

### Foundational Attack 01 — structural omission

Frozen held-out calibration:

- B2 union structural capture: **10/13 = 76.92%**;
- conditional miss: **23.08%**;
- broader post-late structural evidence-preservation proxy: **13/13**.

Conclusion:

> **Structural scouting is a localization layer, not the semantic verdict layer.**

### Foundational Attack 02 — future model capability absorption

The paper no longer relies on a claim that today's failure manifestations must persist as models improve.

The hardened boundary is:

> **Model capability is not identical to external evidence, authorization, provenance, validity, re-entry permission or target-system write authority.**

A future consolidated foundation-model system may absorb today's external monitor implementation. That changes protocol placement, not necessarily the independently governed system boundaries through which reality, authority and state are exchanged.

Canonical formulation:

> **Protocol location can change; boundary integrity does not disappear merely because model capability increases.**

The linked engineering outlook is:

`Process Reality Monitor -> semantic lineage / affected closure -> Repair Authority Gate -> bounded Repair Agent -> selective reopen/recompute -> re-entry watch`.

The monitor does not automatically receive broad execution authority, and the repair agent is bounded to the target lineage, affected closure and authorized operation.

Forward P4 files:

- `docs/submission/nmi/NMI_Manuscript_v0.3.md`
- `docs/submission/nmi/NMI_P4_Capability_Absorption_System_Boundary_Attack_v1.md`
- `docs/submission/nmi/NMI_Reviewer_Attack_Matrix_v1.2.md`
- `docs/submission/nmi/NMI_P4_Reviewer_Attack_Status_v0.2.md`
- `configs/nmi_submission_contract_v1.4.json`
- `theory/change_notes/CN-R-080_nmi_p4_foundational_attack_02_monitor_repair_outlook.md`

Inter-System Process Reality remains an **outlook**, not an experimentally established universal generalization.

## NMI-P4 RA03 Semantic Subjectivity / Post-hoc Attack

P4 now explicitly treats the canonical R8 trajectory-first audit as **retrospective mechanism analysis**, not preregistered confirmation.

Chronology:

- held-out 90 natural trajectories completed first;
- deterministic triage was frozen after subject generation and was prohibited from assigning C/P/R verdicts;
- canonical R8 v0.5 trajectory-first semantics was finalized later;
- the combined R8 audit was then frozen.

The attack therefore retains a real limitation:

> **semantic reviewer dependence and post-generation rubric evolution remain.**

At the same time, the strongest cherry-picking interpretation is constrained because:

- the complete 90-trajectory held-out natural cohort is reviewed;
- subject trajectories were not outcome-conditionally regenerated;
- legacy narrow-window analyses remain immutable;
- healthy, NOT_ESTABLISHED, unresolved and censor-aware outcomes remain admissible.

Paper claim mode:

> **RETROSPECTIVE_MECHANISM_EVIDENCE**

not:

> preregistered prevalence confirmation.

Canonical files:

- `docs/submission/nmi/NMI_Manuscript_v0.4.md`
- `docs/submission/nmi/NMI_P4_Semantic_Subjectivity_Posthoc_Attack_Report_v1.md`
- `docs/submission/nmi/NMI_Reviewer_Attack_Matrix_v1.3.md`
- `docs/submission/nmi/NMI_P4_Reviewer_Attack_Status_v0.3.md`
- `configs/nmi_submission_contract_v1.5.json`
- `theory/change_notes/CN-R-081_nmi_p4_semantic_subjectivity_posthoc_attack.md`

## NMI-P4 RA04 Propagation / Failure-Taxonomy Reduction

P4 now explicitly tests whether Process Reality collapses into ordinary information propagation, collaboration/activity, reopening or persistence.

Frozen reduction guards:

- functional semantic continuation is observed in **9/9** reviewed e-commerce discovery-history trajectories, but continuation is broader than Dynamic C;
- an earlier first-new-Agent P proxy captured only **4/13** later P-supported trajectories;
- reopening/recomputation without a generated C/P event is not Dynamic R;
- in canonical R5, **25/29** persistence cases are better explained by ordinary/healthy alternatives, while **4/29** show stronger case-level structures.

Canonical non-equivalences:

> **propagation != authority migration**

> **collaboration/activity != scope-permission expansion**

> **retrieval/reopen != retrospective-generative permission**

> **persistence != System Inertia**

The paper does not claim to replace failure-taxonomy, provenance, memory or propagation research. It frames Process Reality as an execution-level integrity object connecting permission change to functional lineage, perturbation and localized repair.

Canonical files:

- `docs/submission/nmi/NMI_Manuscript_v0.5.md`
- `docs/submission/nmi/NMI_P4_Propagation_Failure_Taxonomy_Reduction_Attack_v1.md`
- `docs/submission/nmi/NMI_Reviewer_Attack_Matrix_v1.4.md`
- `docs/submission/nmi/NMI_P4_Reviewer_Attack_Status_v0.4.md`
- `configs/nmi_submission_contract_v1.6.json`
- `theory/change_notes/CN-R-082_nmi_p4_propagation_taxonomy_reduction_attack.md`

## NMI-P4 RA05 R5 Causal Boundary

P4 now explicitly bounds what the canonical one-shot R5 intervention can support.

Canonical geometry per selected case:

- one frozen natural reference N0;
- one R5-I intervention continuation;
- zero newly sampled natural controls;
- one canonical replicate;
- zero matched synthetic controls.

The operator is a one-shot next-reader runtime transition:

`fact -> unconfirmed`

with no persistent shared-state mutation and no automatic reinjection.

Canonical interpretation:

> **R5 is a localized intervention-response probe, not a treatment-effect estimator.**

R5 supports controlled local authority exposure and the realized downstream response under that exposure. It does not establish unique causality, an average treatment effect, a universal direction or a treatment probability.

R6 then distinguishes semantic ancestry; R7 adds a separate lineage-level repair/recompute intervention. The cross-stage chain is mechanism triangulation, not randomized causal identification.

Frozen mechanism counts retained:

- canonical R5/R6 cases: **29**;
- stronger System Inertia candidates: **4/29**;
- ordinary/healthy/re-anchored alternatives: **25/29**;
- unique R5 causality established: **0/29**.

Canonical files:

- `docs/submission/nmi/NMI_Manuscript_v0.6.md`
- `docs/submission/nmi/NMI_P4_R5_Causal_Boundary_Attack_v1.md`
- `docs/submission/nmi/NMI_Reviewer_Attack_Matrix_v1.5.md`
- `docs/submission/nmi/NMI_P4_Reviewer_Attack_Status_v0.5.md`
- `configs/nmi_submission_contract_v1.7.json`
- `theory/change_notes/CN-R-083_nmi_p4_r5_causal_boundary_attack.md`


## NMI-P6 Reproducibility and Release Freeze

P6 is complete.

The malformed historical 141-record R8 gzip remains immutable for auditability, while the verified canonical recovery is appended at:

`results/r8_trajectory_first_second_audit_recovered_v0_2/trajectory_second_audit_records.jsonl.gz`

Recovery identity:

- compressed SHA-256: `d8e51328f23ff6619fef5dce37f5768de319d16c3be0e7b478d27c7b614d9957`;
- uncompressed SHA-256: `f4b1ee053d47fb3fe5b681831acd37469549af0f741660b81e28fb0df54f3e61`;
- records: 141.

Submission state:

`NMI_P6_COMPLETE_HANDOFF_TO_P7`

Next gate:

`NMI_P7_FINAL_EDITORIAL_AND_FORMAT_COMPLIANCE`.

No new subject/provider/evaluator execution or semantic adjudication was used for P6.


## NMI-P7 Editorial and Format Compliance

P7 is complete.

Submission-facing package:

- `docs/submission/nmi/NMI_Manuscript_v0.14.md`
- `docs/submission/nmi/NMI_Cover_Letter_v0.2.md`
- `docs/submission/nmi/NMI_Supplementary_Information_v0.2.md`

Current editorial counts:

- abstract: 147 / 150 words;
- main text before Methods: 2,942 / 3,500 words;
- main figures: 5 / 6;
- references: 12.

Repository-internal status metadata has been removed from the clean manuscript. Author identity, affiliation, correspondence, declarations and any real public archive identifier remain human-supplied P8 fields and are not guessed.

Submission state:

`NMI_P7_COMPLETE_HANDOFF_TO_P8`

Next gate:

`NMI_P8_PRE_SUBMISSION_REVALIDATION_AND_EXPORT`.

No new subject/provider/evaluator execution, semantic adjudication or evidence mutation was used for P7.


## NMI-P8 Pre-Submission Revalidation

P8 live journal-rule revalidation is complete.

The current Nature Machine Intelligence Article limits remain compatible with the frozen manuscript:

- abstract: 147 / 150 words;
- main text before Methods: 2,942 / 3,500 words;
- main figures: 5 / 6;
- references: 12.

Current submission state:

`NMI_P8_AUTOMATED_PREFLIGHT_COMPLETE_WAITING_HUMAN_METADATA`

Supplementary Information v0.3 removes planning-only supplementary-figure promises, and 5/5 main figure assets are inventoried.

Final portal-ready export is intentionally blocked until the author supplies verified submission metadata and selects standard vs double-anonymized peer review.

Next gate: `NMI_P8H_METADATA_BIND_AND_FINAL_EXPORT`.

No author identity, affiliation, correspondence data, competing-interest declaration or archive identifier is inferred from repository/account data.

No experiment, semantic adjudication, evidence mutation or theory expansion was used for P8 revalidation.


## NMI-P8H.1 Public Repository Release Sync

The research repository is now public and the final submission package has been synchronized to that release state.

Public repository:

`https://github.com/yu5-520/reality-bias-benchmark`

Final manuscript source:

- `docs/submission/nmi/NMI_Manuscript_v0.16_PUBLIC.md`

Release-sync changes:

- Data Availability points directly to the public repository;
- Code Availability points directly to the public repository;
- obsolete private / controlled-review-access wording is removed;
- no immutable archive DOI is claimed until a real archival release exists.

Final re-export workflow:

`35564932403` — **SUCCESS**

DOCX and PDF visual QA both passed.

Submission state:

`NMI_P8H_1_PUBLIC_RELEASE_SYNC_COMPLETE_PORTAL_READY`

Next action:

`NMI_PORTAL_UPLOAD`.

No experiment, theory expansion, semantic adjudication or raw-evidence mutation was used for the release sync.
