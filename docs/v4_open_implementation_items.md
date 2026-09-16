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
- branch continuation slicing using `behavior_event.turn > branch_start_turn`;
- synchronized R2/R3/R4 structural dynamics view with semantic Jump/adoption/R/Authority Penetration kept unadjudicated;
- additive `RB-R5R6-V4-RESEARCH-BINDING-v0.1` freezes branch-plan identity, code SHA and exact v4 instrument hashes without rewriting historical branch-plan schemas;
- forward Phase-B workflow prepares and verifies `v4_research_binding.json` before any provider call;
- forward Phase-B authorization/journal/trace/error/summary artifacts carry the v4 binding hash;
- frozen `RB-V4-SEMANTIC-AUTHORITY-REVIEW-CONTRACT-v0.1` and `RB-V4-REVIEW-PACKET-POLICY-v0.1`;
- bounded Reviewer-v4 packets localize Jump + source-backed lineage + exact mechanical operational crossings + recorded agent-visible contract excerpts;
- bounded packets explicitly exclude full trajectory, raw model output and hidden chain-of-thought; truncation/missingness is recorded rather than inferred away;
- Reviewer-v4 records are append-only, packet/hash bound, evidence-ref constrained and preserve disagreement;
- `derive_branch_measurements_v4.py` derives Measurement v4, dynamics, lineage and bounded packets from the same frozen Phase-B trace/evidence batch without replacing Measurement v3;
- paired v4 structural branch comparison now verifies same pair, same frozen parent, same evidence batch, same v4 binding and the single registered intervention before computing structural deltas;
- paired structural deltas remain `semantic_status = NOT_ADJUDICATED` and `causal_effect_status = NOT_ADJUDICATED`;
- CI covers registry, adapter, dynamics, lineage, research binding, bounded review, append-only review ledger and post-freeze v4 branch derivation preflights;
- adapter/detector/lineage/binding/review layers fail closed on unsupported sources, drifted hashes, unknown evidence refs or invalid semantic promotion.

Current implementation includes:

- `arena/system_behavior_adapter.py`
- `arena/system_behavior_dynamics_v4.py`
- `arena/system_behavior_lineage_v4.py`
- `arena/v4_experiment_binding.py`
- `arena/v4_review_contract.py`
- `arena/v4_review_packets.py`
- `arena/v4_review_ledger.py`
- `arena/derive_branch_measurements_v4.py`
- `arena/branch_comparison_v4.py`
- `arena/v4_review_preflight.py`
- `arena/v4_branch_derivation_preflight.py`
- `configs/structural_jump_detector_v0.1.json`
- `configs/operational_boundary_set_v0.1.json`
- `configs/source_lineage_rules_v0.1.json`
- `configs/v4_semantic_authority_review_contract_v0.1.json`
- `configs/v4_review_packet_policy_v0.1.json`
- `schemas/r5r6_v4_research_binding_v0.1.schema.json`
- `schemas/v4_bounded_review_packet_v0.1.schema.json`
- `schemas/v4_semantic_authority_review_v0.1.schema.json`
- `schemas/branch_trajectory_comparison_v4.schema.json`

## P0 — before new real v4 subject evidence

- freeze the first-paper primary/secondary outcome registry and aggregation/censoring rules before inspecting new subject outcomes;
- freeze which structural outcomes are confirmatory, which semantic Reviewer-v4 outcomes are confirmatory, and which are exploratory;
- freeze pair-level versus batch-level estimands for the current R5-MID status-downgrade experiment;
- confirm the current Phase-B real workflow emits the v4 paired-comparison artifact alongside Measurement v3 and all v4 structural artifacts;
- add source-version adapter coverage before any future trace schema beyond `R2-ARENA-TRACE-v0.3` is used as v4 evidence.

## P1 — after first v4 subject evidence

- test source-backed lineage coverage for shared-state, message, invocation and FINAL/reopen events under real subject evidence;
- inspect missingness/truncation rates before any semantic conclusion;
- perform independent bounded Reviewer-v4 adjudication asynchronously; do not rerun subject evidence for reviewer disagreement;
- compare mechanical penetration-depth candidates with semantic Authority adjudication without treating them as interchangeable;
- estimate Reviewer agreement as a sensitivity layer, not a source-evidence layer;
- aggregate only preregistered complete/censored pairs according to the frozen analysis rules.

## P2 — future research expansion

- PRE tension-antecedent experiments;
- POST stabilization experiments;
- multi-level dose/response designs;
- topology/Agent-count scaling studies;
- cross-domain replications;
- broader human/LLM Reviewer IRR.

## Explicitly not required now

- full hidden reasoning capture;
- direct Tension measurement;
- paid API calls;
- re-running historical evidence solely to fill new v4 fields;
- automatic semantic Reviewer calls during subject collection.