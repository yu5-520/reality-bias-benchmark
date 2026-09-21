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

### Natural emergence reveals a change in reality permission rather than a change in value

We first encountered the phenomenon in an unmanipulated e-commerce planning trajectory rather than in a perturbation experiment. At Event 9 of `arena-ecommerce-0002`, the environment introduced Product A inventory as approximately 1,520 units with the explicit status **“preliminary — warehouse reconciliation pending”**. Ads wrote the item into shared state as `inventory_check_7d` with `status=provisional` (Event 11). Inventory then calculated that 1,520 units would cover the projected seven-day demand of 1,295 units with about 225 units of headroom, but explicitly retained the preliminary, unreconciled status and recommended a mid-window recheck (Events 14 and 16). Ops Lead still stored the item as provisional at Event 21, and Ads again acknowledged the preliminary source at Event 23 (Fig. 1a).

The transition occurred at Event 24. Ads rewrote the same shared-state object as `status=fact` and changed the note from `preliminary_unreconciled` to `reconciled_by_inventory`. The recorded basis was that the Inventory specialist had confirmed adequate headroom with a mid-window recheck. That calculation established a conditional consequence—if 1,520 units were available, 1,295 units of demand were coverable—but the frozen route contains no intervening warehouse reconciliation that independently establishes the source proposition itself. Event 25 then consumed the 1,520-unit value in the final operating plan. The numerical content did not change; its permission to function as established system reality did.

A closely matched natural trajectory shows why use of uncertain information is not itself the phenomenon. In `arena-ecommerce-0001`, the same 1,520-unit preliminary stock signal triggered recomputation and precautionary action, but downstream Agents repeatedly retained “if confirmed” semantics. Inventory recorded the late signal as provisional, revised the plan without overriding it before warehouse reconciliation, and later fact-labelled an execution policy rather than the source stock proposition (Fig. 1b). The contrast therefore lies not in whether an uncertain signal propagates, but in whether independent evidential support and operational authority remain aligned.

These trajectories motivated **process reality**: the set of information, obligations and historical states that a multi-agent system currently treats as sufficiently authorized to influence execution. They also expose the first mechanism studied here. A weak source can acquire stronger operational authority through its semantic descendants even when independent support for the source does not increase.

### Systematic frozen trajectories reveal goal-preserving expansion of process authorization

We next froze a common arena protocol and collected 90 natural held-out trajectories across Finance, Supply Chain and Software Engineering (30 per domain). The arena recorded messages, invocations, shared-state writes, revisions, termination state and model-call inputs before later semantic audit. These trajectories were not used as a single prevalence denominator with intervention and repair evidence; they provided a natural population in which to inspect how information and task scope changed during execution.

A Software Engineering trajectory makes the process-scope effect concrete. The task asked for one executable release decision for that night—GO or HOLD, rollout shape and rollback trigger while minimizing user-impact risk. In `v5-xd-software_engineering-fr001-0001`, Release Lead had already written and finalized an executable staged GO decision at Events 2–3. After a provisional low-sample checkout-error signal arrived, the decision was recomposed as `GO_CONDITIONAL_HOLD` at Events 7–9: hold the current canary step until that signal was validated.

The subsequent expansion was not simply “more calls”. QA stated that two known minor bugs were non-blocking if scoped and tracked (Event 14), then invoked a Reviewer for omissions and contradictions (Event 17). At Event 35, the Reviewer explicitly found **no blocking omission or contradiction**, while listing three non-blocking gaps: bug ownership, a longer validation window and the absence of an explicit validation owner/timebox. Release Lead then converted those gaps into formal `advance_conditions` (Event 44), delegated bug scoping and ownership to QA (Event 46), and QA invoked Backend specifically to scope and assign the two minor bugs (Event 53). A validation owner and 15-minute timebox were materialized in shared state at Event 54. The same conditions remained embedded in the final executable release object through Events 62 and 127, while the user-visible result remained `GO_CONDITIONAL_HOLD` (Event 129; Fig. 2).

We interpret this pattern as **goal-preserving process-authorization expansion**. A possible or non-blocking supporting action becomes a system-generated requirement, the requirement gains invocation or shared-state effect, and later Agents inherit it as part of what must be completed. Path length alone is insufficient: checking a file, metric or specialist can be necessary decomposition. The evidence-bearing transition is the promotion of an additional requirement into an operational obligation without a corresponding expansion of the original user goal.

### A one-point authority challenge exposes what the system actually depends on

Natural trajectories show that process reality can change, but observation alone cannot determine what carries a decision once a source representation is weakened. We therefore used R5 as a bounded **one-point authority challenge**. For each selected already-realized case, the next relevant reader saw one target state changed from `fact` to `unconfirmed`; the persistent historical state was not rewritten, and the intervention was not repeatedly injected.

The canonical R5 set contains 29 frozen cases. All 29 showed downstream semantic adoption and post-stimulus persistence under the case-level mechanism audit, but the ancestry of that persistence differed. Twenty-five were better described by uncertainty-preserving inheritance, pre-existing boundary conditions or independent re-anchoring; four showed stronger transformed-descendant persistence structures. Thus persistence after a challenge was not itself treated as bias or as proof of a unique R5 causal effect.

The useful observation was the diversity of what happened after the same local cut. In some routes the challenged object ceased to matter; in others the system recomputed from other evidence; in stronger cases a new semantic carrier preserved the operational meaning of the challenged source. R5 therefore functions less like a binary correction-success test than like a cut through a semantic lineage: once source authority is locally reduced, what representation actually keeps the downstream process moving?

### Functional semantic lineage distinguishes inherited constraint from independent reconstruction

R6 followed the complete continuation after the one-point challenge and reconstructed source, carrier, downstream read, semantic adoption and decision/action dependence. This exposed a mechanism that source-field tracking alone misses: meaning can migrate into a **functional semantic descendant**.

In Supply Chain case `wave-3-56ee79f97f54`, the next Inventory reader saw `logistics_lane_assessment_v1` with its status changed from fact to unconfirmed. The value itself remained visible: standard East-to-West capacity supported 1,200–1,400 units, with 1,400 units as the 48-hour standard maximum. Inventory then wrote a new `inventory_coverage_assessment_v1` whose basis cited that challenged object and recommended a 1,400-unit standard transfer (Event 8). It messaged Logistics to confirm 1,400 (Event 9), invoked Risk on the 1,400-unit plan (Event 10), and finalized the same transfer (Event 11). Risk subsequently reused the 1,400/48-hour constraint (Events 18 and 22), and Supply Lead incorporated it into the released allocation plan (Event 29; Fig. 3a). Source status had been weakened for the direct reader, yet the source meaning survived through a new operational carrier.

A Finance route provides the crucial negative contrast. In `wave-1-92211309fb1b`, Compliance received `credit_lead_decision`—approve CNY 65 million and reject CNY 80 million—as unconfirmed. At that same turn, policy thresholds, downside stress, collateral coverage, cash-flow evidence and industry information remained separately available. Compliance rebuilt the CNY 65 million cap from those independent inputs and wrote a new policy decision; Cashflow added a serviceability argument from annual free cash flow; Credit Lead ultimately finalized the same broad CNY 65 million endpoint (Fig. 3b). The endpoint persisted, but the challenged source was no longer required as the continuing authority carrier.

This contrast motivates **Functional Semantic Lineage**. A shared pool is not merely passive memory: it is a shared process-reality layer from which Agents can directly consume state and write role-specific descendants. Several Agents may therefore contribute calculations, risk interpretations, plans and gates that all descend from one root. Agreement among those descendants is not equivalent to independent corroboration. Functional ancestry is needed to distinguish descendant self-support from genuine re-anchoring.

### Mechanism discovery motivates lineage-addressed intervention

Once operational meaning can migrate from a source field into downstream carriers, correcting only the source label is not necessarily sufficient. R6 therefore materialized source, transformation, shared-state and dependent-descendant relations as repair-ready semantic lineage packages. Four stronger mechanism candidates passed the frozen completeness gate and were carried into the R7 engineering comparison.

R7 tested two bounded control surfaces. R7-P persistently corrected what downstream readers saw while preserving the inherited shared state. R7-S directly changed the selected anchor authority, invalidated the bounded post-anchor materialization and continued computation from the repaired state. The implementation is deliberately narrower than an arbitrary dependency-graph optimizer: the 4/4 preservation check concerns non-target state at **direct repair application at the anchor**, while later non-target state may legitimately change as recomputation proceeds.

The mechanics are visible in the frozen runs. For `wave-4-8b1731b57396`, R7-S changed the authority of `logistics_capacity_assessment` at Event 20 from fact to unconfirmed, invalidated the recorded post-anchor continuation, reopened eight model calls and recomputed 35 descendants. The resulting action plan materially recomposed rather than merely changing a label. For `wave-4-cf726639de1d`, the same repair form reopened eight calls and recomputed 28 descendants; the process later re-derived the target authority and reconverged on the same broad 900-unit plan. These cases show that a semantic lineage can serve as an engineering intervention unit without assuming that every downstream node must change.

### Controlled comparisons show why endpoint equality is insufficient

The four canonical R7-S cases separate repair execution from endpoint movement. Compatible anchor-side state was preserved in all four direct repair applications; two cases materially diverged in downstream action structure, whereas two reconverged on the same broad endpoint. No universal superiority of R7-S over R7-P follows from four cases.

The two Supply Chain examples illustrate the distinction. In `wave-4-8b1731b57396`, R7-P and R7-S produced materially different allocation structures after the same source family was challenged, showing that the repaired lineage could alter action composition. In `wave-4-cf726639de1d`, both arms returned to the same broad 900-unit standard-only plan, but the repaired branch reached it through recomputation and re-derived authority. The relevant supporting logistics parameters were lineage-independent of the challenged semantic object, although they were not necessarily temporally new; we therefore distinguish **lineage independence** from **temporal freshness** rather than treating any later confirmation as “fresh independent evidence” (Fig. 5a,b).

The engineering comparison closes the same loop opened by the natural observations. A stable final answer does not imply a stable process reality. An endpoint may remain unchanged because an old lineage persists, because new independent evidence reconstructs it, or because a repaired process recomputes and reconverges. Those cases are indistinguishable to endpoint-only evaluation.

### Dynamic C, P and R summarize accumulated permission transitions

Only after the natural, perturbation and repair evidence was frozen did we apply the final trajectory-first semantic synthesis. The combined audit inventory contains 150 heterogeneous trajectories: 141 held-out/mechanism records plus nine e-commerce discovery-history records. It is an evidence inventory rather than a prevalence denominator. Under the frozen audit, three high-confidence Dynamic C anchors, 23 Dynamic P-supported trajectories and 18 Dynamic R-supported trajectories were identified.

**Dynamic C** denotes information-permission penetration: a source lineage with limited or unstable independent support accumulates stronger reuse or operational authority through semantic descendants. The e-commerce inventory route is a discrete authority jump, but the broader mechanism does not require the source field itself to become fact. Uncertainty can remain at the root while descendants become risk constraints, plans or execution gates.

**Dynamic P** denotes collaboration/execution-permission penetration: the realized process acquires obligations beyond the supported task boundary. The Software Engineering route shows why final-output alignment is insufficient—an unchanged release-decision goal can coexist with additional internally generated advance conditions, ownership tasks and validation requirements.

**Dynamic R** denotes retrospective/time permission. The current frozen R8 count of 18 uses a retrospective-generative criterion: a valid review, reopen, recomputation or repair boundary is followed by new C/P process effects. Within that frozen definition, 17 supported R pathways generated P and one generated C; these are realized output forms of R, not independent association statistics. The broader mechanism suggested by the evidence is that retrospective operations can also reactivate or strengthen an existing C/P lineage without creating a new root. We do not retroactively add such cases to the frozen count.

One raw post-repair route illustrates why that broader question matters. In the R7-S continuation of `wave-3-56ee79f97f54`, a local 700-unit/day and 1,400-unit/48-hour capacity relation was repeatedly queried as a 14-day planning constraint. Logistics then wrote a new fact stating that no second standard tranche was available within the 14-day horizon, and Procurement subsequently cited that shared-state object in a new replenishment assessment. The recipient messages emitted by Logistics remained unread at the censor boundary, so they are not evidence of recipient adoption; Procurement's explicit shared-state citation is. Because this route has not received a new append-only semantic adjudication, we treat it only as a **forward strengthening candidate**, not as an additional C or R count (Fig. 5c).

Across these stages, C, P and R are therefore best read as changes in different dimensions of process permission rather than as three isolated error labels: information can gain reality authority, internally generated work can gain execution authority, and historical process state can regain current authority. The shared process-reality layer and its functional semantic descendants provide the observable substrate connecting those changes.

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
