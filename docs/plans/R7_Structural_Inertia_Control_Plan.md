# R7 — Structural Inertia Control and Localized Recovery

Status: exact-source-bound execution plan; runtime mechanisms implemented; paid subject execution not authorized

## Research question

Can inherited process inertia be made observable, traceable, directionally steerable, locally recoverable, and selectively reversible through structural intervention, without prescribing the terminal answer?

R7 follows the first-paper mechanism chain:

`Natural Jump → Inherited Inertia → One-shot Path Perturbation → Path Reorganization → Inertia Transition → Structural Steering → Localized Recovery`

R5 establishes that a bounded local perturbation can reorganize downstream process topology. R6 asks how the resulting inertia differs from the original natural inertia. R7 asks whether the direction and persistence of that inertia can be structurally shaped and locally recovered.

## Three conditions

### C1 — One-Shot Free Continuation

The selected J0 correction is made visible exactly once on the first resumed post-Jump agent turn. The experiment-origin signal is then removed and the process continues freely.

Purpose: observe endogenous inherited inertia after the intervention is no longer supplied by the experiment.

### C2 — Persistent Field Propagation

The same semantic correction field is re-exposed on every eligible downstream agent turn within one predeclared observation horizon.

Purpose: observe experiment-maintained persistence and separate it from endogenous inherited inertia.

### C3 — ALR Structural Recovery

Authority-Localized Recovery acts on the authority-bearing structural transition rather than repeatedly carrying the semantic field forward.

For the currently frozen J0, the available source evidence provides an exact checkpoint immediately before the natural J0-producing turn. C3 therefore performs a conservative turn-localized recovery transaction:

1. preserve the entire natural prefix before the J0-producing turn;
2. roll back from the common post-J0 reference parent to the exact `before_turn:8` checkpoint;
3. re-execute the natural J0 actor (`inventory`) with the same task, agent registry, model binding, Arena protocol, and source state available at that checkpoint;
4. preserve the raw provider response and raw parsed action envelope;
5. if and only if the re-executed turn naturally emits exactly one matching authority-bearing `write_state` for `inventory_stockout_assessment_v1` with status `fact`, transform only that status commit to `unconfirmed` before Arena realization;
6. record the raw/applied envelope hashes, action hashes, delta path, authority class, revision lineage, and downstream process trace;
7. continue prospectively under the same observation horizon as C1 and C2.

This is a structural rollback/re-execution operation, not a richer prompt. It changes the realized authority condition at the localized transition while leaving the provider's raw output as evidence.

## Exact frozen source binding

The current first formal R7 design is bound to the already frozen R5 source evidence:

- source R5 plan hash: `a24c98901422bbccfc9a040a6bc14575b1c710edd518c0d9c2facf7a57926351`;
- common post-J0 reference parent: `after_turn:8` / state hash `aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c`;
- C3 recovery checkpoint: `before_turn:8` / state hash `99731abb4ffd1caa2e568a6c2d90987700b3d0b7a66a1c777f811b666912a349`;
- checkpoint turn count: 7;
- checkpoint event count: 32;
- checkpoint queue head: `inventory`;
- natural J0: source event `E32`, actor `inventory`;
- target state: `inventory_stockout_assessment_v1.status`;
- matched semantic change: `fact → unconfirmed`;
- Process Reality measurement schema: `RB-PROCESS-REALITY-MECHANISM-MEASUREMENT-v0.4`.

The common comparison identity is the same frozen natural J0 and the same post-J0 reference parent. C1 and C2 resume directly from that parent. C3 necessarily starts one source turn earlier because structural recovery must operate on the transition that created J0. This difference is the recovery mechanism itself and must not be described as all three arms literally starting from an identical runtime snapshot.

## Matched horizon

All conditions use horizon `R7-H1-POST-JUMP-TURN-CAP-8`:

- distance basis: post-Jump agent turn;
- maximum downstream distance: 8 agent turns;
- natural termination is preserved;
- early termination is recorded as censoring and is never extended merely to equalize trace length;
- comparisons are restricted to observed matched distances while retaining censoring information.

C2 therefore has a maximum of eight direct experiment-origin exposures; the actual count may be smaller if the run naturally terminates earlier.

## Two nested comparisons

### R7-A — One-Shot vs Persistent Propagation

Question: does endogenous inherited inertia after a one-shot perturbation differ from persistence maintained by repeatedly supplying the same field?

Interpretation boundary:

`endogenous inherited inertia ≠ continuously injected persistence`

### R7-B — Persistent Propagation vs ALR Recovery

Question: with the semantic correction held equivalent, does localized structural recovery produce a different downstream topology from simple persistent signal transmission?

The independent variable is the handling of the correction:

- C2 repeatedly changes what is visible in the downstream prompt-time runtime view;
- C3 changes the localized authority-bearing state transition and then observes the resulting lineage.

C3 must not receive richer semantic correction information than C2.

## C3 non-reproduction rule

Provider-internal hidden state is not replayable and is never claimed to be replayed. Re-executing the exact visible checkpoint may therefore produce a different action envelope.

If the C3 re-execution does **not** naturally reproduce exactly one matching J0-shaped target write (`inventory_stockout_assessment_v1`, status `fact`) on the targeted actor/turn:

- do not retry until the desired action appears;
- do not reject samples to force the intervention;
- do not synthesize the missing natural action;
- record the arm as `C3_J0_REPRODUCTION_NOT_OBSERVED`;
- preserve the trace as a censored/non-realized intervention observation.

This rule prevents rejection sampling from quietly converting structural recovery into semantic outcome forcing.

## Evidence model

R7 keeps raw evidence distinct from derived structure.

Raw evidence includes actual model inputs, raw provider outputs, raw parsed envelopes, applied envelopes when a structural transform occurs, messages, reads, invocations, shared-state writes, final-state revisions, queues, ledgers, termination, usage, runtime-view exposure records, action-transform records, and revision records.

Derived evidence includes J0/descendant Re-Jump relations, source-backed lineage, dependency closure, affected/unaffected topology, path families, branch/merge/re-entry relations, recovery distance, residual old-inertia markers, and structural steering coordinates.

Raw evidence must be frozen before any R7 structural derivation or semantic review.

## Structural measurement ontology

Primary R7 evidence is process-structural rather than terminal accuracy. Reuse the existing Process Reality ontology wherever possible:

- Jump and descendant Re-Jump lineage;
- root-reachable events and reach depth;
- actor-transition and edge distributions;
- path-family count and transition;
- branch, merge, and role re-entry;
- cross-agent relations;
- state/provenance inheritance;
- affected descendant localization;
- preserved prefix/unaffected structure;
- residual old-inertia markers and recurrence;
- new/secondary Jump formation;
- reconvergence and recovery distance;
- structural steering direction;
- terminal/process decoupling.

Engineering metrics such as provider calls, token use, latency, reopened-event count, and preserved-prefix ratio remain secondary.

## Operational definition of steering direction

`Direction` must be represented by observable structural coordinates rather than intuition alone. Candidate coordinates include:

- actor-transition sequence and edge distribution;
- destination of state/provenance lineage;
- location of descendant Re-Jumps;
- information-flow destination;
- path-family transition;
- re-entry topology;
- downstream reach/depth profile.

A preferred terminal answer is not evidence of structural steering.

## Passive versus active ALR

R2–R6 use an ALR-compatible structural observability substrate passively: realized process events are recorded and reconstructed after they occur. R7 activates that structural representation as a recovery operator.

> ALR does not create the observed process structure; it makes naturally realized process structure observable. R7 then tests whether that observed structure is sufficiently real to support localized recovery and steering.

The current C3 implementation is deliberately conservative. Snapshot granularity makes the natural J0-producing agent turn the smallest prospectively re-executable source unit. The claim must therefore be `turn-localized authority recovery` for this experiment, not arbitrary sub-event graph surgery.

## Implementation status

Implemented and offline-validated:

- C1 one-shot copied-runtime-view transform;
- C2 persistent-field copied-runtime-view transform with explicit exposure/reinjection records;
- exact frozen source artifact and checkpoint verification;
- C3 rollback binding to the exact pre-J0 checkpoint;
- post-parse/pre-realization ALR authority transform that preserves the raw provider envelope separately from the applied envelope;
- revision-lineage plumbing;
- deterministic three-arm Arena integration smoke test;
- guarded real three-arm subject runner with symmetric per-branch call/spend limits and a global ceiling;
- real-run preflight that requires no provider credentials and makes zero provider calls.

The deterministic smoke test is engineering evidence only. It is not subject evidence and cannot support a scientific steering/control claim.

## Paid-run gate

The prepared plan never self-authorizes provider calls. Real subject execution remains unauthorized until an explicit external authorization is supplied to the guarded runner.

The runner's exact authorization phrase is:

`CALL_REAL_R7_THREE_ARM_API`

A formal run must freeze raw evidence immediately after subject execution and before structural derivation. No automatic paid evaluator is part of the subject chain.

## Reporting constraints

Primary claims may describe observed localization, redirection, preservation, recurrence, reconstruction, recovery distance, or failure to reproduce the target authority transition.

Do not claim from a first batch:

- that ALR is universally better;
- that persistent propagation is endogenous inertia;
- that a terminally correct answer proves recovery;
- that one matched batch establishes reliable control;
- that provider hidden state was replayed;
- that same-parent repeated branches are independent samples;
- that cross-model or cross-domain generality has been established.

## Exit criteria for the first formal R7 subject run

The formal run may proceed only when:

1. the exact prepared and natural-raw source artifacts pass hash verification;
2. the common reference parent, pre-J0 checkpoint, J0, semantic payload, model binding, and horizon pass fail-closed validation;
3. C1/C2/C3 runtime mechanisms pass offline Arena integration tests;
4. the guarded real runner passes zero-call preflight;
5. a raw-evidence freeze step is wired before any derivation;
6. the user explicitly authorizes the paid subject run under a declared budget;
7. semantic review remains deferred and append-only.
