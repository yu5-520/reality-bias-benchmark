# Reality Bias Trajectory Dynamics Measurement Plan v3

版本：Trajectory Measurement v3  
日期：2026-09-16  
状态：DESIGN FREEZE CANDIDATE  
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
- anchor event index / call boundary；
- frozen runtime state；
- state hash；
- relevant queue/inbox/active-agent state where recorded；
- model/config/code identity；
- source evidence refs。

只有来源中真实存在的数据可进入 anchor。无法恢复的内部 provider state 不得伪造。

## 8. Branch Manifest

每个分支必须绑定：

- `branch_id`
- `parent_trace_hash`
- `parent_state_hash`
- `anchor_ref`
- `intervention_type`
- `intervention_spec`
- `intervention_hash`
- `replicate_index`
- `created_from_frozen_parent = true`
- model/config/code identity
- output evidence refs/hashes after completion

原 trajectory 不被 branch 覆盖。

## 9. R5 intervention metrics

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

## 10. R6 recovery metrics

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

## 11. R7 orchestration comparison

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

## 12. Statistical caution

- Escape hazard 是行为层 repeated-branch estimate，不是内部神经变量。
- Branches from the same parent are not automatically independent; dependence assumptions must be stated.
- Small-N results remain exploratory unless the protocol explicitly supports stronger inference.
- Censored runs must remain censored and cannot be silently counted as negatives.
- Multiple metrics require claim discipline; no post-hoc cherry-picking of the most favorable dynamic quantity.

## 13. Historical evidence compatibility

Batch001 和旧 trace 可以用于：

- re-derive deterministic Jump candidates；
- compute lineage fields already present in source；
- locate possible anchors where required source state was recorded；
- design new intervention protocols。

它们不能被 retroactively declared as preregistered Escape-hazard experiments or branch experiments。

## 14. Execution boundary

本计划本身不授权：

- 任何新的 paid subject call；
- 任何 paid Reviewer call；
- 任何历史 evidence rewrite。

先完成 offline deterministic validation，再冻结新 behavior protocol，再单独授权真实 provider run。
