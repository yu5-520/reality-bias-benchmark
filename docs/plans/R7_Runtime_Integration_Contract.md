# R7 Runtime Integration Contract

Status: implemented runtime contract for the exact-source first formal R7 design.

## Principle

R7 reuses the existing Arena continuation engine. It does not create a second agent runtime. The three conditions differ only in how the same predeclared `fact → unconfirmed` correction is applied around the frozen natural J0.

The raw provider response is evidence. Any experimental structural transform must be separately recorded and must never overwrite the raw provider envelope in the trace.

## Common comparison identity

All three arms are bound to:

- source R5 plan hash `a24c98901422bbccfc9a040a6bc14575b1c710edd518c0d9c2facf7a57926351`;
- natural J0 `E32`;
- target `inventory_stockout_assessment_v1.status`;
- semantic correction `fact → unconfirmed`;
- common post-J0 reference parent `after_turn:8`, hash `aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c`;
- common horizon `R7-H1-POST-JUMP-TURN-CAP-8`;
- the same task, agent registry, model/provider binding, and Process Reality v0.4 measurement ontology.

C1 and C2 start from the common post-J0 parent. C3 is a recovery operation and therefore rolls back one source turn to the exact pre-J0 checkpoint `before_turn:8`, hash `99731abb4ffd1caa2e568a6c2d90987700b3d0b7a66a1c777f811b666912a349`. The comparison invariant is the same frozen reference parent/J0; it is **not** a claim that C3 begins from the same runtime snapshot as C1/C2.

## C1 — one-shot adapter

Behavior:

1. restore the common post-J0 reference parent;
2. expose the matched correction in the copied runtime view of the first eligible resumed turn;
3. record the exposure;
4. consume the experiment-origin overlay immediately;
5. prohibit later experiment-origin reinjection;
6. leave persistent Arena state/reference parent unchanged;
7. continue through normal Arena execution.

Required evidence:

- direct exposure count = 1;
- reinjection count = 0;
- copied-view before/after hashes;
- actor and turn of exposure;
- persistent-state mutation = false.

## C2 — persistent-field adapter

Behavior:

1. restore the same common post-J0 reference parent;
2. re-expose the same semantic field in each eligible copied runtime view within the common horizon;
3. record every direct experiment-origin exposure;
4. never rewrite the common parent merely to maintain visibility;
5. stop naturally if the Arena terminates before the horizon.

Required evidence:

- ordered exposure records;
- direct exposure count;
- reinjection count;
- identical semantic target/status across exposures;
- persistent-state mutation = false;
- early termination retained as censoring.

## C3 — ALR recovery adapter

The first formal C3 is a **turn-localized authority recovery** because the frozen source provides an exact checkpoint immediately before the J0-producing turn.

Behavior:

1. preserve the entire source prefix through event E31;
2. restore exact checkpoint `before_turn:8` with queue head `inventory`;
3. re-execute turn 8 through the ordinary provider/runtime path;
4. keep raw provider content and raw parsed envelope immutable as evidence;
5. inspect the re-executed envelope for exactly one target `write_state` whose key is `inventory_stockout_assessment_v1` and whose status is `fact`;
6. if exactly one match exists, change only that action's realized `status` to `unconfirmed` before `ArenaState.apply_actions`;
7. record raw/applied envelope hashes, raw/applied action hashes, action index, delta path, authority class `I`, and revision lineage;
8. continue through the ordinary Arena path and observe new descendants.

### C3 non-reproduction rule

Provider hidden state is not replayed. Therefore the same visible checkpoint may not regenerate the original J0-shaped action.

If zero matching target writes appear:

- do not throw away the sample;
- do not retry until a match occurs;
- do not fabricate the action;
- leave the parsed envelope unmodified;
- record a non-application attempt with reason `TARGET_AUTHORITY_COMMIT_NOT_REPRODUCED`;
- classify the condition as `C3_J0_REPRODUCTION_NOT_OBSERVED` and preserve it as a censored/non-realized intervention observation.

If more than one matching target write appears, fail closed as structurally ambiguous.

## Arena engine boundary

`run_arena_once` exposes two optional experimental hooks:

- `runtime_view_transform` — operates only on a copied prompt-time runtime view; used by C1/C2;
- `action_envelope_transform` — operates after raw parsing and before action realization; used by C3.

When the action hook is active, the trace preserves both:

- `parsed_envelope` = raw parsed model behavior;
- `applied_envelope` = action envelope actually realized after the structural intervention.

Transform records are separately emitted in `action_transform_records`.

Historical runs are unchanged when these hooks are absent.

## Cross-arm horizon

The shared post-J0 observation horizon is 8 agent turns. Natural early termination is never padded or extended. Shorter trajectories are preserved as censored observations and comparisons use only observed matched distances.

## Real subject runner

`arena.run_r7_three_arm_real` must:

- verify exact source plan/config/model/domain/task/agent hashes before provider access;
- use symmetric per-branch call and spend ceilings;
- enforce a total spend ceiling covering all planned branches;
- keep C1/C2/C3 condition bindings fixed before the first provider call;
- record execution bindings and journals;
- preserve C3 non-reproduction instead of rejection sampling;
- never call a paid evaluator;
- require the exact external authorization phrase `CALL_REAL_R7_THREE_ARM_API` in addition to the execution flag.

The prepared plan itself always remains `NOT_AUTHORIZED`.

## Evidence freeze contract

A formal subject chain is:

`Prepare exact plan → Subject execution → Freeze raw evidence → Upload raw artifact → Structural derivation → Upload derived artifact`

`arena.freeze_r7_evidence` binds:

- plan/protocol identity;
- common reference parent and C3 checkpoint;
- semantic payload and horizon;
- trace hashes;
- arm/condition statuses;
- runtime/action transform counts;
- revision hashes;
- journals;
- plan-file hashes;
- manual authorization record.

Scientific subject evidence cannot be frozen without an authorization record. Engineering smoke traces are explicitly frozen under a separate `ENGINEERING_VALIDATION_EVIDENCE` role and cannot be promoted into subject evidence.

## Derivation contract

`arena.derive_r7_process_measurements` accepts only a verified frozen evidence batch. It reuses Process Reality v0.4 and produces:

- per-arm structural measurements;
- **R7-A:** C1 one-shot vs C2 persistent field;
- **R7-B:** C2 persistent field vs C3 ALR recovery;
- triad comparability/censoring index;
- integrity-failure records.

C3 non-reproduction prevents an R7-B comparison for that triad rather than being imputed as zero or retried away.

Semantic CPR remains `NOT_ADJUDICATED` throughout this structural derivation.

## Claim boundary

Passing the runtime contract establishes experimental plumbing and evidence integrity. It does not establish that system inertia is steerable, recoverable, or controllable. Those are empirical claims that require prospective real-model subject evidence and subsequent analysis of the frozen traces.
