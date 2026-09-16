# R7 — Structural Inertia Control and Localized Recovery

Status: execution plan

## Research question
Can inherited process inertia be made observable, traceable, locally controllable, and selectively reversible through structural intervention, without specifying the terminal answer?

R7 follows the first-paper mechanism chain:

`Natural Jump → Inherited Inertia → One-shot Path Perturbation → Inertia Transition → Structural Control / Steering → Localized Recovery`

R5 establishes whether a bounded local perturbation can reorganize downstream process topology. R6 characterizes how post-reorganization inertia differs from the original natural inertia. R7 tests whether the direction and persistence of that inertia can be structurally shaped and locally recovered.

## Core distinction
R7 must not collapse three different mechanisms into one condition.

### C1 — One-Shot Free Continuation
The selected J0 receives the bounded intervention once. The experiment-origin signal is then removed and the system continues freely.

Purpose: observe endogenous inherited inertia after the local perturbation.

### C2 — Persistent Field Propagation
The same correction/state field that is introduced at J0 remains available to later eligible nodes.

Purpose: observe experiment-maintained persistence. This condition separates endogenous inertia from persistence that exists only because the experiment keeps supplying the same signal.

### C3 — ALR Structural Recovery
Authority-Localized Recovery operates on the structural lineage rather than merely persisting a semantic field.

Required ALR operations:
1. locate the earliest relevant authority-violating ancestor;
2. compute the affected dependency closure;
3. preserve/freeze unaffected successful nodes;
4. replace or repair the breached authority/provenance condition;
5. create a new revision lineage/hash;
6. reopen and re-execute only the affected subgraph;
7. observe residual inertia, recurrence, re-entry, secondary Jump formation, and topology reconstruction.

Purpose: test causally localized structural recovery and inertia steering.

## Two nested comparisons
### R7-A — One-Shot vs Persistent Propagation
Question: does endogenous inherited inertia differ from continuously injected state persistence?

Interpretation rule:
- persistence in C1 is endogenous to the resulting process;
- persistence in C2 may be experiment-maintained and must not be described as endogenous inertia without additional evidence.

### R7-B — Persistent Propagation vs ALR Recovery
Question: does structural lineage-aware recovery differ from simply carrying the same correction signal forward?

The semantic correction payload must be matched as closely as possible. The experimental difference should be the propagation/recovery structure, not richer information in ALR.

## Frozen comparability constraints
All three conditions should reuse, where technically possible:
- the same frozen parent state;
- the same selected natural J0;
- the same task and task data;
- the same agent pool and role prompts;
- the same model/provider bindings;
- the same semantic correction content;
- the same downstream observation horizon;
- the same Process Reality measurement schema.

Do not tell an agent the desired terminal answer. R7 changes structural conditions, not the target answer.

## Structural measurement ontology
Primary R7 evidence remains process-structural:
- Jump and descendant-Jump lineage;
- affected descendant localization;
- root-reachable events and depth;
- branch and merge structure;
- role re-entry;
- cross-agent relations;
- state inheritance;
- path-family evolution;
- reconvergence distance;
- residual old-inertia markers;
- emergence of new-inertia markers;
- affected/unaffected node preservation;
- reopened-node closure;
- revision lineage;
- recurrence and secondary Jump formation;
- terminal/process decoupling.

Engineering metrics such as token use, latency, reopened-node count, and preserved-node ratio are secondary.

## Operational definition of steering direction
R7 must operationalize "direction" using observable process quantities rather than metaphor alone. Candidate dimensions:
- actor transition sequence and edge distribution;
- state-lineage destination;
- descendant-Jump location;
- information-flow destination;
- path-family membership;
- re-entry topology;
- stage progression;
- affected-closure destination after recovery.

A directional change is reported descriptively as a change in these quantities. Do not claim reliable control unless repeated evidence supports that claim.

## ALR scope boundary
ALR is not synonymous with all structural steering.

ALR is a causally localized recovery operator anchored to the earliest authority-violating ancestor and its dependency closure. Broader structural steering may involve routing, handoff permissions, shared-state visibility, proposal/commit separation, stage boundaries, activation surfaces, re-entry permissions, or state-propagation rules. Those mechanisms are outside ALR unless explicitly implemented as part of an ALR recovery transaction.

## Execution phases
### Phase 0 — Offline contract and fixture validation
Implement and validate the three-arm protocol without paid model calls. Confirm:
- one-shot signal is consumed once and not reinjected;
- persistent field is present only where defined;
- ALR closure includes all and only structurally affected descendants under the registered dependency relation;
- preserved nodes remain immutable;
- revision identity is distinct from the original lineage;
- all three arms emit the same measurement/event schema.

### Phase 1 — Matched replay from frozen R5/R6-compatible parent
Create a three-arm matched run from the selected frozen parent/J0. Keep semantic payload fixed and vary only propagation/recovery structure.

### Phase 2 — Structural derivation
Derive process topology and R7 metrics from frozen raw traces. No semantic adjudication is required for the primary structural comparison.

### Phase 3 — Integrity freeze
Freeze raw evidence before interpretation. Bind task, model/provider, prompts, code SHA, parent-state hash, selected J0, intervention payload, ALR transaction record, revision hash, traces, derived measurements, and artifact hashes.

### Phase 4 — Optional semantic review
Semantic CPR or recovery adjudication is append-only and may be performed later from frozen evidence. Reviewer failure must never trigger a subject rerun.

## Reporting constraints
Primary claims may include observed localization, structural redirection, preservation, recurrence, reconstruction, or recovery distance.

Do not claim:
- that ALR is universally better;
- that persistent propagation is equivalent to endogenous inertia;
- that a terminally correct answer proves recovery;
- that one batch demonstrates reliable system control;
- that cross-model or cross-domain generality has been established.

## Exit criteria
R7 is ready for a first formal run when:
1. all three conditions are represented by executable protocol contracts;
2. one-shot/persistent/ALR differences are verified offline;
3. the same J0 and semantic payload can be bound across all arms;
4. ALR affected closure and preserved-node set are independently inspectable;
5. revision lineage is emitted into raw evidence;
6. downstream measurement uses the existing Process Reality ontology;
7. integrity validation fails closed before any paid subject call.
