# Field-bounded branch repair

Status: implemented offline application integration; no live semantic repair trial.

## Purpose and scope

The full observed graph is the diagnostic view. A semantic branch determines a proposed repair route; a separately host-held policy determines executable fields and operations. Observation or graph reachability never grants write permission. The original broad coding request remains in the policy; this restriction applies to repair execution after diagnosis, not to the natural subject task or its monitoring.

The public implementation is independent of the private product. It uses the experiment's source context, native application checkout and enhanced observation graph. No product registry, fabric or private implementation is copied or imported.

## Implemented path

1. Bind the full graph, archive, terminal checkpoint, original task, branch and semantic identity.
2. Bind exact source witnesses. These establish source identity, not semantic adoption or correctness.
3. Retain a host-side field policy separately from the agent's proposed plan. An agent cannot widen the embedded policy and merely re-hash it to obtain execution.
4. Compile operations, dependencies, exact before versions, expected outputs and preservation conditions over all selected objects before writing.
5. Copy the frozen terminal application into a fresh branch. Native writes occur only inside this copy.
6. Execute exact changes through the existing `HostCheckout.write_file` interface; do not modify protocol/framework implementations. Keep the enhanced observer read-only.
7. Preserve all original graph nodes, observations and edges. Append source-bound captures before, during and after native application operations. Keep a distinct branch clock.
8. Record native attempts, actual outputs, errors and partial execution. Do not silently undo failed actions or replay the natural subject.

There is no fallback to a local repair package, a one-instruction process revision or the old structural watcher.

## Supported native operations

| Operation | Restriction | Preservation measure |
| --- | --- | --- |
| JSON leaf replacement | Existing scalar leaf, exact RFC 6901 pointer, same value type; no duplicate keys or container replacement | All other parsed JSON values remain equal; formatting may change |
| Text span replacement | One nonempty exact character span per object, source/version hash and exact old span hash | Prefix and suffix bytes remain unchanged |
| Multiple JSON leaves in one object | Disjoint leaf grants and explicit ordering; each intermediate file version is projected before execution | Each action preserves non-target values in that intermediate version |
| Multiple application objects | Explicit action dependencies and complete branch manifest checks | Nonselected files retain their captured byte hashes |

The native interface writes entire UTF-8 files. Field restriction is implemented by deterministic transformation and output validation before issuing the native write. An arbitrary replacement body is not accepted. This is not a universal field setter for private model, RAG, memory or protocol state.

## Rejection and failure behavior

- Reject unsupported state/message/private surfaces instead of translating them into a soft instruction.
- Reject out-of-policy fields, spans, action identifiers, stale versions, unverifiable source identity, container replacement, type changes and dependency cycles.
- Reject writes to verify/preserve refs. Unknown semantic relations remain claims; they do not grant writes.
- Check the full branch manifest before the first write and before each operation. Stop on changed target or preserved objects.
- Write an intent before execution, then retain actual native output and its receipt even if postconditions fail. Stop dependent operations; keep the partial branch and full observation evidence.
- The executor exposes exact plan execution only. A later model integration must not also expose bypassing filesystem/shell/unchecked write capabilities.

Hash preconditions are sequential checks, not a concurrency-safe compare-and-swap or an acquired runtime lock. No concurrent subject runs during this offline integration. Production concurrency and branch promotion remain separate missing capabilities.

## Historical prefix and unrelated branches

Old archives, messages and prior graph observations are immutable. The branch starts from the captured terminal application; it does not truncate every event after a historical pressure point. Historical diagnosis can identify pressure points without claiming historical runtime restoration.

Byte/value preservation is a mechanical property. It does not prove that an unrelated semantic route experiences identical downstream behavior after one field changes. Shared dependencies and operational authority still require source-grounded diagnosis and independent after-repair semantic assessment.

## Current evidence and remaining work

The frozen MCP integration is deliberately labeled `OFFLINE_MECHANICAL_INTEGRATION_NOT_SEMANTIC_REPAIR`. It makes two marked fixture changes in an application copy, preserves the full original graph and archive, and adds application captures. No defect diagnosis is prewritten, no evaluator labels enter the plan, no agent continuation occurs and no branch is promoted.

Permanent evidence: `stage2/replication_v2/field_branch_native_integration_v1/`.

Still required before a paid trial:

- A source-based diagnosis identifying semantic conversion, authority adoption, pressure points and affected branches, including intersection and R re-entry.
- A reviewed coordinated plan addressing still-effective descendants; operation dependency order alone is not semantic dependence.
- Native process-state and forward message/task supersession capabilities where supported by the original interfaces.
- Enhanced observation of native agent continuation and independently evaluated full-route semantics/authority.
- A frozen same-parent comparison protocol and budget after both methods work.

Current paid/live entrypoints remain disabled. This is a completed engineering prerequisite, not a semantic efficacy result.

## Reproduce without model calls

```bash
python -m unittest discover -s stage2/route_repair/tests -v
python -m unittest discover -s stage2/monitor_enhancement/tests -v
python scripts/check_stage2_field_branch_native.py --source-root SOURCE_ROOT --graph-root GRAPH_ROOT --out FRESH_OUTPUT
python scripts/validate_stage2_field_branch_integration.py --reproduced FRESH_OUTPUT
```

The workflow materializes the same pinned original archives and graphs; its new integration job has no provider secret or paid input.
