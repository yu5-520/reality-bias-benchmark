# V5 Cross-Domain Semantic Triage Report v1

Date: 2026-09-19  
Role: frozen-evidence audit-queue construction  
Status: COMPLETE / AWAITING LOCALIZED SEMANTIC AUDIT

## 1. Scope

This report records the deterministic triage stage executed after the completed held-out three-domain first round.

Source subject workflow: `35370679448`  
Source execution SHA: `b712dabc227973470900af4aea4e13d1077f5696`  
Preserved natural trajectories: **90 / 90**  
Runner errors: **0**

The triage stage did not rerun any subject trajectory.

## 2. Triage method

The frozen contract is:

- `configs/v5_cross_domain_semantic_triage_v0.1.json`
- `docs/cross_domain_semantic_triage_protocol_v0.1.md`
- `arena/build_v5_cross_domain_semantic_triage.py`

Each trajectory receives up to three deterministic audit roles:

1. **FORMATION_ANCHOR** — earliest non-control structural repair-anchor candidate.
2. **PROPAGATION_ANCHOR** — structurally widest cross-Agent observation surface.
3. **AUTHORITY_REVIEW_ANCHOR** — earliest candidate selected by the frozen status/lexical authority-review rule.

If multiple roles select the same candidate, they are merged into one case packet.

## 3. Execution history

The first execution attempt, workflow `35376830512`, failed before producing a triage artifact because source extraction accepted only `write_state`, while the already-frozen v5 structural index correctly treats both `write_state` and `revise_final_state` patch materializations as state writes.

The failure did not alter source evidence and made zero provider/evaluator calls.

PR #61 aligned triage extraction with the existing `_state_write_rows` semantics and added a regression test.

Successful triage workflow: `35377246079`  
Successful execution SHA: `435ef100f9848dee37a44f07010b3bce9135cb33`  
Artifact: `v5-cross-domain-semantic-triage-35370679448-35377246079`  
Artifact ID: `10560253559`  
Artifact digest: `sha256:b0e8b264cd6ee5b8970f3dbe186a49b3e23a5ae33eb67c01076afc7d8baf0550`  
Summary hash: `0cb90df320499618d3684b21071783f31995d2427efc3e94cdd49d776b0fabfa`

## 4. Result

The original structural stage produced **2,127** repair-anchor candidate rows across 90 trajectories.

Deterministic triage generated:

- **90** FORMATION_ANCHOR assignments;
- **90** PROPAGATION_ANCHOR assignments;
- **85** AUTHORITY_REVIEW_ANCHOR assignments;
- **167 unique localized-audit cases** after role overlap was deduplicated.

The 167-case queue is **7.85%** of the original 2,127 structural candidate rows.

Domain-level unique case counts:

| Domain | Trajectories | Selected unique cases | Trajectories with authority-review anchor |
| --- | ---: | ---: | ---: |
| finance | 30 | 50 | 29 |
| supply_chain | 30 | 53 | 30 |
| software_engineering | 30 | 64 | 26 |
| **Total** | **90** | **167** | **85** |

Selected-case source statuses:

| Source status | Cases |
| --- | ---: |
| provisional | 75 |
| recommendation | 46 |
| fact | 36 |
| unspecified | 10 |

These counts describe where the next semantic audit should inspect evidence. They are **not** counts of semantic errors.

## 5. Interpretation boundary

The triage stage establishes only an audit-location index.

It does not establish:

- semantic adoption;
- semantic transformation;
- authority error or authority migration;
- semantic inheritance;
- System Inertia;
- CPR;
- causal origin;
- R5 eligibility;
- R7 repairability.

In particular, an `AUTHORITY_REVIEW_ANCHOR` means that an explicit status/lexical rule identified a location requiring semantic review. It does not mean the source authority is wrong.

All 167 cases remain:

`AWAITING_LOCALIZED_SEMANTIC_AUDIT`

and:

`semantic_status = NOT_ADJUDICATED`.

## 6. Active-stage boundary

This stage made:

- provider calls: **0**;
- paid evaluator calls: **0**;
- R5 probe calls: **0**;
- R7 repair calls: **0**;
- R8 CPR adjudications: **0**.

Natural-subject authorization did not propagate into any later active stage.

## 7. Next scientific step

Localized semantic audit should now inspect the 167 case packets against the frozen raw trajectories, preserving the trajectory as the sampling unit.

The audit should decide, for each relevant case, whether the observed structure reflects:

- mere visibility/relay;
- semantic adoption;
- semantic transformation;
- downstream decision/action dependence;
- authority materialization/change;
- or `NOT_ESTABLISHED`.

Only append-only semantic audit may later promote a source-bound case to `ELIGIBLE_R5_ATOMIC_PROBE` or `NOT_ELIGIBLE_R5`.
