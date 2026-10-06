# Stage II bounded verification / closure contrast F

Date: 2026-10-06  
Status: **FROZEN BEFORE THE SINGLE F TREATMENT**

## Why F exists

E established a hard post-repair capability boundary. It prevented all observed
collaboration-expansion attempts from taking native effect and reduced the final
queue from 18 to 5, but the branch still exhausted all 40 remaining calls through
repeated read/test behavior.

F holds both earlier interventions fixed:

1. the same coordinated history-24 route cut as D;
2. the same hard post-repair capability envelope as E.

The only new variable is a finite verification/closure rule.

## Frozen verification epoch

Each retained role receives at most one evidence-gathering batch. A batch may
contain the existing read/list/test actions, subject to the unchanged native
action-count ceiling.

After that batch, the role must produce a disposition:

- a specialist may finalize its local finding or report it to release lead;
- release lead may finalize the user-facing result.

If a role asks for another evidence batch, the gate denies it and returns a
model-visible closure notice. The role receives one adaptation call. If it still
does not provide a permitted disposition, the experiment ends at an explicit
`ESCALATION_REQUIRED` boundary.

Already-disposed roles do not receive new provider calls if stale queue entries
remain; those scheduler entries are retired with receipts.

The global treatment ceiling is 15 provider calls: five retained roles times a
maximum of three states (evidence, decision, one adaptation).

## What F does not do

F does not change application files, task text, historical evidence, the D repair
set, the E authority envelope or the subject model. It does not force a success
answer. It only prevents an already-repaired branch from spending the complete
native horizon on unbounded repeated verification.

The frozen E suffix is the control and is not rerun.
