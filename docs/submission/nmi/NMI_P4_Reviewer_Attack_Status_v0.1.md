# NMI-P4 Reviewer Attack Status v0.1

Date: 2026-09-20  
Status: **P4 ACTIVE / STRUCTURAL-SCOUT ATTACK CLOSED WITH CALIBRATION**

Canonical hardened manuscript:

`docs/submission/nmi/NMI_Manuscript_v0.2.md`

## Closed attack: structural pre-screening omission

Question:

> How do we know structural pre-screening did not omit semantically important process-reality problems?

Frozen-data answer:

- same held-out natural cohort: 90 trajectories;
- structural candidate rows: 2,127;
- broad deterministic triage cases: 167;
- candidate-surface compression: 92.1486%;
- later full-trajectory R8 P-supported: 13;
- later full-trajectory R8 R-supported: 12;
- unique later P-or-R-supported: 13;
- earlier narrow B2 union structural selector captures 10/13 = 76.9231%;
- conditional miss = 3/13 = 23.0769%;
- P-specific selector captures 4/13 = 30.7692%;
- R-specific selector captures 9/12 = 75.0%;
- broad triage preserves post-late-event structural evidence in 13/13 later P/R-supported trajectories.

Interpretation:

> The broad structural layer preserved access to the relevant process regions, while narrower rules built on reviewer/new-Agent proxies missed some semantic mechanisms.

Therefore:

> **Structural scouting is a localization layer, not the semantic verdict layer.**

## Manuscript hardening

Manuscript v0.2 adds:

1. a Methods subsection, `Structural pre-screening calibration`;
2. a Discussion paragraph explaining selector miss versus evidence preservation;
3. explicit conditional-denominator language preventing the 23.08% result from becoming a universal miss-rate claim.

Current word budget:

- abstract: 147 words;
- main text before Methods: approximately 2,565 words;
- official ceiling: 3,500 words.

Substantial editorial reserve remains.

## New P6 blocker

P4 also discovered that the repository copy of the 141-record R8 gzip does not match the frozen manifest and is not gzip-readable.

A previously frozen external package was recovered and matches the frozen compressed and uncompressed SHA-256 values exactly.

P6 must:

- append the valid recovered copy;
- preserve the old corrupted repository object;
- publish an integrity/recovery note;
- make the reproducibility path use the recovered canonical object.

## Remaining P4 attacks

Still open:

- failure-taxonomy reduction;
- ordinary information-propagation reduction;
- semantic-review subjectivity;
- post-hoc / selection-bias attack;
- limited model coverage;
- R5 causal-boundary attack;
- repair-is-rerun attack;
- same-endpoint repair attack;
- Inter-System overreach;
- NMI breadth / editorial significance.

No new experiments are authorized by P4.
