# Stage II coordinated complete-route repair D — frozen result

Date: 2026-10-06  
Status: **SEALED**  
Case: **G3-X4-T2, history-24 same-parent contrast**

## Result in one sentence

The coordinated route cut suppressed the earlier **reimplementation** pattern but did not close the process: the branch performed no application writes and did not regenerate a new payment-button implementation path, yet review and verification obligations were repeatedly reopened and the run again consumed all 40 remaining turns.

The conservative classification is:

**PARTIAL_ROUTE_SUPPRESSION — implementation pressure suppressed, verification/review inertia persisted.**

## What D changed

D was the first treatment in this line to modify multiple current authority carriers in one frozen plan rather than repairing one field or one carrier class.

Before subject continuation it atomically:

1. superseded the four stale pending implementation/UX/test obligations;
2. reduced the current queue from 11 repeated scheduling entries to five current deliveries;
3. installed visibly attributed current-completion authority for QA, frontend, backend, product and release lead.

History, original task, subject model, application files, action budget and native ceiling were preserved. The intervention itself performed no application write.

The prior workflow `37406709650` failed before any job/provider dispatch and is not a scientific attempt. The canonical single D treatment is workflow `37406810362`.

## Immediate effect

The intended direct effect occurred.

At turn 26, frontend finalized that the existing `#pay-button`, `web/app.js` checkout POST and backend flow already satisfied the request and made no changes.

Across the full D suffix there were:

- **0** `write_file` actions;
- **0** delegate actions;
- no new application file;
- no re-created implementation branch comparable to the earlier local-repair expansion.

This is stronger than C's local message suppression because the current scheduler and completion-authority carriers were changed together.

## Downstream effect

The process still did not terminate.

At turn 31, release lead reopened four review paths—frontend, backend, QA and reviewer—even though the current-completion authority was present and the current implementation was already verified. Later actors repeatedly asked whether anything remained missing, whether additional UX states were needed, or whether more test coverage should be added.

The branch therefore shifted from implementation pressure toward verification/review pressure.

| History 25–64 | C carrier-class repair | D coordinated route cut |
| --- | ---: | ---: |
| Continued turns | 40 | 40 |
| Boundary | turn budget | turn budget |
| Post-parent writes | 0 | 0 |
| Messages | 13 | **17** |
| Tests | 6 | 5 |
| Final queue length | 23 | **18** |
| QA turns | 14 | 9 |
| Frontend turns | 12 | 9 |
| Backend turns | 5 | **9** |
| Release-lead turns | 4 | **7** |
| Product turns | 3 | 4 |
| Reviewer turns | 2 | 2 |

The smaller final queue does not establish closure because message generation increased and the native horizon was still exhausted.

## Mechanism interpretation

D removes an important easy explanation. Regeneration after C was not simply caused by four stale messages or by duplicated initial queue entries. D changed both, and also supplied a current completion state. The direct implementation obligation stayed suppressed.

What regenerated instead was a higher-level review/verification obligation.

The observed route is therefore:

`coordinated current-state cut -> direct no-change recognition -> release-lead reopening -> repeated verification/review -> new collaboration messages -> turn-budget closure`

This supports **partial route suppression**, not clean suppression. It also shows that a model-visible current authority statement is still a soft carrier: later agents can reinterpret the original task and create new review work because future execution capabilities remain unrestricted.

## Why D is not the final hard-authority test

D is materially stronger than B/C, but one variable remains.

The current completion authority was represented in model-visible host state. It did **not** bind future action authority. Agents remained free to create new messages, reopen review scope and continue collaboration even when no supported mismatch had been established.

A final discriminating contrast, if run, should not add more semantic instructions. It should hold the same route repair fixed and change only the post-repair execution boundary:

- preserve read/list/test/finalize;
- disallow new application writes unless already present in the frozen modify set;
- disallow collaboration expansion outside the frozen post-repair route;
- record any attempted expansion as a policy-boundary event rather than silently executing it.

That would test **hard post-repair authority** rather than another prompt/message repair.

## Evidence accounting

Canonical D:
- workflow: `37406810362`
- head: `cecea7a2fe49b4d1a9b03da3d213309b9fea2a8f`
- artifact: `11387743161`
- artifact digest: `sha256:322d0680c45b7fc29bfabc9d60418705d503e95f8dc63e9ab99a806b65165813`
- subject calls: **40**
- graph observations added: **3885**
- repair-exit hash: `17c1cdb4253568bec4d7d6ac06dc13f7dd2a85a88d27f128ccf99c742290b4c4`
- result summary hash: `542610e728dd1853d818542f6e046d8f783a51219a4ca776566ea23b0fe48b85`
- automatic retry: **false**
- C control rerun: **0**

No private product implementation or source is referenced by this experiment.
