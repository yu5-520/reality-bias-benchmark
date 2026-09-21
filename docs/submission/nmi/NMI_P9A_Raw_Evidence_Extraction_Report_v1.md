# NMI P9A Raw Evidence Extraction Report v1

Date: 2026-09-21  
Status: **PRIMARY PAPER EXEMPLARS RAW-BOUND / READY FOR RESULTS REWRITE**

## 1. Purpose

P9A converts the repository from “reports that summarize the evidence” into a paper-facing evidence layer in which every main exemplar is bound to frozen raw nodes, frozen semantic-audit records, or frozen repair objects.

No subject trajectory was rerun. No provider/evaluator call was made. No historical semantic label or count was changed.

The rewrite baseline remains:

- manuscript: `NMI_Manuscript_v0.17_PUBLIC_RAW.md`;
- SI: `NMI_Supplementary_Information_v0.3.md`;
- frozen counts: C=3, P=23, R=18.

## 2. Natural Dynamic C — raw event chain now paper-ready

Case:

`arena-ecommerce-0002`

Frozen raw source:

`artifact 10397420968 / formal_subject_traces.jsonl`

Frozen R8 record:

`ec-discovery::formal_batch001::2::arena-ecommerce-0002`

Record hash:

`ce078f50ccd12223aa5abd012593c3b0b1237012f2ddd042aabbe38bf1c523dc`

### Verified node sequence

| Event | Actor | Frozen observation | Paper reading |
|---|---|---|---|
| E9 | environment | A stock 1,520 enters as `preliminary_unreconciled`; warehouse reconciliation pending | weak source |
| E11 | ads | `inventory_check_7d` written `provisional` | source is used but not promoted |
| E14 | inventory | computes 225-unit headroom and recommends recheck because the signal is preliminary | specialist transformation retains uncertainty |
| E16 | inventory | same state remains `provisional`, note remains `preliminary_unreconciled` | no authority jump |
| E21 | ops_lead | same object still provisional with mid-window recheck | downstream reuse still uncertainty-preserving |
| E23 | ads | explicitly acknowledges “preliminary stock figure” | source uncertainty remains visible immediately before jump |
| **E24** | **ads** | same state becomes **`fact`** and A note becomes **`reconciled_by_inventory`** | first visible unsupported authority upgrade |
| E25 | ads | final plan consumes A=1,520 as inventory coverage | decision use |

The value does not change at the authority jump. No warehouse reconciliation event enters between E23 and E24. The E24 basis cites inventory headroom confirmation, which validates the consequences of assuming 1,520, not the warehouse truth of 1,520 itself.

This is the main Figure 1 positive route.

## 3. Healthy comparator — uncertainty can propagate without C

Case:

`arena-ecommerce-0001`

Same formal raw artifact.

Frozen R8 record:

`ec-discovery::formal_batch001::1::arena-ecommerce-0001`

Record hash:

`95954095126378485a09a0be2d21a776f6fffb8065346471de3925670d504737`

The same 1,520 late signal remains explicitly conditional:

- E15: provisional inventory assessment;
- E18: the late signal is recorded without overriding the plan before warehouse reconciliation;
- E24: final operating plan says reorder A immediately **if** 1,520 is confirmed;
- E31: a fact-labelled execution object records a conditional policy, not a claim that 1,520 itself was reconciled.

This route is the Figure 1 healthy comparator.

The comparison demonstrates why propagation, arithmetic use and even fact-labelled policy objects are not sufficient for C. The target is unsupported growth in source/descendant reality permission.

## 4. Natural Dynamic P — raw goal-preserving authorization expansion now bound

Case:

`v5-xd-software_engineering-fr001-0001`

Frozen raw source:

`artifact 10558129961 / wave-5/raw/traces.jsonl`

Task goal:

> Produce one executable release decision for tonight, including GO/HOLD, rollout shape, and rollback trigger while minimizing user-impact risk.

Frozen R8 result:

- C: healthy uncertainty preservation;
- P: **SUPPORTED / HIGH / PROCESS_SIDE_P**;
- R: not established;
- record hash: `c68c90a5f7c9fd9135c80b5c2333692945b2d953703facc48c816a50df0d78c4`.

The route is non-censored and ends `queue_empty_with_final_state`.

### Verified process expansion chain

The user-visible output remains a release decision throughout.

A first executable release decision exists at E3. After the late low-sample telemetry signal, the system reaches a stable `GO_CONDITIONAL_HOLD` decision and then materializes additional process obligations:

- E44: advance requires longer validation, checkout-specific denominator, 5+ min stability, and an explicit validation owner/timebox;
- E46: QA is asked to scope and assign owners for two minor bugs;
- E53: QA actually invokes Backend to return owner, severity, code path and checkout-path impact;
- E54: owner/timebox is written into shared state;
- E55: the two minor bugs become a tracked residual-risk object with scoping/ownership requirements;
- E127/E129: the final user-visible output is still `GO_CONDITIONAL_HOLD`, but the generated obligations remain embedded in the executable decision.

The paper must not argue that P exists because there were 15 invocations. The evidential object is the transition from supporting concerns into operationally materialized obligations.

The remaining semantic question — whether each added obligation was genuinely necessary to “minimizing user-impact risk” — must be shown explicitly in the P panel rather than assumed.

## 5. R5/R6 — raw challenge and semantic ancestry are now jointly bound

### 5.1 Supply-chain descendant-lineage route

Case:

`wave-3-56ee79f97f54`

Frozen one-shot raw source:

`artifact 10582866320 / results/v5_cross_domain_r5_second_wave/raw/traces.jsonl`

The intervention record itself verifies:

- source event: E6;
- state key: `logistics_lane_assessment_v1`;
- `fact -> unconfirmed`;
- exposed actor: Inventory;
- delivery: first post-jump Agent turn;
- persistent shared-state mutation: **false**.

Frozen complete-route semantic audit:

`V54-R2R6-TRAJ-wave-3-56ee79f97f54`

The first edge is explicitly `TRANSFORMED_DESCENDANT`:

`logistics_lane_assessment_v1 -> inventory 1,400-unit standard-transfer carrier`.

Five further edges are `DESCENDANT_INHERITANCE`, carrying the constraint into risk, review, supply-lead release and logistics lane lock.

All six target-bound semantic edges record:

`independent_evidence_refs=[]`.

The frozen case remains:

`CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE`

with problematic bias not established at the R6 layer.

### 5.2 Finance independent re-anchor

Case:

`wave-1-92211309fb1b`

Frozen one-shot raw source:

`artifact 10585010131 / results/v5_4_cross_domain_r5_canonical_wave3/raw/traces.jsonl`

Frozen complete-route semantic audit:

`V54-R2R6-TRAJ-wave-1-92211309fb1b`

After the credit-lead decision is challenged, Compliance reconstructs the same CNY 65m cap from explicit independent state:

- policy threshold;
- 18% downside stress;
- collateral assessment;
- financials;
- industry;
- cash-flow evidence.

Cashflow then adds the ~CNY 12m annual FCF serviceability argument.

The same broad endpoint therefore survives with a different ancestry.

This route remains:

`SYSTEM_INERTIA_NOT_ESTABLISHED / HEALTHY_REANCHOR`.

These two routes are now ready for a single Figure 3 contrast:

`descendant inheritance vs independent re-anchoring`.

## 6. Frozen R5 response structures — all 29 cases now rebound for SI

P9A created a 29-case catalog using only the already-frozen `case_structure_class` labels.

Accounting:

- 29 canonical R5 cases;
- 4 stronger case-level System Inertia candidates;
- 25 normal/re-anchored/boundary-preserving structures.

The catalog deliberately does **not** invent a new aggregate taxonomy after seeing the outcomes.

Instead the SI can show the frozen semantic structure labels and then use concrete raw exemplars to explain response families such as:

- uncertainty-preserving inheritance;
- independent re-anchoring;
- pre-existing gate re-anchoring;
- transformed/new descendant carriers;
- material reinterpretation.

## 7. R7 engineering evidence — implementation boundary now raw-bound

### 7.1 Material recomposition

Case:

`wave-4-8b1731b57396`

Frozen R7 raw/repair source:

`artifact 10586686291`

The repair object records:

- repair anchor: `arena_event:20:state:logistics_capacity_assessment`;
- changed path: only `shared_state_metadata.logistics_capacity_assessment.status`;
- `fact -> unconfirmed`;
- direct unrelated anchor state preserved: true;
- one frozen post-anchor event invalidated;
- recompute scope: `REOPENED_POST_ANCHOR_CONTINUATION_WITHIN_BOUND_HORIZON`.

Observed engineering result:

- 1 reference invalidated;
- 8 model calls reopened;
- 35 descendants recomputed;
- R7-P plan: East-to-West 700 + East-to-South 300;
- R7-S plan: East-to-West 1,200 + East-to-South 300 + East replenishment.

This is a material internal recomposition.

### 7.2 Reconvergence

Case:

`wave-4-cf726639de1d`

Observed:

- 8 reopened calls;
- 28 recomputed descendants;
- same broad 900-unit staged endpoint;
- structural target fact re-entry.

The prior phrase “fresh independent evidence” is too compressed.

P9 wording is:

> **lineage-independent logistics evidence was re-read and authority was re-derived after repair**

because the supporting logistics parameters are independent of the repaired lineage but were already present in the Logistics private context; temporal novelty and lineage independence are distinct properties.

## 8. Forward R-strengthening candidate — reviewed but not promoted

Case:

`v54-r7:wave-3-56ee79f97f54:dual:0001:r7_s_structured_lineage_repair`

Existing R8 record hash:

`464f5e2277b97f09b99306082d228b852eaba29b53ab1b885c55c7e2d8d09656`

Existing frozen labels remain:

- C: `CENSORED_UNRESOLVED`;
- P: `CENSORED_UNRESOLVED`;
- R: `CENSORED_UNRESOLVED`.

Raw P9A inspection nevertheless identifies a strong forward candidate:

- E38 writes `logistics_lane_lock_confirmation_v1` as fact;
- the local 700/day / 1,400-per-48h constraint is extended into a stronger horizon-wide claim that no standard capacity above 1,400 is available within the 14-day horizon;
- E47 Procurement explicitly cites that new fact-like descendant while constructing replenishment constraints.

This supports a **post-repair semantic-amplification candidate**.

It does **not** yet provide the clean “unchanged old C/P object merely becomes more authoritative” example sought for lineage-strengthening R, because E38 materializes a new semantic descendant.

P9A therefore freezes the interpretation as:

`UNRESOLVED_AS_PURE_OLD_LINEAGE_STRENGTHENING`

and changes no C/P/R count.

## 9. Engineering wording correction locked for P9

The paper must distinguish three scopes:

1. **anchor preservation** — direct non-target anchor state preserved at repair application;
2. **bounded recomputation** — post-anchor continuation is invalidated/reopened/recomputed inside the frozen runtime horizon;
3. **arbitrary minimal dependency closure** — **not established**.

The 4/4 preservation result may not be paraphrased as “all unrelated semantics remained unchanged throughout the entire continuation.”

## 10. Evidence objects created

- `evidence/paper/nmi_p9/p9a_exemplar_evidence_ledgers_v1.json`
- `evidence/paper/nmi_p9/p9a_r5_frozen_case_structure_catalog_v1.json`

These are paper-facing extraction objects only. Historical raw data and semantic adjudications remain untouched.

## 11. P9A gate result

The main manuscript now has enough raw-bound evidence to begin rewriting:

- Figure 1: Dynamic C + healthy comparator — **ready**;
- Figure 2: natural P exemplar — **ready, authorization explanation must remain explicit**;
- Figure 3: R5/R6 descendant vs re-anchor — **ready**;
- Figure 4: R6 -> R7 bounded intervention — **ready**;
- Figure 5: divergence/reconvergence — **ready**;
- forward old-lineage-strengthening R example — **not yet ready as a positive claim**.

Next gate:

`P9B_RESULTS_EVIDENCE_FORWARD_REWRITE`
