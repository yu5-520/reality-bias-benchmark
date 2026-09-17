# R7 — Structural Inertia Control and Localized Recovery

## Research question

R7 asks whether inherited system inertia can be directionally shaped by a structural framework and whether the same framework can make the resulting process observable, traceable, locally steerable, and selectively recoverable without prescribing the terminal answer.

Mechanism chain:

`Natural Jump → Inherited Inertia → One-shot Path Perturbation → Path Reorganization → Inertia Transition → Structural Steering → Localized Recovery`

R5 establishes local path reorganization. R6 studies post-reorganization inertia. R7 tests whether a structural representation that first observed that process can later support localized intervention and recovery.

## Three matched mechanisms

The experiment is bound to one frozen natural J0, one common post-J0 reference parent, one semantic correction, one task/model/agent configuration, and one downstream observation horizon. The arms differ in **how** the correction enters the process.

### C1 — One-Shot Free Continuation

`J0 → one prompt-visible exposure → free evolution`

The correction is shown exactly once on the first resumed post-Jump turn and is then removed from experiment-origin input.

Purpose: observe endogenous inherited inertia after experiment-origin input stops.

### C2 — Persistent Field Propagation

`J0 → same field visible → next eligible turn → same field visible → ...`

The same correction is repeatedly made visible in the copied runtime view for each eligible downstream turn within the common horizon.

Purpose: observe experiment-maintained persistence and distinguish it from endogenous inherited inertia.

### C3 — ALR Structural Recovery

`pre-J0 checkpoint → re-execute authority ancestor turn → local authority transform → new descendants`

C3 does not repeatedly carry the correction through prompt-visible state. It rolls back to the exact source checkpoint immediately before the natural J0-producing turn, re-executes that turn, preserves the raw provider output, and—only if the same target authority-bearing write naturally appears—changes the realized status of that one write from `fact` to `unconfirmed` before Arena state realization.

Purpose: test whether a localized structural recovery operation produces a different inertia/path response from persistent semantic transmission.

## Exact source binding

The first formal R7 configuration is tied to the frozen R5 source:

- common reference parent: `after_turn:8`, state hash `aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c`;
- exact recovery checkpoint: `before_turn:8`, state hash `99731abb4ffd1caa2e568a6c2d90987700b3d0b7a66a1c777f811b666912a349`;
- natural J0: `E32`, actor `inventory`;
- target: `inventory_stockout_assessment_v1.status`;
- matched semantic correction: `fact → unconfirmed`;
- common post-Jump horizon: 8 agent turns;
- measurement ontology: `RB-PROCESS-REALITY-MECHANISM-MEASUREMENT-v0.4`.

C1 and C2 start directly from the common post-J0 reference parent. C3 starts one natural source turn earlier because the recovery operation must act on the transition that created J0. Therefore `same parent` in R7 means the same frozen **reference parent/J0 comparison object**, not an assertion that all mechanisms literally begin from the same runtime snapshot.

This distinction is methodological rather than cosmetic. Treating C3 as if it could repair an already committed J0 without reopening its causal transition would collapse structural recovery back into downstream field injection.

## Nested tests

### R7-A — One-Shot vs Persistent Propagation

Question: does downstream structure after a one-shot perturbation differ from structure observed when the same signal is continuously reintroduced?

Interpretation boundary:

`endogenous inherited inertia ≠ continuously injected persistence`

### R7-B — Persistent Propagation vs ALR Recovery

Question: with semantic correction meaning matched, does localized authority recovery produce a different downstream structural response from repeated prompt-visible propagation?

C2 changes downstream visibility. C3 changes a localized realized authority transition and then allows the new process to evolve.

## Why raw and applied envelopes are separated

C3 uses a post-parse/pre-realization action transform. The model's raw output is not overwritten in evidence.

For the target turn the trace preserves:

- raw provider content;
- raw parsed envelope;
- applied envelope after the structural transform;
- exact transformed action index and delta path;
- raw/applied action hashes;
- raw/applied envelope hashes;
- subsequent realized Arena event/state.

This separation prevents the recovery framework from laundering its own intervention into apparent model behavior.

## C3 non-reproduction is data, not a failure to retry

Provider hidden state cannot be replayed. Re-executing the same visible source checkpoint may not recreate the natural J0-shaped action.

If exactly one matching `inventory_stockout_assessment_v1` write with status `fact` does not naturally recur on the targeted C3 turn, the system records:

`C3_J0_REPRODUCTION_NOT_OBSERVED`

It must not retry until the desired action appears, force a replacement action, or discard the run. Such a trace is a censored/non-realized intervention observation and is scientifically informative about the recoverability boundary.

## Passive and active ALR

R2–R6 use an ALR-compatible observability substrate passively. It records realized messages, state changes, invocations, execution, final-state revisions, and source-backed lineage without prescribing the natural routing topology.

R7 activates that structural representation as a recovery operator.

> ALR does not create the observed process structure; it makes naturally realized process structure observable. R7 then tests whether that observed structure is sufficiently real to support localized recovery and steering.

The current first formal C3 is intentionally **turn-localized** because the frozen source provides a stable checkpoint immediately before the authority-ancestor turn. This experiment must not be described as arbitrary sub-event graph surgery.

## Raw evidence versus derived structure

Raw facts include:

- model input/messages;
- raw provider output;
- raw parsed actions;
- applied actions when a structural transform occurs;
- message send/delivery/read events;
- invocation/execution events;
- shared-state writes and metadata changes;
- final-state revisions;
- queues, ledgers, failures, termination and usage;
- C1/C2 exposure records;
- C3 authority-transform and revision-lineage records.

Derived interpretation includes:

- J0 and descendant Re-Jumps;
- inherited-inertia lineage;
- affected descendants;
- path-family reconstruction;
- branch/merge/re-entry topology;
- recovery distance and residual old-inertia markers;
- structural steering coordinates.

Raw evidence is frozen before any derived analysis. Semantic CPR review remains a later append-only layer.

## Structural outcome variables

Primary outcomes remain process-structural:

- Jump and descendant Re-Jump lineage;
- root-reachable event count and reach depth;
- actor-transition sequence and edge distribution;
- path-family count/transition;
- branch/merge/re-entry structure;
- cross-agent relations and agent participation;
- state/provenance inheritance;
- preserved prefix and affected descendant localization;
- residual old-path markers and recurrence;
- new/secondary Jump formation;
- reconvergence/recovery distance;
- structural steering direction;
- terminal/process decoupling.

Provider calls, tokens, latency, reopened-event count, and preservation ratio are secondary engineering measures.

## Operational meaning of direction

A steering claim must be tied to predeclared structural coordinates such as:

- actor-transition sequence or edge distribution;
- state/provenance-lineage destination;
- descendant Re-Jump location;
- re-entry topology;
- path-family transition;
- downstream reach/depth profile.

A preferred final answer is not evidence of steering.

## Common horizon and censoring

All arms use `R7-H1-POST-JUMP-TURN-CAP-8`.

- maximum downstream distance: 8 post-Jump agent turns;
- natural termination is retained;
- shorter arms are not artificially extended;
- early termination is marked as censoring;
- C2 exposure count is therefore bounded by eight but may be lower in naturally shorter trajectories.

## Interpretation ladder

Evidence strength is cumulative:

1. **Observable** — process structure can be reconstructed from raw evidence.
2. **Traceable** — downstream events can be linked to the natural J0/source lineage.
3. **Localizable** — a recovery operation can be restricted to the smallest supported source checkpoint/transition rather than restarting the entire run.
4. **Steerable** — matched structural handling changes downstream structural coordinates.
5. **Selectively recoverable** — affected structure can be re-executed while preserving the unaffected prefix, with residual/re-entry/recurrence explicitly measured.

Do not conclude `controllable` from a single matched batch. Reliable control requires repeated evidence that steering is reproducible rather than merely different.

## Engineering status versus scientific evidence

The repository now contains:

- executable C1 and C2 runtime-view transforms;
- an executable C3 authority-localized action transform;
- exact source-parent and pre-J0 checkpoint binding;
- raw-vs-applied envelope preservation in the Arena engine;
- revision-lineage plumbing;
- deterministic three-arm Arena smoke execution;
- a guarded real three-arm subject runner;
- zero-call real-run preflight and symmetric budget guards.

The deterministic smoke uses synthetic provider envelopes and is **engineering-only**. It demonstrates that the experimental machinery functions; it does not demonstrate that system inertia is steerable.

Real provider execution is separately gated and currently unauthorized. The exact external authorization phrase expected by the runner is `CALL_REAL_R7_THREE_ARM_API`.

## Claim boundaries

A first formal R7 batch may support descriptive claims about observed localization, redirection, recurrence, reconstruction, recovery distance, or non-reproduction of the target transition.

It must not by itself establish:

- universal superiority of ALR;
- equivalence between C2 persistence and endogenous inertia;
- reliable system control;
- provider-hidden-state replay;
- independence of same-parent repeated branches;
- semantic CPR status unless separately adjudicated;
- cross-model or cross-domain generality.
