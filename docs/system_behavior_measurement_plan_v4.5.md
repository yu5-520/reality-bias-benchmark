# Reality Bias System Behavior Measurement Plan v4.5

Date: 2026-09-17  
Status: FORWARD / R6 SYSTEM-INERTIA IDENTIFICATION  
Depends on: `docs/R_Plan_v4.5.md`, `theory/theory_contract_v0.9.md`.

## 1. Measurement hierarchy

```text
Raw Event / State Evidence
  -> Natural Jump
  -> Local Perturbation Response
  -> Carrier / Inheritance Evidence
  -> Natural Inertia Baseline
  -> Intervention-Related Inertia Transition
  -> Target Specificity (S0/S1/S2)
  -> R7 Risk-Control / Recovery Evidence
  -> R8 CPR Semantic Adjudication
  -> Terminal Outcome separately
```

No layer may be automatically promoted into the next.

## 2. Direct exposure window

The direct intervention window must be explicitly marked.

For the formal R5-MID family this is the first resumed Agent turn after J0 exposure, e.g. T9.

Record:

- exact prompt/input delta;
- target locator;
- before/after epistemic status annotation;
- exposure count;
- reinjection count;
- persistent mutation flag;
- actor/turn;
- immediate messages/writes/invocations/finalization;
- whether the immediate action explicitly references the perturbed target.

These measurements support **local response**, not long-range inertia by themselves.

## 3. Post-consumption window

A treated branch enters R6 post-consumption analysis only after:

- direct experiment-origin exposure occurred;
- the one-shot envelope was consumed;
- no experiment-origin reinjection remains;
- persistent experiment-origin mutation is false.

For untreated S0/control branches, use the frozen matched analysis origin.

## 4. Carrier evidence object

Each candidate carrier should record:

- `carrier_id`;
- carrier type: message/state/invocation/evidence/revision/handoff;
- source event refs;
- source actor/turn;
- destination actor/turn;
- read/delivery evidence;
- explicit-use/reference evidence if available;
- downstream state/action refs;
- descendant refs;
- carrier evidence level.

Allowed evidence levels:

- `REACHABLE_CARRIER`;
- `DELIVERED_OR_READ_CARRIER`;
- `ADOPTED_CARRIER`;
- `INHERITED_CARRIER`;
- `PROPAGATED_CARRIER`.

Graph reachability alone must not be labeled semantic adoption.

## 5. R6-A Natural Inertia Baseline

Estimate natural-condition variability from repeated natural continuations.

Compare using preregistered structural dimensions such as:

- reachable-event set/count;
- first descendant distance;
- reach depth;
- actor sequence/set;
- edge set;
- branch/merge/re-entry;
- cross-Agent relations;
- path-family structure;
- state-lineage destination;
- reconvergence;
- censoring.

Do not define intervention effect from one A/B difference if natural A/A variation is of similar magnitude.

## 6. Process-distance contract

A future real run must freeze either:

1. a multidimensional process-distance vector; or
2. a validated aggregation rule.

The first-paper default is the multidimensional vector.

Conceptual comparisons:

- `d(Ai, Aj)` natural variability;
- `d(Bi, Bj)` treated variability;
- `d(Ai, Bj)` cross-condition variability;
- `d(S1, S0)` generic uncertainty response;
- `d(S2, S1)` target specificity.

No after-the-fact scalar complexity score may replace the preregistered dimensions.

## 7. R6-B Carrier / Inheritance Identification

For every claimed inertia chain, distinguish:

```text
available downstream
  -> actually delivered/read
  -> explicitly used/adopted
  -> inherited into new state/action
  -> propagated further
```

When semantic adoption cannot be established from raw evidence, report the highest supported structural level rather than inferring use.

## 8. R6-C Intervention-Related Inertia Transition

A valid intervention-related inertia claim requires:

- post-consumption observation;
- source-backed downstream carrier/structure;
- comparison against natural variability;
- matched horizon or explicit censoring;
- no hidden reinjection/persistent experiment-origin state.

Possible structural outcomes:

- retained;
- attenuated;
- amplified;
- deflected;
- transferred;
- transformed;
- reconstructed/hybridized;
- delayed re-emergence;
- rebound/regeneration;
- reconverged;
- unresolved/censored.

## 9. R6-D Target Specificity

Specificity conditions:

- `S0_NATURAL_REFERENCE`;
- `S1_MATCHED_OR_ORDINARY_FACTUAL_INFORMATION_DOWNGRADE`;
- `S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL`.

Primary contrast: `S2 - S1`.

S1 may show local response or even downstream inertia change. Specificity requires structural distinguishability under frozen mechanics/selection rules, not an inert S1.

## 10. Exact-source v0.2 atomic targets

Current prospective bindings:

- S1 locator: `public_context.products.C.gross_margin_pct`, original value `35`;
- S2 locator: `shared_state.inventory_stockout_assessment_v1.A.preliminary_stock`, original value `1520`.

The S2 signal source status was `preliminary_unreconciled`; acquired status at J0 was `fact` through the containing state object.

S1/S2 use the same minimal one-shot target-scoped epistemic annotation and preserve original values.

## 11. Censoring

Use explicit censoring states:

- `UNCENSORED`;
- `EARLY_NATURAL_TERMINATION`;
- `HORIZON_LIMIT`;
- `MISSING_SOURCE_EVIDENCE`;
- `OTHER_UNRESOLVED`.

Rules:

- censored != zero;
- no later Jump within a terminated trace != extinction;
- missing carrier evidence != no carrier;
- same-key recurrence != same semantic state.

## 12. CPR evidence separation

Structural measurements may generate CPR review candidates but cannot adjudicate CPR.

For C review, preserve proposition/source-status/downstream-use evidence.

For P review, preserve authorized scope/boundary and material process-change evidence.

For R review, preserve prior deviation lineage, valid correction opportunity, later source-linked persistence/regeneration and any new evidence that could independently justify re-confirmation.

## 13. R7 measurement extension

R7 must measure both:

### Risk-control outcomes

- affected descendant count;
- risky lineage reach/depth;
- residual old lineage;
- recurrence/re-entry;
- time/distance to containment;
- reopened affected nodes.

### Freedom-preservation outcomes

- unaffected nodes/fields/branches preserved;
- unnecessary reopen count;
- unaffected Agent participation retained;
- unrelated path diversity retained;
- full rerun avoided/invoked.

## 14. Engineering observability profile

The optional R7 engineering profile may register runtime identities:

- EventHash;
- MessageHash;
- StateHash;
- FieldHash;
- SourceHash;
- RevisionHash;
- parent/lineage refs.

This layer is passive by default and must not change Agent behavior merely because observation is enabled.

## 15. Authorization boundary

This plan authorizes offline schema/runtime validation only. It authorizes no scientific provider call, paid evaluator call or semantic CPR adjudication.
