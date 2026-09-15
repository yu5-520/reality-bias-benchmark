# reality-bias-benchmark

Research repository for the first Reality Bias paper:

**Reality Bias × Authority Penetration × Multi-Agent Dynamics**

## Current research state

- R0 Theory Freeze: complete; patched to v0.2 after R1 counterexamples.
- R1 Theory Stress Test: **PASS WITH CONTRACT PATCH** (CN-R1-001).
- R2 Primary Mapping: **PASS WITH CONTRACT REVISION** (CN-R2-016).
  - Completion → Information: supported in frozen confirmatory mapping.
  - Perfection → Invocation: supported in frozen confirmatory mapping.
  - Retrospective → Temporal: **not universal**; stateful replication found architecture-dependent route displacement.
- R2 Free-Agent Arena:
  - v0.1.x five-run E-commerce method-development sample is frozen.
  - raw-trace re-audit shows 4/5 short runs activated four agents but executed only one; only run 0005 verified six-agent execution.
  - v0.2 introduced activation/execution separation and the immutable evidence boundary.
  - v0.3.1 separated plan FINAL from episode termination and produced genuine multi-agent execution, but Microbatch 003 completed only 1/3 episodes because two non-truncated subject responses were malformed JSON.
  - current Base subject runtime is **v0.3.2**, which hardens JSON serialization and preserves the same v0.3 social/observation architecture.
  - Format Verify 005 passed transport: 32/32 subject calls were valid on the first response, but the episode reached the 32-turn observation cap with work still queued and is therefore `BUDGET_CENSORED`, not complete.
- **First formal joint C/P/R collection is complete.** `R234-ECOMMERCE-FORMAL-JOINT-CPR-v1` Batch 001 ran three preregistered E-commerce Base traces under one subject condition. All three naturally completed after 9, 8 and 17 turns with executed/returned Agent counts 4, 4 and 6. Evidence batch: `94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`.
- **Semantic review v1 is recorded over all 70 Authority-bearing packets.** Under the primary `realized + UNAUTHORIZED + mechanism-coded` estimand, run-level emergence is C=2/3, P=2/3, R=3/3; the primary Bias × Authority matrix is C: I3/V0/T0; P: I0/V9/T0; R: I2/V5/T4.
- Review v1 is a **non-blinded GPT-5.6 Sol interactive analyst review**, not independent confirmation or reliability evidence. Across all reviewed packets: 49 authorization judgments are AUTHORIZED, 18 UNAUTHORIZED and 3 UNCERTAIN. Human IRR and multi-model agreement remain unmeasured.
- The review distinguishes retrospective behavior from successful Authority penetration: 42 Authority events are R-labeled, of which 29 are authorized, 11 unauthorized and 2 authorization-uncertain. R is therefore not treated as automatically equivalent to unauthorized T revision.
- R2/R3/R4 remain event, relation and feedback-loop audit layers over the same Arena evidence. All four recorded structural feedback rounds in the formal batch co-occur with at least one primary unauthorized Bias event in their anchor→closing intervals, but this is discovery-level co-occurrence rather than causal feedback or self-reinforcement evidence.
- R4 separates **Base fixed-window measurement** from an expensive **upper-bound loop-budget probe**. Initial K values remain restricted to 2 then 4, with K=4 allowed only after a reviewed K=2 persistence/expansion/amplification candidate.
- The current semantic-blind structural feedback counter is **`R4-STRUCTURAL-FEEDBACK-ROUND-v0.2.1`**. It requires the conservative `A settles → B sees/contributes → A demonstrably receives → A settles again` return and permits only superseded, never-exposed anchors to be skipped.
- `R4-LOOP-BUDGET-RUNTIME-v0.1` and a K=2 candidate configuration are implemented and offline validated. **No paid K run has been launched.** Independent blinded replication of Batch 001 is the current measurement priority before deciding whether to spend on a real K=2 batch.
- Evidence is captured during execution and audited asynchronously. Layer-specific Gates govern claims, not collection. Existing structural runs do not by themselves prove causal propagation or self-reinforcement.
- Current research plan: [R Plan v2.1](docs/R_Plan_v2.1.md). Formal collection is frozen by [CN-R-033](theory/change_notes/CN-R-033_formal_batch001_collection.md); the discovery-stage semantic review is registered by [CN-R-034](theory/change_notes/CN-R-034_formal_batch001_model_review_v1.md).

## Repository map

- `theory/` — theory contract, change notes, novelty matrix.
- `benchmark/` — R1 casebook and retained single-turn R2 pilot benchmarks.
- `arena/` — Free-Agent Arena runtime, evidence capture, objective metrics, structural views, review packet export and optional deferred-review adapters.
- `arena/structural_feedback.py` — semantic-blind structural feedback-round derivation.
- `arena/loop_budget.py` — explicit K-condition runtime binding and stop logic.
- `arena/config/arena_v0.3.json` — current Base Arena v0.3.2 execution policy.
- `arena/config/ecommerce_formal_joint_cpr_v1.json` — frozen first formal E-commerce joint C/P/R design.
- `arena/config/arena_v0.3_k2_candidate.json` — engineering-validated K=2 candidate; not paid-run authorization.
- `arena/config/model_deepseek_v0.2.json` — current subject/evaluator transport and token-budget configuration.
- `arena/config/loop_budget_policy_v0.1.json` — inactive paid R4 policy registry and validation records.
- `reviews/formal_batch001_model_review_v1/` — v1 semantic rubric, all 70 compact event codes and aggregate analysis metadata.
- `schemas/evidence_batch_v0.2.schema.json` — immutable evidence-batch interface.
- `schemas/review_record_v0.1.schema.json` — append-only human/model review interface.
- `conditions/` — retained R2 condition definitions.
- `configs/models/` and `arena/config/` — frozen provider/model settings (no secrets).
- `adapters/` — provider transport layer.
- `runners/` — retained benchmark experiment runners.
- `evaluation/` — retained scoring specifications.
- `analysis/` — retained benchmark analysis.
- `docs/` — reports, evidence/review protocol and phase decisions.
- `.github/workflows/` — reproducible execution entry points.

## Evidence-first Arena lifecycle

The default Arena chain is:

`prepare → subject run → save raw evidence → integrity validation → objective statistics → export R2/R3/R4 review material → PENDING_REVIEW`

A subject run does **not** automatically call a paid evaluator.

Raw evidence binds task/agent/model/config/code versions and hashes. Current traces record model inputs, raw outputs, parsed actions, message lifecycle, invocation execution, runtime snapshots, state history, FINAL/revision state, termination, remaining queue, failures, usage and incremental journal records where supported by the source version.

System statistics are factual execution measurements. C/P/R, invocation necessity, semantic dependency, revision-basis sufficiency, authority penetration, self-reinforcement and decision impact are semantic adjudications. Review records are append-only: a later blinded reviewer does not overwrite v1.

Current objective termination states are intentionally distinct:

- `RUN_COMPLETE` — natural recorded completion;
- `BUDGET_CENSORED` — observation/safety boundary reached with unfinished work; negative findings are prefix-scoped;
- `LOOP_BUDGET_COMPLETE` — configured K condition reached; condition-complete but not natural quiescence or full-episode completion.

For a K-bounded trace, negative findings use `LOOP_BUDGET_CONDITION_ONLY`. Remaining queue and pending invocations are preserved rather than erased by the K stop.

## First formal joint C/P/R experiment

The first formal subject condition is E-commerce Base only. C/P/R are reviewed together over the same frozen traces; subject Agents never see these labels.

Batch 001 (`workflow run 34970142001`) produced three natural `RUN_COMPLETE` traces and no runner error or censoring. The dedicated workflow froze the protocol, manifest, task/Agent/config hashes, raw journals, traces, objective statistics, structural views and review packets in artifact `10397420968` with digest `sha256:ea8ccab5fd890a94dc8e6db3f91f703f0eb09202c3a4278548ffcae0d33b64e5`.

Model Review v1 codes all 70 Authority-bearing events. Primary unauthorized Bias emergence is C=2/3 runs, P=2/3 runs and R=3/3 runs. C is concentrated in I, P in V, while R spans I/V/T. The result is explicitly discovery-stage because the reviewer was not blinded to the study hypotheses. See [the review analysis](docs/R234_ecommerce_formal_joint_cpr_v1_model_review_v1.md).

The next measurement step is an independent blinded review of the **same frozen evidence**, followed by agreement/disagreement analysis. Reviewer disagreement must not trigger a subject rerun.

## Base measurement vs upper-bound loop budget

The Base and upper-bound studies have different jobs.

- **Base fixed window:** current common horizon is 32 turns. It establishes reproducible event/relation measurement and fixed-horizon occurrence statements such as “observed by turn 32”.
- **Upper-bound loop budget:** paid collection is planned, not active. K uses a semantic-blind structural feedback counter; runtime never reads C/P/R, Authority-penetration labels, evaluator output or self-reinforcement judgments to count K.
- Counter v0.2.1 requires a recorded A→B→A return and is non-overlapping. Ordinary one-way propagation does not count. A never-exposed settled anchor may be skipped after supersession; an already-exposed open return may not be leapfrogged.
- Initial paid sequence remains strictly `BASE stable → K=2 → deferred review gate → optional K=4 → deferred review gate → STOP`.
- K=4 requires at least one reviewed C/P/R dimension to show a persistence/expansion/amplification candidate after K=2.
- Larger cumulative C/P/R counts alone do not qualify because larger K mechanically creates more observation opportunities. Qualified growth must appear in measures such as new reviewed events per round, affected Agents/fields, propagation depth or re-inheritance/reopen depth.
- Any K greater than 4 requires a new Change Note and explicit cost review.

Existing Base traces may validate a counter version but are never retroactively converted into K-controlled arms. Passing K=2/K=4 supports discovery wording such as persistence or amplification candidate. Causal self-reinforcement still requires later intervention evidence.

## Participation terminology

Arena v0.3.2 reports separately:

- **available** — present in the domain registry;
- **activated** — entered the active collaboration set through accepted routing/invocation;
- **executed** — completed at least one subject-model call;
- **returned/contributing** — produced a realized message/state/revision/final contribution.

Message read/delivery and invocation execution are logged separately. Decision impact is reviewed later.

## API boundaries

GitHub Actions expects `DEEPSEEK_API_KEY`; the key must never be committed.

- Offline validation: `R2 Free-Agent Arena Offline Validation` — no provider API.
- Subject experiment: `R2 Free-Agent Arena Subject Run` — manual `workflow_dispatch`; subject calls require `CALL_REAL_API`; stops at evidence export.
- Formal Base collection: `R2-R4 E-commerce Formal Joint C-P-R v1` — dedicated three-run formal subject collection, no automatic evaluator.
- Deferred review: existing evidence can be reviewed without rerunning subject behavior; future paid model review requires separate explicit authorization.
- K=2 engineering validation: `R4 K2 Runtime Offline Validation` — ScriptedProvider only, no real subject or evaluator provider call.
- Frozen counter audits/re-derivations reuse existing artifacts and make no subject/evaluator calls.

Evaluation failure therefore cannot trigger a subject rerun. Multiple later human/model review records can bind to the same frozen evidence batch.

## Version boundary

Arena v0.1.x, v0.2 and v0.3.x use different terminal/observation or serialization policies and must not be silently pooled as one experimental condition. Current Base v0.3.2 retains `observe_until_quiescent`: FINAL settles a plan, while the episode continues until the work queue becomes empty or an external budget is hit.

The structural counter also has an explicit version boundary. v0.1 was rejected before activation for over-counting one-way propagation. v0.2 established the conservative A→B→A rule. v0.2.1 repairs superseded-unexposed-anchor progression and changes one frozen failed trace from 0 to 1 round. Feedback-round statistics must therefore record their counter version.

Re-deriving frozen traces with a newer deterministic measurement layer does not alter original subject evidence or experimental condition.

See:

- [R Plan v2.1](docs/R_Plan_v2.1.md)
- [R2–R4 E-commerce Formal Joint C/P/R v1 protocol](docs/R234_ecommerce_formal_joint_cpr_v1_protocol.md)
- [R2–R4 E-commerce Formal Joint C/P/R v1 Batch 001 result](docs/R234_ecommerce_formal_joint_cpr_v1_batch001_result.md)
- [R2–R4 E-commerce Formal Joint C/P/R v1 Model Review v1](docs/R234_ecommerce_formal_joint_cpr_v1_model_review_v1.md)
- [R4 upper-bound loop budget protocol v0.1](docs/R4_loop_budget_protocol_v0.1.md)
- [R4 structural feedback counter v0.2.1 + K2 runtime audit](docs/R4_structural_feedback_counter_v0.2.1_runtime_audit.md)
- [CN-R-032 first formal joint C/P/R E-commerce design](theory/change_notes/CN-R-032_first_formal_joint_cpr_ecommerce.md)
- [CN-R-033 formal Batch 001 collection](theory/change_notes/CN-R-033_formal_batch001_collection.md)
- [CN-R-034 formal Batch 001 model review v1](theory/change_notes/CN-R-034_formal_batch001_model_review_v1.md)
- [CN-R2-023 evidence-first deferred adjudication](theory/change_notes/CN-R2-023_evidence_first_deferred_adjudication.md)

Mock/dry-run/scripted-provider outputs are engineering validation only and are not scientific evidence. Human and multi-model inter-rater reliability remain unmeasured unless explicitly reported from future review records.
