# Formal Batch001 — Measurement v2 Offline Replay Result

Date: 2026-09-15  
Measurement: `R234-MEASUREMENT-V2-v0.1`  
Status: LOCAL OFFLINE REPLAY PASS; REPOSITORY CI VALIDATION PENDING

## Source freeze

- Formal subject workflow run: `34970142001`
- Frozen artifact id: `10397420968`
- Artifact digest: `sha256:ea8ccab5fd890a94dc8e6db3f91f703f0eb09202c3a4278548ffcae0d33b64e5`
- Evidence batch: `94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`
- Subject reruns: **0**
- Paid evaluator calls: **0**

This replay does not alter frozen subject behavior or Reviewer A/B v1 annotations.

## Deterministic output

Output hash:

`9a2b966849f8b18fa553b2b425ff9723fe0d66c2b58e88260e29ad43e6f767f6`

Two independent local rebuilds produced the same output hash.

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

These are mapped from the existing semantic-blind structural feedback counter. The new layer adds interval events, calls, actors, state keys, token usage and R2 candidate membership, but does not classify correction, persistence, regeneration, amplification, laundering, normalization, legitimacy drift or black hole without semantic review.

### Reviewer v2 packets

- Target-local packets: **70**
- `same_response_actions` included: **0**
- Prior Reviewer A/B output included: **0**
- Expected mechanism→Authority mapping included: **0**
- Disagreement-selection status disclosed: **0**

The packet questions are framed as neutral boundary questions (`epistemic_boundary`, `goal_boundary`, `retrospective_boundary`) rather than asking the reviewer to search the trace directly for C/P/R labels.

## Important implementation refinement

Measurement v2 makes the machine/reviewer separation stricter than the initial planning draft:

- deterministic code may record a post-settlement certainty promotion;
- deterministic code does **not** emit `LEGITIMACY_REWRITE_CANDIDATE`, because retrospective legitimation requires natural-language interpretation;
- laundering/normalization remain Reviewer/R4 semantic outcomes;
- prediction itself is never machine-coded as C;
- invocation count itself is never machine-coded as P;
- reopening itself is never machine-coded as R.

## Current scientific status

No new semantic conclusion is produced by this replay. It establishes that the frozen Batch001 evidence can be deterministically transformed into the new R2 jump index, R3 lineage windows, R4 dynamics windows, and Reviewer v2 target-local packets without a subject rerun or paid API.

The next gate is repository CI replay and leakage/hash validation. A new blinded Reviewer v2 call remains unauthorized until that gate passes and paid review is explicitly approved.
