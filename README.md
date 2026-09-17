# reality-bias-benchmark

Research repository for the Reality Bias research program and first-paper **Process Reality** mechanism study.

Historical plans, frozen traces, reports, reviewer outputs and manifests remain append-only. Forward documents are versioned rather than silently rewriting prior evidence.

## Current forward stack

- **[R Plan v4.5](docs/R_Plan_v4.5.md)** — R5 as the bounded local probe; R6 as full System Inertia Identification; R7 as localized structural risk control/recovery.
- **[Theory Contract v0.9](theory/theory_contract_v0.9.md)** — Reality Authority, carriers, inherited system inertia, natural variability, specificity and localized recovery.
- **[Measurement Plan v4.5](docs/system_behavior_measurement_plan_v4.5.md)** — separates local response, carrier evidence, natural baseline, intervention-related inertia and target specificity.
- **[R6 Identification Protocol v0.3](docs/R6_inertia_identification_protocol_v0.3.md)** — R6-A natural baseline, R6-B carrier identification, R6-C intervention-related inertia, R6-D target specificity.
- **[Specificity Protocol v0.3](docs/R5_R6_specificity_protocol_v0.3.md)** — S0/S1/S2 as the R6-D specificity design.
- **[R7 Control Protocol v0.4](docs/R7_structural_inertia_control_protocol_v0.4.md)** — C1 free continuation, C2 persistent field, C3 ALR localized recovery.
- **[ALR Contract v0.3](docs/ALR_authority_localized_recovery_contract_v0.3.md)** — Authority-Localized Recovery with affected-closure and revision-lineage requirements.
- **[Process Integrity Engineering Profile v0.1](docs/R7_process_integrity_engineering_profile_v0.1.md)** — lightweight, pluggable, real-time, content-addressed runtime integrity layer.
- **[Evidence Status Addendum v0.1](docs/evidence_status_addendum_v0.1.md)** — explicit current support/unresolved boundaries for local response, inertia, specificity, CPR and R7.
- **[First-Paper Scope v4.5](docs/first_paper_v4.5_scope.md)** — phenomenon -> mechanism -> identification -> localized solution -> semantic closure.
- **[Report Standard v1.2](docs/reporting/process_reality_report_standard_v1_2.md)** and **[Template v1.2](schemas/process_reality_report_template_v1_2.json)** — reporting grammar for R6 identification and R7 localized recovery.

Repository updates do **not** authorize paid provider calls, paid evaluator calls or CPR adjudication.

## Core research position

The primary object is the realized multi-Agent process rather than terminal correctness alone.

> **Outcome Validity != Process Reality Fidelity**

A run may end at a similar terminal decision while its process history, authority transitions, carrier lineage and inherited structure differ materially.

## Forward research geometry

```text
Natural multi-Agent process
  -> R2: natural Jump emergence
  -> R3: inheritance / propagation structure
  -> R4: retrospective / challenge / return dynamics
  -> R5: one bounded local authority-withdrawal probe
  -> R6: System Inertia Identification
       |- R6-A natural inertia baseline
       |- R6-B carrier / inheritance identification
       |- R6-C intervention-related post-consumption inertia
       `- R6-D target specificity (S0/S1/S2)
  -> R7: localized structural risk control / recovery
  -> R8: CPR semantic adjudication and evidence freeze
  -> R9: external robustness / replication
```

The compact logic is:

> **R5 perturbs. R6 identifies. R7 localizes and repairs. R8 adjudicates semantics.**

## R5 — bounded local probe

The canonical family withdraws acquired factual authority once, e.g.:

```text
fact -> unconfirmed
```

R5 must not provide an opposite fact, replacement conclusion, desired action, desired terminal answer, Agent identity change, topology prescription, persistent experiment-origin mutation or reinjection.

R5 primarily establishes **local perturbability/direct path response** where supported. It does not alone prove long-range inertia change, condition effect, target specificity, CPR identity or successful recovery.

## R6 — System Inertia Identification

R6 is now the main mechanism-identification layer.

### R6-A — Natural Inertia Baseline

Repeated natural continuations estimate how much the system already varies without a new perturbation.

Large natural variation is a measurement object, not merely a limitation.

### R6-B — Carrier / Inheritance Identification

A claimed inertia chain should identify what carried prior state forward.

Carrier evidence levels:

```text
REACHABLE
  -> DELIVERED / READ
  -> ADOPTED
  -> INHERITED
  -> PROPAGATED
```

Graph reachability alone is not semantic adoption.

### R6-C — Intervention-Related Inertia Transition

The direct response window is separated from the post-consumption window.

A single A/B trajectory difference is insufficient when natural A/A continuations already diverge strongly. Intervention-related inertia must be interpreted against a frozen natural-variability/process-distance reference.

Natural early termination is **right-censoring**, not proof of zero inertia or permanent extinction.

### R6-D — Target Specificity

The S triad is an internal R6 design:

- `S0_NATURAL_REFERENCE`
- `S1_MATCHED_OR_ORDINARY_FACTUAL_INFORMATION_DOWNGRADE`
- `S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL`

Contrasts:

- `S1 - S0` — generic uncertainty response;
- `S2 - S0` — total J0-targeted response;
- `S2 - S1` — **primary target-specificity contrast**.

S1 is not required to have zero effect.

## Exact-source atomic specificity

The frozen `after_turn:8` parent contains only one non-initial top-level `shared_state_metadata` item with status `fact`: `inventory_stockout_assessment_v1`.

Therefore the prospective specificity design uses atomic prompt-visible facts rather than inventing a second top-level fact field.

Frozen prospective targets:

- **S1:** `public_context.products.C.gross_margin_pct = 35`
- **S2:** `shared_state.inventory_stockout_assessment_v1.A.preliminary_stock = 1520`

The S2 signal originated as `preliminary_unreconciled` and later entered a state container carrying `fact` authority at J0.

S1/S2 use the same minimal operator:

`ONE_SHOT_TARGET_SCOPED_EPISTEMIC_STATUS_ANNOTATION`

The original values remain unchanged; only the target locator differs.

Relevant artifacts:

- `docs/R5_R6_specificity_source_audit_2026-09-17.md`
- `configs/r5r6_specificity_field_selection_contract_v0.2.json`
- `configs/r5r6_specificity_exact_source_binding_v0.2.json`
- `manifests/r5r6_specificity_s1_selection_2026-09-17_v0_2.json`
- `arena/r5r6_specificity_atomic_v0_2.py`
- `arena/r5r6_specificity_atomic_preflight_v0_2.py`

## CPR remains separate

Structural change does not automatically establish Process Reality bias.

- `fact` label alone != C;
- one extra Agent/tool call alone != P;
- same-key recurrence alone != R.

CPR remains an R8 append-only semantic adjudication layer after structural evidence is frozen.

## R7 — localized structural risk control

R7 uses the independent `C` namespace:

- **C1** — One-Shot Free Continuation;
- **C2** — Persistent Field Propagation;
- **C3** — ALR Authority-Localized Recovery.

R7 should preferably consume an **R6-identified risk-bearing carrier or affected closure**, rather than treating every path difference as a repair target.

Success requires both:

1. risk-bearing inertia reduction/localization; and
2. preservation of unaffected nodes, fields, branches, Agent participation and unrelated path diversity.

Whole-system suppression is not equivalent to localized recovery.

## R7 engineering implication — Process Integrity Protocol

The scientific mechanism motivates a runtime engineering layer with three practical capabilities:

> **Monitor -> Scout/Localize -> Point Repair**

Desired properties:

- lightweight;
- pluggable;
- non-invasive/passive by default;
- protocol-agnostic;
- real-time;
- content-addressed;
- lineage-aware;
- localized in repair scope;
- auditable/reversible.

It should integrate beside existing Agent/MCP/A2A/workflow systems rather than replace them.

Minimal event surface:

- `MessageEvent`
- `StateEvent`
- `InvocationEvent`
- `EvidenceSourceEvent`
- `RevisionEvent`

Recommended runtime identities:

- `EventHash`
- `MessageHash`
- `StateHash`
- `FieldHash`
- `SourceHash`
- `InvocationHash`
- `RevisionHash`
- `ClosureHash`

The practical lifecycle is:

```text
Observe
  -> content-address
  -> reconstruct lineage
  -> detect / localize carrier
  -> compute affected closure
  -> point repair if explicitly authorized
  -> resume free execution
  -> verify old/new lineage and re-entry
```

Passive observation must not become a new supervisor that prescribes the topology it claims to observe.

Machine-readable engineering interfaces:

- `configs/r7_process_integrity_engineering_contract_v0.1.json`
- `schemas/process_integrity_event_v0.1.schema.json`
- `schemas/process_integrity_lineage_record_v0.1.schema.json`

## Current evidence status

Current frozen R5-MID evidence supports or exposes:

- natural J0;
- one-shot intervention integrity;
- direct/local structural response;
- natural downstream inertia candidates, especially A2;
- large natural variability across repeated natural continuations;
- matched downstream structural differences;
- similar core terminal decisions despite process differences.

Still unresolved/prospective:

- intervention-related long-range inertia effect beyond natural variability;
- repeatable carrier-mediated condition difference;
- S2 vs S1 target specificity;
- semantic C/P/R identity;
- R7 scientific localized-recovery efficacy.

See **[Evidence Status Addendum v0.1](docs/evidence_status_addendum_v0.1.md)** for the claim matrix.

## Evidence lifecycle

```text
prepare / freeze protocol
-> scientific subject run only with explicit authorization
-> freeze raw evidence
-> integrity validation
-> deterministic structural derivation
-> R6 identification
-> optional R7 structural-control experiment
-> bounded semantic review packets
-> append-only R8 adjudication
-> paper-level evidence freeze
```

Preferred architecture:

> **immutable evidence core + append-only interpretation layers**

## Reporting

Forward publication reports use:

- **[Process Reality Report Standard v1.2](docs/reporting/process_reality_report_standard_v1_2.md)**
- **[Process Reality Report Template v1.2](schemas/process_reality_report_template_v1_2.json)**

Historical standards remain valid for their frozen reports:

- v1.1: R6 factual/specificity-forward reporting layer;
- v1.0: finalized R5-MID v3 report bundle.

The reporting chain remains:

`frozen raw trace -> source-backed derivation -> bounded report projection`

A report does not authorize reruns, provider calls, semantic promotion or active recovery.
