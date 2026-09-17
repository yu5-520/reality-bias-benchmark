# R7 — Structural Inertia Control and Localized Recovery

## Research question

R7 asks whether inherited system inertia can be directionally shaped by a structural framework and whether the same framework can make the resulting process observable, traceable, locally controllable, and selectively reversible.

R7 follows the first-paper mechanism chain:

`Natural Jump → Inherited Inertia → One-shot Path Perturbation → Path Reorganization → Inertia Transition → Structural Control / Steering → Localized Recovery`

R5 establishes whether a bounded local perturbation can reorganize the downstream process path. R6 studies how the resulting inertia differs from the original natural inertia. R7 tests whether a structural framework can actively localize, redirect, or recover that inertia without prescribing the terminal answer.

## Three matched conditions

All three conditions must begin from the same frozen parent and the same natural Jump anchor J0. Task, model/provider binding, agent registry, prompt policy, semantic correction payload, and observation horizon should be held fixed wherever the mechanism permits.

### C1 — One-Shot Free Continuation

The J0 perturbation is exposed exactly once and then removed from experiment-origin input.

`J0 → one-shot exposure → free evolution`

Purpose: estimate endogenous inherited inertia after the experiment stops injecting the variable.

### C2 — Persistent Field Propagation

The same correction/status field is kept visible to downstream nodes across the matched continuation horizon.

`J0 → field persists → downstream node → same field persists → ...`

Purpose: distinguish endogenous inertia from experiment-maintained persistence. Persistence in this arm must not be interpreted as endogenous inertia because the experiment continues to supply the signal.

### C3 — ALR Structural Recovery

The same J0 and matched semantic correction payload are used, but the correction is applied through Authority-Localized Recovery rather than repeated field exposure. ALR identifies the earliest relevant authority-violating ancestor, computes the affected dependency closure, preserves unaffected successful nodes, changes the breached authority/provenance condition, records a new revision lineage, and reopens or re-executes only the affected subgraph.

Purpose: test whether lineage-aware structural recovery can localize, redirect, and selectively reverse inherited inertia more precisely than simple persistent signal transmission.

## Nested tests

### R7-A — One-Shot vs Persistent Propagation

Question: does the observed downstream structure after a one-shot perturbation differ from a continuation in which the same field is continuously reintroduced?

Interpretation boundary:

`endogenous inherited inertia ≠ continuously injected persistence`

### R7-B — Persistent Propagation vs ALR Recovery

Question: with the semantic correction payload held as equivalent as possible, does lineage-aware structural recovery produce a different downstream process structure than simple continuous field propagation?

This is the direct mechanism comparison for structural controllability.

## Passive and active ALR

R2–R6 use an ALR-compatible structural observability substrate in passive mode. The substrate records naturally realized messages, state transitions, invocations, agent participation, final-state revisions, and lineage evidence; it does not prescribe the natural topology.

R7 activates the same structural representation as a recovery/control operator.

A defensible methodological statement is:

> ALR does not create the observed process structure; it makes naturally realized process structure observable. R7 then tests whether that observed structure is sufficiently real to support localized control and recovery.

The natural Arena remains free-routing rather than structurally steered toward the observed topology. Common runtime constraints such as role identity, action protocol, safety/budget limits, and serialization are not equivalent to prescribing path topology, node order, lineage, or desired terminal answer.

## Raw evidence versus derived structure

To avoid measurement circularity, R7 must preserve the distinction between raw observable facts and derived structural interpretation.

Raw evidence includes:

- message send/delivery/read events;
- agent invocation and execution events;
- shared-state writes and metadata changes;
- final-state revisions;
- actual model input/output and parsed actions;
- queue, inbox, invocation, execution, and termination state.

Derived structure includes:

- J0 and descendant Re-Jumps;
- dependency closure;
- inherited-inertia lineage;
- affected versus unaffected subgraph;
- path-family reconstruction;
- recovery/re-entry relations.

Claims about structural control must be traceable from the derived graph back to immutable raw evidence.

## Structural outcome variables

Primary R7 evidence is process-structural, not terminal-answer accuracy. Reuse the existing Process Reality measurement ontology wherever possible:

- Jump and descendant Re-Jump lineage;
- root-reachable event count and reach depth;
- path-family count and transition pattern;
- branch/merge/re-entry structure;
- cross-agent relations and agent participation;
- state-inheritance lineage;
- affected descendant localization;
- unaffected-node preservation;
- old-path residual markers and recurrence;
- new/secondary Jump formation;
- reconvergence distance;
- recovery distance;
- structural steering direction;
- terminal/process decoupling.

Secondary engineering metrics may include reopened node count, preserved node ratio, provider calls, tokens, latency, and cost, but they do not define the scientific result.

## Operational definition of direction

R7 must not use the word `direction` as an intuitive metaphor only. A steering-direction result must be represented by one or more predeclared structural coordinates, for example:

- actor-transition sequence or edge distribution;
- destination of state/provenance lineage;
- location of descendant Re-Jumps;
- re-entry topology;
- stage progression;
- path-family transition;
- downstream reach/depth profile.

No condition may be labeled successful merely because the final answer is preferred.

## Control rules

1. Freeze the parent state and J0 before any R7 continuation outcome is visible.
2. Bind all conditions to the same parent hash, task hash, agent-registry hash, model-config hash, and code identity.
3. C1 receives exactly one experiment-origin exposure and no reinjection.
4. C2 receives repeated exposure of only the predeclared field/payload according to a fixed delivery rule. Repeated exposure must be recorded explicitly.
5. C3 must not receive richer semantic correction content than C2. The independent variable is structural handling/recovery, not semantic assistance.
6. ALR may reopen only the precomputed affected dependency closure; unaffected successful nodes are preserved unless an explicit structural dependency requires reopening them.
7. Provider-internal hidden state is never claimed to be replayed.
8. Semantic CPR adjudication remains separable from runtime execution and structural measurement.
9. Terminal answer remains a secondary endpoint.

## Interpretation ladder

R7 can support increasingly strong claims only when the corresponding evidence exists:

1. **Observable** — natural process structure can be reconstructed from raw evidence.
2. **Traceable** — downstream affected events can be linked back to J0 through recorded lineage.
3. **Localizable** — the affected closure can be identified without reopening unrelated structure.
4. **Steerable** — changing structural transition/recovery rules changes downstream structural coordinates while semantic payload is matched.
5. **Selectively reversible** — affected structure can be recovered/reopened while preserving unaffected structure, with residual/recurrence explicitly measured.

Do not use the stronger word `controllable` as a conclusion unless repeated evidence demonstrates reliable steering rather than a single structural difference.

## Engineering deliverables

R7 implementation should provide:

- a persistent-field runtime-view transform with explicit per-turn exposure records;
- an ALR recovery plan that binds authority ancestor, dependency closure, preserved nodes, reopened nodes, and revision lineage;
- three-condition manifests sharing one frozen parent identity;
- a preflight that verifies semantic-payload equivalence and condition isolation before any paid provider call;
- a structural comparison artifact for C1/C2/C3;
- an immutable evidence bundle with raw traces, manifests, measurements, hashes, and interpretation boundaries.

The first implementation stage is engineering-only and must not be labeled scientific evidence until it is executed prospectively with the real-model protocol and frozen before analysis.
