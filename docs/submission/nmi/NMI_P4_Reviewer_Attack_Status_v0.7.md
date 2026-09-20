# NMI-P4 Reviewer + Foundational Attack Status v0.7

Date: 2026-09-21  
Status: **P4 ACTIVE / FA03 RECURSIVE MONITOR-REPAIR GOVERNANCE HARDENED**

Canonical manuscript:

`docs/submission/nmi/NMI_Manuscript_v0.8.md`

## Foundational Attack 03

Question:

> Can the integrity layer itself create the same Process Reality failure it is meant to control?

Answer:

> **Yes, if detection, semantic verdict, repair authorization and write execution collapse into one authority surface.**

The forward governance chain is:

`Observed system -> Process Reality Monitor -> semantic adjudication -> Repair Authority Gate -> bounded Repair Agent -> selective recomputation -> re-entry watch`.

The theory now explicitly requires:

- detection is not authority;
- monitor read access is not repair write access;
- semantic verdict is not repair authorization;
- repair authorization is not global write authority;
- re-entry is not renewed authority.

This is recursively applicable without requiring infinite monitor nesting; least-authority interfaces, immutable audit records, explicit capabilities and institutional authorization can terminate the stack.

## Evidence boundary

R7-S supports bounded lineage-repair feasibility (4/4 preservation, 2/4 divergence, 2/4 reconvergence). It does not validate a production Monitor/Repair governance stack.

## Manuscript budget

- abstract: 147 words;
- main text before Methods: approximately 3,314 words;
- tracked ceiling: 3,500 words.

## Remaining P4 priority

1. Inter-System Process Reality overreach;
2. limited-model external validity;
3. NMI breadth/editorial significance.

P6 reproducibility blocker remains unchanged.
