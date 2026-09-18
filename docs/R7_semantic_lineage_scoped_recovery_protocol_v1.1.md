# R7 Semantic-Lineage Scoped Recovery Protocol v1.1

Date: 2026-09-18  
Status: FORWARD v5.1 / ACTIVE PHASE REQUIRES SEPARATE AUTHORIZATION  
Predecessor: `docs/R7_localized_recovery_protocol_v1.0.md`

## 1. Purpose

R7 tests localized recovery over the complete relevant semantic lineage of a target problem while preserving unrelated semantics and process structure.

## 2. Locality definition

Localized recovery means:

`complete relevant semantic history + minimal unrelated context`.

It does not mean:

- only nearby events;
- only downstream descendants;
- a shallow time window;
- refusing to trace to the source.

## 3. Required entry packet

R7 requires a Semantic Repair Packet containing:

- Structural Repair Anchor;
- target semantic ID/content address;
- relevant source proposition/status;
- semantic transformations;
- adoption/authority transitions;
- relevant pool states;
- relevant revisions;
- evidence-supported affected descendants;
- RepairClosure;
- preserved unrelated refs;
- raw evidence pointers;
- Lineage Completeness Gate result.

## 4. Completeness gate

Automatic Repair Agent execution is forbidden when the packet is `LINEAGE_GAP`.

Missing semantic history must not be reconstructed as historical fact.

Allowed behavior under a gap:

- request additional evidence;
- downgrade to audit-only;
- require human review;
- leave repair unresolved.

## 5. Repair operations

When authorized and complete, repair may include:

- authority downgrade;
- source/state revision;
- pool-state invalidation;
- descendant invalidation;
- selective recomputation;
- dependent decision reopen;
- cache/memory invalidation where applicable.

## 6. Preservation

Unrelated semantic branches should not enter the Repair Agent context unless they become evidence-supported dependencies.

Success requires:

1. target integrity improvement;
2. correct recomputation/invalidation of affected descendants;
3. preservation of unrelated semantic structure within the declared boundary.

## 7. Verification

Record:

- repaired revision identities;
- recomputed descendant refs;
- residual old-lineage refs;
- old-lineage re-entry;
- preserved unrelated refs;
- semantic-lineage closure before/after;
- terminal outcome separately.

## 8. Nonclaims

Repair success does not establish CPR or prove that the Repair Anchor was the earliest causal origin.

## 9. Authorization

Any active repair requires a separate explicit authorization gate.
