# CN-R-039 — Reviewer v2 Contract and Locked Adapter Gate

Date: 2026-09-15  
Status: **PASS — OFFLINE CONTRACT / FAIL-CLOSED TRANSPORT VALIDATED; PAID REVIEW NOT AUTHORIZED**

## Decision

The Measurement-v2 semantic-review interface has passed the remaining no-cost engineering gates required before a paid review decision.

This Change Note freezes the distinction between:

- structural packet construction;
- semantic boundary review;
- bounded evidence expansion;
- deterministic C/P/R synthesis;
- provider transport.

No component in this gate changes frozen subject behavior or historical Reviewer A/B v1 records.

## Offline semantic contract

Workflow `34991144340` completed successfully with zero provider calls.

Validated behaviors include:

- R2/R3/R4 output enums and field contracts;
- `UNCERTAIN` as a valid final semantic outcome rather than a retry trigger;
- one expansion request maximum per packet;
- expansion restricted to explicit frozen evidence refs;
- expansion record hashing;
- prompt blindness checks.

The three frozen prompt hashes are:

- R2: `88cc842ea12030530abd43563b8d6c9d6fb82ef25f997bcd9f55831c4794a924`
- R3: `e3b2aaafb0ac344b9d92ce3b0c8e0b0dd1fe2693a78b773c5bb3afd8e432373d`
- R4: `626ace9b857e352380801eb4d125d387af97953ee184b692aa9981b0b2ed12af`

The prompts do not disclose Reviewer A/B results, historical disagreement status, Jaccard overlap, expected C/P/R→Authority mappings or manuscript conclusions.

## Locked DeepSeek transport

Workflow `34991291940` completed successfully with zero provider calls.

The adapter `R234-REVIEWER-V2-DEEPSEEK-ADAPTER-v0.1` was tested to fail closed before reading review inputs when the real-API enable flag is absent.

Any real execution requires all of:

1. `--execute-real-api`;
2. `--authorization-ref`;
3. a positive `--max-spend-usd`;
4. the provider credential.

The adapter limits malformed-output recovery to at most two retries, permits one bounded context expansion, preserves partial records on failure, and contains no subject-rerun path.

## Scientific interpretation of a future DeepSeek-v2 pass

The same DeepSeek model family was already used as historical Reviewer B under Reviewer-v1 definitions. Therefore a new DeepSeek Reviewer-v2 pass must be described as:

> **re-annotation / calibration under a revised semantic contract**

It must not be described as a new independent model-family replication.

A genuinely new model-family reviewer would constitute a separate independent replication layer if its review is frozen before cross-model comparison.

## Current evidence boundary

The current frozen Base evidence remains:

`94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`

The compact Reviewer-v2 packet hash remains:

`21c4c91faf815fcfd5b9a83ebb2a71ecf48e62ab2ba49f8e88af790621cf8dc8`

The clean full-population Reviewer-v2 coverage is 144 units:

`70 R2 + 70 R3 + 4 R4`.

A reduced/staged population is methodologically allowed only when the selection rule and controls are frozen before semantic outputs are observed.

## Current gate

All no-cost engineering required for a Reviewer-v2 launch decision is now complete:

`frozen trace → deterministic structural targets/windows → compact semantic packets → one-ref bounded expansion → boundary-record contract → deterministic mechanism synthesis → fail-closed provider transport`.

The next step is no longer an engineering prerequisite. It is an explicit experimental spending/design decision.

Until explicit authorization is recorded:

- paid Reviewer-v2 calls remain blocked;
- K=2 remains blocked;
- Reviewer A/B v1 records remain untouched;
- no new C/P/R scientific result may be claimed from the v2 engineering layer.
