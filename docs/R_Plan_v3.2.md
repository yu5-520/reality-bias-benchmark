# Reality Bias 研究总规划

版本：R Plan v3.2  
日期：2026-09-16  
状态：CANONICAL CANDIDATE / TRAJECTORY-DYNAMICS + SURGICAL CONTROL  
前序：`docs/R_Plan_v3.1.md`

## 1. 版本决策

R Plan v3.2 不推翻 v3.1 的研究 DAG，也不改写任何冻结主体证据、历史 Reviewer 结果或历史规划记录。

v3.2 的任务是把新形成的 trajectory-dynamics 理论与现有 R2-R8 结构对齐，并为后续 R5/R6/R7 增加最小、可隔离、可回放的实验控制能力。

核心新增不是更多 Bias 标签，而是统一机制链：

`多源上下文/概率合成`
`→ 潜在 Escape Propensity`
`→ 可观测 Jump`
`→ C/P 一阶状态偏移候选`
`→ adoption / commit`
`→ propagation / Authority Penetration / inertia`
`→ challenge / correction / retrospective operation`
`→ R 二阶动力学或 recovery`

Escape Propensity 是理论潜变量；主体实验直接观察和冻结的是 Jump、状态迁移、传播、穿透、反馈和恢复。本文不声称读取模型内部神经层面的“逃逸概率”。

## 2. 第一篇论文范围不扩张

第一篇仍是：**结构性存在与机制研究（structural existence / mechanism study）**。

不把下列内容变成完成条件：

- 大规模旗舰模型覆盖；
- 完整工业 MCP/A2A / tools / memory 生态；
- 复杂异构 Agent 组织；
- 全量工程治理系统；
- 大规模 model × topology × domain 矩阵。

v3.2 只增加足够验证机制的实验控制：冻结、回放、分支、单变量干预、有限组织结构对照。

## 3. R0-R9 职责更新

| 编号 | v3.2 职责 | 动力学角色 | 主要产物 |
| --- | --- | --- | --- |
| R0 | Theory Contract / Boundary Definition | 定义 Escape Propensity、Jump、C/P/R、Authority、Inertia、Recovery | theory contract、排除项、可证伪条件 |
| R1 | Theory & Measurement Stress Test | 击穿粗糙边界，区分正常推理/分解/纠错 | counterexamples、boundary tests |
| R2 | Structural Emergence / Jump Layer | 找到自然出现的可观测状态跃迁 | jump/event structural index |
| R3 | Propagation / Penetration / Inertia | Jump 如何被读取、采用、提交、传播并获得作用力 | lineage、penetration depth、descendants |
| R4 | Feedback / Second-order R Dynamics | 既有 C/P 在回看/挑战后被纠正、维持、再生或洗白 | loop windows、R dynamics evidence |
| R5 | Surgical Causal Interruption | 从冻结父节点创建单变量分支，切断指定机制 | intervention branch contrasts |
| R6 | Recovery / Recurrence | 从不同距离和提交深度恢复，观察复发/残留/成本 | recovery branch evidence |
| R7 | Boundary Conditions / Orchestration Structure | 有限比较不同任务组织与上下文交接结构 | scoped orchestration evidence |
| R8 | Reproducibility Freeze | 冻结原轨迹、分支、干预、代码、配置、hash、分析 | replication package |
| R9 | Supplementary Robustness / External Replication | Reviewer、模型家族、human IRR、未来实验室复制 | supplemental audits / external replication |

R9 继续不阻塞 R2-R8。

## 4. R2 — Jump / Event Layer

R2 不直接宣称存在某种 Bias 本体，而是定位可重复追踪的结构跃迁。

机器候选包括但不限于：

- epistemic-status jump；
- provenance attenuation/loss；
- goal-scope / goal-focus change；
- invocation/task-graph expansion；
- task/final/history reopen or revision；
- authority-bearing state transition candidate。

Jump 是事件层对象：

`S_t → S'_t`

是否构成 C/P Reality Bias、是否获得合法 Authority，由后续语义/Authority 审计决定。

## 5. R3 — Propagation / Authority Penetration / Inertia

R3 在现有 lineage 图基础上增加三个明确问题：

1. **Propagation:** Jump-derived state 到达了哪里？
2. **Penetration:** 它在哪一层第一次获得实际系统作用或更高 Authority 身份？
3. **Inertia:** Jump 被继承后，有多少后续状态继续依赖它？

继续区分：

`visible → read → referenced → semantically adopted → committed/decision-effective`

传播不等于穿透。

建议新增结构字段/派生量：

- `jump_id`
- `parent_state_ref`
- `first_read_ref`
- `first_adoption_ref`（语义）
- `first_commit_ref`
- `penetration_depth`
- `affected_descendant_count`
- `affected_agent_count`
- `post_jump_persistence_k`
- `provenance_retention`

旧 trace 缺失所需源字段时必须写 `NOT_RECORDED_IN_SOURCE_VERSION`。

## 6. R4 — Feedback / R as Second-order Dynamics

R4 保留语义盲 structural feedback counter。

R 不再与 reopen / rework / revision 自动等价。

R 的最小结构是：

`prior C/P deviation or unresolved C/P-derived state`
`+ retrospective/challenge/correction opportunity`
`+ persistence/regeneration/amplification/legitimation/laundering/normalization`

正常纠错属于 `CORRECTION`，不是 R 阳性证据。

R4 可研究挑战延迟：

`t+1, t+k, ...`

并观察随着 Jump-derived state 被更多下游状态继承，恢复是否变得更困难。任何时间动力学函数必须在正式确认性实验前冻结定义。

## 7. R5 — Surgical Causal Interruption

R5 的优先实验形式从“重新完整跑两个系统”升级为：

> **same frozen parent state + one preregistered intervention → branched continuation**

原轨迹永远保留，不被分支覆盖。

候选单变量干预：

- block one Authority route；
- remove one context/source item；
- downgrade one epistemic status；
- block one invocation edge；
- insert one deterministic state-commit check；
- change one reopen/transition permission。

主要比较：

- Jump realization 是否改变；
- propagation depth 是否改变；
- penetration depth 是否改变；
- descendants / effect radius 是否改变；
- post-Jump inertia 是否改变。

Proposal 层发生率与 realized operational effect 必须分开统计。一个干预可以不降低 Jump generation，却显著降低 penetration / downstream effect。

## 8. R6 — Recovery / Recurrence

R6 从不同历史位置建立恢复分支：

- Jump 前 checkpoint；
- Jump 后未穿透；
- 已穿透但传播较浅；
- 已形成多级 descendants；
- 已发生 retrospective challenge 之后。

比较：

- full rerun；
- checkpoint recovery；
- local state correction；
- version/generation-style recovery abstraction（只保留研究所需最小机制）。

主要记录：

- rollback/reconstruction success；
- residual descendants；
- recurrence / regeneration；
- recovery distance；
- recovery calls / tokens / turns；
- provenance reconstruction fidelity。

## 9. R7 — 两类 Multi-Agent 组织结构

R7 的优先组织结构边界条件为：

### A. Emergent / Free Routing

只给总任务目标，Agent 在实验政策内自然拆解、组合和调用。

主要候选风险表现：路径扩张、scope/focus expansion、动态调用结构。

### B. Structured / System-Owned Routing

总目标保持一致，但 stage goal、allowed edge 和 handoff point 由实验系统明确控制。

主要候选风险表现：阶段内部 Jump 被结构化 handoff 继承，固定路径稳定传播 post-Jump state。

关键命题不是哪一种架构“更好”，而是：

> **不同 orchestration structure 是否把同一类潜在 escape risk 转化为不同的 Jump、传播、穿透、惯性和恢复动力学。**

第一篇优先做最小二条件比较；只有发现 routing ownership 与 goal staging 无法区分时，再追加：

`goal fixed/staged × context continuous/reset-or-compressed`

的 2×2 拆分。

## 10. Experimental Control Layer

试验仓增加一个**最小实验控制层**，不引入任何外部工程框架名称，也不复制完整生产系统。

它只承担实验仪器功能：

`Observe + Freeze + Replay + Branch + Intervene`

最小对象：

1. `State Anchor` — 可验证的冻结节点；
2. `Proposal` — Agent 输出但尚未自动等于 operational reality；
3. `Commit Gate` — 可配置的最小 deterministic transition check；
4. `Branch Manifest` — parent trace/state + intervention + replicate identity；
5. `Immutable Journal` — 原历史与每个分支分别保存。

该层默认 **observe-only / intervention-off**，不能静默改变既有 Free-Agent baseline。

## 11. 分支与回放证据规则

每个新分支至少绑定：

- `parent_trace_hash`
- `parent_event/state_ref`
- `parent_state_hash`
- `intervention_spec`
- `intervention_hash`
- `branch_id`
- `replicate_index`
- model/config/code identity
- branch output hashes

原则：

> **Replay(state) 不等于 replay(model randomness).**

同一冻结 state 可以作为相同历史条件的起点，但模型/provider 随机性和版本漂移必须单独记录。概率性 Escape/Jump 研究需要重复分支，而不是期待一次 replay 字节级复现模型输出。

## 12. 行为层 Escape Hazard

在同一冻结父状态下重复展开 N 次，可以得到行为层估计：

`h_hat(S_t) = # branches with preregistered Jump / N`

改变一个实验变量 X 后比较：

`Δh = h_hat(S_t + ΔX) - h_hat(S_t)`

这只描述在冻结条件下的行为分布，不等价于神经内部 escape probability。

Jump incidence、penetration depth、post-Jump inertia、recovery 必须分开测量，因为治理变量可能只改变其中一部分。

## 13. R8 — Reproducibility Freeze

R8 除 v3.1 已要求的 subject trace/config/code/hash 外，新增冻结：

- state anchors；
- branch manifests；
- intervention specs；
- branch lineage graph；
- current trajectory measurement contract；
- replay/branch validator outputs；
- original trajectory 与所有 branch 的不可混淆身份。

R8 完成后，外部复制者应能：

`load frozen parent → verify hashes → apply named intervention → run branch → freeze evidence → derive same deterministic structure`

语义 Reviewer 仍是后置层。

## 14. Version / non-retroactivity rule

- v3.1 及更早规划保持历史事实。
- Batch001 等历史主体 evidence 不重跑、不重写。
- 新 deterministic 指标可以读取旧冻结证据，但只能使用真实存在的源字段。
- 新 Escape/Jump/Inertia 术语不得伪装成旧 run 的同期预注册语言。
- structured/staged、branch、commit-gate 等新行为证据必须产生新版本 subject/intervention evidence。
- Repository 更新不构成任何付费 API 授权。

## 15. Forward execution order

当前前向顺序：

`理论合同 v0.3`
`→ measurement / control layer offline implementation`
`→ environment version alignment`
`→ deterministic/mock branch validation`
`→ freeze new intervention/orchestration protocol`
`→ R2-R4 existing evidence consolidation`
`→ R5 branch intervention`
`→ R6 recovery`
`→ R7 limited orchestration boundary`
`→ R8 freeze`
`→ R9 optional robustness / external replication`

在正式新 subject 或付费运行之前，必须先完成离线控制层验证与实验合同冻结。
