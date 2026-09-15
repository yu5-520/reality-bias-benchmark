# reality-bias-benchmark

Research repository for the first Reality Bias paper:

**Reality Bias × Authority Penetration × Multi-Agent Dynamics**

## Canonical research scope

The current forward plan is **[R Plan v3.2](docs/R_Plan_v3.2.md)**.

The first paper is a **structural existence / mechanism study**, not an exhaustive industrial Multi-Agent benchmark. The current environment intentionally favors a minimal role-responsibility Multi-Agent system so interaction-level mechanisms can be studied with fewer confounds from heterogeneous models, tool ecosystems, long-term memory, dynamic orchestration, MCP/A2A and external environments.

The current program separates three evidence layers:

1. **Structural emergence** — what actually happened in frozen subject trajectories.
2. **Semantic identification** — how later reviewers classify fixed structures as C/P/R, authorization, adoption, laundering, etc.
3. **Measurement sensitivity** — how those classifications change across contracts, packets, reviewers or model families.

Reviewer disagreement can change layers 2–3. It does not rewrite layer 1.

R Plan v3.1 restored the structural/mechanistic dependency DAG. R Plan v3.2 keeps that DAG and adds a trajectory-dynamics interpretation plus a minimal offline experimental-control layer for future R5/R6/R7 work. The relevant forward theory is **[Theory Contract v0.3](theory/theory_contract_v0.3.md)** and the new measurement extension is **[Trajectory Dynamics Measurement Plan v3](docs/trajectory_dynamics_measurement_plan_v3.md)**.

The v3.1 correction is registered by **[CN-R-045](theory/change_notes/CN-R-045_r_plan_v31_dependency_correction.md)**. The trajectory/control alignment is registered by **[CN-R-046](theory/change_notes/CN-R-046_trajectory_dynamics_and_experimental_control.md)**.

## Unified trajectory model

The forward mechanism model is:

```text
multi-source context / probabilistic synthesis
        ↓
latent Escape Propensity
        ↓ realization
observable Jump
        ↓
first-order C/P state deviation candidate
        ↓
adoption / commit
        ↓
propagation / Authority Penetration / inherited inertia
        ↓
challenge / correction / retrospective operation
        ↓
second-order R dynamics or recovery
```

**Escape Propensity is a theoretical latent variable.** The repository does not claim to read a neural/internal “escape probability.” It observes recorded Jump events and can later estimate behavior-level Jump incidence/hazard under repeated frozen conditions.

C and P are treated as first-order deviation mechanisms. R is second-order: reopen/rework/revision alone is not R; R requires an existing C/P deviation or unresolved C/P-derived state plus persistence, regeneration, amplification, laundering, legitimation or normalization. Normal correction is recovery evidence, not an R-positive case.

A key distinction remains:

`reasoning/proposal ≠ operational reality`

and:

`propagation ≠ Authority Penetration`

## Current research state

- R0 Theory Freeze: historical v0.2 remains frozen; forward contract is v0.3.
- R1 Theory Stress Test: **PASS WITH CONTRACT PATCH** (CN-R1-001); v0.3 adds trajectory-level falsifiability without rewriting R1 history.
- Historical R2 Primary Mapping: **PASS WITH CONTRACT REVISION** (CN-R2-016).
- R2 Free-Agent Arena:
  - v0.1.x five-run E-commerce method-development sample is frozen.
  - raw-trace re-audit shows 4/5 short runs activated four agents but executed only one; only run 0005 verified six-agent execution.
  - v0.2 introduced activation/execution separation and the immutable evidence boundary.
  - v0.3.1 separated plan FINAL from episode termination and produced genuine multi-agent execution, but Microbatch 003 completed only 1/3 episodes because two non-truncated subject responses were malformed JSON.
  - current Base subject runtime is **v0.3.2**, which hardens JSON serialization and preserves the same v0.3 social/observation architecture.
  - Format Verify 005 passed transport: 32/32 subject calls were valid on the first response, but the episode reached the 32-turn observation cap with work still queued and is therefore `BUDGET_CENSORED`, not complete.
- **First formal joint C/P/R collection is complete.** `R234-ECOMMERCE-FORMAL-JOINT-CPR-v1` Batch 001 ran three preregistered E-commerce Base traces under one subject condition. All three naturally completed after 9, 8 and 17 turns with executed/returned Agent counts 4, 4 and 6. Evidence batch: `94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`.
- Measurement v2 remains the historical structural measurement contract over frozen Batch001 evidence:
  - C v2 = unauthorized epistemic-state promotion.
  - P v2 = unauthorized goal-scope or goal-focus expansion.
  - R v2 = unauthorized retrospective legitimation/regeneration of C/P.
  - R2 = Structural Emergence / Jump Detection.
  - R3 = Propagation / Lineage / Penetration Structure.
  - R4 = Feedback / Loop / Laundering / Black-Hole Dynamics.
- Measurement v3 extends future work toward Jump incidence, penetration depth, post-Jump inertia, branch intervention and recovery without retroactively declaring old runs to have been preregistered for those metrics.
- Deterministic machinery may emit structural `*_CANDIDATE` records but must not declare semantic C/P/R truth.
- The existing `R4-STRUCTURAL-FEEDBACK-ROUND-v0.2.1` remains semantic-blind and is retained as the neutral loop locator. A structural loop is not automatically a Reality Bias loop.
- Evidence and review records are append-only. Historical Reviewer A/B v1, Measurement/Reviewer-v2 outputs and all Qwen/Bailian work remain preserved.

## R0-R9 dependency boundary

Under v3.2:

```text
R0 / R1
   ↓
Frozen Subject Evidence
   ├── R2 Jump / Structural Emergence
   ├── R3 Propagation / Penetration / Inertia
   └── R4 Feedback / Second-order R Dynamics
            ↓
           R5 Surgical Causal Interruption
            ↓
           R6 Recovery / Recurrence
            ↓
           R7 Boundary Conditions / Orchestration Structure
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

The historical file [`docs/R234_v2_current_gate.md`](docs/R234_v2_current_gate.md) is retained as a snapshot of the previous Reviewer-v2 critical-path state. Its current interpretation is explicitly recorded in [`docs/R234_v2_gate_supersession_note.md`](docs/R234_v2_gate_supersession_note.md).

## Evidence-first Arena lifecycle

The default Arena chain remains:

`prepare → subject run → save raw evidence → integrity validation → objective statistics → machine structural index → export semantic review windows → append independent reviews later`

A subject run does **not** automatically call a paid evaluator.

Raw evidence binds task/agent/model/config/code versions and hashes. Current traces record model inputs, raw outputs, parsed actions, message lifecycle, invocation execution, runtime snapshots, state history, FINAL/revision state, termination, remaining queue, failures, usage and incremental journal records where supported by the source version.

System statistics are factual execution measurements. C/P/R, goal necessity, semantic adoption, decision effect, retrospective laundering, Authority Penetration, self-reinforcement and decision impact remain semantic/contractual adjudications where structure alone is insufficient.

Current objective termination states remain distinct:

- `RUN_COMPLETE` — natural recorded completion;
- `BUDGET_CENSORED` — observation/safety boundary reached with unfinished work; negative findings are prefix-scoped;
- `LOOP_BUDGET_COMPLETE` — configured K condition reached; condition-complete but not natural quiescence or full-episode completion.

## Minimal experimental-control layer

The repository now includes an **offline experimental instrument**, not a product framework:

`Observe → Freeze → Replay deterministic Arena state → Branch → Intervene`

Implemented primitives:

- `arena/experimental_control.py`
- `arena/config/experimental_control_v0.1.json`
- `arena/tests/test_experimental_control.py`
- `docs/experimental_control_layer_v0.1.md`

The layer is **intervention-off by default** and does not alter the current Free-Agent baseline. It freezes deterministic Arena state, verifies content hashes, creates parent-bound branch manifests, supports narrow explicit state interventions, and provides a fail-closed minimal commit gate for future R5 experiments.

A deterministic Arena-state replay does **not** claim replay of provider-internal randomness or hidden model state. New continuations from one frozen parent are new probabilistic branches and receive independent evidence identities.

This enables a future causal form closer to:

`same frozen history + one preregistered intervention → branched continuation`

instead of comparing two runs whose early histories may already differ.

## R5 / R6 forward design

R5 prioritizes surgical intervention over whole-system replacement. Candidate interventions include blocking one Authority route, removing one context/source item, downgrading one epistemic status, blocking one invocation edge, inserting one deterministic state-commit check, or changing one reopen/transition permission.

Proposal generation and operational realization are measured separately. A valid containment result may look like:

`proposal Jump incidence ≈ unchanged`

while:

`penetration depth / descendants / downstream effect ↓`

R6 compares recovery from different distances after a Jump, including checkpoint recovery, local state correction and full rerun where scientifically justified. Recovery metrics include residual descendants, recurrence/regeneration, turns/calls/tokens and provenance reconstruction.

## R7 orchestration boundary

The first high-value organization comparison is:

- **Emergent / Free Routing:** overall goal is given and Agents may dynamically decompose/invoke within policy.
- **Structured / System-Owned Routing:** overall task remains fixed while stage goals, allowed edges and handoff points are externally defined.

The research question is not which architecture is universally “better.” It is whether orchestration structure changes first-Jump location, propagation topology, Authority Penetration, inertia and recovery.

A larger `goal fixed/staged × context continuous/reset-or-compressed` 2×2 design is conditional and should only be added if the smaller comparison leaves those factors confounded.

## First formal joint C/P/R experiment

Batch 001 (`workflow run 34970142001`) produced three natural `RUN_COMPLETE` traces and no runner error or censoring. The dedicated workflow froze protocol, manifest, task/Agent/config hashes, raw journals, traces, objective statistics, structural views and review packets in artifact `10397420968` with digest `sha256:ea8ccab5fd890a94dc8e6db3f91f703f0eb09202c3a4278548ffcae0d33b64e5`.

The subject prompts did not expose Bias labels or the expected mapping. This does not mean the environment had no designed pressure: FINAL/late-event structure can intentionally create opportunities for retrospective behavior. Natural-emergence claims therefore rely on semantic non-contamination plus temporal separation, not on pretending the experimental environment is pressure-free.

## Historical semantic review layers and R9 material

Reviewer A (GPT-5.6 Sol interactive, non-blinded) and Reviewer B (DeepSeek isolated blind bundle) remain preserved as historical v1 annotation layers. Their agreement was not high enough to claim semantic consensus, and human inter-rater reliability remains unmeasured.

Reviewer-v2 introduced a stricter boundary-state contract over the same frozen evidence. The first full DeepSeek Reviewer-v2 pass completed 144/144 units; same-model v1→v2 comparison showed strong measurement-contract sensitivity. Those results are measurement-apparatus observations and do not alter the frozen subject trajectories.

A result-blind independent-v2 bundle was subsequently prepared, followed by Bailian/Qwen transport, runner, launch/preflight, checkpoint, explicit-cache, thinking-control and reasoning-latency engineering. Under v3.2 these assets remain **R9 supplementary robustness infrastructure/material**, not a prerequisite for R4/R5/R6/R7/R8.

## Current forward execution direction

The current priority is structural/mechanistic density and experimental control rather than model-coverage density:

`align theory/measurement → validate offline state-control layer → consolidate R2/R3/R4 structural observations → freeze intervention protocol → R5 branch intervention → R6 recovery → R7 limited orchestration boundary → R8 reproducibility freeze`

R4 Base and upper-bound studies retain different jobs:

- **Base fixed window:** establishes event/relation measurement under a common observation horizon.
- **Upper-bound loop budget:** uses a semantic-blind structural feedback counter to look farther into persistence/expansion dynamics.
- A different-family reviewer is **not** a prerequisite for K=2.
- Any real paid K=2 subject run still requires frozen runtime/evidence-integrity conditions plus explicit provider authorization and a spending ceiling.
- K=4 may remain gated by a preregistered R4-internal persistence/expansion/amplification criterion and cost policy; cross-model reviewer consensus is not required.

## Supplementary reflexive case

The repository preserves a non-experimental research-history case in which reviewer robustness work gradually moved onto the structural program's critical path before v3.1 corrected the dependency DAG:

- [`docs/supplementary/NML_Supplementary_Note_S1_perfection_like_planning_drift.md`](docs/supplementary/NML_Supplementary_Note_S1_perfection_like_planning_drift.md)

This note is explicitly **not** R2-R8 evidence and is not included in C/P/R statistics. It is a provenance-backed reflexive illustration and future hypothesis source only.

## Repository map

- `theory/` — theory contracts, change notes and novelty material.
- `theory/theory_contract_v0.3.md` — forward Escape/Jump/C/P/R/Authority/Inertia/Recovery contract.
- `benchmark/` — R1 casebook and retained single-turn R2 pilot benchmarks.
- `arena/` — Free-Agent Arena runtime, evidence capture, objective metrics, structural views and review packet export.
- `arena/experimental_control.py` — deterministic state snapshot/restore, branch identity and minimal commit-gate primitives.
- `arena/structural_feedback.py` — semantic-blind structural feedback-round derivation.
- `arena/loop_budget.py` — explicit K-condition runtime binding and stop logic.
- `arena/config/arena_v0.3.json` — current Base Arena v0.3.2 execution policy.
- `arena/config/experimental_control_v0.1.json` — intervention-off experimental-control policy.
- `arena/config/ecommerce_formal_joint_cpr_v1.json` — frozen first formal E-commerce joint C/P/R design.
- `arena/config/arena_v0.3_k2_candidate.json` — engineering-validated K=2 candidate; not paid-run authorization.
- `reviews/` — append-only semantic-review infrastructure/records; forward cross-model role is R9.
- `schemas/evidence_batch_v0.2.schema.json` — immutable evidence-batch interface.
- `schemas/review_record_v0.1.schema.json` — append-only human/model review interface.
- `docs/R_Plan_v3.2.md` — current forward research plan.
- `docs/trajectory_dynamics_measurement_plan_v3.md` — forward Jump/penetration/inertia/branch/recovery measurement extension.
- `docs/R234_measurement_plan_v2.md` — historical/current-for-Batch001 R2-R4 structural measurement contract.
- `docs/experimental_control_layer_v0.1.md` — minimal experiment-instrument specification.
- `.github/workflows/` — reproducible subject, offline and isolated review entry points.

## API and authorization boundaries

- Offline validation: no provider API.
- Subject collection and semantic review remain separate operations.
- Evaluation/reviewer failure cannot trigger a subject rerun.
- Multiple later human/model review records may bind to the same frozen evidence batch.
- Any new paid model review or paid subject run requires explicit authorization and an explicit spending ceiling.
- Repository planning/code updates do not constitute paid API authorization.

## Version boundary

Arena v0.1.x, v0.2 and v0.3.x use different terminal/observation or serialization policies and must not be silently pooled. Structural feedback counter versions also remain explicit. Re-deriving deterministic measurements never rewrites frozen subject behavior.

Theory/measurement/planning versions are append-only in meaning:

- [R Plan v3.2 — current forward plan](docs/R_Plan_v3.2.md)
- [R Plan v3.1 — dependency correction baseline](docs/R_Plan_v3.1.md)
- [R Plan v3.0 — historical pre-correction](docs/R_Plan_v3.0.md)
- [Theory Contract v0.3](theory/theory_contract_v0.3.md)
- [Theory Contract v0.2 — historical](theory/theory_contract_v0.2.md)
- [Trajectory Dynamics Measurement Plan v3](docs/trajectory_dynamics_measurement_plan_v3.md)
- [R2-R4 Measurement Plan v2](docs/R234_measurement_plan_v2.md)
- [CN-R-045 dependency correction](theory/change_notes/CN-R-045_r_plan_v31_dependency_correction.md)
- [CN-R-046 trajectory/control alignment](theory/change_notes/CN-R-046_trajectory_dynamics_and_experimental_control.md)
- [Historical Reviewer-v2 current gate snapshot](docs/R234_v2_current_gate.md)
- [Reviewer-v2 gate supersession note](docs/R234_v2_gate_supersession_note.md)
- [NML Supplementary Note S1](docs/supplementary/NML_Supplementary_Note_S1_perfection_like_planning_drift.md)

Mock/dry-run/scripted-provider outputs and experimental-control unit tests are engineering validation only and are not scientific evidence. Human inter-rater reliability remains unmeasured until a human review is actually performed.
