# reality-bias-benchmark

Research repository for the Reality Bias research program and first-paper mechanism study.

## Current forward research layer

The forward first-paper implementation now uses [Mechanism refinement v0.2](docs/first_paper_mechanism_contract_v0.2.md): outcome-blind source-anchor classification, task/activity diagnostics, parent-aware descriptive estimates and optional bounded mechanism reviews. The R5-MID intervention and structural endpoint remain unchanged. v0.1 analysis is preserved historically; its pair-level bootstrap is not the forward uncertainty rule. R9 remains supplementary.

The current forward planning layer is:

- **[R Plan v4.0](docs/R_Plan_v4.0.md)** — system-behavior research program;
- **[Theory Contract v0.4](theory/theory_contract_v0.4.md)** — System–Node–Behavior–Transition–Tension–Escape–Jump–CPR ontology;
- **[System Behavior Measurement Plan v4](docs/system_behavior_measurement_plan_v4.md)** — behavior-first measurement contract;
- **[CN-R-054](theory/change_notes/CN-R-054_system_behavior_measurement_reframe.md)** — records the v3.2 → v4 coordinate change.

R Plan v3.2, Theory Contract v0.3 and Trajectory Measurement v3 remain preserved as the preceding trajectory-dynamics layer and are not rewritten.

## Core research position

The primary research object is no longer a model output sentence or isolated CPR label. The forward measurement hierarchy is:

```text
System Trajectory        = experimental / analysis unit
Node / Boundary          = measurement location
Behavior / Transition    = primary observable
C / P / R                = post-hoc semantic annotation layer
```

The forward mechanism chain is:

```text
controllable antecedents X_pre
        ↓
structural / interaction Tension
        ↓
latent Escape Propensity
        ↓ realization
observable Jump
        ↓
first-order C/P state-deviation candidate
        ↓
adoption / commit
        ↓
propagation / Authority Penetration / inherited inertia
        ↓
challenge / correction / retrospective operation
        ↓
second-order R dynamics or recovery
        ↓
system outcome
```

**Tension and Escape Propensity are theoretical latent constructs.** The repository does not claim to read hidden chain-of-thought, neural state or an internal escape probability. It records behavior and state transitions, and can estimate behavior-level Jump incidence/hazard under repeated frozen conditions.

The default measurement principle is:

> **Behavior first, semantic label second.**

## CPR position

C/P/R remain important but are no longer treated as isolated end labels.

- **C** — first-order epistemic-state deviation;
- **P** — first-order goal/scope/focus deviation;
- **R** — second-order persistence/regeneration/amplification/legitimation/laundering/normalization of an existing C/P-derived deviation.

Normal correction is recovery evidence, not R-positive evidence.

A structural candidate does not automatically establish semantic C/P/R truth.

## R2–R4: simultaneous views over one trajectory

R2, R3 and R4 are not required to be separate sequential subject experiments.

```text
                   ┌─ R2: Behavior / Jump emergence
System Trajectory ├─ R3: Transmission / Penetration / Inertia
                   └─ R4: Retrospective / R dynamics
```

One frozen subject trajectory may support all three structural views, followed by asynchronous semantic review.

## R5–R7: experimental directions

### R5 — Multi-position causal manipulation

R5 now separates:

- **PRE** — manipulate antecedents before Jump realization;
- **MID** — manipulate realization / propagation / containment;
- **POST** — manipulate stabilization after propagation or penetration.

The existing high-certainty-status → provisional branch experiment remains the first implemented **MID** intervention family. It is not the definition of all R5 work.

Forward protocol: [R5/R6 Protocol v0.4](docs/R5_R6_branch_intervention_recovery_protocol_v0.4.md).

### R6 — Recovery / Recurrence

R6 studies recovery from different historical distances and penetration depths, including residual descendants, recurrence, recovery cost and provenance reconstruction.

### R7 — System Structure / Boundary Conditions

R7 treats topology/orchestration as system-level variables, including routing ownership, stage boundaries, context handoff, proposal/commit separation, Agent count and shared-state visibility.

The existing Free Routing vs Structured/System-Owned Routing comparison remains the first R7 condition family.

## Behavior-first instrumentation

Forward machine-readable registries:

- `configs/experimental_variable_registry_v0.1.json`
- `configs/measurement_boundary_registry_v0.1.json`

Forward evidence schemas:

- `schemas/behavior_event_v0.1.schema.json`
- `schemas/system_trajectory_measurement_v4.schema.json`
- `schemas/experimental_variable_registry_v0.1.schema.json`
- `schemas/measurement_boundary_registry_v0.1.schema.json`

Forward implementation:

- `arena/system_behavior.py`
- `arena/system_behavior_preflight.py`
- `arena/tests/test_system_behavior.py`

Offline preflight:

```bash
python -m arena.system_behavior_preflight --outdir results/system_behavior_preflight
```

This produces deterministic engineering-validation artifacts only. It is not scientific subject evidence.

## Experimental control layer

The existing experimental instrument remains active:

```text
Observe → Freeze → Replay deterministic Arena state → Branch → Intervene → Measure
```

Important invariants remain:

- original trajectory is never overwritten by a branch;
- parent state and branch-start state have separate hashes;
- provider hidden state is not claimed replayed;
- semantic Reviewer results cannot rewrite frozen structural evidence;
- failed/censored provider runs are not silently counted as negative evidence.

For the current Arena scheduler:

> **nonterminal snapshot ≠ automatically branchable snapshot**

A continuation anchor must also have pending executable work where required by the runtime.

Forward R5/R6 real-run template: [v0.2](docs/R5_R6_real_run_freeze_template_v0.2.md).

## Current real-run implementation status

### R5/R6 Phase A

Prepared guarded baseline path:

- `arena/config/r5r6_anchor_rule_v0.2.json`
- `arena/anchor_selection.py`
- `arena/build_branch_baseline_manifest.py`
- `arena/run_branch_baseline_real.py`
- `.github/workflows/r5r6-baseline-snapshot-real.yml`

The v0.2 selector requires a replayable structural candidate **and pending continuation work**.

Exact paid authorization phrase:

`CALL_REAL_R5R6_BASELINE_API`

### R5/R6 Phase B

Prepared guarded branch path:

- `arena/branch_plan.py`
- `arena/run_branch_real.py`
- `arena/derive_branch_measurements.py`
- `.github/workflows/r5r6-frozen-parent-branch-real.yml`

Exact paid authorization phrase:

`CALL_REAL_R5R6_BRANCH_API`

Phase-A authorization never authorizes Phase B.

### R7

Prepared Free-vs-Structured comparison infrastructure:

- `arena/structured_routing.py`
- `arena/orchestration_compare.py`
- `arena/orchestration_preflight.py`
- `arena/build_orchestration_manifest.py`
- `arena/run_orchestration_real.py`
- `.github/workflows/r7-orchestration-paired-real.yml`

Exact paid authorization phrase:

`CALL_REAL_R7_API`

No generic repository-update instruction satisfies any paid gate.

## Historical evidence boundary

Historical subject/reviewer evidence remains append-only.

The first formal joint C/P/R collection remains frozen under its original contracts. Evidence batch:

`94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`

Historical Measurement v2, Reviewer-v2 and R9 robustness materials remain historical/supplementary evidence layers. New v4 terminology must not be backdated as if it were preregistered for those runs.

## Evidence-first lifecycle

Default Arena lifecycle:

```text
prepare
→ subject run
→ save raw evidence
→ integrity validation
→ objective statistics
→ machine structural/behavior index
→ export small semantic review windows
→ append independent reviews later
```

A subject run does not automatically call a paid evaluator.

Current objective termination states remain distinct, including natural completion, budget censoring and configured loop-budget completion. Missing historical fields are never semantically reconstructed as if they had been recorded.

## Repository map

- `theory/` — theory contracts, change notes and novelty material.
- `docs/R_Plan_v4.0.md` — current forward research plan.
- `docs/system_behavior_measurement_plan_v4.md` — current behavior-first measurement plan.
- `configs/experimental_variable_registry_v0.1.json` — experimental variable registry.
- `configs/measurement_boundary_registry_v0.1.json` — node/boundary registry.
- `arena/` — subject runtime, evidence capture, branch control, measurements and offline preflights.
- `schemas/` — evidence, branch, behavior, measurement and registry interfaces.
- `reviews/` — append-only semantic-review infrastructure/records.
- `.github/workflows/` — reproducible offline and guarded real-provider entry points.

## Version / non-retroactivity rule

- R Plan v3.2 and earlier remain historical records.
- Theory v0.3 and earlier remain historical contracts.
- Measurement v3 and Measurement v2 remain valid for their original evidence boundaries.
- New deterministic metrics may read old evidence only when required source fields truly exist.
- New v4 behavior evidence requires new versioned subject/intervention records.
- Repository updates do not constitute paid API authorization.
