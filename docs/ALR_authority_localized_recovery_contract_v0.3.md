# ALR Authority-Localized Recovery Contract v0.3

Date: 2026-09-17  
Status: FORWARD OPERATOR CONTRACT / NO PAID RUN AUTHORIZATION  
Predecessor: `docs/ALR_authority_localized_recovery_contract_v0.2.md`

## 1. Purpose

ALR remains **Authority-Localized Recovery**: a causally localized structural recovery operator.

v0.3 adds one important requirement: ALR should consume an R6-identified carrier/closure where available rather than infer contamination from terminal failure or generic trajectory difference.

## 2. Recovery anchor

Preferred anchor:

> the earliest source-backed ancestor `n*` at which a named authority/provenance condition was violated and from which a downstream carrier/closure can be reconstructed.

A valid anchor requires:

- frozen condition id;
- source evidence refs;
- before/after authority/provenance state;
- carrier/dependency relation version;
- reproducible localization rule.

If not resolvable, status remains `UNRESOLVED`.

## 3. Affected closure

Define:

- `Affected = DependencyClosure(n*)`;
- `Preserved = RealizedGraph - Affected`.

The closure may follow preregistered message, state, invocation, evidence, revision, handoff and re-entry edges.

The affected set must not expand by reviewer intuition.

## 4. Preservation rule

Unaffected structure remains preserved by default.

Do not reopen an Agent, branch or state merely because it participated in the same task. Reopen only nodes/fields in the source-backed affected closure or those required by the frozen local-reexecution semantics.

## 5. Repair rule

Repair the violated authority/provenance condition, not the desired final answer.

Possible repair actions include:

- downgrade unsupported factual authority;
- restore missing provenance;
- replace a stale/invalid source reference;
- reopen a prematurely settled state;
- revise an unauthorized invocation/commit boundary.

The repair payload must contain no extra task-solving content beyond what is necessary to change the violated condition.

## 6. Content-addressed revision identity

Where runtime support exists, every recovery should produce an auditable revision chain:

- prior `FieldHash` / `StateHash` / `RevisionHash`;
- repaired hash;
- parent revision ref;
- recovery operation id;
- authority-condition id;
- source refs;
- affected-closure hash;
- preserved-set hash;
- reopen-plan hash.

Historical predecessors must remain queryable. Repair is a new revision, not silent overwrite.

## 7. Real-time localization compatibility

ALR may be implemented on top of a runtime observer that registers content identity and lineage as events occur.

The observer layer is passive. ALR activation is a separate authorized operation.

The operator must therefore support:

`passive observation -> source-backed localization -> explicit recovery activation -> local revision/reopen -> free continuation -> lineage verification`

## 8. Post-repair verification

After recovery, verify:

- repaired revision became the active descendant where intended;
- old lineage no longer produces unauthorized descendants, or residual/re-entry is explicitly recorded;
- preserved nodes remained unchanged;
- reopened nodes are exactly those permitted by the closure/reopen plan;
- new descendants retain source/revision refs.

## 9. Proposal-versus-realization record

When ALR prevents or changes realization, retain:

- original proposal;
- intervention decision;
- realized action/state;
- source condition causing the intervention;
- resulting lineage.

## 10. Relationship to R7

ALR is the C3 operator inside R7. R7 is broader and asks whether localized structural recovery reduces risk-bearing inertia while preserving process freedom.

ALR does not define all structural control and does not itself prove controllability.

## 11. Relationship to CPR

ALR does not adjudicate C/P/R. It operates on a named authority/provenance condition supplied by the experimental/recovery contract.

Semantic CPR status remains an R8 append-only review result.

## 12. Engineering qualities

A production-oriented implementation should aim to be:

- lightweight;
- pluggable;
- framework/protocol agnostic;
- passive by default;
- content-addressed;
- lineage-aware;
- local in repair scope;
- reversible/auditable.

These are engineering design targets, not experimentally established scientific conclusions until tested.

## 13. Authorization

This contract authorizes no provider call, paid evaluator call or semantic adjudication.
