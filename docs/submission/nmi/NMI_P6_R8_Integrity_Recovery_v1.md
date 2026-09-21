# NMI-P6 R8 Integrity Recovery v1

Date: 2026-09-21  
Status: **RECOVERED APPEND-ONLY CANONICAL COPY / HISTORICAL DEFECT RETAINED**

P6 resolves the repository-ingest integrity defect discovered during the P4 structural-scout calibration. It does **not** rerun subjects, re-adjudicate trajectories, or change any semantic result.

## Historical object retained

Path:

`results/r8_trajectory_first_second_audit_v0_1/trajectory_second_audit_records.jsonl.gz`

Frozen repository state:

- size: **14,999 bytes**;
- SHA-256: `c047ae222f6bd4a58e57c109d9c573b0180e0fa3ea5c48ad4f49857098deb508`;
- Git blob: `2f0b3690c19394425221e0c4a6f75d79ac34464e`;
- gzip readable: **false**;
- matches the original R8 manifest's declared compressed hash: **false**.

The historical object is intentionally left unchanged so the ingest defect remains auditable.

## Recovery source

Previously frozen external package:

`r8_second_audit_with_ecommerce_discovery_v0_2.zip`

Package SHA-256:

`cf4d3d8158cc1bbd76649e6f236217283c4f5b3a33d3531ae400325141b44966`

The recovered internal R8 record file was verified before repository insertion.

## Canonical recovered copy

Path:

`results/r8_trajectory_first_second_audit_recovered_v0_2/trajectory_second_audit_records.jsonl.gz`

Verified identity:

- gzip size: **90,834 bytes**;
- Git blob: `bdab2569753a7734c84ce4f203551cbbbafa566c`;
- compressed SHA-256: `d8e51328f23ff6619fef5dce37f5768de319d16c3be0e7b478d27c7b614d9957`;
- gzip readable: **true**;
- uncompressed size: **629,892 bytes**;
- uncompressed SHA-256: `f4b1ee053d47fb3fe5b681831acd37469549af0f741660b81e28fb0df54f3e61`;
- non-empty JSONL records: **141**.

Both the compressed and uncompressed hashes exactly match the values declared by the original frozen R8 repository manifest.

## Scientific boundary

This recovery changes **repository byte integrity only**.

It changes none of the following:

- trajectory contents;
- C/P/R adjudications;
- coupling counts;
- censor status;
- source selection;
- manuscript claims;
- denominators;
- semantic-review chronology.

No subject, provider, evaluator or semantic-adjudication execution was performed for P6 recovery.

The correct canonical policy is therefore:

`historical malformed object retained + verified recovered copy appended`

not:

`historical object overwritten`.
