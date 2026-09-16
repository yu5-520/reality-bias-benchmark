# R8 CPR Semantic Closure and Evidence Freeze Protocol v0.1

Date: 2026-09-17  
Status: FORWARD SEMANTIC/EVIDENCE PROTOCOL / APPEND-ONLY  
Depends on: `docs/R_Plan_v4.2.md`, `theory/theory_contract_v0.6.md`, existing independent semantic-review infrastructure.

## 1. Purpose

R8 is not a new subject-behavior mechanism experiment.

R8 closes the first-paper evidence chain by applying a frozen semantic definition to already-frozen structural evidence and then binding raw evidence, structural derivation, semantic adjudication and publication-facing artifacts into a reproducible record.

R8 therefore contains two coupled activities:

1. **CPR Semantic Closure**;
2. **Paper-level Evidence Freeze**.

## 2. Ordering rule

The required order is:

```text
raw system evidence
  -> deterministic / source-backed structural derivation
  -> structural freeze
  -> bounded semantic-review packet
  -> independent semantic adjudication
  -> disagreement / unresolved record
  -> theory-proposition mapping
  -> final evidence freeze
```

Semantic review must not create a structural Jump, lineage or dependency relation that is absent from the frozen structural evidence.

## 3. CPR Definition Contract

R8 must freeze a versioned CPR definition before a confirmatory semantic review batch.

### C — Epistemic reality promotion

A C-positive finding requires evidence that content with missing, uncertain, inferred, provisional or weak support acquired a stronger inheritable system status beyond the support available in the process.

Not every inference or summarization is C.

### P — Scope/focus reality expansion

A P-positive finding requires evidence that goal, focus, information, Agent/tool/stage surface or responsibility expanded beyond the supported/authorized closure and materially altered the process.

Not every additional Agent call, branch or decomposition is P.

### R — Retrospective regeneration dynamics

An R-positive finding requires a valid retrospective/challenge/reopen/correction opportunity and evidence that prior C/P-derived state or unresolved descendants persisted, regenerated, amplified, laundered or normalized after that boundary.

Ordinary correction/recovery is not R-positive.

## 4. Exclusion boundaries

The semantic contract must preserve explicit non-CPR possibilities, including:

- legitimate inference;
- legitimate decomposition;
- necessary scope expansion;
- authorized specialist involvement;
- valid correction;
- valid uncertainty maintenance;
- independent new Jump with no source-backed relation to the prior deviation;
- insufficient evidence / unresolved.

The review process must be able to return `NON_CPR` or `UNRESOLVED` rather than force C/P/R.

## 5. Structural-to-semantic candidate map

Structural evidence may identify candidate windows but does not settle semantics.

Examples:

| Structural observation | Semantic candidate | Automatic CPR truth? |
| --- | --- | --- |
| stronger state/status transition | C candidate | No |
| extra Agent/tool/stage activation | P candidate | No |
| descendant Jump | C/P/R candidate depending on context | No |
| post-challenge recurrence | R candidate | No |
| branch expansion | P candidate | No |
| path reconvergence | recovery candidate | No |
| residual lineage | R candidate only with valid semantic ancestry/boundary | No |

## 6. CPR Adjudication Contract

A confirmatory semantic batch must freeze:

- eligible structural candidates;
- candidate-window construction;
- evidence packet fields;
- reviewer instructions;
- reviewer independence requirements;
- allowed semantic labels;
- confidence/uncertainty representation;
- disagreement handling;
- adjudication aggregation rule, if any;
- conditions under which no aggregate label is produced.

Structural candidates must remain visible even when reviewers reject CPR status.

## 7. Recommended semantic statuses

At minimum:

- `NOT_ADJUDICATED`;
- `STRUCTURAL_CANDIDATE_ONLY`;
- `ADJUDICATED_C`;
- `ADJUDICATED_P`;
- `ADJUDICATED_R`;
- `ADJUDICATED_MULTI_LABEL` where the contract explicitly permits it;
- `ADJUDICATED_NON_CPR`;
- `REVIEW_DISAGREEMENT`;
- `UNRESOLVED`.

Do not collapse disagreement into majority certainty unless the frozen contract explicitly defines such aggregation.

## 8. Evidence packet principle

Reviewers should receive the smallest packet sufficient for the semantic question, including where needed:

- candidate event/window;
- relevant pre/post state;
- source evidence;
- necessary prior lineage;
- valid authority/responsibility context;
- retrospective boundary for R candidates;
- downstream inheritance needed to judge operational significance.

Reviewers should not be asked to rediscover the entire structural trajectory from scratch if the structural layer already froze the candidate and its evidence refs.

## 9. Independence of structure and semantics

The same raw/structural evidence object may support multiple append-only semantic reviews.

Adding a new reviewer later must not mutate:

- raw evidence;
- structural derivation;
- prior reviewer output;
- prior adjudication object.

New reviews are appended as new interpretation layers.

## 10. Formal R5-MID frozen-batch boundary

The formal R5-MID batch currently frozen as `NOT_ADJUDICATED` remains `NOT_ADJUDICATED` where its freeze record forbids new semantic CPR adjudication.

R8 must not bypass that restriction by editing the old manifest/report or by representing a later informal interpretation as if it were part of the frozen batch.

A new semantic-review batch must use evidence whose freeze contract permits append-only review or create a separately versioned derived/review object that explicitly respects the original freeze.

## 11. Paper-level evidence freeze

The final R8 freeze should bind, where applicable:

- theory contract version/hash;
- R Plan version/hash;
- measurement contract/version/hash;
- CPR definition/adjudication contract version/hash;
- runtime code SHA;
- model/provider/config binding;
- raw evidence hashes;
- structural derivation hashes;
- semantic packet hashes;
- reviewer output hashes;
- disagreement/adjudication records;
- figure/table/report source identities;
- final report/manuscript-facing artifact hashes.

The preferred architecture is:

> immutable evidence core + append-only interpretation/review layers.

## 12. R8 outputs

R8 should produce at least:

1. a versioned CPR Definition Contract;
2. a versioned CPR Adjudication Contract;
3. a semantic candidate index linked to frozen structural evidence;
4. append-only review records;
5. disagreement/unresolved records;
6. a paper-level evidence manifest.

## 13. Relationship to R9

R8 closes the internal structural-semantic evidence chain.

R9 may later test:

- reviewer robustness on the same frozen evidence;
- model-family replication;
- domain replication;
- independent implementation/laboratory replication.

R9 does not retroactively redefine R8 semantic labels without a new versioned append-only review/adjudication object.

## 14. No paid-evaluator requirement

R8 does not require immediate use of multiple paid frontier models. Evidence may be frozen first and reviewed later by additional human/model reviewers.

The evidence object is fixed; reviewer population may expand append-only under a named R9 robustness plan.
