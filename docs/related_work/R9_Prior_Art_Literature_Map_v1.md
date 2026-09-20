# R9 Prior-Art Literature Map v1

Date: 2026-09-20
Status: LITERATURE-GROUNDED INNOVATION AUDIT
Scope: literature checked through 2026-09-20

## 1. Peer-reviewed anchor literature

| ID | Work | Venue | What it establishes | Why it matters to R9 |
| --- | --- | --- | --- | --- |
| L1 | Cemri et al., **Why Do Multi-Agent LLM Systems Fail?** | NeurIPS 2025 Datasets & Benchmarks | 1600+ annotated MAS traces; 14 failure modes across system design, inter-agent misalignment and task verification | Strong boundary against claiming novelty for “MAS failure analysis” itself |
| L2 | Zhang et al., **G-Designer: Architecting Multi-agent Communication Topologies via Graph Neural Networks** | ICML 2025 | task-adaptive communication topology optimization for performance/cost/robustness | Boundary for R2-R4 communication-protocol claims |
| L3 | Shen et al., **Understanding the Information Propagation Effects of Communication Topologies in LLM-based Multi-Agent Systems** | EMNLP 2025 | causal analysis of correct/error information propagation under topology sparsity | Closest peer-reviewed boundary for information propagation versus semantic-authority migration |
| L4 | Lin et al., **AgentAsk: Multi-Agent Systems Need to Ask** | ACL 2026 | edge-level Data Gap, Signal Corruption, Referential Drift, Capability Gap; clarification intervention | Strong boundary for message-handoff semantic errors and cascading errors |
| L5 | Li et al., **Towards Self-Improving Error Diagnosis in Multi-Agent Systems** | Findings ACL 2026 | semantic failure attribution, backward tracing and executable-evidence validation | Boundary for “semantic diagnosis” and local error-step attribution |
| L6 | Zhu et al., **RAFFLES: Reasoning-based Attribution of Faults for LLM Systems** | EACL 2026 | iterative offline fault attribution for long-horizon LLM systems | Boundary for trajectory reasoning and automated fault localization |
| L7 | Souza et al., **PROV-AGENT: Unified Provenance for Tracking AI Agent Interactions in Agentic Workflows** | IEEE eScience 2025 | provenance model for prompts, responses, decisions and workflow/downstream context | Closest peer-reviewed execution-provenance boundary |
| L8 | **ControlA: Agentic Workflow Control Mechanisms for Reliable Science** | IEEE eScience 2025 | provenance-augmented workflow instrumentation, detection, containment and recovery concept | Boundary for general workflow-level process-integrity control |
| L9 | Li et al., **Generator-Assistant Stepwise Rollback Framework for Large Language Model Agent** | EMNLP 2025 | action checking and stepwise rollback as plug-and-play recovery | Boundary against claiming novelty for rollback/recovery itself |
| L10 | Xiong et al., **How Memory Management Impacts LLM Agents: An Empirical Study of Experience-Following Behavior** | ACL 2026 | memory addition/deletion, experience-following, error propagation and misleading replay | Strong boundary for persistence/error propagation through memory |
| L11 | Guo et al., **SyncMind: Measuring Agent Out-of-Sync Recovery in Collaborative Software Engineering** | ICML 2025 | out-of-sync states and recovery in collaborative software engineering | Boundary for Vibe Coding / evolving repository-state outlook |
| L12 | Guo et al., **RepoAudit: An Autonomous LLM-Agent for Repository-Level Code Auditing** | ICML 2025 | repository-level code auditing using memory, data-flow facts and validator | Boundary for code-repository auditing; useful for software-engineering outlook |

## 2. High-risk recent frontier neighbors

These are not used as peer-reviewed priority claims, but they are too close to ignore.

| ID | Work | Status | Why it is high-risk for novelty |
| --- | --- | --- | --- |
| F1 | He & Yu, **Stored Is Not Supported: Typed Provenance and Assertion Guardrails for Persistent AI Agents** | arXiv:2609.02127, 2026 preprint | explicitly separates persistence from epistemic standing; typed provenance, dependency lineage, role promotion, source independence, temporal validity and assertion authority |
| F2 | Chen et al., **Cordon: Semantic Transactions for Tool-Using LLM Agents** | arXiv:2606.17573, 2026 preprint | task-scoped execution boundary binding result lineage, delegated authority, rollback/recovery/audit and staged effects |
| F3 | Wang et al., **From Agent Traces to Trust: Evidence Tracing and Execution Provenance in LLM Agents** | arXiv:2606.04990, 2026 survey/preprint | synthesizes execution/evidence provenance, memory lineage, trace observability, failure diagnosis and calls out semantic provenance as an open problem |

## 3. Exact novelty constraints implied by the literature

### 3.1 We cannot claim “first MAS failure analysis”

L1, L4, L5 and L6 already provide failure taxonomies, edge-level semantic error categories, semantic failure attribution and long-horizon fault attribution.

Forward distinction:

> Our target is not only failure localization. We audit dynamic permission changes in complete trajectories, including cases where the terminal result can remain acceptable.

### 3.2 We cannot claim “first to study information propagation”

L3 explicitly studies correct/error information propagation under communication topologies.

Forward distinction:

> R2-R8 ask what operational/epistemic permission propagated semantics acquire while being transformed and reused.

### 3.3 We cannot claim “first semantic provenance” broadly

L7 provides execution provenance over prompts/responses/decisions, F3 explicitly identifies semantic provenance as a research direction, and F1 already formalizes typed epistemic provenance and role promotion.

Forward distinction:

> The paper operationalizes **functional semantic lineage in natural multi-Agent trajectories** and links semantic transformation to changing operational permission and cross-dimensional C/P/R dynamics.

### 3.4 We cannot claim “first to separate stored from supported”

F1 makes this distinction explicitly and very recently.

Forward distinction:

> Our empirical object is emergent multi-Agent process reality: transformed descendants, shared-state reuse, collaboration-scope expansion and retrospective reopening in natural/controlled trajectories.

### 3.5 We cannot claim “first rollback / repair method”

L9 already provides stepwise rollback; L8 discusses workflow-level recovery; F2 provides task-scoped transactional rollback/recovery.

Forward distinction:

> R6-R7 instantiate **lineage-addressed incremental semantic repair**: localize semantic lineage, content-address affected closure, selectively reopen/recompute, preserve compatible state and watch re-entry/regenerated authority.

### 3.6 We cannot claim “first task/authority boundary”

F2 explicitly introduces a task-scoped transactional execution boundary with delegated authority.

Forward distinction:

> Dynamic P is an empirical mechanism of **semantic self-authorization**: realized collaboration/execution scope grows through Agent-generated obligations relative to the original goal and final result, even without external side-effect commit.

## 4. Bibliographic records

- **L1** Cemri, M. et al. 2025. *Why Do Multi-Agent LLM Systems Fail?* NeurIPS 2025 Datasets and Benchmarks Track. DOI: 10.52202/085713-4082. https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html
- **L2** Zhang, G. et al. 2025. *G-Designer: Architecting Multi-agent Communication Topologies via Graph Neural Networks.* ICML 2025, PMLR 267. https://proceedings.mlr.press/v267/zhang25cu.html
- **L3** Shen, X. et al. 2025. *Understanding the Information Propagation Effects of Communication Topologies in LLM-based Multi-Agent Systems.* EMNLP 2025. DOI: 10.18653/v1/2025.emnlp-main.623. https://aclanthology.org/2025.emnlp-main.623/
- **L4** Lin, B. et al. 2026. *AgentAsk: Multi-Agent Systems Need to Ask.* ACL 2026. https://aclanthology.org/2026.acl-long.1294/
- **L5** Li, J. et al. 2026. *Towards Self-Improving Error Diagnosis in Multi-Agent Systems.* Findings ACL 2026. DOI: 10.18653/v1/2026.findings-acl.98. https://aclanthology.org/2026.findings-acl.98/
- **L6** Zhu, C. et al. 2026. *RAFFLES: Reasoning-based Attribution of Faults for LLM Systems.* EACL 2026. DOI: 10.18653/v1/2026.eacl-long.359. https://aclanthology.org/2026.eacl-long.359/
- **L7** *PROV-AGENT: Unified Provenance for Tracking AI Agent Interactions in Agentic Workflows.* IEEE eScience 2025. DOI: 10.1109/eScience65000.2025.00093. https://ieeexplore.ieee.org/document/11181558/
- **L8** *ControlA: Agentic Workflow Control Mechanisms for Reliable Science.* IEEE eScience 2025. DOI: 10.1109/eScience65000.2025.00086. https://ieeexplore.ieee.org/document/11181468/
- **L9** Li, X. et al. 2025. *Generator-Assistant Stepwise Rollback Framework for Large Language Model Agent.* EMNLP 2025. DOI: 10.18653/v1/2025.emnlp-main.892. https://aclanthology.org/2025.emnlp-main.892/
- **L10** Xiong, Z. et al. 2026. *How Memory Management Impacts LLM Agents: An Empirical Study of Experience-Following Behavior.* ACL 2026. DOI: 10.18653/v1/2026.acl-long.27. https://aclanthology.org/2026.acl-long.27/
- **L11** Guo, X. et al. 2025. *SyncMind: Measuring Agent Out-of-Sync Recovery in Collaborative Software Engineering.* ICML 2025, PMLR 267. https://proceedings.mlr.press/v267/guo25l.html
- **L12** Guo, J. et al. 2025. *RepoAudit: An Autonomous LLM-Agent for Repository-Level Code Auditing.* ICML 2025, PMLR 267. https://proceedings.mlr.press/v267/guo25n.html
- **F1** He, J. & Yu, D. 2026. *Stored Is Not Supported: Typed Provenance and Assertion Guardrails for Persistent AI Agents.* arXiv:2609.02127.
- **F2** Chen, Z. et al. 2026. *Cordon: Semantic Transactions for Tool-Using LLM Agents.* arXiv:2606.17573.
- **F3** Wang, Y. et al. 2026. *From Agent Traces to Trust: Evidence Tracing and Execution Provenance in LLM Agents.* arXiv:2606.04990.

## 5. Literature-map boundary

This map supports boundary setting, not an exhaustive “no prior work exists” proof.

Any future wording of `first` or `first-ever` requires a broader systematic search and should not be inferred from this map alone.
