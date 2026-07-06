# P3-05I 正式坐席工作流阶段卡

## Engineering Control Card

| 项目 | 内容 |
| --- | --- |
| 阶段 | P3-05I 标准运营版正式坐席工作流 |
| 目标 | 在 P3-05H 会话收件箱基础上，把“接管”推进为可审计的坐席动作流：领取、释放、转派、解决、待跟进、等待客户、重开和备注 |
| 产品边界 | 本阶段是商户中控台的坐席处理能力，不是企业微信、公众号、抖音、小红书或电商平台真实自动回复上线 |
| 安全边界 | 不打开真实外发；不写入真实平台密钥；不调用真实客户数据；演示模式下所有坐席动作按钮保持禁用 |
| 当前状态 | 后端动作接口、动作状态机、审计事件、前端动作入口、测试和本地预览已完成；转派选择器、备注弹窗、完整 RBAC、完整工单/SLA 仍未完成 |

## 本阶段完成内容

### 后端动作接口

新增正式坐席动作接口：

```text
POST /api/conversations/{conversation_id}/workflow-actions
```

请求需要 Bearer Token，并沿用租户隔离校验。当前支持的动作：

| 动作 | action | 当前效果 | 审计事件 |
| --- | --- | --- | --- |
| 领取 | `claim` | 未分配会话分配给当前坐席；状态进入 `handoff` | `conversation.workflow.claim` |
| 释放 | `release` | 清空坐席和团队；状态回到 `waiting_human` | `conversation.workflow.release` |
| 转派 | `transfer` | 指定目标坐席或团队；状态进入 `handoff` | `conversation.workflow.transfer` |
| 解决 | `resolve` | 会话状态标记为 `resolved` | `conversation.workflow.resolve` |
| 待跟进 | `follow_up` | 会话状态标记为 `follow_up`；未分配时归属当前坐席 | `conversation.workflow.follow_up` |
| 等客户 | `wait_customer` | 会话状态标记为 `waiting_customer`；未分配时归属当前坐席 | `conversation.workflow.wait_customer` |
| 重开 | `reopen` | 已解决会话重新进入 `handoff` | `conversation.workflow.reopen` |
| 备注 | `note` | 不改变会话状态，只写处理备注 | `conversation.workflow.note` |

### 动作规则

- 没有登录令牌时返回 401。
- 跨租户访问返回 404。
- 领取已分配给其他坐席的会话返回 409，避免两个坐席抢同一条会话。
- 转派必须提供目标坐席或目标团队，否则返回 422。
- 备注必须有非空内容，否则返回 422。
- 转派目标坐席和团队必须属于同一租户。
- 每次动作都会写入 `ConversationEvent`，记录动作前状态、动作后状态、目标坐席、目标团队和备注。

### 前端会话收件箱

会话收件箱从单一“接管”按钮升级为坐席动作区：

- `领取`
- `等客户`
- `解决`
- `释放`
- `查看审核`

前端当前行为：

- 正式登录后调用后端 `workflow-actions` 接口。
- 操作成功后自动刷新当前会话收件箱分页。
- 演示模式没有登录令牌，所以动作按钮保持禁用，避免误导为真实外发或真实业务处理已经打开。
- 已解决会话后续会显示重开能力，当前演示列表主要覆盖待处理会话。

### 审计链

本阶段的关键进展不是多几个按钮，而是把坐席处理动作写入后端审计链：

- 谁领取了会话。
- 谁释放了会话。
- 谁把会话转给了谁。
- 谁把会话标记为已解决、待跟进或等待客户。
- 哪次动作附带了备注。
- 动作前后的会话状态是什么。

这为后续主管复盘、客户投诉追踪、服务质量审计和 SLA 归因打基础。

## 已验证内容

### 后端动作流测试

```text
/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/backend/.venv/bin/pytest tests/test_conversation_inbox_api.py -q
```

结果：

```text
3 passed
```

覆盖：

- 未登录坐席动作返回 401。
- 领取会话后归属当前坐席并进入 `handoff`。
- 空备注返回 422。
- 备注动作写入审计事件。
- 其他坐席领取已归属会话返回 409。
- 转派到其他坐席。
- 标记等待客户。
- 标记已解决。
- 释放会话。
- 重开会话。
- 转派没有目标返回 422。
- 审计事件包含 claim、note、transfer、wait_customer、resolve、release、reopen。

### 后端相关回归

```text
/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/backend/.venv/bin/pytest tests/test_conversation_inbox_api.py tests/test_foundation_api.py tests/test_workflows_api.py tests/test_outbox_api.py tests/test_channel_connectors_api.py tests/test_delivery_failure_reviews_api.py -q
```

结果：

```text
24 passed
```

### 前端构建

```text
npm run build
```

结果：

```text
tsc && vite build
build succeeded
```

### 本地浏览器预览

已在 Chrome 打开：

```text
http://127.0.0.1:5173/#conversations
```

已目检：

- 左侧导航阶段标识为 `P3-05I`。
- 会话收件箱可见。
- 演示样例总量 18。
- 第 1 页显示第 1-8 条。
- 每条会话展示坐席动作入口：领取、等客户、解决、释放、查看审核。
- 演示模式下坐席动作按钮为禁用态。
- 页面明确显示真实外发关闭。

## 当前不能承诺

- 不能承诺已经接通企业微信、公众号、抖音、小红书、淘宝、京东或拼多多的真实自动回复。
- 不能承诺真实平台消息已经进入中控台；当前浏览器验收使用演示样例数据。
- 不能承诺外部发送已经打开；真实外发仍受渠道授权、可信 IP、公网 HTTPS、白名单和人工审核控制。
- 不能承诺完整 RBAC 已完成；当前仍需要补坐席、主管、管理员的细粒度权限矩阵。
- 不能承诺完整工单系统已完成；当前只有会话状态流，没有独立工单编号、工单类型、工单升级和 SLA 归因。
- 不能承诺完整 SLA 系统已完成；当前仍是轻量等待时间判断，不含工作日、班次、节假日、暂停计时和升级通知。
- 不能承诺完整备注体验已完成；后端已有 `note` 动作，前端还没有正式备注弹窗。
- 不能承诺完整转派体验已完成；后端已有 `transfer` 动作，前端还没有坐席/团队选择器。

## 对产品成熟度的真实评价

P3-05I 完成后，标准运营版中控台已经从“能看会话”推进到“能处理会话的核心状态流”。这一步解决的是客服中台最基础的操作闭环：

```text
客户消息进入会话池 -> 坐席领取 -> 坐席处理 -> 等客户/解决/释放/重开 -> 审计留痕
```

但它还不是成熟商用全量版本。成熟商用还需要继续完成：

- 联系人画像和线索状态。
- 坐席/团队/主管权限。
- 工单和 SLA。
- 知识缺口从会话沉淀回知识库。
- 真实渠道官方回调验证。
- 出站白名单发送 smoke。
- 生产部署、监控、备份、诊断包和远程维护 SOP。

## 下一步建议

### P3-05J：联系人与线索画像

目标是让坐席不只看到消息，还能看到客户背景：

- 联系人详情页。
- 渠道身份绑定。
- 最近会话历史。
- 客户标签。
- 意向等级。
- 跟进状态。
- 留资字段。
- 销售移交状态。

### P3-05K：知识缺口闭环

目标是把人工处理过程反哺知识库：

- 从会话中标记知识缺口。
- 自动生成待补知识任务。
- 记录负责人、状态、截止时间和来源会话。
- 知识审核后重新索引。
- 用评测题集验证缺口是否被修复。

### P3-05L：真实渠道入站 smoke

如果企业微信公网 HTTPS、可信 IP、Token、EncodingAESKey 和后台权限具备，优先做：

- 企业微信 URL 验证。
- 企业微信安全模式 XML 入站。
- 解密后写入可信入站消息。
- 生成 AI 草稿。
- 进入人工审核。
- 不真实外发。

