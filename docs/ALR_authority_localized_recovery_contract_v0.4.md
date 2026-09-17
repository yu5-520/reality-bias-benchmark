# ALR Authority-Localized Recovery Contract v0.4

Date: 2026-09-17  
Status: FORWARD OPERATOR CONTRACT / THREE-CLOSURE MODEL / NO PAID RUN AUTHORIZATION  
Predecessor: `docs/ALR_authority_localized_recovery_contract_v0.3.md`

## 1. Recovery anchor

Preferred anchor remains the earliest source-backed ancestor `n*` where a named authority/provenance condition was violated.

## 2. Potential closure

`PotentiallyAffectedClosure = DependencyClosure(n*)`

This is the structurally reachable upper bound used for scouting.

## 3. Evidence-supported affected closure

`EvidenceSupportedAffectedClosure` contains only descendants with frozen source-backed dependence evidence, such as delivery/read, semantic adoption, inherited state/action or propagation.

A node does not enter this set merely because a hash/edge makes it reachable.

## 4. Replay dependencies

`MechanicallyRequiredReplayDependencies` contains nodes needed to execute the frozen local reopen/replay semantics even when they are not semantically affected.

These nodes must be tagged `REPLAY_DEPENDENCY_ONLY`.

## 5. Repair closure

`RepairClosure = EvidenceSupportedAffectedClosure union MechanicallyRequiredReplayDependencies`

The operator must preserve all other realized structure by default.

## 6. Repair rule

Repair the violated authority/provenance condition, not the desired answer.

## 7. Relation evidence

Each active inclusion in EvidenceSupportedAffectedClosure should reference one or more relation-evidence records. If evidence is unresolved, the node remains potential/unresolved rather than silently promoted.

## 8. Content-addressed identity

Hashes remain mandatory for identity/revision where runtime support exists, but hash ancestry is not a semantic-adoption proof.

## 9. Endogenous state

The experiment/recovery operator may avoid direct persistent mutation while the subject system itself naturally writes state. Subject-generated persistence remains observable lineage and may become part of the affected set if evidence supports dependence.

## 10. Verification

After repair verify:

- active repaired revision;
- old lineage re-entry;
- evidence-supported residual descendants;
- potential-only descendants;
- replay-only dependencies;
- preserved nodes unchanged.

## 11. Authorization

No provider/evaluator/semantic-adjudication authorization.
