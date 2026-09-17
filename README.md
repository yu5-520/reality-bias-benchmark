# reality-bias-benchmark

Research repository for the Reality Bias program and first-paper **Process Reality** mechanism study.

Historical evidence remains append-only. Forward methods are versioned rather than silently rewriting frozen evidence or preregistration.

## Current forward layer

The current methodological layer is **v4.5.1**. It does not add a new R stage and does not mutate the frozen R6-D design.

Core forward files:

- `docs/R_Plan_v4.5.1.md`
- `theory/theory_contract_v0.10.md`
- `docs/system_behavior_measurement_plan_v4.5.1.md`
- `docs/R6_inertia_identification_protocol_v0.4.md`
- `docs/R5_R6_specificity_protocol_v0.4.md`
- `docs/R7_structural_inertia_control_protocol_v0.5.md`
- `docs/ALR_authority_localized_recovery_contract_v0.4.md`
- `docs/R7_process_integrity_engineering_profile_v0.2.md`
- `configs/r6/r6d_methodological_interpretation_gate_v0.1.json`
- `manifests/process_reality_v4_5_1_methodological_closure_2026-09-17.json`
- `docs/reporting/process_reality_report_standard_v1_3.md`

The exact R6-D pre-execution design remains frozen at:

`d8783a9c3e0a264c3119ee72e63db9b61d51f0d633ff6dde66068751c31701de`

## Research geometry

```text
R5 — perturb minimally
  -> R6 — identify what persisted/changed and why
  -> R7 — localize and repair an evidence-supported risk-bearing closure
  -> R8 — adjudicate CPR semantics
```

No v4.5.1 update adds an R stage.

## R6 — evidence pivot

R6 now explicitly separates **normal inheritance** from **System Inertia**.

Normal coordination may legitimately carry information forward. An inertia candidate requires evidence that a prior epistemic status, commitment, constraint or action tendency continues to shape later process options, transition propensity or state after the originating event has passed.

Carrier evidence should stop at the highest supported level:

`reachable -> delivered/read -> referenced -> adopted -> inherited -> propagated`

Reachability/hash ancestry is not semantic adoption.

## Three comparison domains

R6 comparison is reported as separate vectors:

1. **Structural** — topology, actor sequence, reach/depth, branch/merge/re-entry, path family, reconvergence.
2. **Information inheritance** — delivery/read, reference, adoption/rejection, inherited state/action, propagation, source replacement.
3. **Epistemic authority** — downstream authority use, response to downgrade, re-confirmation, authority reconstruction and independent new evidence.

No post-hoc total complexity score is used by default.

## R6-D specificity

Frozen conditions remain:

- `S0_NATURAL_REFERENCE`
- `S1_MATCHED_OR_ORDINARY_FACTUAL_INFORMATION_DOWNGRADE`
- `S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL`

Frozen targets remain:

- S1 `public_context.products.C.gross_margin_pct = 35`
- S2 `shared_state.inventory_stockout_assessment_v1.A.preliminary_stock = 1520`

S1/S2 use the same atomic one-shot operator, but **mechanical equivalence does not imply target exchangeability**. The targets may differ in relevance, provenance, structural position, downstream opportunity and decision weight.

Therefore the preregistered `S2 - S1` contrast is first reported as:

> **FROZEN_TARGET_RESPONSE_CONTRAST**

A stronger Escape-derived/J0-specific interpretation requires a supported matching argument or later append-only ordinary-fact robustness controls.

The first S1 result may not be replaced after outcomes are observed.

## Conditional scope

The first R6-D batch is conditional on the exact frozen `after_turn:8` historical prefix. Same-parent repeats are repeated realizations, not independent population samples.

## Experiment-origin versus endogenous persistence

The frozen atomic operator still records `persistent_state_mutation=false`.

Forward interpretation is precise:

> the experiment itself does not directly write persistent state.

Agents are still free to create state/messages/invocations after seeing the one-shot annotation. Those endogenous subject changes are scientific observations and possible carrier evidence.

## R7 closure model

R7/ALR now separates three closure objects:

1. `PotentiallyAffectedClosure` — structurally reachable scouting set;
2. `EvidenceSupportedAffectedClosure` — descendants with source-backed dependence evidence;
3. `RepairClosure` — evidence-supported affected nodes plus only mechanically required replay dependencies.

Potential reachability is not automatically the repair set.

Replay-only dependencies must remain labeled as replay dependencies rather than being silently called affected.

## Process Integrity engineering layer

The proposed engineering lifecycle is:

`Observe -> Address -> Trace -> Localize -> Separate Potential/Evidenced Closure -> Point Repair -> Resume -> Verify`

Content hashes provide identity/version/lineage. Relation evidence provides semantic-use/adoption evidence.

Machine-readable interfaces now include:

- `schemas/process_integrity_event_v0.2.schema.json`
- `schemas/process_integrity_relation_evidence_v0.1.schema.json`
- `schemas/process_integrity_lineage_record_v0.2.schema.json`
- `configs/r7_process_integrity_engineering_contract_v0.2.json`

Observation/indexing can be protocol-agnostic through adapters. Active repair remains dependent on native state/replay/reopen/execution interfaces.

## R6-D runtime readiness and gate

The runtime-readiness implementation contains the plan builder, offline smoke path, guarded real runner, raw-evidence freezer and manual scientific workflow.

The real subject workflow now fail-closes through both:

1. the exact frozen design/authorization gate; and
2. `scripts/validate_process_reality_v4_5_1.py` methodological interpretation validation.

No scientific provider call is authorized by repository state alone.

## Current scientific status

Supported/observed so far:

- natural J0;
- one-shot local perturbation response;
- natural downstream inheritance/inertia candidates;
- large natural variation;
- process/terminal-outcome decoupling.

Still prospective/unresolved:

- intervention-related inertia beyond natural variability under repeated comparison;
- stable carrier-mediated condition difference;
- S2 relative to S1 frozen-target contrast from real scientific execution;
- stronger Escape-derived specificity;
- semantic C/P/R adjudication;
- R7 localized-recovery efficacy.

CPR remains `NOT_ADJUDICATED`.

## Validation

Offline method synchronization:

```bash
python scripts/validate_process_reality_v4_5_1.py
python scripts/validate_process_reality_v4_5.py
python scripts/validate_r6d_specificity_exact_plan_v0_1.py
python -m unittest discover arena/tests -v
```

The v4.5.1 validator explicitly checks that the frozen R6-D design hash has not changed.
