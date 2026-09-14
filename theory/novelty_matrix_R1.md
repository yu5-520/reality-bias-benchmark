# R1 Novelty Matrix
## Adjacent literature vs. Reality Bias / Authority Penetration

**Purpose:** Prevent the first paper from relabeling existing hallucination, prompt injection, tool-risk, memory-security, provenance, or access-control work.

| Adjacent line | Representative work | What that work directly studies | Overlap with this program | Boundary / proposed novelty claim |
|---|---|---|---|---|
| General agent benchmarking | AgentBench (Liu et al., 2023) | Reasoning, decision-making, instruction following across interactive environments | Shows broad agent failure landscape | Reality Bias is not a general competence benchmark; it targets unauthorized promotion into system reality |
| Tool-use risk | ToolEmu (Ruan et al., 2023) | Risky LM-agent behavior under tool use using an LM-emulated sandbox | System actions can create real-world harm | Wrong/risky tool use is not automatically P; P requires completeness-driven unauthorized graph/scope expansion |
| Prompt injection | AgentDojo (Debenedetti et al., 2024) | Indirect prompt-injection attacks/defenses for tool-using agents | Untrusted content can redirect actions | External malicious instruction is not itself Reality Bias; the relevant event is model-originated unauthorized promotion/expansion/reopen |
| Multi-agent coordination | MultiAgentBench (Zhu et al., 2025) | Collaboration/competition and coordination topologies | Provides multi-agent structures where propagation can be tested | Proposed focus is cross-bias transition, authority-bearing state inheritance, and loop formation—not generic collaboration quality |
| Organizational permissions | OrgAccess (Sanyal et al., 2025) | RBAC/permission compliance under organizational hierarchies | Demonstrates LLM difficulty with structured permissions | Authority here is not only user/role permission; it is the conversion right by which inference becomes fact, executable graph, or historical state |
| Memory poisoning | MPBench-style memory poisoning work (Dash et al., 2026) | How malicious content is written to and persists in agent memory | Persistent bad state can influence later behavior | Mechanical/external poisoning is outside Reality Bias unless model-originated probabilistic promotion occurs |
| Memory lifecycle & repair | MemSecBench (Chen et al., 2026) | Persistence → consequence → selective repair across memory systems | Strong overlap with persistence and selective repair | ALR is proposed to localize earliest authority-violating ancestor in a dependency graph, not merely delete poisoned memory |
| Longitudinal memory risk | Remembering More, Risking More (Al-Tawaha et al., 2026) | Safety changes as memory accumulates across tasks | Temporal accumulation and state contamination | Retrospective Bias specifically concerns unauthorized reopen/revision of settled history, not all longitudinal memory risk |
| Provenance / evidence tracing | From Agent Traces to Trust (Wang et al., 2026) | Evidence tracing and execution provenance | Strong overlap with traceability and audit | Provenance is treated as enabling infrastructure; paper claim is about authority penetration dynamics and interventions |
| Provenance-based guardrails | ProvenanceGuard (She et al., 2026) | Detecting misaligned tool calls using traceable support | Close overlap with action justification | Proposed distinction: three authority classes + generation/realization + cross-dimensional transitions + localized recovery |
| Computer-agent side effects | OSWorld (Xie et al., 2024) | Real computer tasks; notes safety/side-effect evaluation gap | Motivates process-level safety | Reality Bias provides a specific mechanism hypothesis, not a general side-effect metric |

## Literature references used in this R1 pass

- Liu et al. (2023), **AgentBench: Evaluating LLMs as Agents**, arXiv:2308.03688.
- Ruan et al. (2023), **Identifying the Risks of LM Agents with an LM-Emulated Sandbox (ToolEmu)**, arXiv:2309.15817.
- Debenedetti et al. (2024), **AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents**, arXiv:2406.13352.
- Xie et al. (2024), **OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments**, arXiv:2404.07972.
- Zhu et al. (2025), **MultiAgentBench: Evaluating the Collaboration and Competition of LLM agents**, arXiv:2503.01935.
- Sanyal et al. (2025), **OrgAccess: A Benchmark for Role Based Access Control in Organization Scale LLMs**, arXiv:2505.19165.
- Dash et al. (2026), **From Untrusted Input to Trusted Memory: A Systematic Study of Memory Poisoning Attacks in LLM Agents**, arXiv:2606.04329.
- Chen et al. (2026), **MemSecBench: Tracking Agent Memory Poisoning from Persistence to Consequence and Repair**, arXiv:2607.27080.
- Al-Tawaha et al. (2026), **Remembering More, Risking More: Longitudinal Safety Risks in Memory-Equipped LLM Agents**, arXiv:2605.17830.
- Wang et al. (2026), **From Agent Traces to Trust: Evidence Tracing and Execution Provenance in LLM Agents**, arXiv:2606.04990.
- She et al. (2026), **Safeguarding LLM Agents from Misalignment through Provenance Analysis**, arXiv:2607.01236.

## R1 novelty conclusion

The strongest defensible novelty boundary is **not** “agents violate permissions” and not “agents can hallucinate, drift, or be poisoned.”

The candidate contribution is narrower:

1. probabilistic model proposals can cross a conversion boundary and acquire **authority-bearing system identity**;
2. this can occur through distinct **Information / Invocation / Temporal** pathways conditioned on distinct C/P/R mechanisms;
3. realized events can propagate as state-mediated transitions across dimensions;
4. controls can be tested for **bias displacement** rather than only aggregate failure reduction;
5. recovery can be localized to the **earliest authority-violating ancestor** rather than the earliest wrong text or a full rerun.

This is still a hypothesis-level novelty claim. R2–R7 must establish empirical distinctiveness.
