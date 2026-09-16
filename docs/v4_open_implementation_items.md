# System Behavior v4 — Remaining Implementation Items

Date: 2026-09-16  
Status: OPEN IMPLEMENTATION TRACKER

The v4 theory/measurement layer is additive. The items below are not claims of scientific completion.

## Completed offline engineering layer

- current `R2-ARENA-TRACE-v0.3` source adapter → `RB-BEHAVIOR-EVENT-v0.1`;
- explicit proposal / realization / read / node-execution phases;
- immutable-source check: adapter does not rewrite source trace;
- current message-read and invocation-read lifecycle mapping;
- shared-state / invocation / message / FINAL-reopen boundary mapping;
- synchronized v4 trajectory record emitted from the same source trajectory;
- frozen `structural_jump_detector_v0.1` structural-candidate rules;
- frozen `operational_boundary_set_v0.1` mechanical crossing rules;
- event-level Jump candidates may carry multiple structural types without becoming multiple events;
- branch continuation slicing primitive using `behavior_event.turn > branch_start_turn`;
- synchronized R2/R3/R4 structural dynamics view with semantic Jump/R/penetration kept unadjudicated;
- CI runs registry, adapter and dynamics preflights;
- adapter/detector fail closed on unsupported source or registry boundaries.

Current implementation:

- `arena/system_behavior_adapter.py`
- `arena/system_behavior_dynamics_v4.py`
- `arena/system_behavior_trace_preflight.py`
- `arena/system_behavior_dynamics_preflight.py`
- `arena/tests/test_system_behavior_adapter.py`
- `arena/tests/test_system_behavior_dynamics_v4.py`
- `configs/structural_jump_detector_v0.1.json`
- `configs/operational_boundary_set_v0.1.json`

## P0 — before new real v4 subject evidence

- freeze explicit source-backed lineage rules for message/invocation/read/state visibility;
- define the subset of lineage + operational crossings that may support a formal penetration-depth candidate;
- bind current R5/R6 branch plans to experimental-variable registry hash, measurement-boundary registry hash, detector hash and operational-boundary-set hash without rewriting historical branch-plan versions;
- bind new subject evidence to exact v4 measurement/registry/adapter/detector/boundary hashes;
- add source-version adapter coverage for any future trace schema before that schema is used for v4 evidence.

## P1 — after first v4 subject evidence

- derive source-backed descendant lineage rather than temporal-order proxies;
- generate bounded semantic review windows from behavior candidates;
- test lineage coverage for shared-state, message, invocation and FINAL/reopen events under real subject evidence;
- freeze primary first-paper dynamic metrics;
- add v4 branch comparison adapter without replacing Measurement v3 historical records.

## P2 — future research expansion

- PRE tension-antecedent experiments;
- POST stabilization experiments;
- multi-level dose/response designs;
- topology/Agent-count scaling studies;
- cross-domain replications;
- human reviewer IRR for v4 small-window semantic packets.

## Explicitly not required now

- full hidden reasoning capture;
- direct Tension measurement;
- paid API calls;
- re-running historical evidence solely to fill new v4 fields.