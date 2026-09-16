# CN-R-053 — Branchable Anchor Requires Pending Executable Work

Date: 2026-09-16  
Status: IMPLEMENTED OFFLINE / ZERO PROVIDER CALLS

## 1. Breakpoint discovered by integration validation

The first end-to-end Phase-B Measurement-v3 integration test exposed a precise control-layer failure mode:

`nonterminal snapshot ≠ executable continuation anchor`

A high-certainty state-write candidate could be followed by an `after_turn:<n>` snapshot that was not marked terminal, yet its Arena scheduler queue was empty.

Restoring that state was mechanically valid, but there was no next Agent turn to execute. The branch therefore ended as `RUN_INCOMPLETE` rather than producing a continuation.

This was an instrumentation/protocol defect, not scientific evidence about Reality Bias.

## 2. Historical behavior preserved

`arena/config/r5r6_anchor_rule_v0.1.json` remains unchanged as the historical selector contract.

Under v0.1, a replayable nonterminal high-certainty state-write snapshot could be selected even when no pending scheduler work remained.

No historical selection record or subject trace is rewritten.

## 3. Forward correction — anchor rule v0.2

Forward Phase-A collection now uses:

`arena/config/r5r6_anchor_rule_v0.2.json`

with the additional frozen condition:

`require_pending_queue = true`

A confirmatory Phase-B candidate therefore requires:

- a deterministic structural candidate;
- an exact recorded post-turn snapshot;
- nonterminal state;
- at least one recorded pending Arena queue item;
- no semantic Reviewer labels during selection;
- no branch outcomes visible during selection.

The requirement is purely structural and does not claim that pending work is semantically necessary or that the candidate is a true C/Jump event.

## 4. Defense in depth

The requirement is enforced at three layers:

1. anchor selection v0.2 excludes empty-queue snapshots;
2. Phase-A manifest validation requires the forward rule to declare `require_pending_queue = true`;
3. `branch_plan.validate_phase_a_selection(...)` and `verify_branch_plan(...)` reject an empty-queue parent even if an old/manual selection package is supplied.

This prevents a historical v0.1 selection package from accidentally being promoted into a current executable Phase-B plan.

## 5. Scientific significance

The correction sharpens the definition of a branchable state anchor:

> A state is not experimentally branchable merely because it can be deserialized; it must also contain a recorded continuation path under the runtime scheduler being studied.

For the current Arena, the minimum executable-continuation evidence is pending queue state.

This is a runtime-specific experimental-control condition, not a universal claim that every Multi-Agent architecture must represent pending work as a queue.

## 6. Failure semantics

If a baseline contains a structural candidate but no eligible pending-work anchor, the objective result is:

`NO_ELIGIBLE_STRUCTURAL_ANCHOR`

The baseline remains frozen. It is not automatically regenerated to manufacture a branchable candidate.

## 7. API boundary

This correction was triggered and validated through offline deterministic tests only.

No paid subject call and no paid Reviewer call was performed or authorized by this update.
