# Stage-II

**Active forward track: `stage2/native_v7/` — native heterogeneous execution + external observation.**

Stage-II still has **zero natural trajectories**. The v6.x files in this directory are retained as historical engineering provenance only; their shared `CodingArena`, mailbox transport and `transport/workspace/context_adapter` composition are not authorized for v7 natural collection.

The frozen scientific conditions remain T1–T3, the nine Software Engineering roles, the checkout fixture, the DeepSeek subject profile, the seven X targets and one natural trajectory per cell. What changed is the experimental boundary:

- X systems are registered and version-frozen, not forced through one runtime interface.
- each X may use an independent dependency environment;
- multi-agent frameworks/protocols keep their native scheduling or communication semantics;
- capability-layer X systems such as MCP/RAG/memory/context compression attach to the software-engineering host at their natural boundary rather than pretending to be schedulers;
- monitoring is external and non-mutating;
- common evidence representation is created after observation, not used to dictate execution.

`docs/R_Plan_v7.1.md` is the active implementation plan. X1 AutoGen now has a probe-specific native-runner candidate and non-study observer smoke under `stage2/native_v7/x1_autogen/`. The registry remains the authority for whether that runner has actually passed its gate. No runner implementation alone opens a natural cell.

## Historical v6.x scaffold

The v6.x track established exact target/version locks, native-boundary engineering smokes, one-shot reservation/sealing logic and the 21-cell prospective matrix. It did **not** collect a Stage-II natural trajectory. Those files remain available to audit why the architecture was rebased, but a passing v6.x smoke does not open a v7 cell.

Do not invoke `stage2.collect_natural` for new Stage-II evidence. The active launcher is `stage2.native_v7.collect`, and it fails closed unless the selected X is explicitly `SUBJECT_READY`.
