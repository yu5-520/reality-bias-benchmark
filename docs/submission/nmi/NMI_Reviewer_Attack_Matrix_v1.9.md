# NMI Reviewer and Foundational Attack Matrix v1.9

Date: 2026-09-21  
Status: **P4 ACTIVE / RA08 SUBJECT-MODEL EXTERNAL VALIDITY HARDENED**  
Predecessor: `docs/submission/nmi/NMI_Reviewer_Attack_Matrix_v1.8.md`

| Class | Attack | Status |
| --- | --- | --- |
| Reviewer 03 | Semantic audit subjective / post-hoc | **HARDENED / LIMITATION RETAINED** |
| Reviewer 04 | Ordinary propagation / failure-taxonomy reduction | **HARDENED** |
| Reviewer 05 | R5 one-shot causality | **HARDENED** |
| Reviewer 06 | Repair is rerun / same endpoint | **HARDENED** |
| Reviewer 07 | Inter-System overreach | **HARDENED / OUTLOOK BOUNDARY** |
| **Reviewer 08** | **Limited subject-model/provider coverage** | **HARDENED / EXTERNAL-VALIDITY LIMITATION EXPLICIT** |
| Foundational 01 | Structural scout omission | **CALIBRATED** |
| Foundational 02 | Future capability absorption | **THEORY BOUNDARY HARDENED** |
| Foundational 03 | Monitor/Repair recursive governance | **THEORY SELF-CONSISTENCY HARDENED** |
| Reviewer | NMI breadth/editorial significance | OPEN |
| Reproducibility | Corrupted R8 repository gzip | **P6 BLOCKER / RECOVERY IDENTIFIED** |

## RA08 boundary

Core formal subject evidence uses one frozen DeepSeek subject configuration:

`deepseek-flash / expected DeepSeek-V4.1-Flash`.

The 90 held-out natural trajectories deliberately lock the same model/provider across Finance, Supply Chain and Software Engineering.

Therefore:

> **cross-domain != cross-model robustness**

Historical cross-model semantic review is a measurement-reliability experiment, not subject-model replication.

Canonical guard:

> **cross-model review != cross-model subject replication**

Current support:

- domain variation: SUPPORTED;
- stochastic process variation: SUPPORTED;
- subject-model robustness: NOT ESTABLISHED;
- provider robustness: NOT ESTABLISHED;
- topology robustness: NOT ESTABLISHED;
- memory-architecture robustness: NOT ESTABLISHED;
- independent external replication: NOT COMPLETE.
