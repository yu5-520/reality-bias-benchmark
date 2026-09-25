# Stage-II execution preparation

The first group is T1–T3 × X1–X7, **one natural trajectory per cell**. The 21
cells in `matrix.json` remain the prospective inventory. Engineering work and
subject execution are deliberately separate: native smoke may run without any
subject/evaluator call, while a natural cell can run only after its probe has a
valid native receipt and the common evidence gate accepts the frozen binding.

The task checkout is `fixtures/project` (the same starting bytes in each cell).
`tasks.json` supplies the exact user request; `roles.json` keeps all nine
Software Engineering agent identities and the same entry agent. Role descriptions
are minimal and identical across probes. Do not give the agent the private
acceptance rubric or a prescribed file-edit list. Each natural cell gets an
isolated copy of the checkout and a separate raw evidence directory.

`versions.json` preserves the original seven scientific probe identities.
`runtime_lock.json` adds exact engineering bindings: upstream commits, official
A2A/MCP SDK commits where needed, the in-repository X5 implementation hash,
native hook identity, and the X7 checkpoint binding surface. `subject_lock.json`
binds one common subject provider/model/limits across the first group while
keeping provider and evaluator execution explicitly unauthorized.

`python -m stage2.freeze` verifies the frozen fixture/task/role/version evidence
contract. `python -m unittest discover -s stage2/tests` tests the offline
interfaces. `.github/workflows/stage2-native-binding-smoke.yml` then exercises
the seven provider-free native boundaries. Every probe produces one of exactly
two engineering receipts:

- `NATIVE_SMOKE_PASS`: the installed native boundary produced reconstructable,
  hash-linked raw evidence;
- `ENGINEERING_BLOCKED`: the exact planned probe could not pass its native
  evidence gate, with a frozen reason.

A blocked probe is not replaced, renamed, or simulated. Its T1–T3 cells remain
visible as engineering-blocked cells in the fixed first-group inventory. Passed
probes proceed through the same `stage2.preflight` evidence gate; the preflight
also binds the runtime lock, subject lock, SDK/checkpoint identity, roles,
matrix, code commit and native provenance.

## Native hook contract

Each framework hook feeds `NativeCapture.capture` the **original** boundary
bytes, stable native locator, hook identity, actor, addressable source and
carrier, operation, phase, causal parent event IDs and execution status. The
capture stores original bytes under a content hash, then writes a hash-linked
common event.

X1 maps AutoGen message send/receive; X2 maps MetaGPT shared state; X3 maps A2A
remote task and returned artifact; X4 maps MCP tool calls and resource reads; X5
maps retrieval hits from the fixed index; X6 requires both MemoryBank memory
write and memory retrieval to be genuinely observable; X7 requires compression
through a revision-bound LongLLMLingua checkpoint. Merely importing a package,
cloning a repository, or renaming a Common Pool action is not native
conformance.

The common event records **exposure and observed operation**, never inferred
semantic adoption. R6 later audits frozen natural raw evidence for source →
carrier → transformation → downstream read/use → consequence, including null,
healthy and unresolved paths. R7 may package and test only eligible local
repairs, within the four-continuation cap. No new R5 is introduced.

## Provider boundary

The engineering workflow contains no subject-model secret and cannot create a
natural trajectory. The frozen subject lock currently requires an explicit
separate authorization event before any paid first-group call. No cell is rerun
because C/P/R failed to appear, and no paid evaluator is automatically invoked
during natural execution.
