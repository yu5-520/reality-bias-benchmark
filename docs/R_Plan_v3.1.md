# Reality Bias 研究总规划

版本：R Plan v3.1  
日期：2026-09-16  
状态：CANONICAL / STRUCTURAL-MECHANISM PROGRAM RESTORED

## 1. 版本决策

R Plan v3.1 保留 v3.0 已冻结的 C/P/R v2 边界定义、Machine Structural Observer、R2-R4 结构索引方法、冻结证据与异步审计机制，但纠正 v3.0 之后逐步形成的研究依赖关系。

v3.0、`docs/R234_v2_current_gate.md`、Reviewer-v2、DeepSeek/Qwen 评审、预飞、缓存与推理遥测记录继续作为 append-only 历史材料保留，不回写、不删除、不伪装为新的同期事实。v3.1 修改的是前向研究 DAG 与论文证据层级，而不是历史 subject evidence 或历史 reviewer 输出。

本版恢复两条早期已接受原则：

> **语义评审是冻结主体证据之后的独立、可追加操作；评审失败不得触发主体重跑。**

> **Gate 约束可以提出多强的主张，而不是决定是否允许继续观察现象。**

新的总原则为：

> **R2-R8 研究被观察系统本身的结构、传播、反馈、控制、恢复与边界；R9 研究外部评审和外部复现对这些结果的稳健性。R9 不反向成为 R2-R8 的完成门槛。**

## 2. 第一篇论文的研究范围

第一篇论文定位为：**结构性存在与机制研究（structural existence / mechanism study）**，而不是穷举式工业 Multi-Agent benchmark。

当前阶段有意采用较小、角色职责明确的 Multi-Agent 环境，以隔离交互机制，减少异构模型、复杂工具生态、长期记忆、动态编排、MCP/A2A、外部环境和大规模算力带来的混杂因素。

因此本研究当前优先级是：

`理论定义 → 最小可复现实验环境 → 自然结构出现 → 传播 → 反馈 → 因果切断 → 恢复 → 边界条件 → 复现冻结`

而不是：

`尽可能多旗舰模型 × 尽可能多 Reviewer × 尽可能多 Agent 框架 × 尽可能多工具生态 × 尽可能多重复次数`

大规模跨主体模型、异构 Agent、MCP/A2A、复杂工具/记忆/RAG、拓扑和 Agent 数量扩展属于后续外部效度与实验室 replication phase。

## 3. 三层研究对象分离

### 3.1 Structural Emergence — 主体结构层

回答：冻结主体系统中是否自然出现可追踪的结构候选？

包括：

- epistemic-status jump candidate；
- provenance attenuation/loss candidate；
- goal-scope / goal-focus change candidate；
- downstream inheritance / propagation path；
- reopen / revision / feedback return；
- structural feedback loop / black-hole candidate；
- 资源、调用、Agent、状态影响范围等动力学变化。

这些是 subject trace 与 deterministic structural observer 可以支持的对象。

### 3.2 Semantic Identification — 后置语义层

回答：已经冻结的结构应如何解释或命名？

Reviewer 可以判断 C/P/R realization、authorization、semantic adoption、decision effect、laundering、normalization 等，但 Reviewer 不创造已经发生的历史轨迹。

因此：

> Reviewer 标签变化可以改变对固定结构的操作性分类，不得被表述为修改了原始 event sequence、state transition、propagation path 或 feedback topology。

### 3.3 Measurement Sensitivity — 测量装置层

回答：换 rubric、prompt、packet、reviewer model family 或 human reviewer 后，语义分类边界有多稳定？

Reviewer v1→v2、DeepSeek→Qwen、未来 human IRR 等主要属于这一层。该层对论文主张强度有影响，但语义分歧本身不构成上游 evidence-integrity defect。

只有发现哈希不一致、源证据损坏、 deterministic extraction bug、错误绑定或其他真实证据完整性问题时，才触发上游审计/修正流程。

## 4. R0-R9 新职责

| 编号 | v3.1 职责 | 主要问题 | 主要产物 |
| --- | --- | --- | --- |
| R0 | Theory Contract / Boundary Definition | C/P/R 与 Authority 到底是什么、什么不是 | 理论合同、正常反例、版本治理 |
| R1 | Theory & Measurement Stress Test | 粗糙定义能否被反例击穿 | 边界压力测试、可证伪条件 |
| R2 | Structural Emergence / Event Layer | 哪些候选边界变化在主体轨迹中自然出现 | event/jump structural index + 局部后置语义意见 |
| R3 | Propagation / Lineage / Penetration Structure | 候选结构如何沿消息、状态、调用与目标血缘传播 | lineage/range graph、adoption/effect 边界 |
| R4 | Feedback / Loop / Laundering / Black-Hole Dynamics | 候选结构如何返回、维持、再生成、扩大或被纠正 | neutral loop windows、dynamics evidence、K probes |
| R5 | Causal Interruption / Control | 切断指定依赖或权限后机制是否减弱 | intervention contrasts |
| R6 | Recovery / Recurrence | 修正后是否恢复、复发、重新洗白或付出额外成本 | recovery/recurrence evidence |
| R7 | Boundary Conditions / Limited Generalization | 结构在可承受的任务、领域、角色池、权限或简单拓扑变化下如何改变 | scoped boundary-condition evidence |
| R8 | Reproducibility Freeze | 第一篇主体证据能否被独立重建和审计 | trace/config/code/hash/analysis freeze |
| R9 | Supplementary Robustness / External Replication | 不同 Reviewer、模型家族和未来实验室复制如何影响解释与外部效度 | supplemental audits、replication protocol、limitations |

原 v3.0 的 `Paper Claim Mapping` 不再占用 R 编号，移为独立的 **Manuscript Claim–Evidence Matrix**，属于论文装配与主张治理，而不是一个新的实验层。

## 5. R2-R4：同一冻结轨迹的三个结构视角

R2、R3、R4 不是必须顺序运行的三套主体实验。三者继续共享同一条主体轨迹，执行时同步记录，之后异步审计。

### R2 — Structural Emergence / Event Layer

R2 首先回答结构是否出现，而不是先要求 Reviewer 宣布 C/P/R 真值。

机器记录 state/status/source/goal/final/invocation 等实际变化并输出 `*_CANDIDATE`。局部 Reviewer 可以追加 C/P/R realization 意见，但 `NOT_ADJUDICATED`、reviewer disagreement 或 reviewer failure 都不得改写结构事实。

### R3 — Propagation / Lineage

R3 从结构候选展开消息、状态、调用、目标与字段血缘。

继续严格区分：

`visible → read → referenced → semantically adopted → decision-effective`

机器负责前部结构事实；后部语义依赖可以异步审计。尚未完成多 Reviewer 共识不阻止 R3/R4 继续观察和记录。

### R4 — Feedback / Dynamics

R4 的 structural feedback counter 保持语义盲。循环、重开、重复、返工和资源增长首先作为动力学结构记录，不自动等同 Reality Bias。

Base 固定窗口负责“测得准”；有限 K 负责“看得远”。K=2/K=4 是 R4 内部的上限观察条件，不属于 R9 跨模型 reviewer replication。

R4 的付费主体运行仍要求：

- runtime / evidence integrity ready；
- K counter 定义冻结；
- subject configuration 冻结；
- 明确预算上限与付费授权。

**不同 model family 的 Reviewer 未完成，不再构成启动 K=2 的研究门槛。**

K=4 是否值得继续，可以由预先冻结的 R4 内部 persistence/expansion/amplification gate 和成本约束决定；该 gate 不要求跨模型 Reviewer 一致。

## 6. R5-R8：主体研究主线

### R5 — Causal Interruption

只有通过真实干预切断指定信息依赖、Authority route、feedback return 或其他候选机制，并观察结构变化，才允许逐步把“相关结构”升级为因果机制证据。

### R6 — Recovery / Recurrence

比较完整重跑、检查点恢复、局部修正等恢复路径，记录恢复速度、复发、再生成、重新洗白和成本。历史静态 replay 不能替代需要新行为证据的恢复实验。

### R7 — Boundary Conditions / Limited Generalization

R7 服务于第一篇论文可承受的边界条件，而非算力竞争。

可以研究：

- 不同任务类型或领域；
- 不同角色池/专业覆盖；
- 不同权限结构；
- 简单拓扑变化；
- 有限主体模型替换或重复样本。

不把旗舰模型全覆盖、复杂 MCP/A2A 生态、异构 Agent 工具系统或大规模 model × topology × domain 矩阵作为当前论文完成条件。

### R8 — Reproducibility Freeze

R8 冻结第一篇论文主体研究所需的：

- subject prompts / role definitions / tasks；
- model/config/code commit；
- raw trace / journal / state history；
- structural indices；
- intervention/recovery conditions；
- deterministic analysis；
- semantic review versions（若有）；
- 文件与 evidence hashes；
- claim boundaries 与缺失字段声明。

R8 完成后，第一篇主体证据应能够在不依赖 R9 成功与否的情况下形成独立闭环。

## 7. R9：补充稳健性与外部复制

R9 只读取已经冻结的 R2-R8 对象，承担补充审计与外部效度扩展。

当前已有 Reviewer-v2、DeepSeek full pass、independent blind bundle、Qwen transport/runner/preflight/cache/reasoning telemetry 等工作，统一保留并重新归类为 **R9 infrastructure / supplementary measurement material**。

R9 可以包括：

- same-model contract sensitivity；
- cross-model-family semantic review；
- human inter-rater review；
- reviewer disagreement taxonomy；
- future flagship subject-model replication；
- heterogeneous Agent replication；
- MCP/A2A/tools/memory/RAG replication；
- larger topology / agent-count / domain / repeat matrices；
- external laboratory reproduction of the entire Agent environment。

R9 的状态允许为：`COMPLETE`、`PARTIAL`、`DEFERRED_TO_EXTERNAL_REPLICATION`。

原则：

> **R9 可以增强、限定或暴露 R2-R8 主张的局限，但单纯的语义分歧、Reviewer 失败或尚未运行，不得反向改写冻结主体证据，也不得阻塞结构研究主线。**

## 8. Semantic Non-Contamination / Temporal Separation

“自然出现”主张必须依赖主体层与评审层的时间分离，而不是依赖多个 Reviewer 投票一致。

需要保留/审计的因果时间链为：

`subject prompts/roles/tasks fixed → subject run → raw trajectories frozen → structural indices derived → reviewer protocols/versions applied later`

主体 prompts、角色定义、任务说明和 RAG/context 不得向 subject Agents 暴露 C/P/R 标签、期望映射、Reviewer 结论或要求其制造特定 Reality Bias 结构。

如果上游确有 designed pressure（例如 FINAL/late-event 结构提供 retrospective opportunity），必须如实声明；“未暴露语义分类”不等于“实验环境没有设计压力”。

因此第一篇可支持的更谨慎表述是：

> 在未向主体 Agent 暴露 C/P/R 语义分类体系的自由运行条件下，冻结轨迹中出现了可重复定位和追踪的候选结构；后置 Reviewer 的协议变化影响这些固定结构的语义分类，而不改变其历史发生顺序。

## 9. Human-AI 扩展假设边界

本论文主体实验仍以 Multi-Agent 系统为研究载体，不把人机协作案例作为 R2-R8 实验证据。

但 Perfection-like goal-scope / goal-focus drift 在理论上不必是 Multi-Agent 专属。迭代 Human-AI 协作中可能出现：

`locally reasonable suggestion → local human authorization → new premise → further locally reasonable expansion → cumulative global drift`

即：**局部授权不必然等于全局目标忠实。**

当前只把这一点作为 discussion / future-work hypothesis。仓库中的研究规划漂移案例可以作为非实验性的 provenance-backed reflexive note，不进入 C/P/R 统计，不证明跨场景泛化。

## 10. 新的依赖 DAG

```text
R0 / R1
   ↓
Frozen Subject Evidence
   ├── R2 Structural Emergence
   ├── R3 Propagation / Lineage
   └── R4 Feedback Dynamics
            ↓
           R5 Causal Interruption
            ↓
           R6 Recovery
            ↓
           R7 Boundary Conditions
            ↓
           R8 Reproducibility Freeze
            ↓
      Main-paper evidence
            │
            ├── Manuscript Claim–Evidence Matrix
            │
            └── R9 Supplementary Robustness / External Replication
```

不存在以下依赖：

`R2-R4 → DeepSeek Reviewer → Qwen Reviewer → reviewer consensus → permission to continue R5-R8`

## 11. 当前执行方向

v3.1 生效后的优先顺序：

1. 冻结本次 dependency correction Change Note；
2. 保留所有历史 v3.0 / Reviewer-v2 / Qwen 记录；
3. 将跨模型 Reviewer 工作从主体 Gate 降为 R9 backlog / supplementary；
4. 审计 subject-layer semantic non-contamination 与时间顺序证据；
5. 基于冻结 subject evidence 继续整理 R2-R4 structural observations；
6. 按资源和科学问题推进 R4 K=2、R5、R6、R7；
7. 完成 R8 reproducibility freeze；
8. R9 在当前资源范围内做有限补充，或冻结 replication protocol 留待实验室合作。

任何真实付费 API 调用仍必须单独取得明确授权和费用上限。R Plan 更新本身不授权任何 provider dispatch。
