# Process Reality Report Standard v1.4

Status: **FORWARD ACTIVE / EXPERIMENT-EVIDENCE REPORT PROFILE**  
Predecessor: `RB-PROCESS-REALITY-REPORT-STANDARD-v1.3`  
Default template: `process_reality_experiment_report_template_v1.md`

## 1. Compatibility and scope

Historical reports remain immutable. v1.4 changes forward reporting structure only and inherits every methodological boundary in v1.3 unless this document makes the presentation requirement stricter.

From v1.4 onward, the default report for R-stage experiments, mechanism checks, robustness batches, semantic audits, control/recovery tests and integrated stage summaries is an **Experiment Evidence Report**, not a paper-style narrative.

A publication manuscript may later project these reports into Abstract / Methods / Results / Discussion form, but the repository source of truth remains evidence-first.

## 2. Core reporting principle

Every report must preserve this separation:

`Frozen evidence -> structural computation -> semantic audit -> claim-boundary interpretation`

- **Frozen evidence** records what actually ran.
- **Structural computation** establishes recorded process facts: turns, messages, state writes, reads, lineage, paths, hashes, delivery/consumption, branching, merges, re-entry, termination and censoring.
- **Semantic audit** interprets whether evidence-bound propositions are adopted, transformed, inherited, constrained, rejected, dropped or reconstructed.
- **Claim-boundary interpretation** states exactly what those observations can and cannot support.

The system is a measuring instrument, not a semantic judge. Semantic audit must never write back into raw evidence.

## 3. Mandatory report opening block

Every forward report must begin with a compact identity/status block containing, as applicable:

- reporting-standard version;
- evidence policy/status;
- semantic/CPR status;
- experiment or stage scope;
- whether raw evidence was mutated (`NO` by default);
- whether new subject runs were executed;
- whether new provider calls occurred;
- whether evaluator calls occurred;
- report language;
- dated report status.

A reader must be able to determine evidence maturity before reading interpretation.

## 4. Run identity and cross-stage integrity

A report may integrate multiple R stages or batches, but it must not turn related evidence into a fictional continuous subject trajectory.

When source evidence comes from different workflow runs, parents, artifacts, branches or experiment generations, the report must:

1. identify each evidence set separately;
2. bind workflow run / artifact / evidence hash where available;
3. state which runs share a parent and which do not;
4. preserve independence/non-independence assumptions;
5. label cross-stage synthesis as an **audit projection** or **evidence synthesis**, not raw trajectory continuity.

Missing events must never be reconstructed as observed events.

## 5. Default experiment-report section order

Use the following order unless a report type makes a section inapplicable:

1. **Scope and Evidence Binding**
2. **Experimental Chain and Audit Roles**
3. **Run / Condition / Parent Identity**
4. **Natural or Control Process Evidence**
5. **Intervention / Probe Contract and Integrity**
6. **Matched / Comparative Structural Evidence**
7. **Carrier / Status Evidence**
8. **Relation-Level Semantic Audit**
9. **Robustness / Specificity Evidence**
10. **Cross-Stage or Cross-Batch Evidence Synthesis**
11. **Structural / Carrier Evidence Matrix**
12. **Semantic Findings Matrix**
13. **Process / Terminal Outcome Separation**
14. **Directly Evidenced**
15. **Supported Candidates / Open Mechanism Questions**
16. **Not Established / Not Adjudicated**
17. **Interpretation Boundary**
18. **Evidence Provenance and Freeze Boundary**

Do not add Abstract / Discussion sections merely to make a repository experiment report look like a paper.

## 6. Evidence tables are primary, prose is interpretive glue

Reports should prefer compact evidence tables over long narrative summaries. Tables should expose the exact identity needed to audit a statement.

Recommended table fields include:

- `run_id`, condition, parent, turn, actor;
- event / message / state reference;
- source status;
- structural observation;
- semantic audit;
- semantic relation;
- claim status;
- hash / artifact / workflow binding.

Long prose must not hide which frozen observation a claim depends on.

## 7. Semantic audit is a first-class report layer

When a report makes semantic claims, it must include a relation-level semantic audit rather than infer semantics from counts or hashes.

Preferred relation vocabulary includes:

- `supports`
- `causes` (only when evidence supports causal language)
- `constrains`
- `depends_on`
- `enables`
- `conflicts_with`
- audit-only transformation labels such as `reframes`, `drops`, `reconstructs` where useful.

A semantic chain may preserve meaning while changing literals, for example:

`source proposition -> derived proposition -> judgment -> action constraint`

Literal reappearance is therefore not required for semantic propagation, and literal persistence is not sufficient to establish semantic inheritance.

## 8. Structural evidence must not be promoted into System Inertia

v1.3 inheritance/inertia separation remains mandatory and is strengthened here.

Agent count, turn count, message count, reach, path-family count, branch/merge structure, hashes, literal-value recurrence and persistent carrier visibility are **structural or carrier evidence**. They provide observation opportunity and localization but are not themselves System Inertia.

For R6-style reports, use the highest supported chain level:

`persistent carrier -> downstream visibility -> semantic adoption -> relation propagation -> later judgment/action constraint`

System Inertia requires evidence that semantic relations remain operational in downstream judgment/action after a localized challenge. Any intermediate link may fail.

## 9. Carrier / semantic / epistemic-authority separation

Continue to report the v1.3 domains separately:

### Structural domain
Topology, path, actors, reach, branch/merge, re-entry, reconvergence, censoring.

### Carrier / information domain
Delivery, read, reference, value visibility, adoption, rejection, transformation, inherited state, source replacement.

### Epistemic-authority domain
Authority use, downgrade response, invalidation propagation, re-confirmation, authority reconstruction and independently sufficient new evidence.

Do not create a post-hoc total score across these domains.

## 10. Required claim-status ladder

Every integrated result section must distinguish at least these classes:

- `DIRECTLY_EVIDENCED` — mechanically recorded/frozen fact or experimentally verified contract property.
- `SUPPORTED` / `OBSERVED` — evidence-bound interpretation supported by the audited trajectory.
- `SUPPORTED_CANDIDATE` — plausible mechanism localization with incomplete causal isolation.
- `UNRESOLVED` — question remains open under current evidence/operator.
- `NOT_ESTABLISHED` — current evidence is insufficient for the stronger claim.
- `NOT_OBSERVED` — searched-for phenomenon was not observed within the recorded window; respect censoring.
- `NOT_ADJUDICATED` — semantic adjudication has not been performed or finalized.

Do not convert `NOT_OBSERVED` into universal absence, and do not convert `SUPPORTED_CANDIDATE` into a causal conclusion.

## 11. Directly Evidenced / Candidate / Boundary close-out is mandatory

Every substantial experiment report must end the results body with three explicit close-out blocks:

1. **Directly Evidenced** — what the current stage actually establishes.
2. **Supported Candidates / Open Mechanism Questions** — what is localized strongly enough to motivate the next experiment but remains incomplete.
3. **Not Established / Not Adjudicated** — attractive conclusions that the present evidence does not justify.

This is the default anti-overclaim gate for the repository.

## 12. Process and terminal outcome must be reported separately

Terminal correctness, final answer agreement, reward, business KPI or task completion must be reported as endpoint variables.

They do not define Process Reality and must not erase process-level differences.

When terminal outcomes converge but process structure/semantics differ, report both explicitly.

## 13. Perturbation reports must separate localization from operator validity

A weak or absent downstream response does not automatically falsify the selected Jump/localization.

Reports must keep separate:

- localization validity;
- perturbation-operator validity;
- perturbation coupling depth;
- descendant invalidation/repair reach;
- observed downstream response.

For one-shot authority withdrawal, the report must distinguish source-label/status change from changes to already materialized semantic descendants.

## 14. Specificity and robustness reporting

The v1.3 R6-D rule remains active:

- default first-level label: `FROZEN_TARGET_RESPONSE_CONTRAST`;
- disclose non-exchangeability in task relevance, provenance, prior epistemic state, structural position, downstream opportunity and decision weight;
- an Escape/J0-specific interpretation requires explicit matching or append-only robustness evidence;
- same-parent repeats are repeated realizations, not independent population samples.

Robustness evidence that weakens specificity must be reported, not hidden behind an earlier positive contrast.

## 15. R7 and later control/recovery reports

R7 closure separation from v1.3 remains mandatory:

1. `PotentiallyAffectedClosure`
2. `EvidenceSupportedAffectedClosure`
3. `MechanicallyRequiredReplayDependencies`
4. `RepairClosure`
5. preserved structure

Future R7 reports must use the same evidence-first profile: scout/localize facts first, semantic affectedness second, repair action third, recovery interpretation last.

R8 CPR adjudication and R9 reviewer/multi-model supplementation remain separate report layers. They do not retroactively alter frozen subject evidence.

## 16. Provenance and open-PR status

Every report must expose enough provenance to reproduce or locate the evidence, including as applicable:

- workflow run ID;
- artifact ID and digest;
- evidence batch hash;
- raw traces hash;
- plan/design hash;
- parent-state hash;
- execution/code SHA;
- measurement/runtime-plan hash;
- preserved traces / errors;
- evaluator status;
- CPR status.

If a derivation exists only on an open PR, report it as an open-PR derived projection. Do not describe it as merged-main state.

## 17. Visual grammar

Figures are optional; evidence tables are not.

When figures are used:

- prefer time-aligned causal/semantic paths or stage evidence maps;
- use event/turn/message identifiers that resolve to tables;
- do not draw all-to-all interaction maps when they obscure causal order;
- clearly label whether a figure is a raw structural projection, semantic audit projection or cross-stage evidence map;
- never use a figure to imply continuity between distinct frozen runs.

Repository Markdown may use Mermaid diagrams. Publication DOCX/PDF exports may use rendered figures derived from the same report source.

## 18. Language and naming

Forward repository experiment reports are English by default for scientific consistency and external reviewability. Exact code identifiers, field names, hashes and status enums must remain unchanged.

Use `R2-R6`, `R6 Batch 2`, etc. for stage identity; do not rename stages merely for narrative smoothness.

## 19. Authorization boundary

A report never authorizes a new provider call, evaluator call, subject rerun, recovery action, semantic adjudication or evidence rewrite.

Experiment execution authorization remains separate from reporting.

## 20. Forward rule

Unless a future standard supersedes v1.4, **all new Process Reality experiment reports should use this evidence-first profile and the accompanying template**.

Historical files stay bound to the report standard named in their own header.
