# Semantic Audit and Reporting Contract v0.1

Status: `FROZEN_METHOD_CONTRACT_CANDIDATE`

Scope: Reality Bias first-paper evidence from R2–R7. This contract governs audit responsibility, semantic interpretation, and scientific reporting. It does **not** rewrite any already-frozen raw evidence, subject trajectory, preregistered structural estimand, intervention design, or CPR adjudication state.

## 1. Core method boundary

The repository uses two different evidence functions:

- **System computation establishes structural facts.**
- **Semantic audit interprets what those structural facts mean in Agent reasoning.**

A structural observation is not automatically a semantic conclusion.

Canonical pipeline:

`raw evidence -> integrity audit -> structural derivation -> frozen structural evidence bundle -> semantic audit -> claim/boundary audit -> report`

The direction is one-way. Later interpretation MUST NOT rewrite raw evidence or frozen structural facts.

## 2. Audit responsibility layers

### 2.1 Evidence / Integrity Audit

Responsible for factual evidence integrity only:

- raw artifact identity and digest/hash;
- execution/run binding;
- trace completeness and missingness;
- provider/subject execution status when observable;
- evidence freeze and immutability;
- authorization/control-plane binding where applicable;
- lineage between subject run and derived artifacts.

Allowed outputs: integrity status, hashes, missing items, freeze status, provenance pointers.

Forbidden outputs: semantic adoption, authority formation, semantic inheritance, System Inertia, CPR, causal interpretation.

### 2.2 Structural Audit

Responsible for mechanically derivable process structure only:

- actors, calls, turns, messages and event ordering;
- reads, writes, state mutations and termination/censoring;
- literal references and field/value visibility;
- graph/topology edges and propagation opportunities;
- observation windows and downstream exposure opportunities;
- condition/branch structural comparisons defined by frozen analysis contracts.

Allowed outputs: tables, counts, timelines, node/edge graphs, deterministic structural contrasts.

Forbidden upgrades:

- hash or lineage != semantic adoption;
- literal reference != semantic inheritance;
- persistent visibility != System Inertia;
- turn/Agent/message count != semantic propagation strength;
- event order != causal origin;
- state co-occurrence != supports/causes/constrains relation.

Structural metrics may locate where semantic audit should inspect evidence. They MUST NOT adjudicate semantic meaning by themselves.

### 2.3 Semantic Audit

Semantic audit operates only on frozen raw evidence plus frozen/identified structural evidence. It is responsible for evaluating semantic process reality, including:

- source proposition and epistemic status;
- semantic transformation and derived propositions;
- semantic adoption versus mere visibility/relay;
- cross-Agent coupling;
- semantic relations such as `supports`, `causes`, `constrains`, `depends_on`, `enables`, `conflicts_with`, `reframes`, `drops`, `reconstructs`;
- authority materialization or authority change;
- semantic descendants and cross-domain amplification;
- Jump interpretation;
- perturbation response and whether a perturbation reaches inertia-bearing semantic relations;
- downstream judgment/action constraint;
- recovery meaning in R7.

Every positive semantic claim MUST bind to exact evidence pointers (trace/run/event/node/message/state path as available) and state the structural facts used.

Semantic audit MUST distinguish at least:

1. carrier visibility;
2. semantic adoption;
3. semantic relation propagation;
4. downstream judgment/action constraint.

If evidence does not establish a semantic relation, the result MUST be `NOT_ESTABLISHED` rather than inferred from structural proximity.

Semantic audit MUST NOT modify structural facts, reconstruct missing evidence, or convert retrospective interpretation into a preregistered fact.

### 2.4 Claim / Boundary Audit

Responsible for checking that scientific claims do not exceed evidence.

Canonical statuses:

- `SUPPORTED`
- `SUPPORTED_CANDIDATE`
- `NOT_ESTABLISHED`
- `CONTRADICTED`

Boundary audit MUST check at least:

- structural evidence has not been silently upgraded into semantic evidence;
- temporal precedence has not been upgraded into causal origin;
- same-parent repeated realizations are not described as independent population samples;
- no post-hoc scalar/ranking is presented as frozen confirmatory analysis;
- local perturbation non-response is not treated as proof that Jump localization was wrong;
- `fact -> unconfirmed` is treated as one perturbation operator, not a universal validity test;
- CPR remains separately adjudicated and cannot be inferred by this audit contract;
- missing evidence remains missing;
- raw evidence remains immutable.

## 3. Required semantic distinctions

The following concepts MUST remain separable unless evidence explicitly identifies them:

`semantic origin != initial driving event != coupling event != authority materialization != Jump != inertia carrier`

Jump may be a macroscopic observable anchor after a semantic process has already formed. A Jump node MUST NOT be called the semantic origin solely because it is the intervention anchor.

Likewise:

`failure of perturbation response != failure of Jump localization`

Interpretation must separate:

1. localization validity;
2. perturbation-operator validity;
3. perturbation coupling depth/strength to the inertia-bearing semantic structure.

## 4. R2–R7 responsibility map

This map defines audit questions, not predetermined answers.

- **R2–R4:** inspect natural formation: semantic origin/seed, first action-bearing use, cross-Agent adoption, coupling, authority materialization, amplification, semantic descendants, and the relation of these to Jump.
- **R5:** inspect the local semantic response to the single minimal probe. R5 alone does not establish inertia, causality, CPR, or recovery.
- **R6:** inspect whether existing semantic relations and downstream constraints survive, weaken, break, reorganize, or reconstruct after perturbation. System Inertia is a semantic-relation/constraint question, not trajectory length.
- **R7:** inspect whether localized recovery targets evidence-supported affected semantic structure and whether semantic process integrity is restored without unjustified collateral rewriting.

## 5. Blind semantic audit contract

An independent reviewer SHOULD receive the same frozen evidence package and audit protocol while being shielded, where practical, from previous semantic labels, desired conclusions, and other reviewers' answers.

For each audited event/node/relation the reviewer MUST answer, where evidence permits:

1. What proposition or information is introduced or transformed?
2. What epistemic status is explicit in the evidence?
3. Is the information merely visible, or is it used as a premise?
4. Does it generate a derived proposition/judgment?
5. Does it constrain an action, priority, budget, gate, fallback, or other decision?
6. Is it adopted by another Agent, or merely relayed/copied?
7. Does source uncertainty remain explicit?
8. Does authority of a source or descendant change?
9. Does a semantic descendant form and persist?
10. Which semantic role is supported: `observation`, `adoption`, `coupling`, `authority_materialization`, `amplification`, `jump`, `perturbation_response`, `inertia`, `recovery`, or `NOT_ESTABLISHED`?

Reviewers MUST provide evidence pointers and a boundary statement. Free-form narrative without evidence binding is not an admissible semantic audit record.

Multiple independent semantic audits are append-only and may coexist. Reviewer disagreement is evidence about interpretation uncertainty; it MUST NOT trigger a subject rerun.

## 6. Semantic-first scientific reporting

Scientific reports and paper sections SHOULD use semantic audit as the explanatory narrative and structural/system outputs as factual support.

Canonical reporting order:

`semantic claim -> structural evidence -> raw evidence pointer -> boundary/alternative interpretation`

The report MUST NOT use the reverse shortcut:

`structural metric -> automatic semantic conclusion`

### 6.1 Main text

Main text should explain semantic process changes: how a proposition is interpreted, adopted, transformed, coupled, materialized, amplified, perturbed, inherited, reorganized, or repaired.

### 6.2 Tables

Tables are evidence witnesses. A preferred table contains:

- evidence node/event;
- actor;
- source proposition/status;
- structural observation;
- semantic audit result;
- relation type;
- claim status/boundary.

### 6.3 Node / lineage graphs

Primary explanatory graphs SHOULD show semantic lineage rather than actor topology alone, for example:

`source proposition -> derived proposition -> judgment -> constraint/action -> downstream descendant`

Each semantic edge SHOULD be traceable to evidence node/event identifiers. Structural actor/call topology may be shown separately as supporting instrumentation.

### 6.4 Metrics

Counts such as turns, messages, references, state writes, and Agent calls remain valid structural facts and may quantify observation opportunity or process geometry. They MUST NOT be presented as direct measures of System Inertia unless a separately frozen operational definition explicitly establishes that mapping.

## 7. Existing frozen contracts

This contract does not retroactively alter frozen structural estimands in existing analysis contracts, including `schemas/first_paper_analysis_contract_v0.1.schema.json`.

Where an existing frozen contract defines confirmatory structural outcomes, those outcomes remain frozen. This contract governs:

- responsibility boundaries between structural and semantic layers;
- semantic-audit admissibility;
- interpretation boundaries;
- scientific reporting order and evidence binding.

Any future change to a frozen experimental estimand requires a new versioned contract rather than silent reinterpretation.

## 8. Immutability and append-only rule

- Raw subject evidence: immutable.
- Frozen structural derivations: immutable within their version.
- Semantic audits: append-only, reviewer/version identified.
- Claim/boundary audits: append-only, bound to exact semantic-audit versions.
- Reports may be revised, but every scientific claim must remain traceable to the evidence/audit version on which it depends.

## 9. Non-claims

Adopting this contract does not itself establish:

- CPR;
- Escape specificity;
- causal origin of any semantic trajectory;
- efficacy of R7 repair;
- validity of any particular Jump localization;
- that any current R2–R6 retrospective label is final.

Those remain empirical/adjudicative questions.