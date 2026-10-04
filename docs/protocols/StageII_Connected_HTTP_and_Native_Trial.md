# Captured provider planning and same-parent native trial

The current entry is `ConnectedPlanningRepairEntry` in `configs/stage2_monitor_repair_active.json`. It accepts a host-bound provider planning session and returns after native repair, before host release. It has no legacy fallback. Older sealed implementations remain reproducible on their own frozen trees.

## Implemented behavior

`connected_provider.py` adds a one-attempt HTTPS transport for the frozen DeepSeek endpoint and a separate loopback socket fixture. The model alias, parameters, original task, framework source hashes and native parent come from retained host bindings. Credentials exist only in memory. Each request body is durably recorded before dispatch; status, non-secret headers and each response chunk are recorded before decoding. HTTP failures, malformed replies, incomplete bodies, model-name drift and uncertain transport failures close the source without retry or budget refund. Native model content remains unchanged, including malformed action JSON. A configured or reported model name does not verify backend identity. `provider_calls` counts live HTTP dispatch attempts, not confirmed successful inference; historical provider-attempt counts remain unknown.

`connected_planning.py` sends the full available prefix interface, original task, host capability envelope, tool history and structured output contract to the provider. The actor can read catalog, node context, native file versions, observations and source witnesses. It cannot write, invoke native commands, alter the actor ID, supply a verifier or grant permission. REPAIR, NO_REPAIR_NEEDED and UNRESOLVED are distinct outcomes. Finalization revokes tools before compilation. The unchanged mechanical compiler re-reads the source ledger and freezes exact field/span, value, version, dependency and route permissions. The new connected authorization separately retains transport provenance and the one-use dispatch token. Mechanical reuse does not relabel an offline scripted proposal as autonomous.

`connected_mcp.py` restores the exact original nonterminal parent and attaches the unchanged official MCP proxy/client/server. A passive wrapper retains an exclusive, durable byte-for-byte snapshot of each observed protocol stream before interpreting it. Native process-owned logs are transient and excluded from the seal; retained wire snapshots and their graph capture hashes are authoritative. Exact repairs, readback and host-defined engineering checks precede a paused boundary. Host release requires the same retained planning/authorization objects, complete actions and checks, no failed or in-flight planning exchange, revoked tools, unchanged native host state, unchanged source/config bindings and the expected application versions. Only a successfully closed real-provider session followed by native completion can yield the host-owned `REPAIR_AGENT_EXIT` record. An actor's JSON or a loopback model-name assertion cannot create this event. Exit opens observation/review readiness; it does not certify repair effectiveness.

The original subject resume loop runs with its original 64-turn ceiling and 8-action limit. The trial has at most four new subject dispatches, within the parent's remaining horizon. If the fourth returned native turn remains open, a boundary exception censors the trial before the fifth queue pop. It preserves native stop_reason, queue, inbox, historical prefix and the remaining 56 turns. It is not a failure, terminal closure, reset or authorization to resume later. Uncertain failures preserve a native failure checkpoint; all attempted branches are one-use.

Independent review preparation uses the existing semantic and lineage rules. It remains read-only and separately bound. No reviewer is invoked automatically. Censoring, source retention and successful engineering checks do not establish semantic repair efficacy.

## Validation and scientific status

171 route-repair checks and 12 enhanced-monitor checks pass. The added wire-retention regression verifies that a later process-log change cannot alter the byte snapshots referenced by captured observations.

The sealed loopback/MCP fixture contains 600 artifacts: 14 planning HTTP exchanges, four subject HTTP exchanges and seven native MCP invocations. All 434 prefix observations and 801 prefix edges remain unchanged, with 333 new observations appended. Native history advances from four to eight entries; ceiling 64, remaining horizon 56 and the live queue are preserved. This is an engineering fixture whose responses and conditional-launch proposal are scripted. It establishes transport, source-bound compilation, phase gates and native integration, not autonomous semantic diagnosis, actual provider execution or repair success. Its controlled alternate-launcher change does not identify the earliest unsupported authority transition; actual historical adoption remains unknown.

Sealed evidence: `stage2/replication_v2/connected_http_mcp_preflight_v1/`.

The 459-artifact predecessor's seal includes its old active registry. CI reproduces the entire predecessor in an isolated worktree at `a9df69ede037b2f27af1545f928e3f4c19daab02`. Today's registry points exclusively to the connected entry. No old evidence, source implementation or seal is rewritten.

Local live preflight passed the frozen runtime and source bindings. Actual execution was blocked before any request because `DEEPSEEK_API_KEY` is unavailable. No credential was read or saved and no model or semantic reviewer was invoked. Real autonomous planning, a real exit and independent semantic effectiveness therefore remain unobserved.

## Running a single new trial

Use the SDK interpreter pinned by the existing offline integration workflow. First run zero-call preflight:

```bash
python scripts/run_stage2_connected_repair.py \
  --source-root /absolute/frozen/sources \
  --sdk-root /absolute/frozen/python-sdk \
  --protocol-root /absolute/frozen/protocol \
  --out /absolute/fresh/preflight
```

With the already configured credential, `--execute` starts one new captured derived trial in another fresh output directory. It does not reread future trajectory material or rerun the frozen natural experiment. The operator does not prescribe a fix: the provider may return REPAIR, a scoped NO_REPAIR_NEEDED or UNRESOLVED. The host offers only the original native test suite as the engineering checker, excludes its test files from the repair write envelope and refuses an absent suite. The transport retains the provider key in memory; the executable entry removes it from the environment inherited by application subprocesses. This is an application permission boundary, not an OS sandbox. Bytecode generation is disabled for this process environment to avoid introducing cache files into the branch; native framework and command sources are unchanged.

There is no automatic paid launch on push, no format resampling, no continuation restart, no promotion and no automatic paid evaluation. The available connector in this session has no workflow-dispatch operation; a real provider run cannot be claimed from the passing offline workflow.
