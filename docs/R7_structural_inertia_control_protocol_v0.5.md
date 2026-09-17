# R7 Structural Inertia Risk Control Protocol v0.5

Date: 2026-09-17  
Status: FORWARD SCIENTIFIC CONTROL PROTOCOL / CLOSURE MODEL REFINED / NO REAL RUN AUTHORIZED  
Predecessor: `docs/R7_structural_inertia_control_protocol_v0.4.md`

## 1. Purpose

R7 tests whether a source-backed risk-bearing inherited condition can be localized and repaired while preserving unrelated process freedom.

## 2. Entry requirement

R7 should consume R6 evidence that distinguishes normal inheritance from an inertia-bearing candidate and records relation/adoption evidence where available.

## 3. Three closure objects

### PotentiallyAffectedClosure

All descendants structurally reachable from the root under preregistered dependency/lineage edges.

Purpose: scouting and upper-bound localization.

It is not automatically the repair set.

### EvidenceSupportedAffectedClosure

Subset with source-backed evidence of delivery/read/adoption/inheritance/propagation or another frozen dependence criterion.

Purpose: evidence-supported impact set.

### RepairClosure

The minimal active recovery set:

`EvidenceSupportedAffectedClosure + MechanicallyRequiredReplayDependencies`

Any replay-only dependency must be explicitly marked and must not be semantically relabeled as affected.

## 4. C1/C2/C3 remain unchanged

- C1 one-shot free continuation;
- C2 persistent field propagation;
- C3 ALR localized recovery.

## 5. Locality criterion

R7 success requires both:

- reduction/localization of the identified risk-bearing inheritance;
- preservation of nodes/fields/branches outside RepairClosure.

Potential closure size alone must not justify a broad intervention.

## 6. Hash/adoption boundary

Hash lineage supports exact identity and structural ancestry. Active recovery decisions require relation evidence and a named authority/provenance condition, not hash reachability alone.

## 7. Post-repair verification

Verify separately:

- repair revision activation;
- residual evidence-supported old lineage;
- structurally reachable but not adopted old lineage;
- old-lineage re-entry;
- preserved structure unchanged;
- replay-only dependencies restored/released correctly.

## 8. Recovery interface boundary

The observer/protocol may be framework-agnostic for observation and indexing, but active repair requires adapters to native state, replay, reopen and execution interfaces.

Protocol-agnostic is therefore a design target for the common integrity layer, not a claim that every recovery operation is implementation-independent.

## 9. No target answer

Repair authority/provenance/process integrity, not a desired terminal answer.

## 10. Authorization

No provider/evaluator/active scientific recovery authorization.
