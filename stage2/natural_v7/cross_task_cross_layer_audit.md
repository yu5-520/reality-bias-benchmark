# Stage-II T1→T2→T3 complete cross-task / cross-layer semantic audit

**Audit state:** READ-ONLY. Natural collection is closed at **21/21** (7 systems × 3 task families × 1 first attempt). T1 remains historical Action Contract v1 evidence; T2/T3 remain prospective Action Contract v2 evidence where the custom JSON-action surface applies. This audit does not call the subject model, rerun any natural cell, resume any trajectory, or spend C3/C4.

**Frozen inputs:** `T1_posthoc_audit.{md,json}`, `T2_posthoc_audit.{md,json}`, `T3_posthoc_audit.{md,json}`, plus the 21 sealed raw manifests and archives already verified in-repository.

## Executive finding

The 21-cell matrix does not reduce to one repeated software-engineering failure mode. The three task families place the same system structures under three different process pressures, and the dominant phenomenon changes with the pressure:

- **T1 — version review:** construct a reliable account of what the system is and what changed.
- **T2 — feature request:** implement a narrow user-visible target, then decide whether the process is allowed to stop.
- **T3 — legacy retirement:** cut a historical route, then determine whether its structural and semantic residue has actually disappeared.

Across those tasks, the strongest repeated higher-level result is that **process state can remain open after the immediate functional target has been reached**. The carrier differs by layer: review scope, role delegation, semantic/state mismatch, persistent repository residue, memory recall, static retrieval, or context compression. Stage II therefore supports CPR as linked process dimensions expressed through different carriers, not as three framework-specific labels.

The evidence does **not** support a framework ranking, an occurrence-rate estimate, or a claim that any named framework causes the observed behavior.

## Evidence comparability boundary

T1 and T2/T3 are not symmetric rows. X2–X7 in T1 are dominated by the frozen v1 subject-to-action envelope mismatch. T1 is therefore retained as a valid natural diagnostic row, but its terminal outcomes are not compared quantitatively with T2/T3 as if all three tasks used the same interface contract.

The prospective v2 clarification removes that admission bottleneck for T2/T3 without rewriting T1. This makes the correct cross-task comparison:

`T1 = natural historical diagnostic + layer behavior around the interface gate`

versus

`T2/T3 = prospective process observations after the gate is made model-visible`.

X1 is the exception in interface mechanics: it retains the native AutoGen tool interface in all three tasks and never uses the custom action-contract helper.

## 7 × 3 cross-task matrix

| Layer / system | T1 — version review | T2 — feature request | T3 — legacy retirement | Cross-task reading |
| --- | --- | --- | --- | --- |
| **X1 AutoGen** | Complete native chain; 102 events; changes `run.py`, `legacy_compat.py`, tests; terminal “release-ready” language exceeds live-service verification | Payment button is implemented, then review expands into `run.py`, UI-test/cart-source concerns; 129 events; max-turn QA handback | Runtime path is cut, legacy server neutralized, tests/docs/version text expanded; 135 events; max-turn Product Ops handback | Same native interface repeatedly shows **useful artifact completion plus a release/process boundary broader than the direct user request**. T2/T3 both fail to close cleanly after substantive work. |
| **X2 MetaGPT** | v1 envelope bottleneck dominates; only 3 accepted actions | 109 accepted actions; requested UI files written; QA/verification persists; no terminal closure | 113 accepted actions; repeated investigation/delegation; direct-launcher repair arrives near budget end; no closure | After the interface gate is removed prospectively, two different tasks both expose **verification/delegation persistence rather than parser failure**. |
| **X3 A2A** | Outer A2A entry works, but internal delegation is not reached under v1 | 22 A2A / 21 role-to-role calls; repeated claimed-revision → file-read mismatch → correction/review loop; scope expands into launcher/tests | 14 A2A / 13 role-to-role calls; functional cut occurs, but empty legacy module remains and repeatedly re-enters review because no delete action exists | Strongest cross-task semantic/process recurrence: **downstream observed state can keep reopening work after an upstream role says the state is resolved**. In T2 the object is current revision state; in T3 it is historical residue. |
| **X4 MCP** | MCP boundary never reached | Six MCP operations, then preserved provider-format failure | 126 MCP calls; launcher fixed; terminal report describes broader cleanup than frozen tree actually contains | Shows why “layer present” and “layer effect” must be separated. Once deeply exercised, T3 yields a concrete **report/state divergence** after extensive inspection. |
| **X5 RAG** | 32 retrievals; one static query/hit serialization; no task execution | 32 retrievals remain static while feature is written and role scope expands | 32 retrievals remain static; exact causal files are absent from hit set; no checkout write | Stable negative structure across all tasks: **retrieval activity is not semantic evolution**. The RAG layer can be continuously active while its contribution stays fixed. |
| **X6 MemoryBank** | 32 writes, 31 retrievals, 90 recalled items; early malformed exchanges are repeatedly recalled and strengthened | Two early exchanges are written/recalled, then preserved provider-format failure | Finalizes in 3 turns; 3 writes, 2 retrievals, 2 recalled items; direct launcher fix | Memory dynamics are trajectory-dependent. T1 contains a real **C→R feedback carrier**; T3 demonstrates that the mere presence of memory does not imply long temporal inertia. |
| **X7 LongLLMLingua** | 32 calls but effectively 100% retention: compression is a no-op | 18,805 → 10,257 total tokens; mean per-call retention ≈63.3%; visible text distortion; no checkout write | 32,890 → 15,615 total tokens; mean per-call retention ≈55.9%; stronger visible distortion; no checkout write | Strongest repeated layer-specific transformation. Once context is long enough, **lossy context transformation recurs across two different tasks**. Causal effect on non-closure remains unproven. |

## Task-axis audit

### T1: state construction and the interface boundary

T1 asks the systems to determine what changed, whether the update works and what should be fixed. That makes the core process epistemic: inspect artifacts, form a system-state account, verify it and act.

The v1 action-envelope mismatch dominates X2–X7, so T1 cannot be used as a clean cross-system performance row. It still exposes three important layer behaviors before/around the gate:

- X5 repeatedly injects the same retrieval context without semantic evolution.
- X6 repeatedly writes, recalls and strengthens earlier malformed exchanges, creating a closed temporal feedback route.
- X7 is genuinely invoked but performs no measured compression on the short contexts.

T1 therefore establishes an important cross-layer baseline: **having a layer in the process does not mean that layer transformed the process**.

### T2: implementation followed by process expansion

T2 removes the dominant parser-admission ambiguity prospectively. X2, X3, X5 and X7 produce 99–128 accepted actions; X4 reaches MCP before its preserved provider-format stop.

The row-level phenomenon is not “the systems cannot build a payment button.” X1, X2, X3 and X5 all write the requested UI feature or a variant. The stronger observation is:

`requested output exists → review / verification / collaboration opens new work → terminal closure is deferred`.

X1 and X3 explicitly widen the file/task boundary beyond the original feature. X3 additionally shows a semantic state-reconciliation loop: a role reports that a revision exists, another role reads the actual artifact and finds a different state, and the mismatch opens another edit/review cycle.

This is the clearest Stage-II **P-like** natural row, with C-like state reconciliation feeding that expansion in X3.

### T3: functional cut versus historical residue

T3 separates several notions that ordinary success/failure metrics collapse:

1. Is the old runtime route disconnected?
2. Is the old structural artifact removed or neutralized?
3. Are documentation/version/release semantics aligned with the new state?
4. Does the process itself close?

X1/X2/X3/X4/X6 functionally cut the old launcher route in different ways, yet the rest of the state does not always close with it. X3's empty `legacy_compat.py` remains process-relevant and repeatedly re-enters review. X4's terminal account closes more of the legacy cleanup semantically than the frozen tree closes structurally.

T3 therefore supplies the clearest Stage-II **R-like historical-residue observation** and an independent **C-like report/state divergence**.

## Cross-layer mechanism audit

### 1. Information / C dimension: information state is not identical to persisted state

Three distinct carriers converge on the same descriptive dimension:

**X3-T2 — collaborative state reconciliation.**
A claimed revision is followed by a downstream file read that observes a different state. The discrepancy becomes new system information and opens another correction/review cycle.

**X4-T3 — terminal semantic closure exceeds structural closure.**
The final answer describes legacy-path / release-manifest cleanup more completely than the frozen checkout tree supports. The functional launcher fix is real, but the semantic report incorporates a stronger completion state.

**X7-T2/T3 — carrier transformation before downstream use.**
The context itself is compressed and visibly distorted. T1 provides a useful negative comparison: the same layer is present but effectively no-op when context is short.

These are not the same mechanism, but they support one cross-layer statement: **system information can be transformed, reconciled or semantically closed at a different state from the underlying source artifact.**

### 2. Permission / P dimension: task boundary can grow without the user target changing

The clearest repeated carriers are X1 and X3.

In X1-T2, a narrow payment-button request expands into launcher policy, UI-level testing and cart-source questions. In X1-T3, a launcher repair expands into regression tests, legacy-module neutralization, documentation and version-text cleanup.

In X3-T2, a two-file feature becomes a release/configuration/test reconciliation problem. In X3-T3, the process keeps reopening deletion, stale documentation and regression coverage after the runtime route has already been cut.

X2-T2/T3 supplies a narrower version of the same process pressure: repeated verification/delegation persists until the budget even when the eventual required edit is small.

The cross-layer statement is: **the output target can remain stable while the operational/review boundary expands in pursuit of completeness, consistency or release confidence.**

### 3. Time / R dimension: prior state can remain active through different carriers

Stage II contains at least two non-equivalent temporal carriers.

**Memory carrier — X6-T1.**
Earlier model/system exchanges are written, recalled and strengthened. The early malformed items become the dominant recalled memories while the later parser-compatible turn remains weak and unrecalled.

**Repository / process-residue carrier — X3-T3.**
The runtime influence of the old path is neutralized, but the historical module remains present. Reviewer repeatedly treats that residue as a release condition, so a past structure continues constraining the later process after its original functional role has been removed.

The second observation is especially important for scope: **R is not synonymous with a memory product or a recursion counter.** Temporal persistence can be carried by repository state, shared state, message history, configuration, or any other artifact that later process stages continue to read as authoritative/relevant.

## Dynamic CPR cross-penetration

The complete matrix supports linked directions rather than isolated labels.

**C → P — X3-T2:** a mismatch between claimed and observed state creates new coordination, edits and review.

**P → C — X1-T2 / X3-T2:** expanded review opens new files and concerns (launcher policy, cart source, test coverage), which then become new information premises for the system.

**C → R — X6-T1:** an earlier exchange is written into memory, recalled later and strengthened; information becomes a temporal carrier.

**R → P — X3-T3:** historical residue remains readable/relevant and repeatedly reopens review/deletion work.

These paths are observable process orderings. They do not by themselves prove counterfactual causality, but they show why CPR should be treated as a dynamic linked system rather than three independent static tags.

## Cross-layer negative evidence that sharpens the mechanism

The negative structures are scientifically useful:

- X5 shows that repeated context access can remain static across all three task families.
- X7-T1 shows that an invoked compression layer can be effectively no-op.
- X6-T3 shows that an active memory layer can coexist with a very short path and no long feedback loop.
- X4-T1 shows that a named boundary can exist in the architecture yet never be reached in the natural trajectory.
- T1 X2–X7 show that an upstream interface contract can dominate everything below it.

Together these prevent a weak interpretation in which every added layer is automatically called CPR. **The relevant object is the observed transformation / boundary expansion / temporal carry-forward path, not the component name.**

## Stage-II CPR correspondence frozen by this audit

This audit freezes a **descriptive correspondence**, not a causal framework ranking:

| Dimension | Stage-II operational correspondence | Strongest frozen examples | Boundary |
| --- | --- | --- | --- |
| **C — information penetration / transformation** | System information changes status, representation or semantic closure relative to the source/persisted artifact, and the transformed state is available to downstream process | X3-T2 state-reconciliation loop; X4-T3 report/tree divergence; X7-T2/T3 lossy context transformation | Does not mean every semantic difference is erroneous or harmful; named layer causality is not inferred |
| **P — collaboration / task-permission penetration** | Process scope opens new files, roles, verification questions or release conditions beyond the immediate user-visible target while pursuing the same goal | X1-T2/T3; X3-T2/T3; X2-T2/T3 persistence | Does not mean all additional work is unnecessary; the observation is boundary growth and closure deferral |
| **R — temporal penetration / inherited inertia** | Earlier state remains process-relevant later through recall, artifact persistence or reactivation, including after the original stimulus/function has weakened or disappeared | X6-T1 memory strengthening; X3-T3 historical residue re-entry | Does not require explicit memory or recursion; one natural path is not an occurrence-rate estimate |

This correspondence is consistent with the Stage-I CPR definitions and extends their observable carriers across AI-system layers. It does not redefine CPR by framework brand.

## What the 21-cell matrix now supports

The frozen matrix supports the following research claims at the descriptive/mechanistic-observation level:

1. Different AI-system layers expose different carriers of process-reality divergence under one unified software-engineering environment.
2. The same higher-order process dimensions recur under different task pressures rather than appearing only in one prompt type.
3. Useful or correct local output does not imply process closure.
4. Historical influence can survive functional deactivation as structural/semantic residue.
5. Information-layer activity is not enough: the audit distinguishes static exposure, no-op transformation, lossy transformation, memory reinforcement and report/state divergence.
6. CPR dimensions can cross-penetrate in observed sequence (C→P, P→C, C→R, R→P).

The matrix does **not** support:
- a seven-framework performance ranking;
- a general population frequency;
- a claim that a named framework caused an outcome;
- a claim that every extra review step is harmful;
- a claim that compression caused X7 non-completion;
- a claim that MemoryBank generally creates inertia.

## Remaining-contrast decision gate

C1/C2 are already spent on the action-contract/interface ambiguity. The remaining budget is **2/4 reserved**.

The full audit now identifies two mechanisms that are sufficiently repeated and localizable to justify prospective contrast designs, but **neither contrast is authorized or spent by this audit**.

### C3 candidate — X7 local information-transformation discrimination

Rationale: T2 and T3 independently show materially lossy compression; T1 shows the same layer as a no-op when context is short.

Minimal design: choose one already-frozen X7 T3 parent node with strong measured compression. Fork once from that exact parent. A keeps the frozen official compression behavior; B bypasses compression for that single context transformation only. The experimenter exits immediately and subsequent native process is observed under the same contract. No natural trajectory is rerun and no framework is modified.

Discriminating question: **does changing only that one information-carrier transformation alter the subsequent semantic/action lineage?**

### C4 candidate — X3 T3 historical-residue discrimination

Rationale: after the launcher route is functionally cut, the still-present `legacy_compat.py` repeatedly re-enters reviewer decisions.

Minimal design: choose the first frozen X3-T3 parent node at which the runtime route is already neutralized and reviewer identifies the residual legacy file. A preserves the frozen residue. B performs exactly one local content-addressed removal of that residual file (or an equivalent structured repair package scoped only to that artifact), then the experimenter exits.

Discriminating question: **does removing the historical carrier once collapse/re-route the later review loop, or does the old state persist through messages/shared semantics even after the artifact is gone?**

These two candidates target different CPR mechanisms: C3 targets information transformation; C4 targets temporal residue. Selection/authorization remains a separate gate.

## Final Stage-II natural-phase conclusion

The natural phase is closed at **21/21**. Its strongest result is not that one framework “wins” or that all systems fail the same way. It is that process reality separates into observable layers:

`source / artifact state → carrier → transformation or persistence → downstream reading → collaboration consequence → closure or re-opening`.

T1, T2 and T3 expose different parts of that chain. The cross-layer evidence shows that information transformation (C), process-boundary expansion (P), and temporal carry-forward (R) can appear through different technical carriers and can feed one another during operation.

No further natural sampling is required for Stage II. The next scientific gate is prospective authorization of zero, one or both minimal discriminating contrasts after reviewing the two frozen candidate designs above.
