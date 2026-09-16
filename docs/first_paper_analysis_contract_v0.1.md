# First Paper Analysis Contract v0.1

Date: 2026-09-16  
Status: **FROZEN BEFORE NEW v4 SUBJECT EVIDENCE**

This document explains the human-readable position frozen in `configs/first_paper_analysis_contract_v0.1.json`. The JSON contract is the machine-readable source of truth. Any later change requires a new contract version and must not be back-applied to evidence already bound to v0.1.

## 1. What this first-paper experiment actually tests

The current confirmatory intervention is the existing R5-MID frozen-parent branch experiment:

```text
same frozen parent state
├── control: selected state keeps HIGH_CERTAINTY status
└── intervention: same state value is downgraded to PROVISIONAL
```

The intervention changes the registered epistemic status only. All other branch-visible state is required to remain identical at branch start under the existing single-field-diff proof.

The first-paper question is therefore not “does the model think less?” and not “did Tension decrease?” It is:

> When only the selected state status is changed from high-certainty to provisional, does the exact frozen branch-start state show less downstream structural reach to operational boundaries?

This is a containment experiment after the source anchor has already been selected. It is not a PRE Tension experiment.

## 2. Primary outcome

The single primary confirmatory structural outcome is:

`R5MID_ANCHOR_DOWNSTREAM_OPERATIONAL_CROSSING_COUNT`

Source:

`structural_deltas.r5_mid_branch_anchor.potential_downstream_operational_crossing_count`

For each matched pair:

```text
pair delta = intervention - control
```

A negative pair delta is consistent with reduced structural reach under the status downgrade. It does **not** by itself mean semantic adoption fell, Authority Penetration was prevented, or a generalized causal law was established.

The batch estimand is the arithmetic mean of eligible complete-pair deltas. Median pair delta and the full distribution of negative/zero/positive pair deltas are always reported.

## 3. Why Jump count is not primary here

The current manipulation is MID-stage. It acts on a state already present at the branch start. A new downstream structural Jump may occur, disappear, move, or change type, but that is not the cleanest measure of whether the manipulated state propagated.

Therefore the analysis is rooted at:

```text
Frozen Branch-Start State Anchor
→ actual runtime visibility
→ source-backed downstream lineage
→ mechanical operational crossings
```

Continuation Jump counts remain exploratory for this experiment.

## 4. Secondary structural outcomes

Secondary confirmatory structural outcomes are:

- mechanical anchor reach depth candidate;
- downstream affected-agent count;
- downstream event count;
- anchor-visible Agent-turn count.

Authority-class reach, downstream Jump structure, retrospective windows and pair-order interactions are exploratory unless a later protocol versions them forward before new evidence.

## 5. Semantic Authority endpoint stays separate

The key secondary semantic endpoint is Reviewer-v4 `authority_penetration` over the bounded packet scope:

`BRANCH_START_ANCHOR_PROPAGATION`

Mechanical crossing count is never substituted for this judgment.

For confirmatory semantic resolution, a packet requires at least two distinct independent reviewer IDs with `evidence_sufficiency = SUFFICIENT`. If all eligible independent reviewers agree, the endpoint resolves to that value. If they disagree, the result stays unresolved unless an append-only adjudication record references all conflicting eligible parent reviews.

`UNCERTAIN`, `NOT_APPLICABLE`, absent review, partial-only evidence, insufficient evidence and unresolved reviewer disagreement are **not** converted to `NO`.

Additional reviewers may be added later because the subject evidence and packet are already frozen. They add semantic sensitivity evidence; they do not change the subject trajectory.

## 6. Pair eligibility and censoring

The primary complete-pair estimand requires both planned conditions to be present, both traces to be `RUN_COMPLETE`, both v4 measurements to exist, the v4 pair comparison to pass parent/binding/hash verification, and the primary outcome to be observed for both conditions.

`BUDGET_CENSORED`, `RUN_INCOMPLETE` and `RUN_FAILED` are execution censoring. If either condition has one of these statuses, the pair is excluded from the primary complete-pair estimate and counted as censored. It is never converted to zero, `NO`, recovery, or absence of effect.

A hash mismatch, unsupported source schema, invalid pair identity or missing required measurement is a data-integrity failure, not a scientific outcome.

A machine-verified observed count of zero in a complete trace is a real zero, not missing data.

No outcome-aware rerun is allowed to manufacture a complete pair.

## 7. Frozen aggregation rule

Primary structural estimate:

```text
mean(intervention_i - control_i)
```

Always report:

- planned pair count;
- complete pair count;
- censored pair count;
- integrity-failure count;
- every pair delta;
- mean and median pair delta;
- negative / zero / positive delta counts.

The uncertainty rule is a paired nonparametric percentile bootstrap with 10,000 resamples, deterministic seed `20260916`, and 95% interval. A confirmatory interval is emitted only when at least 8 complete pairs exist. Below that threshold the system must report all pair values and mark the interval as not estimated.

There is no primary p-value in v0.1. The first paper is estimation-first rather than “find a significant test and promote it.”

Pair-order pattern is reported as a sensitivity view; no order stratum may be dropped after looking at outcomes.

## 8. What this contract does not claim

The paired design starts from the same frozen parent and freezes the registered intervention, but provider hidden state is not replayed. The same logical seed is not treated as hidden-state determinism.

Therefore:

```text
same parent + one registered manipulation
≠ identical hidden counterfactual worlds
```

One pair never establishes a generalized causal effect. The primary analysis reports a matched paired structural contrast under the frozen experiment. Broader causal claims require repeated evidence and the preregistered semantic/robustness layers.

The experiment also does not directly measure Tension or latent Escape Propensity. Those remain future PRE-variable research targets.

## 9. Binding rule

Before any new Phase-B provider call used for this first-paper experiment, the forward `v4_research_binding.json` must contain both:

- the canonical content hash of `first_paper_analysis_contract_v0.1.json`;
- its exact file SHA-256, plus the contract/schema/output-schema interface bindings.

The real-run authorization gate remains separate. Freezing the analysis contract does not authorize paid provider calls or paid Reviewer calls.

## 10. Execution chain after this freeze

```text
frozen Phase-A evidence
→ Phase-B branch plan
→ v4 research binding
   ↳ exact analysis-contract hash
→ explicit paid subject authorization only when separately supplied
→ subject traces freeze once
→ Measurement v3 remains preserved
→ v4 behavior / lineage / branch-anchor derivation
→ paired structural comparison
→ frozen-contract structural analysis
→ bounded Reviewer-v4 semantic review later
```

The analysis code path is `arena/analyze_first_paper_r5mid.py`; it consumes `pair_structural_comparisons_v4.jsonl` plus the v4 derivation summary and emits an append-only derived structural analysis artifact without modifying subject evidence.