# reality-bias-benchmark

Research repository for the first Reality Bias paper:

**Reality Bias × Authority Penetration × Multi-Agent Dynamics**

## Current research state

- R0 Theory Freeze: complete; patched to v0.2 after R1 counterexamples.
- R1 Theory Stress Test: **PASS WITH CONTRACT PATCH** (CN-R1-001).
- R2 Primary Mapping: **PASS WITH CONTRACT REVISION** (CN-R2-016).
  - Completion → Information: supported in frozen confirmatory mapping.
  - Perfection → Invocation: supported in frozen confirmatory mapping.
  - Retrospective → Temporal: **not universal**. Stateful replication found architecture-dependent route displacement, dominated by Information Authority when a writable active-state override exists.
- R2 Free-Agent Arena extension: environment v0.1 prepared for self-organizing multi-agent discovery; real API execution is manually gated and has not been run by the environment-build commit.
- R3 Coupling: next phase; design must use separate Bias-mechanism and Authority-route axes.

## Repository map

- `theory/` — theory contract, change notes, novelty matrix.
- `benchmark/` — R1 casebook and R2 benchmark/micro-workflow items.
- `arena/` — domain-general Free-Agent Arena, minimal Agent Cards, self-organizing routing engine, topology metrics, blinded event coding, and Authority counterfactual replay.
- `conditions/` — frozen R2 condition definitions.
- `configs/models/` — frozen provider/model settings (no secrets).
- `adapters/` — provider transport layer.
- `runners/` — real-model experiment runners.
- `evaluation/` — scoring specification.
- `analysis/` — item/dimension/gate analysis.
- `manifests/` — run matrices and repeat policy.
- `docs/` — phase decisions and protocol notes.
- `.github/workflows/` — reproducible execution entry points.

## Secret

GitHub Actions expects a repository secret named `DEEPSEEK_API_KEY`. The key must never be committed to the repository.

## R2 evidence freeze

Frozen C/P confirmatory run:
- GitHub Actions `34927333961`
- 72 unique API traces → 168 condition cells
- exact matched structural-gate counterfactuals

Frozen R stateful replication:
- GitHub Actions `34927333973`
- 40 fresh micro-workflow traces
- Retrospective primary Authority distribution: I=10, V=0, T=2 among 12 observed R events
- counterfactual realization: Baseline 0.30; I-only 0.05; V-only 0.30; T-only 0.25; Full 0.00

See `docs/R2_decision.md` and `theory/change_notes/CN-R2-016.md`.

## Free-Agent Arena execution boundary

The Arena fixes task/input/goal, agent identities/responsibilities, private information, shared-state interface, resource limits, and external Authority rules. Agent activation count, routing order, communication topology, state writes, and revision behavior are free to self-organize.

- Offline validation workflow: `R2 Free-Agent Arena Offline Validation` — never uses the provider API.
- Real workflow: `R2 Free-Agent Arena Real API Run` — `workflow_dispatch` only; provider calls require the explicit confirmation string `CALL_REAL_API`.

See `docs/R2_free_agent_arena_design.md` and `theory/change_notes/CN-R2-017_free_agent_arena.md`.

Mock/dry-run/scripted-provider outputs are engineering validation only and are not scientific evidence.
