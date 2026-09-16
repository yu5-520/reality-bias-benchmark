# CN-R-054 — System-Behavior Measurement Reframe

Date: 2026-09-16  
Status: FORWARD THEORY / MEASUREMENT CHANGE NOTE

## Trigger

Trajectory Dynamics v3 successfully separated latent Escape Propensity from observable Jump and moved the program away from sentence-level CPR classification. Subsequent design analysis exposed a remaining ambiguity: the program still described the state transition as the unit of analysis without explicitly separating the system trajectory, measurement location, primary observable and semantic annotation layers.

At the same time, Escape Propensity remained theoretically upstream of Jump but lacked a clear manipulable antecedent family. This risked making Escape sound like an ungrounded latent property or encouraging expensive post-hoc interpretation of full model reasoning traces.

## Decision

Forward work adopts a system-behavior measurement hierarchy:

- **System Trajectory** = experimental / analysis unit;
- **Node / Boundary** = measurement location;
- **Behavior / State Transition** = primary observable;
- **C/P/R and Authority semantics** = post-hoc annotation layer.

The forward mechanism chain becomes:

`controllable antecedents`
`→ Tension`
`→ latent Escape Propensity`
`→ observable Jump`
`→ propagation / penetration / inertia`
`→ retrospective dynamics / recovery`

Tension is introduced only as an upstream explanatory construct. The first paper does not claim direct measurement of Tension or hidden reasoning.

## Experimental consequence

The program can manipulate upstream variables such as goal conflict, evidence conflict, context competition, authority mismatch and information load without requiring full chain-of-thought reconstruction.

R5 is generalized from a single status intervention into a multi-position causal layer:

- PRE — formation antecedents;
- MID — realization / containment;
- POST — stabilization.

The existing high-certainty-status → provisional intervention remains preserved as the first implemented MID family.

## R2–R4 consequence

R2, R3 and R4 are formally treated as simultaneous observation views over the same frozen system trajectory rather than mandatory sequential subject experiments.

One frozen run may support:

- R2 Jump/behavior extraction;
- R3 propagation/penetration/inertia extraction;
- R4 retrospective-window extraction;

with semantic review performed later.

## New forward artifacts

- `docs/R_Plan_v4.0.md`
- `theory/theory_contract_v0.4.md`
- `docs/system_behavior_measurement_plan_v4.md`
- `configs/experimental_variable_registry_v0.1.json`
- `configs/measurement_boundary_registry_v0.1.json`
- `schemas/behavior_event_v0.1.schema.json`
- `schemas/system_trajectory_measurement_v4.schema.json`
- `arena/system_behavior.py`
- `arena/system_behavior_preflight.py`
- `docs/R5_R6_branch_intervention_recovery_protocol_v0.4.md`
- `docs/R5_R6_real_run_freeze_template_v0.2.md`

## Non-retroactivity

This note does not rewrite:

- R Plan v3.2;
- Theory Contract v0.3;
- Measurement v3;
- Batch001;
- historical CPR Reviewer results;
- historical branch manifests/protocols;
- any previously frozen subject evidence.

New terminology must not be backdated as if it had been preregistered for historical runs.

## Paid execution boundary

This theory/measurement update authorizes no paid provider calls. Existing exact authorization phrases and spending gates remain unchanged.