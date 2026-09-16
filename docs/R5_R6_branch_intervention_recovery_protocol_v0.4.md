# R5 / R6 Branch Intervention & Recovery Protocol v0.4

Date: 2026-09-16  
Status: FORWARD CANDIDATE / MULTI-POSITION CAUSAL LAYER / ZERO NEW PROVIDER CALLS  
Supersedes for forward work: `docs/R5_R6_branch_intervention_recovery_protocol_v0.3.md`

Depends on:

- `docs/R_Plan_v4.0.md`
- `theory/theory_contract_v0.4.md`
- `docs/system_behavior_measurement_plan_v4.md`
- `configs/experimental_variable_registry_v0.1.json`
- `configs/measurement_boundary_registry_v0.1.json`

Historical v0.1-v0.3 protocol files and all frozen evidence remain unchanged.

## 1. Core causal form

The preferred branch form remains:

```text
same frozen parent
  ├── control continuation
  └── exactly one preregistered manipulation
        → continuation
        → freeze raw evidence
        → derive behavior/state-transition measurements
        → semantic review later where needed
```

v0.4 generalizes the scientific position of the intervention. It does not replace the existing Phase-A / Phase-B execution guards.

## 2. Intervention positions

### 2.1 PRE — Formation Manipulation

Purpose: manipulate an antecedent before the candidate Jump is realized.

Examples:

- goal conflict level;
- evidence conflict level;
- context competition;
- information load;
- authority mismatch;
- alternative path availability.

Primary outcomes:

- Jump incidence / hazard;
- first-Jump location;
- Jump type distribution.

PRE experiments do not claim to directly measure Tension or Escape Propensity.

### 2.2 MID — Realization / Containment Manipulation

Purpose: manipulate the conversion, propagation or operationalization of Jump-derived state.

Examples:

- epistemic status downgrade;
- authority edge block;
- routing edge block;
- commit gate;
- shared-state visibility;
- proposal/realization separation.

Primary outcomes:

- propagation depth;
- operational-boundary crossings;
- affected descendants / actors;
- penetration criteria;
- post-Jump persistence / inertia.

The existing `EPISTEMIC_STATUS_DOWNGRADE_TO_PROVISIONAL` experiment remains valid as the first MID intervention family.

### 2.3 POST — Stabilization Manipulation

Purpose: manipulate the system after a deviation has propagated or obtained operational force.

Examples:

- challenge timing;
- provenance restoration;
- correction permission;
- reopen policy;
- review/verification timing.

Primary outcomes:

- persistence;
- retrospective outcome;
- residual descendants;
- recovery distance/cost;
- recurrence/regeneration.

## 3. Anchor classes

Forward branch planning distinguishes:

- `ANTECEDENT_ANCHOR`;
- `TRANSITION_ANCHOR`;
- `PENETRATION_ANCHOR`;
- `CHALLENGE_RECOVERY_ANCHOR`.

All branch anchors must be source-backed and restorable.

For the current Arena scheduler, a continuation anchor must be nonterminal and contain pending executable work. Therefore:

`nonterminal snapshot ≠ automatically branchable snapshot`

Historical anchor selectors remain versioned and preserved.

## 4. Current MID Phase-A selector

The forward existing selector is:

`arena/config/r5r6_anchor_rule_v0.2.json`

It selects the lowest-event-index replayable `HIGH_CERTAINTY_STATE_WRITE_CANDIDATE` satisfying the current branchability rule, including pending continuation work.

This selector is reclassified as a concrete `TRANSITION_ANCHOR` selector for the MID epistemic-status experiment.

It does not establish:

- semantic C;
- Jump truth;
- unauthorized promotion;
- Authority Penetration;
- causal importance.

## 5. Existing MID intervention

The first implemented MID intervention remains:

`EPISTEMIC_STATUS_DOWNGRADE_TO_PROVISIONAL`

It changes only:

`shared_state_metadata[selected_key].status`

from a high-certainty status to `provisional`, while preserving all other branch-visible runtime state except the derived state hash.

Existing implementation remains authoritative for this specific family:

- `arena/branch_plan.py`
- `arena/run_branch_real.py`
- `arena/derive_branch_measurements.py`
- `.github/workflows/r5r6-frozen-parent-branch-real.yml`
- `schemas/r5r6_branch_execution_plan_v0.1.schema.json`
- `schemas/r5r6_branch_execution_manifest_row_v0.1.schema.json`

v0.4 does not silently broaden these files to other intervention families.

## 6. Variable binding

Every forward confirmatory manipulation must bind one entry in:

`configs/experimental_variable_registry_v0.1.json`

The execution plan must freeze, where applicable:

- `variable_id`;
- registry version/hash;
- intervention stage;
- target boundary;
- control level;
- manipulation level;
- held-constant fields;
- source requirements;
- intervention hash。

Exploratory manipulations not yet in the registry may be run offline but must not be mislabeled confirmatory.

## 7. Boundary binding

Every manipulated or measured node must bind one registered boundary from:

`configs/measurement_boundary_registry_v0.1.json`

This separates:

- where the experiment manipulates the system;
- what behavior occurs at that location;
- what semantic label is later assigned.

## 8. Behavior-first evidence

Branch evidence must prioritize:

`Behavior Event → State Transition → downstream lineage`

Raw model inputs/outputs remain frozen source evidence, but full reasoning text is not the primary measurement unit.

New forward behavior records use:

- `schemas/behavior_event_v0.1.schema.json`
- `schemas/system_trajectory_measurement_v4.schema.json`

Semantic C/P/R fields remain `NOT_ADJUDICATED` unless separately reviewed.

## 9. R2 / R3 / R4 extraction from branch evidence

One frozen branch trajectory may simultaneously support:

- R2 Jump/behavior candidate extraction;
- R3 propagation/penetration/inertia extraction;
- R4 retrospective window extraction.

No automatic subject rerun is required to create separate R2/R3/R4 datasets.

## 10. Recovery

R6 remains a distinct research role even when POST manipulations exist.

Recovery experiments compare restoration from different distances:

- pre-Jump checkpoint;
- post-Jump pre-penetration;
- shallow penetration;
- multi-descendant state;
- post-challenge retrospective state.

Recovery metrics may include:

- residual descendants;
- recurrence/regeneration;
- distance to last valid state;
- calls/tokens/turns;
- provenance reconstruction fidelity;
- remaining operational contamination.

## 11. Two-phase paid boundary remains active

For the currently implemented MID status-downgrade path:

### Phase A

baseline subject run → snapshots → structural selector → evidence freeze.

Exact authorization phrase remains:

`CALL_REAL_R5R6_BASELINE_API`

### Phase B

same frozen parent → control/intervention branches → evidence freeze → offline measurement.

Exact authorization phrase remains:

`CALL_REAL_R5R6_BRANCH_API`

Phase-A authorization never authorizes Phase B.

Repository updates do not satisfy either paid gate.

## 12. First-paper scope

The first paper should not attempt the full PRE/MID/POST matrix.

Priority remains:

- establish Jump and downstream system dynamics;
- run one or more narrow MID containment interventions;
- run recovery contrasts;
- keep Tension as an upstream explanatory construct and future PRE-experiment entry point.

## 13. Stop / audit conditions

Stop interpretation if any of the following occurs:

- parent/start hash mismatch;
- non-branchable parent;
- intervention changes more than the frozen variable contract allows;
- variable or boundary registry mismatch;
- provider/model/code mismatch;
- branch outcomes influence anchor selection;
- provider failure counted as negative evidence;
- structural behavior difference presented as semantic C/P/R without review;
- tension or Escape Propensity presented as directly observed internal state.

## 14. Execution boundary

This protocol update authorizes offline repository and instrumentation work only.

No new paid subject or Reviewer call is authorized by this document.