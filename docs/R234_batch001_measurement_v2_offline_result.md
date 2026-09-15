# Formal Batch001 — Measurement v2 Offline Replay Result

Date: 2026-09-15  
Measurement: `R234-MEASUREMENT-V2-v0.1`  
Status: **OFFLINE MEASUREMENT / COVERAGE / REVIEW-PACKET CI PASS; SEMANTIC REVIEW NOT RUN**

## Source freeze

- Formal subject workflow run: `34970142001`
- Frozen artifact id: `10397420968`
- Artifact digest: `sha256:ea8ccab5fd890a94dc8e6db3f91f703f0eb09202c3a4278548ffcae0d33b64e5`
- Evidence batch: `94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`
- Subject reruns: **0**
- Paid evaluator calls: **0**

This replay does not alter frozen subject behavior or Reviewer A/B v1 annotations.

## Deterministic Measurement v2 output

Output hash:

`9a2b966849f8b18fa553b2b425ff9723fe0d66c2b58e88260e29ad43e6f767f6`

Local rebuild and repository CI rebuild reproduce the same hash.

Repository validation workflow:

- workflow: `R2-R4 Measurement v2 Offline Validate`
- successful run: **`34988379906`**
- successful head: `02171451f7d6c2916bd2015d717fbb416d86c71d`
- output artifact id: **`10404238594`**
- artifact name: `r234-measurement-v2-offline-34988379906`
- artifact digest: **`sha256:1c54a0fd2b6c8a0c063bb869c1e340a0a56e83be6bd27afe73ce9d09b02e42ac`**
- artifact expiry: `2026-12-14T15:25:46Z`

All unit tests, frozen-artifact download, deterministic rebuild, evidence-hash checks, packet leakage checks, target-local checks, v1 coverage diagnostic and artifact upload passed.

### R2 structural index

- Authority-bearing structural candidates: **70**
- Realized structural effects: **68**
- Non-realized Authority attempts: **2**
- State-write candidates: **40**
- Invocation-expansion candidates: **22**
- Final-revision candidates: **8**
- High-certainty state-write candidates: **6**
- Explicit same-key epistemic-status jump candidates: **3**
- Post-settlement certainty-promotion candidates: **4**
- Repeated specialist-invocation candidates: **10**
- Pending-duplicate invocation candidates: **9**

These counts are a structural search-space index, not C/P/R prevalence.

The index deliberately does **not** call a new `ABSENT -> fact` field an epistemic jump. It is recorded as a high-certainty write requiring semantic review. A deterministic `EPISTEMIC_STATUS_JUMP_CANDIDATE` requires an explicit previously recorded status for the same key and a later upward status transition. This prevents the machine from inventing a semantic source relation that is not structurally recorded.

### R3 windows

- Lineage windows: **70**

R3 uses recorded message/state/final-version relations to identify visibility/read/version lineage. `semantic_adoption`, `decision_effective`, `penetration_range`, `goal_scope_effective`, and `goal_focus_effective` remain `NOT_ADJUDICATED`.

### R4 windows

- Neutral structural feedback windows: **4**

These are mapped from the existing semantic-blind structural feedback counter. The layer adds interval events, calls, actors, state keys, token usage and R2 candidate membership, but does not classify correction, persistence, regeneration, amplification, laundering, normalization, legitimacy drift or black hole without semantic review.

## Reviewer v2 packet materialization

R3/R4 semantic-review material was then materialized and independently validated offline.

Reviewer-packet workflow:

- workflow: `R2-R4 Reviewer v2 Packets Offline Validate`
- successful run: **`34988452980`**
- successful head: `f2cdb4f9a3eb1f7c95cd32a595ddc665ec1e6c34`
- artifact id: **`10404024120`**
- artifact name: `r234-reviewer-v2-packets-offline-34988452980`
- artifact digest: **`sha256:bb1c436d062ea5820127c2b56a906042a6e9834689eb3939141e389698b388dc`**
- artifact expiry: `2026-12-14T15:26:25Z`
- reviewer-packet output hash: **`e8b7d3cc7d09a2bc629ed95ac130e8d9aac737bb904229171b61f21979fff5f6`**

Materialized output:

- R3 reviewer packets: **70**
- R4 reviewer packets: **4**
- prior Reviewer A/B output included: **false**
- expected mechanism mapping included: **false**
- disagreement selection disclosed: **false**
- paper claims included: **false**
- semantic labels present: **false**
- paid API calls: **0**

One R4 interval is marked `BLACK_HOLE_REVIEW_CANDIDATE` because the second structural feedback round in `arena-ecommerce-0003` shows structural resource/intensity growth relative to its previous round: tokens per call rose by about **45.7%** and tokens per event by about **99.8%**. This is **not** a black-hole finding. The same interval has fewer model calls, actors and state keys than the prior round, and original-goal progress / verified-evidence value remain semantically unadjudicated. It is only a machine-generated window that deserves semantic review.

## Reviewer v2 R2 packets

- Target-local R2 packets: **70**
- `same_response_actions` included: **0**
- Prior Reviewer A/B output included: **0**
- Expected mechanism→Authority mapping included: **0**
- Disagreement-selection status disclosed: **0**

The packet questions are framed as neutral boundary questions (`epistemic_boundary`, `goal_boundary`, `retrospective_boundary`) rather than asking the reviewer to search the trace directly for C/P/R labels.

## V1 annotation coverage diagnostic

Measurement v2 was compared with frozen Reviewer A/B v1 only as an **index-coverage diagnostic**, never as adjudication and never by treating v1 labels as ground truth.

Coverage-analysis version: `R234-V2-V1-COVERAGE-ANALYSIS-v0.1`  
Frozen analysis hash: `ad2951dfc5eaa73ab1335a409457531e2817268640c369a412b345ca2929f191`

Results:

- old reviewed Authority events covered by Measurement v2 target index: **70/70**
- old reviewed events covered by Reviewer v2 target-local packets: **70/70**
- old A/B disagreement events covered: **54/54**
- Reviewer A historical primary-like count reconstructed: **16**
- Reviewer B historical primary-like count reconstructed: **26**

The structural alignment is diagnostically useful but is not a new semantic result. For example, all three Reviewer-A C events fall on state writes and all three are high-certainty writes, while only one is an explicit same-key structured status jump. Reviewer-B C is much broader across write-state, invocation and final-revision actions. Likewise, Reviewer-A P is entirely invocation-shaped, whereas Reviewer-B P also includes state and revision targets. These patterns support the need for the new boundary review, but do not by themselves prove which old labels are right or wrong.

## Important implementation refinement

Measurement v2 makes the machine/reviewer separation stricter than the initial planning draft:

- deterministic code may record a post-settlement certainty promotion;
- deterministic code does **not** emit semantic retrospective legitimation merely from structure;
- laundering/normalization remain Reviewer/R4 semantic outcomes;
- prediction itself is never machine-coded as C;
- invocation count itself is never machine-coded as P;
- reopening itself is never machine-coded as R;
- visibility/read/version lineage is never auto-promoted to semantic adoption or decision effect.

## Validation incident log

Coverage workflow run `34988224457` failed only at the frozen coverage-hash assertion. The coverage analyzer itself completed and returned the expected event/count structure, but its repository-frozen wording differed from the local prototype used to precompute the expected hash. The repository output hash `ad2951df...` was then frozen and the workflow rerun. No provider API or subject call occurred in the failed attempt. The corrected run `34988379906` passed all gates.

## Current scientific status

No new semantic C/P/R conclusion is produced by these offline runs. What is now established is an engineering/methodological capability:

`frozen Batch001 trace -> R2 structural jumps -> R3 lineage windows -> R4 dynamics windows -> target/range-local Reviewer v2 packets`

The pipeline is deterministic, hash-checked, leakage-checked, and requires no subject rerun or paid evaluator.

The remaining Base gate is now **semantic boundary review under Reviewer System v2**. That review must inspect the actual Agent inputs/outputs and decide whether the machine-defined windows contain effective C/P/R authority penetration. A new paid blinded Reviewer v2 call is still **not authorized by this result**; it requires explicit spend authorization. Human inter-rater reliability remains unmeasured.
