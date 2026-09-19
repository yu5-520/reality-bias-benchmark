# Semantic Trajectory Audit Contract v0.1

Date: 2026-09-20  
Status: **FORWARD ACTIVE / COMPLETE-ROUTE SEMANTIC AUDIT**

## 1. Purpose

This contract upgrades semantic review from summary classification over structural records into an append-only, machine-verifiable reconstruction of the **complete realized Agent route** and the **semantic lineage carried across that route**.

The semantic audit is not a prose annotation attached to topology. It is a first-class evidence layer.

Core chain:

`Frozen Raw Trace -> Complete Actual Agent Route -> Node-Level Semantic Audit -> Relation-Level Semantic Audit -> Case Judgement -> Report Evidence Bundle`

No subject rerun is required for this migration.

## 2. Frozen evidence boundary

- raw subject evidence remains immutable;
- historical structural derivations remain immutable;
- historical semantic audits remain immutable;
- new semantic-trajectory audits are append-only;
- missing events may not be reconstructed as observed;
- no provider call is authorized by this contract;
- no paid evaluator call is authorized by this contract.

## 3. Primary experiment domains

For the current held-out first-round experiment, primary experiment evidence is restricted to:

- finance;
- supply_chain;
- software_engineering.

Ecommerce is historical method-development context only.

Ecommerce may not be used as:

- a held-out replication domain;
- a primary experimental typical case;
- a positive/negative mechanism comparator for this first-round report family;
- part of the natural-population denominator.

If mentioned, it must be labeled:

`HISTORICAL_METHOD_DEVELOPMENT_CONTEXT`.

## 4. Complete actual route is mandatory

A semantic trajectory audit must first preserve the entire executed Agent route in time order.

All executed Agent turns must remain visible even when a turn is irrelevant to the target semantic lineage.

Target-irrelevant route nodes must be retained and marked:

`IRRELEVANT_TO_TARGET_LINEAGE`.

The semantic lineage is an overlay on the actual route. It may not replace the route.

## 5. Node-level semantic audit

For every executed Agent node, bind where recorded:

- route index / turn;
- Agent role;
- call ref and event refs;
- relevant input premises;
- observed shared-state refs;
- messages/invocations;
- output actions and state writes;
- authority/status;
- termination/censoring state.

For each semantically relevant node, audit:

- input semantic content;
- output semantic content;
- **semantic delta**;
- semantic function;
- independent evidence introduced or not;
- independent evidence refs;
- exact evidence refs;
- claim status.

A label such as `SEMANTIC_TRANSFORMATION` without the actual before/after meaning is insufficient.

## 6. Relation-level semantic audit

Every major semantic edge must bind:

- source route node;
- recipient route node;
- propagation type;
- semantic relation;
- semantic-before content;
- semantic-after content;
- semantic delta;
- evidence refs;
- claim status.

Forward propagation vocabulary includes:

- `DIRECT_RELAY`;
- `SEMANTIC_TRANSFORMATION`;
- `TRANSFORMED_DESCENDANT`;
- `DESCENDANT_INHERITANCE`;
- `INDEPENDENT_REANCHOR`;
- `PREEXISTING_GATE_REAFFIRMATION`;
- `BOUNDARY_PRESERVATION`;
- `AUTHORITY_MIGRATION`;
- `DECISION_APPLICATION`;
- `MERE_VISIBILITY`;
- `MERE_RELAY`;
- `NOT_ESTABLISHED`.

## 7. Semantic change must be human-readable

The audit must record actual meaning changes, not only structural object names.

Acceptable form:

`"1200-1400 appears feasible" -> "1400 is the executable standard-lane ceiling"`

followed by:

`"1400 ceiling" -> "above 1400 requires escalation / residual-risk treatment"`.

Insufficient form:

`carrier changed` or `semantic transformation observed`.

## 8. Adoption is reader-bound

A downstream-adoption claim requires an identified reader node and evidence showing that the reader used the proposition/carrier in reasoning, constraint formation, decision or action.

Visibility alone is not adoption.

Same-key recurrence alone is not adoption.

## 9. Re-anchoring is evidence-bound

`INDEPENDENT_REANCHOR` requires explicit independent-evidence refs.

If the challenged source is no longer necessary because downstream Agents reconstruct the same decision from independent evidence, the case must not be labeled source-specific System Inertia by default.

Likewise, reaffirmation of a gate that already existed before the probe is not new source-specific System Inertia by default.

## 10. System Inertia case gate

A `CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE` requires a bound chain containing:

1. challenged source or target;
2. direct response;
3. post-challenge carrier;
4. downstream read/adoption;
5. decision/action consequence;
6. direct-stimulus end;
7. post-stimulus descendant persistence.

Mere persistence, literal recurrence, structural reachability or same endpoint is insufficient.

## 11. Uniform substantive decisions are forbidden

A semantic review manifest may define common:

- reviewer configuration;
- questions;
- allowed vocabularies;
- claim boundaries.

It may not preassign substantive results such as:

- semantic adoption = supported;
- decision/action dependence = supported;
- post-stimulus persistence = supported;
- System Inertia status;
- problematic-bias status.

Those fields must be audited per case/trajectory and aggregate counts must be computed from the resulting case records.

## 12. Probability / structure separation

Domain occurrence/distribution claims use the natural-trajectory population denominator.

Case-level mechanism classifications use source-bound case evidence.

Same-parent stochastic repeats are local conditional sensitivity, not population probability.

## 13. Report handoff

A report may treat a case as a major semantic example only after a complete `RB-SEMANTIC-TRAJECTORY-AUDIT-v0.1` record exists and passes validation.

Reports must not invent semantic steps that are absent from the frozen semantic-trajectory audit.

## 14. Claim boundaries

The following remain separate:

- structural support;
- semantic adoption;
- post-stimulus persistence;
- System Inertia candidate status;
- problematic bias;
- unique R5 causal attribution;
- CPR.

A semantic-trajectory audit does not authorize R7, R8 or any new subject execution.
