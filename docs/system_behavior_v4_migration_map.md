# System Behavior v4 Migration Map

Date: 2026-09-16  
Status: FORWARD IMPLEMENTATION MAP

This file records how existing v3.x research/instrumentation maps into the v4 system-behavior layer without rewriting historical evidence.

## 1. Concept mapping

| Existing artifact / concept | v4 position | Action |
| --- | --- | --- |
| `Trajectory Measurement v3` | structural branch / continuation substrate | preserve and reuse |
| C/P/R Reviewer layers | semantic annotation layer | preserve; do not make primary detector |
| `HIGH_CERTAINTY_STATE_WRITE_CANDIDATE` | one concrete `TRANSITION_ANCHOR` selector | preserve; reclassify forward use only |
| status downgrade branch | first `MID` containment experiment | preserve |
| Free vs Structured routing | first `STRUCTURE` variable family | preserve |
| parent/start hash separation | branch identity invariant | preserve |
| continuation slicing | branch outcome boundary | preserve |
| branchability pending-queue rule | runtime continuation invariant | preserve |
| full raw model outputs | source evidence | preserve; not primary measurement unit |
| semantic reviewer packets | small-window semantic layer | narrow forward packets where possible |

## 2. New v4 layers

New artifacts are additive:

- System Trajectory identity;
- Node/Boundary registry;
- Behavior Event record;
- State Transition record/refs;
- Experimental Variable registry;
- multi-position PRE/MID/POST manipulation semantics;
- four forward anchor classes.

## 3. Code migration rule

Do not rewrite the current Arena event journal merely to fit v4.

Forward implementation should use adapters:

`existing trace/journal → behavior-event adapter → v4 measurement`

This preserves raw historical and current runtime evidence while allowing the measurement ontology to evolve independently.

If a source event lacks a required v4 field, the adapter must emit a missing/not-recorded status or omit the derived record. It must never invent a historical observation.

## 4. First implementation phase

Current first phase:

1. machine-readable variable registry;
2. machine-readable boundary registry;
3. behavior-event schema;
4. system-trajectory measurement schema;
5. registry validators;
6. deterministic offline behavior-first preflight;
7. README / protocol / theory alignment.

This phase does not change live subject behavior.

## 5. Second implementation phase

Before new real subject evidence, add source-version-specific adapters that map current Arena trace events into `RB-BEHAVIOR-EVENT-v0.1` without altering the raw source trace.

Candidate adapters should cover first:

- shared-state writes;
- message send/delivery/read;
- invocation proposal/realization;
- FINAL/reopen/revision;
- deterministic commit/handoff events where recorded.

## 6. Third implementation phase

After adapter validation:

- emit v4 behavior indexes from new subject evidence;
- derive R2/R3/R4 synchronized views;
- create small semantic review windows around selected behavior transitions;
- bind branch plans to experimental variable and measurement boundary registries.

## 7. Scientific boundary

The migration itself is engineering work, not scientific evidence.

No existing CPR count, Jump count, penetration result or intervention result changes merely because the measurement ontology has been upgraded.