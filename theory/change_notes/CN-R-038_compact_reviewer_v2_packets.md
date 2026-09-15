# CN-R-038 — Compact Reviewer v2 Packet Gate

Date: 2026-09-15  
Status: **PASS — OFFLINE COMPACTION / BOUNDED EXPANSION VALIDATED**

## Decision

The Reviewer-v2 evidence interface may use compact structural packets as the default semantic-review input, provided that omitted frozen records remain accessible only through explicit evidence references and at most one bounded context-expansion request per packet.

This change does not alter subject traces, Measurement-v2 structural targets, historical Reviewer A/B records, or semantic mechanism definitions.

## Validation

Workflow `34990393003` completed successfully on frozen Formal Batch001.

- evidence batch: `94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`
- compact packet version: `R234-REVIEWER-V2-COMPACT-PACKETS-v0.1`
- deterministic output hash: `21c4c91faf815fcfd5b9a83ebb2a71ecf48e62ab2ba49f8e88af790621cf8dc8`
- artifact ID: `10405251940`
- artifact digest: `sha256:858988eb84bd798732ae6457e78bd1485c7c46f6461bed5e5d95b11dbc61e8e9`
- R2 packets: 70
- R3 packets: 70
- R4 packets: 4
- paid API calls: 0

## Size result

Full serialized review material across R2/R3/R4 was `14,940,834` bytes. The compact layer is `5,687,695` bytes, or approximately `38.07%` of the full representation, a reduction of approximately `61.93%`.

Layer fractions relative to the full packet representation:

- R2: `36.91%`
- R3: `37.61%`
- R4: `52.19%`

The reduction is an engineering property of the packet serialization. It is not a provider-token or monetary-cost measurement.

## Semantic safety rule

Compaction must remain structural. It may retain target-local task context, state-key indexes/hashes, selected structurally relevant state values, Agent role/private context, inbox, Agent output summary/actions, lineage relations and explicit expansion refs.

Compaction must not use a C/P/R verdict, prior reviewer result, expected C→I/P→V/R→T mapping or disagreement status to choose what evidence to retain.

If the compact packet is insufficient for a semantic boundary judgment, the Reviewer must either:

1. return `UNCERTAIN`; or
2. request the one permitted expansion by an allowed frozen evidence ref.

The Reviewer must not fill omitted evidence by assumption.

## Current gate

The no-cost Measurement-v2 path is now complete through:

`structural index → R2/R3/R4 windows → semantic range packets → compact packets → bounded expansion → deterministic CPR synthesis contracts`.

A paid Reviewer-v2 launch remains blocked until a provider/model, population, retry/expansion ceiling, price snapshot and maximum spend are frozen and explicitly authorized.

No K=2 subject run is authorized by this Change Note.
