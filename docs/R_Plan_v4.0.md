# Reality Bias 研究总规划

版本：R Plan v4.0  
日期：2026-09-16  
状态：FORWARD CANDIDATE / SYSTEM-BEHAVIOR DYNAMICS  
前序：`docs/R_Plan_v3.2.md`

## 1. 版本决策

R Plan v4.0 不重写 R Plan v3.2、Theory Contract v0.3、Trajectory Measurement v3、Batch001、历史 Reviewer 记录或任何冻结主体证据。

v4.0 的变化不是新增更多 Bias 标签，而是重新确定研究坐标系：

- **实验/分析单位：System Trajectory**；
- **测量位置：Node / Boundary**；
- **主要观测对象：Behavior / State Transition**；
- **语义分类层：C/P/R 与 Authority 相关语义判断**。

核心原则：

> **Behavior first, semantic label second.**

研究重点从“模型为什么这样想”转向“系统中实际发生了什么行为、这些行为如何改变状态、如何被继承并形成系统级后果”。

## 2. 统一机制链

前向理论链更新为：

`controllable antecedents X_pre`
`→ structural/interaction tension`
`→ latent Escape Propensity`
`→ observable Jump`
`→ first-order C/P state-deviation candidate`
`→ adoption / commit`
`→ propagation / Authority Penetration / inherited inertia`
`→ challenge / correction / retrospective operation`
`→ second-order R dynamics or recovery`
`→ system outcome`

其中：

- `X_pre` 是可操纵的上游实验变量；
- Tension 是理论上的中间构念，不要求在第一篇论文中被直接测量；
- Escape Propensity 是潜在性质，不声称可直接读取；
- Jump 是行为层可观察实现；
- Propagation / Penetration / Inertia / Recovery 是系统动力学结果。

## 3. 测量层级

### 3.1 System Trajectory — 实验/分析单位

一次完整 subject run 或 branch continuation 构成一条系统轨迹。最终问题是：

- 是否发生 Jump；
- Jump 到达哪些节点；
- 是否获得 operational force；
- 是否产生 inherited inertia；
- challenge 后进入 R 还是 recovery；
- 系统最终状态与 valid trajectory 相距多远。

### 3.2 Node / Boundary — 测量位置

可观测位置包括但不限于：

- Agent activation / turn；
- message send / receive / read；
- shared-state read / write；
- RAG/context handoff；
- invoke proposal / realization；
- commit gate；
- FINAL / reopen / revision；
- authority conversion boundary；
- recovery/checkpoint boundary。

节点不是研究对象本身，而是系统行为测量仪器的安装位置。

### 3.3 Behavior / State Transition — 主要观测量

重点记录：

`read / write / message / invoke / commit / reopen / revise / inherit / finalize`

以及行为导致的：

`S_t → S_t+1`

自然语言 reasoning 只作为必要时的局部解释证据，不作为整条实验的主测量单位。

### 3.4 Semantic Annotation — 后置语义层

机器先定位和冻结行为、状态变化、血缘与边界，再由后置 Reviewer 判断：

- C/P/R；
- semantic adoption；
- legitimation / laundering / normalization；
- Authority Penetration 的语义条件；
- decision effect。

语义 Reviewer 不负责重新发现整个系统发生了什么。

## 4. Tension 的位置

Tension 的作用是给 Escape Propensity 提供上游来源解释，而不是把第一篇论文变成“张力测量论文”。

可操纵前置变量包括但不限于：

- `GOAL_CONFLICT_LEVEL`；
- `EVIDENCE_CONFLICT_LEVEL`；
- `CONTEXT_COMPETITION_LEVEL`；
- `AUTHORITY_MISMATCH_LEVEL`；
- `INFORMATION_LOAD`；
- `ALTERNATIVE_PATH_COUNT`。

第一篇允许只测：

`do(X_pre) → Jump / downstream trajectory`

而不声称直接读出内部 tension 或 Escape Propensity。

未来若多个不同上游操纵产生稳定、部分共同的行为响应，可进一步研究 Tension 的结构与 Escape hazard。

## 5. R0–R9 重新分工

| 编号 | v4.0 职责 | 系统角色 |
| --- | --- | --- |
| R0 | Theory Contract / Measurement Ontology | 定义 System–Node–Behavior–Transition–Tension–Escape–Jump–CPR |
| R1 | Boundary / Counterexample Stress Test | 排除正常推理、正常任务分解、合法纠错、合法扩展 |
| R2 | Behavior / Jump Emergence | 从同一系统轨迹定位行为跃迁与 Jump candidate |
| R3 | Transmission / Penetration / Inertia | 测传播、作用力获得与 Jump-derived path dependence |
| R4 | Retrospective Dynamics | 测 challenge/correction 后的 R、persistence、regeneration 与 recovery |
| R5 | Causal Manipulation Layer | 在前置/中段/后段不同位置进行单变量分支干预 |
| R6 | Recovery / Recurrence | 测不同距离、提交深度与恢复策略下的恢复和复发 |
| R7 | System Structure / Boundary Conditions | 测 topology、routing ownership、stage boundary、context handoff 等系统变量 |
| R8 | Reproducibility Freeze | 冻结轨迹、节点、行为、状态、branch、变量、代码、配置与 hash |
| R9 | Supplementary Robustness / External Replication | Reviewer、模型家族、human IRR、跨领域与外部复制 |

## 6. R2–R4 不再解释为顺序实验

R2、R3、R4 是同一冻结系统轨迹的同步观察层：

```text
                   ┌─ R2: Behavior / Jump emergence
System Trajectory ├─ R3: Transmission / Penetration / Inertia
                   └─ R4: Retrospective / R dynamics
```

它们可以同步记录、异步审计。

因此一条 subject trajectory 可以同时产生：

- R2 structural behavior observations；
- R3 lineage / penetration observations；
- R4 retrospective windows；

而不需要分别重新运行三次主体实验。

## 7. R5 — 多位置因果干预层

R5 不再由某一种 status downgrade 定义。现有 `EPISTEMIC_STATUS_DOWNGRADE_TO_PROVISIONAL` 保留，但重新定位为第一个中段干预实例。

### R5-PRE — Formation Manipulation

改变 Jump 之前的上游变量：

- goal conflict；
- evidence conflict；
- context competition；
- authority mismatch；
- information load；
- alternative path availability。

主要结果：

- Jump incidence / hazard；
- Jump type distribution；
- first-Jump location。

### R5-MID — Realization / Containment Manipulation

改变 Jump 后、系统后果形成前的变量：

- epistemic status downgrade；
- commit gate；
- authority route block；
- invocation edge block；
- shared-state visibility；
- routing / handoff policy。

主要结果：

- adoption；
- propagation depth；
- penetration depth；
- affected descendants / agents；
- post-Jump inertia。

### R5-POST — Stabilization Manipulation

在偏移已传播或获得作用力后改变：

- challenge timing；
- provenance restoration；
- correction permission；
- reopen policy；
- review/verification timing。

主要结果：

- persistence；
- R regeneration / amplification；
- time-to-recovery；
- residual contamination。

## 8. R6 — Recovery / Recurrence

R6 专门研究系统从不同历史距离恢复：

- pre-Jump checkpoint；
- post-Jump / pre-penetration；
- shallow penetration；
- multi-descendant state；
- post-challenge retrospective state。

比较 local correction、checkpoint recovery、provenance reconstruction 与必要时 full rerun。

R6 不承担前置 tension 实验，也不把 ordinary correction 自动归类为 R。

## 9. R7 — System Structure / Boundary Conditions

R7 不再只是“最后做一次 Free vs Structured 比较”，而是系统级结构变量层。

优先变量：

- routing ownership；
- topology density；
- stage boundary；
- context continuity / reset / compression；
- dynamic invocation surface；
- proposal/commit separation；
- Agent count；
- shared-state visibility。

现有 Emergent / Free Routing 与 Structured / System-Owned Routing 保留为第一个 R7 对照族。

R5、R6、R7 建立在 R2–R4 的共同观测基础上，不要求严格串行完成。

## 10. 多类 State Anchor

Anchor 从“找一个高确定性 write_state”升级为按实验问题选择测量位置。

前向 anchor class：

- `ANTECEDENT_ANCHOR` — 前置变量进入系统之前；
- `TRANSITION_ANCHOR` — Jump candidate 前后；
- `PENETRATION_ANCHOR` — 已传播/获得 operational force 后；
- `CHALLENGE_RECOVERY_ANCHOR` — challenge / correction / recovery 边界。

所有可执行 branch anchor 仍必须满足当前 runtime 的 branchability 条件，包括真实可恢复状态和 pending continuation work。

历史 `HIGH_CERTAINTY_STATE_WRITE_CANDIDATE` 保留为 `TRANSITION_ANCHOR` 的一个具体 selector，不回写其历史身份。

## 11. Behavior Event 作为最小主证据单位

前向统一结构：

```text
SystemTrajectory
  └── Node / Boundary
       └── BehaviorEvent
             └── StateTransition
```

Behavior Event 至少应绑定：

- event identity；
- system trajectory / branch identity；
- node/boundary；
- actor；
- action type；
- target；
- proposal vs realized；
- state-before / state-after hashes；
- authority before/after where applicable；
- provenance/source refs；
- parent/dependency refs；
- turn/event index。

Jump detector、lineage、penetration、inertia 与 semantic review 都在此主证据层之上工作。

## 12. Experimental Variable Registry

前向实验变量必须进入统一注册表，不再把 intervention 硬编码为单一 status downgrade。

每个变量至少登记：

- `variable_id`；
- `family`；
- `stage = PRE | MID | POST | STRUCTURE`；
- target boundary；
- control level；
- intervention/manipulation level；
- held-constant fields；
- expected observable family；
- evidence requirements；
- version / hash。

初始变量族包括：

- `GOAL_CONFLICT_LEVEL`；
- `EVIDENCE_CONFLICT_LEVEL`；
- `CONTEXT_COMPETITION_LEVEL`；
- `INFORMATION_LOAD`；
- `AUTHORITY_EDGE_BLOCK`；
- `EPISTEMIC_STATUS_DOWNGRADE`；
- `ROUTING_EDGE_BLOCK`；
- `CHALLENGE_DELAY`；
- `PROVENANCE_RESTORE`；
- `ORCHESTRATION_STRUCTURE`。

## 13. 第一篇论文边界

长期 R Program 可以扩展大量变量和跨领域实验，但第一篇继续保持窄范围。

第一篇优先建立：

`Jump`
`→ propagation`
`→ penetration / inertia`
`→ branch intervention`
`→ recovery`

Tension 只作为 Escape Propensity 的上游来源解释和未来实验入口。

不要求第一篇完成：

- tension 的直接测量；
- 全变量矩阵；
- 全模型覆盖；
- 大规模跨领域复制；
- 对内部 chain-of-thought 的完整解释。

## 14. Version / Non-retroactivity Rule

- v3.2、Theory v0.3、Measurement v3 与全部历史 evidence 保持历史事实；
- Batch001 不重新解释成同期 v4 预注册实验；
- 历史 CPR reviewer 结果继续作为语义层证据；
- 新 Behavior/Event/Variable/Anchor 字段不存在于旧源数据时必须标记缺失，不能事后补造；
- 新 v4 行为证据必须产生新版本 subject/intervention evidence；
- 所有分支保留 parent / branch-start 分离；
- provider hidden state 不宣称被 replay；
- 仓库更新不构成 paid API 授权。

## 15. Forward Execution Order

新的前向顺序不是把所有 R 编号串成一条流水线，而是：

```text
Theory v0.4 + Measurement v4
        ↓
Behavior/Event + Variable + Boundary registries
        ↓
Offline compatibility / branch validation
        ↓
New System Behavior subject evidence
        ↓
R2 + R3 + R4 synchronous extraction
        ├── R5 causal manipulations
        ├── R6 recovery / recurrence
        └── R7 system-structure conditions
                ↓
               R8 freeze
                ↓
               R9 robustness / replication
```

任何新的真实模型调用仍需单独冻结 provider/model/run count/call cap/spending ceiling/currency，并通过对应 paid authorization gate。