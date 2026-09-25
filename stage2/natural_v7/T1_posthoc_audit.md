# Stage-II T1 seven-cell post-hoc audit

**Evidence state:** seven one-shot natural T1 attempts frozen under `stage2/natural_v7/X1-T1` through `X7-T1`. This audit is read-only. It does not resume a runner, call the subject model, reserve a cell, rerun a trajectory or consume a contrast.

## Core result

T1 is now informative in two different ways, but those two kinds of evidence must not be mixed.

First, X1 contains a complete native execution chain: source files were read, work crossed AutoGen roles, three checkout files were changed, tests were run, the changed files were reread, and a terminal report was produced. The existing X1 pass-1 audit remains the detailed event-level record.

Second, X2–X7 expose a **shared action-envelope bottleneck**. Their model-facing prompts say to return one JSON object with `actions` and present `available_actions` as an action-name-to-argument-shape mapping. Their parsers, however, require `envelope["actions"]` to be a list whose members each contain a `type` field. Natural responses repeatedly used plausible alternative shapes such as a singular `action` field or `{"actions":[{"list_files":{}}]}`. This bottleneck consumed most or all of the 32-turn budget in X2–X7.

That common bottleneck means the six no-answer outcomes cannot be read as clean performance differences between MetaGPT, A2A, MCP, RAG, MemoryBank and LongLLMLingua. It does **not** erase the native process evidence recorded before or around that bottleneck. X5, X6 and X7 in particular expose three sharply different process behaviors.

## Seven-cell accounting

| Cell | Natural result | Native layer evidence | Checkout consequence | Audit reading |
| --- | --- | --- | --- | --- |
| X1 AutoGen | terminal answer | 102 native stream events; file/tool/handoff chain | `run.py`, `legacy_compat.py`, `tests/test_checkout.py` changed | Complete execution chain; final “release-ready” wording exceeds the recorded live-service test scope. |
| X2 MetaGPT | 32-turn budget, no answer | 34 native environment/role-memory events; valid turns 25 and 30; two `list_files` results and one passing `run_tests` result | unchanged | Native MetaGPT runs, but the release-lead loop is dominated by envelope rejection before meaningful inter-role propagation. |
| X3 A2A | 32-turn budget, no answer | one outer official A2A SendMessage call; one valid local turn; internal `protocol_calls=0` | unchanged | A2A transport is proven at the entry boundary, but no role-to-role A2A delegation occurs. |
| X4 MCP | 32-turn budget, no answer | `mcp_calls=0`, `mcp_wire_files=0` | unchanged | The trajectory never reaches the MCP tool/resource boundary. It is not evidence of an MCP effect. |
| X5 RAG | 32-turn budget, no answer | 32 retrieval calls / 64 events; one unique query payload and one unique hit payload | unchanged | Same frozen retrieval context is re-exposed every turn, without evidenced executable uptake. |
| X6 MemoryBank | 32-turn budget, no answer | 32 writes, 31 retrievals, 90 recalled items, 156 native events; one valid turn at 28 | unchanged | A traceable memory-feedback loop forms around earlier malformed exchanges. This is the strongest new T1 mechanism observation. |
| X7 LongLLMLingua | 32-turn budget, no answer | 32 compression calls / 64 events; only three unique input/output payloads | unchanged | Compressor is active but measured token counts remain unchanged, so the boundary is effectively a no-op in this trajectory. |

The six X2–X7 checkout trees are byte-identical to one another across the frozen 12 files. Only X1 changes checkout contents.

## The shared action-envelope bottleneck

The common model-facing representation in X2, X3 and the X4–X7 software host lists actions like this conceptually:

`"available_actions": {"list_files": {}, "read_file": {"path": ...}, ...}`

while the parser accepts actions only when every list member has a `type` field. The natural X6 memory is especially useful because it preserves the model responses themselves. Early examples include:

- `{"type":"json_object","action":"list_files","args":{}}`
- `{"type":"json_object","actions":[{"list_files":{}}]}`
- `{"type":"json_object","actions":[{"action":"list_files","path":"."}]}`

All are understandable attempts to follow the visible action catalogue, but they fail the frozen parser. At turn 28 X6 finally emits the parser-compatible form:

`{"actions":[{"type":"list_files","path":"."}]}`

and that turn is accepted.

X2 independently shows the same boundary through native MetaGPT tool-result messages: 16 missing-`actions` errors, 12 unsupported-action-shape errors and one invalid-action-count error. Its two valid turns execute three harmless actions in total: two file listings and one test run. The tests pass, but no file is edited and no terminal answer follows.

This is therefore not merely “six systems failed T1.” The more precise statement is: **under the frozen T1 execution contract, a shared subject-to-action representation bottleneck dominates six trajectories, while the layer-specific systems expose different behavior around that bottleneck.**

## X6: natural memory feedback path

X6 gives a complete native memory-layer path that is not present in the static RAG or no-op compression cells.

The first model response is stored as a MemoryBank item. After the next invalid-envelope observation, MemoryBank retrieves prior exchanges, writes the new exchange, rebuilds the memory index and later retrieves earlier items again. This repeats throughout the trajectory:

`model response → parser observation → memory write → retrieval into a later prompt → new response → memory write`

By the end of the attempt, the memory contains 32 entries. The six early malformed memories become the dominant recalled items, with recorded recall counts of 18, 16, 15, 13, 12 and 12. Their final memory strengths are 19, 17, 16, 14, 13 and 13. The valid turn-28 response remains at strength 1 and is not recorded in any later recall during turns 29–32.

A representative recalled state therefore does not merely preserve the original user request. It repeatedly reintroduces earlier malformed system/model exchanges into the next model-visible context and strengthens those items as they are recalled. This is a **candidate temporal feedback / inherited-inertia mechanism** at the memory layer.

The causal boundary remains strict: one natural trajectory cannot establish that MemoryBank caused the malformed-response pattern, nor estimate how much it changed its probability. No local contrast has been spent. What is established is the existence and exact route of the feedback structure in this trajectory.

## X5 and X7: useful negative structures

X5 executes retrieval on every turn. All 32 calls use the same T1 user request, and all 32 return the same three frozen hits: `README.md` (score 7), `checkout_app/checkout.py` (score 3), and `versions/after.json` (score 3). The observer records 64 events but only one unique query serialization and one unique hit serialization. This is **repeated static context exposure**, not a changing semantic lineage.

X7 also executes its native boundary every turn, but it behaves differently. The 32 LongLLMLingua calls contain only three unique input payloads and three unique output payloads. The observed token pairs are 81→81 and 74→74, both reported as `1.0x` / `100.0%`. Thus the compressor is genuinely loaded and called, yet it does not reduce these short contexts. The T1 no-answer result cannot be attributed to compression in this trajectory.

X4 is an even earlier negative boundary: no accepted tool action reaches the MCP proxy, so no MCP wire call exists. X3 proves the outer A2A entry call but records `protocol_calls=0` internally. These negative observations matter because they show exactly where each layer did or did not enter the process.

## What T1 can and cannot support

T1 now supports four concrete claims:

1. The same frozen task and subject can produce sharply different process depth across system structures.
2. A common action-contract bottleneck can dominate terminal outcome while native layer behavior still remains observable.
3. MemoryBank can naturally form a closed feedback route in which prior model/system exchanges are retrieved and strengthened over time.
4. “Layer present” is not equivalent to “layer transformed the trajectory”: MCP was not reached, RAG was repeatedly static, and LongLLMLingua was active but effectively no-op.

T1 does **not** support a cross-system success ranking, a causal claim that one X caused better or worse task completion, a general occurrence rate, or a frozen CPR classification. Those conclusions require evidence beyond this seven-cell row.

## Prospective gate before T2/T3

T2 and T3 stay closed. The next operation is an **offline source-level contract decision**, not another natural run.

The decision must compare the model-visible action representation with the parser-required type-tagged representation and choose one of two prospective paths: keep the frozen contract unchanged and accept that envelope rejection is part of the experimental environment, or version a clarified future contract. If a clarification is adopted, it must be declared prospectively, must not rewrite or rerun T1, and T1 terminal outcomes must not be presented as though they were collected under that later contract.

No local causal contrast is spent by this audit. The four-contrast ceiling remains intact.
