# R4 Structural Feedback Counter v0.2 — Offline Audit

## Status

**PASS FOR OFFLINE STRUCTURAL MEASUREMENT. NOT YET ACTIVE AS A SUBJECT-RUNTIME STOP RULE.**

Counter: `R4-STRUCTURAL-FEEDBACK-ROUND-v0.2`  
Frozen-trace audit workflow: `34965261787`  
Format Verify 005 evidence re-derivation workflow: `34965319939`  
Re-derived measurement artifact: `r234-format005-censor-aware-rederived-34965319939`  
Artifact ID: `10395007522`  
Artifact digest: `sha256:c18c9faefb0d01672696875c51885805bc70ad27e1792376b1bf3701154dee3b`

No subject or evaluator provider call was made during either audit.

## Why v0.1 was rejected

The first counter draft only required a settled version to be seen by a different Agent, followed by a contribution and a later settled version. On frozen traces that rule over-counted ordinary sequential propagation: the completed 18-turn Microbatch 003 run produced 12 apparent rounds.

That was not an acceptable K unit. It could turn a sequence of `A settles → B sees → B settles` handoffs into repeated “feedback” without evidence that anything returned to A.

v0.1 was therefore rejected before runtime activation.

## v0.2 objective rule

One structural feedback round requires an observed `A → B → A` return:

`A settles → B sees exact settled version → B contributes → A demonstrably receives B contribution → A settles again`

Accepted return evidence is deterministic and contemporaneously logged:

- B message ID appears in A's later model input;
- B invocation ID appears in A's later model input;
- B state-write event is the recorded origin of a state version visible to A; or
- B's settled version is exactly visible to A.

The closing A settled event becomes the next anchor, so counted rounds are non-overlapping.

The counter never reads C/P/R, authorization, Authority penetration, semantic-dependency, evaluator, or self-reinforcement labels.

## Frozen-trace audit

| Source | Status | Turns | v0.2 rounds | Boundary note |
| --- | --- | ---: | ---: | --- |
| Smoke 001 | RUN_COMPLETE | 29 | 3 | later open return opportunity remained at recorded end |
| Microbatch 003 / 0001 | RUN_FAILED | 8 | 1 | open return opportunity before failure |
| Microbatch 003 / 0002 | RUN_COMPLETE | 18 | 2 | open one-way exposure at recorded end |
| Microbatch 003 / 0003 | RUN_FAILED | 13 | 0 | no complete A-B-A round observed |
| Format Verify 005 | BUDGET_CENSORED | 32 | 3 | open return opportunity at observation boundary |

The v0.2 counts are intentionally much lower than the rejected v0.1 counts. This is desirable: K is meant to bound repeated return structure, not ordinary downstream propagation.

For Format Verify 005 the three closed rounds were structurally:

- `ads → inventory → ads`, anchor turn 2, return/close turn 9;
- `ads → inventory → ads`, anchor turn 9, return/close turn 14;
- `ads → finance → ads`, anchor turn 14, return/close turn 19.

Those statements describe only recorded structural return. They do not assert C, P, R, Authority violation, semantic causation, or self-reinforcement.

## Evidence re-derivation

The current structural-view exporter includes the counter under `structural_feedback_rounds`. Re-deriving Format Verify 005 from its frozen raw trace preserves the same evidence-batch identity while adding the newer deterministic measurement view.

The re-derivation asserts:

- `ARENA-STRUCTURAL-VIEWS-v0.2`;
- counter version `R4-STRUCTURAL-FEEDBACK-ROUND-v0.2`;
- semantic-blind flag true;
- 3 closed rounds in Format Verify 005;
- all semantic fields `NOT_ADJUDICATED`;
- original evidence-batch hash unchanged.

The re-derived artifact is a new deterministic measurement product over the same frozen subject evidence. It does not create a new behavioral sample and does not alter the source evidence-batch identity.

## What this does not authorize

These old Base traces are counter-validation material, not K-controlled subject experiments. A Base trace containing three structural rounds is not relabeled as `K=3`.

Before a paid K=2 run, the runtime must still implement an explicit loop-budget stop condition bound to the counter version and preserve the usual turn/invocation/queue safety caps. K=4 remains conditional on the K=2 semantic review gate.
