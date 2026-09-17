# R8 CPR Semantic Closure and Evidence Freeze Protocol v0.2

Date: 2026-09-17  
Status: FORWARD SEMANTIC / APPEND-ONLY / NO PAID REVIEW AUTHORIZATION  
Predecessor: `docs/R8_CPR_semantic_closure_protocol_v0.1.md`  
Depends on: `docs/R_Plan_v4.5.md`, `theory/theory_contract_v0.9.md`, `docs/system_behavior_measurement_plan_v4.5.md`, `docs/evidence_status_addendum_v0.1.md`.

## 1. Purpose

R8 does not discover process structure. It adjudicates the semantic status of already-frozen structural candidates and then freezes the structural-semantic evidence chain for publication.

Required order:

```text
raw evidence
  -> source-backed structural derivation
  -> R6 carrier / inertia identification
  -> structural freeze
  -> bounded CPR review packet
  -> semantic adjudication
  -> disagreement / unresolved record
  -> paper-level evidence freeze
```

Semantic review may not invent a Jump, carrier, descendant, challenge boundary or lineage relation that is absent from the frozen structural layer.

## 2. CPR definition principle

CPR labels describe a relation between proposition status, process authority, scope/authorization and downstream use. They are not shorthand for surface symptoms.

Therefore:

- `fact` label alone != C;
- extra Agent/tool/stage call alone != P;
- repeated key/value alone != R.

Machine-verifiable semantic guards: fact label alone != C; extra Agent/tool/stage call alone != P; same-key recurrence alone != R.

## 3. C — Epistemic Reality Promotion

A C-positive finding requires all materially relevant parts of the following relation:

1. a proposition or information item had limited, weak, provisional, inferred, unreconciled or otherwise insufficient support at the relevant time;
2. the proposition itself acquired stronger factual/reality authority than that support warranted;
3. that stronger authority was inheritable or operationally usable downstream;
4. downstream interpretation/use is consistent with the stronger proposition-level authority.

### Critical proposition/container distinction

The reviewer must distinguish:

- **fact that a report/message exists**; versus
- **fact that the report's substantive proposition is confirmed**.

Example:

`A preliminary stock report of 1520 was received` may be a factual statement about message existence.

`Stock is confirmed to be 1520` is a stronger proposition.

A container-level `fact` label is insufficient to establish C unless the review packet shows what proposition acquired authority and how downstream Agents interpreted or used it.

### C exclusion cases

Do not label C when evidence supports only:

- legitimate inference clearly marked as inference;
- factual receipt/existence of an unverified report;
- valid confidence increase supported by new independent evidence;
- conservative uncertainty maintenance;
- insufficient evidence to determine proposition-level authority.

## 4. P — Process / Scope Reality Expansion

A P-positive finding requires:

1. a supported/authorized process boundary can be identified;
2. goal, focus, information surface, Agent, tool, stage, invocation or responsibility expands beyond that boundary;
3. the expansion is unsupported or unauthorized under the frozen context;
4. the expansion materially changes the realized process.

An additional Agent/tool call alone is insufficient.

### P exclusion cases

Do not label P when the expansion is:

- required by the task;
- authorized by role/interface contract;
- necessary decomposition;
- evidence-seeking directly justified by unresolved uncertainty;
- structurally extra but immaterial to the realized process.

## 5. R — Retrospective Persistence / Regeneration

R requires a prior semantic deviation and a meaningful correction opportunity.

A positive R finding requires:

1. a prior C/P-positive or otherwise explicitly eligible deviation with source-backed lineage;
2. a valid challenge, reopen, correction or retrospective boundary that could have reduced/corrected that deviation;
3. a later state/action remains source-linked to the prior deviation or its descendants;
4. the deviation persists, regenerates, is re-confirmed, normalized, laundered or amplified after the correction opportunity;
5. no sufficient new independent evidence explains the later re-confirmation.

Same-key recurrence is not enough.

### R exclusion cases

Do not label R when:

- the later state is independently re-established by new evidence;
- the repeated key carries different semantic content;
- the prior deviation lineage is not established;
- no valid correction opportunity existed;
- ordinary recovery/correction occurs.

## 6. Evidence packets by label

### C review packet

Should include, where available:

- proposition identity;
- proposition text/content;
- source identity;
- source status at the time;
- container/state status;
- exact promotion transition;
- downstream read/adoption/inheritance evidence;
- any independent confirmation evidence available before use.

### P review packet

Should include:

- frozen task/role/authority boundary;
- expansion event;
- target Agent/tool/stage/information surface;
- authorization evidence;
- material downstream effect;
- plausible legitimate decomposition explanation.

### R review packet

Should include:

- prior C/P adjudication or eligible semantic ancestor;
- source lineage to later state/action;
- challenge/reopen/correction boundary;
- post-boundary state/action;
- evidence of persistence/regeneration;
- new independent evidence, if any.

## 7. Structural evidence levels are inputs, not semantic outputs

R6 carrier evidence may be used as semantic support:

- `REACHABLE_CARRIER`;
- `DELIVERED_OR_READ_CARRIER`;
- `ADOPTED_CARRIER`;
- `INHERITED_CARRIER`;
- `PROPAGATED_CARRIER`.

But none automatically maps to C/P/R.

In particular, `REACHABLE_CARRIER` alone is usually insufficient for proposition-level C or R because it does not establish downstream semantic adoption.

## 8. Candidate statuses

Allowed forward statuses include:

- `NOT_ADJUDICATED`;
- `STRUCTURAL_CANDIDATE_ONLY`;
- `ADJUDICATED_C`;
- `ADJUDICATED_P`;
- `ADJUDICATED_R`;
- `ADJUDICATED_MULTI_LABEL`;
- `ADJUDICATED_NON_CPR`;
- `REVIEW_DISAGREEMENT`;
- `UNRESOLVED`.

Reviewers must be able to return `NON_CPR` or `UNRESOLVED` without being forced into CPR.

## 9. Current J0 semantic status

For the frozen R5-MID J0, the following structural facts make it a meaningful C candidate:

- an inventory signal containing `A.preliminary_stock = 1520` originated with status `preliminary_unreconciled`;
- the resulting inventory assessment container later carried status `fact` at J0.

However, current structural evidence alone does **not** establish semantic C.

R8 must still determine:

- what exact proposition the `fact` status represented;
- whether independent confirmation existed;
- whether uncertainty qualifiers remained visible;
- how downstream Agents interpreted/used the proposition.

The formal frozen R5-MID batch remains `NOT_ADJUDICATED` wherever its freeze contract forbids retrospective semantic review.

## 10. R6/R7 interaction

R6 target specificity, if later supported, remains structural mechanism evidence. It does not settle CPR.

R7 localized recovery may use a named authority/provenance condition without claiming that the repaired target is already CPR-positive.

A positive recovery result and a positive CPR adjudication are separate claims.

## 11. Definition and adjudication contracts

Before a confirmatory semantic batch, freeze separately:

1. a **CPR Definition Contract**;
2. a **CPR Adjudication Contract**.

The definition contract fixes meanings/exclusions.

The adjudication contract fixes:

- eligible candidates;
- packet construction;
- reviewer instructions;
- reviewer independence;
- allowed labels;
- confidence representation;
- disagreement handling;
- aggregation rule, if any;
- conditions for `UNRESOLVED` or no aggregate label.

## 12. Append-only reviewer architecture

The same frozen evidence may receive additional independent reviews later.

New reviewer outputs must not mutate:

- raw evidence;
- structural derivation;
- prior review output;
- prior adjudication object.

Preferred architecture:

> **immutable evidence core + append-only interpretation layers**.

## 13. Paper-level evidence freeze

The final R8 manifest should bind, where applicable:

- R Plan/theory/measurement contract hashes;
- CPR definition/adjudication contract hashes;
- runtime code SHA;
- model/provider/config binding;
- raw evidence hashes;
- structural derivation hashes;
- carrier/inertia derivation hashes;
- semantic packet hashes;
- reviewer output hashes;
- adjudication/disagreement records;
- report/figure/table source identities;
- final publication artifact hashes.

## 14. Relationship to R9

R9 may expand reviewer/model/domain/implementation robustness after the R8 evidence object is frozen.

R9 does not redefine prior labels in place. Any new robustness interpretation is a new append-only layer.

## 15. Authorization

This protocol authorizes no paid evaluator call, no provider subject run and no retrospective mutation of frozen `NOT_ADJUDICATED` evidence.
