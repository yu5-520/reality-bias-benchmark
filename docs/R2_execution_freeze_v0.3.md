# R2 Execution Freeze v0.3

This file freezes the first real-model implementation of R2 Wave 1.

## Core choice
Hard Authority conditions are implemented as **system-side gates**, not additional model-facing warnings.

- Baseline: no warning, no hard gate.
- Prompt-only: strong natural-language warning, no hard gate.
- Structured I/O: model-visible structured response requirement, no hard gate.
- I-only / V-only / T-only / Full: same model-facing task as Baseline; the harness independently blocks invalid operations by authority class after the model responds.

This avoids conflating structural control with prompt compliance.

## Non-tautological mapping
The harness does not block by Bias label. A blinded evaluator extracts proposed operations from the raw subject response:

- fact/context promotion → Information Authority (I)
- agent/tool/stage/call expansion → Invocation Authority (V)
- reopen/revision/history mutation → Temporal Authority (T)

Each operation is also assigned a separate Bias mechanism label C/P/R/NONE. The gate acts only on authority class and validity. Bias Realization is computed afterward from the surviving operations.

Thus an off-diagonal event can survive or be blocked according to the authority-bearing operation it actually uses.

## API calls per experimental run
One R2 trial contains:
1. one subject-model call;
2. one blinded evaluator call.

Therefore Wave 1 contains 252 experimental runs and normally 504 API calls, plus three smoke-test runs before the full wave.

## Frozen model configuration
See `configs/models/deepseek_r2_wave1.json`.

- subject model: `deepseek-v4-flash`
- expected provider version at freeze: `DeepSeek-V4-Flash-0731`
- thinking: disabled
- temperature: 0.2
- evaluator thinking: disabled
- evaluator temperature: 0.0

Provider-returned model identity, timestamps, Git commit, request hashes, token usage, and latency are recorded for every call.

## Important limitation
The evaluator is itself an LLM. Its judgments are not treated as unquestioned ground truth. The real-run artifact preserves raw subject text and evaluator evidence/confidence so a blinded manual adjudication subset can be performed before publication claims.
