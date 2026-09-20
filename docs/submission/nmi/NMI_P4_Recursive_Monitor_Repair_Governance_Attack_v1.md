# NMI-P4 Foundational Attack 03 — Recursive Monitor/Repair Governance

Date: 2026-09-21  
Status: **THEORY SELF-CONSISTENCY HARDENED / OUTLOOK ONLY / NO NEW EXECUTION**

## Attack question

> If a Process Reality monitor is allowed to decide what is suspicious and a repair agent is allowed to modify the system, can the integrity layer itself create the same Reality Bias it is meant to control?

Yes, as an architectural risk. The control layer can reproduce C/P/R-like failures if observation, verdict, authorization and write execution collapse.

## Recursive risks

- **C-like:** a monitor alert such as “possible authority mismatch” is promoted into “target state is false/invalid” without separate adjudication.
- **P-like:** a repair agent expands from one disputed lineage into adjacent state, whole-system optimization or broader rewrites without a bounded authorization surface.
- **R-like:** superseded state re-enters during recomputation and is treated as renewed authority without fresh evidence or re-authorization.

Canonical guards:

> **detection != authority**

> **monitor read access != repair write access**

> **semantic verdict != repair authorization**

> **repair authorization != global write authority**

> **re-entry != renewed authority**

## Repair Authority Gate

The forward architecture is:

`Observed system -> Process Reality Monitor -> semantic adjudication -> Repair Authority Gate -> bounded Repair Agent -> selective recomputation -> re-entry watch`.

The gate binds:

- target semantic object / lineage;
- source evidence;
- evidence-supported affected closure;
- permitted operation;
- preservation set;
- recomputation horizon;
- re-entry policy;
- audit identity.

The gate is a permission boundary, not necessarily another LLM. It may be deterministic, capability-based, signed, human-authorized or embedded.

The affected closure is a dependency set, not a general optimization budget.

## No infinite regress requirement

Recursive governance is a property, not a demand for infinitely nested monitors. The integrity layer can terminate in least-authority interfaces, read-only monitoring, explicit write capabilities, immutable audit records, content-addressed repair transactions or institutional authorization.

Canonical principle:

> **A system that enforces Process Reality must itself obey Process Reality boundaries.**

## Evidence boundary

R7-S gives bounded lineage-repair feasibility evidence:

- compatible/unrelated structure preserved: **4/4**;
- material divergence: **2/4**;
- compatible reconvergence: **2/4**.

It does **not** experimentally validate an external Monitor Agent, Repair Authority Gate, recursive production governance stack or security against a compromised control component. These remain architecture/outlook implications.

## Relation to capability absorption

Foundational Attack 02 established that protocol placement may move from external to middleware, embedded or model-native. FA03 adds that wherever the protocol resides, monitoring or repair must not automatically inherit unlimited authority.

Externality is not the safeguard. **Permission separation is.**

## Verdict

Attack:

**“The monitor/repair layer can itself become a source of Reality Bias.”**

Verdict:

**SUPPORTED AS A REAL ARCHITECTURAL RISK.**

Theory consequence:

> **Process Reality governance is recursively applicable to the integrity layer itself.**
