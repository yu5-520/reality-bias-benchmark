# ALR Authority-Localized Recovery Contract v0.2

Date: 2026-09-17  
Status: FORWARD CONCEPT/OPERATOR CONTRACT / NO PAID RUN AUTHORIZATION  
Predecessor: `docs/ALR_observability_and_inertia_recovery_contract_v0.1.md`

## 1. Purpose

This contract narrows the forward definition of **ALR**.

ALR means **Authority-Localized Recovery**.

ALR is a **causally localized structural recovery operator**. It is not identical to the broader R7 research question of structural inertia steering and it is not defined as a generic sustained-feedback framework.

Its central proposition is operational:

> If a Reality-Bias-relevant process displacement is carried through identifiable authority/provenance and dependency relations, recovery can target the earliest violated structural condition and its affected dependency closure while preserving unrelated realized structure.

Whether this proposition is empirically supported is an R7 question; the contract does not assume success.

## 2. Passive observability remains separate

The passive structural layer may record or derive:

- Behavior Events and State Transitions;
- message / invocation / state relations;
- field provenance;
- parent/dependency relations;
- Jump candidates;
- descendant lineage;
- branch / merge / re-entry;
- path families;
- inherited inertia.

Passive observability must not merely by being enabled:

- prescribe Agent order;
- prescribe a target path;
- insert recovery instructions into subject prompts;
- require a semantic CPR label;
- repair or suppress a candidate Jump;
- rewrite the natural trajectory to fit an expected graph.

Observation and recovery are different roles even when they use compatible structural representations.

## 3. Recovery anchor

ALR does not anchor on the first piece of text that appears incorrect.

The preferred anchor is the **earliest source-backed ancestor at which a named authority/provenance condition was violated**.

Call this node/state `n*`.

A valid `n*` requires:

- a named frozen condition or contract;
- recorded evidence showing the before/after transition or unsupported state change;
- source refs sufficient to distinguish the violation from a later textual consequence;
- a derivation rule that can be reapplied without reviewer intuition.

If these requirements are not met, the recovery anchor remains `UNRESOLVED`.

## 4. Authority/provenance condition

The recovery condition may concern one or more frozen dimensions such as:

- information/evidence authority;
- invocation/action authority;
- temporal/history authority;
- role/responsibility authority;
- provenance/support status;
- state-commit authority.

The exact condition must be named in the run contract. ALR does not infer a generic violation merely because a final answer is undesirable.

## 5. Dependency closure

Given `n*`, ALR computes the downstream dependency closure under a frozen structural derivation rule.

Define:

- `Affected = DependencyClosure(n*)`
- `Preserved = RealizedGraph - Affected`

The closure may include source-backed descendants through:

- field/state inheritance;
- message delivery/read relations;
- invocation/execution relations;
- proposal/commit relations;
- revision lineage;
- Agent/stage transitions;
- re-entry relations;
- other preregistered dependency edges.

The affected set must not expand by intuition alone.

## 6. Preservation rule

Nodes, fields or branches outside the source-backed affected closure remain preserved by default.

ALR therefore differs from whole-system rerun in a crucial way:

- successful unaffected structure is **not reopened merely because it shares the same task**;
- an Agent is not marked wholly contaminated merely because one of its fields/actions lies inside the affected closure;
- preservation decisions must themselves be auditable.

## 7. Repair rule

ALR repairs the **violated authority/provenance condition**, not the terminal answer.

Examples include:

- restoring an uncertain state from `fact` to `unconfirmed` where the source support does not justify fact status;
- reopening an invocation that was committed without required authority;
- correcting a historical state that was prematurely settled;
- replacing a source/provenance reference with a verified revision.

The repair payload must be minimally sufficient to change the violated condition. It must not contain a target final answer unless that answer is itself the frozen source fact being restored.

## 8. Revision identity

A repaired state must be distinguishable from its predecessor.

Where runtime support exists, record:

- field/state key;
- prior revision/hash;
- repaired revision/hash;
- parent revision ref;
- repair condition id;
- source evidence refs;
- recovery anchor `n*`;
- affected-closure identity/hash;
- timestamp/turn/recovery operation id.

A repaired state must not silently overwrite its historical predecessor in the evidence record.

## 9. Local reopen / re-execution

ALR reopens or re-executes **only the affected subgraph** under the repaired condition where runtime semantics permit.

The recovery record must preserve:

- which nodes were reopened;
- which preserved nodes remained untouched;
- original subject proposals where a structural policy blocks or redirects realization;
- realized replacement actions/states;
- new descendant relations after recovery.

The local recovery path remains generative. ALR does not prescribe the terminal answer.

## 10. Operator lifecycle

The minimal ALR operator is:

```text
Detect named authority/provenance breach
  -> locate earliest violating ancestor n*
  -> compute affected dependency closure
  -> preserve unaffected realized structure
  -> repair breached condition
  -> create new revision lineage/hash
  -> reopen/re-execute affected subgraph only
  -> observe downstream structural consequences
```

This is one localized recovery operation.

A higher-level experiment protocol may invoke ALR again if another preregistered recovery condition is met. Iteration is not required to define ALR itself.

## 11. Structural outcomes

Possible observed outcomes include:

- local containment;
- attenuation;
- redirection;
- partial recovery;
- residual old lineage;
- recurrence/rebound;
- transfer to another lineage;
- re-entry;
- path reconstruction;
- secondary Jump;
- failure to localize;
- failure to recover within horizon.

No outcome is pre-labelled as the only scientifically acceptable result.

## 12. Persistent field is a distinct mechanism

A persistent-field condition continuously supplies the same correction state/signal to later nodes.

It therefore studies **experiment-maintained persistence**.

ALR instead studies whether the affected process can be localized and recovered through source-backed structural relations.

For a valid R7-B comparison:

- semantic correction content should be materially equivalent;
- parent/J0 should be matched where feasible;
- passive observability should be equivalent;
- the intended treatment difference is propagation/recovery structure.

A persistent field knows that the signal is still present. ALR must additionally show which structural carrier is affected, what is preserved, what is revised and what is reopened.

## 13. Full Rerun and Checkpoint Retry

Full Rerun may change the sample while leaving the violated authority condition unchanged. It can therefore re-enter the same failure basin.

Checkpoint Retry may start closer to the failure but still reopen structure unrelated to the actual dependency closure or preserve the same violated condition.

These remain useful secondary engineering baselines for recurrence, preservation and cost. They do not replace the core persistent-field vs ALR mechanism contrast.

## 14. Observability / traceability / local controllability / reversibility

ALR naturally exposes four testable properties:

### Observability
Can the recovery substrate expose `n* -> descendants -> affected state -> affected actors`?

### Traceability
Can a later event/state be traced through source-backed lineage to the recovery anchor and revision lineage?

### Local controllability
Can recovery operate on the affected dependency closure without reopening the entire process?

### Selective reversibility / localized recovery
Can affected structure be revised/reopened while unrelated successful structure remains preserved?

These are empirical properties, not guaranteed capabilities.

## 15. Semantic boundary

ALR localization/recovery does not itself determine semantic C, P or R.

CPR adjudication belongs to R8 and consumes frozen structural evidence through append-only review objects.

## 16. Historical compatibility

Existing free-routing traces, persistent-exposure pilots, structured-orchestration pilots, formal R5-MID evidence and earlier ALR documents remain historical records.

This contract does not retroactively convert them into ALR v0.2 evidence and authorizes no provider call.
