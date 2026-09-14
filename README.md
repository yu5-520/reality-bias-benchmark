# reality-bias-benchmark

Research repository for the first Reality Bias paper:

**Reality Bias × Authority Penetration × Multi-Agent Dynamics**

## Current research state

- R0 Theory Freeze: complete, patched to v0.2 after R1 counterexamples.
- R1 Theory Stress Test: PASS WITH CONTRACT PATCH (CN-R1-001).
- R2 Primary Mapping: design frozen for first real-model Wave 1; GitHub Actions runs 3 smoke cells and then 252 experimental cells using DeepSeek V4 Flash.

## Repository map

- `theory/` — theory contract, change notes, novelty matrix.
- `benchmark/` — R1 casebook and R2 benchmark items.
- `conditions/` — frozen R2 condition definitions.
- `configs/models/` — frozen provider/model settings (no secrets).
- `adapters/` — provider transport layer.
- `runners/` — real-model experiment runner.
- `evaluation/` — scoring specification.
- `analysis/` — item/dimension analysis.
- `manifests/` — Wave 1 run matrix and repeat policy.
- `docs/` — R1/R2 decisions and protocol notes.
- `.github/workflows/` — reproducible execution entry point.

## Secret

GitHub Actions expects a repository secret named `DEEPSEEK_API_KEY`. The key must never be committed to the repository.

## R2 execution

The first real run is triggered by the R2 workflow. Each of 252 experimental cells uses one subject call and one blinded evaluator call. Raw subject text, evaluator evidence, provider-returned model identity, timestamps, token usage, hashes, and cost estimates are retained in the workflow artifact.

Mock/dry-run outputs are engineering validation only and are not scientific evidence.
