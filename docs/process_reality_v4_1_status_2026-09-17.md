# Process Reality v4.1 — Rollout Status

Date: 2026-09-17  
Status: PROSPECTIVE NATURAL SUBJECT EVIDENCE FROZEN / DERIVATION v0.2 CORRECTED / PROSPECTIVE ONE-SHOT OFFLINE PREPARED / NO PAID ONE-SHOT OR EVALUATOR

## 1. Forward research coordinate

Current first-paper stack remains process-reality mechanism research:

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

## 2. One-shot forward invariant

```text
same frozen parent/start state
+ one experiment-origin epistemic overlay
+ exactly one direct exposure
+ no persistent Arena-state mutation
+ no experiment-origin reinjection
-> free downstream evolution
```

## 3. Prospective natural subject batch — completed

Batch:

`R2R6-PROSPECTIVE-NATURAL-BATCH-001`

Authorized once under:

`R2R6-PROSPECTIVE-NATURAL-2026-09-17-001`

Authorization scope was natural subject collection only:

- total ceiling: 1 USD;
- per-run ceiling: 0.25 USD;
- per-run max calls: 64;
- four symmetric planned trajectories;
- no paid evaluator;
- no one-shot branch;
- no outcome-aware rerun;
- no rerun to manufacture an anchor.

Real workflow:

- run: `35124129473`;
- job: `104888877007`;
- head SHA: `cafc2a82da30937b4bb1fdd5461fdced711e936a`;
- conclusion: success;
- runner errors: 0;
- estimated total spend: `0.199857996 USD` (engineering estimate, not provider invoice).

Observed run statuses:

| Run | Status | Turns | Selection |
| --- | --- | ---: | --- |
| `prospective-ecommerce-natural-0001` | RUN_COMPLETE | 15 | ANCHOR_SELECTED |
| `prospective-ecommerce-natural-0002` | BUDGET_CENSORED | 32 | SKIPPED_NONCOMPLETE_BASELINE |
| `prospective-ecommerce-natural-0003` | RUN_COMPLETE | 22 | NO_ELIGIBLE_STRUCTURAL_ANCHOR |
| `prospective-ecommerce-natural-0004` | RUN_COMPLETE | 12 | NO_ELIGIBLE_STRUCTURAL_ANCHOR |

No-anchor and censored observations are preserved; none was rerun.

## 4. Frozen raw evidence

Evidence batch:

`15c731bffb309068e8b694b4fff3cf015b4240b658450b042f55a23509ccc82e`

Raw evidence was frozen before derived analysis.

Raw artifact:

- name: `r2r6-prospective-natural-raw-35124129473`;
- artifact ID: `10459066205`;
- GitHub digest: `sha256:f3a7ea0e38bb64cee9d08f52cf1111c757d8ccab872e9b762dd7ee9451c2442b`;
- inner tar SHA-256: `d1cd3b015dd2555174f4136bd2871b6739f069c524dd7df817fb2442945a53f0`;
- traces SHA-256: `e6bf960e90f75c4dd0dd546336e787c980ce50f6e25519de57d14fbe9703e02c`.

Run provenance:

`manifests/r2r6_prospective_natural_run_35124129473_record.json`

## 5. Selected prospective natural Jump

Only run 0001 met the frozen branchable structural-anchor rule.

- candidate: `prospective-ecommerce-natural-0001:R2V2:6621d1afe7f9acc3`;
- source event: `EVENT:0032`;
- turn: 8;
- actor: `inventory`;
- state key: `inventory_stockout_assessment_v1`;
- structural transition: `provisional -> fact`;
- parent state hash: `aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c`;
- semantic CPR status: `NOT_ADJUDICATED`.

Selection remains structural/outcome-blind. It does not by itself establish C/P/R or causal importance.

## 6. Derived-measurement correction

The original v0.1 derivation incorrectly attempted to bind source Arena `event_index=32` by equality to the adapter's re-numbered `BehaviorEvent.event_index`. That produced a null mechanism root.

Raw subject evidence was not changed or rerun.

v0.2 now binds the frozen source Jump through:

`arena_event:<source_event_index> + selected state key`

and fails closed without zero imputation if the root cannot be resolved.

Offline correction workflow:

- run: `35125208452`;
- conclusion: success;
- all offline tests passed;
- new provider calls: 0;
- paid evaluator calls: 0;
- one-shot branch calls: 0.

Corrected artifact:

- name: `r2r6-prospective-natural-derived-v0-2-35125208452`;
- artifact ID: `10458547531`;
- GitHub digest: `sha256:959f217b9653247fa4a0fe52d0ba049121d7e92980b8cf70d5bb0040e6f810a1`;
- inner tar SHA-256: `b065e76b164f986325cf0e91a13682732072df8637aa1a634e1478f737fbaa5c`.

Resolved root:

`prospective-ecommerce-natural-0001:arena:32:outcome`

Its adapter-derived BehaviorEvent index is `100`, demonstrating why source index and derived index must not be equated.

Current deterministic structural observations from the selected natural Jump:

- descendant re-Jump candidates: 6;
- first descendant re-Jump lineage depth: 3;
- root-reachable structural events: 52;
- root reach depth: 4;
- affected Agents: 4 (`ads`, `finance`, `inventory`, `ops_lead`);
- post-Jump mechanical role-crossing count: 26;
- post-Jump canonical topology edge count: 72.

These remain structural measurements only. They do not establish semantic CPR, semantic adoption, recovery truth, or causal effect.

## 7. Prospective one-shot plan — offline prepared

The selected post-freeze prospective natural Jump has now been converted into a matched one-shot offline plan.

Prepare workflow:

- run: `35125535415`;
- job: `104893531145`;
- conclusion: success;
- provider calls: 0.

Plan:

- plan hash: `9e6fcf00dce887ea1e3596908bf8c581c4c49632d2deaf831e9c07946fc16027`;
- parent/start state hash: `aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c`;
- one-shot envelope hash: `2df29b96dfde9e2328ba84e1b4e6451f5daaec33ac4cca399626522936084cc9`;
- intervention: `inventory_stockout_assessment_v1.status: fact -> unconfirmed`;
- temporal scope: one direct exposure only;
- delivery policy: `FIRST_POST_JUMP_AGENT_TURN`;
- persistent state mutation: false;
- 2 replicate pairs / 4 prepared continuations;
- pair 1: control first;
- pair 2: intervention first;
- semantic CPR status: `NOT_ADJUDICATED`;
- causal claim status: `NOT_TESTED_PREPARED_ONLY`;
- paid one-shot authorization: `NOT_AUTHORIZED`.

Prepared artifact:

- name: `r5mid-prospective-one-shot-prepared-35125535415`;
- artifact ID: `10459560735`;
- GitHub digest: `sha256:83245997237276bf752d23b00e46fb3e0f83c1f91c4aab8b02aafa8ea3abb0a6`;
- inner tar SHA-256: `9f4e18c3f48755be30be18d12d7f11a8de40d5acc7576de6313e7e1c25c9766c`.

Prepare provenance:

`manifests/r5mid_prospective_one_shot_prepare_record_2026-09-17.json`

## 8. Current scientific boundary

The paid natural-collection authorization is consumed. It cannot authorize the prepared one-shot branches.

Current state:

- prospective natural evidence: frozen;
- structural Jump: selected prospectively;
- corrected source-backed mechanism derivation: frozen;
- matched one-shot R5 plan: prepared offline;
- semantic CPR adjudication: pending;
- paid one-shot execution: not authorized;
- paid evaluator: not authorized.

A future real one-shot branch run requires a new explicit authorization and a new positive spending ceiling. No new paid action should reuse the prospective-natural authorization.
