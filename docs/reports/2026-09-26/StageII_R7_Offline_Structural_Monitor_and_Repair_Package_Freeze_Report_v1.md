<!-- Stage-II R7 engineering-readiness report. Structural monitor only; semantic audit is intentionally excluded from target selection. -->

**Reporting position:** Stage-II R7 engineering-readiness / structural-monitor freeze  
**Evidence policy:** frozen 21-path first-attempt source population; no natural rerun; no semantic answer-key input  
**Boundary principle:** Observe across boundaries; repair only through boundaries  
**New subject/provider/evaluator call:** none  
**Active repair executed:** no

# REALITY BIAS | PROCESS REALITY

# Stage-II R7 Offline Structural Monitor and Repair-Package Freeze Report v1

## Structural localization before repair, native-boundary preservation, and fail-closed repair readiness

| Field | Frozen position |
|---|---|
| Source population | 21 frozen Stage-II first-attempt trajectories: X1-X7 × T1-T3 |
| Natural reruns | 0 |
| Monitor input | raw structural/runtime evidence only |
| Semantic audit input | prohibited |
| CPR labels in monitor | prohibited |
| Future suffix used for localization | prohibited |
| Normalized structural events | 1,120 |
| Raw structural candidate signals | 244 |
| Cells with structural candidates | 15/21 |
| Structurally assembled episodes / repair packages | 24 |
| Package cells | 15/21 |
| Active-repair-ready packages | 0 |
| Primary readiness result | 16 parent-reconstruction blocked; 7 lineage-gap blocked at immutable foreign carriers; 1 no-repair-required |
| Engineering interpretation | monitor localization and package formation are executable offline, but the frozen Stage-II collection did not preserve native resumable parents at monitor-selected prefixes; active repair must remain fail-closed |

> **Integrity declaration.** This report does not use the completed Stage-II semantic audit to choose, merge, prioritize or expand repair targets. It performs no natural rerun, no stochastic prefix reconstruction, no subject/provider continuation, no evaluator call and no active repair. The semantic audit remains reserved for later independent validation of already-frozen monitor/package outputs.

---

# 1. Why this report exists

Stage-II natural observation and semantic interpretation had already established a rich cross-system process-reality evidence base. That evidence is scientifically useful, but it cannot be allowed to become an online answer key for the engineering repair system.

A deployable repair architecture cannot require a separate Agent to first read an entire trajectory, perform complete semantic adjudication, identify C/P/R, and then tell the repair system what to repair. The engineering chain must instead be:

`raw structural/runtime evidence`  
→ `external structural monitor`  
→ `pressure/support localization`  
→ `content-addressed package`  
→ `repair gate`  
→ `native-boundary repair when legally executable`  
→ `continued external watch`.

The independent semantic chain comes later:

`frozen monitor/package output`  
→ `semantic validation`  
→ `localization-quality audit`  
→ `repair-consequence interpretation`.

The frozen rule is therefore:

> **Semantic audit validates the monitor; semantic audit does not guide the monitor.**

---

# 2. Frozen Stage-II R7 boundary

The experiment boundary is bound by:

- `configs/stage2_r7_boundary_contract_v1.json`;
- `configs/stage2_r7_monitor_input_firewall_v1.json`;
- `configs/stage2_r7_21_path_source_freeze_v1.json`;
- `docs/StageII_R7_External_Process_Integrity_Repair_Protocol_v1.0.md`.

The central engineering invariant is:

> **Observe across boundaries; repair only through boundaries.**

The external monitor may observe heterogeneous AI-system surfaces, but wider observability does not grant wider execution authority.

R7 therefore cannot make a repair succeed by:

- modifying AutoGen or MetaGPT framework semantics;
- modifying A2A protocol/service semantics;
- modifying or bypassing MCP protocol, tools/resources or security boundaries;
- rewriting RAG corpus, index, embeddings or retrieval structure;
- rewriting MemoryBank stored memory, index, strength or recall mechanism;
- changing LongLLMLingua model/checkpoint/compression implementation;
- directly mutating private native runtime state;
- introducing an otherwise unavailable capability solely for the experiment.

If a legal repair surface does not exist, a blocked result is retained as evidence.

---

# 3. Frozen source population

All 21 Stage-II first attempts were bound before monitor execution.

`7 system/layer conditions × 3 task families = 21 natural trajectories`.

No natural trajectory was regenerated.

The frozen source manifest binds each cell to its archived attempt, execution SHA, workflow and artifact identifiers:

`configs/stage2_r7_21_path_source_freeze_v1.json`.

The monitor therefore does not create a new natural baseline.

For any future repair experiment:

A = the already-frozen natural continuation.

B may only be created from the same machine-verified frozen parent after one monitor-derived repair package.

---

# 4. Future-blind prefix replay

The 21 paths are now complete historical records, but the monitor was not allowed to use future events to decide where a repair candidate first appears.

For every normalized trajectory:

`E1 → E2 → ... → Ek`

the detector at `Ek` only sees the structural evidence accumulated through `Ek`.

It does not inspect `Ek+1...End` and then move the repair point backward.

Every candidate therefore records a `prefix_cutoff_ref`, and the monitor output freezes:

`future_evidence_used = false`.

This preserves the intended engineering analogue of an online monitor even though the experiment is performed offline over frozen evidence.

---

# 5. Structural-monitor inheritance from Stage I

The Stage-II monitor does not invent a semantic classifier for each named system.

Its frozen structural rules inherit the Stage-I engineering concepts of:

- addressable materialization;
- direct downstream consumption;
- descendant materialization;
- multi-consumer reuse;
- structural pressure exposure.

Stage II adds heterogeneous native-surface adapters, not framework-specific semantic answers.

Frozen monitor rules:

| Rule | Structural meaning | Semantic non-claim |
|---|---|---|
| MULTI_CONSUMER_ADDRESSABLE_REUSE | same addressable object reaches multiple actors | not automatically shared semantic authority |
| REENTRY_OR_REUSE | an addressable object reappears after intervening process | not automatically temporal inertia |
| WRITE_THEN_REUSE | application object is written/materialized and later consumed | not automatically a defective lineage |
| IMMUTABLE_CARRIER_REPEAT | RAG/memory/compression carrier is repeatedly exposed | carrier presence is not CPR |
| CONTEXT_TRANSFORMATION_EXPOSURE | recorded compression/context carrier changes | transformation is not automatically harmful |
| TERMINAL_OPEN_WITH_REUSE | process ends open while reused structural objects remain active | open process is not automatically failure |

The monitor intentionally emits structural candidates rather than C/P/R labels.

---

# 6. Heterogeneous evidence normalization

The monitor reads each system at the structural surface the Stage-II experiment actually exposed.

| X | Structural input surface | Monitor normalization |
|---|---|---|
| X1 AutoGen | native AgentChat event stream | message, tool, handoff, file/test object refs |
| X2 MetaGPT | Environment history + Role memory post-round copies | message identity, role consumption, referenced application objects |
| X3 A2A | exact JSON-RPC role-call wire payloads | sender/target/call, message identity, referenced application objects |
| X4 MCP | exact stdio tool wire | native tool/action and application object refs |
| X5 RAG | retrieval query/hit observer | immutable retrieval-hit content addresses + host-turn actors |
| X6 MemoryBank | query/recall/state observer | immutable recall/state content addresses + host-turn actors |
| X7 LongLLMLingua | compressor input/output observer | context-channel transformation + host-turn actors |

This normalization does not replace the upstream framework or protocol.

It operates after observation.

---

# 7. Raw structural scan

The full 21-path replay produced:

| Measure | Frozen result |
|---|---:|
| Normalized structural events | 1,120 |
| Structural candidate signals | 244 |
| Cells with ≥1 candidate | 15/21 |
| Cells with no candidate under frozen rules | 6/21 |
| Natural reruns | 0 |
| Provider calls | 0 |
| Evaluator calls | 0 |

Rule accounting:

| Rule | Candidate signals |
|---|---:|
| MULTI_CONSUMER_ADDRESSABLE_REUSE | 101 |
| REENTRY_OR_REUSE | 93 |
| TERMINAL_OPEN_WITH_REUSE | 21 |
| IMMUTABLE_CARRIER_REPEAT | 16 |
| WRITE_THEN_REUSE | 11 |
| CONTEXT_TRANSFORMATION_EXPOSURE | 2 |
| **Total** | **244** |

These 244 rows are monitor signals, not 244 proposed experiments.

They remain individually addressable for audit.

---

# 8. From 244 candidate signals to 24 structural packages

Treating every repeated file read, message reuse or carrier observation as a separate repair package would inflate one connected process structure into many artificial experiments.

A second rule layer was therefore frozen **before canonical package assembly**:

`configs/stage2_r7_package_assembly_rules_v1.json`.

It uses only structural adjacency, object identity, actor overlap, event-prefix distance and carrier family.

It does not use:

- semantic-audit verdicts;
- CPR labels;
- case-specific human selections.

The 244 candidate signals were assembled into:

**24 lineage-bounded structural episodes/packages across 15 cells.**

Package distribution:

| Cell | Raw candidate signals | Assembled packages |
|---|---:|---:|
| X1-T1 | 22 | 1 |
| X1-T2 | 20 | 2 |
| X1-T3 | 29 | 2 |
| X2-T1 | 0 | 0 |
| X2-T2 | 42 | 5 |
| X2-T3 | 30 | 3 |
| X3-T1 | 0 | 0 |
| X3-T2 | 12 | 2 |
| X3-T3 | 13 | 1 |
| X4-T1 | 0 | 0 |
| X4-T2 | 0 | 0 |
| X4-T3 | 1 | 1 |
| X5-T1 | 9 | 1 |
| X5-T2 | 12 | 1 |
| X5-T3 | 12 | 1 |
| X6-T1 | 11 | 1 |
| X6-T2 | 0 | 0 |
| X6-T3 | 0 | 0 |
| X7-T1 | 8 | 1 |
| X7-T2 | 14 | 1 |
| X7-T3 | 9 | 1 |

The 24 packages are frozen in:

`stage2/r7_monitor_v1/monitor_derived_repair_packages.jsonl`.

Each package preserves the original candidate hashes used to construct it.

---

# 9. Package contents

The repair-package schema is:

`RB-STAGE2-R7-MONITOR-DERIVED-REPAIR-PACKAGE-v1`.

Every package contains, structurally:

`source cell`  
→ `prefix cutoff`  
→ `monitor evidence refs`  
→ `pressure refs`  
→ `support refs`  
→ `ancestor refs`  
→ `observed descendants`  
→ `affected closure`  
→ `preserve set`  
→ `repair anchor`  
→ `content address`  
→ `detection surface`  
→ `legal repair surfaces`  
→ `native capabilities required`  
→ `forbidden mutations`  
→ `parent reconstruction status`  
→ `post-repair watch contract`.

It deliberately contains no CPR label.

---

# 10. Repair-boundary behavior on external information systems

The monitor detects structures in X5, X6 and X7, but the repair planner is not allowed to turn that observability into foreign-state write access.

Therefore:

- an X5 RAG hit can be a detection/support carrier but the RAG store remains immutable;
- an X6 MemoryBank recall can be a detection/support carrier but the stored memory remains immutable;
- an X7 compression transformation can be a detection/support carrier but the compressor remains immutable.

A legal future repair must move to the nearest downstream application/process surface that the original system already permits.

Where raw structural evidence does not yet bind the immutable carrier to such a complete legal downstream repair anchor, the package is:

`LINEAGE_GAP_BLOCKED`.

That is a deliberate fail-closed outcome.

---

# 11. Repair-readiness gate result

Final package gates:

| Gate | Packages | Meaning |
|---|---:|---|
| PARENT_RECONSTRUCTION_BLOCKED | 16 | application/message repair surface is visible, but exact native continuation parent is not currently resumable from the frozen archive |
| LINEAGE_GAP_BLOCKED | 7 | immutable external carrier is visible, but a complete legal downstream repair lineage is not yet machine-bound |
| NO_REPAIR_REQUIRED | 1 | observed structural exposure does not itself expose a justified direct repair object |
| COMPLETE_FOR_STRUCTURED_REPAIR | **0** | no package may yet enter active scientific repair |

This is the most important result of the current engineering stage.

The monitor and package builder are operational offline.

The active repair gate correctly remains closed.

---

# 12. Why all active repair remains blocked

The canonical repair geometry requires:

A:

`frozen parent → already-observed natural continuation`

and B:

`same frozen parent → one repair package → repair executor exits → one native continuation`.

The existing Stage-II raw archives were originally designed for passive natural observation, not for arbitrary mid-trajectory branching.

They contain rich native/protocol/process evidence, but they do not contain a framework-native resumable runtime checkpoint at every monitor-selected prefix.

For example, an application file can be content-addressed from evidence, but continuation may also depend on:

- framework scheduling state;
- role inbox/memory state;
- pending work;
- message/task state;
- already-returned tool observations;
- remaining execution horizon.

R7 cannot simply rerun the prefix to recreate these states because that would create a new stochastic parent.

It also cannot invent hidden state.

Therefore the current preflight correctly produces:

`PARENT_RECONSTRUCTION_BLOCKED`

rather than silently changing the experimental geometry.

---

# 13. This is not a repair-failure result

No active repair has been attempted.

Therefore the current evidence does **not** support statements such as:

- “R7 repair failed”;
- “the package cannot repair CPR”;
- “external monitoring is ineffective”;
- “one framework is less repairable than another.”

The frozen result is narrower:

> **The structural monitor can automatically nominate and content-address heterogeneous pressure/support episodes without semantic-answer input, but the current Stage-II passive-observation archives do not yet provide the resumable native-parent state required for a valid one-branch repair experiment.**

This is an engineering-readiness boundary.

---

# 14. Negative / non-trigger behavior

Six cells produced no structural candidate under the frozen monitor:

- X2-T1;
- X3-T1;
- X4-T1;
- X4-T2;
- X6-T2;
- X6-T3.

This is useful because the monitor is not designed to force a repair candidate out of every path.

In particular, an active memory system or a named protocol layer is not automatically sufficient to trigger repair.

X4-T3 produced one structural episode, but the assembled package was classified `NO_REPAIR_REQUIRED` because the generic structural episode did not itself expose a direct application/message repair surface.

Later independent semantic validation may measure whether this reflects an appropriate negative boundary or a monitor miss. That later audit is not allowed to retroactively rewrite the package.

---

# 15. Continuous-monitor contract for the later active phase

No active B branch has yet run, but the monitoring contract for that future phase is already frozen.

## Before repair

`causal prefix replay`  
→ `pressure/support localization`  
→ `repair anchor`  
→ `package freeze`.

## During repair

The external monitor must record:

- requested repair operation;
- target object;
- native interface used;
- original permission availability;
- closure membership;
- preserve-set effect;
- framework/protocol immutability;
- foreign-state immutability.

Any boundary violation is fail-closed.

## After repair

The repair executor exits.

The native AI system then continues naturally while the external monitor records:

- old-support re-entry;
- new support formation;
- authority regeneration;
- carrier migration;
- scope reopening;
- independent re-anchoring;
- repository/application state;
- native calls/messages;
- process closure;
- terminal outcome separately.

The monitor does not become a persistent corrective controller in the canonical branch.

---

# 16. Evidence provenance

Primary frozen engineering artifacts:

| Object | Path / value |
|---|---|
| Boundary contract | `configs/stage2_r7_boundary_contract_v1.json` |
| 21-path source freeze | `configs/stage2_r7_21_path_source_freeze_v1.json` |
| Monitor firewall | `configs/stage2_r7_monitor_input_firewall_v1.json` |
| Monitor rules | `configs/stage2_r7_structural_monitor_rules_v1.json` |
| Package assembly rules | `configs/stage2_r7_package_assembly_rules_v1.json` |
| Freeze manifest | `configs/stage2_r7_offline_monitor_freeze_v1.json` |
| Normalized events | `stage2/r7_monitor_v1/normalized_structural_events.jsonl` |
| Raw candidates | `stage2/r7_monitor_v1/structural_candidates.jsonl` |
| Repair packages | `stage2/r7_monitor_v1/monitor_derived_repair_packages.jsonl` |
| Parent preflight | `stage2/r7_monitor_v1/parent_reconstruction_preflight.jsonl` |
| Final summary hash | `a7372e03200ea02a819f540953bf9d41a08a862625ba0876f8e8926721b7ad3d` |
| Candidate-scan summary hash | `64b29aa6d69a6ef4ffa3e437f7b5340684dcfea7248c05d1d0e882540c995e0a` |

No raw natural evidence was mutated.

---

# 17. Claim boundary

## Directly evidenced

- all 21 frozen natural first attempts were scanned;
- monitor input excluded the frozen semantic audit;
- replay was configured future-blind;
- 1,120 structural events were normalized;
- 244 raw structural candidate signals were emitted;
- generic structural assembly produced 24 packages across 15 cells;
- 16 packages are parent-reconstruction blocked;
- 7 packages are lineage-gap blocked at immutable foreign-carrier boundaries;
- 1 package is no-repair-required;
- no package is currently active-repair-ready;
- no provider/evaluator call or natural rerun occurred.

## Not established by this stage

- CPR correctness of each monitor candidate;
- exact monitor semantic precision/recall;
- active repair efficacy;
- repair superiority;
- cross-framework repairability ranking;
- prevalence;
- stability after repair;
- any causal effect of a named framework/protocol.

---

# 18. Next operation

The next Stage-II R7 operation is not active repair.

It is:

> **framework-specific native-parent resumability / reconstruction proof over the already-frozen monitor-selected prefixes.**

That work must remain offline and must not:

- rerun a stochastic natural prefix;
- patch upstream framework/protocol semantics;
- bypass native permissions;
- use the semantic audit to choose a different repair target;
- mutate RAG/MemoryBank/compression internal state.

For immutable foreign carriers, the same stage must attempt to bind the observed carrier to the nearest legal downstream application/process repair surface.

Only packages that become machine-verifiable under those rules may later be submitted for active R7 authorization.

Until then:

**ACTIVE REPAIR REMAINS CLOSED.**
