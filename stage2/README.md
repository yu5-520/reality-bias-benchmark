# Stage-II Day-1 preparation

The first group is T1–T3 × X1–X7, **one natural trajectory per cell**. All 21
cells in `matrix.json` are currently pending the engineering gate. These files
are prospective preparation, not subject evidence or a completed adapter run.

The task checkout is `fixtures/project` (the same starting bytes in each cell).
`tasks.json` supplies the exact user request; `roles.json` keeps all nine
Software Engineering agent identities and the same entry agent. Role descriptions
are minimal and identical across probes. Do not give the agent the private
acceptance rubric or a list of permitted file edits. Each cell gets an isolated
copy of the checkout and a separate raw evidence directory.

`versions.json` locks six upstream reference commits (two protocol tags separately)
and the in-repo X5 retrieval code SHA-256. `runtime_packages.json` pins checked
distribution versions separately. `native_status.json` reports which **non-subject**
framework/protocol smoke checks passed and which remain blocked. All seven subject
runtimes, model, provider, budgets and complete native hooks remain unbound. `python -m stage2.freeze`
verifies fixture/task/role/version hashes. `python -m unittest discover -s stage2/tests`
tests the offline interface only. A synthetic test frame never satisfies native
probe conformance. `python -m stage2.preflight --runtime-manifest <path> --captures-root <path> --probe X1`
gates an individual fixed probe; omit `--probe` for the whole seven-layer group.
Both paths fail closed without a bound subject provider/model/limits and full
native code-changing smoke. A blocked probe never makes a passing probe change
the frozen matrix denominator.

## Native hook contract

Each framework hook feeds `NativeCapture.capture` the **original** boundary
bytes, stable native locator, hook identity, actor, addressable source and carrier,
operation, phase, causal parent event IDs and execution status. The capture
stores original bytes under a content hash, then writes a hash-linked common
event. X1 maps conversational send/receive/delegation; X2 adds shared structured
state; X3 records remote task and returned artifact; X4 records tool call and
resource read; X5 records retrieval hits from the fixed index; X6 records memory
write/retrieve; X7 records input and output of compression. All include actual
file changes, tests and termination when observed. Adapters must expose their
real native boundaries; a renamed Common Pool action does not pass.

The common event records **exposure and observed operation**, never inferred
semantic adoption. R6 audits frozen raw for source → carrier → transformation →
downstream read/use → consequence, including null or healthy paths. R7 may
package and test only eligible local repairs, within the four-continuation cap.
An unsuccessful or non-observable probe is recorded as `ENGINEERING_BLOCKED`
at execution freeze; it is not secretly rerun or swapped.

`coding_arena.py` provides file operations and common model input/output
recording. `AutoGenTransport`, `A2AProtocolTransport`, `MCPWorkspace`, and
`RAGContext` have executable non-subject smoke paths. The A2A service currently
returns an artifact without remote model execution; it does not pass subject
preflight. `MetaGPTTransport` and `LongLLMLinguaContext` require exact native
dependencies and a frozen local compressor checkpoint respectively. X6 remains
blocked until the upstream MemoryBank runtime can be bound to a fixed
embedding/persistence policy. See `native_status.json` before interpreting a
passing offline test as subject readiness.
