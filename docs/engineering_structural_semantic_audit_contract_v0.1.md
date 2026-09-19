# Engineering Structural Semantic Audit Contract v0.1

Date: 2026-09-20  
Status: **FORWARD ACTIVE / R5-R7 STRUCTURAL ENGINEERING SEMANTICS**

## 1. Purpose

This contract defines the semantic audit used by the R5-R7 engineering-report family.

The audit does **not** ask whether a business-domain answer is globally correct. It asks what a structural intervention means operationally inside the multi-Agent process:

`Probe -> Localize -> Correct-at-reader -> Repair-lineage -> Recompute -> Preserve -> Watch re-entry`

The engineering semantic unit is therefore a **control-surface / lineage / repair operation**, bound to exact frozen process evidence.

## 2. Stage semantics

### R5-I

`TRANSIENT_READER_SURFACE_AUTHORITY_PROBE`

- one-shot `fact -> unconfirmed` exposure;
- persistent shared state is not mutated;
- purpose: diagnose local downstream dependence;
- engineering role: **PROBE_NOT_REPAIR**.

### R6

`LINEAGE_LOCALIZATION_AND_CONTENT_ADDRESSING`

- binds source, transformations, authority history, pool state and affected descendants;
- produces Repair Anchor, content address, Semantic Lineage Closure, Lineage Completeness Gate and repair packet;
- no subject execution;
- engineering role: **REPAIR_READINESS_NOT_REPAIR**.

### R7-P

`PERSISTENT_READER_SURFACE_SEMANTIC_CORRECTION`

- the downstream reader repeatedly sees the target with corrected uncertainty/status;
- inherited shared-state lineage remains internally unchanged;
- purpose: keep correction visible across the common observation horizon;
- engineering role: **EXTERNAL_CORRECTION_NOT_INTERNAL_REPAIR**.

### R7-S

`INTERNAL_LINEAGE_REPAIR_AND_SELECTIVE_RECOMPUTE`

- repairs authority at the exact Repair Anchor;
- invalidates affected post-anchor lineage;
- reopens dependent processing;
- recomputes descendants inside the frozen common horizon;
- preserves compatible/unrelated structure;
- monitors old-lineage re-entry;
- engineering role: **STRUCTURAL_REPAIR**.

## 3. Mandatory engineering-semantic dimensions

Each case audit must explicitly interpret:

1. control surface;
2. repair/localization identity;
3. content addressing;
4. invalidation;
5. reopen;
6. recomputation;
7. preservation;
8. old-lineage re-entry;
9. authority result;
10. endpoint/process relation;
11. common-horizon censoring.

A protocol name by itself is not an engineering semantic interpretation.

## 4. Route-first engineering evidence

R7-P and R7-S must each expose the full realized Agent route under the common eight-post-source-turn horizon.

The audit must retain:

- turn/order;
- Agent;
- decision summary;
- state writes/revisions;
- run status;
- termination reason;
- direct experiment-origin exposure count where applicable.

All eight canonical R7 traces are fixed-horizon censored. This is a designed observation boundary, not a monetary or provider failure.

## 5. Repair-scope evidence

R7-S must bind exact:

- Repair Anchor;
- target semantic ID;
- Lineage Completeness Gate;
- allowed repair operations;
- repair application hash;
- invalidated refs;
- reopened call refs;
- recomputed descendant refs;
- preserved unrelated refs;
- preservation result;
- target final authority/status;
- old-lineage re-entry refs;
- verification hash;
- post-repair watch status.

## 6. Semantic interpretation of re-entry

`exact key/status re-entry != blind restoration`

Structural recurrence is always reported.

If an old target key returns with fact authority, semantic audit must separately determine whether its basis is inherited old authority or fresh evidence produced after repair.

The current `wave-4-cf726639de1d` recurrence is retained as structural re-entry and interpreted, from its frozen evidence, as fresh evidence-based authority regeneration rather than blind restoration.

## 7. Process / endpoint separation

`same endpoint != same engineering process`

R7-S may materially diverge from R7-P or may reconverge on a compatible decision after recomputation.

Reconvergence does not mean the repair did nothing. Divergence does not establish that the repaired branch is better.

## 8. Structural recomputation / semantic novelty separation

`structural recomputation != semantic novelty`

Reopened and recomputed nodes may reaffirm compatible information, decisions or plans. The audit must report whether the recomputed branch:

- materially changes parameters/actions; or
- reconstructs a compatible endpoint using repaired lineage.

## 9. Canonical evidence geometry

Per qualified case:

`N0 frozen + R5-I frozen + R6 passive lineage package + R7-P once + R7-S once`.

No canonical replicate aggregation is used to determine engineering success.

## 10. Claim boundaries

The engineering audit does not establish:

- universal superiority of R7-S over R7-P;
- problematic bias;
- unique R5 causality;
- domain prevalence;
- CPR.

CPR remains `NOT_ADJUDICATED`.

## 11. Report handoff

A major R5-R7 engineering report case must bind a validated:

`RB-ENGINEERING-STRUCTURAL-SEMANTIC-AUDIT-v0.1`

record.

The report should treat the realized structural operation and its engineering semantic meaning as the main content; aggregate structural metrics remain supporting evidence.
