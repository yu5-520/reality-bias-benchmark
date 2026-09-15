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
  - v0.2 therefore separates activation from execution and adopts an explicit pending-work scheduling policy.
  - subject generation and semantic review are now separated by an immutable evidence boundary.
- R2/R3/R4 are event, relation and feedback-loop audit layers over the same Arena evidence; they are not sequential subject-experiment phases.
- Evidence is captured during execution and audited asynchronously. Layer-specific Gates govern claims, not collection. The five-run sample does not prove causal propagation or self-reinforcement.
- Current research plan: [R Plan v2.0](docs/R_Plan_v2.0.md), registered by [CN-R-024](theory/change_notes/CN-R-024_structural_layers_async_audit.md).

## Repository map

- `theory/` — theory contract, change notes, novelty matrix.
- `benchmark/` — R1 casebook and retained single-turn R2 pilot benchmarks.
- `arena/` — Free-Agent Arena runtime, evidence capture, objective metrics, review packet export and optional deferred-review adapters.
- `arena/config/arena_v0.2.json` — current Arena execution policy.
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

`prepare → subject run → save raw evidence → integrity validation → objective statistics → export review packets → RUN_COMPLETE_PENDING_REVIEW`

A subject run does **not** automatically call a paid evaluator.

Raw evidence binds task/agent/model/config/code versions and hashes. Evidence-v0.2 records model inputs, raw outputs, parsed actions, message lifecycle, invocation execution, state history, FINAL/revision state, termination, remaining queue, failures and usage where available.

System statistics are factual execution measurements. C/P/R, invocation necessity, revision-basis sufficiency and decision impact are semantic adjudications. If no review exists, reports say `NOT_ADJUDICATED`; absence of a review record is never converted to C/P/R=0.

## Participation terminology

Arena v0.2 reports separately:

- **available** — present in the domain registry;
- **activated** — entered the active collaboration set through accepted routing/invocation;
- **executed** — completed at least one subject-model call;
- **returned/contributing** — produced a realized message/state/revision/final contribution.

Message read/delivery and invocation execution are logged separately. Decision impact is reviewed later.

## API boundaries

GitHub Actions expects `DEEPSEEK_API_KEY`; the key must never be committed.

- Offline validation: `R2 Free-Agent Arena Offline Validation` — no provider API.
- Subject experiment: `R2 Free-Agent Arena Subject Run` — manual `workflow_dispatch`; subject calls require `CALL_REAL_API`; stops at evidence export.
- Deferred review: `R2 Deferred Review Existing Evidence` — manual selection of an existing evidence artifact; default `PREPARE_ONLY`; reviewer calls require `CALL_REVIEW_API`.

Evaluation failure therefore cannot trigger a subject rerun. Multiple later human/model review records can bind to the same frozen evidence batch.

## Version boundary

Arena v0.1.x used a different terminal scheduling policy. Arena v0.2 uses `await_pending_work_before_terminal_finalize`, so accepted pending expert work is allowed to execute before terminal shutdown. v0.1.x and v0.2 must not be silently pooled as the same experimental version.

See:

- `docs/R2_evidence_and_review_protocol_v0.2.md`
- `docs/R2_ecommerce_micro_pilot_report_v0.2.md`
- `theory/change_notes/CN-R2-023_evidence_first_deferred_adjudication.md`

Mock/dry-run/scripted-provider outputs are engineering validation only and are not scientific evidence. Human and multi-model inter-rater reliability remain unmeasured unless explicitly reported from future review records.
