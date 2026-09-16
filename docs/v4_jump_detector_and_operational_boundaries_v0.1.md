# v4 Structural Jump Detector & Operational Boundary Set v0.1

Date: 2026-09-16  
Status: FROZEN OFFLINE INTERFACE / NOT SCIENTIFIC EVIDENCE

## 1. Purpose

This layer converts normalized `RB-BEHAVIOR-EVENT-v0.1` records into two machine-readable structural indexes:

```text
BehaviorEvent
├── Structural Jump Candidate
└── Mechanical Operational Boundary Crossing
```

Neither index is a semantic Reality Bias label.

## 2. Structural Jump detector

Frozen config:

`configs/structural_jump_detector_v0.1.json`

Current rule families:

- realized shared-state mutation;
- realized high-certainty shared-state write;
- realized invocation-graph expansion;
- realized final-state revision.

The detector answers:

> Where did an observable task-relevant state/routing/temporal displacement occur under the frozen structural rule?

It does **not** answer:

- whether the displacement was unauthorized;
- whether it is C/P/R;
- whether Tension or Escape Propensity was directly observed;
- whether the event caused downstream behavior.

One BehaviorEvent may match multiple structural rule types but remains one event-level Jump candidate.

## 3. Operational boundary set

Frozen config:

`configs/operational_boundary_set_v0.1.json`

Current mechanically countable crossings:

- `INFORMATION_STATE_COMMIT` — realized shared-state write;
- `INVOCATION_COMMIT` — realized invocation;
- `TEMPORAL_REVISION_COMMIT` — realized final-state revision;
- `FINAL_SETTLEMENT` — realized finalization;
- reserved explicit commit/authority-conversion boundaries for future runtimes.

An operational crossing is not automatically Authority Penetration. Authorized normal behavior is also counted when it crosses the same structural boundary.

## 4. Post-candidate order versus lineage

v0.1 intentionally distinguishes:

```text
post-candidate temporal order ≠ causal lineage ≠ Authority Penetration
```

The current dynamics view may count later events, actors and operational crossings after the first structural Jump candidate. These are temporal-order measurements only.

Therefore `descendant_event_count` and `affected_agent_count` remain zero until a separate lineage criterion is frozen and satisfied.

## 5. Branch continuation slicing

The v0.1 dynamics layer includes a branch-safe slicing primitive:

```text
behavior_event.turn > branch_start_turn
```

for a branch whose frozen parent is the after-turn snapshot at `branch_start_turn`.

This prevents parent history from being silently recounted as branch outcome. Provider hidden state is still not claimed replayed.

## 6. Synchronized R2/R3/R4 output

`arena/system_behavior_dynamics_v4.py` updates one v4 trajectory measurement with:

- R2 structural Jump candidate count/type/first location;
- R3 operational crossing and post-candidate order counts while lineage/penetration remain unadjudicated;
- R4 structural revision windows while semantic R remains unadjudicated.

## 7. Offline validation

Deterministic preflight:

```bash
python -m arena.system_behavior_dynamics_preflight \
  --outdir results/system_behavior_dynamics_preflight
```

The fixture currently asserts:

- 3 structural Jump candidates;
- 5 mechanical operational crossings;
- Jump truth remains `NOT_ADJUDICATED`;
- penetration remains `NOT_ADJUDICATED`;
- temporal order is not relabeled as lineage.

These numbers validate implementation shape only and are not scientific estimates.

## 8. Next boundary

The next offline layer should freeze explicit lineage relations from source-backed message/invocation/read/state visibility evidence, then define what subset can support a formal penetration-depth candidate.

No paid provider call is authorized by this document.