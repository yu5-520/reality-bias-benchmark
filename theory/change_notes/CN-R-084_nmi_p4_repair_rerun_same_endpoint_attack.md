# CN-R-084 — P4 Repair-Rerun and Same-Endpoint Attack

Date: 2026-09-21  
Status: **ACCEPTED / ENGINEERING CLAIM HARDENING**

## Attack

Combine two reviewer reductions:

1. R7-S is only prompt correction / rerun.
2. Same endpoint means repair had no effect.

## Control-surface result

R7-P and R7-S remain distinct.

R7-P:

- persistent reader-surface semantic correction;
- inherited shared state remains intact.

R7-S:

- addressable repair anchor;
- evidence-supported affected closure;
- descendant invalidation where required;
- dependent-recipient reopen;
- selective recomputation;
- compatible/unrelated-state preservation;
- re-entry watch.

Therefore:

> **persistent correction != internal lineage repair**

and:

> **selective lineage recomputation != whole-run rerun**.

## Frozen repair outcomes

Across four canonical R7-S cases:

- compatible/unrelated preservation: 4/4;
- material divergence: 2/4;
- compatible reconvergence: 2/4;
- reopened calls per case: 8;
- recomputed descendants: 43 / 35 / 28 / 29.

The representative reconvergence case `wave-4-cf726639de1d` returns to the same broad plan after 28 descendants are recomputed. Exact fact re-entry is supported by fresh post-repair logistics evidence.

Therefore:

> **same endpoint != no process-level repair effect**.

## Claim boundary

The update does not establish:

- universal R7-S superiority;
- universal repair success;
- optimal affected-closure size;
- cross-model repair robustness.

## Manuscript update

Create append-only manuscript:

`docs/submission/nmi/NMI_Manuscript_v0.7.md`

Main text before Methods: approximately 3,275 words.

Abstract: 147 words.

## Execution boundary

No new subject run, provider call, evaluator call, semantic adjudication or raw-evidence mutation.
