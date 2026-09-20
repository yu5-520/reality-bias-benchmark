# NMI-P4 Reviewer + Foundational Attack Status v0.6

Date: 2026-09-21  
Status: **P4 ACTIVE / RA06 REPAIR-RERUN + SAME-ENDPOINT HARDENED**

Canonical manuscript:

`docs/submission/nmi/NMI_Manuscript_v0.7.md`

## RA06 — repair-is-rerun / same-endpoint attack

### Attack A

> Is structured repair merely a prompt correction or rerun?

Frozen answer:

- R7-P and R7-S are separate control surfaces;
- R7-P repeatedly corrects downstream reader-visible semantics while inherited state remains intact;
- R7-S acts on an addressable lineage and affected closure;
- R7-S can invalidate descendants, reopen dependent recipients and selectively recompute only the bounded closure;
- compatible/unrelated state is preserved.

Four canonical R7-S cases:

- preservation: **4/4**;
- reopened calls: **8 / 8 / 8 / 8**;
- recomputed descendants: **43 / 35 / 28 / 29**.

Conclusion:

> **Selective lineage recomputation is not equivalent to a whole-run rerun.**

### Attack B

> If the endpoint remains the same, did repair do nothing?

Frozen outcomes:

- material divergence: **2/4**;
- compatible reconvergence: **2/4**.

In `wave-4-cf726639de1d`, R7-S reopens 8 calls and recomputes 28 descendants before returning to the same broad 900-unit staged plan.

The exact logistics fact later re-enters, but its authority is regenerated from fresh post-repair logistics evidence rather than blind restoration.

Conclusion:

> **Endpoint equality is not sufficient to judge whether the process lineage changed.**

A valid repair may produce:

- material divergence; or
- compatible reconvergence from a repaired/freshly re-anchored lineage.

## Manuscript hardening

Manuscript v0.7 now explicitly states:

- R7-S is not a blind rerun;
- 4/4 compatible/unrelated structure preservation;
- 2/4 divergence and 2/4 reconvergence;
- same endpoint can be reconstructed from a different and better-supported lineage;
- repair should be evaluated at lineage/recomputation level rather than endpoint inequality alone.

Current word budget:

- abstract: 147 words;
- main text before Methods: approximately 3,275 words;
- tracked Article ceiling: 3,500 words.

## Remaining P4 priority

1. recursive Monitor/Repair governance foundational attack;
2. Inter-System overreach wording;
3. limited-model external-validity wording;
4. NMI breadth/editorial significance.

P6 reproducibility blocker remains unchanged.

No new subject run, provider call, evaluator call, semantic adjudication or raw-evidence mutation is authorized.
