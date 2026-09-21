# Frozen Raw Evidence Access Policy v1

Date: 2026-09-21  
Status: ACTIVE

## Rule

Frozen raw evidence is **publicly readable/downloadable but not rewritten**.

The repository separates two concerns:

- runtime working directories remain ignored because they are mutable execution surfaces;
- completed evidence packages are published to the public frozen-raw-evidence-v1 GitHub Release after their historical artifact SHA-256 values are verified.

This means:

`runtime raw != published frozen raw`

and:

`frozen != hidden`

## Public evidence surface

Release:

https://github.com/yu5-520/reality-bias-benchmark/releases/tag/frozen-raw-evidence-v1

Repository catalog:

`evidence/frozen_raw/`

The public release contains 24 byte-preserved historical evidence archives covering:

- e-commerce discovery history;
- the held-out natural R2-R4 cohort;
- canonical R5 raw batches, including second-wave recovery;
- R7 raw historical/canonical runs;
- earlier R2-R6, R5MID and R6D mechanism evidence.

## Integrity

Each release asset is bound by:

- historical GitHub Actions artifact ID;
- historical artifact digest;
- public release asset name;
- SHA-256 in `evidence/frozen_raw/SHA256SUMS_v1.txt`;
- per-artifact internal file catalog.

The publication workflow refuses to upload an artifact if the downloaded bytes do not match the frozen historical digest.

Existing release assets are preserved; the publisher does not use overwrite/clobber behavior.

## Versioning

If a frozen package is later found to be malformed or incomplete, the old package remains preserved.

A correction must be added as a new version with a new digest and explicit relationship to the historical package. It must not replace the original bytes.

This is the same evidence rule used for the historical malformed and recovered R8 gzip records.

## Runtime directories

The following remain intentionally ignored:

- `results/raw/`
- `results/scored/`
- `results/runs/`

This prevents new executions from accidentally becoming repository evidence before they pass a freeze gate.

The ignore rule is therefore an execution-safety rule, not a visibility rule for completed evidence.
