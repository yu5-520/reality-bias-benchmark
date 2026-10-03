> Current replay correction: use [P2 native evidence replay v2](StageII_P2_Replay_Correction_v2.md). The v1 graph promotion and localization comparison are withdrawn; prior frozen files remain historical evidence.

# Stage-II Enhanced External Evidence-Graph Monitor and Route-Repair Protocol v1.0

Status: implementation baseline. This protocol adds a public research prototype only. It does not change frozen natural trajectories, historical R7 outputs, studied framework protocols, or existing evidence.

## 1. Research boundary

The enhanced monitor remains an external, read-mostly process-observation layer. It may consume already-observed runtime events, frozen evidence, corrected chronology, source-backed structural lineage and separately produced semantic judgments. It may normalize, index, connect, inspect and export those observations.

It may not modify AutoGen, MetaGPT, A2A, MCP, RAG, MemoryBank or LongLLMLingua protocols; require a new shared registry inside the studied systems; redefine framework-native input/output contracts; inspect or mutate framework-private runtime state; rewrite messages or schedule agents as part of monitoring; infer semantic adoption from temporal adjacency, lexical similarity or hash equality; or convert visibility into write authority.

The public prototype is independently implemented from the experiment repository's own evidence contracts. It contains no external product registry, deployment fabric, governance policy or product-internal repair implementation.

## 2. Existing evidence substrate

The enhanced monitor builds on existing public research artifacts rather than replacing them: arena/checkpoint_chronology.py for fail-closed chronology; configs/source_lineage_rules_v0.1.json for source-backed structural lineage; schemas/process_integrity_relation_evidence_v0.2.schema.json for relation evidence; schemas/semantic_lineage_closure_v0.1.schema.json for repair anchors and lineage gaps; stage2/r7_prospective_v1/runtime_event_adapter.py for passive event attachment; stage2/r7_prospective_v1/repair_boundary_watcher.py for mutation boundaries; and stage2/r7_checkpoint_v1/controller.py for same-parent checkpoint binding.

Historical monitor packages and repair outputs remain immutable.

## 3. Enhanced monitor pipeline

native/frozen evidence -> observation normalization -> evidence graph -> bounded inspection -> route map

Relations have four epistemic states: SUPPORTED, CANDIDATE, UNKNOWN and REJECTED. Candidate and unknown relations may remain visible for diagnosis but do not become repair authority.

## 4. Three separate scopes

Observation graph: what was observed or can be traced from available evidence.

Diagnostic route: what the investigator or repair agent identifies as potentially relevant.

Repair scope: what the original task authorization and native interfaces permit to be changed.

Operative rule:

repairable route = diagnosed refs ∩ supported reachable refs ∩ frozen authorized write refs - preserve refs - unknown refs

Therefore observation authority != mutation authority, and graph reachability != repair eligibility. A node may be visible, diagnostically relevant and still be non-writable.

## 5. Route repair

Active route repair starts only from a verifiable FULL_NATIVE same-parent checkpoint. The repair agent receives the route map available at the checkpoint and must identify nodes to modify, nodes to preserve, nodes requiring verification, and a reason for each proposed modification.

The route planner intersects that proposal with the already-frozen task write scope. Unsupported, unknown, preserve-set or out-of-scope nodes are blocked. Execution then goes through the existing RepairBoundaryWatcher and an injected system-native executor. The route-repair harness itself has no framework-patching capability and no framework-private-state access.

After the repair executor exits, monitoring returns to watch-only mode. Historical evidence is not rewritten.

## 6. First-round evaluation

First replay frozen trajectories offline to evaluate graph construction, reference resolution, false connections, unknown relations, conflict localization and bounded route export. No model call is required for this phase.

Only after graph behavior is frozen should the limited same-parent comparison run: at most four eligible cases, two arms per case, A using existing local/package evidence and B using the enhanced route map with the same evidence access and external permission/budget. No retry is added to obtain a successful result.

This first comparison estimates the combined value of enhanced monitoring plus route-map-assisted repair. It does not by itself isolate graph representation from evidence quantity.

## 7. Implementation paths

Enhanced monitoring: stage2/monitor_enhancement/observation_adapter.py, evidence_graph.py, inspection.py and route_export.py.

Route repair: stage2/route_repair/plan.py and runner.py.

Frozen machine-readable boundary: configs/stage2_enhanced_external_monitor_contract_v1.json.

The implementation is additive. Existing Stage-I and Stage-II monitor, lineage, checkpoint and repair code remains the historical/reproduction baseline.

## 9. Monitoring stages and current audit comparison

Runtime observation and terminal frozen verification form complementary stages of the monitoring design. Candidate objects feed the observation graph; route-map-assisted repair is not one repair per candidate. Complete available observation maps support diagnosis without conferring write authority or proving all semantic edges. The [dual-audit comparison](../reports/2026-10-03_Enhanced_Monitor_Dual_Audit_Comparison.md) records the tested retrospective gains, including the A2A application case, and separates these from unmeasured live performance and future route-repair outcomes.
