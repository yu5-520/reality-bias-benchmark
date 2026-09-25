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
and the in-repo X5 retrieval code SHA-256. `runtime_bindings.json` and `subject.json`
freeze the experimental implementation targets and DeepSeek subject profile.
`eligibility.json` records the forward X7 variant mismatch; X2/X6 remain blocked
in the v6.4 target locks. The earlier exploratory SDK release status files have
been retired. X1/X3/X4 now run scripted coding smokes against their exact frozen
upstream commits, and X5 runs against the in-repository implementation.
No subject-ready native coding trace or subject credential is present. `python -m stage2.freeze`
verifies fixture/task/role/version hashes. `python -m unittest discover -s stage2/tests`
tests the offline interface only. A synthetic test frame never satisfies native
probe conformance. `python -m stage2.preflight --level native-smoke --runtime-manifest <path> --captures-root <path>`
validates the v6.4 engineering smoke without opening subject collection. Omit
`--level native-smoke` for the stricter natural-run gate; `--probe X1` checks one
fixed probe. A blocked probe never makes a passing probe change the frozen
matrix denominator.

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
recording. `target_coding_smoke.py` and `verify_target_coding.py` exercise and
verify exact-target, non-subject code-changing traces in CI. The A2A service currently
returns an artifact without remote model execution; it does not pass subject
preflight. `MetaGPTTransport` and `LongLLMLinguaContext` require exact native
dependencies and a frozen local compressor checkpoint respectively. X6 remains
frozen as `ENGINEERING_BLOCKED` at the upstream dependency conflict. X7's
previous smoke used LLMLingua-2 and is blocked prospectively in R Plan v6.6.
Never interpret a
passing offline test as subject readiness.
