# CPR Semantic Review Position under System Behavior v4

Date: 2026-09-16  
Status: FORWARD REVIEW POSITION

## 1. Purpose

C/P/R remain important semantic mechanisms, but they are no longer the primary data-discovery interface.

Forward review order:

```text
raw frozen evidence
→ machine behavior index
→ structured transition candidate
→ lineage / downstream window
→ semantic adjudication
```

## 2. Reviewer responsibility

The Reviewer should answer a bounded question about an already localized transition, rather than being asked to inspect an entire long trajectory and discover all possible Bias events from scratch.

A preferred review packet contains:

- task/authority contract excerpt;
- state before;
- relevant source/provenance evidence;
- localized behavior event;
- state after;
- selected downstream lineage;
- challenge/correction window where R is being assessed.

## 3. C/P/R status

- C/P are first-order semantic forms over behavior/state-transition evidence.
- R is a second-order semantic/dynamic judgment that requires a prior C/P-derived deviation or unresolved state.
- ordinary correction is not R.
- a structural candidate remains `NOT_ADJUDICATED` until semantic criteria are applied.

## 4. Historical reviewers

Historical Reviewer v1/v2 packets and results remain preserved. They are not invalidated by v4.

Their role is historical semantic evidence and measurement-sensitivity material. New v4 packets may be narrower and behavior-localized, but must never rewrite old review records.

## 5. Cost and scale implication

Behavior-first localization allows expensive semantic evaluation to be concentrated on selected state transitions and downstream windows rather than the complete reasoning history of every run.

This is a measurement-efficiency argument, not a claim that semantic review becomes unnecessary.