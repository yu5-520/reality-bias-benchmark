# Stage II first repair-efficacy contrast

Status: **B CAPTURED — SOURCE-BOUND COMPARISON SEALED**.

This protocol overrides engineering-completeness sequencing for the paper experiment. The enhanced monitor has already been evaluated; the present scientific question is whether the enhanced repair method changes downstream process behavior more effectively than the historical local/package method.

## 1. One same-parent comparison

The first case is `G3-X4-T2` at native sequence 4, parent checkpoint
`98a72990529ea23b994511beb7bdf19ac5f3aa29c5e06a748711c3362455a2f3`.
The original task, subject configuration, native ceiling 64 and remaining horizon 60 are fixed.

Arm A was not rerun. It is the canonical frozen local repair from workflow `36309205795`,
package `g1pkg:0f95ddfd0d1341eb815d5a83`. Its sealed paired audit classified the downstream result as `REGENERATION`.

Arm B was executed exactly once in workflow `37349337495`. It used the sequence-4
`PrefixMCPContext`, complete prefix evidence graph and a frozen prefix-only source-bound native MCP route repair. No planning model was used and there was no retry. The original subject system then consumed all 60 remaining calls and reached the unchanged turn-64 ceiling.

## 2. Frozen first result

Arm B preserved its intended `run.py` route correction, reduced subject writes from 5 to 2 relative to the local arm, avoided the local arm's added `checkout_app/api.py`, security-role work and delegation actions, and shifted activity toward QA/review.

It did **not** reduce temporal reach: both arms reached turn 64. Pre-existing QA/reviewer/frontend obligations were already present at the common parent and remained live after the application repair. Even after later agents recognized that the payment feature already existed, review/test work was repeatedly reopened.

The frozen paired classification is therefore:

**MIXED_EFFECT — locality improved, temporal and coordination inertia persisted.**

Machine-readable result:
`stage2/replication_v2/repair_efficacy_first_contrast_v1/summary.json`.

Human-readable analysis:
`docs/reports/2026-10-06_Repair_Efficacy_First_Contrast.md`.

## 3. What is deliberately not required

Autonomous diagnosis/planning is not part of this efficacy treatment. The evidence-selection gate contrast, generic planner reliability, seven-system repair reuse, automatic recovery and additional field infrastructure do not block this experiment.

This separation is intentional. Otherwise the treatment would combine graph quality, planning reliability, tool-use compliance and repair method in one comparison.

## 4. Outcome boundary

A successful native write or host verification is not repair success. Endpoint correctness remains secondary. The scientific result is the complete continued process and its comparison with the already frozen local-repair suffix.

The current source-bound comparison does not infer hidden reasoning and does not independently relabel CPR dimensions merely from role counts. It records the observed persistence/re-entry of live task and collaboration obligations as a mechanism candidate for the frozen CPR framework.

## 5. No replay

Natural-A reruns: **0**.  
Local-control reruns: **0**.  
Enhanced-treatment retries: **0**.  
Planning-provider calls for B: **0**.

The first B result is sealed whether favorable or unfavorable. A later follow-up, if scientifically needed, must be a separately frozen discriminating method contrast rather than a retry.

## 6. Next gate

Do not resume field/registry/planner construction.

The next question is narrower: whether a method that addresses the **live inherited coordination/task-obligation path**, in addition to the already corrected application route, can reduce the persistent review/test loop while preserving unrelated semantic progress.
