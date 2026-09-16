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
- exact frozen branch-start state anchors for R5-MID status intervention, including runtime visibility, potential downstream lineage and mechanical reach metrics;
- additive `RB-R5R6-V4-RESEARCH-BINDING-v0.1` freezes branch-plan identity, code SHA and exact v4 instrument hashes without rewriting historical branch-plan schemas;
- research binding now includes structural measurement interfaces, branch-anchor/comparison schemas, canonical Reviewer-v4 contract/policy/schema/generators, and first-paper analysis contract/schema identities;
- forward Phase-B workflow prepares and verifies `v4_research_binding.json` before any provider call;
- forward Phase-B authorization/journal/trace/error/summary artifacts carry the v4 binding hash;
- frozen `RB-V4-SEMANTIC-AUTHORITY-REVIEW-CONTRACT-v0.1` and `RB-V4-REVIEW-PACKET-POLICY-v0.1`;
- bounded Reviewer-v4 packets localize Jump + source-backed lineage + exact mechanical operational crossings + recorded agent-visible contract excerpts;
- supplemental branch-anchor packets localize the exact Phase-B manipulated-state exposure path without reconstructing missing Phase-A evidence;
- bounded packets explicitly exclude full trajectory, raw model output and hidden chain-of-thought; truncation/missingness is recorded rather than inferred away;
- Reviewer-v4 records are append-only, packet/hash bound, evidence-ref constrained and preserve disagreement;
- `derive_branch_measurements_v4.py` derives Measurement v4, dynamics, lineage, branch-anchor views, bounded packets and paired comparisons from the same frozen Phase-B trace/evidence batch without replacing Measurement v3;
- paired v4 structural branch comparison verifies same pair, same frozen parent, same evidence batch, same v4 binding and the single registered intervention before computing structural deltas;
- paired structural deltas remain `semantic_status = NOT_ADJUDICATED` and `causal_effect_status = NOT_ADJUDICATED`;
- frozen `RB-FIRST-PAPER-ANALYSIS-CONTRACT-v0.1` defines primary/secondary/exploratory outcomes, pair eligibility, censoring, missingness, semantic resolution and batch aggregation before new v4 subject evidence;
- primary first-paper endpoint is `R5MID_ANCHOR_DOWNSTREAM_OPERATIONAL_CROSSING_COUNT`; intervention-minus-control pair deltas are aggregated by arithmetic mean with median as robust summary;
- primary uncertainty rule is a deterministic paired nonparametric percentile bootstrap only when the frozen minimum complete-pair count is met; no primary p-value is invented;
- real Phase-B workflow now emits all v4 structural artifacts and applies the frozen first-paper structural analysis after evidence freeze, without a paid evaluator;
- CI executes the same first-paper analysis contract against deterministic fixture pair comparisons;
- adapter/detector/lineage/binding/review/analysis layers fail closed on unsupported sources, drifted hashes, unknown evidence refs, invalid pair identity or semantic promotion.

Current implementation includes:

- `arena/system_behavior_adapter.py`
- `arena/system_behavior_dynamics_v4.py`
- `arena/system_behavior_lineage_v4.py`
- `arena/branch_anchor_lineage_v4.py`
- `arena/v4_experiment_binding.py`
- `arena/v4_review_contract.py`
- `arena/v4_review_packets.py`
- `arena/v4_branch_anchor_review_packets.py`
- `arena/v4_review_ledger.py`
- `arena/derive_branch_measurements_v4.py`
- `arena/branch_comparison_v4.py`
- `arena/first_paper_analysis_contract.py`
- `arena/analyze_first_paper_r5mid.py`
- `arena/v4_review_preflight.py`
- `arena/v4_branch_derivation_preflight.py`
- `configs/structural_jump_detector_v0.1.json`
- `configs/operational_boundary_set_v0.1.json`
- `configs/source_lineage_rules_v0.1.json`
- `configs/v4_semantic_authority_review_contract_v0.1.json`
- `configs/v4_review_packet_policy_v0.1.json`
- `configs/first_paper_analysis_contract_v0.1.json`
- `schemas/r5r6_v4_research_binding_v0.1.schema.json`
- `schemas/v4_bounded_review_packet_v0.1.schema.json`
- `schemas/v4_semantic_authority_review_v0.1.schema.json`
- `schemas/branch_start_state_anchor_v0.1.schema.json`
- `schemas/branch_trajectory_comparison_v4.schema.json`
- `schemas/first_paper_analysis_contract_v0.1.schema.json`
- `schemas/first_paper_structural_analysis_v0.1.schema.json`

## P0 — before new real v4 subject evidence

For the current `R2-ARENA-TRACE-v0.3` R5-MID status-downgrade design, the mandatory offline measurement/analysis definitions are now frozen.

Remaining pre-subject conditions are execution conditions rather than new outcome design:

- keep the full offline CI green at the exact commit used for preparation;
- use only the bound trace schema/model/config/code/review/analysis interfaces recorded by `v4_research_binding.json`;
- do not alter v0.1 outcome definitions, pair eligibility, censoring or aggregation rules after inspecting new subject outcomes;
- resolve provider/model/call cap/spending ceiling/currency only through an explicitly authorized future run;
- add source-version adapter coverage before any future trace schema beyond `R2-ARENA-TRACE-v0.3` is used as v4 evidence.

No extra subject run should be created to manufacture a minimum pair count, repair reviewer disagreement, fix an inconvenient outcome or backfill a missing structural event.

## P1 — after first v4 subject evidence

- verify real-evidence source-backed lineage coverage for shared-state, message, invocation and FINAL/reopen events;
- inspect execution censoring, packet truncation and missingness rates before semantic conclusions;
- apply the frozen structural analysis contract without changing primary/secondary outcome definitions;
- perform independent bounded Reviewer-v4 adjudication asynchronously; do not rerun subject evidence for reviewer disagreement;
- compare mechanical penetration/reach candidates with semantic Authority adjudication without treating them as interchangeable;
- estimate Reviewer agreement as a sensitivity layer, not a source-evidence layer;
- aggregate only preregistered complete/resolved pairs according to the frozen rules;
- keep unresolved/uncertain/insufficient semantic evidence as missing/non-resolution rather than encoding it as `NO`.

## P2 — future research expansion

- PRE tension-antecedent experiments;
- POST stabilization experiments;
- multi-level dose/response designs;
- topology/Agent-count scaling studies;
- cross-domain replications;
- broader human/LLM Reviewer IRR;
- additive analysis-contract versions for new variables/experiments, never silent replacement of first-paper v0.1.

## Explicitly not required now

- full hidden reasoning capture;
- direct Tension measurement;
- paid API calls;
- re-running historical evidence solely to fill new v4 fields;
- automatic semantic Reviewer calls during subject collection;
- outcome-aware modification of the frozen first-paper analysis contract.