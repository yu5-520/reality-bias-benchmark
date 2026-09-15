# CN-R-041 — Reviewer v2 Paid-Launch Preflight Gate

Date: 2026-09-15  
Status: **PASS — EXACT PAID-LAUNCH INPUTS FROZEN; PAID REVIEW STILL NOT AUTHORIZED**

## Decision

The Reviewer-v2 Base re-annotation has reached the final pre-payment gate.

The exact semantic-review population, packet files, prompts, model configuration, retry/expansion rules, provider-model identity rule and repository-level spend ceiling are now frozen before any paid Reviewer-v2 call.

This Change Note does **not** authorize a provider call.

## Exact population

The future clean Reviewer-v2 pass remains the full frozen Base population:

- R2: 70 units;
- R3: 70 units;
- R4: 4 units;
- total: **144 units**.

Selection is not conditioned on historical Reviewer A/B disagreement status.

## Exact packet bindings

The zero-call preflight (`34992898867`) passed with no errors and no provider calls.

Packet files are bound by SHA256:

- R2 v0.1: `c23522f9916530b4a342c2fd4b2cc028bb8613d0b8626cdc0d76ed9bc1ded63f`
- R3 v0.2: `7cbe61987172f6dd2fa6f547766c145ddf8782d5fc7ec1bf3762b06fb0db0151`
- R4 v0.1: `fe0a7d24a2d8fa4f102da9883529bebbcef9be0397057f3b8a23230754ee393a`

The underlying Base evidence batch remains:

`94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`.

The preflight manifest hash is:

`38288a8ceb51d2c95148f9ceca206c93efa0597244e67b7751919d85e9eebccc`.

## Prompt / model bindings

Prompt hashes remain:

- R2: `88cc842ea12030530abd43563b8d6c9d6fb82ef25f997bcd9f55831c4794a924`
- R3: `e3b2aaafb0ac344b9d92ce3b0c8e0b0dd1fe2693a78b773c5bb3afd8e432373d`
- R4: `626ace9b857e352380801eb4d125d387af97953ee184b692aa9981b0b2ed12af`

Model config SHA256:

`fe7bbafda1c4c12b1d1f5dca963d1a45cbe503713aaa486fac09f569d1b5f8c5`.

Configured model alias is `deepseek-flash`; the historical provider response identity accepted for this re-annotation transport is also frozen as `deepseek-flash`.

A different returned provider model is a stop condition rather than being silently pooled.

## Request-volume boundary

After R3 v0.2 structural compaction, the selected 144 packet files occupy `4,341,898` bytes including JSONL newlines. Repeating the frozen system prompt for every unit adds `427,562` bytes, for a combined pre-provider-wrapper serialized body of `4,769,460` bytes.

These are byte-volume measurements only. They are not exact token counts and are not monetary-cost estimates.

## Runtime / stop policy

The first paid v2 pass, if authorized, is frozen to one worker. Valid semantic `UNCERTAIN` is final and does not trigger retry. Malformed output may receive at most two bounded recovery attempts. A packet may request at most one explicit frozen-ref expansion. Reviewer failure never triggers subject rerun and partial review records remain preserved.

The pathological engineering envelope is six provider calls per unit if every format attempt also consumes its one expansion, or 864 calls over all 144 units. This is a safety envelope, not expected use; the spend ceiling and earlier stop conditions are intended to stop long before such a pathological path.

## Spend gate

The repository-level absolute ceiling for this first v2 pass is frozen at **USD 2.00** under the repository's 2026-09-15 price snapshot.

This is not authorization to spend USD 2.00.

The actual `launch_max_spend_usd` remains unset. A later authorized launch record must choose a positive amount no greater than USD 2.00 and bind that value immutably before provider access.

## Stronger activation lock

The DeepSeek Reviewer-v2 adapter is now `R234-REVIEWER-V2-DEEPSEEK-ADAPTER-v0.2`.

Offline workflow `34993080553` passed. CLI flags alone can no longer activate a real review. Before the provider credential is read, the adapter requires a separate immutable launch record whose:

- status is `AUTHORIZED`;
- `execute_real_api` is true;
- authorization reference matches the command;
- packet SHA256 and unit count match;
- model-config and prompt hashes match;
- retry/expansion settings match;
- price mode and launch spend match;
- launch spend does not exceed the repository absolute ceiling.

Returned model identity is checked after every provider response and an unexpected model aborts the pass.

## Immutable launch-record rule

A non-executable template now exists at:

`reviews/reviewer_system_v2/AUTHORIZED_LAUNCH_RECORD_TEMPLATE_v0.1.json`.

The template must never be converted in place. After explicit user authorization, it must be copied to a new unique file under a launch-record namespace, populated with the authorization reference, authorization time and approved spend ceiling, then left append-only once provider execution begins.

## Scientific interpretation

A future DeepSeek Reviewer-v2 pass is still **re-annotation/calibration under the revised semantic contract**, because DeepSeek already supplied historical Reviewer B. It is not a new independent model-family replication.

No new C/P/R prevalence, cross-reviewer agreement, laundering, black-hole, causal or K-budget finding is established by this preflight.

## Current gate

All safe/no-cost preparation has now reached the payment boundary.

The next valid transition is:

`explicit user authorization → create immutable AUTHORIZED launch record → one-worker real Reviewer-v2 semantic pass over frozen Base evidence`.

Until that explicit authorization exists:

- Reviewer-v2 paid calls remain blocked;
- K=2 remains blocked;
- the subject experiment remains frozen;
- historical Reviewer A/B v1 records remain untouched.
