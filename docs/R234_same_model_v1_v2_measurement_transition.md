# Formal Batch001 — Same-Model Reviewer v1→v2 Measurement Transition

Date: 2026-09-15  
Status: **OFFLINE COMPARISON COMPLETE — MEASUREMENT-CONTRACT SENSITIVITY, NOT INTER-RATER RELIABILITY**

## 1. Why this comparison matters

Historical Reviewer B and the first Reviewer-v2 pass both use the DeepSeek model family over the same frozen 70 Authority-bearing events from Formal Batch001.

That creates a useful stress test:

> What happens when the underlying subject evidence and reviewer model family are held approximately constant, but the semantic measurement contract is changed?

The answer is: **the labels change dramatically**.

This does not isolate rubric wording as the only cause. The v2 system also changes packet construction, prompt wording, evidence-window design and output schema. Therefore the correct name is **measurement-contract sensitivity**, not pure rubric causality.

It is also not inter-rater reliability because the reviewer family is intentionally reused rather than independently varied.

## 2. Frozen inputs

Evidence batch:

`94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`

Historical v1 source:

`reviews/formal_batch001_blind_deepseek_v1/review_records.jsonl`

Reviewer-v2 source:

workflow `34993941914`, artifact `10407112876`.

Offline transition workflow:

`34995630944`

Transition artifact:

- ID: `10407228786`
- digest: `sha256:1135b79bf99fc7aa57d65c46f36665d64205f8dbeeab3f1051f3ca4e34cca47b`

All 70 event keys align exactly between v1 and v2.

## 3. Headline transition

Historical DeepSeek Reviewer-B v1 labeled **61/70 events** with at least one C/P/R mechanism.

Mechanism-positive counts were:

- C: 24
- P: 25
- R: 25

The v1 primary estimand contained **26 realized + unauthorized + mechanism-coded events**.

Under Reviewer-v2 deterministic synthesis over the same event population:

- C positive: **0**
- P positive: **0**
- event-level R positive: **0**

This is too large a shift to treat semantic coding as a passive observation layer. The measurement contract materially changes what counts as the phenomenon.

## 4. Completion transition

Among the **24 events labeled C in v1**:

- 22 → `NO_PROMOTION`
- 2 → `SUPPORTED_PROMOTION`
- 0 → `UNSUPPORTED_PROMOTION`

This is exactly the boundary introduced by C v2.

v1 could treat completion/filling behavior as evidence of Completion Bias. v2 instead asks whether the epistemic or execution state actually became stronger than the evidence allowed.

Thus a forecast, estimate, recommendation or provisional value may be propagated and used while remaining non-C.

The transition supports the distinction:

> **information completion ≠ unauthorized epistemic promotion**.

## 5. Perfection transition

Among the **25 events labeled P in v1**:

- 22 → `NECESSARY_DECOMPOSITION`
- 3 → `ORIGINAL_GOAL`
- 0 → `UNAUTHORIZED_EXPANSION`

All 70 v2 targets are `NO_MATERIAL_SHIFT` with respect to goal focus.

This directly tests the refined P definition.

v1 frequently reasoned from collaboration shape: repeated specialist invocation, confirmation, additional checks or apparent completeness-seeking. v2 instead asks which **goal** the behavior serves.

The same behavior can therefore be complex and multi-Agent without being P if it remains inside the authorized closure of the original task.

The transition supports the distinction:

> **behavioral expansion ≠ goal-scope expansion**.

## 6. Retrospective transition

Among the **25 events labeled R in v1**:

- 15 → `NOT_REWORK`
- 10 → `CORRECTION`
- 0 → `REGENERATION_C`
- 0 → `REGENERATION_P`

Reviewer-v2 does identify one `LEGITIMATION_CANDIDATE` elsewhere in the full R2 population, but R4 does not confirm laundering or normalization.

The important change is that revision/reopening/rechecking is no longer itself Retrospective Bias.

The transition supports the distinction:

> **rework ≠ retrospective penetration**.

R requires the rework process to regenerate C/P or to grant an unresolved C/P state greater legitimacy.

## 7. What happened to the historical primary 26 events?

The strongest historical DeepSeek-v1 subset was the 26 events that were simultaneously:

- realized;
- mechanism-coded;
- judged unauthorized.

Under v2 those same 26 events become:

### Epistemic boundary

- 16 `NOT_APPLICABLE`
- 7 `NO_PROMOTION`
- 3 `SUPPORTED_PROMOTION`
- 0 unsupported promotion

### Goal boundary

- 21 `NECESSARY_DECOMPOSITION`
- 5 `ORIGINAL_GOAL`
- 0 unauthorized expansion

### Goal focus

- 26 `NO_MATERIAL_SHIFT`

### Retrospective boundary

- 21 `NOT_REWORK`
- 3 `CORRECTION`
- 1 `LEGITIMATION_CANDIDATE`
- 1 `NOT_APPLICABLE`

### Authorization

- 26 `AUTHORIZED`

No event in the historical primary-26 set synthesizes to a positive v2 C/P/R mechanism.

## 8. Authorization transition

Historical Reviewer-B v1 authorization:

- AUTHORIZED: 42
- UNAUTHORIZED: 27
- NOT_APPLICABLE: 1

Reviewer-v2 authorization:

- AUTHORIZED: 70

Transitions:

- 42 AUTHORIZED → AUTHORIZED
- 27 UNAUTHORIZED → AUTHORIZED
- 1 NOT_APPLICABLE → AUTHORIZED

This should not be read as evidence that “authorization does not matter.” It shows that the v1 authority judgment mixed behavioral necessity/completeness judgments with the semantic bias boundary more heavily than the v2 contract does.

In v2, semantic mechanism and Authority realization are deliberately separated.

## 9. Agreement statistics are not the main object here

If v1 mechanism labels are binarized against v2 synthesized mechanism presence, raw agreements are:

- C: 0.6571
- P: 0.6429
- R: 0.6429

Cohen κ is 0 for each mechanism because the v2 marginal contains zero positives. This is a prevalence-degenerate situation and is **not** a useful substantive reliability statistic.

The central quantity here is the **transition structure**, not κ.

## 10. Scientific implication

The comparison gives the paper a stronger measurement argument than simple reviewer disagreement.

Historical A/B disagreement showed that different reviewers apply broad semantic labels differently.

The same-model v1→v2 transition now shows that even approximately holding reviewer family constant does not stabilize labels when the operational definition changes.

That means semantic operationalization must be treated as part of the measurement apparatus:

`observed trace → structural candidate → semantic contract → reviewer judgment → deterministic mechanism synthesis`

not as:

`observed trace → obvious C/P/R truth`.

This strengthens the rationale for keeping the trace immutable while allowing semantic annotations to be versioned and revisable.

## 11. What this comparison does not prove

It does **not** prove:

- every v1 label was false;
- v2 is automatically correct because it is newer;
- C/P/R cannot emerge in the Arena;
- Reality Bias prevalence is zero;
- the same model instance was bit-identical across v1/v2 calls.

Packet design, prompt wording and review schema changed together with the operational definitions. The v2 zero-positive finding still needs independent replication.

## 12. Current implication for the experiment plan

Do not loosen the v2 definitions to recover the old positive rate.

Do not start K=2 merely because v1 previously showed many positives.

The immediate scientific gate is to distinguish two possibilities:

1. **measurement correction:** v1 substantially over-counted ordinary prediction, decomposition and rework, while v2 correctly identifies no CPR in Batch001;
2. **measurement over-tightening / sample insufficiency:** v2 boundaries are valid in principle, but the current reviewer or N=3 Base sample is too limited to establish mechanism realization.

The clean ways to separate those possibilities are:

- independent Reviewer-v2 replication on the same frozen evidence; and/or
- additional Base subject sampling under the unchanged Arena, followed by the frozen v2 measurement system.

K=2 remains blocked until the Base measurement question is resolved.
