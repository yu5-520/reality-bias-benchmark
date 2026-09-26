# Process Reality Report Standard v1.9

Date: 2026-09-26  
Status: **FORWARD ACTIVE / GENERAL-CHAPTER-LINKED**  
Predecessor: `RB-PROCESS-REALITY-REPORT-STANDARD-v1.8`

Historical reports remain immutable.

This version retains every complete-route / semantic-trajectory requirement of v1.8 and adds the parent/child report relationship required by the Stage-II General Chapter.

## 1. Core report chain

Forward reports continue to use:

`Frozen Evidence -> Complete Actual Agent Route -> Semantic Lineage Overlay -> Node/Edge Semantic Audit -> Typical Contrast -> Supporting Structural Data -> Aggregate Counts -> Claim Boundary -> Provenance`

Semantic audit remains the primary interpretive content.

## 2. Stage-II General Chapter

The parent interpretation contract is:

`docs/reports/2026-09-26/StageII_General_Chapter_Process_Reality_Methodology_and_Hypotheses_v1.md`

with machine-readable IDs in:

`configs/stage2_general_chapter_claim_registry_v1.json`.

The General Chapter defines:

- methodological foundations;
- interpretation boundaries;
- hypothesis IDs;
- forbidden claim upgrades;
- the relationship between process evidence and terminal outcome.

It does not replace source-bound evidence.

## 3. Mandatory child-report relationship

Every new Stage-II child experiment report that invokes the General Chapter must include:

### Relation to Stage-II General Chapter

with four fields:

1. **Adopted methodological IDs**
2. **General-Chapter hypotheses informed**
3. **Independent evidence contributed**
4. **Claim boundary**

Example:

`adopted: GC-M1, GC-M3, GC-M4`

`informs: GC-H3a`

`evidence: X5-T3 route/material refs + frozen retrieval carriers`

`boundary: does not prove all RAG systems fail to form shared state`

## 4. Anti-circularity rule

The General Chapter is a parent interpretive contract, not evidence for a child empirical result.

A child report must not reason:

`GC claim -> child repeats GC claim -> child therefore proves GC claim`.

The valid direction is:

`GC research question / definition -> child source-bound evidence -> bounded child finding`.

A later General Chapter synthesis may cite the child evidence, but must preserve the child's evidence and claim boundary.

## 5. Hypothesis wording

For claim-registry entries with `class=RESEARCH_HYPOTHESIS`:

- `NOT_ESTABLISHED`: use “hypothesis”, “motivates”, “raises the possibility”, or equivalent.
- `SUPPORTED_CANDIDATE`: use “is consistent with”, “supports the candidate interpretation”, or equivalent.
- Do not use “proves”, “establishes universally”, or a causal named-framework statement unless a separately authorized design supports that wording.

## 6. Framework / outcome discipline

Forward Stage-II reports must preserve:

- no seven-framework performance ranking;
- no population prevalence from n=1/cell natural trajectories;
- no named-framework causal claim from natural cells;
- `same endpoint != same process`;
- `different process != automatically worse process`.

## 7. Full-route and semantic-content rules

All v1.8 requirements remain active:

- all executed route nodes remain visible;
- semantic overlays do not replace the actual route;
- semantic before/after/delta must be concrete;
- edge endpoints must bind evidence;
- missing semantics remain missing;
- aggregates come after case-level evidence.

## 8. Resource-comparison rule

Cross-stage statements about token/resource efficiency require a frozen common denominator.

Total resource consumption from experiments with different trajectory populations or task structures may not be compared as though directly exchangeable.

Prospective valid units may include token/trajectory, token/turn, token/handoff, or token/semantic-transition, but the chosen denominator must be defined before the comparison is promoted to a report-level result.

## 9. Authorization boundary

This standard authorizes no:

- subject run;
- provider/evaluator call;
- natural rerun;
- C3/C4 contrast;
- repair action;
- semantic reconstruction of missing observations.

## 10. Required opening block

The v1.8 opening block remains required. New Stage-II child reports additionally state:

- General Chapter version/path;
- General Chapter claim IDs used;
- whether each ID is methodological, supported-candidate, or hypothesis-only.

## 11. Required provenance

A forward child report must bind its own evidence independently of the General Chapter, including as applicable:

- cell/trajectory ID;
- route material;
- semantic ledger;
- manifest;
- protocol/native event refs;
- checkout state;
- workflow/artifact/hash provenance.

This is the mechanism by which child reports and the General Chapter mutually organize the research programme without circularly proving one another.
