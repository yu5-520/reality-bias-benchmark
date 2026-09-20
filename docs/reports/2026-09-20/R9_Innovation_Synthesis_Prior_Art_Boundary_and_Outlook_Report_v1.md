# R9 Innovation Synthesis, Prior-Art Boundary, and Research Outlook Report v1

Date: 2026-09-20
Status: **FORWARD SYNTHESIS / NO NEW SUBJECT EVIDENCE / PAPER-LEVEL FREEZE NOT YET**

## Report role

R9 closes the first paper at the **innovation, contribution-boundary and outlook layer**.

It replaces the earlier idea of mandatory compute-heavy cross-model replication as a first-paper completion criterion.

Cross-model / cross-provider / cross-topology replication remains an external-validation programme.

## Primary question

> What did the first paper actually discover or operationalize that is not already supplied by existing work on MAS failures, communication topology, memory, provenance, fault attribution, rollback and recovery?

## Evidence basis

R9 adds no new subject evidence.

Empirical basis remains R2-R8, including:

- E-commerce discovery;
- 90 held-out natural trajectories;
- canonical R5/R6 mechanism evidence;
- R7 process-integrity intervention evidence;
- R8 trajectory-first Dynamic CPR semantic closure.

Literature basis is bound in:

- `docs/related_work/R9_Prior_Art_Literature_Map_v1.md`;
- `docs/related_work/R9_Innovation_Boundary_Matrix_v1.md`.

---

# 1. What existing literature already covers

## 1.1 MAS failure analysis is established

NeurIPS 2025 MAST provides a large annotated MAS failure dataset and a 14-mode taxonomy spanning system design, inter-agent misalignment and task verification.

ACL/EACL 2026 work further develops:

- edge-level handoff error categories and clarification (AgentAsk);
- semantic failure attribution and backward tracing (ErrorProbe);
- long-horizon iterative fault attribution (RAFFLES).

Therefore the first paper must not present “multi-Agent failures exist” or “long traces require semantic diagnosis” as its primary novelty.

## 1.2 Communication topology and information propagation are established

ICML 2025 G-Designer optimizes task-specific communication topology.

EMNLP 2025 directly studies how correct and erroneous outputs propagate under different topology sparsity.

Therefore R2-R4 cannot claim novelty for information propagation itself.

The forward research distinction is:

> communication/topology work asks how information moves; Process Reality asks what operational permission transformed information acquires while moving and being reused.

## 1.3 Provenance and memory lineage are established research areas

PROV-AGENT captures prompts, responses, decisions and broader workflow/downstream provenance.

ACL 2026 memory work shows experience-following, error propagation and misleading replay through stored experience.

A 2026 provenance survey explicitly frames evidence/execution tracing, memory lineage, audit and semantic provenance as an emerging research programme.

Therefore this paper should not claim “first provenance” or “first memory-lineage analysis”.

## 1.4 Recovery / rollback / process control are established

EMNLP 2025 GA-Rollback provides action checking and stepwise rollback.

ICML 2025 SyncMind studies out-of-sync recovery in collaborative software engineering.

IEEE eScience ControlA proposes provenance-augmented workflow control for detection, containment and recovery.

A 2026 preprint, Cordon, goes further with task-scoped semantic transactions, result lineage, delegated authority, rollback, recovery and audit.

Therefore R7 must not be positioned as “the first agent recovery method”.

---

# 2. High-risk frontier overlap that narrows novelty claims

## 2.1 Stored Is Not Supported

The September 2026 preprint *Stored Is Not Supported* is a particularly important boundary.

It explicitly separates:

- persistence / availability;
- evidential support;
- epistemic roles;
- temporal validity;
- disclosure authority;
- source independence.

It also formalizes typed provenance and role promotion.

Therefore this paper cannot claim novelty for the generic proposition:

> stored or retrieved content is not automatically supported.

### Remaining difference

The present study empirically reconstructs a different object:

> **natural multi-Agent process reality in motion**.

It follows transformed semantic descendants across Agents and tests how:

- uncertainty;
- constraints;
- decision implications;
- action implications;
- collaboration scope;
- retrospective process state

gain or lose operational permission through actual trajectories.

The paper's Dynamic C contribution must therefore be framed as **semantic authority migration through functional lineage in multi-Agent process dynamics**, not as invention of epistemic support typing.

## 2.2 Cordon

The June 2026 Cordon preprint defines a task-scoped semantic transaction binding tool intents, result lineage, delegated authority, staged effects, rollback, recovery and audit.

Therefore Dynamic P / process-integrity engineering cannot claim ownership of “task-level execution boundary” or delegated-authority runtime control.

### Remaining difference

Dynamic P is an empirical process mechanism:

> Agents can progressively generate new collaboration/execution obligations relative to the original goal, even when the requested result is already semantically stable and even without an irreversible external tool commit.

R7 then uses semantic-lineage closure to repair/recompute affected process structure.

---

# 3. Paper-level innovation synthesis

## 3.1 Structural contribution — Multi-Agent execution as process reality

The paper's structural move is to treat multi-Agent execution as more than:

- a call graph;
- a communication topology;
- a memory store;
- an action sequence.

The observed process contains a reusable semantic layer in which source information is transformed into descendants, constraints, plans, decisions and actions.

The paper calls this operational layer **Process Reality**.

The contribution is not that shared state exists.

It is that process analysis explicitly distinguishes:

`source evidence`
!= `semantic descendants`
!= `operational permission`.

## 3.2 Mechanism contribution — Dynamic CPR

Dynamic CPR treats permission as a process variable.

- **C** — information permission penetration / semantic authority migration;
- **P** — collaboration/execution permission penetration / semantic self-authorization;
- **R** — temporal permission penetration / retrospective generation.

The first paper provides mechanism-level evidence that these dimensions can interact:

- C can drive P;
- R can generate P;
- R can generate C;
- P reinforcing C remains candidate evidence.

This is not a claim that CPR explains every MAS failure.

## 3.3 Semantic-observability contribution — Functional Semantic Lineage

Execution provenance can tell us which event/message/tool/result depended on what.

R8 additionally asks:

> after the wording changes, what functional meaning is still alive?

Functional Semantic Lineage traces the continuity of:

- uncertainty;
- constraints;
- causal interpretation;
- decision implication;
- action implication;
- operational reuse.

The source proposition can disappear while functional meaning persists.

This is the semantic layer used to interpret Process Reality.

## 3.4 Method contribution — Trajectory-First Dynamic Semantic Audit

The audit reads the complete realized process before assigning mechanism labels.

Mandatory components include:

- semantic reconstruction;
- functional lineage;
- goal/boundary/process/result alignment;
- retrospective continuation;
- censor-aware interpretation.

This differs from fault attribution because the target does not have to be a discrete error step or failed terminal result.

## 3.5 Engineering contribution — Lineage-addressed incremental repair

R6/R7 instantiate:

`detect/localize`
-> `content-address semantic lineage`
-> `completeness gate`
-> `persistent correction OR structural repair`
-> `selective reopen/recompute`
-> `preserve compatible state`
-> `watch re-entry/regenerated authority`.

The appropriate claim is an **engineering pattern demonstrated on frozen experimental processes**, not universal superiority over rollback or transactional controls.

---

# 4. Innovation boundary matrix

The canonical matrix is:

`docs/related_work/R9_Innovation_Boundary_Matrix_v1.md`.

The strongest distinction can be summarized as:

| Existing research | Already strong at | This paper adds |
| --- | --- | --- |
| MAS failure taxonomy / diagnosis | failure categories and fault localization | dynamic permission mechanisms that may exist even without terminal failure |
| communication topology | who communicates and how information propagates | what semantic/operational authority propagated information acquires |
| memory / provenance | storage, retrieval, dependency and execution lineage | functional meaning migration and process-reality authority through transformed descendants |
| rollback / recovery | restoring or correcting state/action trajectories | retrospective generation of new C/P plus lineage-addressed selective repair |
| software-agent benchmarks | task success / repository recovery / code auditing | formation provenance: why the process considered later scope/assumptions authorized |

---

# 5. Three-layer research outlook

## 5.1 Professional depth

Current evidence opens a coherent research sequence:

`formation -> dynamics -> observability -> controllability`.

### Agent Communication Protocol Research

R2-R4 can develop into controlled studies of:

- broadcast;
- peer-to-peer;
- blackboard;
- router;
- typed message;
- authority protocol;
- memory scope.

The target is no longer only success rate.

Future work can measure:

- information topology;
- semantic common-pool formation;
- authority migration;
- process-scope dynamics.

### Semantic Common Pool Dynamics

R5-R6 suggest a broader research object:

- formation;
- transformation;
- variant generation;
- commit;
- adoption;
- maintenance;
- authority migration;
- decay;
- replacement.

Reality Bias can then be studied as one pathology inside a larger semantic-common-pool dynamics theory.

### Semantic Lineage Observability

R6 points toward runtime semantic observability:

`field identity + content hash + authority history + semantic descendants + decision dependencies`.

Execution provenance is a necessary substrate, but runtime systems could additionally expose how meaning changes.

### External Process Integrity Layer / Repair Sidecar

R7 points toward an external control layer that does not require model-weight modification.

Possible engineering pattern:

`observe -> localize -> correct -> escalate to lineage repair -> selective recompute -> verify`.

This is a transition from:

`rerun-based recovery`

toward:

`incremental semantic repair`.

## 5.2 Generality

### Vibe Coding / AI software engineering

Software-agent research already studies repository task performance, issue localization, code auditing and out-of-sync recovery.

The Process Reality outlook asks a different provenance question:

> How did the repository become semantically authorized to contain these changes?

Potential formation chain:

`requirement`
-> `inferred assumption`
-> `field/interface`
-> `module`
-> `code`
-> `downstream dependency`.

Thus:

> **Artifact transparency does not imply process transparency.**

A repository can remain code-visible while the authorization and semantic lineage of its formation becomes opaque.

### Enterprise Agent systems

The current cross-domain evidence motivates external validation across:

- memory architectures;
- communication topology;
- MCP;
- tool agents;
- enterprise workflows;
- persistent organizational knowledge.

These remain future validity tests.

## 5.3 Production / societal deployment

The deployment question is shifting from:

> Can the model perform this task?

toward:

> Under what provenance, authority, process, audit, repair and acceptance conditions should probabilistic capability be admitted into production?

Future process qualification may require explicit standards for:

- inputs;
- authority;
- provenance;
- drift;
- repair;
- re-entry;
- acceptance;
- recovery.

This paper does not define those standards.

It supplies a mechanism study motivating why such standards may be needed.

---

# 6. External-validation programme

The original compute-heavy R9 idea is retained as later external validation.

Priority axes:

1. cross-model;
2. cross-provider;
3. cross-topology;
4. cross-memory architecture;
5. cross-tool / MCP environment;
6. Agent-count scaling;
7. task-complexity scaling;
8. independent semantic reviewers;
9. external-lab replication.

The first paper does not treat these as already completed.

---

# 7. First-paper role

The first paper is best positioned as:

> **mechanism-first, high-resolution study of multi-Agent process reality.**

Its central question is:

> **Not how often does this happen across all systems, but what exactly is happening when it does?**

Large-scale prevalence, cross-model rate and topology-specific frequency are downstream empirical questions.

This positioning preserves the paper's strongest evidence:

- dynamic semantic reconstruction;
- mechanism-level contrasts;
- healthy comparators;
- localized intervention;
- process/endpoint separation.

---

# 8. Contribution wording approved by R9

## Preferred abstract-level wording

> Rather than treating multi-Agent reliability only as terminal failure, message corruption or state recovery, we study how operational permission is dynamically constructed through semantic lineage, collaboration scope and retrospective process reuse, and show how these mechanisms can be observed and locally intervened on.

## Preferred related-work boundary wording

> Prior work has characterized multi-Agent failure modes, communication-topology effects, execution provenance, memory error propagation and rollback/recovery. Our focus is complementary: we reconstruct complete trajectories to study how semantic meaning and operational permission evolve across transformed descendants, collaboration scope and retrospective process reuse.

## Not authorized

No R9 document authorizes:

- “first-ever”;
- “first MAS failure analysis”;
- “first semantic provenance”;
- “first stored-vs-supported distinction”;
- “first Agent rollback”;
- “first task-level authority boundary”.

---

# 9. Claim boundary

R9 establishes a literature-grounded contribution boundary.

It does **not** establish:

- exhaustive global novelty;
- prevalence;
- cross-model robustness;
- cross-topology robustness;
- closed CPR attractor;
- independent reviewer agreement;
- universal engineering superiority.

Any future `To our knowledge, the first...` statement requires a broader systematic novelty search immediately before submission.

---

# 10. R9 conclusion

The first paper's innovation is strongest as a **combined mechanism programme**, not as ownership of isolated primitives.

The paper connects:

`dynamic Process Reality`
+ `functional semantic lineage`
+ `trajectory-first semantic auditing`
+ `lineage-addressed process integrity control`.

The current literature already provides important neighboring capabilities in failure diagnosis, topology, memory, provenance and recovery.

R9 therefore narrows the paper's contribution to the layer the frozen evidence actually supports:

> **how multi-Agent systems dynamically construct, expand, reopen and locally repair operational process reality through semantic trajectories.**
