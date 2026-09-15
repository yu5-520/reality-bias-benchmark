# Independent Reviewer-v2 Replication Protocol v0.1

Date: 2026-09-15  
Status: **FROZEN DESIGN — NO PROVIDER/MODEL SELECTED; NO PAID CALL AUTHORIZED**

## 1. Purpose

The first full Reviewer-v2 pass over Formal Batch001 was a DeepSeek re-annotation/calibration under the revised semantic contract. Because the same model family supplied historical Reviewer B, that pass is not an independent Reviewer-v2 replication.

This protocol defines the next clean semantic validation layer:

> apply the already-frozen Reviewer-v2 measurement contract to exactly the same frozen 144-unit population using a **different model family from DeepSeek**, while keeping the new reviewer blind to all earlier semantic results.

The goal is not to recover positive C/P/R labels. The goal is to test whether the v2 boundary judgments reproduce when reviewer family changes while evidence, packet versions and semantic definitions remain fixed.

## 2. Frozen scientific object

Subject behavior is not rerun or modified.

Evidence batch:

`94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`

Replication population:

- R2: 70 / 70;
- R3: 70 / 70;
- R4: 4 / 4;
- total: **144 review units**.

Selection rule:

`FULL_FROZEN_BASE_POPULATION`

The replication must not select only historical disagreements, v1 positives, DeepSeek-v2 positives/negatives, or any result-dependent subset.

## 3. Exact packet / prompt freeze

Reviewer input versions remain unchanged from the first v2 pass.

### R2

- packet version: `R234-REVIEWER-V2-R2-COMPACT-PACKET-v0.1`
- packet file SHA256: `c23522f9916530b4a342c2fd4b2cc028bb8613d0b8626cdc0d76ed9bc1ded63f`
- prompt SHA256: `88cc842ea12030530abd43563b8d6c9d6fb82ef25f997bcd9f55831c4794a924`

### R3

- packet version: `R234-REVIEWER-V2-R3-COMPACT-PACKET-v0.2`
- packet file SHA256: `7cbe61987172f6dd2fa6f547766c145ddf8782d5fc7ec1bf3762b06fb0db0151`
- packet-set semantic hash: `b1abe2510bce774a3d9f5792aaa8353b60781090894c6ba0bade7d4f5955a765`
- prompt SHA256: `e3b2aaafb0ac344b9d92ce3b0c8e0b0dd1fe2693a78b773c5bb3afd8e432373d`

### R4

- packet version: `R234-REVIEWER-V2-R4-COMPACT-PACKET-v0.1`
- packet file SHA256: `fe0a7d24a2d8fa4f102da9883529bebbcef9be0397057f3b8a23230754ee393a`
- prompt SHA256: `626ace9b857e352380801eb4d125d387af97953ee184b692aa9981b0b2ed12af`

No prompt or packet may be edited after seeing the first DeepSeek-v2 result merely to increase agreement or recover mechanism prevalence.

## 4. Reviewer independence requirement

A run qualifies as **independent Reviewer-v2 replication** only if all of the following hold:

1. reviewer model family is different from DeepSeek;
2. the reviewer receives no earlier reviewer labels, rationales, aggregate counts or agreement statistics;
3. the reviewer receives no first-v2-pass outcome, including the zero-positive synthesis;
4. the reviewer receives no same-model v1→v2 transition analysis;
5. the reviewer receives no expected C/P/R→Authority mapping;
6. the reviewer receives no paper conclusion or current research-gate interpretation;
7. reviewer outputs are fully frozen before any comparison with historical or DeepSeek-v2 annotations.

A second DeepSeek run may be useful for repeatability, but it must be named **same-family repeatability/re-annotation**, not independent replication.

The current interactive GPT-5.6 Sol conversation must also not be used as the blind independent reviewer because this conversation has already observed the DeepSeek-v2 result and the paper hypotheses.

## 5. Blind workspace allowlist

The independent reviewer workspace may contain only:

- the exact R2/R3/R4 packet files listed above;
- the exact R2/R3/R4 frozen prompts listed above;
- a sanitized expansion corpus containing only frozen subject event/call records explicitly referenced by packet `context_expansion.allowed_refs`;
- reviewer transport/runtime code needed to send packets and validate schema;
- a provider/model configuration that contains transport and cost metadata but no study results.

The workspace must not contain historical or current review-result directories, analysis summaries, paper/change-note conclusions or transition reports.

## 6. Explicit blinded exclusions

The independent reviewer must be blind to at least:

- `reviews/formal_batch001_model_review_v1/`;
- `reviews/formal_batch001_blind_deepseek_v1/`;
- `results/formal_batch001_measurement_v2/reviewer_v2_deepseek_round001_summary.json`;
- the complete Reviewer-v2 round-001 artifact from workflow `34993941914`;
- `theory/change_notes/CN-R-034*`;
- `theory/change_notes/CN-R-035*`;
- `theory/change_notes/CN-R-042*`;
- `theory/change_notes/CN-R-043*`;
- `docs/R234_same_model_v1_v2_measurement_transition.md`;
- any A/B agreement report;
- any text stating historical or v2 C/P/R prevalence;
- any text stating that the first v2 pass produced zero C/P/R positives;
- current manuscript claims or expected Authority-route hypotheses.

## 7. Bounded expansion rule

The packet remains the default evidence surface.

If the reviewer cannot resolve a semantic field from the compact packet, it may request at most one expansion using an exact ref in that packet's `context_expansion.allowed_refs`.

The expansion corpus must return the exact frozen subject record bound to that ref. It must not inject reviewer history, inferred context, adjacent paper claims or a hand-written explanation.

A semantically valid `UNCERTAIN` is final and is not retried to force a more decisive answer.

## 8. Output contract

Use the same frozen Reviewer-v2 boundary schemas:

- `schemas/reviewer_v2_r2_boundary_record_v0.1.schema.json`
- `schemas/reviewer_v2_r3_boundary_record_v0.1.schema.json`
- `schemas/reviewer_v2_r4_boundary_record_v0.1.schema.json`

After all independent boundary records are frozen, run the existing deterministic mechanism synthesizer:

`R234-MECHANISM-SYNTHESIS-v0.1`

The synthesizer must not be changed in response to the new review output before cross-review comparison.

## 9. Comparison plan

Only after the independent 144-unit annotation is frozen may it be compared with the DeepSeek-v2 pass.

Primary comparison objects are the boundary fields, not only final C/P/R labels.

Report at minimum:

- R2 epistemic-transition agreement;
- R2 goal-relation agreement;
- R2 goal-focus agreement;
- R2 retrospective-outcome agreement;
- R2 authorization agreement;
- R3 semantic-adoption agreement;
- R3 decision-effect agreement;
- R3 lineage-outcome agreement;
- R4 correction/persistence/regeneration/amplification/laundering/normalization/black-hole agreement;
- deterministic C/P/R synthesis agreement;
- disagreement taxonomy with evidence refs.

Raw agreement and contingency counts are mandatory. Cohen κ may be reported only where marginals make it interpretable; zero-positive or highly degenerate marginals must be explicitly flagged rather than advertised as meaningful reliability evidence.

## 10. What replication can and cannot establish

A high-agreement independent v2 replication would support the reproducibility of the refined semantic contract on this frozen Base batch.

A low-agreement replication would indicate that semantic ambiguity remains even after the v2 refinement and would motivate measurement-contract analysis before further subject scaling.

Agreement on zero positives would still not establish universal absence of C/P/R because the subject sample is only N=3 in one e-commerce task family.

Disagreement must not trigger silent changes to the frozen subject trace or retroactive overwriting of either reviewer layer.

## 11. Provider/model gate

Current state:

`NOT_SELECTED`

No different-family reviewer API is currently frozen in the repository for this replication.

Before a paid independent run, a separate launch candidate must freeze:

- provider/model family;
- exact returned-model allowlist;
- configuration hash;
- pricing snapshot;
- hard spend ceiling;
- retry/expansion policy;
- exact blind-bundle hash;
- explicit user authorization.

Until then provider calls remain blocked.

## 12. K=2 gate

K=2 remains blocked.

Independent v2 replication and/or additional unchanged-Base sampling must resolve the Base measurement question before upper-bound loop-budget escalation.
