# CN-R-060 — Semantic-Lineage Scoped Repair

Date: 2026-09-18  
Status: FORWARD THEORY / ENGINEERING-SCOPE REFINEMENT / NO SCIENTIFIC RUN AUTHORIZATION

## Trigger

Process Reality v5 established a distinction between semantic formation, structural support, stable shared pools and structural exposure.

The second-pass semantic/mechanism re-audit then clarified that later stable shared-pool existence can be supported even when the first support point or first pool-entry event remains unknown.

This creates an engineering consequence:

A repair protocol does not need to reconstruct every semantic branch in the whole task, and it does not need to localize the globally earliest semantic origin before intervention.

However, repair must not operate on an incomplete history of the **target semantic object**. A repair Agent that sees only the current abnormal state may reconstruct missing meaning, assumptions or causes and thereby create a new Reality Bias.

## Decision

Forward engineering adopts **semantic-lineage scoped repair**.

Locality is defined as:

`LOCAL_BY_SEMANTIC_SCOPE`

not:

`LOCAL_BY_TRACE_DEPTH`.

A repair scope may traverse the full temporal depth of one relevant semantic lineage while excluding unrelated semantic branches.

## Core chain

```text
Structural Scout
  -> Structural Repair Anchor
  -> Content Address
  -> Semantic Lineage Closure
  -> Lineage Completeness Gate
  -> Localized Semantic Audit
  -> Repair Closure
  -> Invalidate / Revise / Recompute
  -> Recovery Verification
```

## Structural Repair Anchor

A Structural Repair Anchor is a sufficiently exposed, machine-addressable and repair-efficient structural node used as the engineering entry point.

It is selected for control efficiency, not causal primacy.

A Repair Anchor may be:

- later than semantic genesis;
- later than the first Structural Support point;
- later than the first Stable Shared Pool entry.

Historical Jump/J0 may be interpreted as a Repair Anchor candidate when its structural identity, descendants and content address make it cheap to scout and repair.

## Content addressing

The Repair Anchor provides a stable entry ID.

Content addressing retrieves the complete **relevant** semantic history for the target object:

- source proposition;
- source epistemic state;
- semantic transformations;
- cross-Agent adoption;
- authority transitions;
- shared-pool materializations;
- revisions;
- rejected/abandoned relevant branches;
- downstream semantic descendants;
- affected constraints/actions.

Unrelated semantic branches are excluded.

## Semantic Lineage Closure

For target semantic object `s`:

```text
SemanticLineageClosure(s)
  = RelevantAncestors(s)
  ∪ RelevantTransformations(s)
  ∪ RelevantAuthorityTransitions(s)
  ∪ RelevantPoolStates(s)
  ∪ RelevantSemanticDescendants(s)
```

The closure is allowed to span the entire run.

It is "local" because it is semantically scoped, not because it is temporally shallow.

## Lineage Completeness Gate

Automatic repair requires sufficient completeness of the relevant semantic lineage.

```text
minimize(UnrelatedContext)
subject to Completeness(RelevantSemanticLineage) >= threshold
```

If critical lineage evidence is missing, the system must emit `LINEAGE_GAP` or an equivalent unresolved status.

A repair Agent must not reconstruct missing semantic lineage as historical fact.

## Scientific / engineering separation

The first paper now separates:

1. **Theory experiment layer** — how Process Reality forms and persists.
2. **Engineering experiment layer** — how a repairable structural anchor can address the complete relevant semantic lineage and support localized repair.
3. **Future discussion layer** — how this could generalize into a portable Process Integrity Protocol.

First-support and first-pool-entry localization remain scientifically useful mechanism observables. They are not mandatory prerequisites for engineering repair.

## Nonclaims

This change does not claim:

- that historical J0 is the universal optimal Repair Anchor;
- that every exposure anchor is safely repairable;
- that semantic lineage can always be made complete;
- that content hashes establish semantic use;
- that current evidence establishes R7 repair efficacy.

## Authorization

This change note authorizes no provider call, evaluator call, active recovery or CPR adjudication.
