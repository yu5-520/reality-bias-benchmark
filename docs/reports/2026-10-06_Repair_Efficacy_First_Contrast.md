# Stage II first repair-efficacy contrast — frozen result

Date: 2026-10-06  
Status: **SEALED**  
Case: **G3-X4-T2**  
Scientific object: **repair-method downstream process effect**

## Result in one sentence

The enhanced source-bound node-route repair **reduced downstream implementation expansion but did not close the process**: compared with the frozen local repair, it used fewer writes, avoided the additional backend API/security/delegation expansion, and preserved its direct route correction, yet the continued system still consumed the full 60 remaining subject calls and reached the original 64-turn ceiling through repeated review/test work.

The first enhanced-repair result is therefore classified as **MIXED_EFFECT — locality improved, temporal and coordination inertia persisted**.

## Frozen comparison

Both arms start from the same G3-X4-T2 sequence-4 parent:

`98a72990529ea23b994511beb7bdf19ac5f3aa29c5e06a748711c3362455a2f3`

The original task, subject profile, remaining horizon 60 and native ceiling 64 are unchanged.

The local control is **not rerun**. It is the canonical one-shot repair from workflow `36309205795`, already audited as `REGENERATION`.

The enhanced treatment is the single workflow `37349337495` at head
`408258db42df4a016276ea9f5ecebb8c49e584d9`. It used zero planning-model calls, one frozen prefix-only source-bound route action through the unchanged official MCP interface, then released the original subject system for all 60 remaining calls. No retry occurred.

| Measure | Frozen local repair | Enhanced node-route repair |
| --- | ---: | ---: |
| Final boundary | turn budget | turn budget |
| History at boundary | 64 | 64 |
| Subject continuation calls | 60 | 60 |
| Subject write actions | 5 | **2** |
| Distinct subject-written refs | 3 | **2** |
| Delegate actions | 4 | **0** |
| Backend role turns | 13 | **5** |
| Security role turns | 3 | **0** |
| QA role turns | 15 | 21 |
| Test actions | 3 | 6 |
| Enhanced-monitor new observations | — | 6293 |

The local arm wrote the frontend pair and additionally created/changed
`checkout_app/api.py`; it also entered security/delegation work. The enhanced arm's subject continuation wrote only `web/index.html` and `web/app.js`. Its route repair of `run.py` remained present.

## What improved

The enhanced intervention changed the alternate launcher default so an unset
`CHECKOUT_COMPAT` selected the documented current service while retaining explicit legacy mode. The native write and controlled route verification passed, and that repaired route remained in the final branch.

More importantly for process comparison, the downstream mutation surface was narrower. The enhanced branch did not reproduce the local arm's extra backend API file, security-role participation or delegation actions. Backend participation dropped from 13 turns to 5 and subject write actions from 5 to 2.

This is evidence that the node-route method improved **intervention locality and implementation-scope control** in this frozen case.

## What did not improve

The repair did not shorten temporal reach. Both methods reached the original turn-64 ceiling.

The reason is visible before the first post-repair subject call. The restored parent already carried live QA, reviewer and frontend obligations created before the intervention. The route repair changed application state; it did not rewrite historical messages, queue state or collaboration obligations.

After the payment button had been written, several later frontend/backend responses explicitly recognized that the feature already existed or required no further change. That recognition still did not close the run. Release-lead actions repeatedly reopened review and testing, including late in the observation window, and the system exhausted the remaining budget.

The observed mechanism is therefore not “the enhanced repair failed to write the right file.” It is:

> **a locally corrected application route can coexist with inherited collaboration/task obligations that remain operational and continue to drive work.**

That separates repair locality from process closure.

## Paired interpretation

The first contrast is frozen as:

- direct route target: **preserved intended correction**;
- target-task work after repair: **regenerated once**;
- implementation mutation breadth versus local repair: **reduced**;
- collaboration scope: **mixed / redirected** rather than cleanly reduced;
- temporal reach: **stable at the native ceiling**;
- route relation: **diverged**;
- overall process effect: **MIXED_EFFECT**;
- mechanism class: **LOCALITY_IMPROVED_TEMPORAL_AND_COORDINATION_INERTIA_PERSIST**.

The collaboration classification is deliberately not “decreased”. Security disappeared and backend work fell sharply, but QA/review activity increased and product entered the route. The method redirected work away from broad implementation expansion toward repeated verification/review rather than terminating it.

## CPR / authority boundary

This comparison does not mechanically relabel C/P/R from role counts or event order. It does, however, expose a source-bound mechanism candidate relevant to P/R: collaboration obligations already present at the parent remained active after the application route was repaired, and later review/test requests repeatedly re-entered the process.

A later semantic synthesis may connect this observation to the paper's frozen CPR definitions, but this result does not infer hidden reasoning or declare a universal repair-success rate.

## Evidence accounting

Local control:
- canonical workflow: `36309205795`
- artifact: `10927609662`
- artifact digest: `sha256:5e8076b9d939adf1671dd892d683d4bd12eee1bedf15228d409191509f8037ac`
- selected package: `g1pkg:0f95ddfd0d1341eb815d5a83`
- natural rerun: **0**
- local-repair rerun: **0**

Enhanced treatment:
- workflow: `37349337495`
- artifact: `11361543373`
- artifact digest: `sha256:91ebc92f0b58ac3b2bd7090cd356e6a98a974a90fa1e86907e0e41587f9814b5`
- plan hash: `5ca73f0716a780d0dd8c7000057a7a4abaf3fa5f55f9ea52382a92a5bcebfe4d`
- repair-exit hash: `114a64c61a2db2ca09b62625d7be71768408a90a57c7283ceb01bce55c0ea44d`
- efficacy receipt hash: `7cb99dadcc2471cbd60b9f71746bf2ff02b529cd59e14690f630bbfb25d82d1d`
- planning provider calls: **0**
- subject provider calls: **60**
- automatic retry: **false**
- paid semantic reviewer: **0**

A successful write is not counted as repair success. The result comes from the complete continued process.

## Next scientific gate

Do **not** return to field, registry or autonomous-planner construction.

The next discriminating question, if one additional treatment is needed, is narrower:

> When the application route is already corrected, does a repair that also addresses the **live inherited coordination/task obligation path** reduce the persistent review/test loop without disturbing unrelated semantic progress?

That should be a separately frozen method contrast, not a retry of this B arm. The first result must remain unchanged.
