# R7 Process Integrity Protocol — Engineering Profile v0.2

Date: 2026-09-17  
Status: ENGINEERING IMPLICATION / OFFLINE DESIGN / NOT A SCIENTIFIC RESULT  
Predecessor: `docs/R7_process_integrity_engineering_profile_v0.1.md`

## 1. Position

The proposed layer remains lightweight, pluggable and passive by default. Observation/indexing can be protocol-agnostic through adapters; active recovery still depends on native runtime state/replay/execution interfaces.

## 2. Core lifecycle

`Observe -> Address -> Trace -> Localize -> Separate Potential/Evidenced Closure -> Repair if authorized -> Resume -> Verify`

## 3. Identity is not adoption

Content hashes answer:

- which object/version;
- where it came from;
- which structural descendants are linked.

Relation evidence answers:

- whether delivered/read;
- whether used as a decision premise;
- whether inherited into a new state/action;
- whether propagated.

The protocol must not substitute hash ancestry for semantic-use evidence.

## 4. Closure tiers

Maintain three explicit sets:

- `PotentiallyAffectedClosure`;
- `EvidenceSupportedAffectedClosure`;
- `RepairClosure`.

Potential closure supports scouting. Evidence-supported closure supports risk localization. Repair closure adds only mechanically required replay dependencies.

## 5. Minimal event surface

- MessageEvent;
- StateEvent;
- InvocationEvent;
- EvidenceSourceEvent;
- RevisionEvent;
- RelationEvidenceRecord.

## 6. Relation evidence

A relation record should bind source/destination refs, relation type, evidence refs, evidence level and semantic-use status.

## 7. Endogenous persistence

Passive/experimental overlays must distinguish experiment-origin persistence from subject-generated persistence. Endogenous subject writes remain first-class observed events.

## 8. Runtime modes

### PASSIVE

Observe/register/hash/trace only. No prompt rewrite, routing control or recovery state write.

### ACTIVE_RECOVERY

Requires:

- explicit gate;
- named authority/provenance condition;
- evidence-supported affected set;
- repair closure;
- native recovery adapter;
- revision identity;
- post-repair verification.

## 9. Interoperability boundary

Common observation/event semantics may be portable across frameworks. State patching, replay, reopen and execution are adapter responsibilities and may differ by framework.

## 10. Product/scientific boundary

This engineering profile is a design implication. Scientific efficacy remains an R7 experimental question.
