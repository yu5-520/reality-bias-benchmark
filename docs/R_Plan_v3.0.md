# Reality Bias 研究总规划

版本：R Plan v3.0  
日期：2026-09-15  
状态：MEASUREMENT-ARCHITECTURE REDESIGN / SUBJECT ARENA FROZEN

## 1. 版本决策

R Plan v3.0 不推翻 v2.1 的主体实验底座，也不回写覆盖历史定义。v2.1 继续作为历史计划和 Batch001 采集阶段的有效记录。v3.0 的升级对象是：理论操作定义、R2-R4 测量架构、评审接口和证据组合方式。

主体 Arena、自由多 Agent 协作、固定窗口 Base、有限 K 上限实验、原始 trace 冻结、同步记录与异步审计原则继续保留。当前正式 Batch001 的原始行为证据不重采样、不重写；新版测量层优先在冻结证据上验证。

核心原则升级为：

> **机器负责定位结构变化与压缩搜索空间；评审负责判断自然语言语义中的边界是否真正被穿透。**

> **预测正常、分工正常、回溯正常。Reality Bias 由“未经授权的边界变化”定义，而不是由某一种表面行为定义。**

## 2. 三种权限穿透模型 v2

### 2.1 C — Completion：信息真实性边界穿透

操作定义：**Unauthorized Epistemic-State Promotion**。

允许预测、推断、派生、建议和条件判断。只要这些信息保留其认识论身份、来源和必要的不确定性标识，就不构成 C。

C 的候选结构是信息确定性发生向上迁移，例如：

- predicted → fact
- preliminary → confirmed
- inferred → verified
- planned → executed

只有当该确定性提升缺乏足够验证、认证或外部证据时，才由语义评审判定为 C realization。

多 Agent 链路允许 C 具有潜伏期。合法预测可以经过多个 Agent 的压缩、摘要、派生和传递后才第一次发生非法确定性提升。因此必须区分：

- C precursor：尚未越界，但不确定性、来源或状态身份开始弱化；
- C realization：第一次未经授权的确定性提升；
- C inheritance：下游读取或继承已经被污染的状态；
- C regeneration：后续节点再次产生新的非法确定性提升。

### 2.2 P — Perfection：任务目的边界穿透

操作定义：**Unauthorized Goal-Scope / Goal-Focus Expansion**。

多 Agent 分工、并行调用、重复调用、专家审查都不是 P 的定义。判断核心不是行为数量，而是行为所服务的目的是否仍处于原任务的授权范围内。

合法 Goal Decomposition：把原目标 G0 分解为完成 G0 所必需的子目标。

P 候选包括两种结构：

- **Scope Expansion**：新增目标 ΔG 超出原目标及其必要分解闭包；
- **Focus Drift**：目标集合表面不变，但未经授权地重构了目标优先级或任务重心，使实际决策被次要/新增问题主导。

只有当新增目的或重心迁移不是原任务必要分解、也没有显式外部授权时，才由语义评审判定为 P realization。

Invocation 是 P 的常见实现通道，而不是 P 本身。即使只调用一个 Agent，也可能产生 P；即使同时调用多个 Agent，只要全部严格服务于 G0，也可能完全没有 P。

### 2.3 R — Retrospective：历史合法性边界穿透

操作定义：**Unauthorized Retrospective Legitimation / Regeneration of C/P**。

返工、复查、回溯、FINAL 重开、重新计算和纠错本身均为中性行为。R 是作用于 C/P 及其历史后果上的二阶时间机制。

R 重点观察：

- R-C regeneration：返工过程中重新产生新的 C；
- R-P expansion：返工过程中重新扩大任务范围或任务重心；
- R-laundering：原本可识别的 C/P 经过回溯解释后，被重新包装为合法、必要、已验证或原本就在任务范围内；
- R-normalization：被洗白后的 C/P 状态成为后续 Agent 的普通合法输入，继续支撑新的决策或新的 C/P。

R 的核心不是“是否发生回溯”，而是回溯是否改变了原 C/P 的历史合法性，或者在返工过程中重新生成边界穿透。

## 3. 新的统一研究对象：边界状态迁移

v3.0 将 Reality Bias 的直接研究对象从行为标签改为三类边界状态：

| 模型 | 边界对象 | 正常能力 | 未授权变化 |
| --- | --- | --- | --- |
| C | Epistemic Boundary | 预测、推断、派生 | 确定性向上提升 |
| P | Goal Boundary | 分工、必要子任务 | 范围扩大或重心偏移 |
| R | Historical Legitimacy Boundary | 返工、纠错、回溯 | C/P 再生成、洗白或正常化 |

因此 `write_state`、`invoke_agent`、`revise_final_state` 只作为行为载体和 Authority route，不再隐式等同于 C/P/R。

C/P/R 与 Authority I/V/T 继续独立编码：Bias 描述边界发生了什么变化；Authority 描述该变化通过什么系统能力获得了效力以及是否被授权。

## 4. R0-R9 新职责

| 编号 | v3.0 职责 | 主要产物 |
| --- | --- | --- |
| R0 | 理论合同与边界状态定义 | C/P/R v2 定义、正常反例、边界测试 |
| R1 | 测量压力测试 | 预测≠C、分工≠P、回溯≠R 等反例验证 |
| R2 | Jump Detection / Event Audit | 结构跳点候选 + 局部语义 realization 审计 |
| R3 | Lineage / Drift / Penetration Range | 信息血缘、目标血缘、任务范围、重心偏移、有效实施 |
| R4 | Loop / Laundering / Black-Hole Dynamics | 中性闭环、C/P 洗白、正常化、自增强、黑洞候选 |
| R5 | Control / Causal Interruption | 切断指定依赖或权限后比较机制变化 |
| R6 | Recovery | 修正、局部恢复、复发、洗白后的恢复难度 |
| R7 | Generalization / Measurement Robustness | 跨模型、跨领域、跨 Reviewer 稳健性 |
| R8 | Reproducibility Freeze | trace、结构索引、评审记录、规则版本全部冻结 |
| R9 | Paper Claim Mapping | 每个理论主张绑定对应证据层级 |

## 5. 机器层与语义层的职责边界

### 5.1 Machine Structural Observer

机器只记录和导出客观结构事实，不直接宣布 C/P/R：

- state version / field / status change；
- message delivered / read；
- invocation created / pending / executed；
- actor activation；
- task/goal structure mutation；
- finalization / reopening / revision；
- source/provenance references；
- structural return path / feedback round；
- token、调用数、Agent 数、reopen depth 等动力学指标。

机器可以生成 `*_CANDIDATE`，例如 epistemic jump candidate、scope change candidate、focus drift candidate、feedback-loop candidate、black-hole candidate，但不得自动把候选写成 Reality Bias 真值。

### 5.2 Semantic Reviewer

Reviewer 只在机器确定的跳点、关系范围或闭环窗口内读取 Agent 的实际输入输出，判断：

- 预测/推断是否真的被提升为事实；
- 新增任务是否是原目标的必要分解；
- 任务重心是否发生未经授权的迁移；
- 某条消息是否被下游语义采用，而不仅仅是可见；
- 回溯是否真正修正 C/P、保持 C/P、生成新 C/P，或把 C/P 洗白；
- 洗白后的状态是否获得新的系统合法性并继续驱动决策。

机器的作用是压缩 Reviewer 的搜索空间，而不是替代自然语言理解。

## 6. R2-R4 统一测量链

`Subject Trace → Machine Structural Index → R2 Jump Candidates → R3 Lineage Expansion → R4 Loop/Dynamics Windows → Semantic Review → Mechanism Synthesis`

R2、R3、R4 继续共享同一条冻结轨迹，不要求重新运行三套主体实验。

### R2

定位第一次值得语义审查的结构变化，并在局部 evidence window 中判断是否发生 C/P/R realization。

### R3

从 R2 跳点向前后展开血缘。机器给出 exposure / read / provenance / state-version / invocation graph；Reviewer 判断 semantically adopted、decision-effective 和真正的 penetration range。

### R4

结构计数器继续语义盲，只负责定位中性反馈回路。Reviewer 在闭环窗口内区分：correction、persistence、regeneration、amplification、laundering、normalization。

## 7. 闭环、黑洞与自增强

闭环是结构事实，不等于 Bias。

黑洞是动力学候选，不等于无限循环。机器可以基于以下指标定位黑洞候选：

- feedback rounds 增加；
- calls / tokens / active Agents 增加；
- task scope / focus drift 增加；
- reopen depth 增加；
- verified evidence gain / round 下降；
- original-goal progress / round 下降。

Reviewer 再判断候选区间是否由 C、P、R 的边界穿透维持。

自增强的高阶候选路径：

`C/P realization → downstream inheritance → retrospective laundering → normalization → washed state becomes legitimate premise → new C/P → new laundering`

只有后续 R5 切断指定反馈依赖或权限后，增强显著减弱，才允许升级为因果 self-reinforcement 证据。

## 8. Base 与 Upper-Bound 保持不变

Base 固定窗口仍负责“测得准”；K=2/K=4 循环预算仍负责“看得远”。K counter 必须保持语义盲，不能读取新版 C/P/R 评审结果。

但在新版 Measurement/Reviewer v2 完成冻结并在 Batch001 上验证以前，不新增付费 K 实验。优先解决 Base 的测量可重复性。

## 9. Batch001 的新用途

Batch001 不废弃，也不改写既有 Reviewer A/B 结果。原 Reviewer v1 继续作为 append-only 历史测量层。

新版计划在同一 frozen evidence 上新增 Measurement v2 / Reviewer v2，比较：

- 行为型 rubric 与边界型 rubric 的差异；
- 假阳性是否下降；
- C/P/R 核心事件是否保持；
- 跨 Reviewer agreement 是否提高；
- 主要 disagreement 是否从“定义模糊”转移为真正的证据边界问题。

如果原始行为不变而新版测量可重复性提高，这本身是第一篇论文的重要方法学证据。

## 10. 当前执行门

当前顺序：

`R Plan v3.0 freeze → R2-R4 Measurement Plan v2 freeze → Reviewer System v2 freeze → offline reconstruction on Batch001 → no-cost consistency tests → blinded re-review only after explicit paid-review authorization → Base replication → optional K=2/K=4`

在前四步完成前，不启动新的付费主体实验。
