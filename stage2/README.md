# Stage-II

**Active forward track: `stage2/native_v7/` — native heterogeneous execution + external observation.**

Stage-II still has **zero natural trajectories**. The v6.x files in this directory are retained as historical engineering provenance only. They are not a universal v7 execution interface.

The frozen scientific conditions remain T1–T3, the nine Software Engineering roles, the checkout fixture, the DeepSeek subject profile, the seven X targets and one natural trajectory per cell. The active boundary is:

- X systems are registered and version-frozen, not forced through one runtime interface.
- X1/X2 keep their native multi-agent framework semantics; X3 keeps native A2A communication.
- X4–X7 are capability-layer conditions and share the explicitly registered `software_engineering_host_v1` background role substrate because those X systems do not own scheduling or inter-agent transport.
- `software_engineering_host_v1` is now frozen as a de-instrumented host: historical queue/mailbox/action semantics are preserved while monitor/audit IDs are removed from the execution path and model-visible context.
- monitoring is external and non-mutating.
- common evidence representation is created after observation, not used to dictate execution.

`docs/R_Plan_v7.2.md` is the active implementation checkpoint. X1 AutoGen remains `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`. X4–X7 now have a frozen background host but their probe-specific native capability attachments are still pending. **No natural cell is open.**

## Historical v6.x scaffold

The v6.x track established exact target/version locks, native-boundary engineering smokes, one-shot reservation/sealing logic and the 21-cell prospective matrix. It did **not** collect a Stage-II natural trajectory. Its `CodingArena` and `RoleMailboxTransport` semantics are retained as the declared historical source for the X4–X7 background host, not as a requirement that all seven X conditions use the same interface.

Do not invoke `stage2.collect_natural` for new Stage-II evidence. The active launcher is `stage2.native_v7.collect`, and it fails closed unless the selected X is explicitly `SUBJECT_READY`.
