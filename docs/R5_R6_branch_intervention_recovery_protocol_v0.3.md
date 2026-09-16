# R5 / R6 Branch Intervention & Recovery Protocol v0.3

Date: 2026-09-16  
Status: PROTOCOL FREEZE CANDIDATE / PHASE-A AND PHASE-B EXECUTION PATHS PREPARED / ZERO NEW PROVIDER CALLS  
Scope: first-paper mechanism experiments only  
Supersedes for forward work: `docs/R5_R6_branch_intervention_recovery_protocol_v0.2.md`

Depends on:

- `docs/R_Plan_v3.2.md`
- `theory/theory_contract_v0.3.md`
- `docs/trajectory_dynamics_measurement_plan_v3.md`
- `docs/experimental_control_layer_v0.2.md`
- `docs/R5_R6_real_run_freeze_template_v0.1.md`

Historical v0.1/v0.2 protocol files and evidence interfaces remain preserved.

## 1. Core causal form

R5/R6 now use an explicit two-phase design:

```text
Phase A
baseline subject trajectory
  → before/after-turn snapshots
  → deterministic structural candidates
  → structural-only replayable anchor selection
  → freeze source evidence

OFFLINE FREEZE BOUNDARY
  → select exact parent snapshot
  → freeze one intervention ΔX
  → freeze control/intervention branch plan

Phase B
same frozen parent
  ├── unchanged control continuation
  └── one-variable intervention continuation
        → freeze new subject evidence
        → deterministic Measurement-v3 slicing
        → semantic review later
```

Phase-A authorization never authorizes Phase B.

## 2. Why the two-phase boundary is mandatory

The design prevents three forms of post-outcome contamination:

1. selecting an anchor after favorable branch outcomes are visible;
2. rerunning baselines until a convenient candidate appears;
3. silently expanding one paid authorization from baseline collection into intervention continuations.

Allowed Phase-A objective outcomes therefore include:

- `ANCHOR_SELECTED`;
- `NO_ELIGIBLE_STRUCTURAL_ANCHOR`;
- `SKIPPED_NONCOMPLETE_BASELINE`;
- provider failure;
- censoring/budget stop.

All are preserved. No-anchor is not automatically replaced.

## 3. Phase-A structural selector

Frozen candidate rule:

- `arena/config/r5r6_anchor_rule_v0.1.json`

Implementation:

- `arena/anchor_selection.py`
- `arena/build_branch_baseline_manifest.py`
- `arena/run_branch_baseline_real.py`
- `.github/workflows/r5r6-baseline-snapshot-real.yml`

The current rule selects the lowest-event-index replayable:

`HIGH_CERTAINTY_STATE_WRITE_CANDIDATE`

with an `after_turn:<candidate turn>` nonterminal snapshot.

This is structural-only selection. It does **not** establish semantic C, unauthorized promotion, Jump truth, Authority Penetration, or causal importance.

## 4. Phase-B intervention v0.1

The first confirmatory candidate intervention family is deliberately narrow:

`EPISTEMIC_STATUS_DOWNGRADE_TO_PROVISIONAL`

For the selected state key:

```text
high-certainty status
(fact / confirmed / verified / executed)
          ↓ ΔX
provisional
```

The Phase-B plan proves that the branch-visible snapshot changes exactly one runtime metadata field:

`shared_state_metadata[selected_key].status`

The following are held identical between parent and intervention-start snapshots:

- turn count;
- event history;
- queue/inboxes;
- shared-state value;
- all unrelated metadata;
- target metadata other than `status`;
- parent anchor/provenance fields.

The derived `state_hash` changes, as expected.

Implementation:

- `arena/branch_plan.py`
- `schemas/r5r6_branch_execution_plan_v0.1.schema.json`
- `schemas/r5r6_branch_execution_manifest_row_v0.1.schema.json`

## 5. Parent versus branch-start identity

Each branch binds:

- `parent_trace_hash`;
- `parent_state_hash`;
- `branch_start_state_hash`;
- parent/start turn and event-count boundaries;
- intervention hash;
- branch hash;
- replicate index;
- model/config/code identity.

For control:

`parent_state_hash == branch_start_state_hash`

For intervention:

`parent_state_hash != branch_start_state_hash`

Both members of a pair must retain the same parent trace and parent state.

## 6. Paired branch replicates

Each replicate contains exactly two continuations:

- `CONTROL_CONTINUATION`
- `STATUS_DOWNGRADE_INTERVENTION`

The pair shares:

- frozen parent;
- task/domain/Agent pool;
- Arena config;
- subject model config/provider;
- logical-seed identity;
- branch execution code SHA.

Execution order is counterbalanced:

- odd replicate: control first;
- even replicate: intervention first.

Logical seed is evidence metadata; provider-internal randomness is not claimed to be replayed.

## 7. Code identity separation

Phase-B plans distinguish:

- `source_baseline_commit` — code that produced the Phase-A source trace;
- `branch_execution_commit` — exact repository commit allowed to execute the Phase-B continuation.

The real Phase-B runner rejects a code SHA that does not match the frozen branch plan.

This avoids falsely treating later branch instrumentation code as identical to the historical baseline code.

## 8. Phase-B paid execution guard

Implementation:

- `arena/run_branch_real.py`
- `.github/workflows/r5r6-frozen-parent-branch-real.yml`

Exact authorization phrase:

`CALL_REAL_R5R6_BRANCH_API`

Real Phase-B calls additionally require:

- a Phase-A subject-evidence artifact;
- exact selected Phase-A baseline run ID;
- `ANCHOR_SELECTED` selection package;
- frozen branch plan/hash;
- exact provider matching the Phase-A model binding;
- exact model-config path/hash matching Phase A;
- exact branch execution commit SHA;
- positive subject-call cap;
- explicit positive spending ceiling;
- matching currency;
- `--execute-real-api`.

Generic repository execution instructions do not satisfy this paid gate.

Phase B cannot authorize or trigger a Phase-A rerun.

## 9. Evidence freeze order

Phase-B execution order is:

1. execute subject continuations;
2. preserve raw traces/journals/errors/usage;
3. freeze standard evidence batch;
4. derive continuation-only Measurement-v3 records;
5. derive structural control/intervention pair comparisons;
6. append semantic review later if required.

Paid semantic evaluation is never automatic.

## 10. Continuation-only Measurement v3

Implementation:

- `arena/trajectory_measurement_v3.py`
- `arena/derive_branch_measurements.py`

Measurement begins at the frozen:

- `branch_start_turn`;
- `branch_start_event_count`.

Therefore parent history is retained for provenance but is not recounted as a branch outcome.

Deterministic records may report:

- continuation turns/calls/events;
- realized event/action counts;
- participating actors;
- realized Authority-class events;
- realized operational events;
- structural candidate counts/types;
- final-state/final-answer hashes;
- usage.

They do **not** automatically label:

- C/P/R;
- semantic adoption;
- Authority Penetration;
- recovery;
- general causal effect.

Those remain `NOT_ADJUDICATED` until separately reviewed under a frozen semantic contract.

## 11. Pair eligibility for structural comparison

Current v0.1 deterministic comparison requires both pair members to be natural:

`RUN_COMPLETE`

Missing, failed or censored members remain preserved but do not silently enter a complete-pair comparison.

A later protocol may define additional prefix/censoring estimands, but v0.3 does not invent them post hoc.

## 12. R5 interpretation boundary

A future result may support a containment pattern such as:

```text
proposal/structural Jump opportunity ≈ unchanged
but
realized descendants / penetration / persistence ↓
```

only if the corresponding Jump and penetration criteria were frozen before analysis.

Generic event-count or final-state differences cannot be substituted post hoc for those semantic/dynamic outcomes.

## 13. R6 recovery boundary

Recovery remains a second step after R5 branch evidence exists.

Recovery records continue to separate:

- structural recurrence;
- residual descendants;
- reconstruction status;
- recovery cost;
- semantic R regeneration.

`regeneration_semantic_status` remains `NOT_ADJUDICATED` unless independently reviewed.

## 14. Stop conditions

Stop and audit before interpretation if:

- parent hash mismatch;
- branch-start hash mismatch;
- branch plan/code SHA mismatch;
- model/config/provider mismatch;
- intervention changes more than the named status field;
- branch outcome influenced anchor selection;
- a no-anchor baseline was silently replaced;
- provider failures were counted as negative branches;
- standard parent-history events were recounted as branch-continuation effects;
- structural differences were presented as semantic C/P/R/penetration conclusions.

## 15. Current status

Prepared and offline-tested:

- Phase-A baseline snapshot path;
- structural-only anchor selector;
- Phase-B frozen branch-plan builder;
- one-variable status intervention proof;
- counterbalanced pair manifests;
- execution-code binding;
- guarded Phase-B real runner;
- post-freeze Measurement-v3 derivation;
- Phase-A and Phase-B separate paid authorization gates.

No new paid subject or Reviewer call is authorized or performed by this protocol update.
