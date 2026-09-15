# CN-R-035 — Independent blind cross-model review exposes measurement disagreement

**Status:** REVIEWER B COMPLETE; CROSS-MODEL AGREEMENT MEASURED; SEMANTIC CONSENSUS NOT ESTABLISHED.

## Evidence binding

Reviewer B is bound to the same frozen formal evidence batch as Reviewer A:

`94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`

Reviewer B used DeepSeek through the existing repository `DEEPSEEK_API_KEY`. No subject trajectory was rerun. The blind-review workspace excluded Reviewer A files, theory Change Notes, expected C/P/R→Authority mappings and structural-feedback conclusions. Seventy sanitized event units were reviewed and frozen before comparison.

Successful blind-review workflow: `34976668171`.

## Independence boundary

- Reviewer A: GPT-5.6 Sol interactive analyst, non-blinded to the study hypotheses.
- Reviewer B: DeepSeek blind Reviewer B, isolated from Reviewer A results and expected mappings.

This is **asymmetric cross-model replication**, not two fully blinded raters and not human inter-rater reliability.

## Agreement result

Across 70 Authority-bearing events:

| Dimension | Percent agreement | Cohen κ | A positive | B positive |
| --- | ---: | ---: | ---: | ---: |
| C | 0.700 | 0.158 | 3 | 24 |
| P | 0.729 | 0.318 | 10 | 25 |
| R | 0.729 | 0.486 | 42 | 25 |

Authorization agreement is 0.700 with Cohen κ = 0.376.

Exact Bias-label-set agreement is 0.300. Exact joint Bias+authorization agreement is 0.229. Fifty-four of 70 events have at least one label-set or authorization disagreement.

Therefore this blind review **does not provide high semantic inter-rater agreement**. The result must not be described as independent confirmation of Reviewer A's event-level coding.

## Primary-estimand comparison

Using the same `realized + UNAUTHORIZED + mechanism-coded` primary rule:

| Reviewer | C run emergence | P run emergence | R run emergence | C I/V/T | P I/V/T | R I/V/T |
| --- | ---: | ---: | ---: | --- | --- | --- |
| A | 2/3 | 2/3 | 3/3 | 3/0/0 | 0/9/0 | 2/5/4 |
| B | 3/3 | 3/3 | 3/3 | 4/0/3 | 0/18/2 | 1/1/3 |

The reviewers share 12 primary unauthorized Bias-bearing events. Reviewer A marks 16 primary events and Reviewer B marks 26; the union is 30 and Jaccard overlap is 0.400.

The useful signal is therefore asymmetric:

- 12/16 of Reviewer A's primary events are independently recovered by Reviewer B;
- Reviewer B is substantially more liberal in assigning C and P and in judging events unauthorized;
- run-level R emergence is 3/3 under both reviewers;
- P remains strongly concentrated in V for both reviewers;
- C is I-only for A but I-plus-T for B;
- R spans I/V/T under both, but with different event distributions.

These are robustness observations, not consensus labels.

## Measurement implication

The largest current uncertainty has moved from subject collection to **semantic operationalization**. The frozen subject evidence is stable; reviewer thresholds differ materially, especially for:

- when a specialist is “materially needed” versus completeness-seeking expansion;
- when an inference counts as evidential-status promotion rather than a legitimate recommendation;
- whether retrospective behavior should be attached to downstream I/V events or reserved for narrower reopen/revision behavior;
- how to judge non-realized Authority attempts and events whose applicability is borderline.

Changing the rubric after seeing Reviewer B would create post-hoc optimization. Reviewer A and Reviewer B records therefore remain frozen unchanged.

## Next gate

Before using a single semantic matrix as a paper-level estimate, the project should perform a **rubric/adjudication stage on the frozen disagreements**, ideally with a human coder and/or a third blinded model operating under a preregistered clarification protocol.

The adjudication objective is not majority vote. It is to identify which operational definitions produce reproducible distinctions and to preserve unresolved cases as uncertainty.

No subject rerun is warranted. A real K=2 experiment may still be scientifically useful later, but reviewer disagreement is now the higher-priority measurement problem; K=2 should not be used to bypass unresolved Base semantic reliability.

## Cost/audit note

The successful Reviewer B run recorded 1,802,392 tokens, dominated by prompt-cache hits, with repository-snapshot estimated cost USD 0.0196 off-peak / 0.0393 peak. Two units required bounded review-output retry.

An earlier review attempt (`34976354279`) produced 65/70 valid records before five units failed validation. Those partial outputs were not frozen or used in agreement analysis, but the attempt did incur additional provider usage that was not fully aggregated. It must not be hidden from cost/audit history.
