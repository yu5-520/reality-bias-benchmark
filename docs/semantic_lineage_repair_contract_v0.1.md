# Semantic Lineage Repair Contract v0.1

Date: 2026-09-18  
Status: FORWARD ENGINEERING CONTRACT / OFFLINE ONLY

## 1. Repair scope

A repair context is bounded by target semantic identity, not by a fixed number of nearby turns.

`local = complete relevant lineage + excluded unrelated semantics`.

## 2. Required machine objects

- Structural Repair Anchor
- target semantic ID
- content address
- Semantic Lineage Closure
- Lineage Completeness Gate
- EvidenceSupportedAffectedClosure
- RepairClosure
- preserved unrelated refs
- raw evidence refs

## 3. Repair-Agent rule

The Repair Agent may reason over recorded lineage.

It may not convert missing lineage into historical fact.

When a critical component is missing, the packet status must expose `LINEAGE_GAP`.

## 4. Completeness dimensions

At minimum:

- source bound;
- transformations bound;
- authority history bound;
- pool/current state bound;
- affected descendants bound;
- evidence pointers bound.

## 5. Optimization objective

```text
minimize unrelated context
subject to relevant semantic lineage completeness >= repair threshold
```

## 6. Identity / semantics boundary

Content address establishes object identity and enables retrieval.

It does not establish semantic adoption. Relation evidence remains required.

## 7. Authorization

This contract authorizes no active repair.
