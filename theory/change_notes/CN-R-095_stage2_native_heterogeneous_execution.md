# CN-R-095 — Stage-II native heterogeneous execution rebase

Date: 2026-09-25

Stage-II forward execution is rebased before any natural trajectory is collected.

The v6.x engineering scaffold remains provenance only. Its shared `CodingArena`,
role mailbox and `transport/workspace/context_adapter` composition are not
authorized as natural-run infrastructure because they can normalize the process
being studied.

The new invariant is:

**freeze scientific inputs and upstream versions; preserve heterogeneous native
execution; observe externally; normalize evidence only after observation.**

`stage2/native_v7/registry.json` freezes X1–X7 as independently runnable targets.
No dependency compatibility across X systems is required. A framework may use
its own environment, scheduler, message representation, tool protocol and state
model. Monitoring may attach to framework-owned native surfaces but may not
change those semantics.

All seven v7 runners intentionally begin `PENDING_NATIVE_RUNNER`. The subject
gate remains closed and the 21 cells remain unopened. The next implementation
step is one native runner + passive observer per X, followed by exact-version
non-subject smoke and subject-readiness verification. No Stage-II natural data
from v6.x exists to migrate.
