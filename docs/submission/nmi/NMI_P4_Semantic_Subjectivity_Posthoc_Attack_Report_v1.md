# NMI-P4 Reviewer Attack 03 — Semantic Subjectivity and Post-hoc Selection

Date: 2026-09-20  
Status: **REAL LIMITATION CONFIRMED / CLAIM MODE HARDENED / NO NEW SEMANTIC ADJUDICATION**

## Attack question

> Are Dynamic C/P/R findings merely a post-hoc semantic interpretation of trajectories selected after the theory was known?

This attack combines two related reviewer concerns:

1. **semantic-review subjectivity** — the final verdict requires interpretation rather than a purely mechanical rule;
2. **post-hoc / cherry-picking risk** — the theory or rubric may have been adjusted after observing the data and then applied selectively to favourable cases.

The correct defence is not to claim that the audit was preregistered or objective. It was not.

The defence must separate four different sources of researcher freedom and audit each one.

## 1. Chronology audit

### Held-out natural subject generation

The complete cross-domain first round ran as workflow:

`35370679448`

with execution SHA:

`b712dabc227973470900af4aea4e13d1077f5696`.

The run started on 2026-09-18 at 16:48:51 UTC and completed at 17:29:48 UTC.

It preserved:

- 90 / 90 natural trajectories;
- 30 Finance;
- 30 Supply Chain;
- 30 Software Engineering;
- zero runner errors.

### Deterministic triage

The deterministic cross-domain triage protocol was committed after the subject run:

- commit: `8f1a8d68d0098868e31fdcbf9241346f28b3dd59`;
- commit time: 2026-09-18 17:51:37 UTC.

The protocol explicitly prohibited triage from establishing:

- semantic adoption;
- authority error;
- semantic transformation;
- semantic inheritance;
- System Inertia;
- CPR;
- causality;
- R5 eligibility;
- R7 repairability.

Thus triage was post-generation, but it was an evidence-localization operation rather than a semantic verdict.

### Final trajectory-first R8 protocol

The canonical R8 v0.5 protocol was committed later:

- commit: `2b19294211ffab90712845ee73cefc5cb33e0951`;
- commit time: 2026-09-20 06:36:58 UTC.

This protocol replaced the earlier window-first R8 approach with:

`complete trajectory -> dynamic semantic reconstruction -> functional semantic lineage -> C/P/R adjudication -> coupling`.

The combined R8 audit was then frozen at:

- commit: `8bef82f3737fb4b8af9639ee8c47acbf17b80fdd`;
- commit time: 2026-09-20 07:41:56 UTC.

### Chronology verdict

The canonical semantic rubric was **not preregistered before subject generation**.

Therefore:

> **R8 is a retrospective mechanism audit, not a preregistered confirmatory study.**

Any manuscript wording that implies otherwise is invalid.

## 2. Four post-hoc risk channels

### A. Hypothesis/rubric evolution

**Risk: REAL.**

The final trajectory-first rubric was developed after the natural evidence existed and after earlier narrower audit attempts exposed limitations.

This creates legitimate construct-level researcher degrees of freedom.

Mitigation:

- versioned protocols remain in repository history;
- legacy narrow-window products are not overwritten;
- the paper reports the final audit as retrospective;
- the combined inventory is not used for a confirmatory prevalence claim.

Residual limitation:

> Independent replication under a frozen rubric remains necessary.

### B. Outcome-conditioned trajectory selection

**Risk: STRONGLY REDUCED FOR THE 90 HELD-OUT NATURAL COHORT.**

The later R8 audit consumed the complete held-out natural cohort:

- Finance: 30 / 30;
- Supply Chain: 30 / 30;
- Software Engineering: 30 / 30.

The semantic stage did not review only the trajectories selected by the earlier B2 high-risk rules.

This matters because the structural-scout calibration later showed that the B2 rules themselves missed some P/R-supported trajectories. Full-cohort review therefore prevents the old selector from defining the semantic-positive population.

Residual limitation:

The 90 trajectories are still one generated experimental cohort, not a population sample for universal prevalence.

### C. Outcome-conditioned stochastic rerunning

**Risk: NOT OBSERVED IN THE CANONICAL R8 RE-AUDIT.**

The final trajectory-first audit re-used frozen subject trajectories.

The source registry and R8 report bind:

- new subject reruns: 0;
- raw evidence mutation: false.

The study therefore did not repeatedly regenerate natural trajectories until the final theory reappeared.

This is important because stochastic rerunning after observing an outcome would blur discovery and confirmation.

### D. Semantic verdict discretion

**Risk: REAL AND NOT ELIMINATED.**

C/P/R are semantic constructs. Structural records can prove chronology, state transitions, messages, invocations and provenance, but they cannot mechanically determine all questions of:

- carried functional meaning;
- whether a scope extension was necessary or separately authorized;
- whether uncertainty remained operationally attached;
- whether a retrospective continuation generated new process permission.

The v0.5 protocol limits this discretion by requiring the following order before verdict:

1. trajectory reconstruction;
2. semantic episode list;
3. functional lineage map;
4. goal / authorization / realized-process / result alignment;
5. retrospective / censor timeline;
6. C;
7. P;
8. R;
9. coupling;
10. unresolved evidence;
11. claim boundary.

It also allows non-positive outcomes including:

- `NOT_ESTABLISHED`;
- `HEALTHY_REANCHOR`;
- `UNRESOLVED`;
- `CENSORED_UNRESOLVED`.

These constraints make a verdict auditable against frozen evidence, but they do not make it reviewer-independent.

Independent blinded semantic replication remains incomplete.

## 3. Why healthy comparators matter

A post-hoc theory is especially vulnerable if every observed continuation can be redescribed as confirming evidence.

The R8 protocol explicitly preserves alternatives that do **not** count as CPR:

- uncertainty-preserving descendants;
- fresh independent re-anchoring;
- necessary specialist decomposition;
- reopen/recompute without generated C/P;
- compatible reconstruction after repair;
- structural recurrence without restored authority;
- active censoring.

This creates semantic negative space.

The theory therefore does not define:

`any continuation = Reality Bias`.

It instead requires a stricter permission transition.

## 4. Relation to Foundational Attack 01

Foundational Attack 01 showed that a narrow structural selector captured only 10/13 trajectories later supported for P and/or R, while broader structural packets preserved relevant post-late evidence in 13/13.

Reviewer Attack 03 explains why the solution cannot be to replace semantic review with a more aggressive structural rule.

The correct separation is:

`frozen structural evidence`
-> `recall-oriented localization`
-> `complete-trajectory reconstruction`
-> `semantic adjudication with explicit alternatives`.

The structural layer constrains where and when events happened.

The semantic layer remains interpretive.

## 5. Manuscript consequence

The manuscript must state explicitly that:

1. the canonical R8 rubric was finalized after natural subject generation;
2. R8 is retrospective mechanism analysis;
3. the complete 90-trajectory held-out cohort was re-reviewed rather than only positive-looking trajectories;
4. natural subject trajectories were not outcome-conditionally regenerated;
5. healthy alternatives and non-positive verdicts are part of the protocol;
6. independent blinded reviewer replication is still missing.

The paper should not use:

- “preregistered”;
- “objective semantic detector”;
- “unbiased prevalence estimate”;
- “reviewer-independent ground truth”.

## 6. What this attack does and does not close

### Hardened

The evidence supports a defence against the strongest cherry-picking interpretation:

> The final semantic theory was not evaluated only on a hand-picked positive subset, and the stochastic subject runs were not regenerated to match the final theory.

### Not closed

The evidence does **not** eliminate:

- retrospective construct formation;
- semantic reviewer discretion;
- researcher degrees of freedom in evolving the rubric;
- need for independent blinded semantic replication;
- need for future prospective validation under a frozen audit contract.

## Verdict

Attack:

**“The semantic findings are subjective and post-hoc.”**

Verdict:

**PARTLY SUPPORTED AS A REAL LIMITATION, BUT THE FAILURE MODE IS NARROWER THAN ‘CHERRY-PICKED RESULTS’.**

The final audit is retrospective and reviewer-dependent.

However, the complete held-out natural cohort is retained and reviewed, subject trajectories remain frozen, legacy analyses remain visible, outcome-conditioned natural rerunning is absent, and the protocol preserves healthy/non-positive alternatives.

Paper-level consequence:

> **Treat R8 as traceable retrospective mechanism evidence, not preregistered prevalence confirmation.**
