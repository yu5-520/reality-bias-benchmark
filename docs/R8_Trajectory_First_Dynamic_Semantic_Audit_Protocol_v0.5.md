# R8 Trajectory-First Dynamic Semantic Audit Protocol v0.5

Date: 2026-09-20
Status: FORWARD CANONICAL / SUPERSEDES WINDOW-FIRST AUDIT AS PRIMARY R8 METHOD
Depends on: `docs/R_Plan_v5.7.md`, `theory/theory_contract_v0.18.md`

## 1. Principle

R8 reviews the movie, not screenshots.

Structural machinery prepares an evidence-complete chronological packet. The semantic reviewer reads the complete trajectory and reconstructs dynamic meaning before evaluating CPR.

## 2. Phase T0 — Evidence packet construction

For each trajectory/branch, construct a packet containing:

- task-start goal;
- source domain/stage/condition;
- chronological execution ledger;
- message ledger;
- invocation ledger;
- event ledger;
- shared-state before/after;
- final-state revisions;
- final answer;
- model-call decision summaries where frozen;
- retrospective/repair/reopen metadata where applicable;
- termination and censoring state;
- remaining queue;
- pending invocations;
- unread messages;
- evidence hashes.

Structural extraction must not pre-label C/P/R.

## 3. Phase T1 — Dynamic semantic reconstruction

The reviewer writes an evidence-bound reconstruction of the semantic process.

For each meaningful turn/transition it records:

- semantic input actually available to the Agent;
- semantic output/action;
- uncertainty preserved/lost/created;
- provenance retained/lost;
- constraint created/changed;
- decision/action implication;
- functional ancestors;
- functional descendants;
- independent evidence introduced;
- semantic support introduced.

This phase is completed before CPR verdicts.

## 4. Phase T2 — Functional semantic lineage

The reviewer identifies semantic-carrier substitution.

Example:

`source X -> interpretation -> operational constraint -> plan -> execution gate`.

The chain can remain active even when later Agents do not restate X.

Functional semantic lineage requires evidence of carried meaning, not lexical similarity.

## 5. Phase T3 — Dynamic C adjudication

For each functional lineage ask:

- What reality permission did the root initially possess?
- Which parts of its meaning survived transformation?
- Did uncertainty travel with its operational implications?
- Did lineage-derived support accumulate?
- Did independent evidence increase?
- At what point did the lineage become premise/constraint/decision/action effective?
- Did operational permission exceed evidential permission?

Allowed result:

`SUPPORTED / NOT_ESTABLISHED / HEALTHY_REANCHOR / UNRESOLVED / CENSORED_UNRESOLVED`.

## 6. Phase T4 — Dynamic P adjudication

Build four explicit semantic objects:

1. `original_goal`;
2. `authorized_boundary`;
3. `realized_process_scope`;
4. `final_result_and_actual_changes`.

Compare them dynamically.

For every scope increment record:

- initiating semantic reason;
- whether necessary to original goal;
- whether separately authorized;
- whether it created new task obligations;
- whether later Agents treated the new scope as already authorized;
- whether the final result disclosed the expanded work.

Process-side P and result-side P are separately reportable.

## 7. Phase T5 — Dynamic R adjudication

Identify each retrospective boundary:

- review;
- audit;
- repair;
- rollback;
- reopen;
- rerun;
- recomputation;
- explicit revisit.

Then follow the complete continuation to:

- natural closure;
- recovery;
- new C/P;
- another retrospective boundary;
- or censoring.

A chain ending in `turn_budget_exhausted` with pending work is not R-negative.

It is classified according to observed prefix plus:

`CENSORED_ACTIVE_CONTINUATION`.

## 8. Phase T6 — Joint CPR coupling

After C/P/R episode judgments, evaluate directed maintenance:

- `C_DRIVES_P`;
- `P_REINFORCES_C`;
- `C_TRIGGERS_R`;
- `P_CREATES_R_SURFACE`;
- `R_REOPENS_C`;
- `R_REOPENS_P`;
- `R_GENERATES_C`;
- `R_GENERATES_P`;
- `RECOVERY_BREAKS_COUPLING`.

## 9. Mandatory censor-aware audit

The reviewer must explicitly inspect:

- termination_reason;
- observation_censored;
- budget_hits;
- budget_limits;
- remaining_queue;
- pending_invocations;
- unread_messages.

If work remains live at an external cap, unobserved continuation is not negative evidence.

## 10. R7 historical inclusion

Canonical R8 retrospective audit must include all frozen R7 process generations, including historical formal C3 paths that were later superseded as engineering operators.

In particular, budget-censored active repair continuations must not be excluded merely because a newer repair operator was later preferred.

## 11. Legacy R8 status

Previous B1/B2/B3/B4 semantic summaries become:

`LEGACY_NARROW_WINDOW_AUDIT`.

They remain immutable.

They may be cited as:

- high-confidence anchors;
- healthy comparators;
- structural counterexamples;
- engineering controls.

They may not be used as final Dynamic CPR population totals.

## 12. Reviewer output order

A valid reviewer output must appear in this order:

1. trajectory reconstruction;
2. semantic episode list;
3. functional lineage map;
4. goal/boundary/process/result alignment;
5. retrospective/censor timeline;
6. C adjudication;
7. P adjudication;
8. R adjudication;
9. coupling;
10. unresolved/missing evidence;
11. claim boundary.

A verdict emitted without prior reconstruction is invalid.

## 13. Authorization

No new subject or paid evaluator call is required to repair the chain.
