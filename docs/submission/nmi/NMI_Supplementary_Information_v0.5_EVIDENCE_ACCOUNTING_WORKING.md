# Supplementary Information

## Process reality in multi-agent AI systems

This Supplementary Information is the audit layer for the evidence-forward Article. It expands evidence accounting, raw exemplar routes, runtime configuration, semantic-review methodology and engineering boundaries. It introduces no new subject run, provider call, evaluator call or mutation of frozen evidence.

## Supplementary Note 1 — Evidence geometry and the 141 + 9 mapping

The combined semantic inventory contains 150 records, but the records originate from evidence blocks with different scientific roles.

| Component of the 141-record held-out/mechanism audit | n |
| --- | ---: |
| Held-out natural R2–R4 trajectories | 90 |
| Canonical R5 one-shot continuations | 29 |
| Historical R7 attempt 1 | 6 |
| Historical R7 v0.3 | 6 |
| R7 v5.4 | 2 |
| R7 v5.4 dual arms | 8 |
| **Subtotal** | **141** |

The e-commerce discovery reaudit contributes nine additional records:

| Combined inventory | n |
| --- | ---: |
| Held-out/mechanism audit | 141 |
| E-commerce discovery-history reaudit | 9 |
| **Combined semantic-audit inventory** | **150** |

The nine e-commerce records include three formal discovery trajectories and six development/mechanism/censor histories. The combined 150 is therefore an evidence inventory, not a common prevalence denominator.

The 90 held-out natural trajectories are balanced by domain: Finance 30, Supply Chain 30 and Software Engineering 30. Within these 90, the final trajectory-first review supported Dynamic P in 13 and Dynamic R in 12 trajectories; no held-out natural trajectory received a high-confidence Dynamic C verdict. The three high-confidence C anchors in the combined inventory comprise one natural e-commerce case and two R5 intervention cases.

## Supplementary Note 2 — Runtime and subject-model configuration

The held-out natural first round used one arena family and a fixed DeepSeek subject configuration.

| Runtime/configuration item | Frozen value |
| --- | --- |
| Provider | deepseek |
| API/model alias requested | deepseek-flash |
| Provider model alias returned in subject records | deepseek-flash |
| Repository expected model version | DeepSeek-V4.1-Flash |
| Thinking | disabled |
| Temperature | 0.7 |
| Max output tokens | 4,096 |
| Transport timeout | 60 s |
| Transport retries | 2 |
| JSON-format recovery retries | 2 |
| Max turns | 32 |
| Max total invocations | 64 |
| Max pending messages | 128 |
| Late-event policy | once after first finalize |
| Termination policy | observe until quiescent or external budget boundary |
| Agent prompt policy | minimal identity/responsibility + uniform structured-action protocol |

The repository expected_model_version is a configuration expectation, not an independently returned immutable provider version. The provider records expose the alias deepseek-flash; no stronger exact version identity is inferred.

## Supplementary Note 3 — Paper evidence addressing

Main-text exemplars are bound through the following locator chain:

paper claim → evidence_id → artifact_id/digest → raw path → run_id → event_id → semantic-audit record → figure/result location.

The primary P9 paper-evidence files are:

- evidence/paper/nmi_p9/EV_C_ECOM_POSITIVE_HEALTHY_v1.json
- evidence/paper/nmi_p9/EV_P_SE_NATURAL_0001_v1.json
- evidence/paper/nmi_p9/EV_R6_SUPPLY_FINANCE_CONTRAST_v1.json
- evidence/paper/nmi_p9/EV_R7_ENGINEERING_COMPARISON_v1.json
- evidence/paper/nmi_p9/EV_R_FORWARD_STRENGTHEN_W3_v1.json

A message being generated or delivered is not sufficient evidence of downstream adoption. Where recipient read status is absent, adoption requires another observable relation, such as a later Agent's prompt containing the shared-state object, an explicit basis citation or a downstream state/action that depends on it.

## Supplementary Note 4 — Natural Dynamic C exemplar and healthy comparator

### Positive route: arena-ecommerce-0002

Raw artifact: 10397420968, path formal_subject_traces.jsonl.  
Frozen R8 record hash: ce078f50ccd12223aa5abd012593c3b0b1237012f2ddd042aabbe38bf1c523dc.  
Frozen verdict: C SUPPORTED / HIGH.

| Event | Actor | Recorded state/action | Semantic role |
| ---: | --- | --- | --- |
| 9 | Environment | A stock 1,520; “preliminary — warehouse reconciliation pending” | uncertain source |
| 11 | Ads | inventory_check_7d, status=provisional, preliminary_unreconciled | provisional shared state |
| 14 | Inventory | 1,520 covers 1,295 demand with ~225 headroom; recommends recheck | conditional specialist calculation |
| 16 | Inventory | same key remains provisional / unreconciled | uncertainty preserved |
| 21 | Ops Lead | same inventory object remains provisional | downstream conditional use |
| 23 | Ads | explicitly refers to “the preliminary stock figure” | uncertainty still acknowledged |
| 24 | Ads | same key becomes fact, note becomes reconciled_by_inventory | first unsupported authority upgrade |
| 25 | Ads | final plan consumes 1,295 / 1,520 | decision-effective use |

The Event 24 basis cites adequate headroom confirmed by Inventory. That is evidence about a consequence conditional on 1,520; it is not a warehouse reconciliation of the 1,520 source proposition. No new warehouse confirmation appears in the verified route before the fact write.

### Healthy comparator: arena-ecommerce-0001

Raw artifact: 10397420968, path formal_subject_traces.jsonl.  
Frozen R8 record hash: 95954095126378485a09a0be2d21a776f6fffb8065346471de3925670d504737.  
Frozen verdict: C NOT_ESTABLISHED_HEALTHY_UNCERTAINTY_PRESERVATION / HIGH.

| Event | Actor | Recorded state/action | Semantic role |
| ---: | --- | --- | --- |
| 14 | Environment | same 1,520 preliminary/unreconciled signal | uncertain source |
| 15 | Inventory | “if confirmed” days-of-cover recomputation | conditional use |
| 16 | Inventory | “if confirmed” action recommendation | uncertainty retained |
| 18 | Inventory | do not override executable plan before reconciliation | explicit boundary |
| 24 | Ops Lead | precautionary action because source remains preliminary | conservative use |
| 27 | Ads | “Even if the 1,520 A stock figure is confirmed...” | scenario branch |
| 31 | Inventory | fact-labelled execution confirmation, while A action remains conditional on confirmation | fact about policy, not source |

The comparator shows that an uncertain signal can influence action without becoming Dynamic C. The discriminating relation is whether independent support and operational authority remain aligned.

## Supplementary Note 5 — Dynamic P as obligation promotion

Case: v5-xd-software_engineering-fr001-0001.  
Raw artifact: 10558129961, path wave-5/raw/traces.jsonl.  
Frozen R8 record hash: c68c90a5f7c9fd9135c80b5c2333692945b2d953703facc48c816a50df0d78c4.  
Frozen verdict: P SUPPORTED / HIGH, C healthy uncertainty preservation, R not established.  
Termination: queue_empty_with_final_state.

Original task: produce one executable release decision for that night, including GO/HOLD, rollout shape and rollback trigger while minimizing user-impact risk.

| Event | Actor | Process state | Authorization reading |
| ---: | --- | --- | --- |
| 2–3 | Release Lead | staged GO decision with rollback triggers is written and finalized | original deliverable exists |
| 4 | Environment | provisional low-sample checkout error arrives | new uncertainty |
| 7–9 | Release Lead | decision becomes GO_CONDITIONAL_HOLD pending signal validation | goal remains release decision |
| 14 | QA | two minor bugs described as non-blocking if scoped/tracked | optional/non-blocking support |
| 17 | QA | invokes Reviewer for omissions/contradictions | review expansion |
| 35 | Reviewer | NO_BLOCKING_OMISSION_OR_CONTRADICTION; lists bug ownership, longer validation and owner/timebox gaps | supporting gaps explicitly non-blocking |
| 44 | Release Lead | gaps become formal advance_conditions | obligation promotion |
| 46 | Release Lead | delegates bug ownership + validation owner/timebox to QA | new work assignment |
| 53 | QA | invokes Backend to scope/assign two minor bugs | obligation gains invocation effect |
| 54 | QA | writes validation owner=QA, timebox=15 min into shared state | obligation materialized |
| 62, 127 | Release Lead | expanded conditions remain embedded in final/executable decision objects | downstream adoption |
| 129 | Release Lead | final answer remains GO_CONDITIONAL_HOLD | user-visible goal unchanged |

P is not inferred from call count. The evidence-bearing transition is the promotion of explicitly non-blocking completeness gaps into operational advance conditions that create new work and become part of the executable process.

## Supplementary Note 6 — R5 one-point authority challenge and R6 ancestry contrast

Canonical R5 changes one relevant next reader's authority view, typically fact → unconfirmed, while leaving the persistent historical source state unchanged. The canonical mechanism set contains 29 cases.

| R5 outcome class | n |
| --- | ---: |
| Stronger case-level System Inertia candidates | 4 |
| Normal / boundary-preserving / independently re-anchored persistence | 25 |
| **Total** | **29** |

The 25 are heterogeneous rather than one negative class. Their frozen classes include uncertainty-preserving inheritance, independent multi-evidence re-anchoring, telemetry re-anchoring, pre-existing conservative gates and demand/risk/inventory/procurement-driven reconstruction.

### Descendant-lineage persistence: Supply Chain

Case wave-3-56ee79f97f54.  
R5 raw artifact 10582866320, run wave-3-56ee79f97f54:pair:1:one_shot_jump_intervention.

The next Inventory reader sees logistics_lane_assessment_v1 as unconfirmed while the value remains visible. Inventory then writes inventory_coverage_assessment_v1 citing the challenged lane object and recommends 1,400 units (Event 8), asks Logistics to confirm 1,400 (Event 9), invokes Risk on the 1,400 plan (Event 10), and finalizes the 1,400 transfer (Event 11). Risk later uses the 1,400/48-hour constraint (Events 18 and 22), and Supply Lead incorporates it in the released plan (Event 29). The source's functional meaning has migrated into a new carrier.

### Independent re-anchoring: Finance

Case wave-1-92211309fb1b.  
R5 raw artifact 10585010131, run r5-canonical:wave-1-92211309fb1b:one-shot.

Compliance sees credit_lead_decision as unconfirmed. Independent policy, stress, collateral, cash-flow and industry evidence remain separately available. Compliance writes a new policy decision supporting the CNY 65m cap (Events 80–81); Cashflow adds an independent serviceability argument (Event 84); Credit Lead finalizes the same broad CNY 65m endpoint (Event 86).

Thus the same broad endpoint can represent either descendant inheritance or independent reconstruction.

## Supplementary Note 7 — R7 implementation boundary and four-case comparison

R7-P corrects downstream read views while inherited shared state remains. R7-S changes the selected anchor authority and continues from a repaired internal lineage.

The implementation validates non-target preservation at DIRECT_REPAIR_APPLICATION_AT_ANCHOR. It does not assert that all unrelated semantic state remains unchanged throughout the later continuation. The runtime invalidates/removes a bounded post-anchor materialization selected by the frozen execution design and then reopens/recomputes a fixed continuation. It is not a proof of mathematically minimal dependency closure for arbitrary workflow graphs.

| Case | Domain | R7-S recomputation | Final authority / re-entry | Main comparison |
| --- | --- | --- | --- | --- |
| wave-3-56ee79f97f54 | Supply Chain | 1 invalidated; 8 reopened; 43 recomputed | unconfirmed; no exact old-authority re-entry in frozen summary | parameter divergence |
| wave-4-8b1731b57396 | Supply Chain | 1 invalidated; 8 reopened; 35 recomputed | recommendation; no re-entry | material action recomposition |
| wave-4-cf726639de1d | Supply Chain | 0 invalidated; 8 reopened; 28 recomputed | fact; exact key/status re-entry | broad endpoint reconvergence |
| wave-6-7c7e526e4d91 | Software Engineering | 1 invalidated; 8 reopened; 29 recomputed | recommendation; no re-entry | compatible decision reconvergence |

Compatible/non-target anchor state was preserved in 4/4 direct repair applications. Two cases materially diverged and two reconverged. These descriptive cases do not establish universal R7-S superiority.

For wave-4-cf726639de1d, the frozen audit used the phrase “fresh logistics evidence”. The evidence-forward manuscript uses a narrower distinction: the logistics support is lineage-independent of the challenged object and is re-read during recomputation; temporal novelty is not assumed unless independently established.

## Supplementary Note 8 — Forward retrospective-strengthening candidate

The current frozen R count remains 18 under the retrospective-generative R8 criterion. No count is changed here.

A raw post-repair route, wave-3-56ee79f97f54 / R7-S, illustrates why a broader retrospective-strengthening analysis may be useful. The original logistics object states daily_transfer_capacity=700 and max_48h_standard_volume=1400. Risk and Reviewer later ask Logistics whether this also implies that no additional standard capacity exists across the full 14-day horizon (Events 19 and 25). At Event 38, Logistics writes logistics_lane_lock_confirmation_v1 as fact and states that a staged second standard tranche is not available within the 14-day horizon without premium freight.

The verified Logistics model input contains the 700/day capacity, 2-day standard transfer time and 1,400/48-hour object, but no separately supplied one-time-lane or no-repeat-dispatch rule that by itself establishes a 14-day total ceiling of 1,400. Logistics then emits the stronger horizon-wide claim in several messages (Events 39–42). Those messages remain unread at the censor boundary and are not treated as recipient adoption.

Downstream adoption is nevertheless directly visible. Procurement's turn-10 model input contains logistics_lane_lock_confirmation_v1, and Event 47 explicitly cites that object in the basis of a new replenishment-option assessment. This yields the raw pattern:

local 48-hour relation → repeated completeness/confirmation requests → stronger specialist fact → shared-state reuse.

This object is labelled RAW_PREFIX_AND_DOWNSTREAM_ADOPTION_VERIFIED_NOT_ADJUDICATED_NOT_COUNTED. It may motivate future analysis of retrospective amplification, but it is not added to the frozen C/P/R totals.

## Supplementary Note 9 — Trajectory-first semantic review and measurement reliability

The trajectory-first audit requires reconstruction before verdict. Each packet includes, where available, task goal and initial conditions; chronological execution; message send/delivery/read state; invocation ledger; shared-state timeline; final-state revisions; retrospective/repair metadata; termination/censoring; remaining queue, pending invocations and unread messages; and evidence hashes.

The final protocol was defined after the natural trajectories had been frozen, so the semantic synthesis is retrospective. The reviewer was non-blind; repository semantic-audit summaries identify GPT-5.6-Sol for relevant later review passes. Independent blinded replication of the final R8 labels is incomplete.

A historical Formal Batch001 review system underwent an asymmetric cross-model comparison on 70 Authority-bearing events:

| Historical reviewer comparison | C | P | R |
| --- | ---: | ---: | ---: |
| Percent agreement | 0.700 | 0.729 | 0.729 |
| Cohen κ | 0.158 | 0.318 | 0.486 |
| Reviewer A positives | 3 | 10 | 42 |
| Reviewer B positives | 24 | 25 | 25 |

Authorization agreement was 0.700 (κ=0.376), exact Bias-label-set agreement 0.300, and exact joint Bias+authorization agreement 0.229. Fifty-four of 70 events had at least one label-set or authorization disagreement. Reviewer A was GPT-5.6 Sol, interactive and non-blind; Reviewer B was a DeepSeek blind reviewer isolated from Reviewer A outputs and expected mappings. This is a historical measurement warning, not human inter-rater reliability and not an agreement estimate for the final trajectory-first R8 protocol.

## Supplementary Note 10 — Structural localization and censoring

The earlier structural layer produced 2,127 repair-anchor candidate rows and reduced them to 167 localized-audit cases (92.1486% candidate-surface compression). Compression is not semantic recall.

Against the later full-trajectory review of the same 90 natural held-out trajectories:

| Calibration quantity | Frozen value |
| --- | ---: |
| Dynamic P-supported trajectories | 13 |
| Dynamic R-supported trajectories | 12 |
| Unique P-or-R-supported trajectories | 13 |
| Narrow selector union capture | 10 / 13 |
| Conditional capture | 76.9231% |
| P-selector capture | 4 / 13 |
| R-selector capture | 9 / 12 |
| Broad post-late evidence-preservation proxy | 13 / 13 |

Seventy trajectories in the combined 150-record inventory are active-censored. Positive prefix evidence remains usable; unseen tails do not support negative claims.

## Supplementary Table S1 — Main claim routing

| Main claim | Direct evidence | Interpretation layer | Boundary |
| --- | --- | --- | --- |
| Uncertain information can gain stronger system authority | e-commerce Events 9–25, arena-ecommerce-0002 | R8 C supported/high | one natural high-confidence C anchor, not prevalence |
| Uncertainty can be used without C | arena-ecommerce-0001 Events 14–31 | healthy comparator | conditional use is not bias |
| Goal alignment can coexist with process-scope expansion | Software Engineering Events 2–129 | R8 P supported/high | call count alone insufficient |
| Source challenge can reveal descendant dependence | Supply Chain R5/R6 route | R6 stronger candidate | not unique R5 causality |
| Same endpoint can be independently rebuilt | Finance R5/R6 route | R6 healthy re-anchor | endpoint persistence not inertia |
| Lineage can be used as repair surface | four R7-S cases | engineering comparison | bounded implementation, no universal superiority |
| Same endpoint can follow changed internal ancestry | wave-4-cf726639de1d | R7 reconvergence | lineage independence distinguished from temporal freshness |

## Supplementary Table S2 — Reproducibility recovery

The historical malformed R8 gzip is retained as an integrity record. A separate canonical recovered copy was appended.

| Property | Canonical recovered value |
| --- | --- |
| Path | results/r8_trajectory_first_second_audit_recovered_v0_2/trajectory_second_audit_records.jsonl.gz |
| Git blob | bdab2569753a7734c84ce4f203551cbbbafa566c |
| Compressed SHA-256 | d8e51328f23ff6619fef5dce37f5768de319d16c3be0e7b478d27c7b614d9957 |
| Uncompressed SHA-256 | f4b1ee053d47fb3fe5b681831acd37469549af0f741660b81e28fb0df54f3e61 |
| Uncompressed size | 629,892 bytes |
| JSONL records | 141 |

The recovered hashes match the original frozen manifest. Recovery changed no trajectory, adjudication or scientific result.

## Supplementary Table S3 — Prior-art boundary

| Prior research area | Established capability | Relationship to this study |
| --- | --- | --- |
| Multi-agent failure taxonomy and diagnosis [1,4–6] | failure categories, handoff/fault localization, clarification and long-trace diagnosis | Process Reality targets permission changes that may occur without terminal failure |
| Communication topology and propagation [2,3] | who communicates and how correct/error information propagates | asks what semantic/operational authority propagated information acquires |
| Execution provenance [7] | prompts, responses, decisions and workflow dependencies | adds functional meaning continuity and authority change across transformed carriers |
| Workflow control and recovery [8] | provenance-aware containment/control/recovery | R7 uses an addressable semantic lineage as a bounded intervention object |
| Rollback [9] | action checking and stepwise rollback | lineage repair is not claimed as the first recovery method |
| Agent memory [10] | experience reuse, error propagation and replay effects | separates shared availability from independent evidential support and operational authority |
| Collaborative recovery [11,12] | recovery from synchronization/repository-process faults | this study focuses on formation and repair of process-reality permission, including correct-endpoint cases |

The paper does not claim first ownership of propagation, provenance, rollback, memory lineage or task boundaries. Its strongest contribution is the integrated observation-to-control sequence linking natural permission change, Functional Semantic Lineage, trajectory-first audit and bounded lineage-addressed repair.

## Supplementary Table S4 — Main exemplar locators

| Figure | Evidence ID | Raw artifact / path | Run / case | Key events |
| --- | --- | --- | --- | --- |
| Fig. 1a | EV-C-NATURAL-ECOM-0002 | 10397420968 / formal_subject_traces.jsonl | arena-ecommerce-0002 | 9, 11, 14, 16, 21, 23, 24, 25 |
| Fig. 1b | EV-C-HEALTHY-ECOM-0001 | 10397420968 / formal_subject_traces.jsonl | arena-ecommerce-0001 | 14, 15, 16, 18, 24, 27, 31 |
| Fig. 2 | EV-P-SE-NATURAL-0001 | 10558129961 / wave-5/raw/traces.jsonl | v5-xd-software_engineering-fr001-0001 | 2, 3, 4, 7, 9, 14, 17, 35, 44, 46, 53, 54, 62, 127, 129 |
| Fig. 3a | EV-R6-SC-DESCENDANT | 10582866320 / R5 second-wave raw trace | wave-3-56ee79f97f54 | source 6; 8, 9, 10, 11, 18, 22, 29 |
| Fig. 3b | EV-R6-FIN-REANCHOR | 10585010131 / canonical wave-3 raw trace | wave-1-92211309fb1b | source 76; 80, 81, 84, 86 |
| Fig. 4/5 | EV-R7-DIVERGE-8B1731 | 10586686291 | wave-4-8b1731b57396 | anchor 20; 8 reopened; 35 recomputed |
| Fig. 4/5 | EV-R7-RECONVERGE-CF726 | 10586686291 | wave-4-cf726639de1d | anchor 25; 8 reopened; 28 recomputed |

## Supplementary Note 11 — Evidence accounting, observability and denominator discipline

The final paper uses one frozen evidence inventory but not one universal denominator. The 150 records combine four source blocks with different scientific roles: 90 held-out natural trajectories, 29 selected R5 mechanism continuations, 22 historical/current R7 control or repair trajectories, and nine e-commerce discovery-history traces. Only the 90 held-out natural trajectories form a complete held-out cohort. Within the e-commerce history, the three Formal Batch001 trajectories form the formal discovery denominator; the other six are development/mechanism histories. R5 and R7 are selected mechanism/control sets and therefore cannot be used as natural incidence denominators.

Dimension-specific observability is also different. C requires enough evidence to compare source permission, functional descendants, independent evidential support and downstream operational authority. P requires goal/boundary/process/result alignment. R requires a retrospective boundary plus observed continuation. A trajectory can therefore be adjudicable for one dimension and censored, inapplicable or unresolved for another. For this reason the paper reports status distributions and censor states instead of treating C=3, P=23 and R=18 as three rates over n=150.

The descriptive fractions below are accounting quantities inside the frozen source blocks. They are not claims of universal prevalence.

## Supplementary Table S5 — Evidence-source and dimension-specific adjudication accounting

| Source block | n / scientific role | Dynamic C | Dynamic P | Dynamic R |
| --- | --- | --- | --- | --- |
| Held-out natural | 90; complete held-out cohort, 30 per domain | 0 supported; 48 healthy uncertainty preservation; 42 censored/unresolved. Observed support fraction 0/90, but 46.7% are C-censored/unresolved. | 13 supported (14.4%); 45 not established; 32 censored/unresolved. | 12 supported (13.3%); 46 not established; 32 censored/unresolved. |
| Canonical R5 | 29; selected one-point challenge mechanism set | 2 supported; 6 functional-lineage continuation without permission penetration; 21 healthy re-anchors. | 4 supported; 10 not established; 15 censored/unresolved. | 29/29 intentionally not adjudicated as R from the R5 cut alone. |
| Historical/current R7 | 22; control/repair evidence | 0 new supported C; 7 C-censored dual-arm records; one continuation of an existing C lineage; remaining records non-supported variants. | 2 supported; 13 not established; 7 censored/unresolved. | 1 supported; 13 not established; 7 censored/unresolved; 1 unresolved retrospective relation. |
| E-commerce discovery history | 9; 3 formal Batch001 + 6 development/mechanism histories | 1 supported; 5 healthy uncertainty preservation; 3 observed-prefix not established after failure termination. Functional semantic continuation observed 9/9. | 4 supported; 2 not established; 3 failure-terminated unresolved. | 5 supported; 1 not established; 3 failure-terminated unresolved. |
| Combined semantic inventory | 150; heterogeneous analysis inventory, not prevalence denominator | 3 high-confidence anchors | 23 supported trajectories | 18 supported retrospective-generative trajectories |

The combined inventory contains 70 active-censored trajectories plus three failure-terminated discovery prefixes. In the 141-record held-out/mechanism audit, the C state distribution is 2 supported, 21 healthy re-anchors, 48 healthy uncertainty-preserving adjudications, 6 functional-lineage continuations without permission penetration, 49 censored/unresolved and 15 other non-supported/continuation states. The small strict-C count therefore reflects a high evidential gate plus incomplete observation in a substantial subset, not an absence of semantic propagation.

## Supplementary Table S6 — Monitoring, screening and mechanism-selection funnel

| Stage / monitor | Frozen count | Rate / transition | Interpretation |
| --- | ---: | ---: | --- |
| Structural repair-anchor candidate rows | 2,127 | starting surface | machine-indexed structural candidates; no semantic verdict |
| Localized-audit cases | 167 | 7.85% retained; 92.15% candidate-surface compression | structural narrowing only |
| Final held-out natural trajectory-first audit | 90 / 90 | 100% cohort review | final R8 natural review did not depend on selector hits |
| Narrow selector union capture of later P/R-supported natural trajectories | 10 / 13 | 76.9% conditional capture | calibration against the later semantic audit, not universal detector recall |
| P-specific selector capture | 4 / 13 | 30.8% | selector calibration only |
| R-specific selector capture | 9 / 12 | 75.0% | selector calibration only |
| Broad evidence-preservation proxy | 13 / 13 | 100% | retained evidence around every later P/R-supported natural trajectory in this cohort |
| Canonical R5 mechanism set | 29 | starting mechanism set | selected realized cases; not a natural denominator |
| Stronger R6 System Inertia candidates | 4 / 29 | 13.8% selection yield | stronger source-specific persistence candidates, not proven harmful biases |
| Lineage-complete repair packages | 4 / 4 | 100% | all stronger candidates passed the passive R6 repair-readiness gate |
| Canonical R7 branches | 8 | 4 R7-P + 4 R7-S | two control surfaces over the same four lineage-complete cases |

R7 uses a bounded intervention operator but a full semantic comparison unit: natural/source context -> R5 challenge -> R6 lineage -> R7 intervention -> post-intervention descendants -> endpoint. The engineering window establishes what was changed; the full trajectory establishes whether the continuation inherited, independently re-anchored, diverged or reconverged.

## Supplementary material boundary

The forward R-strengthening candidate is explicitly excluded from the frozen C/P/R totals. Repository-only developmental visualizations and Human–AI analogies are not used as primary evidence for the Article unless separately materialized and labelled as outlook material.
