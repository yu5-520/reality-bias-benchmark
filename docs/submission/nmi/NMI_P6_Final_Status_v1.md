# NMI-P6 Final Status v1

Date: 2026-09-21  
Status: **P6 COMPLETE / HANDOFF TO P7**

P6 closes the reproducibility blocker without reopening the scientific programme.

## Closed

- recovered the previously frozen valid R8 package;
- appended the 141-record canonical gzip at a new content path;
- matched the original frozen manifest's compressed and uncompressed hashes;
- retained the historical malformed repository object unchanged;
- froze the release locator registry;
- froze submission Data Availability and Code Availability wording;
- advanced the append-only manuscript to v0.13;
- kept all P4/P5 claim boundaries intact.

## Integrity identity

Canonical recovered R8:

- Git blob: `bdab2569753a7734c84ce4f203551cbbbafa566c`;
- compressed SHA-256: `d8e51328f23ff6619fef5dce37f5768de319d16c3be0e7b478d27c7b614d9957`;
- uncompressed SHA-256: `f4b1ee053d47fb3fe5b681831acd37469549af0f741660b81e28fb0df54f3e61`;
- records: **141**.

Historical defective R8 remains immutable.

## Execution boundary

P6 used **zero** new subject runs, provider calls, evaluator calls or semantic adjudications.

No experimental outcome changed.

## Workflow boundary

The legacy `r8a-dynamic-cpr-first-round-materialize` workflow is a separate historical workflow. Its push-trigger failure is not a P6 reproducibility-gate verdict.

The P6 gate is the dedicated NMI-P6 validator over the canonical recovery and release-freeze files.

## Next gate

`NMI_P7_FINAL_EDITORIAL_AND_FORMAT_COMPLIANCE`

P7 should be editorial/formatting-only unless a concrete submission defect is found.
