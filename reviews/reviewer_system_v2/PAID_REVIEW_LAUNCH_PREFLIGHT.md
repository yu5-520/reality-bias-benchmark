# Reviewer v2 Paid Launch Preflight

Date: 2026-09-15  
Status: **BLOCKED — EXPLICIT AUTHORIZATION REQUIRED**

This file is a launch gate, not a launch instruction. It does not authorize any provider call.

## Frozen no-cost inputs

Evidence batch:

`94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`

Compact packet layer:

- version: `R234-REVIEWER-V2-COMPACT-PACKETS-v0.1`
- output hash: `21c4c91faf815fcfd5b9a83ebb2a71ecf48e62ab2ba49f8e88af790621cf8dc8`
- R2 packets: 70
- R3 packets: 70
- R4 packets: 4
- total review units for full coverage: 144
- compact serialized material: 5,687,695 bytes
- one bounded context-expansion request maximum per packet

The compact representation is approximately 38.07% of the full packet serialization. This is a byte-volume result, not a provider-token estimate.

## Default scientific population

The cleanest v2 semantic pass is full coverage:

`70 R2 + 70 R3 + 4 R4 = 144 review units`.

This avoids selecting only historical A/B disagreements and avoids conditioning R3/R4 evidence on a prior reviewer's verdict.

A staged/cost-limited design is permitted only if its selection rule is frozen before semantic results are observed and includes negative/control targets. It must be reported as staged discovery, not full-population replication.

## Provider/model decision

Current status: `NOT_SELECTED_FOR_V2_LAUNCH`.

The repository contains a historical DeepSeek evaluator configuration (`DeepSeek-V4.1-Flash`) and a configured API secret path, but using the same model family again under v2 would be a **re-annotation/calibration under a revised rubric**, not a new independent model-family replication.

If a different model family is selected, its provider/model/config must be frozen before the first review output.

## Cost decision

Current status: `NOT_FROZEN`.

Before launch, record:

- price snapshot and source date;
- packet population;
- estimated input-token envelope;
- maximum output tokens per unit;
- maximum format retries;
- maximum context expansions;
- maximum workers;
- hard maximum spend;
- fail-closed behavior if the spend/input envelope is exceeded.

The 5.69 MB compact serialization is suitable for cost preflight, but byte count must not be presented as exact provider token count.

## Retry ceiling

Proposed engineering ceiling, not yet paid authorization:

- valid semantic uncertainty: **no retry**;
- malformed output: maximum **2 bounded format-recovery attempts**;
- context insufficiency: maximum **1 allowed-ref expansion**;
- reviewer failure: must never trigger subject rerun.

## Required launch record

A paid run may start only when a separate launch record freezes all of the following:

1. provider/model and configuration hash;
2. prompt/rubric version hashes;
3. compact packet artifact/hash;
4. exact R2/R3/R4 population;
5. retry/expansion limits;
6. price snapshot and hard spend ceiling;
7. real-API enable flag;
8. explicit authorization reference.

Until then the real-API adapter must fail closed.

## Current decision

`DO_NOT_LAUNCH`.

Next work is engineering only: implement and test the fail-closed Reviewer-v2 adapter, output schemas, bounded expansion path and cost/preflight checks without calling a provider.
