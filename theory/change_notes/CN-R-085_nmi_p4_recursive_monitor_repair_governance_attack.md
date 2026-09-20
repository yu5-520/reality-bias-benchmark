# CN-R-085 — P4 Recursive Monitor/Repair Governance Foundational Attack

Date: 2026-09-21  
Status: **ACCEPTED / THEORY SELF-CONSISTENCY HARDENING**

FA03 establishes that the Monitor/Repair layer can itself create C/P/R-like failures if observation, verdict, authorization and execution are collapsed.

Canonical guards:

- detection != authority;
- monitor read access != repair write access;
- semantic verdict != repair authorization;
- repair authorization != global write authority;
- re-entry != renewed authority.

Forward chain:

`observe -> adjudicate -> authorize -> execute bounded repair -> re-entry audit`.

A Repair Authority Gate binds target lineage, affected closure, permitted operation, preservation set, recomputation horizon and re-entry policy. It need not be an LLM.

Canonical principle:

> **A system that enforces Process Reality must itself obey Process Reality boundaries.**

R7-S supports bounded-repair feasibility but does not validate production recursive governance. No new execution or semantic adjudication is authorized.
