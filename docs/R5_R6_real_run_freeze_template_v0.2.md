# R5 / R6 Real-Model Run Freeze Template v0.2

Date: 2026-09-16  
Status: TEMPLATE / NOT AUTHORIZED / NOT A FORMAL SUBJECT FREEZE  
Supersedes for forward work: `docs/R5_R6_real_run_freeze_template_v0.1.md`

No provider call is authorized by this document.

## 1. Phase architecture

### Phase A — Baseline Snapshot Collection

Purpose:

- run the normal subject condition;
- freeze deterministic Arena snapshots before/after each completed turn;
- derive structural candidates under the frozen measurement contract;
- select a **branchable** structural anchor using a frozen structural-only rule;
- perform no branch continuation and no paid semantic evaluation.

Current forward implementation:

- `arena/build_branch_baseline_manifest.py`
- `arena/run_branch_baseline_real.py`
- `arena/config/r5r6_anchor_rule_v0.2.json`
- `.github/workflows/r5r6-baseline-snapshot-real.yml`

### Offline Boundary — Anchor / Variable Freeze

After Phase A evidence is frozen:

- preserve every baseline including no-anchor outcomes;
- never rerun merely to manufacture an eligible anchor;
- freeze selected parent snapshot/hash;
- freeze anchor class and selector version;
- freeze experimental `variable_id` and registry hash;
- freeze exact intervention spec and held-constant fields;
- freeze control/intervention branch plan before outcomes exist;
- semantic Reviewer labels do not select the confirmatory anchor.

### Phase B — Branch Continuation

Purpose:

- start control/intervention branches from the same frozen parent identity;
- apply exactly one preregistered manipulation;
- run repeated continuations under separately authorized provider calls;
- freeze raw evidence before derived measurements;
- derive continuation-only Measurement-v3 and, where source-compatible, System Behavior Measurement-v4 records;
- defer semantic C/P/R/penetration/recovery adjudication.

Phase B has an implemented guarded execution path but remains separately unauthorized until all fields are frozen and the exact paid authorization is supplied.

## 2. Forward MID structural anchor rule

Repository rule:

`arena/config/r5r6_anchor_rule_v0.2.json`

It selects the lowest-event-index replayable:

`HIGH_CERTAINTY_STATE_WRITE_CANDIDATE`

subject to:

- `action_type = write_state`;
- realized event required;
- exact `after_turn:<candidate turn>` snapshot required;
- nonterminal snapshot required;
- **pending continuation queue required**;
- semantic Reviewer labels forbidden during selection;
- branch outcomes unavailable during selection.

Therefore:

`nonterminal snapshot ≠ automatically branchable snapshot`

This rule is a concrete `TRANSITION_ANCHOR` selector for the current MID status-downgrade experiment. It does not establish semantic C, Jump truth, Authority Penetration or causal importance.

## 3. Phase-A unresolved fields

Must freeze before provider calls:

- `provider`: **UNRESOLVED**
- `model/config`: **UNRESOLVED**
- `baseline run count`: **UNRESOLVED**
- `maximum subject-call budget`: **UNRESOLVED**
- `explicit spending ceiling`: **UNRESOLVED**
- `currency`: **UNRESOLVED**
- `run-start commit SHA`: **UNRESOLVED**
- `final baseline manifest hash`: **UNRESOLVED**
- `final anchor-rule hash`: exact v0.2 file at run start
- `measurement contract hash`: exact current file(s) at run start

Workflow defaults remain prepare-only / zero-budget until explicitly changed.

## 4. Phase-A paid authorization gate

Real baseline calls require all of:

- exact provider/model config binding;
- positive baseline run count;
- explicit positive call cap;
- explicit positive spending ceiling;
- matching currency;
- exact authorization phrase:

`CALL_REAL_R5R6_BASELINE_API`

Generic “执行/继续/推进” instructions do not satisfy this gate.

## 5. Phase-A evidence package

Preserve where available:

- manifest rows and hashes;
- full subject traces;
- append-only journals;
- before/after-turn snapshots;
- state hashes;
- usage/cost-guard records;
- termination/failure/censoring status;
- structural candidate index;
- anchor-selection package or explicit no-anchor outcome;
- standard evidence-batch outputs;
- authorization record.

No baseline is silently regenerated due to lack of an eligible anchor.

## 6. Phase-B freeze fields

After Phase-A evidence exists, freeze:

- selected parent trace / source evidence identity;
- selected parent state hash;
- selected candidate/event ref;
- anchor class;
- `variable_id` from `configs/experimental_variable_registry_v0.1.json`;
- variable-registry hash;
- target `boundary_id` / boundary-registry hash;
- exact manipulation and held constants;
- replicate count;
- primary branch metrics;
- provider/model binding;
- subject-call cap;
- spending ceiling/currency;
- branch execution commit SHA;
- final branch manifest hashes.

For the current implemented MID experiment:

- `variable_id = EPISTEMIC_STATUS_DOWNGRADE`;
- manipulation = high-certainty status → `provisional`;
- only the named metadata status field may change before continuation, except derived state hash.

## 7. Phase-B paid authorization gate

Real branch continuations require exact phrase:

`CALL_REAL_R5R6_BRANCH_API`

plus exact frozen provider/model/code/plan/hash bindings, positive call cap, positive spending ceiling, matching currency and guarded execution.

Phase-A authorization never authorizes Phase B.

## 8. Evidence freeze order

Phase B order:

1. execute subject continuations;
2. preserve traces/journals/errors/usage;
3. freeze standard evidence batch;
4. derive deterministic continuation-only measurements;
5. derive System Behavior v4 records where all source fields exist;
6. append semantic reviews later.

Derived measurements may never rewrite frozen subject evidence.

## 9. Measurement boundary

Current implemented branch execution remains compatible with Measurement v3.

Forward v4 adds behavior-first records:

- `schemas/behavior_event_v0.1.schema.json`
- `schemas/system_trajectory_measurement_v4.schema.json`
- `configs/measurement_boundary_registry_v0.1.json`
- `configs/experimental_variable_registry_v0.1.json`

Structural branch difference is not automatically C/P/R, Authority Penetration, recovery success, Tension or general causal effect.

## 10. Objective outcomes

Allowed Phase-A outcomes:

- `ANCHOR_SELECTED`
- `NO_ELIGIBLE_STRUCTURAL_ANCHOR`
- `SKIPPED_NONCOMPLETE_BASELINE`
- provider failure
- censoring/budget stop

Allowed Phase-B pair outcomes include complete, incomplete, failed and censored members. Only protocol-eligible pairs may enter a stated comparison.

## 11. Failure / censoring

- provider/transport failure is preserved;
- budget stop is preserved;
- incomplete/censored run is preserved;
- missing snapshot/state is never fabricated;
- provider hidden state is never claimed replayed;
- branch cannot start from an invalid or empty-work continuation state under the current Arena scheduler;
- failures are never counted as negative Jump branches.

## 12. Current execution boundary

Offline preparation, validation, registry work and protocol updates may proceed without API calls.

No Phase-A or Phase-B paid call is authorized by this template.