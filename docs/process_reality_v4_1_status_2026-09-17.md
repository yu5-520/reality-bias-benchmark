# Process Reality v4.1 — Rollout Status

Date: 2026-09-17  
Status: OFFLINE FORWARD STACK IMPLEMENTED / ONE-SHOT PREPARED / PROSPECTIVE NATURAL OFFLINE PREPARED / NO NEW PAID API

## 1. Research-coordinate update

The forward first-paper coordinate is now process-reality mechanism research rather than terminal-outcome or engineering-containment evaluation.

Implemented forward contracts:

- `docs/R_Plan_v4.1.md`
- `theory/theory_contract_v0.5.md`
- `docs/system_behavior_measurement_plan_v4.1.md`
- `docs/R5_R6_branch_intervention_recovery_protocol_v0.5.md`
- `docs/experimental_control_layer_v0.3.md`
- `configs/experimental_variable_registry_v0.2.json`
- `configs/first_paper_mechanism_contract_v0.3.json`
- `configs/first_paper_analysis_contract_v0.2.json`
- `arena/config/r5r6_anchor_rule_v0.3.json`
- `configs/prospective_natural_collection_contract_v0.1.json`

Historical contracts/evidence remain immutable.

## 2. One-shot runtime implementation

Implemented:

- `arena/one_shot_intervention.py`
- `arena/branch_plan_one_shot.py`
- `arena/run_branch_one_shot_real.py`
- generic copied-runtime-view transform hook in `arena/engine.py`
- `arena/process_reality_dynamics_v0_1.py`
- `arena/derive_one_shot_process_measurements.py`
- schemas and offline tests for one-shot delivery and process-dynamics comparison.

Forward invariant:

```text
same frozen parent/start state
+ one experiment-origin metadata overlay
+ exactly one direct exposure
+ no persistent Arena-state mutation
+ no experiment-origin reinjection
-> free downstream evolution
```

## 3. Existing-source one-shot compatibility prepare

Code commit used for the first offline one-shot prepare:

`0f15fcfd0f392af16f989d5e59795e8f0b003462`

Validation workflows completed successfully:

- R5-MID One-Shot Phase-B Prepare — run `35122637983`;
- R2 Free-Agent Arena Offline Validation — run `35122637992`.

The latter also passed legacy/control/v4 regression paths, so adding the runtime-view transform hook did not replace or silently break historical execution paths.

The offline prepare reused immutable Phase-A source evidence only as a mechanism-development compatibility parent:

- source Phase-A run: `35106356084`;
- baseline: `r5r6-ecommerce-baseline-0002`;
- selected candidate: `r5r6-ecommerce-baseline-0002:R2V2:36030171fcfa588e`;
- frozen parent state hash: `9bd705d76b15726b64b941d16604a83933cd1b635bb1af9845e82aa9581a05ce`.

Prepared one-shot identities:

- plan hash: `3c292c9b6db089891d23f277076c8e5d78748a08c40f59bbe9eb4eb02b36d6bb`;
- envelope hash: `c916e189a15def55fe64544a0503484e7ca75a58a85b2c76235c02456bf5af82`;
- target state key: `inventory_transfer_feasibility`;
- target source event index: `41`;
- overlay: `fact -> unconfirmed`;
- delivery policy: `FIRST_POST_JUMP_AGENT_TURN`;
- 2 replicate pairs / 4 prepared branches;
- all rows have identical parent and branch-start state hashes;
- authorization status: `NOT_AUTHORIZED`;
- prospective confirmation status: `NOT_ESTABLISHED_EXISTING_PHASE_A_SOURCE`.

Prepared artifact:

- artifact: `r5mid-one-shot-prepared-35122637983`;
- artifact ID: `10457562997`;
- digest: `sha256:e8655163ada6924c473e45b1e01558fa6a3cb3fd1436f124729fba6782db3454`.

## 4. Prospective natural evidence path

The prospective path is separate from the historical R5/R6 baseline runner and is frozen after Theory v0.5 / R Plan v4.1.

Collection contract:

- batch: `R2R6-PROSPECTIVE-NATURAL-BATCH-001`;
- domain: ecommerce;
- planned repeats: 4;
- same input / same goal;
- free-Agent structure;
- CPR/Jump/authority research labels hidden from subject prompts;
- structural-only outcome-blind anchor selection after raw trace collection;
- no-anchor preserved;
- censored traces preserved;
- no outcome-aware rerun;
- no rerun to manufacture an anchor;
- automatic paid evaluator disabled.

New implementation:

- `arena/build_prospective_natural_manifest.py`;
- `arena/run_prospective_natural_real.py`;
- `arena/freeze_prospective_evidence.py`;
- `arena/derive_prospective_natural_measurements.py`;
- `.github/workflows/r2r6-prospective-natural-prepare.yml`;
- `.github/workflows/r2r6-prospective-natural-authorized-once.yml`.

The v0.3 structural selector is now supported by `arena/anchor_selection.py` while v0.1/v0.2 remain backward compatible.

## 5. Prospective offline prepare result

Prepare workflow:

- run: `35123705888`;
- head SHA: `fd7a99422180d7beb45fd01662af88ccea7ff04d`;
- conclusion: success;
- offline tests: success;
- provider execution: none.

Frozen subject rows:

- `prospective-ecommerce-natural-0001`;
- `prospective-ecommerce-natural-0002`;
- `prospective-ecommerce-natural-0003`;
- `prospective-ecommerce-natural-0004`.

Frozen bindings:

- collection contract SHA-256: `a9dee880eb0d0302dcbd778e8c534e0146a4e2eef7b316bceb79502c8be90fd9`;
- Theory v0.5 SHA-256: `e0b12ab52ea9d59223f1100a5fb787f6fb200b7c33a5f09cdc0e0425127e17aa`;
- Measurement v4.1 SHA-256: `c7f1ce683ac70507a5d50c8eacc575f2fd3843562d7293781d13983231945f57`;
- task hash: `849de0b4ab9874e0adf328b6f4f3768790215ad565a891e4c0a1dc1a9069f61b`;
- Agent-pool hash: `d2e2ab7c6996098850bff7a6b24bd65b61567fe3bebb6c484c7024c67c020f26`;
- arena config SHA-256: `8e33288516fc47f116d20f4579ca84410a3cdefecef7c99c5bf2bb31e5d14002`;
- model config SHA-256: `fe7bbafda1c4c12b1d1f5dca963d1a45cbe503713aaa486fac09f569d1b5f8c5`;
- anchor-rule SHA-256: `ac54ed7b31584f11ec96b9ad0ec5683f5562efc569ab0f693e33cae9eec58788`.

Prepared artifact:

- name: `r2r6-prospective-natural-prepared-35123705888`;
- artifact ID: `10457404885`;
- GitHub artifact digest: `sha256:9e0067d57d532f5c4e58b1caed70cfa35b198534885a0333200f90e4431d70c3`;
- inner prepared tar SHA-256: `25d887967a3353fc62d948985a1ecd54dfcaabfdb1837b8ad08d3561e2277091`;
- expires: `2026-12-15T16:43:30Z`.

Repository provenance record:

`manifests/r2r6_prospective_natural_prepare_record_2026-09-17.json`

## 6. Evidence ordering for the future real prospective batch

```text
real subject run
-> preserve raw traces / snapshots / journals / failures
-> freeze raw evidence batch + hashes
-> upload raw frozen artifact
-> only then derive R2/R3/R4/R6 structural measurements
-> semantic review remains append-only and deferred
```

No-anchor, censored and null trajectories remain part of the planned evidence set.

## 7. Prospective paid boundary

The new real-run gate is:

`CALL_REAL_R2R6_PROSPECTIVE_NATURAL_API`

No paid authorization manifest exists. A valid future authorization must separately provide:

- positive total USD ceiling;
- positive symmetric per-run USD ceiling;
- positive symmetric per-run call ceiling.

It authorizes prospective natural subject collection only. It does not authorize one-shot branching and does not authorize a paid evaluator.

## 8. Scientific boundary

The old Phase-A parent and its one-shot compatibility bundle are not independent prospective confirmation. The theory/contracts were refined after inspecting earlier exploratory evidence.

`R2R6-PROSPECTIVE-NATURAL-BATCH-001` is the first post-freeze natural-trajectory path intended for prospective validation. Only after those raw trajectories are collected and frozen may their natural Jumps become candidates for a later formal one-shot perturbation batch.

## 9. Current stop point

P0 theory/contracts: complete.  
P1 transient runtime: initial implementation complete.  
P2 recurrence/inertia/path-topology measurement: initial deterministic implementation complete.  
P3 execution symmetry/evidence durability: initial implementation complete.  
P4 existing-source one-shot compatibility prepare: complete and artifact frozen.  
P5 prospective natural collection path: implementation complete and offline subject plan frozen. Real provider collection remains unauthorized.  
P6 prospective Jump-derived formal one-shot batch: not started.

No new paid subject or paid Reviewer call was authorized by this repository update.
