# R7 Semantic-Lineage Scoped Recovery Protocol v1.2

Date: 2026-09-18  
Status: FORWARD / ENGINEERING CONTROL / ACTIVE PHASE REQUIRES SEPARATE AUTHORIZATION  
Predecessor: `docs/R7_semantic_lineage_scoped_recovery_protocol_v1.1.md`

## 1. Purpose

R7 tests whether a content-addressed target can be repaired as a lineage-bounded structure package while preserving unrelated structure and maintaining post-repair observability.

R7 is engineering-neutral with respect to CPR semantics.

## 2. Repair unit

The Repair Anchor is the package entry point.

The repair unit is the Semantic Lineage Package containing, when evidence supports them:

- target semantic identity/content address;
- source/provenance refs;
- transformations and authority transitions;
- adoption/relation refs;
- shared-pool representations;
- decision/action dependencies;
- descendant candidates;
- evidence-supported affected closure;
- RepairClosure;
- preserved/unresolved refs.

## 3. Three-arm parity

C1, C2 and C3 use a common full-lineage observation contract.

C1 changes the runtime view once.

C2 persistently changes the runtime view while persistent shared state remains unchanged.

C3 changes the actual authorized structural state and applies bounded descendant invalidation/reopen/recompute.

Observation depth must not be reduced for C1/C2.

## 4. Completeness gate

`LINEAGE_GAP` blocks automatic active repair.

Missing semantic history must not be invented as fact.

## 5. Repair dispositions

R7 may make machine-supported structural dispositions:

- preserve structurally unrelated material;
- invalidate descendants already inside the authorized RepairClosure;
- reopen mechanically dependent recipients/decisions;
- recompute only the bounded affected continuation.

Semantic compatibility that cannot be established mechanically remains unresolved and is deferred to R8/human semantic review.

## 6. Revision model

Historical source evidence is immutable.

Repair creates a branch-local new revision. Superseded/invalidated lineage remains addressable for audit.

## 7. Post-repair watch

Every C3 repair produces a Post-Repair Watch Contract.

The watch must record, at minimum:

- exact target old-authority re-entry;
- post-repair target writes;
- new state-write/descendant candidates;
- authority-escalation candidates;
- closure-expansion candidates;
- watch scope and observed horizon.

Watch triggers are structural signals, not CPR adjudications.

## 8. Verification

R7 verifies:

- anchor revision identity;
- invalidated/reopened refs;
- recomputed refs;
- old-lineage exact re-entry;
- direct preservation of unrelated anchor material;
- post-repair watch result;
- frozen-evidence binding.

## 9. Nonclaims

R7 does not decide whether a trajectory contains C, P or R.

R7 does not treat downstream structural expansion as proof of failure or recovery.

R7 does not treat multiple descendant supports as independent evidence without semantic review.

## 10. Authorization

Any active repair or paid subject execution requires separate explicit authorization.
