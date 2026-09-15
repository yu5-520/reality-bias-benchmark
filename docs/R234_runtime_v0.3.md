# R2–R4 共享结构试验：v0.3 运行说明

本版本落实 R Plan v2.0：一份主体轨迹供事件、关系和闭环三层异步审计。三层无需分别跑主体，审计失败不触发重跑。当前主体运行条件为 **Arena v0.3.2**。

## 操作入口

- `R2-R4 Shared Structure Smoke`：用于 1–5 条有明确 launch 记录的电商小批次；当前只在 launch 文件变化或手动 dispatch 时运行。最多 32 轮，不调用 evaluator。每次均产生独立 Actions artifact。
- `R2 Free-Agent Arena Subject Run`：默认使用 `arena/config/arena_v0.3.json`；先准备，再按已有 `CALL_REAL_API` 选项运行所选领域和次数。
- `R2 Free-Agent Arena Offline Validation`：旧回归及四领域合成工程验证。合成数据明确不是研究样本。

## 运行与记录

方案 FINAL 与 episode 结束分离。队列中还有消息就继续协作；没有待处理消息时自然结束。相同参与者的待唤醒槽位合并，但消息、调用次数和调用 ID 完整保留。不会因重复、疑似偏差或出现通信回路而自动终止。

达到轮次、调用或队列上限记录 `BUDGET_CENSORED`，保留剩余任务。它既不是任务成功，也不是故障，也不能外推为“不会收敛”。没有 FINAL 的自然停滞记录 `RUN_INCOMPLETE`。provider/解析失败记录 `RUN_FAILED` 并保留数据。

v0.3.2 对 subject JSON 采用更严格的序列化契约；模型配置 v0.2.1 最多允许一次额外的同请求 JSON 格式恢复。所有失败响应、retry 次数以及聚合 token/延迟都保留。格式恢复不是 evaluator，也不能因为结果不符合研究预期而触发。

`subject_traces.jsonl.journals/` 保存逐轮输入、响应、动作事件和消息/执行账本检查点；每条记录带时间、前序哈希，写入后同步落盘。主体文件一旦存在，runner 拒绝覆盖。硬终止可能只留下日志前缀，不能将其冒充完整轨迹。

## 同一批次三个审计入口

| 文件 | 用途 |
| --- | --- |
| review_packets.jsonl | 原有 R2 单事件材料 |
| review_evidence_index.jsonl | 原始调用、事件、消息和调用账本引用 |
| structural_views.jsonl | R3 消息读取/状态版本可见性关系；R4 角色投影返回路径与定稿修改序列 |
| objective_stats.jsonl | 实际参与、执行、调用、剩余工作和截断状态 |
| integrity.json | 派生文件完整性；批次元数据另绑定主体和日志哈希 |

所有语义判断保持 `NOT_ADJUDICATED`。反馈候选只表示角色投影存在返回路径，不能直接称为权限穿透、自增强或因果闭环。无候选也不是已经审定无闭环；状态介导的复杂闭环需要读取完整证据。

异步导入：

```bash
python -m arena.layer_reviews --batch-dir results/subject_evidence --records my_reviews.jsonl --outdir results/reviews
```

每条记录包括 `review_id`、`layer`（R2/R3/R4）、`evidence_batch_hash`、`reviewer`、`rubric_version`、`prompt_version`、`created_at`、`evidence_refs`、`finding`（SUPPORTED/NOT_SUPPORTED/UNCERTAIN）、`rationale`、`uncertainties` 和 `record_kind`。模型评审者同时记录 model/config_hash。复核或裁决引用 parent_review_ids，独立意见不得继承其他意见。该导入只保存审计意见，不自动汇总为已审结论或多数票真值。

## 当前运行边界

v0.3.2 Format Verify 005 在 32 次 subject model call 中全部首轮得到可解析 JSON，格式 retry 实际使用 0 次；但 episode 在第 32 轮仍有待处理队列，因此结果是 `BUDGET_CENSORED`。这说明序列化阻塞暂时解除，同时也证明 32 轮是实际会生效的观察边界。

不能为了把该轨迹“跑完整”而事后修改它。若未来设置 64/96 轮窗口，应作为独立 observation condition 绑定新配置。R5 控制后继续运行、R6 ALR 恢复，以及多模型语义评审仍需独立实验或后续实现。
