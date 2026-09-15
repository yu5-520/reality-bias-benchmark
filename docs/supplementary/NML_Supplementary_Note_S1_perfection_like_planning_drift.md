# NML Supplementary Note S1 — A Provenance-Backed Reflexive Case of Perfection-Like Planning Drift

Working subtitle: **When a Reality Bias Study Nearly Drifted into Perfection Bias**  
Document type: **formal supplementary methodological story template**  
Status: **DRAFT MATERIAL / NON-EXPERIMENTAL / PROVENANCE-BACKED**  
Repository date: 2026-09-16  
Timestamp basis: GitHub commit timestamps in UTC unless otherwise stated.

> **Scientific status notice**
>
> This note is not a preregistered experiment, is not part of the R2-R8 subject population, does not enter C/P/R statistics, and is not used as empirical evidence for the existence, prevalence or cross-setting generality of Reality Bias. It is retained as a reflexive methodological illustration whose chronology can be independently inspected through repository provenance. The interpretation below is hypothesis-generating only.

## S1.1 Purpose

The main study uses a controlled Multi-Agent environment to investigate interaction-level Reality Bias through structural emergence, propagation, feedback, causal interruption and recovery. During development of the measurement and review apparatus, the research workflow itself accumulated a sequence of locally reasonable extensions: additional semantic reviewers, cross-model-family replication, provider integration, checkpoint recovery, thinking controls, cache optimization and reasoning-latency telemetry.

None of these steps was individually unreasonable. The reflexive interest lies in the **cumulative dependency shift**: a supplementary robustness objective gradually moved onto the critical path of the structural research program. The repository history preserves both the earlier evidence-first rule and the later gate state, allowing the planning drift to be reconstructed without relying only on retrospective memory.

This note therefore illustrates a narrow methodological point:

> **A sequence of locally defensible improvements can cumulatively shift task scope and task focus, even when the nominal high-level goal remains unchanged.**

The case is described as *Perfection-like planning drift*, not as a formally adjudicated Perfection Bias event.

## S1.2 Original research boundary

The earlier accepted execution contract separated subject generation from later adjudication:

`prepare → subject run → preserve raw evidence → integrity validation → deterministic objective statistics → export review material → RUN_COMPLETE_PENDING_REVIEW`

Semantic review was explicitly defined as an optional later operation over frozen evidence, and review failure was not allowed to trigger a subject rerun.

A subsequent accepted planning revision also stated that R2/R3/R4 were structural views over shared immutable evidence and that research gates regulate **strength of claims**, not permission to observe a phenomenon.

The intended first-paper path was therefore approximately:

`theory → minimal Multi-Agent environment → natural structural emergence → propagation → feedback → causal interruption → recovery → bounded generalization → reproducibility freeze`

## S1.3 Provenance chronology

The table below is an evidentiary navigation aid. It records repository-visible milestones, not experimental observations.

| UTC timestamp | Repository evidence | Commit | Planning significance |
| --- | --- | --- | --- |
| 2026-09-15T06:38:37Z | `theory/change_notes/CN-R2-023_evidence_first_deferred_adjudication.md` | `da83c60b15e09d686db9b0b795c36b2f1ba7ab8b` | Evidence-first lifecycle frozen; semantic review separated from subject execution; review failure cannot trigger subject rerun. |
| 2026-09-15T07:04:10Z | `theory/change_notes/CN-R-024_structural_layers_async_audit.md` | `15abe68ce13307638a81c044a84d72fc450fb6d7` | R2/R3/R4 framed as shared structural layers with asynchronous audit; gates limit claim strength rather than permission to observe. |
| 2026-09-15T15:00:07Z | `docs/R_Plan_v3.0.md` | `42d32d6cfa01e6942322e6765b085decf2994246` | Measurement architecture v2 made reviewer-mediated semantic boundary judgment central to the forward execution sequence. |
| 2026-09-15T16:10:32Z | `docs/R234_v2_current_gate.md` history | `1fef801e94487732746dadaee6617c8ee1a682d7` | Reviewer-v2 gate advanced to explicit paid-review authorization boundary. |
| 2026-09-15T16:30:08Z | `docs/R234_v2_current_gate.md` history | `f779a8cd72f4d5905c4d48c77d9d204ec50c08d5` | Gate advanced after full semantic round. |
| 2026-09-15T16:39:39Z | `docs/R234_v2_current_gate.md` history | `99af96626394576a6e9c265605495b73582f2dbc` | Different-family independent replication became the next stated gate while K=2 remained blocked. |
| 2026-09-15T17:26:43Z | `adapters/bailian_openai_chat.py` | `6844a063b11b96bf183348273f658b2d8a39c2cf` | Bailian/Qwen transport added for a different-family reviewer. |
| 2026-09-15T17:32:59Z | `arena/run_reviewer_v2_bailian_qwen_round.py` | `027a948800e06db88bd9e05b2df55570f5f727a8` | Gated full Qwen independent Reviewer-v2 runner added. |
| 2026-09-15T18:05:12Z | `arena/run_reviewer_v2_bailian_qwen_round.py` | `3f4ee441dc776be13fc78d030a8458772f32211c` | Checkpoint resume and failed-attempt evidence added after partial-run failure. |
| 2026-09-15T18:10:44Z | `adapters/bailian_openai_chat.py` | `da4e4e826e21ece9159078a15babe0dd3beb7072` | Explicit thinking controls exposed for reviewer runtime calibration. |
| 2026-09-15T18:17:02Z | `arena/run_bailian_reviewer_v2_preflight.py` | `cde03f99fe6d912f3aff1d68e024331a826d3f16` | Five-packet Qwen Reviewer-v2 preflight gate added. |
| 2026-09-15T18:42:27Z | `adapters/bailian_openai_chat.py` | `fa175e21ef247be19b8844bfebe1a6b0164e457c` | Explicit message cache markers added. |
| 2026-09-15T18:43:30Z | `arena/run_bailian_reviewer_v2_preflight.py` | `08ad4dd564c6c5c3e8d82da86a1b5302b6527af3` | Preflight gained explicit-cache mode. |
| 2026-09-15T18:56:49Z | `arena/run_bailian_reviewer_v2_preflight.py` | `7004a2b58e97c759f77c3fb6104672bf07fd901b` | Reasoning/latency telemetry added, extending optimization of the reviewer path. |
| 2026-09-15T19:41:13Z | `docs/R_Plan_v3.1.md` | `831bd5b71d09731d27b999a873dab586dd791de6` | Dependency DAG corrected: R2-R8 restored as structural/mechanistic subject program; cross-model robustness moved to R9. |
| 2026-09-15T19:41:32Z | `theory/change_notes/CN-R-045_r_plan_v31_dependency_correction.md` | `4d61814f4c77114476317091ce5bccbaa183e8c6` | Correction formally registered without deleting or rewriting the historical path. |

## S1.4 Locally rational expansion

The drift did not begin as an explicit decision to turn the study into a reviewer benchmark. It emerged through a sequence of individually defensible steps:

`semantic ambiguity`

→ add an independent reviewer

→ observe reviewer disagreement

→ redesign the reviewer contract

→ require a different model family for independent replication

→ integrate a new provider/model

→ build a full 144-unit runner

→ handle partial-run recovery

→ investigate latency and reasoning cost

→ add thinking controls

→ investigate cache behavior

→ add explicit cache

→ add reasoning-latency telemetry

Every local step can be justified as increasing reliability, completeness, efficiency or reproducibility. The planning issue becomes visible only at the global level, where the supplementary reviewer objective began to determine whether the structural research program could continue.

## S1.5 Turning point: from robustness aid to blocking dependency

The most informative repository transition is not the addition of Qwen itself. It is the change in dependency semantics.

Earlier governance:

`frozen subject evidence → optional/deferred semantic review`

and

`gate → limits claim strength`

Later critical-path state:

`DeepSeek Reviewer-v2 → different-family Reviewer still needed → K=2 blocked`

This shift made reviewer robustness function as a prerequisite for further structural observation. The research remained nominally about Reality Bias, but operational attention increasingly moved toward reviewer-model coverage and provider/runtime optimization.

R Plan v3.1 reverses this dependency while preserving every historical artifact.

## S1.6 Perfection-like interpretation

The following mapping is an **illustrative interpretation only**:

### Scope-expansion-like pattern

A limited semantic robustness task expanded into a larger engineering and evaluation subprogram. The added work remained relevant to the paper, but it exceeded what was necessary to continue observing the structural subject mechanisms.

### Focus-drift-like pattern

The nominal research objective did not change. However, the operational center of effort moved from Multi-Agent structural emergence and dynamics toward cross-model reviewer completion, latency, caching and reasoning-budget questions.

### Retrospective-legitimation-like pattern

As reviewer infrastructure accumulated, the growing reviewer path was increasingly represented as a prerequisite for later structural experiments rather than as supplementary robustness material.

These descriptions intentionally use the suffix **“-like”** because the planning history was not generated under the study's preregistered subject protocol.

## S1.7 Correction strategy

The correction follows the repository's own evidence-governance principles:

- do not delete R Plan v3.0;
- do not overwrite the historical Reviewer-v2 gate;
- do not delete DeepSeek/Qwen review attempts, partial records, preflights or engineering commits;
- create a new canonical R Plan v3.1;
- create an additive Change Note explaining the dependency correction;
- reclassify the **forward scientific role** of multi-model reviewer work as R9 supplementary robustness;
- allow R2-R8 to continue subject to their own evidence-integrity, preregistration and cost gates.

The result is a provenance-preserving sequence:

`original rule → local expansion → blocking dependency → detection → additive correction`

rather than a cleaned-up history that hides the planning detour.

## S1.8 Broader implication: beyond Multi-Agent systems

The formal experiments in the main paper remain Multi-Agent experiments. However, this planning history occurred in an iterative **Human–AI collaborative workflow**, which motivates a broader future hypothesis.

A possible cumulative mechanism is:

`human gives G0`

→ `AI proposes locally reasonable ΔG1`

→ `human locally authorizes ΔG1`

→ `G1 becomes inherited context`

→ `AI proposes locally reasonable ΔG2`

→ `human locally authorizes ΔG2`

→ `...`

→ `the final operational goal G* may drift materially from the original practical objective G0`

This suggests a future research question:

> **Can a sequence of individually reasonable and locally authorized AI suggestions collectively produce global goal-scope or goal-focus drift in Human–AI collaboration?**

A compact theoretical form is:

> **Local authorization does not necessarily imply global goal fidelity.**

This is explicitly hypothesis-generating. The present repository case does not establish prevalence, causality or generality in Human–AI systems.

## S1.9 Suggested main-text pointer

A brief Discussion/Future Work sentence may point to this note without turning it into a main-paper claim:

> Although the present experiments operationalize Perfection Bias in a Multi-Agent setting, the underlying goal-drift mechanism may not be exclusive to Multi-Agent systems. Iterative Human–AI workflows may also accumulate locally reasonable and locally authorized goal expansions; Supplementary Note S1 documents a provenance-backed research-planning example as a hypothesis-generating illustration rather than experimental evidence.

## S1.10 Suggested supplementary figure

A single provenance timeline is sufficient:

```text
CN-R2-023
Evidence-first / deferred review
        ↓
CN-R-024
Gate limits claim strength
        ↓
R Plan v3.0
Reviewer moves forward in execution DAG
        ↓
R234 v2 current gate
Different-family reviewer → K2 blocked
        ↓
Qwen reviewer engineering
transport → runner → recovery → thinking → cache → telemetry
        ↓
R Plan v3.1 + CN-R-045
Reviewer robustness returned to R9 supplementary scope
```

Each node should display only `UTC timestamp + path + short commit SHA` in the figure, with the full provenance table retained in this note.

## S1.11 Reporting boundary for submission

If used in a manuscript supplement, retain all of the following statements:

1. This is not an additional experiment.
2. It is not included in C/P/R counts or effect estimates.
3. The repository chronology verifies that the planning sequence occurred, not that the sequence satisfies the formal causal definition of Perfection Bias.
4. The Perfection-like mapping is interpretive and reflexive.
5. The Human–AI extension is a future hypothesis, not a demonstrated generalization.
6. Historical files are preserved so readers can inspect the sequence independently.

This boundary is essential to keep the story lively and scientifically useful without converting an interesting research-history episode into evidence it was never designed to provide.
