# Terminal node-graph repair: actual first-attempt results

> Design correction: these are premature diagnostic-harness records, not first attempts of the intended complete node-route repair method. The graph only supplemented diagnosis, while the proposed action was restricted to the legacy local process revision. The coordinated route plan, native plan executor and enhanced full post-repair graph were absent. Keep all records; do not interpret these outcomes as a test of the intended method. See [design correction](2026-10-03_Node_Route_Repair_Design_Correction.md).

The frozen two-case, four-arm comparison completed with 21 live provider calls and no repair actions. The A2A preservation decisions were supported by inspected terminal source files. Neither MCP arm repaired the remaining process-account contradiction. These results do not establish graph-guided repair efficacy or a graph advantage.

Execution commit: `7348e20ecbf6720150fcfc81fe07a5b49ec3a30c`. Workflow: [37097781266](https://github.com/yu5-520/reality-bias-benchmark/actions/runs/37097781266). Complete artifact: [11264897469](https://github.com/yu5-520/reality-bias-benchmark/actions/runs/37097781266/artifacts/11264897469). Its ZIP SHA-256 is `540b6f712b001d08891fb00bbf829c0db6fbd22cbee3dbc41067bdd0343fa515`. Permanent results and the complete compressed request/response/query trace are in `stage2/replication_v2/terminal_route_repair_first_attempt_v1/`.

## Actual outcomes

| Case / arm | Calls | Queries / invalid | Decision or boundary | Native actions |
| --- | ---: | ---: | --- | ---: |
| G3-X4-T2 MCP / LOCAL | 6 | 9 / 4 | No decision within the frozen call budget | 0 |
| G3-X4-T2 MCP / GRAPH | 4 | 7 / 2 | UNRESOLVED | 0 |
| G2-X3-T2 A2A / LOCAL | 5 | 11 / 3 | NO_REPAIR_NEEDED | 0 |
| G2-X3-T2 A2A / GRAPH | 6 | 12 / 3 | NO_REPAIR_NEEDED | 0 |

All four downloaded application trees exactly match their respective terminal parent file manifests. Original subjects were not rerun. There were no continuation calls, application writes, native revision actions or separate paid evaluator calls. The provider reported 116,230 prompt tokens and 3,324 completion tokens, 119,554 total. Both arms used the frozen deepseek-flash configuration; responses identify that alias. The configured DeepSeek-V4.1-Flash backend version was not independently attested by the response.

GitHub marks the workflow failed because one arm reached its budget boundary. This is the retained first-attempt result; the other three mechanical PASS receipts do not establish semantic repair success. No active attempt was repeated.

## Evidence review

This is an exploratory, source-based offline review after execution, not an independent blind semantic audit. It uses the existing chronology-corrected finding to identify what remained unresolved, not to supply a missing diagnosis retrospectively.

In A2A, both agents read the actual terminal frontend/backend files and cited their hashes. They identified the payment button, its checkout request, matching server response fields and error handling. GRAPH also inspected `run.py` and described the current server as the default, with the legacy route explicitly opt-in. LOCAL inspected the HTTP test source; GRAPH inspected the checkout unit test source. Reading a test file is not evidence that the agent ran the test. Offline execution of the existing frozen application tests after the trial passed all eight A2A tests, including default/compatibility launcher paths and HTTP responses. These checks support preservation of this case, without establishing production readiness or live A2A restoration.

In MCP, LOCAL repeatedly navigated archive member lists and never emitted a terminal decision. GRAPH queried the two frontend nodes, but did not retrieve observation sources, file histories or the actual terminal application content. Its UNRESOLVED rationale generalized two failed bare-path requests into a source-availability problem. That generalization was incorrect: the terminal archive contains both frontend files at `checkpoints/<terminal_hash>/application/web/index.html` and `.../web/app.js`, with 535 and 1,228 bytes respectively. The source bindings themselves were not missing. Both files can be read through the same raw-member interface available to either arm.

The retained MCP finding is a contradiction between the observed change history and the final no-change account. Verifying that a button exists at the terminal endpoint would not alone resolve that contradiction. Neither arm reconstructed the change history or tested the account against it. The two existing MCP checkout unit tests passed offline; they do not validate the terminal process account or show that this repair round succeeded.

## Where this implementation failed to help

1. The agent-facing paths were object refs such as `file:web/app.js`, while raw reads required archive member paths. There was no explicit mapping from the current file ref to its terminal checkpoint member in the initial prompt. All four arms first attempted bare paths and consumed budget on missing-member errors.
2. The archive list was unfiltered and sorted. MCP had 963 members, with many tool-wire files before checkpoint application files; A2A had 287 members and exposed the checkpoint directory on the first page. Retrieval effort was therefore sensitive to archive layout. MCP LOCAL also requested an invalid page size of 63; the maximum of 50 was enforced but not stated in the query-parameter prompt.
3. The graph was complete and queryable, but this did not make its sources easy to use. MCP GRAPH received roughly 15,000-character node pages with observation IDs and event edges, then stopped without using the source lookup. Completeness is an observation-coverage property; usable route evidence requires an explicit path from node/version to content and change history.
4. The diagnostic task remained too broad to reliably elicit a chronology-based process-account check. The corrective diagnosis would need to distinguish terminal functionality from claims about prior actions. This must be supported by captured evidence, without revealing the evaluation verdict.

These observations do not isolate an effect of graph topology, model reasoning or a semantic explanation mechanism. They identify usability/budget limitations of this first harness. A2A GRAPH used one more call than LOCAL and reached the query ceiling; there is no efficiency advantage in that case.

## Follow-up boundary

Do not rerun these four attempts to replace their outcomes. First repair navigation offline: expose the exact terminal member mapping to both arms, state parameter bounds, support prefix-filtered archive listing, and add a source-bound current-version lookup without inferred authority. GRAPH should additionally support compact chronological change navigation with explicit clocks and source locators. Use the same underlying source access and budget policy for both arms.

A later live comparison would be a separately frozen follow-up protocol, with this result retained as the first attempt. It must assess the historical action/account relationship rather than merely checking the presence of the final feature. Code-level complete-route mutation and a live A2A repair executor remain separate extensions. The present round cannot support a claim of successful full-route repair in the manuscript.

## Offline verification

`scripts/validate_stage2_terminal_route_first_attempt.py --source-root SOURCES --graph-root GRAPHS` replays every retained query against the pinned archives/graphs, verifies citations/decision gates, checks the frozen implementation/subject bindings and reconciles all 21 saved requests/responses. It makes no model calls and does not infer semantic efficacy.
