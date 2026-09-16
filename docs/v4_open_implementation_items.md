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
- CI runs both registry preflight and real Arena-v0.3 scripted-trace adapter preflight;
- adapter fails closed on unsupported source trace schemas;
- Jump detector remains explicitly `NOT_RUN_DETECTOR_NOT_FROZEN` rather than silently assigning Jump truth.

Current implementation:

- `arena/system_behavior_adapter.py`
- `arena/system_behavior_trace_preflight.py`
- `arena/tests/test_system_behavior_adapter.py`

## P0 — before new real v4 subject evidence

- bind current R5/R6 branch plans to experimental-variable registry hash and measurement-boundary registry hash without rewriting historical branch-plan versions;
- freeze a v4-compatible Jump detector for any confirmatory Jump-incidence claim;
- define operational-boundary set/version for any formal penetration-depth claim;
- bind new subject evidence to exact v4 measurement/registry/adapter hashes;
- add branch-continuation-aware v4 slicing so parent history is not counted as branch outcome;
- add source-version adapter coverage for any future trace schema before that schema is used for v4 evidence.

## P1 — after first v4 subject evidence

- derive Jump-anchored synchronized R2/R3/R4 views from one frozen trajectory;
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