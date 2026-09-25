# Stage-II

**Active forward track: `stage2/native_v7/` — native heterogeneous execution + external observation.**

Stage-II still has **zero natural trajectories**. The v6.x files in this directory are retained as historical engineering provenance only. They are not a universal v7 execution interface.

The frozen scientific conditions remain T1–T3, the nine Software Engineering roles, the checkout fixture, the DeepSeek subject profile, the seven X targets and one natural trajectory per cell. The active boundary is:

- X systems are registered and version-frozen, not forced through one runtime interface.
- X1/X2 keep their native multi-agent framework semantics; X3 keeps native A2A communication.
- X4–X7 are capability-layer conditions and may share the explicitly registered software-engineering background host because those X systems do not own scheduling or inter-agent transport.
- that background host is never implicit: the registry names its execution and communication semantics and keeps it blocked until monitor responsibilities are removed from the execution path.
- monitoring is external and non-mutating.
- common evidence representation is created after observation, not used to dictate execution.

`docs/R_Plan_v7.1.md` is the active implementation plan. X1 AutoGen has a verified probe-specific native runner and passive observer smoke under `stage2/native_v7/x1_autogen/`. Its registry state is `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`: the engineering runner is accepted, but **no natural cell is open** until a separate real-provider readiness check is bound to the exact execution commit.

## Historical v6.x scaffold

The v6.x track established exact target/version locks, native-boundary engineering smokes, one-shot reservation/sealing logic and the 21-cell prospective matrix. It did **not** collect a Stage-II natural trajectory. Its `CodingArena` and `RoleMailboxTransport` semantics are retained as the declared historical source for the X4–X7 background host, not as a requirement that all seven X conditions use the same interface.

Do not invoke `stage2.collect_natural` for new Stage-II evidence. The active launcher is `stage2.native_v7.collect`, and it fails closed unless the selected X is explicitly `SUBJECT_READY`.
