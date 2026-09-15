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
- R2/R3/R4 are event, relation and feedback-loop audit layers over the same Arena evidence; they are not sequential subject-experiment phases.
- R4 separates **Base fixed-window measurement** from an expensive **upper-bound loop-budget probe**. Initial K values remain restricted to 2 then 4, with K=4 allowed only after a reviewed K=2 persistence/expansion/amplification candidate.
- The current semantic-blind structural feedback counter is **`R4-STRUCTURAL-FEEDBACK-ROUND-v0.2.1`**. It requires the conservative `A settles → B sees/contributes → A demonstrably receives → A settles again` return and permits only superseded, never-exposed anchors to be skipped.
- `R4-LOOP-BUDGET-RUNTIME-v0.1` and a K=2 candidate configuration are now implemented and offline validated. The K=2 scripted validation stopped exactly at round 2 while further work remained queued, proving the stop is a condition boundary rather than natural quiescence. **No paid K run has been launched.**
- Frozen v0.2→v0.2.1 re-audit changed one failed trace from 0 to 1 structural round; this is recorded as a measurement-version difference, not new subject behavior.
- Evidence is captured during execution and audited asynchronously. Layer-specific Gates govern claims, not collection. Existing structural runs do not by themselves prove causal propagation or self-reinforcement.
- Current research plan: [R Plan v2.1](docs/R_Plan_v2.1.md), with K strategy in [CN-R-029](theory/change_notes/CN-R-029_base_then_loop_budget_upper_bound.md), counter history in [CN-R-030](theory/change_notes/CN-R-030_structural_feedback_counter_v02.md), and runtime candidate boundary in [CN-R-031](theory/change_notes/CN-R-031_loop_budget_runtime_candidate.md).

## Repository map

- `theory/` — theory contract, change notes, novelty matrix.
- `benchmark/` — R1 casebook and retained single-turn R2 pilot benchmarks.
- `arena/` — Free-Agent Arena runtime, evidence capture, objective metrics, structural views, review packet export and optional deferred-review adapters.
- `arena/structural_feedback.py` — semantic-blind structural feedback-round derivation.
- `arena/loop_budget.py` — explicit K-condition runtime binding and stop logic.
- `arena/config/arena_v0.3.json` — current Base Arena v0.3.2 execution policy.
- `arena/config/arena_v0.3_k2_candidate.json` — engineering-validated K=2 candidate; not paid-run authorization.
- `arena/config/model_deepseek_v0.2.json` — current subject/evaluator transport and token-budget configuration.
- `arena/config/loop_budget_policy_v0.1.json` — inactive paid R4 policy registry and validation records.
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

System statistics are factual execution measurements. C/P/R, invocation necessity, semantic dependency, revision-basis sufficiency, authority penetration, self-reinforcement and decision impact are semantic adjudications. If no review exists, reports say `NOT_ADJUDICATED`; absence of a review record is never converted to a zero finding.

Current objective termination states are intentionally distinct:

- `RUN_COMPLETE` — natural recorded completion;
- `BUDGET_CENSORED` — observation/safety boundary reached with unfinished work; negative findings are prefix-scoped;
- `LOOP_BUDGET_COMPLETE` — configured K condition reached; condition-complete but not natural quiescence or full-episode completion.

For a K-bounded trace, negative findings use `LOOP_BUDGET_CONDITION_ONLY`. Remaining queue and pending invocations are preserved rather than erased by the K stop.

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
- Bounded structural pilot: `R2-R4 Shared Structure Smoke` — subject only, no automatic paid evaluator.
- Deferred review: `R2 Deferred Review Existing Evidence` — manual selection of an existing evidence artifact; default `PREPARE_ONLY`; reviewer calls require `CALL_REVIEW_API`.
- K=2 engineering validation: `R4 K2 Runtime Offline Validation` — ScriptedProvider only, no real subject or evaluator provider call.
- Frozen counter audits/re-derivations reuse existing artifacts and make no subject/evaluator calls.

Evaluation failure therefore cannot trigger a subject rerun. Multiple later human/model review records can bind to the same frozen evidence batch.

Legacy single-turn calibration workflows are manual-only and are not triggered by Arena/adaptor pushes.

## Version boundary

Arena v0.1.x, v0.2 and v0.3.x use different terminal/observation or serialization policies and must not be silently pooled as one experimental condition. Current Base v0.3.2 retains `observe_until_quiescent`: FINAL settles a plan, while the episode continues until the work queue becomes empty or an external budget is hit.

The structural counter also has an explicit version boundary. v0.1 was rejected before activation for over-counting one-way propagation. v0.2 established the conservative A→B→A rule. v0.2.1 repairs superseded-unexposed-anchor progression and changes one frozen failed trace from 0 to 1 round. Feedback-round statistics must therefore record their counter version.

Re-deriving frozen traces with a newer deterministic measurement layer does not alter original subject evidence or experimental condition.

See:

- [R Plan v2.1](docs/R_Plan_v2.1.md)
- [R Plan v2.0 — frozen predecessor](docs/R_Plan_v2.0.md)
- [R2–R4 shared runtime v0.3](docs/R234_runtime_v0.3.md)
- [R2–R4 observation censoring policy v0.1](docs/R234_censoring_policy_v0.1.md)
- [R4 upper-bound loop budget protocol v0.1](docs/R4_loop_budget_protocol_v0.1.md)
- [R4 structural feedback counter v0.2 audit](docs/R4_structural_feedback_counter_v0.2_audit.md)
- [R4 structural feedback counter v0.2.1 + K2 runtime audit](docs/R4_structural_feedback_counter_v0.2.1_runtime_audit.md)
- [R2–R4 v0.3.1 execution result](docs/R234_v0.3.1_execution_result.md)
- [R2–R4 v0.3.1 Microbatch 003 result](docs/R234_v0.3.1_microbatch_003_result.md)
- [R2–R4 v0.3.2 Format Verify 005](docs/R234_v0.3.2_format_verify_005_result.md)
- [R2–R4 Format 005 censor-aware re-derivation](docs/R234_format005_censor_aware_rederive_result.md)
- [R2 evidence and deferred review protocol v0.2](docs/R2_evidence_and_review_protocol_v0.2.md)
- [R2 E-commerce micro-pilot report v0.2](docs/R2_ecommerce_micro_pilot_report_v0.2.md)
- [CN-R-025 structural runtime v0.3](theory/change_notes/CN-R-025_structural_runtime_v03.md)
- [CN-R-026 v0.3.1 serialization failure](theory/change_notes/CN-R-026_v031_microbatch_serialization_failure.md)
- [CN-R-027 v0.3.2 serialization pass / censoring](theory/change_notes/CN-R-027_v032_serialization_pass_observation_censoring.md)
- [CN-R-028 censor-aware R2–R4 analysis](theory/change_notes/CN-R-028_censor_aware_r234_analysis.md)
- [CN-R-029 base then K2/K4 upper bound](theory/change_notes/CN-R-029_base_then_loop_budget_upper_bound.md)
- [CN-R-030 structural feedback counter v0.2](theory/change_notes/CN-R-030_structural_feedback_counter_v02.md)
- [CN-R-031 K2 runtime candidate](theory/change_notes/CN-R-031_loop_budget_runtime_candidate.md)
- [CN-R2-023 evidence-first deferred adjudication](theory/change_notes/CN-R2-023_evidence_first_deferred_adjudication.md)

Mock/dry-run/scripted-provider outputs are engineering validation only and are not scientific evidence. Human and multi-model inter-rater reliability remain unmeasured unless explicitly reported from future review records.
