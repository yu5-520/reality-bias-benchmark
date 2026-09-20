# NMI-P4 Reviewer Attack 06 — Repair-is-Rerun and Same-Endpoint Attack

Date: 2026-09-21  
Status: **ENGINEERING REDUCTION ATTACK HARDENED / ENDPOINT METRIC BOUNDED / NO NEW EXECUTION**

## Attack questions

> Is R7-S merely a prompt correction or rerun with extra bookkeeping?

and

> If a repaired trajectory returns to the same broad endpoint, does that mean the repair had no effect?

These attacks target the engineering meaning of lineage-level repair.

The correct test is not whether the final answer differs. It is whether the repair operator acts on a different control surface from prompt-time correction and whether the affected process lineage is actually invalidated, reopened and recomputed while unrelated state is preserved.

## 1. R7-P and R7-S are different control surfaces

The frozen engineering stack separates:

### R7-P — persistent reader-surface correction

R7-P repeatedly changes what downstream readers see.

Its defining property is:

- inherited shared state remains intact;
- uncertainty/correction is re-exposed to downstream readers;
- the repair does not invalidate the stored semantic lineage.

This is the closest arm to a persistent prompt-visible correction.

### R7-S — internal lineage repair

R7-S instead acts on the internal semantic process object:

`repair anchor`
-> `affected closure`
-> `invalidate affected descendants`
-> `reopen dependent recipients`
-> `selectively recompute`
-> `preserve compatible/unrelated state`
-> `watch re-entry`.

Therefore:

> **R7-S != prompt correction**

and:

> **R7-S != whole-run rerun**.

A whole-run rerun discards the realized process and samples a new stochastic trajectory from an earlier start.

R7-S preserves the unaffected prefix and compatible memory, re-executing only the bounded dependency closure supported by the lineage package.

## 2. Four-case frozen repair geometry

The four canonical R7-S cases with complete R6 packages show:

| Case | Invalidated refs | Reopened calls | Recomputed descendants | Engineering outcome |
| --- | ---: | ---: | ---: | --- |
| `wave-3-56ee79f97f54` | 1 | 8 | 43 | parameter divergence |
| `wave-4-8b1731b57396` | 1 | 8 | 35 | action recomposition |
| `wave-4-cf726639de1d` | 0 | 8 | 28 | reconvergence with fresh authority regeneration |
| `wave-6-7c7e526e4d91` | 1 | 8 | 29 | compatible decision reaffirmation |

Across all four:

- compatible/unrelated structure preserved: **4/4**;
- material divergence after repair: **2/4**;
- compatible reconvergence after recomputation: **2/4**.

The repair therefore changes less than a full rerun and more than a prompt annotation.

## 3. Why preservation is evidence against the “just rerun” reduction

If R7-S were merely a rerun, preservation would not be an explicit engineering invariant of the operator.

Instead the repair package binds:

- target semantic identifier;
- content address;
- source provenance;
- authority history;
- semantic descendants;
- evidence-supported affected closure;
- repair closure.

Only dependent recipients are reopened.

Unrelated/compatible state is intentionally retained.

The observed 4/4 preservation result is therefore relevant to the reduction attack:

> the operator is designed and observed to act selectively on an addressable dependency structure rather than reset the entire run.

This does not prove an optimal minimal repair boundary, but it does falsify the simple description “the whole run was just rerun.”

## 4. Why endpoint equality is not a null result

A terminal-only metric would classify:

`same endpoint before/after repair -> no effect`.

The frozen process evidence shows why this inference is invalid.

### Material-divergence cases

Two of four cases produce a materially different downstream plan after lineage repair.

These demonstrate that the internal intervention can alter executable behavior.

### Reconvergence cases

Two cases recompute the affected process and return to the same broad endpoint.

The clearest example is:

`wave-4-cf726639de1d`.

R7-S:

- reopens 8 calls;
- recomputes 28 descendants;
- returns to the broad 900-unit staged plan;
- later observes the exact logistics fact re-entering.

The re-entry is not classified as blind restoration of the old authority.

It is supported by fresh post-repair logistics evidence.

Thus:

`same broad endpoint`

can coexist with:

`different semantic ancestry + actual recomputation + fresh authority basis`.

The endpoint has reconverged; the process has not remained untouched.

## 5. Repair success is multi-dimensional

For this paper, a repair cannot be evaluated solely by whether the final answer changes.

Relevant process-level dimensions include:

- was the target lineage actually revised?
- were affected descendants invalidated or reopened?
- was the bounded closure recomputed?
- was unrelated state preserved?
- did superseded authority re-enter?
- if it re-entered, was that blind restoration or fresh re-anchoring?
- did the executable process materially diverge or compatibly reconverge?

Accordingly:

> **endpoint inequality is neither necessary nor sufficient for lineage-level repair.**

A changed endpoint could arise from stochastic rerolling without a valid repair.

A same endpoint can arise from valid reconstruction after repair.

## 6. What the evidence does not establish

The four canonical cases do not establish:

- universal superiority of R7-S over R7-P;
- universal repair success;
- optimality of the affected closure;
- stability beyond the observed horizon;
- cross-model repair robustness;
- that every reconvergence is healthy;
- that endpoint accuracy is irrelevant.

The result is narrower:

> **lineage-addressed selective repair is technically and empirically distinguishable from persistent prompt correction and whole-run rerolling in the frozen cases.**

## 7. Manuscript consequence

The manuscript should preserve three explicit boundaries:

> **persistent correction != internal lineage repair**

> **selective lineage recomputation != whole-run rerun**

> **same endpoint != no process-level repair effect**

and should retain:

> universal R7-S superiority = NOT ESTABLISHED.

## Verdict

Attack 1:

**“Repair is just prompt correction / rerun.”**

Verdict:

**NOT SUPPORTED AS A COMPLETE REDUCTION.**

Attack 2:

**“Same endpoint means repair did nothing.”**

Verdict:

**NOT SUPPORTED BY THE PROCESS EVIDENCE.**

The frozen repair trajectories support a narrower engineering claim:

> An addressable semantic lineage can be revised and its bounded descendants selectively recomputed while compatible state is preserved; the resulting process may materially diverge or compatibly reconverge.
