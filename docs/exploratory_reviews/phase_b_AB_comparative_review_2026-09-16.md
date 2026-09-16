# Phase-B Exploratory A/B Comparative Review

Date: 2026-09-16  
Scope: exploratory pilot comparison only  
Source run: GitHub Actions `35108633026`  
A: `CONTROL_CONTINUATION`  
B: `STATUS_DOWNGRADE_INTERVENTION` (`inventory_transfer_feasibility.status: fact -> provisional`)

## 1. Review status

This is an exploratory A/B structural comparison. It is **not** the formal R5-MID causal-effect report.

The Phase-B subject runs, evidence derivation, Measurement-v3 and System Behavior v4 all executed on the GitHub runner. However, the raw evidence artifact was not durably persisted because the upload step rejected journal filenames containing `:`. The primary R5-MID outcome value therefore cannot be reconstructed from the retained job log alone.

The formal primary outcome remains:

`R5MID_ANCHOR_DOWNSTREAM_OPERATIONAL_CROSSING_COUNT`

That outcome is **not available for adjudication in this report**. This comparison therefore uses only retained run-status, turn-count, execution-order, censoring and derivation-status facts.

## 2. Observed A/B layout

| Pair | Execution order | A: Control | B: Status downgrade | Pair status for formal comparison |
|---|---|---|---|---|
| Pair 1 | A first, B second | `RUN_COMPLETE`, 13 turns | `RUN_COMPLETE`, 30 turns | Complete pair |
| Pair 2 | B first, A second | `BUDGET_CENSORED`, 32 observed turns | `RUN_COMPLETE`, 16 turns | Incomplete pair |

Measurement-v3 derived 4 branch measurements but only **1 complete pair comparison**. System Behavior v4 likewise reported **1 structurally compared pair**.

## 3. Pair-level exploratory reading

### Pair 1

Both branches completed naturally.

- A Control: 13 turns
- B Intervention: 30 turns
- descriptive turn difference `B - A = +17`

This `+17` is a **secondary trajectory-length diagnostic only**. It is not the frozen primary outcome and cannot be interpreted as a positive or negative causal effect.

### Pair 2

B completed naturally at 16 turns. A remained active through 32 turns and was censored.

Therefore no natural episode-length delta can be computed for Pair 2. Writing `16 - 32 = -16` would be methodologically wrong because A's 32 is an observation boundary, not its natural endpoint.

The only valid statement is that A had at least 32 observed turns before censoring, while B naturally completed at 16 turns.

## 4. The two pairs do not support a simple length-direction story

If one looks only at retained turn counts:

- Pair 1 has B longer than A.
- Pair 2 has A observed for at least twice as many turns as B before A was censored.

The direction therefore does not replicate across the two pairs. That is useful in the exploration stage because it warns against replacing the frozen primary outcome with an easy proxy such as total turns.

Trajectory length appears to be strongly affected by stochastic continuation dynamics and possibly execution-resource context. It should remain a diagnostic measure rather than become the causal target after seeing the pilot.

## 5. Execution-order and shared-budget signal

The pair order was deliberately counterbalanced:

- Pair 1: A first, B second.
- Pair 2: B first, A second.

A notable exploratory pattern is that the **second-executed branch in each pair was the longer observed branch**:

- Pair 1 second branch B: 30 turns versus first branch A: 13.
- Pair 2 second branch A: 32 observed turns and censored versus first branch B: 16.

This does **not** prove an order effect, but it creates a real design concern. In addition, all four branches shared one batch-level call/resource guard, and the final branch was the only censored branch. Its cumulative engineering spend remained well below the `2 USD` monetary ceiling, so the censoring cannot safely be attributed to dollar spend alone.

For future formal evidence collection, resource allocation should be treated as part of the experimental interface. A design in which all branches share a single cumulative call budget can expose later branches to a different censoring risk than earlier branches.

Candidate future designs include:

1. equal per-branch call caps;
2. equal per-pair call caps with explicit unused-budget handling;
3. a fixed observation window applied symmetrically to both conditions;
4. preserving the current natural-until-quiescent design but ensuring the global batch cap is sufficiently above the maximum possible branch demand.

Any such change would create a new experimental version and must not be retroactively applied to this pilot.

## 6. Condition-level descriptive comparison

### A — Control

- 2 planned branches;
- 1 natural completion;
- 1 censored branch;
- observed lengths: 13 and 32+ turns;
- high within-condition variability.

### B — Intervention

- 2 planned branches;
- 2 natural completions;
- 0 censored branches;
- natural lengths: 30 and 16 turns;
- high within-condition variability.

The difference in completion count (`A 1/2`, `B 2/2`) must **not** be read as evidence that B is more stable or superior. The sample is tiny, A's censored branch was last in the batch, and the censoring mechanism is not fully recoverable from the persisted high-level record.

## 7. What the A/B pilot does support

This pilot supports several experiment-design conclusions:

1. The single-field `fact -> provisional` intervention is executable and does not mechanically disable downstream continuation.
2. Both A and B exhibit substantial within-condition stochastic variability.
3. Turn count is not a reliable substitute for the pre-frozen primary outcome.
4. Censoring handling is essential; an incomplete branch cannot be coerced into a complete pair.
5. Execution order and shared resource guards are plausible nuisance factors that should be controlled more explicitly in a formal batch.
6. The current paired, same-parent framework is valuable precisely because raw trajectory variability is large.

## 8. What the A/B pilot does not support

This pilot does **not** support:

- a claim that status downgrade increases or decreases downstream anchor influence;
- a claim that A or B is better, worse, more efficient, more accurate or more stable;
- a C/P/R or Authority Penetration judgment;
- a semantic claim that agents trusted, ignored, propagated or operationalized the selected anchor differently;
- a task-success conclusion;
- a formal R5-MID causal-effect estimate;
- a population-level or cross-parent generalization.

## 9. Relationship to the frozen first-paper question

The narrow first-paper question remains sound:

> From the same frozen parent, if only the epistemic status of one selected shared-state item is downgraded, does downstream anchor-reachable operational behavior systematically change?

This pilot does not answer that question, because the raw evidence needed to recover the frozen primary outcome was not durably persisted. What it does answer is a prior engineering/scientific question: **the intervention and paired continuation machinery are capable of producing natural, nontrivial, heterogeneous continuations without hard-coding the desired result.**

That makes the pilot useful even without promotion to formal evidence.

## 10. Exploratory comparative conclusion

**A/B exploratory assessment:** The pilot shows a functioning but high-variance causal-test environment. A and B both generate nontrivial natural continuations; neither condition collapses into a deterministic path. The retained turn-level pattern is directionally inconsistent across pairs, and one late Control branch is censored. Therefore the correct next lesson is not “A wins” or “B wins,” but that formal R5-MID inference must rely on the frozen anchor-reachable operational outcome, paired parent-aware analysis, explicit censoring, and tighter control of execution-resource exposure.
