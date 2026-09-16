# Reality Bias System Behavior Measurement Plan v4

版本：System Behavior Measurement v4  
日期：2026-09-16  
状态：FORWARD CANDIDATE / BEHAVIOR-FIRST MEASUREMENT  
依赖：`docs/R_Plan_v4.0.md`、`theory/theory_contract_v0.4.md`  
历史兼容：`docs/trajectory_dynamics_measurement_plan_v3.md` 与 `docs/R234_measurement_plan_v2.md` 保持历史身份。

## 1. 目标

Measurement v4 把 v3 的 trajectory dynamics 扩展为 system-behavior measurement hierarchy。

核心层级：

```text
SystemTrajectory
  └── Node / Boundary
       └── BehaviorEvent
             └── StateTransition
                   ├── Jump candidate
                   ├── lineage / propagation
                   ├── operational penetration candidate
                   ├── inertia candidate
                   └── retrospective / recovery window
```

原则：

> **行为先记录，结构先冻结，语义后判断。**

## 2. Experimental / Analysis Unit

一个完整 `RUN_COMPLETE`、有效 branch continuation 或明确 censored/failed trajectory 是系统级实验记录单位。

每条 trajectory 必须绑定：

- run / branch identity；
- parent identity where applicable；
- domain/task identity；
- Agent pool/topology identity；
- model/config/provider identity；
- code commit；
- protocol/measurement version；
- evidence batch / trace hash；
- termination / censoring status。

系统级指标不得把不同 source version 静默池化。

## 3. Measurement Location

Node / Boundary 是测量位置，不是 Bias 标签。

前向 boundary families：

- `AGENT_TURN`；
- `MESSAGE_HANDOFF`；
- `SHARED_STATE`；
- `CONTEXT_RAG_HANDOFF`；
- `INVOCATION`；
- `COMMIT_GATE`；
- `FINAL_REOPEN`；
- `AUTHORITY_CONVERSION`；
- `RECOVERY_CHECKPOINT`。

具体注册见 `configs/measurement_boundary_registry_v0.1.json`。

## 4. Behavior Event

Behavior Event 是 v4 的最小主证据单位。

最小字段：

- `behavior_event_id`；
- `trajectory_id`；
- `event_index`；
- `turn`；
- `node_id`；
- `boundary_id`；
- `actor`；
- `action_type`；
- `target_ref`；
- `realization_status = PROPOSAL | REALIZED | BLOCKED | FAILED`；
- `state_before_hash`；
- `state_after_hash`；
- `source_refs[]`；
- `parent_event_refs[]`；
- `authority_before[] / authority_after[]` where applicable。

原始 model input/output 继续保留在 frozen source evidence 中，但不强迫 Behavior Event 重复复制完整文本。

## 5. State Transition

结构测量优先比较：

`S_t → S_t+1`

机器可直接确认：

- state hash changed / unchanged；
- specific structured field changed；
- message/invocation lifecycle；
- queue/inbox changes；
- shared-state write；
- final/history mutation；
- realized operational action。

需要语义理解的字段必须保持 candidate / NOT_ADJUDICATED 状态。

## 6. Jump Candidate Pipeline

前向 detector 采用：

`Behavior Event → structured transition diff → preregistered candidate rule → Jump candidate`

候选族包括：

- epistemic status/provenance；
- goal scope/focus；
- invocation/task graph；
- settled/final/historical state；
- authority-bearing transition；
- other preregistered dimensions。

Jump truth 与 C/P semantic truth 不由 detector 自动宣布。

## 7. Tension / Escape measurement boundary

Measurement v4 不直接输出“tension score”或“escape probability”。

可操纵变量来自 `configs/experimental_variable_registry_v0.1.json`。

对于前置操纵 X，可报告：

- condition identity；
- level/value；
- valid replicate count；
- Jump-positive branch count under frozen detector；
- `h_hat = jump_positive / valid`；
- failures/censoring separately。

任何 tension 解释属于理论层，不能把 `h_hat` 直接改名为 tension。

## 8. R2 / R3 / R4 同步派生

同一 frozen trajectory 允许同步产生：

### R2

- first Jump candidate；
- Jump count/type/location；
- behavior/action distribution around Jump。

### R3

- first read / reference / commit refs；
- descendant lineage；
- affected agents；
- operational-boundary crossings；
- persistence length；
- provenance retention/loss candidate。

### R4

- prior deviation anchor；
- challenge/reopen/correction opportunity；
- retrospective outcome window；
- semantic outcome deferred to reviewer where required。

R2/R3/R4 不是三次主体运行。

## 9. Multi-position intervention measurement

### PRE

输入：`ANTECEDENT_ANCHOR` + one `PRE` variable manipulation。

主要输出：Jump incidence/location/type。

### MID

输入：`TRANSITION_ANCHOR` or `PENETRATION_ANCHOR` + one `MID` manipulation。

主要输出：propagation / penetration / descendants / inertia。

### POST

输入：`PENETRATION_ANCHOR` or `CHALLENGE_RECOVERY_ANCHOR` + one `POST` manipulation。

主要输出：persistence / retrospective outcome / recovery。

## 10. Anchor classes

Forward anchor classes：

- `ANTECEDENT_ANCHOR`；
- `TRANSITION_ANCHOR`；
- `PENETRATION_ANCHOR`；
- `CHALLENGE_RECOVERY_ANCHOR`。

通用 branchability 要求：

- source snapshot truly recorded；
- parent identity/hash verifiable；
- runtime state restorable；
- nonterminal where continuation required；
- pending continuation work where current Arena scheduler requires it；
- provider hidden state not fabricated；
- anchor selection independent of unseen branch outcomes。

## 11. Variable registry

每个实验 manipulation 必须绑定 registry entry：

- variable/version/hash；
- stage；
- target boundary family；
- control level；
- manipulation level；
- held constants；
- expected observable family；
- source requirements。

未注册临时变量可用于 exploratory work，但不得作为 confirmatory intervention 悄悄进入结果。

## 12. Proposal / Realization separation

所有可执行行为优先分开记录：

- `PROPOSAL`；
- `REALIZED`；
- `BLOCKED`；
- `FAILED`。

一个 proposal Jump 可以存在而不改变 operational state。

因此必须允许：

`proposal Jump ≈ unchanged`

同时：

`realized descendants / penetration / persistence ↓`

## 13. Semantic review windows

Reviewer 默认只接收与候选 transition 相关的小窗口：

- state before；
- relevant source/evidence refs；
- behavior event；
- state after；
- relevant downstream lineage；
- applicable Authority contract。

完整 trajectory 可作为可追溯附件，但不要求 Reviewer 通过通读整条 reasoning 自行寻找所有 Bias。

## 14. Historical compatibility

- Measurement v3 branch continuation slicing 继续有效；
- parent/start state hash separation继续有效；
- Batch001 可派生的结构量只限 source 中真实记录字段；
- 历史缺失字段必须写 `NOT_RECORDED_IN_SOURCE_VERSION`；
- 历史 CPR 语义结果不被 v4 覆盖；
- v4 新字段不得反向伪造到旧 evidence。

## 15. First-paper measurement scope

第一篇优先冻结并报告：

- Jump candidate/incidence；
- propagation / descendants；
- operational-boundary crossing / penetration criteria；
- post-Jump persistence/inertia；
- one or more narrow MID intervention contrasts；
- recovery contrasts。

Tension direct measurement、全 PRE variable matrix、大规模 model/domain matrix 均可留给后续论文。

## 16. Execution boundary

本计划不授权任何 paid subject / Reviewer API。

真实实验仍需独立冻结 provider、model/config、replicate count、call cap、spending ceiling、currency、code SHA、registry hashes 与 exact authorization phrase。