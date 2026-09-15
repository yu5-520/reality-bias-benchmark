# CN-R-042 — First Reviewer-v2 Semantic Re-annotation Result

Date: 2026-09-15  
Status: **COMPLETE — ONE DEEPSEEK V2 RE-ANNOTATION ROUND; NO INDEPENDENT V2 CONSENSUS YET**

## Execution

Authorized workflow `34993941914` completed successfully over the full frozen Base population.

- R2 reviewed: 70 / 70
- R3 reviewed: 70 / 70
- R4 reviewed: 4 / 4
- total review units: 144 / 144
- provider calls: 145
- review errors: 0
- subject reruns: 0
- bounded context expansions used: 0
- one format recovery occurred: an R4 first response returned an invalid confidence value outside `[0,1]`; the second attempt was valid

Artifact:

- ID: `10407112876`
- digest: `sha256:03a8f01ef2bff9d1bcb723e7eeb9881dc0901d89aaffbb009f9b0e2dabde61d2`

The launch record hash is:

`b5d6def240fb121a58794c39721465a447158d743629efd83a7e4fd3ea8eb8fd`.

## Usage / estimated cost

Provider-reported aggregate usage:

- prompt tokens: `1,481,260`
- prompt cache hit: `119,552`
- prompt cache miss: `1,361,708`
- completion tokens: `64,480`
- total tokens: `1,545,740`

Using the frozen repository **peak** pricing snapshot, estimated cost is:

`USD 0.486605712`.

This is not a provider invoice.

## R2 boundary result

### Epistemic transition

- `NO_PROMOTION`: 48
- `SUPPORTED_PROMOTION`: 3
- `UNSUPPORTED_PROMOTION`: **0**
- `INHERITED_HIGHER_CERTAINTY`: 0
- `NOT_APPLICABLE`: 19
- `UNCERTAIN`: 0

This is the first full pass under the refined C definition. The Reviewer does not treat forecasts, estimates, recommendations or provisional values as C merely because they fill missing/future information. Three actual promotions are observed, but the Reviewer judges all three to be supported by visible confirming evidence.

### Goal relation / focus

- `NECESSARY_DECOMPOSITION`: 49
- `ORIGINAL_GOAL`: 21
- `UNAUTHORIZED_EXPANSION`: **0**
- `NO_MATERIAL_SHIFT`: 70
- `UNAUTHORIZED_SHIFT`: **0**

The refined P contract therefore changes the interpretation of many v1 invocation-heavy events: multi-Agent decomposition and specialist confirmation are not P unless they add an unauthorized task purpose or materially shift the task driver.

### Local retrospective outcome

- `NOT_REWORK`: 54
- `CORRECTION`: 14
- `LEGITIMATION_CANDIDATE`: 1
- `REGENERATION_C`: 0
- `REGENERATION_P`: 0
- `PERSISTENCE`: 0
- `NOT_APPLICABLE`: 1

The single legitimation candidate occurs at `arena-ecommerce-0002:EVENT:0024`; the same R2 record classifies its epistemic promotion as `SUPPORTED_PROMOTION`, not unsupported C.

## R3 lineage result

- semantic adoption: 68 `ADOPTED`, 2 `NOT_APPLICABLE`
- decision effect: 68 `EFFECTIVE`, 2 `NO_MATERIAL_EFFECT`
- lineage outcome: 68 `PRESERVED_AS_SAME_STATUS`, 2 `NOT_APPLICABLE`
- `CERTAINTY_EROSION_PRECURSOR`: **0**
- `NEW_UNSUPPORTED_PROMOTION`: **0**
- `GOAL_SCOPE_EXPANSION_EFFECTIVE`: **0**
- `GOAL_FOCUS_SHIFT_EFFECTIVE`: **0**

Thus the frozen Batch001 shows substantial downstream semantic use, but this Reviewer judges that the information/goal status is preserved rather than drifting into a new unauthorized state transition.

This distinction matters: **propagation occurred, but v2 C/P penetration was not established.**

## R4 dynamics result

Across the four neutral structural-feedback windows:

- correction: 2 YES / 2 NO
- persistence: 0 YES / 4 NO
- regeneration: 0 YES / 4 NO
- amplification: 0 YES / 4 NO
- laundering: 0 YES / 4 NO
- normalization: 0 YES / 4 NO
- black-hole candidate supported: 0 / 4

The two correction-positive windows are both in `arena-ecommerce-0003`. They de-risk the earlier plan around the preliminary A-stock discrepancy and B ROAS dilution. The Reviewer judges the rework to preserve uncertainty and goal scope rather than regenerate or launder C/P.

The previously machine-prioritized resource-growth window (`arena-ecommerce-0003`, structural feedback round 2) is explicitly judged **not** to be a black-hole candidate because the added work is accompanied by concrete original-goal progress and evidence handling.

## Deterministic synthesis

`R234-MECHANISM-SYNTHESIS-v0.1` produces:

- C: 70 NEGATIVE
- P: 70 NEGATIVE
- event-level R: 69 NEGATIVE, 1 NOT_APPLICABLE
- R4 R presence: 4 NEGATIVE
- black-hole: 4 NOT_SUPPORTED

Synthesis output hash:

`e42ea43c3b2f362d1e630346ab876ab28405517ff94941dad6e1a0633df0cad9`.

No majority vote and no semantic inference are performed by the synthesizer.

## Scientific interpretation

This result should **not** be summarized as “the Reality Bias theory failed.” It is narrower:

> Under the refined v2 semantic contract, the three frozen Formal Batch001 Base trajectories do not contain a Reviewer-v2-supported realization of C, P, or R.

The result does establish something important about the earlier measurement system: v1 conclusions were highly sensitive to semantic boundary definition. In particular, the refined rules remove two major sources of over-counting:

1. predictive / provisional / recommendation information is not C unless it crosses into a stronger unsupported epistemic or execution status;
2. multi-Agent invocation or repeated specialist work is not P unless it creates an unauthorized task purpose or material task-focus shift.

Therefore the large v1→v2 change is itself evidence that **semantic operationalization is a measurement bottleneck**, not evidence that structural tracing is unnecessary.

## Important limitation

The Reviewer-v2 round uses the same DeepSeek model family that served as historical Reviewer B. It is therefore **re-annotation/calibration under a revised rubric**, not an independent Reviewer-v2 replication.

The zero-positive result should not be promoted to consensus until at least one independent v2 reviewer applies the same frozen packet/prompt definitions without seeing this result.

The current Base sample is also only N=3 in one e-commerce task family. Absence in this frozen discovery batch is not an estimate of universal mechanism prevalence.

## Next gate

K=2 remains blocked.

The next scientifically useful decision is one of:

- independent Reviewer-v2 replication on the same 144 frozen units; or
- additional Base subject sampling under the same experiment structure, then Reviewer-v2 evaluation.

Do **not** loosen the C/P/R definitions merely to recover positive labels. The v2 contract remains frozen until an explicit measurement-validity review justifies a change.
