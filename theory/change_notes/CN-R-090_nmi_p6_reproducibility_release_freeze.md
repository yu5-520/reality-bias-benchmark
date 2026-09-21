# CN-R-090 — NMI P6 Reproducibility and Release Freeze

Date: 2026-09-21  
Status: **ACCEPTED / P6 COMPLETE**

P6 repairs a repository-byte integrity defect without changing the frozen scientific object.

The historical malformed R8 object remains immutable:

`results/r8_trajectory_first_second_audit_v0_1/trajectory_second_audit_records.jsonl.gz`

A separately recovered canonical copy is appended:

`results/r8_trajectory_first_second_audit_recovered_v0_2/trajectory_second_audit_records.jsonl.gz`

Recovered identity:

- compressed SHA-256: `d8e51328f23ff6619fef5dce37f5768de319d16c3be0e7b478d27c7b614d9957`;
- uncompressed SHA-256: `f4b1ee053d47fb3fe5b681831acd37469549af0f741660b81e28fb0df54f3e61`;
- Git blob: `bdab2569753a7734c84ce4f203551cbbbafa566c`;
- JSONL records: 141.

These values match the original frozen R8 manifest.

P6 also freezes:

- release claim locators;
- Data Availability wording;
- Code Availability wording;
- manuscript v0.13 reproducibility status;
- dedicated P6 validation.

No subject/provider/evaluator execution, semantic adjudication or experimental evidence mutation occurred.

The legacy `r8a-dynamic-cpr-first-round-materialize` workflow remains historically separate from the NMI-P6 gate.

Next gate:

`NMI_P7_FINAL_EDITORIAL_AND_FORMAT_COMPLIANCE`.
