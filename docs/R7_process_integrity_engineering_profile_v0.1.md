# R7 Process Integrity Protocol — Engineering Profile v0.1

Date: 2026-09-17  
Status: ENGINEERING IMPLICATION / OFFLINE DESIGN / NOT A SCIENTIFIC RESULT

## 1. Position

This document captures the engineering value implied by the R2-R7 mechanism work without redefining the scientific R7 experiment.

The proposed system role is a **lightweight, pluggable, non-invasive runtime integrity layer** for existing multi-Agent systems.

It does not replace existing Agent frameworks, MCP/A2A protocols, tool APIs or orchestration logic.

## 2. Core engineering value

The runtime layer provides three capabilities:

1. **Monitor** — register process events, source/provenance and content identity in real time;
2. **Scout / Localize** — trace Jump candidates, carriers, lineage, inherited inertia and affected closure;
3. **Point Repair** — when explicitly authorized, revise the smallest source-backed risk-bearing closure and resume free execution.

Compact lifecycle:

`Observe -> Address -> Trace -> Localize -> Repair -> Resume -> Verify`

## 3. Design principles

### Lightweight

Collect the minimum interoperable event/provenance data needed for tracing. Do not require private chain-of-thought or wholesale duplication of Agent internals.

### Pluggable

Integrate as middleware, sidecar, interceptor, adapter or event subscriber.

### Non-invasive by default

Passive mode must not alter normal prompts, Agent selection, tool routing, interface schema or terminal output.

### Protocol-agnostic

The layer should be adaptable to MCP, A2A, HTTP/RPC, event bus, workflow+Agent and custom orchestration.

### Real-time

Identity/lineage registration occurs as events happen rather than only through after-the-fact log reconstruction.

### Content-addressed

Messages, fields, states, evidence and revisions can be located by stable content/revision identity.

### Localized

Active recovery targets the smallest source-backed affected closure rather than rerunning the whole system.

### Auditable / reversible

Repairs create revision lineage instead of silent overwrite. Old lineage and re-entry remain observable.

## 4. Minimal event surface

A minimal adapter contract should expose:

### MessageEvent

- sender;
- receiver;
- message id/hash;
- source/provenance refs;
- send/delivery/read status;
- parent refs.

### StateEvent

- state/field key;
- value/content hash;
- status/authority metadata if available;
- writer;
- source refs;
- prior revision;
- new revision.

### InvocationEvent

- caller;
- callee/tool;
- request hash;
- result hash;
- authority context;
- parent refs.

### EvidenceSourceEvent

- source id/hash;
- evidence status;
- origin;
- time/version;
- linked fields/states.

### RevisionEvent

- prior hash;
- new hash;
- revision reason/condition id;
- affected closure;
- operation id.

## 5. Content-addressed identity

Recommended identities:

- `EventHash`;
- `MessageHash`;
- `StateHash`;
- `FieldHash`;
- `SourceHash`;
- `InvocationHash`;
- `RevisionHash`;
- `ClosureHash`.

Identity should be stable enough to support lineage queries while allowing framework adapters to preserve native ids as aliases.

## 6. Why this is different from ordinary logging

Traditional logs usually answer:

> what happened at a time/path?

The Process Integrity layer aims to answer:

> which exact information/state existed, where did it come from, who consumed it, what later state inherited it, where did the lineage propagate, and what is the smallest repairable affected closure?

Natural-language wording may change while content/revision lineage remains traceable.

## 7. Passive mode

Normal operation:

```text
Agent / Tool / State runtime
        |
        +--> passive event tap
                -> content identity
                -> source/provenance binding
                -> lineage registration
                -> R6 carrier/inertia observation
```

Passive mode must not become a supervisor or route planner.

## 8. Active recovery mode

Only after an explicit recovery condition/gate:

```text
candidate risk-bearing carrier
  -> source-backed localization
  -> affected closure
  -> preserve unaffected structure
  -> revise violated authority/provenance state
  -> local reopen/re-execution
  -> free continuation
  -> verify old/new lineage and re-entry
```

## 9. Interoperability rule

Adapters translate native runtime events into the common integrity event surface.

The core protocol should not require:

- replacement Agent SDK;
- proprietary multi-Agent topology;
- mandatory prompt format;
- replacement MCP/A2A transport;
- centralized decision authority.

## 10. Real-time point localization

Content addressing enables direct queries such as:

- Which source produced `FieldHash X`?
- Which messages/states inherited X?
- Which Agents read or adopted descendants of X?
- Which current states remain in X's affected closure?
- Which revision replaced X?
- Has the old lineage re-entered after repair?

This is the engineering basis for point repair.

## 11. Scientific relationship

The engineering profile depends on scientific evidence from:

- R2/R3 — observable Jump and lineage structure;
- R6 — carrier/inertia identification and target specificity;
- R7 — localized recovery and preservation tests.

If those scientific claims fail, the engineering layer may still be useful as observability tooling, but its stronger mechanism-guided repair claims would need to be weakened.

## 12. Productization boundary

The first paper only needs to show mechanism-derived feasibility and experimentally testable local recovery. It does not need to prove full enterprise production readiness.

Future product work may add:

- streaming indexes;
- distributed content-address stores;
- framework adapters;
- visual lineage graphs;
- authorization policies;
- tenant isolation;
- rollback/replay tooling;
- SLA/latency benchmarking.

These are downstream engineering extensions, not prerequisites for the first scientific paper.
