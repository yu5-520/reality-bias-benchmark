# Process Reality v4.1 — Rollout Status

Date: 2026-09-17  
Status: OFFLINE FORWARD STACK IMPLEMENTED / ONE-SHOT PREPARED / PROSPECTIVE NATURAL PATH PREPARED / NO NEW PAID API

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
- digest: `sha256:e8655163ada6924c473e45b1e01558fa6a3cb3fd1436f124729fba6782db3454`;
- safe outer archive strategy: tar.gz bundle + SHA-256 file.

## 4. Prospective natural evidence path

A new subject path is prepared separately from the historical R5/R6 baseline runner.

Forward collection contract:

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

Raw subject evidence is required to freeze before derived R2/R3/R4/R6 structural measurements. The future authorized workflow uploads the raw frozen archive before derived analysis.

## 5. Prospective paid boundary

The new real-run gate is:

`CALL_REAL_R2R6_PROSPECTIVE_NATURAL_API`

No authorization manifest exists at this status point, so the prospective real-provider workflow cannot start. A valid future authorization must separately provide a positive global spending ceiling, symmetric per-run spending ceiling and symmetric per-run call ceiling. It authorizes natural subject collection only and does not authorize one-shot branching or a paid evaluator.

## 6. Scientific boundary

The old Phase-A parent and its one-shot prepared compatibility bundle are **not** independent prospective confirmation. The theory/contracts were refined after inspecting earlier exploratory evidence.

The new prospective-natural batch is the first path intended to generate post-freeze natural trajectories suitable for prospective validation. Only after those raw trajectories are collected and frozen may their natural Jumps be selected for a later formal one-shot perturbation batch.

## 7. Current stop point

P0 theory/contracts: complete.  
P1 transient runtime: initial implementation complete.  
P2 recurrence/inertia/path-topology measurement: initial deterministic implementation complete.  
P3 execution symmetry/evidence durability: initial implementation complete.  
P4 existing-source one-shot compatibility prepare: complete and artifact frozen.  
P5 prospective natural collection path: implementation complete; offline prepare triggered by repository update; real provider collection not authorized.  
P6 prospective Jump-derived formal one-shot batch: not started.

No new paid subject or paid Reviewer call was authorized by this repository update.
