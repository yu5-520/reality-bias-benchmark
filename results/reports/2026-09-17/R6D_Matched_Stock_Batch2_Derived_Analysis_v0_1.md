# R6-D Matched-Stock Batch 2 — Derived Analysis v0.1

- Workflow run: `35242903322`
- Evidence batch hash: `a550543edf53339c44cd6d72a0a2bde2151fff56d98117043edab28980033a45`
- Design hash: `5064e255da26949a152a2300fe659ebdddddc9b44f1a97a4b31d7796005a959d`
- Execution SHA: `be0cfeebcbd20f7c6b304f2b91c95fa563eceb03`
- Artifact ZIP SHA256: `1db98dc6f1ea618d4ed6d85f3430f44b4083d4575beba9b34f94a376b0a98e92`
- Inner tar SHA256: `be314b8cff3aef2e4283874bbe82244fda6b56175ac8a9657f6642269207f164`
- Raw frozen before derivation: **YES**
- Paid evaluator: **NO**
- CPR: **NOT_ADJUDICATED**

## Main result

**Batch 2 does not establish Escape/J0-specific response. It does strengthen the carrier mechanism: target values survive while the local epistemic downgrade fails to become an inherited carrier.**

## 1. Structural distance

|Rep|S2 T10+ turns|S3 T10+ turns|S4 T10+ turns|S2-S3|S2-S4|S3-S4|
|---:|---:|---:|---:|---:|---:|---:|
|1|0|7|0|-7|+0|+7|
|2|0|2|2|-2|-2|+0|
|3|7|4|0|+3|+7|+4|

S2 does not separate consistently from matched controls: both primary contrasts change sign. The ordinary-control spread S3-S4 is itself large. No post-hoc total score is constructed.

## 2. Inheritance distance

|Condition|T10+ calls|Target-value output refs|Ref rate|Target-bearing state writes|
|---|---:|---:|---:|---:|
|S2|7|7|1.000|1|
|S3|13|12|0.923|2|
|S4|2|2|1.000|1|

Conditional on there being a downstream turn, target-value reuse is high for every arm. Therefore raw propagation counts must be separated from **opportunity to propagate**; T9 termination is not evidence that the target was semantically rejected.

## 3. Epistemic-authority transport

- T9 annotation visible: **9/9**.
- T9 target value referenced in output: **9/9**.
- T9 output explicitly retained `unconfirmed`: **0/9**.
- T10+ calls: **22**.
- T10+ target-value references: **21/22**.
- T10+ annotation still visible: **0/22**.
- T10+ original source-container `status=fact` visible: **22/22**.
- T10+ outputs explicitly retained `unconfirmed`: **0/22**.
- Direct write-back to the withdrawn leaf itself: **0**.

This is a clean **value/status decoupling**: the information value remains operationally available and is repeatedly reused, while the local epistemic downgrade is not externalized into a persistent downstream carrier. The old `inventory_stockout_assessment_v1` container and its `status=fact` metadata remain the observable carrier. This is stronger evidence for R6-B carrier identification than for R6-D specificity.

## 4. S2 anchor rerun

First-batch S2 T10+ turns: `[5, 7, 3]`
Second-batch S2 T10+ turns: `[0, 0, 7]`
Combined S2 persistence opportunity: **4/6** runs continued beyond T9.

The S2 anchor therefore ranges from immediate T9 termination to T16 censoring across repeated realizations. The first batch’s 3/3 post-withdrawal continuation is not a deterministic property of S2.

## 5. Why S3 matters

S3 opened a downstream coordination chain at T9 in **3/3** runs; S2 did so in **1/3**, S4 in **1/3**. Yet none of those S3 outputs explicitly said that B stock was `unconfirmed`. This makes S3 a strong warning against an Escape-specific interpretation: an ordinary matched stock downgrade can generate at least as much structural continuation as the J0 target.

A remaining non-exchangeability is now visible: A=1520 was already encoded as `preliminary_stock` and repeatedly described as `preliminary_unreconciled (1520 vs 2100)` before the intervention, while B=900 and C=3400 were ordinary stock facts. Same container/provenance/category therefore still does not match **prior epistemic state / novelty of downgrade / decision role**.

## R6 status after Batch 2

- **R6-A natural variability:** established as large from Batch 1; Batch 2 trajectories remain within the same broad continuation scale.
- **R6-B carrier:** strengthened. Persistent old source-container authority is directly localized.
- **R6-C intervention-related inertia beyond natural variability:** not established.
- **R6-D Escape/J0 specificity:** **NOT ESTABLISHED**; Batch 2 does not support upgrading the first-batch frozen target-response contrast.
- **CPR:** `NOT_ADJUDICATED`.

## Methodological consequence

Do not respond by adding arbitrary controls until one produces the preferred pattern. The informative result is that two separable quantities exist: **continuation opportunity** and **carrier inheritance conditional on opportunity**. The latter is currently much more stable than the former. Any next R6 analysis should preserve that separation.
