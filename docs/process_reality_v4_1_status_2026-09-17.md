# Process Reality v4.1 — Rollout Status

Date: 2026-09-17  
Status: OFFLINE FORWARD STACK IMPLEMENTED / ONE-SHOT PREPARED / NO PAID API

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

## 3. Offline validation

Code commit used for the first offline one-shot prepare:

`0f15fcfd0f392af16f989d5e59795e8f0b003462`

Two validation workflows completed successfully:

- R5-MID One-Shot Phase-B Prepare — run `35122637983`;
- R2 Free-Agent Arena Offline Validation — run `35122637992`.

The latter also passed legacy/control/v4 regression paths, so adding the runtime-view transform hook did not replace or silently break historical execution paths.

## 4. Prepared compatibility plan

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

## 5. Prepared artifact

Workflow run `35122637983` uploaded:

- artifact: `r5mid-one-shot-prepared-35122637983`;
- artifact ID: `10457562997`;
- digest: `sha256:e8655163ada6924c473e45b1e01558fa6a3cb3fd1436f124729fba6782db3454`;
- safe outer archive strategy: tar.gz bundle + SHA-256 file.

## 6. Scientific boundary

This prepared bundle is **not** independent prospective confirmation. The theory/contracts were refined after inspecting earlier exploratory evidence, so the existing Phase-A parent is used only to verify that the new one-shot mechanism machinery can bind to real frozen source evidence.

For first-paper prospective validation, new natural trajectories must be collected after the new definitions/contracts are frozen. A later one-shot perturbation batch can then be derived from those prospectively collected natural Jumps.

## 7. Paid boundary

No paid subject or paid Reviewer API was called by this rollout.

The historical Phase-B authorization is consumed and cannot authorize the new protocol. A future real one-shot run requires a new explicit authorization using the new one-shot gate plus a new positive spending ceiling.

## 8. Current stop point

P0 theory/contracts: complete.  
P1 transient runtime: initial implementation complete.  
P2 recurrence/inertia/path-topology measurement: initial deterministic implementation complete.  
P3 execution symmetry/evidence durability: initial implementation complete.  
P4 offline one-shot prepare: complete and artifact frozen.  
P5 new prospective natural evidence / real one-shot evidence: **not started**.

This is the intentional stop point before any new paid subject execution.
