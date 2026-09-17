# R7 Runtime Integration Checklist

Status: engineering/runtime readiness checklist for the exact-source first formal R7 design.

## Existing-runtime reuse

- [x] Existing Arena continuation path reused.
- [x] Existing one-shot runtime-view overlay reused for C1.
- [x] Persistent copied-runtime-view transform implemented for C2.
- [x] Post-parse/pre-realization action transform added to the existing Arena engine for C3.
- [x] Existing event/trace/ledger emitters reused.
- [x] Exact frozen source artifacts and state hashes verified in CI.
- [x] No parallel R7 agent runtime introduced.

## Frozen comparison identity

- [x] Common post-J0 reference parent fixed: `aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c`.
- [x] Natural J0 fixed: E32 / `inventory`.
- [x] Target fixed: `inventory_stockout_assessment_v1.status`.
- [x] Semantic correction fixed: `fact → unconfirmed`.
- [x] Exact C3 pre-J0 checkpoint fixed: `99731abb4ffd1caa2e568a6c2d90987700b3d0b7a66a1c777f811b666912a349`.
- [x] Common post-J0 horizon fixed at 8 agent turns.
- [x] Same task, agents, model binding and Process Reality v0.4 measurement ontology enforced.

## C1 — one-shot

- [x] Exactly one experiment-origin copied-view exposure.
- [x] Overlay consumed after delivery.
- [x] Reinjection count remains zero.
- [x] Common reference parent remains immutable.
- [x] Exposure evidence carries actor/turn and before/after view hashes.

## C2 — persistent field

- [x] Same semantic target/status as C1.
- [x] Same field re-exposed on every eligible downstream turn within the common horizon.
- [x] Every exposure is recorded.
- [x] Repeated visibility does not rewrite the common parent.
- [x] Natural early termination remains censoring rather than being extended.

## C3 — ALR turn-localized recovery

- [x] Exact checkpoint immediately before the authority-ancestor turn is inspectable and hash-bound.
- [x] Entire pre-J0 source prefix is preserved.
- [x] Natural J0-producing turn is re-executed through the ordinary provider/runtime path.
- [x] Raw provider content and raw parsed envelope are retained separately from the applied envelope.
- [x] Only the matching target `write_state.status` commit may be changed from `fact` to `unconfirmed`.
- [x] Action index, delta path, raw/applied hashes and authority class are recorded.
- [x] Revision-lineage plumbing is implemented.
- [x] Common reference parent is never mutated.
- [x] Provider hidden state is explicitly not replayed.
- [x] Zero natural target matches produce `C3_J0_REPRODUCTION_NOT_OBSERVED`, not retry-until-success.
- [x] Multiple target matches fail closed as ambiguous.

## Arena integration

- [x] C1/C2/C3 execute through the real Arena loop in deterministic engineering smoke tests.
- [x] Smoke traces are explicitly labeled `ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE`.
- [x] Smoke verifies C1 one exposure, C2 repeated exposure, and C3 one localized authority transform.
- [x] Source parent/checkpoint immutability is checked after smoke execution.
- [x] Guarded real runner passes preflight without credentials or provider calls.

## Evidence freeze

- [x] R7 raw-evidence freezer implemented.
- [x] Plan, parent, checkpoint, payload, horizon and trace identities are bound.
- [x] Journal and plan-file hashes are recorded.
- [x] Scientific subject evidence requires a bound manual authorization record.
- [x] Engineering smoke evidence is kept in a separate evidence role.
- [x] Raw evidence is frozen before structural derivation.
- [x] Formal workflow uploads the raw frozen artifact before derived analysis.
- [x] Semantic review is deferred and append-only.
- [x] No evaluator failure can trigger a subject rerun because no paid evaluator is in the subject chain.

## Structural derivation

- [x] Process Reality v0.4 reused as primary measurement ontology.
- [x] R7-A C1 vs C2 comparison implemented.
- [x] R7-B C2 vs C3 comparison implemented.
- [x] C3 non-reproduction produces a preserved non-comparable/censored triad rather than zero imputation.
- [x] Frozen-evidence-only derivation path passes offline CI on engineering smoke evidence.
- [x] Semantic CPR remains `NOT_ADJUDICATED`.

## Formal subject workflow

- [x] Zero-call preparation workflow implemented.
- [x] Separate formal subject workflow implemented.
- [x] Real runner requires the exact phrase `CALL_REAL_R7_THREE_ARM_API` plus the execution flag.
- [x] Symmetric per-branch call/spend ceilings and a total ceiling are required.
- [x] Default formal gate contract is recorded in `configs/r7/r7_formal_subject_gate_v0.1.json`.
- [x] Gate contract itself remains `NOT_AUTHORIZED`.
- [ ] Paid subject execution explicitly authorized by the user/manual dispatch.
- [ ] Formal real-model R7 raw evidence collected.
- [ ] Formal raw evidence frozen and archived.
- [ ] Formal R7 structural measurements derived from that frozen evidence.

## Scientific boundary

Engineering readiness is complete enough for a formal run, but no steering/control conclusion exists before the real-model subject traces are collected and frozen. Same-parent repeated triads remain repeated continuations of one parent, not independent samples.
