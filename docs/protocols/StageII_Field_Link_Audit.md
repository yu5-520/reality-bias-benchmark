# Stage II 活动字段检索与链接整理

本次范围是现有外挂修复链路的字段连接；未引入统一字段注册表、注册服务或通用适配框架。原始 MCP、主体任务、干预权限和冻结实验均不改动。基线提交为 `6284b11f520ed8ad359c3d98f6f4913a7fa97ecc`。

## 字段来源与去向

| 字段组 | 生产位置 | 消费位置与约束 |
|---|---|---|
| `kind/name/arguments` | connected_planning.TOOL_CONTRACTS 与模型回复 | CONNECTED_TOOLS 从既有说明派生，tool() 直接校验并调用；活动入口不再借用旧 TOOLS 参数表 |
| `ref/version_handle/checkpoint_hash/content_sha256/native_sequence/boundary/is_parent` | source_navigation.describe() 从已冻结版本记录投影 | prefix_index、versions、read_version.source_version 及证据进度使用相同描述；保留各自版本身份 |
| `parent_checkpoint_hash` | 冻结上下文与规划绑定 | 标明本轮当前父节点，不能替代 source_version.checkpoint_hash |
| `source_locator` | 原始 archive/member/member_sha256/json_pointer | 读记录与版本精确关联；不按相同内容哈希猜测时间 |
| `read_id/text_hash/text_length` | planning_session._read() | span/witness 的输入；读取不自动生成引用资格 |
| `witness_id/read_id/start/end/span_hash` | planning_session.witness()，span 委托它生成 | diagnoses.witness_ids 与 no-action.witness_ids 只能引用已选择的片段；返回与进度通过 read_id 链接原版本 |
| `field_path` | 宿主 task_capabilities.message_fields | message_source、message、授权编译器使用同一路径；进度明确完整当前消息证据要求 |
| `before_value_hash` | 当前消息 read.text_hash | 消息替换前值校验 |
| `before_span_hash/replacement/start/end` | 选中原句的 witness.span_hash，加模型提出的替换内容 | native_message 校验原句和局部替换；不自动扩展到整条消息 |
| `value` | 宿主编译器依据冻结当前消息、选中 span、replacement 与固定 attribution 派生；模型不再提交 | native_message 再验证完整目标值，保留选中 span 外的原文 |
| `verification_tasks/execution_order` | 已有宿主验证能力 + 模型动作引用 | 输出模板改为真实数组结构，与 compile() 的数组/顺序要求一致；不把逗号字符串转换成数组 |

## 本次消除的断点

1. 8 个活动工具的参数名字原来在说明和名单中重复维护；现在只有既有 TOOL_CONTRACTS 为活动参数名单供值。历史离线工具表仅服务冻结回放。
2. v2 导航使用平行的 checkpoint_indices/version_handles 数组，读取与进度省略显式版本时间。v3 直接把句柄和时间放在同条记录中，所有 192 个文件版本成员均保留；活动入口删除 v2 表达，没有双接口兼容分支。
3. read_version 返回 source_version，证据结果及后续进度通过原始来源定位保持这一连接。未知/非文件来源显示 null，并保留原始 source_locator；不为它推测文件版本。
4. 当前消息的完整证据片段要求原来主要存在于编译器，现由 pending_message_sources 明确呈现，并在请求中说明。生成证据仍须显式调用，错误 FINAL 仍立即结束。
5. execution_order 和 verification_tasks 的输出模板由文字描述改为数组示例，与实际消费者一致。
6. 单次 field-link 试验 `37300920836` 已正确使用合法 witness 并区分 TASK_START 与 parent，但最终同时提交 replacement 与完整 value，触发 `UNRELATED_MESSAGE_TEXT_DRIFT`。活动接口现只接受局部 replacement；完整 value 由宿主派生，不增加新字段或兼容层。每个 diagnosis 的 source/destination witness 要求也直接暴露给模型。

## 验证及限制

- 203 项 route_repair 测试通过；连接层测试覆盖同内容不同时间不合并、导航/读取/证据进度保持同一版本、错误证据引用仍拒绝。
- 第二、第三轮冻结证据校验通过；第三轮非盲前缀审查来源成功回放，均为零新增模型调用。
- 第五轮四个原查询离线成功回放，仍在 CURRENT_MESSAGE_WITNESS_REQUIRED 拒绝原方案；没有修改原输出、补造 witness 或将失败转为成功。
- 第四轮原 ZIP 回放与官方 MCP 脚本集成沿用现有 CI，在新提交上运行；不触发任何新付费试验。
- 当前完整导航 JSON 为 108265 字节（ensure_ascii=False、sort_keys=True 默认 JSON 分隔符）。显式关联时间增加了元数据体积；不宣称节省 token。预算和模型参数不变。
- 当前/历史的字段关联已明确，不等于语义判定必然正确。TASK_START 不能单独证明当前不存在某功能；当前功能存在也不能证明历史从未修改。不得以字段一致性认证修复有效。

本次到此收口：静态检索、直接链接、冻结回放，以及活动生产端/消费端的单一字段职责。不增加注册层，也不自动登记新试验。

## e55d5c3 检索计数（整理基线）

范围：活动规划链路及其直接调用的 8 个模块。下表按 AST 中完全匹配字段名的字符串常量计数，包含读写、校验和说明，不代表独立字段定义数量；历史证据不参与计数。

| 字段 | 出现次数 | 涉及模块数 |
|---|---:|---:|
| `kind` | 33 | 5 |
| `name` | 12 | 3 |
| `arguments` | 17 | 3 |
| `ref` | 37 | 7 |
| `version_handle` | 4 | 2 |
| `checkpoint_hash` | 23 | 6 |
| `parent_checkpoint_hash` | 17 | 8 |
| `boundary` | 7 | 3 |
| `native_sequence` | 3 | 3 |
| `source_locator` | 19 | 6 |
| `read_id` | 13 | 5 |
| `witness_id` | 3 | 2 |
| `witness_ids` | 8 | 3 |
| `text_hash` | 4 | 2 |
| `span_hash` | 2 | 2 |
| `content_sha256` | 5 | 2 |
| `field_path` | 12 | 5 |
| `before_value_hash` | 3 | 2 |
| `before_span_hash` | 2 | 2 |
| `start` | 14 | 6 |
| `end` | 14 | 6 |
| `replacement` | 4 | 2 |
| `value` | 15 | 4 |
| `verification_tasks` | 7 | 3 |
| `execution_order` | 4 | 3 |
