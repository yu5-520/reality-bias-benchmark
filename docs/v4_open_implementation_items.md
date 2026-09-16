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
- runtime-snapshot state-origin exposure for source-backed visibility lineage;
- synchronized v4 trajectory record emitted from the same source trajectory;
- frozen `structural_jump_detector_v0.1` structural-candidate rules;
- frozen `operational_boundary_set_v0.1` mechanical crossing rules;
- frozen `source_lineage_rules_v0.1` source-backed lineage rules;
- exact proposal→realization, message/invocation→read, read→Agent-turn, state-mutation→later-runtime-visibility, and final-state-version ancestry edges;
- source-backed descendant/affected-actor derivation from structural Jump roots;
- mechanical penetration-depth candidates derived only from source-backed lineage + operational crossings;
- event-level Jump candidates may carry multiple structural types without becoming multiple events;
- branch continuation slicing primitive using `behavior_event.turn > branch_start_turn`;
- synchronized R2/R3/R4 structural dynamics view with semantic Jump/adoption/R/Authority Penetration kept unadjudicated;
- additive `RB-R5R6-V4-RESEARCH-BINDING-v0.1` freezes branch-plan identity, code SHA and exact v4 interface hashes without rewriting historical branch-plan schemas;
- forward Phase-B workflow prepares and verifies `v4_research_binding.json` before any provider call;
- forward Phase-B authorization/journal/trace/error/summary artifacts carry the v4 binding hash;
- CI runs registry, adapter, dynamics, lineage and v4 research-binding preflights;
- adapter/detector/lineage/binding layers fail closed on unsupported source, drifted hashes or unregistered interfaces.

Current implementation:

- `arena/system_behavior_adapter.py`
- `arena/system_behavior_dynamics_v4.py`
- `arena/system_behavior_lineage_v4.py`
- `arena/v4_experiment_binding.py`
- `arena/system_behavior_trace_preflight.py`
- `arena/system_behavior_dynamics_preflight.py`
- `arena/system_behavior_lineage_preflight.py`
- `arena/v4_binding_preflight.py`
- `arena/tests/test_system_behavior_adapter.py`
- `arena/tests/test_system_behavior_dynamics_v4.py`
- `arena/tests/test_system_behavior_lineage_v4.py`
- `arena/tests/test_v4_experiment_binding.py`
- `configs/structural_jump_detector_v0.1.json`
- `configs/operational_boundary_set_v0.1.json`
- `configs/source_lineage_rules_v0.1.json`
- `schemas/r5r6_v4_research_binding_v0.1.schema.json`

## P0 — before new real v4 subject evidence

- define the confirmatory semantic/Authority adjudication contract that converts only eligible mechanical penetration-depth candidates into Authority Penetration judgments;
- generate bounded semantic-review packet interfaces from localized Jump + lineage + operational-crossing evidence;
- add a v4 post-freeze derivation command for completed Phase-B traces so System Behavior Measurement v4 / lineage outputs are generated from the same frozen evidence batch without replacing Measurement v3;
- add source-version adapter coverage for any future trace schema before that schema is used for v4 evidence.

## P1 — after first v4 subject evidence

- test lineage coverage for shared-state, message, invocation and FINAL/reopen events under real subject evidence;
- freeze primary first-paper dynamic metrics;
- add v4 branch comparison adapter without replacing Measurement v3 historical records;
- compare mechanical penetration-depth candidates with later semantic Authority adjudication rather than treating them as interchangeable;
- measure reviewer agreement over bounded semantic/Authority packets as a sensitivity layer rather than a source-evidence layer.

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