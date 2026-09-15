# CN-R-044 — Independent Reviewer-v2 Replication Gate

Date: 2026-09-15  
Status: **BLIND BUNDLE VALIDATED; DIFFERENT MODEL FAMILY NOT YET SELECTED**

## Decision

The next Reviewer-v2 validation layer must be a true independent semantic replication, not another DeepSeek re-annotation.

The first v2 pass and the same-model v1→v2 transition established two things simultaneously:

1. the refined measurement contract can be executed over the full frozen Base population; and
2. semantic output is highly sensitive to the measurement contract.

Therefore the next useful question is whether the **frozen v2 contract** reproduces under a different reviewer model family without result leakage.

## Frozen protocol

`reviews/reviewer_system_v2/INDEPENDENT_V2_REPLICATION_PROTOCOL_v0.1.md`

The independent pass must:

- use a model family different from DeepSeek;
- review all 144 frozen v2 units;
- receive the same exact packets and prompts as the first v2 pass;
- remain blind to all Reviewer A/B v1 results;
- remain blind to the first DeepSeek-v2 result;
- remain blind to same-model v1→v2 transition counts;
- remain blind to expected Authority-route mappings and manuscript conclusions;
- freeze all 144 outputs before any cross-review comparison.

A repeat DeepSeek run may measure same-family repeatability but cannot satisfy this gate.

The current interactive GPT-5.6 Sol conversation also cannot satisfy the blind gate because it has already observed the study hypotheses and the first v2 results.

## Blind bundle validation

Workflow `34996155560` completed successfully with zero provider calls.

Artifact:

- ID: `10406569694`
- digest: `sha256:0defe71e372440bdcea9f5fe6b2bfc3d8fa7b9a0eea569de56cdc89e44739c5e`
- size: `634138` bytes

Blind bundle version:

`R234-INDEPENDENT-REVIEWER-V2-BLIND-BUNDLE-v0.1`

Bundle hash:

`fc46e673c0d21bff9e30ca97a197c3b9dd04c27bf69ba0f3e07849ee6d00638e`

Population:

- R2: 70
- R3: 70
- R4: 4
- total: 144

The deterministic rebuild produced the same bundle hash.

## Expansion corpus

The bundle does not expose the whole repository to a future reviewer.

It contains a sanitized expansion corpus with exactly **162** unique refs that appear in packet `context_expansion.allowed_refs`.

All 162 refs resolve to exact frozen subject event/call records. No extra result-derived context is injected.

Expansion corpus SHA256:

`9ef68ef54a56f50ba81e8a9cca2d0eb1ab33ff7e4b2d4d0de1ace757666b24a3`

This preserves the one-expansion-per-packet rule while making the reviewer workspace independent of the main repository's result directories.

## Blindness validation

The generated reviewer workspace contains:

- exact frozen R2/R3/R4 packets;
- exact frozen R2/R3/R4 prompts;
- the sanitized allowed-ref expansion corpus;
- a manifest.

It does not contain:

- historical Reviewer A/B outputs;
- the DeepSeek-v2 round-001 output;
- historical agreement summaries;
- same-model v1→v2 transition results;
- expected C/P/R→Authority routing;
- manuscript conclusions.

An 18-cue result-leakage scan passed.

## Existing provider capability check

Repository code search found no configured `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY` or `OPENROUTER_API_KEY` transport path.

This is only a repository-code observation; it does not inspect or claim anything about account-level secrets outside the accessible repository interface.

The repository currently has no frozen different-family transport suitable for calling this pass independently.

## Candidate state

`reviews/reviewer_system_v2/independent_v2_replication_candidate_v0.1.json`

Current candidate:

- status: `BLOCKED_PROVIDER_NOT_SELECTED`;
- real API execution: false;
- provider: null;
- model family: null;
- spend ceiling: null;
- explicit authorization: null;
- K=2: false.

## Scientific consequence

At this point the Base evidence has:

- historical cross-model disagreement under v1;
- one complete DeepSeek-v2 re-annotation;
- a same-family v1→v2 measurement-contract sensitivity analysis;
- a validated blind interface ready for a genuinely different reviewer family.

The remaining uncertainty is no longer primarily an engineering question. It is a semantic reproducibility question.

## Current gate

Do not run another DeepSeek pass and call it independent replication.

Do not use this already-informed interactive conversation as a blind reviewer.

Do not start K=2.

The next valid independent-review transition is:

`select different model family → freeze transport/config/pricing → bind blind-bundle hash → explicit paid authorization → run 144 units blind → freeze → compare`.

If a suitable different-family reviewer cannot be obtained, the alternative scientifically useful branch is additional unchanged-Base subject sampling followed by the frozen v2 measurement contract.
