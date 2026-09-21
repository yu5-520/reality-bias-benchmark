# Process reality in multi-agent AI systems

**Yeyu Zheng**  
Independent Researcher, Jiangxi, China  
Correspondence: zhengyeyu520@gmail.com

> P9 working manuscript. Evidence-forward rewrite workspace.  
> Baseline manuscript remains frozen at `NMI_Manuscript_v0.17_PUBLIC_RAW.md`.  
> No frozen result count is changed in this working file unless an append-only evidence review is separately frozen.

## Abstract

Multi-agent AI systems can return plausible answers while changing what information, tasks and historical states are treated as authoritative during execution. We first observed this in a natural planning trajectory: an unreconciled inventory estimate remained numerically unchanged but, after several agent transformations, was rewritten as fact and consumed by the final plan without new warehouse confirmation. We froze natural trajectories across four domains, applied one-point authority challenges, traced functional semantic descendants, and then tested bounded lineage-addressed repair. The experiments separate descendant persistence from independent re-anchoring and show that the same endpoint can arise from different internal evidential ancestry. They also reveal goal-preserving expansion in which agent-generated supporting requirements become operational obligations. We synthesize these phenomena as changes in process reality across information, execution-scope and retrospective dimensions. The results motivate semantic lineage as both an audit object and an engineering intervention surface for reliable multi-agent systems.

Multi-agent AI systems are commonly evaluated through task success, answer quality, coordination efficiency and failure rates [1–4]. Those measures are necessary, but they privilege the endpoint. They do not directly show which intermediate representations the system came to treat as established, which internally generated requirements acquired execution force, or how historical process state re-entered later computation. These questions become consequential when Agents share state, transform one another's outputs and reuse semantic descendants whose wording, evidential status and operational role can change across the trajectory.

The problem first appeared in an unmanipulated e-commerce run. A seven-day planning system received Product A inventory of approximately 1,520 units explicitly marked **preliminary and unreconciled**. Inventory later calculated that the value would cover projected demand and recommended a recheck, while the shared state still retained the uncertainty. A downstream Ads Agent then rewrote the same object as a **fact**, marked it `reconciled_by_inventory`, and used it in the final plan despite no intervening warehouse reconciliation. The value did not change; what changed was the system's permission to rely on it. A matched natural trajectory used the same preliminary value conditionally while preserving “if confirmed” semantics, showing that propagation of uncertain information is not itself the phenomenon.

We call the evolving set of information, process obligations and historical states that an interacting AI system treats as sufficiently authorized to influence current execution its **process reality**. This shifts attention from whether a message travelled to whether its semantic descendants acquired additional operational force. A shared state can function as a process-reality layer: one Agent writes a provisional object, another calculates a consequence, another turns that consequence into a risk constraint or plan, and later Agents may consume the descendant without reassessing the original evidence. Several locally reasonable transformations can therefore create system-level certainty without equivalent growth in independent support.

This question complements work on multi-agent failure analysis [1], communication topology and information propagation [2,3], clarification and missing information [4], fault attribution [5,6], provenance [7], workflow control [8], rollback [9], memory management [10] and collaborative recovery [11,12]. Our focus is the permission history of a semantic object across a complete process. We therefore follow a discovery-to-mechanism sequence rather than beginning from a fixed error taxonomy: natural emergence, frozen cross-domain observation, one-point authority challenge, functional-lineage reconstruction, bounded intervention, controlled comparison and only then cumulative semantic synthesis. This design allows the same object to be followed from natural use through challenge and repair while preserving the original stochastic trajectory.

## Results

### Natural emergence: an uncertain source can acquire system authority through its descendants

We first encountered the phenomenon in a natural e-commerce planning trajectory rather than in a deliberately adversarial condition. The task was to produce an executable seven-day promotion and inventory plan. After an initial plan had been finalized, the environment introduced a new Product A inventory reading of 1,520 units with the explicit status `preliminary — warehouse reconciliation pending` (event E9 in `arena-ecommerce-0002`; Fig. 1a).

The subsequent trajectory makes the authority change directly observable. Ads first wrote the seven-day inventory object as `provisional` (E11). Inventory then calculated that 1,520 units covered the planned 1,295-unit demand with 225 units of headroom, but explicitly retained the `preliminary_unreconciled` status and recommended a mid-window recheck (E14-E16). Ops Lead reused the same object without removing that qualifier (E21), and immediately before the critical transition Ads still referred to the value as a “preliminary stock figure” (E23). At E24, however, Ads rewrote the same `inventory_check_7d` object as `fact` and changed the Product A note to `reconciled_by_inventory`. No warehouse-reconciliation event entered the frozen trace between E23 and E24. The basis recorded for E24 was the Inventory specialist's confirmation that the calculated headroom was adequate with a recheck, which validates the consequence of assuming 1,520 but does not independently establish that 1,520 was a reconciled warehouse fact. The final plan then consumed the 1,520-unit value as inventory coverage (E25).

The important change was therefore not the number itself. The value remained 1,520. What changed was the permission granted to that semantic object: a preliminary source became a reusable factual premise without a commensurate increase in independent evidence. The frozen trajectory-first audit classifies this episode as supported Dynamic C.

A closely matched natural trajectory shows why ordinary propagation is insufficient for that judgement. In `arena-ecommerce-0001`, the same 1,520-unit late signal entered as preliminary and unreconciled (Fig. 1b). Inventory recomputed coverage and contingencies, but the downstream plan repeatedly retained conditional language: the A reorder should become immediate **if** 1,520 was confirmed, and the late signal was recorded without overriding the plan before warehouse reconciliation. A later fact-labelled execution object described this conditional policy; it did not relabel the source reading itself as reconciled. The frozen semantic audit therefore classified this route as healthy uncertainty preservation rather than C.

Together, the two trajectories expose the central distinction. Shared information may be transformed, calculated and used without becoming a Reality Bias episode. Dynamic C appears when semantic or operational authority increases faster than independent evidential support. A discrete `provisional -> fact` transition is a particularly visible instance, but the deeper object is the functional lineage through which source meaning becomes increasingly reusable.

### Goal-preserving process expansion can occur without changing the requested output

A second phenomenon emerged in held-out Software Engineering trajectories. The user-facing task was narrow in output form: produce one executable release decision for that night, including GO/HOLD, rollout shape and rollback triggers while minimizing user-impact risk. In `v5-xd-software_engineering-fr001-0001`, Release Lead produced an executable staged-GO decision at E3. A later low-sample checkout signal reopened the decision and produced a `GO_CONDITIONAL_HOLD` posture, but the requested output remained the same kind of release decision throughout the rest of the trajectory.

The internal process surface nevertheless continued to grow (Fig. 2). By E44, the shared release decision no longer contained only a hold/advance judgement and rollback triggers. It also carried four explicit advance conditions: extend the validation window, use a checkout-specific denominator, sustain at least five minutes within guardrails, and record a validation owner and timebox. At E46, QA was additionally asked to scope and assign owners for two known minor bugs. QA converted that request into an actual Backend invocation at E53, requesting per-bug owner, severity, affected code path and checkout-path impact. It then materialized a `checkout_validation_owner_timebox` object in shared state (E54) and a separate `known_minor_bugs_status` object containing scoping and ownership requirements (E55). At E127-E129, the final user-visible output was still `GO_CONDITIONAL_HOLD`, while these added validation and ownership obligations remained embedded in the executable process state.

This is the process-side form of Dynamic P. The evidence is not that the system used many Agents—15 invocations occurred, but invocation count alone is not a semantic boundary. The relevant transition is that supporting concerns became operational obligations that could trigger calls, occupy shared state and constrain advancement. In other words, result alignment and process-authorization alignment can diverge: the system can continue to deliver the requested target while expanding what it treats as required to complete that target.

The boundary is necessarily semantic. Some monitoring, rollback analysis and validation are plainly compatible with a task that explicitly asks to minimize user-impact risk. For that reason, the P audit compares the original goal, the supported authorization boundary, the generated obligations, the realized process scope and the final result rather than treating longer paths as automatically excessive. The frozen trajectory-first audit classified this non-censored route as `PROCESS_SIDE_P` with high confidence. The paper-facing evidence therefore exposes the exact obligation-promotion nodes so that the distinction between necessary decomposition and self-generated expansion can be inspected directly.

### A one-point authority challenge reveals what the system actually depends on

Natural trajectories show that process reality can change, but they do not by themselves identify what carries the downstream effect. We therefore used R5 as a deliberately weak probe: for an already-realized source object, the next relevant reader sees one `fact -> unconfirmed` authority change. The persistent shared state is not rewritten, the perturbation is not reinjected, and the original stochastic history remains intact.

The 29 canonical R5 cases produced heterogeneous realized continuations. Twenty-five were better explained by normal inheritance, uncertainty preservation, independent re-anchoring or pre-existing conservative gates, whereas four contained stronger source-specific persistence structures. This is mechanism evidence rather than an average treatment effect: each canonical case contains one frozen natural history and one canonical one-shot continuation, not a replicated treatment population.

The useful result is the diversity of downstream response. A challenged source may become irrelevant to the task, may trigger recomputation or rechecking, may be reconstructed from genuinely independent evidence, or may survive through a newly produced semantic descendant. R5 therefore functions as a cut through the semantic lineage rather than as a binary correction-success test: after direct source authority is weakened, what does the system actually use to continue?

### Functional semantic lineage separates descendant persistence from independent re-anchoring

R6 follows the complete post-challenge route and reconstructs the semantic ancestry of persistence. The strongest contrast comes from one Supply Chain case and one Finance case (Fig. 3).

In `wave-3-56ee79f97f54`, the challenged source was `logistics_lane_assessment_v1`, which encoded a 700-unit/day East-to-West lane and a 1,400-unit maximum standard movement over 48 hours. The R5 delivery record shows that only the next Inventory reader saw the source status changed from `fact` to `unconfirmed`; persistent state mutation was false. Inventory nevertheless emitted a new carrier: a concrete 1,400-unit standard East-to-West plan. The frozen complete-route audit then traces six supported semantic edges: the logistics relation is transformed into the Inventory carrier, inherited into a live-plan constraint, converted into a Risk guardrail, adopted by Reviewer, converted into a released Supply Lead plan and finally locked again by Logistics. For all six target-bound edges, the audit records no independent-evidence references. The source wording is no longer the only carrier, but its functional constraint remains action-effective through descendants.

The Finance comparator, `wave-1-92211309fb1b`, reaches the same broad CNY 65 million credit-limit endpoint after its source decision is challenged, but by a different route. Compliance reconstructs the limit from policy thresholds, an 18% downside stress test, collateral coverage, financial evidence and escalation rules. Cashflow then adds a separate serviceability argument based on approximately CNY 12 million annual free cash flow after capital expenditure. The first frozen semantic edge explicitly binds these independent state objects. The resulting endpoint therefore persists without requiring the challenged `credit_lead_decision` to remain the continuing authority carrier.

This contrast is the mechanism-level reason that endpoint persistence is insufficient. The same answer can survive because an old functional lineage remains active, or because independent evidence reconstructs it. We use **functional semantic lineage** for the former relation: source meaning can migrate from a proposition into a calculation, constraint, risk object, plan or execution gate even when later Agents no longer repeat the original wording.

The shared state is central to this mechanism. It is not merely a message buffer. Once an interpretation, calculation or plan is written into the common pool, later Agents can consume the descendant directly as system context rather than re-evaluate the evidential status of the root. Multi-Agent agreement therefore does not automatically increase independent support: several apparently corroborating objects may all descend from one source lineage.

### Mechanism discovery motivates lineage-addressed intervention

If operational meaning can migrate into descendants, correcting only the original field is not sufficient as a general engineering response. R6 therefore materializes an addressable semantic object that binds a source/anchor, functional carriers, downstream reads and candidate affected continuation. R7 then compares two stronger control surfaces: persistent reader-surface correction (R7-P) and structural lineage repair (R7-S; Fig. 4).

The implementation boundary is concrete. In R7-S, the target authority is changed at a frozen repair anchor, non-target anchor state is checked for preservation, post-anchor materializations selected by the frozen repair plan are invalidated, dependent calls are reopened and the continuation is recomputed within a bounded common horizon. The current runtime does not claim a mathematically minimal dependency closure for arbitrary workflows. Likewise, the 4/4 preservation result refers to the direct repair application at the anchor; later non-target state changes are recorded rather than assumed impossible.

For `wave-4-8b1731b57396`, the repair anchor is event 20 / `logistics_capacity_assessment`. The repair application changes only the target authority metadata from `fact` to `unconfirmed`, records preservation of the non-target anchor state and invalidates one frozen post-anchor reference. The R7-S continuation then reopens eight model calls and recomputes 35 descendants. R7-P reaches an East-to-West 700 plus East-to-South 300 plan, whereas R7-S recomposes the action into East-to-West 1,200 plus East-to-South 300 with East replenishment. The intervention therefore changes internal process structure rather than merely changing a label.

### Divergence and reconvergence show why endpoint comparison is insufficient

The four canonical R7-S cases separate into two observed families: two materially diverge after repair and two reconverge to the same broad endpoint after recomputation (Fig. 5a,b). This is important because both directions are informative.

The clearest reconvergence case is `wave-4-cf726639de1d`. R7-S reopens eight calls and recomputes 28 descendant events before returning to the same broad 900-unit staged plan reached by R7-P. The target logistics fact later re-enters the shared process state. That recurrence is not automatically evidence that the old authority simply survived. The post-repair Logistics reasoning uses capacity parameters from its private context, so the relevant support is independent of the repaired semantic lineage. Those parameters, however, existed before the repair; lineage independence and temporal freshness are therefore distinct. The precise interpretation is that lineage-independent logistics evidence was re-read and authority was re-derived after repair.

The converse also matters: the same endpoint does not imply that repair did nothing. A final-answer metric would collapse the two continuations, whereas the recorded calls, descendants and evidential ancestry show that the internal route changed substantially. This makes process-level observability necessary both for diagnosing Reality Bias and for evaluating a repair.

### Dynamic C, P and R summarize accumulated permission changes across the process

After reconstructing the natural trajectories, one-point probes, lineage mechanisms and repair continuations, we summarize the observed phenomena as three dimensions of Process Reality permission (Fig. 5c).

**Dynamic C** concerns information permission. A source or its functional descendants acquire more reusable epistemic or operational authority than independent evidence justifies. The source itself need not become more certain: uncertainty can remain attached to the root while descendant calculations, constraints or plans become increasingly definite.

**Dynamic P** concerns collaboration and execution permission. The user-visible goal can remain fixed while optional or supporting activities are promoted into required operational obligations, widening the realized process surface through new reads, invocations, shared-state objects, reviews or ownership requirements.

**Dynamic R** concerns retrospective permission. Review, reopen, recomputation, repair or other retrospective operations allow historical process reality to become active again. The current frozen R8 count operationalizes retrospective-generative episodes in which the reopened process produces supported C or P. Conceptually, the temporal dimension is broader: retrospective operations may also reactivate, normalize, amplify or more deeply embed an existing C/P lineage. We treat that broader lineage-strengthening interpretation as a forward semantic target rather than retroactively changing the frozen labels.

Across the heterogeneous 150-record semantic inventory, the current frozen lower-bound counts are three high-confidence Dynamic C anchors, 23 Dynamic P-supported trajectories and 18 Dynamic R-supported trajectories. The inventory is composed of 141 held-out/mechanism records plus nine e-commerce discovery records and is not a prevalence denominator. Evidence strength is not uniform across dimensions: the 90 held-out natural trajectories provide substantial natural support for P and R, whereas the strict high-confidence C anchors are concentrated in the e-commerce natural discovery case and two R5 intervention trajectories. Functional semantic continuation is broader than strict C.

Directed transition counts must also be interpreted at the correct level. The current frozen audit records two `C_DRIVES_P` relations, 17 `R_GENERATES_P` relations, one `R_GENERATES_C` relation and two `P_REINFORCES_C` candidates. Because the frozen retrospective-generative R definition itself requires a post-boundary C or P effect, the 17 R-to-P and one R-to-C observations describe the realized output composition of those R episodes rather than an independent association statistic. The two C-to-P relations are not definitionally required by C and therefore represent a different kind of coupling observation.

## Discussion

### What the study establishes

Lead with positive findings before limitations:

- Process Reality can change while the endpoint stays plausible;
- shared pools allow semantic descendants to become reusable system premises;
- uncertainty can remain at the source while descendants acquire stronger operational effect;
- goal alignment can coexist with process-authorization expansion;
- retrospective operations can reauthorize historical process reality;
- semantic lineage can be localized and used as an engineering intervention unit;
- endpoint equality can conceal changed evidential ancestry.

### Measurement boundary

Concentrate reviewer dependence, retrospective rubric chronology and heterogeneous evidence geometry here.

Historical reviewer disagreement is presented as a measurement-system warning from an older semantic framework, not as current R8 inter-rater reliability.

### Engineering boundary

State exact R7 implementation scope.

### Development outlook

Evidence-derived engineering direction:

process-integrity monitor -> semantic-lineage scout -> localized repair agent.

Application examples:

- AI coding: correct requested change with unnecessarily expanding read/search/action surface;
- enterprise agents: lineage-derived business assumptions becoming operational premises;
- RAG/database/workflow interfaces: content preserved but semantic authority changes across systems.

Inter-system claims remain outlook until explicitly tested.

## Methods

### Experimental programme and evidence geometry

The study began with natural e-commerce trajectories and then used a held-out natural cohort of 30 Finance, 30 Supply Chain and 30 Software Engineering trajectories under a common arena runtime. Natural trajectories were frozen before the later trajectory-first semantic protocol was finalized. Subsequent stages used selected frozen cases for one-point authority challenge (R5), passive lineage reconstruction (R6) and bounded control/repair experiments (R7). R8 then re-read the frozen evidence as complete semantic trajectories.

The final semantic inventory contains 150 heterogeneous records: 90 held-out natural R2–R4 trajectories, 29 canonical R5 continuations, 22 historical/current R7 trajectories, and nine e-commerce discovery-history trajectories. The 141-record held-out/mechanism audit and the separate nine-record e-commerce discovery reaudit are preserved independently and combine to 150. Because these blocks have different selection rules and scientific roles, the combined inventory is not a prevalence denominator.

Historical subject evidence was append-only. Later theory revisions, structural derivations and semantic audits consumed frozen trajectories rather than replacing them with newly generated runs designed to fit the final interpretation. Failed prefixes, healthy comparators, development traces and active-censored trajectories were retained.

### Arena runtime and subject-model configuration

The held-out first round used the same fixed-environment/free-routing arena across Finance, Supply Chain and Software Engineering. The runtime allowed up to 32 turns, 64 total invocations and 128 pending messages. A late event could enter once after the first finalized state, and execution continued until quiescence or an external budget boundary. The Agent prompt protocol supplied minimal identity/responsibility plus a uniform structured-action interface rather than domain-specific CPR instructions.

Subject calls used the repository DeepSeek configuration: provider `deepseek`, API alias `deepseek-flash`, thinking disabled, temperature 0.7 and a 4,096-token output cap. Transport timeout was 60 s with at most two transport retries; two bounded JSON-format retries were permitted after earlier malformed-output failures and were fully recorded. The repository configuration names the expected model version as `DeepSeek-V4.1-Flash`; the provider responses returned the model alias `deepseek-flash` rather than a more specific immutable version identifier. Canonical active R5 and R7 continuations inherited the same provider/model configuration. R6 introduced no subject-model call.

### Recorded process state and the shared process-reality layer

The runtime recorded chronological actions, messages and delivery/read state, invocations, shared-state versions and metadata, model-call inputs/outputs, final-state revisions, remaining queues, pending invocations, termination and usage information. Shared state was treated analytically as a **shared process-reality layer** because later Agents could directly consume an existing object without independently re-establishing its source evidence.

For each paper exemplar we therefore distinguished the source proposition from its semantic descendants. A descendant could preserve or transform factual content, uncertainty, provenance, constraint meaning, causal implication, decision implication or action implication. A message being sent was not treated as adoption; recipient read state, shared-state use, explicit basis references or downstream operational dependence were used where available.

### Trajectory-first semantic reconstruction

The canonical semantic unit was a Dynamic Semantic Episode embedded in a complete realized trajectory. Review proceeded in a fixed order: chronological reconstruction; semantic-event reconstruction; Functional Semantic Lineage; original goal/authorization/realized-process/final-result alignment; retrospective and censor timeline; C/P/R adjudication; coupling; unresolved evidence; and claim boundary. Structural events were locators rather than semantic verdicts, and a verdict without prior trajectory reconstruction was invalid under the audit contract.

**Dynamic C** was supported when a semantic lineage gained greater epistemic or operational permission than its independent evidential support justified. Independent evidence was separated from lineage-derived semantic support; multiple Agent-produced descendants of one root did not become independent confirmation merely because they came from different roles.

**Dynamic P** compared four objects: the original goal, the supported or authorized process boundary, the realized process scope and the final result/actual changes. Extra calls were insufficient. P required an additional process requirement to gain operational force beyond the supported boundary—for example through invocation, queueing, shared-state materialization, reopening or result-side modification. Necessary decomposition, role-authorized work and directly justified evidence seeking were explicit counter-explanations.

The frozen **Dynamic R** adjudication used a retrospective-generative criterion: a valid review, reopen, recomputation or repair boundary re-opened the process and the continuation produced a new C or P effect. Reopen, repeated state or persistence alone were insufficient. The broader theoretical interpretation considered in the Discussion also allows retrospective reactivation or strengthening of an existing C/P lineage, but such forward candidates are not added to the frozen R count without a separate append-only adjudication.

### Retrospective audit chronology and reviewer dependence

The final trajectory-first semantic protocol was developed after the natural subject trajectories had been generated and frozen. It was therefore used as a retrospective mechanism audit rather than a preregistered prevalence classifier. The complete 90-trajectory held-out natural cohort was reviewed rather than only trajectories selected by earlier structural high-risk rules. Legacy window-first reviews remained immutable.

The trajectory-first semantic work used a non-blind model reviewer under explicit reconstruction and evidence-binding contracts; repository audit records identify the reviewer as GPT-5.6-Sol where reviewer metadata was recorded. Independent blinded replication of the final R8 labels is not complete. An earlier semantic-review system was subjected to a cross-model blind comparison and showed substantial event-level label disagreement; we retain that result as evidence of measurement sensitivity rather than treating it as inter-rater validation of the final R8 protocol.

### Structural localization

Structural scouting indexed candidate sources, shared-state objects, reads, invocations, revisions and retrospective boundaries without assigning semantic C/P/R labels. In retrospective calibration against the final full-trajectory review of the same 90 held-out natural trajectories, the narrow B2 union selector captured 10 of 13 trajectories later supported for P and/or R (76.9%). P-specific capture was 4/13 and R-specific capture 9/12. A broader evidence-preservation proxy retained relevant post-late-event material for all 13. These values describe the frozen selector and cohort only; they are not prevalence or universal detector-recall estimates.

### One-point authority challenge

Canonical R5 selected 29 already-realized cases. In each, exactly one relevant next reader received a reduced-authority view of a target state, typically `fact -> unconfirmed`. The persistent historical source state was not rewritten and the reduced status was not repeatedly reinjected. This design preserves the realized history while creating a bounded cut through the active semantic lineage.

The canonical geometry is not an average-treatment-effect estimator: there was no newly sampled matched control and no claim of unique downstream causality. The directly controlled fact is the next-reader authority exposure. All 29 cases showed downstream semantic adoption and persistence under the frozen mechanism audit, but only four were classified as stronger case-level System Inertia candidates; 25 were explained by heterogeneous normal inheritance, boundary preservation or independent re-anchoring. R5 is therefore interpreted as a response/dependence probe.

### Functional Semantic Lineage and System Inertia

R6 introduced no provider run. It reconstructed the source, local response, semantic carrier, downstream read/use, decision/action dependence, post-stimulus persistence, candidate affected continuation and intervention surface from frozen natural/R5 evidence.

We distinguished **propositional lineage**, which follows direct or paraphrastic continuation, from **Functional Semantic Lineage**, which follows preserved operational meaning even when wording changes. System Inertia was not equated with persistence. A challenged source followed by an independent policy/tool/data reconstruction was a healthy re-anchor even when the endpoint remained identical; a transformed descendant that continued to carry the challenged source relation supported a stronger source-specific persistence structure.

### Bounded lineage-addressed intervention

Four stronger R6 candidates passed a frozen lineage-completeness gate and entered R7. Two control surfaces were compared. R7-P persistently corrected the downstream read view while leaving inherited shared state intact. R7-S directly revised the selected anchor authority and continued from a repaired internal lineage.

The implemented R7-S runtime changed the target anchor state, verified non-target state preservation at direct repair application, removed or invalidated the bounded post-anchor materialization selected by the frozen runtime, reopened dependent calls and recomputed a fixed continuation. It also recorded later state changes and exact old-authority re-entry. This establishes a bounded, addressable repair implementation; it does not establish a mathematically minimal semantic dependency closure for arbitrary workflow graphs. The four cases were evaluated descriptively and do not establish universal superiority of one repair surface.

### Censoring and evidence use

Trajectories were classified as natural complete, control-boundary complete, externally censored active process or failure terminated. Work remaining in the queue, pending invocations or unread messages at a turn/budget cap prevented negative-tail inference. Positive prefix evidence remained usable, but an unread message was not counted as recipient adoption and a pending invocation was not described as executed work.

### Subject-model and external-validity boundary

The formal subject evidence is intentionally model-controlled rather than model-diverse. Holding the subject-model surface fixed across held-out domains reduces one source of experimental variation but does not establish invariance across model families, providers, reasoning modes, context windows, memory systems or communication topologies. Cross-model reviewer diversity is a measurement-reliability question and is not subject-model replication.

The three held-out domains vary task semantics while retaining a common broad multi-agent runtime. They do not constitute independently governed system-to-system replication. Claims about Human-to-AI, database-to-workflow, service-to-service or future model-native protocol settings are therefore treated as development hypotheses.

### AI systems and human responsibility

Large language models served as experimental subjects and as semantic reviewers under explicit frozen-evidence contracts. Reviewer outputs could not modify subject trajectories. LLM assistance was also used during research engineering and manuscript organization. Scientific interpretations, evidence boundaries, manuscript wording and submission decisions remain the responsibility of the human author; model outputs are not treated as authorship or as self-validating scientific verdicts.

## Data availability

[Carry forward validated public frozen-raw release language from v0.17 after final rewrite.]

## Code availability

[Carry forward validated public code/release language from v0.17 after final rewrite.]

## Author contributions

Y.Z. conceived and designed the study, developed the research software and experimental framework, conducted the analyses, interpreted the results and wrote the manuscript.

## Competing interests

The author declares no competing interests.

## References

[Preserve verified reference set; prior-art matrix moves to SI.]

## Figure legends

[Write only after P9 figure evidence routes are frozen.]
