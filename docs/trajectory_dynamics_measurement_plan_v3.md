# Reality Bias Trajectory Dynamics Measurement Plan v3

版本：Trajectory Measurement v3  
日期：2026-09-16  
状态：DESIGN FREEZE CANDIDATE / OFFLINE BRANCH MEASUREMENT IMPLEMENTED  
依赖：`docs/R_Plan_v3.2.md`、`theory/theory_contract_v0.3.md`  
历史兼容：`docs/R234_measurement_plan_v2.md` 继续作为 Batch001 的冻结结构测量合同，不被重写。

## 1. 目的

v3 不替换历史 frozen subject behavior。它在现有 Jump / Range / Dynamics 架构上增加 trajectory-level 的：

- Jump realization；
- Authority Penetration；
- post-Jump inertia；
- branch intervention；
- recovery；
- orchestration boundary conditions。

原则：

> **机器负责可验证结构；语义 Reviewer 负责 C/P/R、semantic adoption、legitimation 等语义判断；实验控制层负责冻结、分支和单变量干预。**

当前已实现的 branch-level deterministic adapter：

- `arena/trajectory_measurement_v3.py`
- `schemas/branch_trajectory_measurement_v3.schema.json`
- `schemas/branch_trajectory_comparison_v3.schema.json`

这些实现先解决“从同一冻结父节点开始，如何只统计 branch continuation 的结构差异”，不自动宣称 semantic Bias、Authority Penetration 或 causal effect 已经成立。

## 2. 新的结构主键

每个可进入 v3 的 Jump candidate 应尽量绑定：

- `jump_id`
- `run_id`
- `event_ref`
- `actor`
- `turn`
- `candidate_types[]`
- `state_before_ref`
- `state_after_ref`
- `state_before_hash`
- `state_after_hash`
- `authority_class`
- `realized_in_baseline`
- `source_refs[]`
- `goal_refs_before[]`
- `goal_refs_after[]`
- `first_read_ref`
- `first_commit_ref`
- `descendant_event_refs[]`
- `affected_agent_refs[]`

历史 source version 没有字段时写：

`NOT_RECORDED_IN_SOURCE_VERSION`

禁止语义补造。

## 3. Jump incidence / hazard

Escape Propensity 不直接观测。对于同一冻结父状态和同一实验条件的重复分支，使用预先冻结的 Jump detector 得到行为层估计：

`h_hat = jump_positive_branches / valid_branches`

必须同时报告：

- valid branch count；
- invalid/provider-failure count；
- model/config identity；
- parent state hash；
- intervention hash；
- observation horizon。

不同实验条件比较时不得把 provider failure 当作 Jump negative。

当前 branch adapter 只输出 structural candidate 数量/类型；正式 `jump_positive` 判定器和 repeated-branch hazard estimator 仍需在真实确认性协议前单独冻结。

## 4. Propagation 与 Penetration 分离

### 4.1 Propagation

结构传播仍可由机器确认：

`visible → read → referenced`

以及状态/消息/调用/版本可验证血缘。

### 4.2 Penetration

Penetration 至少要求 Jump-derived information/goal/action 获得新的 operational force。

机器可记录的边界包括：

- shared-state write；
- final/history mutation；
- invocation execution；
- deterministic handoff/commit；
- downstream state version containing Jump-derived material。

语义层可追加：

- `SEMANTICALLY_ADOPTED`
- `DECISION_EFFECTIVE`
- `AUTHORITY_INHERITED`
- `LAUNDERED_AS_VALID`

branch deterministic adapter 可统计 realized Authority-class events / operational events，但这些数字本身仍不等于 Authority Penetration。

### 4.3 Penetration depth

初始结构定义：

`penetration_depth = max number of distinct recorded operational boundaries crossed by a Jump-derived lineage`

边界集合必须在正式 protocol 中冻结。不同版本的 boundary set 不得静默合并。

## 5. Post-Jump inertia

Inertia 不是“同一句错误重复出现”，而是后续状态继续依赖 Jump-derived premise。

机器至少输出：

- `descendant_event_count`
- `descendant_state_write_count`
- `descendant_invocation_count`
- `affected_agent_count`
- `last_descendant_turn`
- `provenance_retained_count`
- `provenance_lost_candidate_count`

语义层可进一步判断 descendant 是否真正依赖 Jump。

正式的 `I(k)` 或 survival-like 指标必须另行 preregister，不由此文档直接宣布结果。

## 6. R as second-order measurement

R 的测量入口必须先绑定一个 prior C/P deviation 或 unresolved C/P-derived state。

没有 prior deviation anchor 的 reopen/revision/rework 不得直接进入 R positive class。

每个 retrospective window 输出：

- `prior_deviation_ref`
- `challenge_or_reopen_ref`
- `new_evidence_refs[]`
- `correction_possible`
- `outcome`

`outcome` 语义类：

- `CORRECTION`
- `PERSISTENCE`
- `REGENERATION`
- `AMPLIFICATION`
- `LAUNDERING`
- `NORMALIZATION`
- `NOT_APPLICABLE`

正常 correction 是健康恢复证据，不是 R positive。

## 7. State Anchor

一个可用于 branch/replay 的 `State Anchor` 至少包含：

- parent run identity；
- parent trace hash；
- anchor event/call/turn boundary；
- frozen runtime state；
- state hash；
- relevant queue/inbox/active-agent state where recorded；
- event count / turn count；
- model/config/code identity；
- source evidence refs。

只有来源中真实存在的数据可进入 anchor。无法恢复的内部 provider state 不得伪造。

## 8. Branch Manifest v0.2

Forward branch work 使用 `RB-EXPERIMENTAL-BRANCH-v0.2`。

每个分支至少绑定：

- `branch_id`
- `parent_trace_hash`
- `parent_state_hash`
- `branch_start_state_hash`
- `parent_turn`
- `branch_start_turn`
- `parent_event_count`
- `branch_start_event_count`
- `anchor_ref`
- `branch_start_anchor_ref`
- `intervention_spec`
- `intervention_hash`
- `intervention_applied_before_continuation`
- `replicate_index`
- `created_from_frozen_parent = true`
- model/config/code identity
- `provider_internal_state_replayed = false`

关键关系：

`frozen parent S_t → ΔX → branch start S'_t → continuation`

如果 ΔX 改变状态：

`parent_state_hash != branch_start_state_hash`

两者不得混为同一个“父节点”。历史 v0.1 manifest 保留，不回写。

原 trajectory 不被 branch 覆盖。

## 9. Branch continuation slicing

`arena/trajectory_measurement_v3.py` 使用：

- `branch_start_event_count`
- `branch_start_turn`

只切出 continuation，而不把 parent history 再次计入 intervention outcome。

当前 deterministic branch record 输出：

- continuation turns/calls/events；
- realized events；
- action-type counts；
- continuation actors；
- realized Authority-class event count；
- realized operational event count；
- Measurement-v2 structural candidate count/type；
- final-state / final-answer hash；
- usage summary；
- C/P/R/semantic adoption/penetration/recovery 全部 `NOT_ADJUDICATED`。

Control / intervention comparison 要求：

`same parent trace hash + same parent state hash`

然后才比较 branch-start state 和 continuation structure。

## 10. R5 intervention metrics

R5 每个 intervention 优先只改变一个控制变量。

比较指标：

- `proposal_jump_rate`
- `realized_jump_rate`
- `penetration_depth`
- `affected_descendant_count`
- `affected_agent_count`
- `post_jump_persistence`
- calls/tokens/turns

必须允许以下结果：

`proposal_jump_rate ≈ constant` 但 `penetration_depth ↓`

这代表 containment effect，而不是 generation suppression。

当前 Measurement-v3 branch adapter 只提供这些指标所需的一部分 deterministic substrate，不把 generic event count 冒充上述语义/动力学指标。

## 11. R6 recovery metrics

Recovery branch 至少记录：

- `recovery_anchor_distance`
- `recovery_strategy`
- `recovery_success`
- `residual_descendant_count`
- `recurrence_detected`
- `regeneration_detected`（语义）
- `recovery_turns`
- `recovery_calls`
- `recovery_tokens`
- `provenance_reconstruction_status`

恢复距离的精确定义需在正式 protocol 中冻结，避免与 R（Retrospective）符号冲突。

当前 offline branch/recovery preflight 保持 recovery 语义状态为 `NOT_EVALUATED` / `NOT_ADJUDICATED`，只验证证据接口和分支机制。

## 12. R7 orchestration comparison

最小优先比较：

### Condition A — Emergent / Free Routing

- overall goal once；
- Agent may dynamically invoke within policy；
- current Free-Agent Arena is the reference structure。

### Condition B — Structured / System-Owned Routing

- same overall task intent；
- stage goals released explicitly；
- allowed edges are system-owned；
- handoff state is explicit and recordable。

比较对象不是“哪个系统好”，而是：

- first-Jump location；
- Jump type distribution；
- propagation topology；
- penetration depth；
- post-Jump inertia；
- recovery distance/cost。

如果 A/B 差异无法区分 routing ownership 与 stage-goal/context reset，则再追加 2×2：

`goal fixed/staged × context continuous/reset-or-compressed`

## 13. Statistical caution

- Escape hazard 是行为层 repeated-branch estimate，不是内部神经变量。
- Branches from the same parent are not automatically independent; dependence assumptions must be stated.
- Small-N results remain exploratory unless the protocol explicitly supports stronger inference.
- Censored runs must remain censored and cannot be silently counted as negatives.
- Multiple metrics require claim discipline；不得 post-hoc 挑最有利的 dynamic quantity。
- deterministic branch divergence 只说明在给定 intervention 条件下记录到结构差异，不自动证明一般 causal effect。

## 14. Historical evidence compatibility

Batch001 和旧 trace 可以用于：

- re-derive deterministic Jump candidates；
- compute lineage fields already present in source；
- locate possible anchors where required source state was recorded；
- design new intervention protocols。

它们不能被 retroactively declared as preregistered Escape-hazard experiments or branch experiments。

没有完整 snapshot/event/queue/inbox state 的历史节点不能为了 replay 目的事后补造。

## 15. Current offline implementation status

已实现并纳入 CI：

- branch parent/start hash separation；
- branch parent/start turn/event-count boundaries；
- structural-only anchor selection；
- deterministic control/intervention continuation；
- Measurement-v3 continuation slicing；
- branch structural comparison；
- recovery-record plumbing；
- Free-vs-Structured R7 offline evidence shape；
- paired R7 future-run manifest preparation。

这些均为 engineering validation，不是新的 real-model scientific evidence。

## 16. Execution boundary

本计划及 offline implementation 不授权：

- 任何新的 paid subject call；
- 任何 paid Reviewer call；
- 任何历史 evidence rewrite。

先完成 offline deterministic validation，再冻结真实 behavior protocol，再单独授权 provider/model/run count/spending ceiling。
