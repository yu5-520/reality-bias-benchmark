# Stage II bounded verification / closure contrast F — frozen result

Date: 2026-10-06  
Status: **SEALED**  
Case: **G3-X4-T2, history-24 same-parent contrast**

## Result

F converted the remaining E failure mode from an unbounded read-only loop into an
explicit bounded outcome.

The coordinated repair and hard authority envelope were unchanged. Each retained
role was allowed one evidence-gathering batch, followed by a required disposition
and at most one adaptation call after a budget denial.

The branch ended after **11 logical subject responses**, rather than E's 40,
with:

- **0** application writes;
- **0** final pending queue entries;
- **4** role dispositions;
- **3** verification-budget denials;
- **1** hard-authority denial;
- terminal boundary **ESCALATION_REQUIRED**.

This is classified as **BOUNDED_VERIFICATION_ESCALATION**, not automatic repair
success.

## Path

The first response was the exact QA turn-25 response already obtained in workflow
`37421493309`. It was never resampled. That response read the five frozen
verification sources.

The completed continuation then observed:

- turn 26: frontend finalized its local finding;
- turn 27: backend finalized its local finding;
- turn 28: product used its one evidence batch;
- turn 29: release lead used its one evidence batch;
- turn 30: QA requested another test and was denied because its verification
  batch was exhausted;
- turn 31: product requested another read and was denied;
- turn 32: release lead requested another read and was denied;
- turn 33: QA adapted and finalized;
- turn 34: product adapted and reported to release lead;
- turn 35: release lead attempted to delegate new frontend/backend/QA work.
  The hard authority gate denied the expansion and the bounded closure rule
  terminated the branch at `ESCALATION_REQUIRED`.

The system therefore did not fabricate a user-facing success answer. It exposed
the unresolved decision as an escalation boundary instead of allowing another
verification cycle.

## Comparison with E

| Measure | E hard authority | F bounded closure |
| --- | ---: | ---: |
| Logical subject responses | 40 | **11** |
| Application writes | 0 | 0 |
| Executed scope-expansion messages/delegates | 0 | 0 |
| Final queue | 5 | **0** |
| Terminal condition | turn budget | **explicit escalation** |

The scientific change is not merely fewer turns. F changes the semantics of the
terminal state from accidental budget exhaustion to an auditable control
decision.

## Resume accounting

F experienced technical harness interruptions and was not resampled.

1. Workflow `37421493309` obtained one real QA turn-25 provider response, then
   failed before any action from that response had native effect.
2. Workflow `37421933976` reused that exact response with zero new provider
   calls, then failed before turn-26 dispatch because the live connector's
   logical call counter had not been advanced.
3. Workflow `37422296557` failed in preflight with zero provider calls.
4. Workflow `37422418453` reconstructed the frozen parent, verified the exact
   turn-25 request/response hashes, reused that response without provider recall,
   advanced the logical sequence, and issued only the remaining **10** new
   provider calls.

Thus the completed F trajectory contains exactly **one original frozen first
response + ten subsequent live responses**, not a retry-selected replacement.

## Mechanism conclusion

Across the repair sequence, the remaining failure moved through distinct layers:

`local regeneration -> descendant obligation regeneration -> coordinated review
inertia -> hard-gated read-only inertia -> bounded disposition/escalation`.

The result supports a layered repair architecture. A complete graph alone does
not repair the process; graph evidence must be converted into a coordinated
route intervention, persistent execution authority, and a bounded
verification/closure rule.

F is the stopping point for this mechanism series. A new experiment should be
opened only for a different scientific question, not to manufacture a cleaner
outcome.
