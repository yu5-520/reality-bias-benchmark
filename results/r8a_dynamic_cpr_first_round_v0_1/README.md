# R8-A Dynamic CPR first-round derivative material

This directory intentionally stores only the compact `summary.json` in Git source.

The complete derivative package contains:

- `case_index.jsonl`;
- `semantic_event_ledger.jsonl`;
- `permission_review_packets.jsonl`;
- `summary.json`;
- `manifest.json`.

The complete ledger is not committed inline because it is a multi-megabyte reproducible derivative of already-frozen evidence.

Canonical hashes and source artifact identities are frozen in:

`manifests/r8a_dynamic_cpr_first_round_2026-09-20_v0_1.json`.

Reproduction entry points:

- `configs/r8a_dynamic_cpr_first_round_source_binding_v0.1.json`;
- `arena/build_r8a_dynamic_cpr_first_round.py`;
- `scripts/validate_r8a_dynamic_cpr_first_round.py`;
- `.github/workflows/r8a-dynamic-cpr-first-round-materialize.yml`.

Scientific status:

`R8-A COMPLETE / CPR NOT_ADJUDICATED / ZERO NEW SUBJECT RUNS`.
