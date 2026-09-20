# P6 R8 gzip recovery carrier

Status: **READY FOR APPEND-ONLY CANONICAL RECOVERY**

This directory stores a text-safe Base64 carrier for the already-verified frozen R8 full-record gzip. It exists only because the repository write connector used during P6 accepts UTF-8 text rather than raw binary.

## Frozen recovery object

- source package: `r8_second_audit_with_ecommerce_discovery_v0_2.zip`
- source package SHA-256: `cf4d3d8158cc1bbd76649e6f236217283c4f5b3a33d3531ae400325141b44966`
- recovered gzip size: `90,834` bytes
- recovered gzip SHA-256: `d8e51328f23ff6619fef5dce37f5768de319d16c3be0e7b478d27c7b614d9957`
- uncompressed JSONL size: `629,892` bytes
- uncompressed JSONL SHA-256: `f4b1ee053d47fb3fe5b681831acd37469549af0f741660b81e28fb0df54f3e61`
- JSONL records: `141`
- Base64 carrier length: `121,112` characters

## Canonical ordered carrier parts

The recovery workflow MUST concatenate exactly this ordered list:

1. `part-00.b64`
2. `part-01.b64`
3. `part-02.b64`
4. `p03-0.b64`
5. `p03-1.b64`
6. `p04-0.b64`
7. `p04-1.b64`
8. `p05-0.b64`
9. `p05-1.b64`
10. `p06-0.b64`
11. `p06-1.b64`
12. `p07-0.b64`
13. `p07-1.b64`

## Excluded staging artifact

`part-03.b64` is an incomplete failed transport attempt retained as staging history. It is **not** a member of the canonical carrier and MUST NOT be concatenated or treated as evidence.

## Append-only rule

The historical defective object remains at:

`results/r8_trajectory_first_second_audit_v0_1/trajectory_second_audit_records.jsonl.gz`

P6 does not overwrite or delete it. The verified recovery is decoded to a new append-only path:

`results/r8_trajectory_first_second_audit_recovered_v0_1/trajectory_second_audit_records.jsonl.gz`

The recovery changes repository materialization only. It does not create new subject runs, provider/evaluator calls, semantic adjudication or scientific evidence.
