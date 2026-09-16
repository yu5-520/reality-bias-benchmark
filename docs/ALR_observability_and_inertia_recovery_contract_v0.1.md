# ALR Observability and Inertia-Recovery Contract v0.1

Date: 2026-09-17  
Status: FORWARD CONCEPT CONTRACT / NO PAID RUN AUTHORIZATION

## 1. Purpose

This contract separates two roles that share a structural representation but must not be conflated:

1. **passive structural observability** used to reconstruct naturally realized process structure;
2. **active ALR recovery/control** used under an explicit R7 treatment to manage risk-bearing system inertia.

ALR in this program is not defined as a single correction at a Jump and is not a fixed production workflow.

## 2. Passive observability mode

The passive mode may record or derive:

- Behavior Events and State Transitions;
- message / invocation / state relations;
- field provenance;
- parent/dependency relations;
- Jump candidates;
- descendant lineage;
- branch / merge / re-entry;
- path families;
- inherited inertia.

It must not, merely by being enabled:

- prescribe Agent order;
- prescribe a target path;
- insert lineage instructions into subject prompts;
- require a semantic CPR label;
- repair or suppress a candidate Jump;
- rewrite the natural trajectory to fit an expected graph.

The observation claim is therefore:

> The structural layer makes realized process relations inspectable; it does not establish that the observational representation caused those relations.

## 3. Raw-fact boundary

Any derived structural relation must retain a source path to recorded facts where the runtime supports it.

Examples of raw facts include:

- `message_sent`, `message_delivered`, `message_read`;
- invocation proposal/execution;
- state read/write/revision;
- actor / turn;
- before/after state identity;
- FINAL/reopen/revision;
- queue or execution record.

Examples of derived relations include:

- Jump;
- descendant-of-Jump;
- affected field;
- dependency closure;
- path family;
- system inertia.

The latter must not be presented as raw observations.

## 4. Active ALR mode

Active ALR is a named treatment that begins only after a risk-bearing Jump/field lineage has been selected under a frozen experimental protocol.

Its objective is not to standardize the whole process. It is to make the affected lineage **traceable, locally revisable, repeatedly observable and recoverable across downstream propagation**.

The active loop is:

```text
Locate
  -> Structure
  -> Repair
  -> Propagate
  -> Observe
  -> Re-repair if residual/recurrence remains
  -> Release
```

## 5. Localization object

The Jump `J0` is the entry anchor, not the complete control object.

The continuing recovery object is the source-backed **risk-bearing field lineage and affected dependency closure**, including downstream field/state/message/Agent relations that remain causally connected under the frozen derivation rules.

Where evidence is insufficient, the status must remain unresolved rather than expanding the affected closure by intuition.

## 6. Structured recovery routing

Structured routing in active ALR is **recovery routing**.

It may determine which affected actor/stage/node must receive or recompute a revised field state, but it is not intended to permanently replace natural free routing.

Properties:

- **dynamic** — generated from the realized lineage rather than one fixed sequence for all cases;
- **local** — limited to the affected recovery scope where evidence permits;
- **field-aware** — tracks the specific field/revision lineage instead of treating an entire Agent as contaminated by default;
- **iterative** — observes downstream residual/recurrence and may run another recovery round;
- **releasable** — exits to free routing after the preregistered release condition.

## 7. Field-level revision requirements

Where runtime support exists, a repaired/revised field should carry sufficient identity to distinguish it from its predecessor, for example:

- field key;
- prior value/status identity;
- new value/status identity;
- source evidence ref;
- revision identity/hash;
- parent revision ref;
- recovery round;
- affected lineage refs;
- current recovery status.

The exact schema may evolve, but old and new field states must not become observationally indistinguishable after repair.

## 8. Why one-shot repair is insufficient as a control claim

R5 deliberately removes the experimental mark after one exposure. This is appropriate for testing perturbability.

System inertia, by definition, may already be represented across later state, messages, Agent activations, invocations and historical dependencies. Correcting only the entry Jump does not establish that these downstream carriers have been controlled.

Therefore:

> one-shot modification may change a path; sustained lineage-aware feedback is required before claiming evidence about inertia controllability.

This is a theoretical boundary, not a preregistered assumption that active ALR will succeed.

## 9. Risk-control objective

ALR targets **risk-bearing inertia**, not process diversity.

Allowed outcomes include:

- containment;
- attenuation;
- redirection;
- localized repair;
- partial residual;
- recurrence;
- transfer to another lineage;
- secondary Jump;
- failure to localize/control within the observed horizon.

No direction is pre-labelled as the only acceptable scientific result.

## 10. Freedom-preservation objective

Active ALR should separately report its cost to unaffected structure.

Evidence should distinguish:

- affected vs preserved nodes;
- affected vs preserved fields;
- reopened vs untouched branches;
- local recovery vs full rerun;
- non-risk path diversity retained/lost.

A framework that suppresses the whole process may reduce observed risk but does not thereby demonstrate localized control.

## 11. Release

A recovery treatment must have a preregistered release rule. Release means active structured recovery routing ends and the system may resume free routing.

Later residual or recurrence after release is evidence, not an automatic integrity failure.

## 12. Semantic boundary

ALR structural localization/recovery does not itself decide whether an event is semantic C, P or R.

CPR adjudication belongs to R8 and consumes frozen structural evidence through an append-only review process.

## 13. Historical compatibility

Existing free-routing traces, R5-MID evidence, structured-routing pilots and recovery-related artifacts retain their historical identities. This contract does not retroactively convert them into active ALR evidence.
