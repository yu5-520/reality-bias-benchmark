# Stage-II Full-Context Audit Validator Recovery Note v1

Date: 2026-09-27  
Status: **CONTROL-PLANE RECOVERY / NO NATURAL RERUN / NO RE-AUDIT OF PRESERVED SUCCESSFUL CELLS**

## Incident

Initial Layer-C workflow:

- run: `36258923654`;
- 80-cell packet materialization: PASS;
- Layer-C claim: PASS;
- preserved successful full-context cell audits: 10;
- next cell: `G2-X4-T2`;
- failure: evaluator output rejected by the local validator with `bad semantic relation`;
- cross-group synthesis: not started;
- final Layer-C seal: not created.

The first ten successful cell audits were committed to:

`stage2-full-context-semantic-audit-results-v1`

and are immutable inputs to recovery.

## Diagnosis

The full-context semantic validator omitted the established semantic relation:

`MERE_VISIBILITY`

from its accepted relation vocabulary.

This is a control-plane schema/validator omission, not:

- a natural experiment failure;
- a subject/model failure;
- a monitor result;
- a CPR result;
- evidence that G2-X4-T2 lacks a semantic route.

The scientific prompt, model configuration, frozen evidence packet and CPR definitions are unchanged.

## Recovery boundary

Authorization:

`GitHub issue #266 — STAGE2 FULL-CONTEXT AUDIT VALIDATOR RECOVERY 1`

Recovery rules:

1. preserve the 10 completed audits;
2. do not re-audit those 10;
3. resume at G2-X4-T2 and continue only failed/unprocessed units;
4. accept `MERE_VISIBILITY` as an established non-adoption semantic relation;
5. preserve raw provider responses before semantic validation;
6. no subject calls or natural reruns;
7. no monitor access;
8. no blind-reference label access;
9. no repair or engineering B;
10. maintain original $10 total evaluator ceiling with a $0.5 reserve for the one pre-validation provider call whose token usage was not persisted by the initial runner.

## Scientific status

Layer C remains unsealed until:

- 80/80 eligible full-context trajectories are complete;
- 21/21 same-X/T cohort syntheses are complete;
- Dynamic CPR topology validation passes;
- the final Layer-C seal is written.

No partial Layer-C result may be reported as the completed full-context audit.
