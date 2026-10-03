# External monitoring and its attached repair system

The unit of engineering is the monitoring system with its attached repair system. Safety, effectiveness, automation and reuse are separate requirements of one closed operation, not four names for a successful write. The active offline coordinator is `OfflineRouteRepairSystem`; previous integration scripts remain frozen reproduction fixtures. The coordinator uses the existing native field and current-host bindings directly. It does not invoke the historical local revision harness.

Machine-readable requirements: `configs/stage2_monitor_repair_system_v1.json`. Implementation: `stage2/route_repair/offline_system.py`, `system_contract.py`, `recovery_journal.py`.

## Responsibility and boundaries

| Component | Responsibility | Does not establish |
| --- | --- | --- |
| External read-only monitor | Record sources, versions, clocks, changes and missing evidence; preserve the full graph | Semantic truth, write authority or a complete causal graph |
| Repair planner | Propose an evidence-grounded route, entry location, coordinated actions and preserve/verify obligations | That its own interpretation is correct |
| Host execution validator | Re-read inspected witnesses, recompile the whole plan, bind original task and exact native capabilities, enforce field/version/dependency limits | Repair effectiveness |
| Continued monitoring and independent evaluation | Examine old C/P after historical re-entry, transformed descendants and unrelated semantic progress | Success from an endpoint or a repair agent's completion statement alone |

The original broad task and available native capabilities are retained before diagnosis. Exact field grants, values, source versions and dependencies are fixed after a proposal and before the first write. A future agent planner must select a route from full evidence without receiving case-specific correct fields/values as its input. Today's integration is explicitly a previously sealed manual proposal; it cannot demonstrate autonomous diagnosis. Hashes provide integrity, not signatures or authorization.

## Route and entry selection

Do not always repair the root, the last answer, or the most connected node. Select the earliest evidence-supported transition where information gains unsupported operational authority and a legitimate native action is available. Record whether the problem is at the source, a transformed descendant, an obligation or a later acceptance gate. The present implementation records this as a review obligation; it does not algorithmically infer the first authority transition.

Coordinate modifications along demonstrated semantic inheritance. Preserve other semantics carried in the same object. A graph neighbor or a reachable node remains an inspection object until its relation is supported; an unknown relation becomes a verification task, not a write grant. Current field grants protect bytes and selected values. Preservation of unrelated semantic progress requires continued observation and separate evaluation.

## Implemented automatic offline operation

1. Replay the host-retained successful query log against pinned native sources. Rebuild exact witness spans and recompile the proposal with separately retained policies. A re-sealed forged bundle cannot substitute a source or expand its grants.
2. Build a system contract over the full graph. For each diagnosed transition, retain obligations for old information/task authority, historical re-entry, transformed descendants and unrelated semantic progression. Keep unsupported relations explicit.
3. Bind all available native surfaces and host verification implementations before plan actions. Unknown or unsupported verification operations block branch construction. Execute only in a fresh copied branch.
4. Execute ordered application actions, host-defined checks and optional current-host answer supersession. Detect verifier-induced application drift. Stop dependent actions on failure and retain actual native outputs and a full observed graph.
5. Read and checksum every new capture. Preserve every historical observation/edge and all historical nodes. Without an actual repair-agent exit and ordered native continuation, emit `AWAITING_NATIVE_CONTINUATION`, not repair success.
6. Maintain a host-owned durable hash-chained journal. After interruption, inspect current versions to distinguish expected state, unchanged pre-state, divergent state and intermediate same-object versions. Reconciliation never replays, rolls back or resumes a subject automatically.

The journal uses exclusive sequence files and filesystem flushes on one coordinator. It detects stale coordinators and torn/tampered entries. It is not a native-state checkpoint, OS-level compare-and-swap or concurrent isolation. An expected hash after an interrupted call does not prove dependency completion or semantic effectiveness; inspect the retained receipts before any new plan.

## Post-repair observation

`assess_continuation` accepts complete before/after graphs and a host source reader. A repair exit must be a new source-bound `REPAIR_AGENT_EXIT` native record. Only observations later in the same native clock are ordered after it. Other clocks remain unordered. No exit event is manufactured for an offline script or application write.

Literal historical content hashes appearing after exit are collected across all observed objects, including newly appearing carriers. They are version reappearance clues, not confirmed regeneration or semantic adoption. Transformed descendants may have different words/hashes; independent semantic path review remains necessary. The evaluator records that gate as pending, even when mechanical postconditions pass. It cannot declare success without the missing native continuation and semantic evaluator.

## Reuse and evidence

Reuse the contract, planning revalidation, journal and assessment format. Bind original native operations and trusted verification implementations separately for each supported environment. Do not modify a framework to fit a unified protocol and do not grant writes into foreign private state or historical messages. This release demonstrates the coordinator on synthetic multiple-object application fixtures and the frozen MCP G3-X4-T2 application/current-host branch. It does not establish seven-framework repair reuse.

Frozen integration: `stage2/replication_v2/monitor_repair_system_integration_v1/`. The input remains the separately sealed manual inspected proposal. Its application and host policies are retained by the host. Offline application actions and controlled handler checks are engineering checks; no agent/model runs or natural trajectories are repeated.

## Remaining implementation order

Agent route diagnosis and planning; independently bound semantic/authority assessment with exact witnesses; native continuation capture and recovery capability; same-parent method/budget/outcome freeze; then a separately specified live evaluation. Keep current capability limits explicit. Mechanical replay readiness cannot substitute for scientific readiness or autonomous system readiness.
