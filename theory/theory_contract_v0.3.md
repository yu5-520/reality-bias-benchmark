# Reality Bias Research Program
## R0 — Theory Contract v0.3

**Status:** CANONICAL CANDIDATE / TRAJECTORY-DYNAMICS EXTENSION  
**Date:** 2026-09-16  
**Supersedes for forward work:** `theory/theory_contract_v0.2.md`  
**Historical rule:** v0.2 and all evidence/reviewer records produced under it remain append-only and unchanged.

## 0. Scope and scientific boundary

The first paper studies interaction-level Reality Bias in a minimal Multi-Agent environment. It does not claim that every model failure is Reality Bias, that escape is a directly observable neural variable, or that a specific engineering architecture is uniquely correct.

The forward theory separates a latent propensity from observable events:

> **Escape propensity is a theoretical latent tendency for locally plausible probabilistic synthesis to produce a task-relevant state displacement. A Jump is the observable realization of such a displacement in a recorded trajectory.**

The contract therefore studies observable state transitions and their downstream effects. It does **not** claim access to an internal neural "escape probability" or hidden chain of thought.

A behavior-level hazard may be estimated under repeated, frozen conditions:

`h_t = P(J_t = 1 | recorded state/context/goal/authority condition at t)`

This is an experimental abstraction over repeated behavior, not a measurement of an internal model variable.

## 1. Unified trajectory model

The forward mechanism chain is:

`context interaction / probabilistic synthesis`
`→ latent escape propensity`
`→ Jump realization`
`→ first-order state deviation (C and/or P candidate)`
`→ adoption / commit`
`→ propagation / Authority Penetration / inherited inertia`
`→ challenge, correction, or retrospective operation`
`→ second-order R dynamics or recovery`

The ordering after Jump is not assumed to be strictly linear. Propagation, penetration and inertia may be coupled or recursive. The recorded trajectory determines the actual ordering for each case.

The unit of analysis is a state transition inside a trajectory, not merely an output sentence:

`S0 → S1 → ... → St → St' → St+1' ...`

A later step can be locally coherent from `St'` even when the transition `St → St'` was the critical displacement.

## 2. Core objects

### 2.1 Jump

A **Jump** is a recorded transition in which at least one task-relevant state dimension moves outside the previously supported or authorized closure and becomes a candidate for downstream inheritance.

Candidate dimensions include:

- epistemic status or provenance;
- goal scope or goal focus;
- invocation/task graph;
- settled/final/historical state;
- authority-bearing status;
- other explicitly preregistered task-state dimensions.

A structural Jump is not automatically a Reality Bias. Semantic and Authority conditions still require adjudication.

### 2.2 Bias Generation and Bias Realization

**Bias Generation** means that a model produces a beyond-contract proposal, inference, expansion, or retrospective reinterpretation, but that content has not yet obtained system effect.

**Bias Realization** means that the generated content acquires system effect through an authority-bearing state, executable edge, shared state, historical state, or equivalent mechanism.

Therefore:

`reasoning/proposal ≠ operational reality`

and the central transition remains:

`proposal → conversion/commit boundary → authority-bearing state`

### 2.3 Authority-bearing State

A state is **Authority-bearing** when downstream components are mechanically entitled to treat it as an official fact/context, executable action/call, or valid current/historical task state.

An ordinary model utterance is not authority-bearing by default.

### 2.4 Authority Penetration

Authority Penetration is the process by which a claim, goal increment, invocation, or historical reinterpretation progressively acquires operational force without satisfying the required end-to-end Authority condition.

Penetration does not require a dramatic bypass of one explicit permission check. A trajectory may pass several locally valid checks while still violating the global Information, Invocation, or Temporal Authority contract.

Candidate penetration mechanisms include:

- semantic transformation across representations;
- authority inheritance from an upstream local authorization;
- cumulative sub-threshold expansion;
- temporal carry-over after conditions change;
- provenance attenuation or laundering;
- local-pass / global-fail checking;
- aggregation of individually non-authoritative signals;
- role-mediated trust in upstream output.

These are hypotheses/categories for measurement and must not be treated as established empirical frequencies before data support them.

### 2.5 Inherited Inertia

**Inherited inertia** is the persistence effect that appears after a Jump-derived state becomes part of later context, state, goals, evidence, or execution history.

A later Agent may reason correctly relative to the inherited post-Jump state. Inertia therefore concerns path dependence, not merely repeated identical error.

A behavior-level post-Jump persistence statistic may be estimated as a preregistered function such as:

`I(k) = P(descendant state remains Jump-dependent at t+k | J_t) - comparison condition`

The exact estimator must be frozen before use in confirmatory claims.

### 2.6 Recovery

Recovery is the restoration of an authorized and evidence-consistent trajectory after detection or challenge of a Jump-derived state.

Recovery may be evaluated by:

- rollback/reconstruction success;
- residual Jump descendants;
- recurrence/regeneration;
- recovery latency/calls/tokens;
- distance to the last valid state;
- provenance reconstruction fidelity.

## 3. First-order Reality Bias dimensions

### 3.1 Completion Bias (C)

C is a first-order epistemic-state deviation.

C-Generation occurs when missing, uncertain, weakly supported, or provisional information is advanced beyond its authorized epistemic status.

C-Realization occurs when that promotion obtains authority-bearing factual/contextual or execution-relevant status without a valid Information Authority conversion.

Core path:

`uncertain / inferred / predicted → stronger epistemic status → inherited as reality`

Explicitly provisional, non-inheritable inference is not C-Realization.

### 3.2 Perfection Bias (P)

P is a first-order goal/scope/focus deviation.

P-Generation occurs when the system proposes unnecessary or unauthorized expansion of goals, task scope, Agent/tool/stage surface, information surface, or decision focus in pursuit of completeness, robustness, or an idealized solution.

P-Realization occurs when that expansion becomes an effective task purpose, executable graph/scope, or materially shifted decision focus without valid authorization.

Invocation expansion is an important route but is not the entire definition of P.

Core paths include:

`G0 → G0 + ΔG`

and

`same nominal goal set → unauthorized material focus shift`

Necessary decomposition and explicitly authorized scope change are not P.

## 4. Retrospective Bias (R) is second-order

R is not defined by reopening, revision, rework, or correction alone.

> **R is a second-order transformation of an already existing C/P deviation or unresolved C/P-derived state.**

The minimum R structure is:

`prior C/P deviation or unresolved C/P-derived state`
`+ retrospective/challenge/correction opportunity`
`+ persistence, regeneration, amplification, legitimation, laundering, or normalization effect`

Normal correction is therefore an exclusion, not a positive R case.

Candidate R outcomes include:

- **CORRECTION** — the prior deviation is removed or downgraded;
- **PERSISTENCE** — the prior deviation remains effective;
- **REGENERATION** — retrospective processing produces a new C/P deviation;
- **AMPLIFICATION** — effect radius, authority, goal scope, or downstream dependency expands;
- **LAUNDERING** — the deviation is reinterpreted as legitimate/necessary/verified without new sufficient basis;
- **NORMALIZATION** — a laundered state becomes an ordinary premise for later actors.

R-Realization requires a second-order effect on an existing deviation. A valid correction/reopen under policy is not R.

## 5. Authority classes

The v0.2 Authority classes remain active:

- **Information Authority (I):** governs promotion into official fact/context and required provenance.
- **Invocation Authority (V):** governs executable Agent/tool/stage/call graph and bounded dynamic expansion.
- **Temporal Authority (T):** governs reopen, revision, version identity, and historical/task-state mutation.

Authority does not forbid inference, collaboration, or correction. It governs when those operations may acquire system effect.

A legitimate conversion must bind, where applicable:

1. source identity;
2. Authority class;
3. conversion condition;
4. provenance record;
5. current state/version identity when transition semantics require it.

## 6. Structural, semantic and measurement layers

The program maintains three separate layers:

1. **Structural emergence:** recorded events, state transitions, reads, writes, calls, versions, feedback topology and resource dynamics.
2. **Semantic identification:** C/P/R, authorization, semantic adoption, laundering, normalization and decision effect.
3. **Measurement sensitivity:** changes caused by rubric, packet, reviewer, model family, or human annotation.

Reviewer changes cannot rewrite layer 1.

## 7. Experimental organization conditions

Two orchestration families are scientifically relevant without asserting that either is universally safer:

### Emergent / Free Routing

The system receives an overall task and Agents may dynamically decompose work and invoke other Agents within the experiment policy.

Candidate escape expression: path/scope/topology expansion.

### Structured / System-Owned Routing

The overall task remains fixed but stage goals, allowed edges and handoff points are externally defined.

Candidate escape expression: an internal Jump may be inherited and propagated along a stable path.

A fixed topology does not imply fixed semantics:

`Fixed Topology ≠ Fixed Semantic State`

Stage boundaries may contain a deviation through checkpointing, or may formalize/launder it through structured inheritance. This is an empirical question.

## 8. Causal intervention principle

R5 interventions should change one explicit system variable while preserving the frozen pre-intervention history as far as the experimental design permits.

Preferred form:

`same parent state + one preregistered intervention → branched continuation`

Candidate interventions include blocking one Authority route, removing one context source, changing one state status, restricting one edge, or inserting one state-commit check.

A branch must never overwrite the original trajectory.

## 9. Falsifiability

The trajectory theory is weakened if, under preregistered measurements and adequate repeated samples:

- proposed Jump definitions do not produce reproducible structural events;
- post-Jump descendants show no distinguishable persistence/path-dependence from matched comparisons;
- Authority Penetration cannot be operationally separated from simple visibility/propagation;
- R cannot be separated from ordinary correction/rework;
- targeted interruption of a hypothesized dependency does not change the predicted downstream structure;
- recovery dynamics do not differ with distance/commit/lineage conditions in the predicted direction;
- orchestration manipulations do not change any preregistered trajectory-dynamic quantity.

Null findings remain valid evidence and must not be rewritten as positive Reality Bias evidence.

## 10. Evidence and version rule

- Frozen historical subject traces remain historical facts.
- New deterministic metrics may be derived from old traces only when all required source fields are actually recorded.
- Missing historical fields remain `NOT_RECORDED_IN_SOURCE_VERSION`.
- New terminology must not be backdated as if it were preregistered for old runs.
- New behavior evidence requires a new frozen subject/intervention run.
- Semantic review remains post-hoc and append-only.
- Paid API use requires separate explicit authorization and spending ceiling.
