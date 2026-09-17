# R7 Execution Status — 2026-09-17

## Current state

R7 is now implemented through the **formal-run readiness boundary** on branch `r7-structural-inertia-control`. No paid R7 subject call has been launched from this branch.

The current repository state supports three distinct mechanisms:

- `C1_ONE_SHOT` — one prompt-visible experiment-origin correction, then free continuation;
- `C2_PERSISTENT_FIELD` — repeated visibility of the same correction across eligible downstream turns within a fixed horizon;
- `C3_ALR` — rollback to the exact pre-J0 source checkpoint, re-execution of the natural authority-ancestor turn, and a single localized authority-status transform if the target commit naturally reappears.

## Exact source binding

The formal design is bound to frozen R5/natural evidence:

- source R5 plan hash: `a24c98901422bbccfc9a040a6bc14575b1c710edd518c0d9c2facf7a57926351`;
- common post-J0 reference parent: `aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c` (`after_turn:8`);
- C3 recovery checkpoint: `99731abb4ffd1caa2e568a6c2d90987700b3d0b7a66a1c777f811b666912a349` (`before_turn:8`);
- natural J0: E32, actor `inventory`;
- target field: `inventory_stockout_assessment_v1.status`;
- matched semantic correction: `fact → unconfirmed`;
- common horizon: 8 post-Jump agent turns;
- measurement ontology: `RB-PROCESS-REALITY-MECHANISM-MEASUREMENT-v0.4`.

## Runtime implementation complete

Implemented and CI-validated:

1. C1 copied-runtime-view one-shot transform with exactly one direct exposure and no reinjection.
2. C2 copied-runtime-view persistent transform with explicit per-turn exposure/reinjection evidence and no common-parent mutation.
3. Arena `action_envelope_transform` hook that runs after raw parsing and before action realization.
4. C3 `AuthorityLocalizedEnvelopeTransform` that preserves raw provider behavior and transforms only one matching `write_state.status` authority commit.
5. Exact pre-J0 recovery checkpoint loading and hash verification.
6. C3 revision-lineage plumbing.
7. Deterministic engineering smoke execution of all three mechanisms through the real Arena loop.
8. Guarded real three-arm runner with exact code/config/model/domain/task/agent/source binding and symmetric budgets.

## C3 non-reproduction rule

Provider hidden state is not replayed. Re-executing the visible `before_turn:8` checkpoint may therefore fail to regenerate the original J0-shaped `fact` write.

The implementation now treats this as data rather than an execution bug:

- zero matching target writes → preserve the run as `C3_J0_REPRODUCTION_NOT_OBSERVED`;
- no retry-until-success;
- no rejection sampling;
- no synthetic replacement action;
- more than one match → fail closed as structurally ambiguous.

This prevents the recovery arm from quietly forcing the experimental condition through repeated sampling.

## Freeze-before-derive chain complete

The repository now implements:

`Exact plan → Subject traces → Raw evidence freeze → Raw artifact upload → Structural derivation → Derived artifact upload`

`arena.freeze_r7_evidence` distinguishes:

- `ENGINEERING_VALIDATION_EVIDENCE` for deterministic smoke traces;
- `SUBJECT_PROCESS_EVIDENCE` for real-model traces.

Scientific subject evidence requires a bound manual authorization record. Engineering evidence cannot be promoted into subject evidence.

`arena.derive_r7_process_measurements` refuses unfrozen evidence and reuses the existing Process Reality v0.4 ontology to produce:

- per-arm structural measurements;
- R7-A: C1 one-shot vs C2 persistent field;
- R7-B: C2 persistent field vs C3 ALR recovery;
- triad comparability/censoring records;
- integrity failures separately from semantic review.

Semantic CPR remains `NOT_ADJUDICATED`.

## CI status

The R7 offline validation workflow currently verifies, without provider credentials:

- protocol/schema invariants;
- exact frozen artifact hashes;
- exact common parent and recovery checkpoint;
- three-arm condition isolation;
- real Arena integration smoke;
- engineering raw-evidence freeze;
- frozen-evidence-only nested structural derivation;
- guarded real-run preflight;
- absence of the obsolete Free-vs-Structured paid R7 route.

The latest checked PR-head validation is green. This establishes engineering readiness only, not a steering/control result.

## Formal workflow

`.github/workflows/r7-three-arm-subject-real.yml` is the formal subject pipeline.

It has two stages:

1. **prepare** — exact source verification, plan construction, zero-call real-run preflight, dispatch record freeze;
2. **subject** — runs only when the manual dispatch contains the exact authorization phrase `CALL_REAL_R7_THREE_ARM_API`.

The subject stage uploads the frozen raw artifact before structural derivation and contains no automatic paid evaluator.

Default gate contract:

- 2 matched triads / 6 branches;
- DeepSeek source-model binding inherited from the frozen design;
- per-branch ceiling: USD 0.25;
- total ceiling: USD 1.50;
- per-branch call cap: 64;
- authorization status: `NOT_AUTHORIZED`.

These are ceilings/gate defaults, not authorization to spend.

## Remaining boundary

Engineering preparation is no longer the blocker. The remaining first-paper R7 steps are empirical:

1. explicit paid subject authorization/manual dispatch;
2. collect formal real-model C1/C2/C3 traces;
3. freeze and archive raw evidence;
4. derive structural R7-A/R7-B measurements from the frozen evidence;
5. only then interpret localization, steering, recurrence, recovery and any failure-to-reproduce cases.

No claim of reliable system control, ALR superiority, semantic CPR, or cross-model/domain generality is established at the current stage.
