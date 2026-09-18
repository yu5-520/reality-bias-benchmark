# R7 Process Integrity Protocol — Engineering Profile v0.3

Date: 2026-09-18  
Status: ENGINEERING IMPLICATION / OFFLINE DESIGN / NOT A SCIENTIFIC RESULT  
Predecessor: `docs/R7_process_integrity_engineering_profile_v0.2.md`

## 1. Core lifecycle

`Observe -> Scout -> Repair Anchor -> Content Address -> Semantic Lineage Closure -> Completeness Gate -> Audit -> Repair -> Recompute -> Verify`

## 2. Engineering principle

The protocol does not minimize relevant semantic history.

It minimizes **unrelated** semantic context while preserving the complete evidence-supported target lineage.

## 3. Content addressing

Hashes/IDs establish:

- object identity;
- version;
- provenance links;
- structural descendants.

They do not by themselves establish semantic adoption.

Relation evidence remains required for semantic-use claims.

## 4. Semantic Lineage Closure

Maintain a semantically scoped closure containing relevant:

- ancestors;
- transformations;
- authority transitions;
- shared-pool states;
- revisions;
- semantic descendants.

The closure may span the entire task.

## 5. Completeness gate

A repair packet must be classified before active repair:

- COMPLETE_FOR_AUTHORIZED_REPAIR
- COMPLETE_FOR_AUDIT_ONLY
- LINEAGE_GAP
- UNRESOLVED

`LINEAGE_GAP` blocks automatic repair.

## 6. Closure model

Keep distinct:

- PotentiallyAffectedClosure;
- EvidenceSupportedAffectedClosure;
- SemanticLineageClosure;
- RepairClosure.

SemanticLineageClosure explains the relevant semantic history.

EvidenceSupportedAffectedClosure explains what is semantically/decision affected.

RepairClosure adds mechanically required replay/recompute dependencies.

## 7. Repair Agent constraint

The Repair Agent may interpret recorded lineage.

It may not invent missing lineage as fact.

## 8. Runtime modes

PASSIVE:

- scout;
- address;
- trace;
- build closures;
- evaluate completeness;
- no state mutation.

ACTIVE_RECOVERY:

requires:

- explicit authorization;
- Repair Anchor;
- complete/authorized Semantic Repair Packet;
- evidence-supported affected closure;
- RepairClosure;
- native recovery adapter;
- revision identity;
- post-repair verification.

## 9. Scientific boundary

This engineering profile is an implication derived from the mechanism work.

Its efficiency and repair efficacy require separate engineering experiments.
