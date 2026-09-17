# R5-R6 Specificity Exact-Source Audit — 2026-09-17

Status: **R6-D OFFLINE SOURCE AUDIT + ATOMIC OPERATOR READY / NO SUBJECT RUN AUTHORIZED**

## 1. Role under Process Reality v4.5

This audit is the exact-source preparation layer for **R6-D Target Specificity**. It is not a new R stage.

The scientific question is:

> Is the J0-targeted post-consumption system-inertia response structurally distinguishable from the generic response to making an ordinary factual information item uncertain once?

The primary future contrast remains `S2 - S1`. The primary readout remains the **post-consumption R6 system-inertia profile**, not immediate activity volume.

## 2. Frozen source binding

The audit uses the frozen R5-MID raw artifact from workflow `35132777581`.

| Field | Value |
|---|---|
| Evidence batch hash | `244d10dfd7655eef7ac99db4731e85daab62fe9a2546b89e7d27720fbb8c20f7` |
| Raw traces SHA256 | `102089199c7e1292e80444e339b84b00d2124e298f9ab849844dda0116473ef7` |
| Common parent state hash | `aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c` |
| Source plan hash | `a24c98901422bbccfc9a040a6bc14575b1c710edd518c0d9c2facf7a57926351` |
| Source measurement hash | `5ec7953b473e4d7b29612de18aac9992238e722e1b12ea7c6999929958b24191` |
| Control T9 prompt hash | `3152c87e0238f6cf033badd6e8ecfc01ff2e713d1d64dee2108c300f28e65225` |
| Control T9 runtime snapshot hash | `776892d1214693dae2880fe197068da6dcc727974529e87e7960251f16fb67bf` |
| J0 event | `E32` |
| J0 state key | `inventory_stockout_assessment_v1` |
| J0 acquired container status | `fact` |

## 3. Exact-source finding

At the frozen `after_turn:8` parent, `shared_state_metadata` contains only one non-initial entry with status `fact`:

`inventory_stockout_assessment_v1.status = fact`

Other material shared-state entries are `recommendation`, `unspecified`, or `initial`.

Therefore an honest S1 control cannot be produced by pretending that a second non-J0 top-level shared-state field already had equivalent `fact` status.

The prospective specificity unit was therefore changed **before any scientific S-arm outputs existed** from top-level state-key matching to **atomic prompt-visible factual information**.

## 4. R6-D condition namespace

Canonical forward condition IDs are:

- `S0_NATURAL_REFERENCE`
- `S1_MATCHED_OR_ORDINARY_FACTUAL_INFORMATION_DOWNGRADE`
- `S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL`

The `S` namespace is reserved for R6-D target specificity.

R7 continues to use the separate `C1/C2/C3` structural-handling namespace. S/C aliasing is forbidden.

## 5. S1 eligible pool and outcome-blind selection

The first control pool uses ordinary atomic task facts that are:

- already visible to the resumed Operations Lead;
- source-backed by task public context;
- factual rather than recommendation/provisional text;
- non-J0 targets;
- outside the direct inventory/stockout semantic family for the first generic-uncertainty control;
- scalar and addressable by a stable locator;
- selected before any scientific S-arm outcomes exist.

Frozen pool rule:

`PUBLIC_CONTEXT_PRODUCT_SCALAR_NON_INVENTORY_FAMILY_v1`

Eligible pool size: `9`.

Selection rule:

`PARENT_HASH_SEEDED_LEXICOGRAPHIC_INDEX_v1`

Frozen seed hash:

`7347944910449db5d12de365c29131dc86b094dee8c34cf0da53de3ed09ccbc3`

Selected index: `7` zero-indexed.

Frozen S1 target:

`public_context.products.C.gross_margin_pct = 35`

This selection is outcome-blind and may not be replaced after S-arm outcomes are observed.

## 6. S2 exact target

Frozen S2 target:

`shared_state.inventory_stockout_assessment_v1.A.preliminary_stock = 1520`

The exact source signal originated as:

`preliminary_unreconciled`

and later entered `inventory_stockout_assessment_v1` when that containing state acquired status:

`fact`

The prospective S2 intervention withdraws the acquired factual authority of this exact atomic signal. It does not replace the numerical value.

## 7. Common atomic operator

S1 and S2 use the same prospective primitive:

`ONE_SHOT_TARGET_SCOPED_EPISTEMIC_STATUS_ANNOTATION`

Prompt-visible delta:

```json
{
  "target_locator": "<frozen locator>",
  "epistemic_status": "unconfirmed"
}
```

Frozen invariants:

- original target value preserved;
- from-status class `fact`;
- to-status `unconfirmed`;
- exactly one experiment-origin direct exposure;
- zero experiment-origin reinjection;
- zero persistent experiment-origin state mutation;
- no opposite factual claim;
- no replacement conclusion;
- no desired terminal answer;
- free continuation after consumption.

Only target identity/provenance differs between S1 and S2.

## 8. Historical boundary

The atomic v0.2 specificity operator is prospective.

It is **not** represented as an exact replay of the historical R5-MID operator:

`shared_state_metadata.inventory_stockout_assessment_v1.status: fact -> unconfirmed`

Historical R5-MID A/B evidence remains frozen and is not retroactively relabelled S0/S2.

## 9. Offline implementation status

Implemented:

- exact-source binding;
- outcome-blind S1 pool and selection record;
- common atomic one-shot operator;
- conditional prompt support;
- copied-runtime-view transformation;
- one-shot consumption and no-reinjection evidence;
- source-runtime immutability check;
- original-value preservation check;
- deterministic exact-source preflight;
- unit tests;
- cross-contract validator;
- offline CI;
- atomic plan and preflight schemas.

These are **engineering readiness evidence only**.

They do not create scientific S0/S1/S2 subject outcomes.

## 10. Next freeze boundary

Before any scientific S-arm execution, the repository should bind a branch-head exact prepared plan containing at minimum:

- source parent/evidence hashes;
- S1 selection record hash;
- S1/S2 envelope hashes;
- canonical R6-D condition IDs;
- natural-baseline/process-distance contract;
- observation horizon/censoring rule;
- plan hash;
- code SHA;
- `NOT_AUTHORIZED` run gate.

Only after that freeze and explicit user authorization may a real provider subject run be considered.

## 11. Scientific status

Current status:

- exact source audited: **YES**;
- S1 selected outcome-blind: **YES**;
- atomic S1/S2 operator implemented: **YES**;
- deterministic offline preflight available: **YES**;
- scientific S-arm outcomes: **NO**;
- target specificity established: **NO**;
- CPR adjudicated: **NO**;
- paid provider authorization: **NO**.

## 12. Authorization boundary

This audit authorizes offline parsing, selection, implementation, testing, schema validation and exact-plan freezing only.

It does **not** authorize:

- a scientific provider subject call;
- a paid evaluator call;
- CPR semantic adjudication;
- mutation of historical frozen evidence.
