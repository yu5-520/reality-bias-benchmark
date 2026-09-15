# reality-bias-benchmark

Research repository for the first Reality Bias paper:

**Reality Bias × Authority Penetration × Multi-Agent Dynamics**

## Canonical research scope

The current forward plan is **[R Plan v3.1](docs/R_Plan_v3.1.md)**.

The first paper is a **structural existence / mechanism study**, not an exhaustive industrial Multi-Agent benchmark. The current environment intentionally favors a minimal role-responsibility Multi-Agent system so interaction-level mechanisms can be studied with fewer confounds from heterogeneous models, tool ecosystems, long-term memory, dynamic orchestration, MCP/A2A and external environments.

The current program separates three layers:

1. **Structural emergence** — what actually happened in frozen subject trajectories.
2. **Semantic identification** — how later reviewers classify fixed structures as C/P/R, authorization, adoption, laundering, etc.
3. **Measurement sensitivity** — how those classifications change across contracts, packets, reviewers or model families.

Reviewer disagreement can change layers 2–3. It does not rewrite layer 1.

The v3.1 correction is registered by **[CN-R-045](theory/change_notes/CN-R-045_r_plan_v31_dependency_correction.md)**. R Plan v3.0 and the previous Reviewer-v2 critical-path gate remain historical records.

## Current research state

- R0 Theory Freeze: complete; patched to v0.2 after R1 counterexamples.
- R1 Theory Stress Test: **PASS WITH CONTRACT PATCH** (CN-R1-001).
- Historical R2 Primary Mapping: **PASS WITH CONTRACT REVISION** (CN-R2-016).
- R2 Free-Agent Arena:
  - v0.1.x five-run E-commerce method-development sample is frozen.
  - raw-trace re-audit shows 4/5 short runs activated four agents but executed only one; only run 0005 verified six-agent execution.
  - v0.2 introduced activation/execution separation and the immutable evidence boundary.
  - v0.3.1 separated plan FINAL from episode termination and produced genuine multi-agent execution, but Microbatch 003 completed only 1/3 episodes because two non-truncated subject responses were malformed JSON.
  - current Base subject runtime is **v0.3.2**, which hardens JSON serialization and preserves the same v0.3 social/observation architecture.
  - Format Verify 005 passed transport: 32/32 subject calls were valid on the first response, but the episode reached the 32-turn observation cap with work still queued and is therefore `BUDGET_CENSORED`, not complete.
- **First formal joint C/P/R collection is complete.** `R234-ECOMMERCE-FORMAL-JOINT-CPR-v1` Batch 001 ran three preregistered E-commerce Base traces under one subject condition. All three naturally completed after 9, 8 and 17 turns with executed/returned Agent counts 4, 4 and 6. Evidence batch: `94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`.
- Measurement architecture v2 remains the current structural measurement design over the frozen Batch001 evidence:
  - C v2 = unauthorized epistemic-state promotion.
  - P v2 = unauthorized goal-scope or goal-focus expansion.
  - R v2 = unauthorized retrospective legitimation/regeneration of C/P.
  - R2 = Structural Emergence / Jump Detection.
  - R3 = Propagation / Lineage / Penetration Structure.
  - R4 = Feedback / Loop / Laundering / Black-Hole Dynamics.
- Deterministic machinery may emit structural `*_CANDIDATE` records but must not declare semantic C/P/R truth.
- The existing `R4-STRUCTURAL-FEEDBACK-ROUND-v0.2.1` remains semantic-blind and is retained as the neutral loop locator. A structural loop is not automatically a Reality Bias loop.
- Evidence and review records are append-only. Historical Reviewer A/B v1, Measurement/Reviewer-v2 outputs and all Qwen/Bailian work remain preserved.

## R0-R9 dependency boundary

Under v3.1:

```text
R0 / R1
   ↓
Frozen Subject Evidence
   ├── R2 Structural Emergence
   ├── R3 Propagation / Lineage
   └── R4 Feedback Dynamics
            ↓
           R5 Causal Interruption
            ↓
           R6 Recovery
            ↓
           R7 Boundary Conditions
            ↓
           R8 Reproducibility Freeze
            ↓
      Main-paper evidence
            │
            ├── Manuscript Claim–Evidence Matrix
            │
            └── R9 Supplementary Robustness / External Replication
```

R9 contains cross-reviewer and cross-model semantic robustness, future human IRR and later external/laboratory replication. **R9 does not gate permission to continue R2-R8.**

A reviewer result may strengthen, qualify or limit a claim. Semantic disagreement alone is not an evidence-integrity defect. Hash mismatches, corrupt source records, wrong bindings or deterministic extraction bugs still trigger the normal evidence-audit process.

## Evidence-first Arena lifecycle

The default Arena chain remains:

`prepare → subject run → save raw evidence → integrity validation → objective statistics → machine structural index → export semantic review windows → append independent reviews later`

A subject run does **not** automatically call a paid evaluator.

Raw evidence binds task/agent/model/config/code versions and hashes. Current traces record model inputs, raw outputs, parsed actions, message lifecycle, invocation execution, runtime snapshots, state history, FINAL/revision state, termination, remaining queue, failures, usage and incremental journal records where supported by the source version.

System statistics are factual execution measurements. C/P/R, goal necessity, semantic adoption, decision effect, retrospective laundering, authority penetration, self-reinforcement and decision impact are semantic adjudications. Review records are append-only: a later reviewer does not overwrite an earlier reviewer.

Current objective termination states remain distinct:

- `RUN_COMPLETE` — natural recorded completion;
- `BUDGET_CENSORED` — observation/safety boundary reached with unfinished work; negative findings are prefix-scoped;
- `LOOP_BUDGET_COMPLETE` — configured K condition reached; condition-complete but not natural quiescence or full-episode completion.

## First formal joint C/P/R experiment

Batch 001 (`workflow run 34970142001`) produced three natural `RUN_COMPLETE` traces and no runner error or censoring. The dedicated workflow froze protocol, manifest, task/Agent/config hashes, raw journals, traces, objective statistics, structural views and review packets in artifact `10397420968` with digest `sha256:ea8ccab5fd890a94dc8e6db3f91f703f0eb09202c3a4278548ffcae0d33b64e5`.

The subject prompts did not expose Bias labels or the expected mapping. This does not mean the environment had no designed pressure: FINAL/late-event structure can intentionally create opportunities for retrospective behavior. Natural-emergence claims therefore rely on semantic non-contamination plus temporal separation, not on pretending the experimental environment is pressure-free.

## Historical semantic review layers and R9 material

Reviewer A (GPT-5.6 Sol interactive, non-blinded) and Reviewer B (DeepSeek isolated blind bundle) remain preserved as historical v1 annotation layers. Their agreement was not high enough to claim semantic consensus, and human inter-rater reliability remains unmeasured.

Reviewer-v2 then introduced a stricter boundary-state contract over the same frozen evidence. The first full DeepSeek Reviewer-v2 pass completed 144/144 units; same-model v1→v2 comparison showed strong measurement-contract sensitivity. Those results are measurement-apparatus observations and do not alter the frozen subject trajectories.

A result-blind independent-v2 bundle was subsequently prepared, followed by Bailian/Qwen transport, runner, launch/preflight, checkpoint, explicit-cache, thinking-control and reasoning-latency engineering. Under v3.1 these assets are retained as **R9 supplementary robustness infrastructure/material**, not as a prerequisite for R4/R5/R6/R7/R8.

The historical file [`docs/R234_v2_current_gate.md`](docs/R234_v2_current_gate.md) is retained as a snapshot of the prior Reviewer-v2 critical-path state. It is no longer the global research gate.

## Current forward execution direction

The current priority is structural/mechanistic density rather than model-coverage density:

`audit subject semantic non-contamination/time order → consolidate R2/R3/R4 structural observations → R4 bounded K probe where scientifically justified → R5 causal interruption → R6 recovery → R7 scoped boundary conditions → R8 reproducibility freeze`

R4 Base and upper-bound studies retain different jobs:

- **Base fixed window:** establishes event/relation measurement under a common observation horizon.
- **Upper-bound loop budget:** uses a semantic-blind structural feedback counter to look farther into persistence/expansion dynamics.
- A different-family reviewer is **not** a prerequisite for K=2.
- Any real paid K=2 subject run still requires frozen runtime/evidence-integrity conditions plus explicit provider authorization and a spending ceiling.
- K=4 may remain gated by a preregistered R4-internal persistence/expansion/amplification criterion and cost policy; cross-model reviewer consensus is not required.

## Supplementary reflexive case

The repository also preserves a non-experimental research-history case in which reviewer robustness work gradually moved onto the structural program's critical path before v3.1 corrected the dependency DAG.

A formal supplementary story template with commit-level timestamps and provenance is stored at:

- [`docs/supplementary/NML_Supplementary_Note_S1_perfection_like_planning_drift.md`](docs/supplementary/NML_Supplementary_Note_S1_perfection_like_planning_drift.md)

This note is explicitly **not** R2-R8 evidence and is not included in C/P/R statistics. It uses the repository history only as a provenance-backed reflexive illustration and as a source of a future hypothesis: Perfection-like cumulative goal drift may also occur in iterative Human–AI collaboration, where locally reasonable and locally authorized expansions accumulate into global goal drift.

## Repository map

- `theory/` — theory contract, change notes and novelty matrix.
- `benchmark/` — R1 casebook and retained single-turn R2 pilot benchmarks.
- `arena/` — Free-Agent Arena runtime, evidence capture, objective metrics, structural views, blind-bundle/review tooling and review packet export.
- `arena/structural_feedback.py` — semantic-blind structural feedback-round derivation.
- `arena/loop_budget.py` — explicit K-condition runtime binding and stop logic.
- `arena/config/arena_v0.3.json` — current Base Arena v0.3.2 execution policy.
- `arena/config/ecommerce_formal_joint_cpr_v1.json` — frozen first formal E-commerce joint C/P/R design.
- `arena/config/arena_v0.3_k2_candidate.json` — engineering-validated K=2 candidate; not paid-run authorization.
- `reviews/` — append-only historical and current semantic-review infrastructure/records.
- `reviews/reviewer_system_v2/` — Reviewer-v2 contracts, blind replication protocol and launch records; forward role is R9 supplementary measurement infrastructure.
- `schemas/evidence_batch_v0.2.schema.json` — immutable evidence-batch interface.
- `schemas/review_record_v0.1.schema.json` — append-only human/model review interface.
- `docs/R_Plan_v3.1.md` — current canonical total research plan.
- `docs/R_Plan_v3.0.md` — historical measurement-architecture plan before dependency correction.
- `docs/R234_measurement_plan_v2.md` — R2-R4 jump/lineage/dynamics measurement architecture.
- `docs/reviewer_system_v2.md` — Reviewer-v2 architecture; retained for R9 robustness work.
- `theory/change_notes/CN-R-045_r_plan_v31_dependency_correction.md` — canonical dependency correction record.
- `docs/supplementary/` — manuscript supplementary material templates and provenance-backed notes.
- `.github/workflows/` — reproducible subject, offline and isolated review entry points.

## API and authorization boundaries

- Offline validation: no provider API.
- Subject collection and semantic review remain separate operations.
- Evaluation/reviewer failure cannot trigger a subject rerun.
- Multiple later human/model review records may bind to the same frozen evidence batch.
- Any new paid model review or paid subject run requires explicit authorization and an explicit spending ceiling.
- Repository planning updates do not constitute paid API authorization.

## Version boundary

Arena v0.1.x, v0.2 and v0.3.x use different terminal/observation or serialization policies and must not be silently pooled. Structural feedback counter versions also remain explicit. Re-deriving deterministic measurements never rewrites frozen subject behavior.

Reviewer and measurement versions are equally explicit. Reviewer A/B v1, Reviewer-v2 and Qwen/Bailian records remain preserved as versioned historical/robustness layers.

Planning versions are also append-only in meaning:

- [R Plan v3.1 — current canonical](docs/R_Plan_v3.1.md)
- [R Plan v3.0 — historical pre-correction](docs/R_Plan_v3.0.md)
- [R Plan v2.1 — historical](docs/R_Plan_v2.1.md)
- [CN-R-045 dependency correction](theory/change_notes/CN-R-045_r_plan_v31_dependency_correction.md)
- [R2-R4 Measurement Plan v2](docs/R234_measurement_plan_v2.md)
- [Reviewer System v2](docs/reviewer_system_v2.md)
- [Historical Reviewer-v2 current gate snapshot](docs/R234_v2_current_gate.md)
- [R2-R4 E-commerce Formal Joint C/P/R v1 protocol](docs/R234_ecommerce_formal_joint_cpr_v1_protocol.md)
- [R2-R4 E-commerce Formal Joint C/P/R v1 Batch 001 result](docs/R234_ecommerce_formal_joint_cpr_v1_batch001_result.md)
- [Cross-model Blind Review Agreement v1](docs/R234_ecommerce_formal_joint_cpr_v1_cross_model_blind_agreement.md)
- [R4 upper-bound loop budget protocol v0.1](docs/R4_loop_budget_protocol_v0.1.md)
- [R4 structural feedback counter v0.2.1 + K2 runtime audit](docs/R4_structural_feedback_counter_v0.2.1_runtime_audit.md)
- [CN-R2-023 evidence-first deferred adjudication](theory/change_notes/CN-R2-023_evidence_first_deferred_adjudication.md)
- [CN-R-024 structural layers and asynchronous audit](theory/change_notes/CN-R-024_structural_layers_async_audit.md)
- [NML Supplementary Note S1 template](docs/supplementary/NML_Supplementary_Note_S1_perfection_like_planning_drift.md)

Mock/dry-run/scripted-provider outputs are engineering validation only and are not scientific evidence. Human inter-rater reliability remains unmeasured until a human review is actually performed.
