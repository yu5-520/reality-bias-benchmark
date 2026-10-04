# Read-only planning protocol and same-parent host entry

> This is the sealed predecessor protocol. The current [provider-bound phased entry](StageII_Bound_Provider_and_Native_Phases.md) replaces its one-call dispatcher for current work; it retains this implementation only for frozen reproduction.
This stage implements the planning tool conversation and host dispatch boundary. It is an **offline scripted engineering test**, not an autonomous planning experiment or evidence of semantic repair effectiveness. No model or paid reviewer is called, and no frozen natural experiment is rerun.

The unchanged prefix context exposes every observed node and every readable source in the verified early prefix. It excludes later checkpoints, terminal answers, retrospective audit verdicts and unrecorded historical provider exchanges. The current native binding is X4 MCP at the pinned nonterminal parent; general support for arbitrary systems or checkpoints is not established.

## Host and actor responsibilities

Before exposing evidence, the host freezes the original task, writable application surfaces, action/value bounds, actor identity, planning call budget and response size bound. The capability envelope prescribes no replacement value and conveys no semantic finding. The actor sees only five read-only tools: `catalog`, `node`, `file`, `observation` and `witness`. These expose the full available prefix without a graph depth cutoff. Exact argument keys are required. No compiler, native write, shell command, provider or verifier implementation is an actor tool.

`ReadOnlyPlanningActorSession` persists each actual request, exact response content and tool result before further interpretation. Each artifact has a source hash and deterministic gzip member hash; each ledger row is saved with an exclusive write and file fsync. Requests retain the complete earlier conversation. Malformed JSON, duplicate fields, nonfinite values, unsupported tools, future versions, source mismatches and exhausted budgets close the session and retain its first attempt. They do not trigger a retry or a new sample.

The enabled actor is exactly `OfflinePlanningScript`. Subclasses, callbacks and live providers are rejected. Its responses are fixed engineering fixtures, not generated diagnoses. A future autonomous provider requires a separate frozen provider/actor configuration, exact request/response capture and an authorized trial. The protocol test cannot establish the quality or adequacy of that future actor.

## Final decisions

| Decision | Required result | Host behavior |
| --- | --- | --- |
| `REPAIR` | Existing structured route proposal with exact parent/task/source bindings, inspected witnesses, classified route nodes, proposed actions and checks | Revoke planning tools, compile using the separate host envelope, revalidate source reads, then dispatch the retained one-use authorization |
| `NO_REPAIR_NEEDED` | Reason, explicitly inspected scope, witnesses covering that scope, and uncertainty | Record a scoped actor claim; create no repair branch and issue no authorization |
| `UNRESOLVED` | Reason, any inspected scope/witnesses, and unresolved relations | Record insufficient evidence; create no repair branch and issue no authorization |

“No repair needed” is neither a global absence-of-defects judgment nor success certification. An empty inspected scope cannot support that decision. `UNRESOLVED` can represent unavailable evidence without inventing a witness. Unknown diagnoses cannot justify a write. Unsupported relationships cannot expand task capabilities.

`OfflinePlanningRepairEntry` connects a completed repair decision to the sealed `SameParentMCPBranch`. Verifier implementations and frozen MCP runtime roots remain host inputs. The existing branch checks exact application versions, action dependencies, postconditions, write scope, original host state and remaining subject horizon. No-action decisions bypass native runtime construction. Planning or dispatch failures retain an entry receipt linked to the planning outcome and cannot be automatically replayed.

## Exit and review boundary

The session records `OFFLINE_PLANNING_SESSION_EXIT` when its tools close. The unchanged branch records `OFFLINE_REPAIR_DRIVER_EXIT` after scripted host execution. Neither is `REPAIR_AGENT_EXIT`; neither opens independent semantic review. A planning actor's proposal submission precedes repair actions and cannot prove a real repair actor finished those actions.

Planning transcript artifacts are separately sealed protocol evidence. They are not relabeled as historical subject observations or spliced into the frozen native prefix. The original semantic criteria and source evidence remain unchanged. Actual repair-agent exit, ordered post-exit subject-model observations and independent semantic assessment are still required before an effectiveness claim.

## Reproduction

Run the new check using the unchanged, pinned official MCP SDK interpreter described in [same-parent native MCP integration](StageII_Same_Parent_Native_MCP_Repair.md):

```bash
"$SDK_ROOT/.venv/bin/python" scripts/check_stage2_read_only_planning_entry.py \
  --source-root "$SOURCE_ROOT" --sdk-root "$SDK_ROOT" --protocol-root "$PROTOCOL_ROOT" \
  --out "$FRESH_OUTPUT" --compare-frozen
```

The new dataset is `stage2/replication_v2/read_only_planning_entry_integration_v1`. Previous sealed datasets and their implementation hashes remain unchanged. Four cases exercise repair dispatch, scoped no-repair, unresolved evidence and rejected native-write tool requests. The repair proposal is the existing explicitly scripted conditional-launcher probe, with actual historical launcher adoption unknown; it is not a newly discovered defect or earliest semantic transition.

Pending gates are a frozen autonomous planning provider, evidence-supported semantic entry selection, actual repair-agent exit, frozen subject provider continuation within the original remaining budget and independent semantic review. X5–X7 native bindings remain separate work.
