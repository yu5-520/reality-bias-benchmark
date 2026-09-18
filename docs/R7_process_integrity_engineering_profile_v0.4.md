# R7 Process Integrity Protocol — Engineering Profile v0.4

Date: 2026-09-18  
Status: ENGINEERING PROFILE / NO SEMANTIC CPR ADJUDICATION  
Predecessor: `docs/R7_process_integrity_engineering_profile_v0.3.md`

## 1. Lifecycle

`Observe -> Scout -> Repair Anchor -> Content Address -> Semantic Lineage Package -> Completeness Gate -> RepairClosure -> Repair -> Recompute -> New Revision -> Reinforced Watch -> Verify`

## 2. Content address + hash lineage

Content addressing identifies the semantic object/revision.

Hash lineage records transformations, adoptions, authority transitions, pool representations and descendants.

Together they make the repair object a lineage-bounded structure package rather than a single field.

## 3. Full-lineage observation

All R7 arms record the same structural observation surface.

The observation envelope separates:

- inherited pre-branch lineage descendants;
- prospective branch events;
- state writes and authority statuses;
- message/invocation refs;
- actors and model-call refs;
- exact target rewrites.

## 4. Repair scope

The current implementation may conservatively invalidate structurally bounded post-anchor descendants already present in the frozen parent when the authorized packet does not provide finer event-level semantic disposition.

This is a bounded engineering safety policy, not a claim that every post-anchor event is semantically incompatible.

Future finer disposition requires stronger relation evidence or semantic review.

## 5. Watch policy

Post-repair watch is cheap by default:

- hash/ID matching;
- event/state-write recording;
- exact authority re-entry checks;
- closure-expansion candidate recording.

No model call is required for ordinary watch operation.

Semantic recurrence or structural equivalence beyond exact machine matches is deferred.

## 6. Scientific boundary

R7 outputs structural evidence only.

C/P/R event interpretation, collective completion, authority migration, recurrence semantics and probability claims belong to R8/R9.
