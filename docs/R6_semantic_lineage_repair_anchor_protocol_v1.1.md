# R6 Repair Anchor and Semantic-Lineage Localization Protocol v1.1

Date: 2026-09-18  
Status: FORWARD v5.1 / ENGINEERING IDENTIFICATION LAYER / NO ACTIVE REPAIR AUTHORIZATION  
Predecessor: `docs/R6_structural_support_trace_control_surface_protocol_v1.0.md`

## 1. Purpose

R6 identifies a repair-efficient structural entry point and reconstructs the complete relevant semantic lineage for the target problem.

R6 does **not** require all task semantics and does **not** require localization of the globally earliest semantic origin.

## 2. Structural Repair Anchor

R6 may select a Structural Repair Anchor when a node is sufficiently:

- exposed;
- addressable;
- provenance-bound;
- descendant-visible;
- cheap to scout;
- suitable for bounded repair.

Selection criterion:

`repair efficiency`

not:

`causal primacy`.

## 3. Content addressing

From the Repair Anchor, R6 resolves content identity and follows recorded provenance/relation evidence both upstream and downstream.

Target:

`complete relevant lineage`

not:

`complete task history`.

## 4. Semantic Lineage Closure

R6 builds:

- relevant source refs;
- relevant semantic-transformation refs;
- adoption/coupling refs;
- authority-transition refs;
- pool-state refs;
- relevant revision refs;
- evidence-supported descendant refs;
- rejected/abandoned relevant branch refs;
- raw evidence refs.

This forms `SemanticLineageClosure`.

## 5. Unrelated semantics

R6 must explicitly exclude structurally nearby but semantically unrelated branches when evidence supports their exclusion.

A branch is not included merely because it is temporally adjacent or reachable in the global task graph.

## 6. Lineage Completeness Gate

Before R7 handoff, R6 evaluates relevant-lineage completeness.

Minimum dimensions:

- source bound;
- transformation history sufficiently bound;
- authority history sufficiently bound;
- current pool/state identity bound;
- affected descendant set sufficiently bound;
- evidence pointers available.

Allowed outcomes:

- `COMPLETE_FOR_AUTHORIZED_REPAIR`;
- `COMPLETE_FOR_AUDIT_ONLY`;
- `LINEAGE_GAP`;
- `UNRESOLVED`.

If `LINEAGE_GAP`, R6 must not ask a Repair Agent to guess the missing history.

## 7. Repair Anchor versus Trace Root

The following may differ:

`Repair Anchor != Trace Root != Earliest Semantic Origin`

R6 may trace all the way to the source when the target lineage requires it.

The efficiency gain comes from content-addressed scoping, not from truncating relevant history.

## 8. Handoff to R7

R6 hands R7:

- repair_anchor_ref;
- target_semantic_id;
- semantic_lineage_closure;
- lineage_completeness_status;
- evidence-supported affected closure;
- candidate repair surfaces;
- selected repair surface if frozen;
- mechanically required replay dependencies;
- preserved unrelated refs;
- unresolved gaps.

## 9. Authorization

R6 localization authorizes no active repair.
