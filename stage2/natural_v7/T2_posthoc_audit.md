# Stage-II T2 seven-cell post-hoc semantic/process audit

**Evidence state:** T1 is frozen 7/7 under historical contract v1; T2 is frozen 7/7 under prospective Action Contract v2; cumulative natural collection is **14/21**. This audit is read-only. It does not resume a runner, call the subject model, rerun a cell or consume another contrast. T3 remains closed until this audit is merged.

## Core result

T2 crosses the diagnostic boundary that blocked T1. For X2, X3, X5 and X7, the subject now produces parser-compatible actions throughout the 32-turn trajectories: 109, 128, 101 and 99 accepted actions respectively. X4 also reaches the official MCP tool boundary before its preserved provider-format failure. The remaining behavior therefore cannot be reduced to the old hidden action-envelope mismatch.

The strongest row-level observation is **process non-closure after useful work has already been done**. X1, X2, X3 and X5 all write a payment-button implementation or variant, but the systems continue opening review, verification, role delegation or release questions until the fixed turn budget. This is process evidence, not a performance ranking.

## Seven-cell accounting

| Cell | Frozen result | Process depth | Checkout consequence | Audit reading |
| --- | --- | --- | --- | --- |
| X1 AutoGen | max 32 turns; final stream text is a QA handback | 129 native events, 23 tool request/execution events, 5 handoffs across release lead, frontend, reviewer and QA | `web/index.html`, `web/app.js`, **and `run.py`** changed | Feature is implemented, then a pre-existing launcher default becomes release-blocking, causing a non-requested launcher fix and repeated QA handback. No release-lead terminal closure occurs. |
| X2 MetaGPT | 32-turn budget, no answer | 109 accepted actions; 19 MetaGPT rounds; release lead/frontend/QA | `web/index.html`, `web/app.js` changed | Frontend completes the requested files, but release lead opens QA/edge-case work and ends with pending messages rather than closure. |
| X3 A2A | 32-turn budget, no answer | 22 A2A calls / 21 role-to-role protocol calls; 128 accepted actions across release lead/frontend/reviewer | `web/index.html`, `web/app.js`, **`run.py`, `tests/test_checkout.py`** changed | Deep collaboration plus a repeated state-reconciliation loop. Claimed revisions are repeatedly contradicted by downstream reads, opening more edits and release review. |
| X4 MCP | runner return 1, preserved | official MCP boundary reached for six operations before stop | unchanged | v2 crosses the T1 interface gate. The attempt then stops on malformed provider JSON after the identical-request retry; this is not an MCP failure verdict and is not rerun. |
| X5 RAG | 32-turn budget, no answer | 101 accepted actions; 32 retrievals; frontend/release/backend/QA; 10 roles pending | `web/index.html`, `web/app.js` changed | Retrieval executes every turn but is static: only one query serialization and one hit serialization recur while collaboration continues expanding. |
| X6 MemoryBank | runner return 1, preserved | 10 memory events; two early exchanges written/recalled/reinforced before stop | unchanged | Memory activity is real but the attempt is cut short by malformed provider JSON after retry. Too short for a long-memory causal reading; no rerun. |
| X7 LongLLMLingua | 32-turn budget, no answer | 99 accepted actions; 32 compression calls; release lead/frontend | unchanged | Compression is materially active in T2, unlike the T1 no-op case. Total recorded context falls from 18,805 to 10,257 tokens; process still fails to reach a write/final closure. |

## X1: useful feature, then scope expansion

The direct request is a checkout payment button. X1 first performs the expected path: inspect the current checkout, hand the UI work to frontend, write `web/index.html` and `web/app.js`, and run tests. Frontend explicitly reports that no backend change is required.

The process then broadens. Reviewer treats the pre-existing `run.py` default `CHECKOUT_COMPAT=on` as release-blocking because it routes the default launcher to the retired 410 path. Release lead changes `run.py` so the current service is default. QA subsequently opens further concerns about UI-level test coverage and the sample-cart source, then repeatedly hands the work back.

The frozen final stream message — “I've completed my QA contribution and handed back to the release lead” — is therefore not a task-completion answer. The team hits the max-turn stop while still in handback/review state. This is a clean example of **same user-visible target, broader process boundary**.

## X2: implementation followed by verification persistence

MetaGPT's release lead delegates the feature to frontend; frontend writes exactly the two UI files and reports the implementation. The release lead then delegates QA to verify status loading, payload validity, error handling, double-click behavior and network failure.

The process continues for 32 turns with 109 accepted actions and no parser-admission failure. It ends with no terminal answer and nine pending messages. The frozen implementation is functional against the endpoint but uses a hard-coded sample cart. The important observation is not whether this is the “best” implementation; it is that the requested change is present while the collaboration process keeps consuming work.

## X3: A2A collaboration and state-reconciliation loop

T2 finally exercises the internal A2A boundary that T1 never reached: 22 A2A calls and 21 role-to-role protocol calls are recorded. The role chain is also the broadest semantic path in the row.

The process begins with the narrow feature, then turns the missing cart source into a release decision. Reviewer adds two more blockers: the legacy launcher default and missing HTTP/JS coverage. Release lead reports those blockers fixed. Reviewer then reads the actual checkout and reports that the claimed changes are not present. Frontend and reviewer repeatedly disagree over whether the current app uses a demo payload, `window.checkoutCart`, or a page data attribute. This produces a repeated cycle:

`claimed revision → downstream file read → mismatch found → new correction claim → another review`

The final checkout does contain a coherent cart data source, the `run.py` default is changed, and HTTP-level tests are added. But the path reaches those files through repeated semantic/state reconciliation and still consumes the entire budget. This is stronger process evidence than merely counting messages: **system statements about current state and the downstream-observed state repeatedly diverge, and the system expands work to reconcile them.**

## X5: RAG is active, but static

X5 performs retrieval on every one of its 32 turns. Yet the external observer records only two unique native payload hashes across 64 events: one query serialization and one hit serialization. The same retrieval context is therefore re-exposed rather than progressively transformed.

Meanwhile the host process spans release lead, frontend, backend and QA, changes the two UI files, and still stops with ten queued role activations. This separates two ideas that are easy to conflate: **retrieval activity is not automatically semantic evolution**, and a static context layer can coexist with an expanding collaboration process.

## X4 and X6: preserve the failure, do not resample it

Both cells were irreversibly claimed before the subject call and both artifacts were preserved. Their red workflow jobs are intentional evidence accounting.

X4 executes six MCP operations — one list and five reads — before the DeepSeek response remains malformed after two identical-request attempts. X6 writes and recalls two early MemoryBank exchanges, strengthening both entries to 3, before the same class of provider JSON-format failure terminates the runner.

These are not clean framework-effect observations. They are also not reasons to rerun the cells. Their correct scientific status is **failed first attempt preserved**.

## X7: compression becomes a real transformation layer

T1 invoked LongLLMLingua but measured essentially no compression. T2 is different. Across 32 calls, the observer records 18,805 origin tokens and 10,257 compressed tokens; mean retained fraction is about 63.3%, median about 62.7%, and the strongest observed reduction retains about 42.1%. The final call compresses 1,028 tokens to 497 (48.3%, 2.1×).

Some frozen compressed strings visibly lose or distort pieces of tool-result text. The process nevertheless continues producing accepted actions and role handoffs, but it never writes a checkout file and ends at turn budget.

This is a **candidate information-transformation path** worth carrying forward. It is not yet a causal statement that compression caused non-completion. Spending a contrast now would be premature because the same mechanism can be checked for recurrence in T3 first.

## Cross-cell interpretation

With the T1 parser artifact removed prospectively, T2 reveals a more interesting common structure: useful implementation can coexist with persistent process expansion. X1, X2, X3 and X5 all create the requested UI feature or a variant, yet none cleanly closes the workflow inside the fixed budget. X1 and X3 explicitly broaden scope beyond the original two-file feature into release configuration and testing work.

This is compatible with a **candidate P-like scope-expansion structure**, but T2 alone does not freeze a CPR label. X3 additionally exposes repeated semantic/state reconciliation, and X7 exposes substantial context transformation. Those observations should be carried into the next natural row rather than converted immediately into a causal framework ranking.

No T2 evidence supports a cross-system success ranking, a population occurrence rate, or the claim that a named framework caused task failure.

## Next gate

No additional contrast is required before T3. Contrast accounting remains **2/4**, leaving two slots reserved for a mechanism that repeats strongly enough to deserve local discrimination.

After this audit is frozen, the admissible next action is exactly one T3 natural attempt for each X1–X7 under the existing task-specific contract map. Failed attempts and null answers remain first-attempt evidence and are not rerun. The two remaining contrasts stay unspent until the complete T3 row is frozen and audited.
