# R2 Wave 1 — Attempt 1 infrastructure failure and patch

## Attempt 1

Workflow run: `34875060760`  
Commit: `c5cb719429bc84263771fca6b54cedd8e7d2d836`

The API smoke test succeeded for C/P/R. The full 252-cell run then completed valid processing for **250/252** cells. Two cells failed because the blinded evaluator returned malformed/truncated JSON:

- `R2-C02 / structured_io / trial 3`: unterminated JSON string.
- `R2-C04 / i_only / trial 2`: invalid JSON property syntax near the output limit.

The workflow therefore exited before statistical analysis. Attempt 1 is classified as an **infrastructure-format failure**, not an R2 empirical result, and must not be used for PASS/FAIL inference.

## Patch v0.3.1

No benchmark item, subject prompt, Authority condition, hypothesis, temperature, or subject-model configuration was changed.

Infrastructure-only changes:

1. evaluator `max_tokens` increased from 1200 to 1800;
2. JSON-mode responses are validated in the provider adapter;
3. malformed JSON is retried up to three times using the **identical API request**;
4. failed JSON attempts are written to `results/json_format_retries.jsonl` with raw text, response id, usage and parse error;
5. token usage from format retries is aggregated into the successful response for cost accounting;
6. Wave 1 raw/error/audit files are uploaded even if a later attempt fails.

This patch does not change the theoretical or experimental treatment; it only makes the measurement pipeline robust to provider JSON formatting failures.
