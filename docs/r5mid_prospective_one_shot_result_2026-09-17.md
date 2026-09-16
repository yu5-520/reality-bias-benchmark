# R5-MID Prospective One-Shot — Formal Run Result

Date: 2026-09-17  
Workflow run: `35132777581`  
Status: SUBJECT EVIDENCE FROZEN / v0.4 THREE-LAYER DERIVATION COMPLETE / SEMANTICS NOT ADJUDICATED

## 1. Execution result

The formal prospective one-shot run completed successfully under the user-authorized envelope:

- total ceiling: 1 USD;
- per-branch ceiling: 0.25 USD;
- per-branch max calls: 64;
- 2 matched replicate pairs / 4 continuations;
- all 4 continuations: `RUN_COMPLETE`;
- runner errors: 0;
- integrity failures: 0;
- estimated total spend: `0.017197464 USD` (engineering estimate, not provider invoice);
- paid evaluator: not called.

Raw evidence was frozen and uploaded before derived analysis.

Evidence batch hash:

`244d10dfd7655eef7ac99db4731e85daab62fe9a2546b89e7d27720fbb8c20f7`

## 2. Intervention integrity

The real run satisfied the one-shot invariant:

```text
same frozen parent
A: no experiment-origin exposure
B: first resumed prompt sees fact -> unconfirmed exactly once
   -> overlay consumed
   -> no experiment-origin reinjection
   -> persistent Arena state unchanged by experiment
```

Observed direct experiment-origin exposures:

- pair1 A: 0
- pair1 B: 1
- pair2 B: 1
- pair2 A: 0

This establishes experimental-delivery integrity, not semantic CPR or a causal conclusion.

## 3. Pair 1 — realized structural contrast

### Layer 1: Jump recurrence

- control descendant re-Jumps: `1`
- intervention descendant re-Jumps: `3`
- first re-Jump distance in both: `8` behavior events / `1` turn
- first re-Jump lineage depth in both: `3`

### Layer 2: inherited inertia

- common canonical prefix: `1` event
- first structural divergence: immediately after that shared prefix
- post-exposure edge-set overlap: `0.25`
- control root-reachable events: `5`
- intervention root-reachable events: `9`
- root reach depth: `3` vs `3`
- first later canonical-signature reconvergence exists, but at different positions (`control index 3`, `intervention index 7`); this is not full-state equality.

### Layer 3: path topology

- control observed root path families: `2`
- intervention observed root path families: `4`
- path-family Jaccard: `0.20`
- edge-set Jaccard: `0.25`
- control/intervention branch nodes: `1 / 1`
- control/intervention merge nodes: `0 / 1`

Pair 1 therefore realizes a broader intervention continuation at the frozen root, but this direction is not treated as a general treatment effect.

## 4. Pair 2 — realized structural contrast

### Layer 1: Jump recurrence

- control descendant re-Jumps: `5`
- intervention descendant re-Jumps: `1`
- first re-Jump distance in both: `8` behavior events / `1` turn
- first re-Jump lineage depth in both: `3`

### Layer 2: inherited inertia

- common canonical prefix: `1` event
- first structural divergence: immediately after that shared prefix
- post-exposure edge-set overlap: `0.0652`
- control root-reachable events: `34`
- intervention root-reachable events: `5`
- control/intervention depth: `6 / 3`
- control-only affected Agents: `ads`, `inventory`; `ops_lead` is shared
- control/intervention descendant cross-Agent relations: `17 / 1`

### Layer 3: path topology

- control observed root path families: `149`
- intervention observed root path families: `2`
- path-family Jaccard: `0.0`
- edge-set Jaccard: `0.0652`
- control/intervention branch nodes: `10 / 1`
- control/intervention merge nodes: `7 / 0`
- control/intervention role re-entry candidates: `1 / 0`

Pair 2 realizes the opposite directional pattern from Pair 1: the intervention continuation is structurally narrower than control.

## 5. What the two pairs jointly show — and do not show

The strongest current observation is **not** that the one-shot treatment makes the system larger or smaller.

The two matched repeats point in opposite directions:

```text
Pair 1: B broader than A
Pair 2: B narrower than A
```

At the same time, both pairs:

- start from the same frozen parent;
- diverge structurally immediately after a one-event shared prefix;
- produce a downstream descendant re-Jump one turn later;
- later exhibit some canonical-signature reconvergence;
- preserve valid one-shot exposure integrity.

This is compatible with the research design's non-directional mechanism view: a local perturbation may reorganize realized paths rather than monotonically reduce or increase reach. But two pairs are insufficient to separate treatment-linked reorganization from the large conditional stochastic variability of the model. Provider hidden state was not replayed, and same-parent repeats are not independent samples.

Accordingly, the present evidence supports **observed paired structural reorganization**. It does not yet support a stable directional treatment effect or a generalized causal law.

## 6. Process vs terminal outcome

All four continuations converged on the same core operational decision:

- allocation: `A 45,000 / B 30,000 / C 75,000 CNY`;
- expected blended ROAS: `3.33`;
- promo depth: `A 8% / B 5% / C 8%`.

The exact final answer strings were not identical in all four runs, but their core decision was the same. Meanwhile the process structures differed sharply — most clearly in Pair 2, where the root path-family count was `149` vs `2` and root-reachable events were `34` vs `5`.

This is a concrete example of why terminal output alone is insufficient to describe the observed system process. It remains a descriptive Process Reality observation; task correctness and CPR semantics are still separate adjudication questions.

## 7. Current evidence status

- structural Jump root: resolved;
- one-shot delivery: verified;
- raw evidence: frozen before derivation;
- Layer 1/2/3 measurements: complete for both pairs;
- path-family overflow: false for all compared branches;
- integrity failures: 0;
- semantic CPR: `NOT_ADJUDICATED`;
- semantic recovery: `NOT_ADJUDICATED`;
- semantic authority/responsibility crossing: `NOT_ADJUDICATED`;
- paid evaluator: not used.

Primary provenance:

`manifests/r5mid_prospective_one_shot_run_35132777581_record.json`

## 8. Next scientific step

Do not rerun these four branches to obtain a preferred direction.

The next useful expansion is additional preregistered same-parent matched pairs and then additional distinct prospective natural parents. The purpose is to estimate conditional path-family variability and ask whether the one-shot perturbation changes the **distribution of process structures**, rather than forcing a monotonic `B < A` or `B > A` result.

Semantic CPR adjudication can proceed asynchronously on the already-frozen evidence and must not rewrite the structural traces.
