# Terminal node-graph repair: frozen first round

Status: protocol and engineering preflight frozen before live model execution, 3 October 2026. Machine-readable specification: `configs/stage2_terminal_route_repair_first_round_v1.json`.

Execution record: [actual first-attempt results](../reports/2026-10-03_Terminal_Node_Graph_Repair_First_Attempt.md). Four branches consumed 21 calls and performed no repairs. These results establish neither repair efficacy nor graph advantage; no active branch was repeated.

## Question and experimental unit

Does access to a complete, source-bound observation graph help an agent distinguish a remaining process-account contradiction from a historical problem that is already resolved? The unit is a new repair attempt from a frozen terminal checkpoint. This is an engineering feasibility comparison, not an estimate of general repair efficacy.

This phase follows terminal evidence freeze. It is not a reconstruction of an earlier R7 midrun intervention. The full trajectory is legitimately available at this point; no terminal suffix is supplied to a midrun agent. Natural trajectories, old audit packets, old repair outputs and original graphs remain immutable. There are no original subject reruns.

## Frozen cases

| Case | Evaluation question | Native action scope |
| --- | --- | --- |
| G3-X4-T2, MCP | Does diagnosis reconcile the implemented feature with the inconsistent final process account? | Append a bounded revision request to the experiment-owned native host and continue through its original interfaces. Preserve every application file. |
| G2-X3-T2, A2A | Does diagnosis recognize that the historical launcher problem has already been resolved? | No mutation authorized in this round. Record a requested repair as a capability boundary; do not substitute another executor. |

Case selection uses the chronology-corrected semantic review. The earlier claim that the G3-X4-T2 feature was absent is not the retained finding: code was written at decision 10, while the final no-change account was inconsistent. G2-X3-T2 is a preservation case, not a remaining launcher failure. This retrospective selection limits generalization. Case purposes, audit verdicts, CPR labels and corrected rationales are evaluation-only; they are excluded from agent prompts and graph construction.

The A2A permission difference is identical between its two arms. The cases must not be pooled as equivalent repair opportunities, and no A2A live restoration claim follows from checksum/application restoration alone.

## LOCAL and GRAPH

Within each case, both branches restore the identical terminal checkpoint into fresh directories and use the same frozen subject/model configuration, original task, raw archive access, preservation scope and budget. LOCAL can list and read archive members. GRAPH can additionally query all nodes, bidirectional recorded edges, object histories and exact observation sources. The treatment is the navigable graph index, not additional raw evidence or a larger budget. This LOCAL terminal comparator is not the historical R7 local intervention.

All nodes remain addressable through pagination; there is no depth cutoff or preselected repair route. Unknown relations remain unknown. Capture order alone does not establish cross-clock causal order. Visibility, graph adjacency and observation counts do not grant write authority. The agent identifies the relevant route through its queries rather than receiving an audit-selected route.

The initial terminal-record query uses one of each arm's 12 query slots. Per response: at most 24,000 serialized characters; total returned evidence: at most 120,000 characters. Raw-member reads are paginated with at most 16,000 text characters. Failed query attempts consume the same query budget. Query requests, returned evidence, exact source hashes and model requests/responses are retained.

## Decision and execution gates

The agent returns REPAIR, NO_REPAIR_NEEDED or UNRESOLVED, with a reason and citations to inspected evidence. The latter two have no actions. REPAIR requires bounded actions, per-action reasons/citations, the exact parent hash and current native-state hash. Duplicate targets, unseen citations, stale state, unauthorized paths and writes to preserve-set files fail before execution.

The graph is diagnostic input. It is not sufficient to validate the semantic truth of a proposed diagnosis. Mechanical validation checks source bindings and authority; a separate outcome audit assesses the diagnosis and repair.

For MCP, the existing SoftwareEngineeringHost checkpoint adapter must round-trip the parent state exactly. A new revision request enters its entry-role inbox/queue and is serviced first. This is an explicit new phase in the experiment-owned host: the frozen answer/history is retained in the parent, and the new live phase reopens its terminal stop state. No foreign MCP implementation or protocol is patched. The existing native MCP interface supports reads/tests; application writes are blocked before invocation. The repair executor exits before passive continuation monitoring starts. Native actions, continuation outputs, new checkpoints and file manifests are recorded.

The public implementation does not contain the private product registry or repair fabric. First-round actions concern the process account only. Application-node mutations and a live A2A repair executor require a separately frozen extension; they are not silently introduced here.

## Budget and first-attempt retention

Two cases, two arms per case, four attempts. Each diagnosis has at most six provider calls. Only an authorized MCP repair can consume up to four additional continuation calls, also bounded by the original remaining horizon. Maximum across all arms: 32 live calls. No transport or JSON-format retries, no success retries, no automatic subject reruns, and no overwrite of an existing output directory. Failed provider requests count as attempts.

The workflow checks the frozen configuration, rejects workflow reruns and rejects a previously retained artifact containing an active attempt for the same configuration. Active execution requires the explicit commit marker `[run terminal route repair]` or an execute-enabled manual dispatch by the repository owner. Failed first attempts are retained alongside successful attempts. Missing credentials produce a zero-call boundary rather than changing providers or models. An environment-only artifact with no `terminal-active/` files can precede a corrected first execution; its archive is inspected and retained, rather than deleted or bypassed. The frozen MCP SDK is installed with its original workspace lock using `uv sync --frozen --no-default-groups`.

## Outcomes and interpretation

Record independently: diagnosis evidence, decision class, queries/calls, gate rejection, native action receipts, application preservation, native continuation and separate semantic outcome. PASS means the engineering path completed; it is not semantic repair success. NO_REPAIR_NEEDED is neither failure nor success without evidence review. A continuation boundary is reported even if some actions occurred.

The preserved original graph plus `post_repair_observation_delta.json` binds file/native action changes. This delta is not a complete regenerated post-repair semantic graph, and no semantic dependency edges are inferred. Native post-repair evidence is retained for subsequent comparison.

Zero-call preflight decisions are scripted fixtures, not model diagnoses. The scripted MCP bridge probe tests restoration, request injection, finalization and passive monitoring; it makes no live provider or MCP tool call. These checks establish execution readiness only.

## Reproduction

1. Materialize the two natural-A archives from the evidence commits pinned in the G2/G3 semantic-audit configs.
2. Run `scripts/materialize_stage2_terminal_route_graphs.py --source-root SOURCES --out GRAPHS`; both graph hashes must match the frozen case config.
3. Run `scripts/run_stage2_terminal_route_repair.py --source-root SOURCES --graph-root GRAPHS --out PREFLIGHT`.
4. Run `scripts/check_stage2_terminal_route_native_bridge.py --source-root SOURCES --graph-root GRAPHS --out BRIDGE`.
5. With the frozen provider credential and original pinned MCP SDK, add `--execute` and use a fresh output directory for the four live first attempts.

Local permanent preflight receipts and exact implementation hashes are under `stage2/replication_v2/terminal_route_repair_preflight_v1/`. The workflow retains complete per-attempt evidence. Later active results must be reported separately from these fixtures.
