# AI+RPA 智能客服闭环研究技术方案

版本：v0.1  
日期：2026-07-02  
归属：万法常世 AI 全智能客服系统 / 标准运营版研究线  
状态：研究方案 + 独立 dry-run 骨架；尚未嵌入现有客服中台；不连接真实平台账号。

## 1. 结论

AI+RPA 是非官方多平台客服自动化里最成熟、最容易复刻的工程范式。它成熟的原因不是平台开放程度高，而是它把真人客服的“看界面、读消息、填回复、转人工、打标签”抽象成可编排动作，再把 AI 的“理解、检索、生成、风控”放在动作之前。


本轮已经新增一个独立研究骨架：

```text
standard_ops/research/ai_rpa_closed_loop/
```


## 2. 参考源

| 参考项目 | 可学习点 | 不应照搬点 |
|---|---|---|
| [AIjiaKeFu/AI-Customer-Service](https://github.com/AIjiaKeFu/AI-Customer-Service) | 多平台 AI+RPA 产品形态、知识库、文本/图片、多平台口径、转人工 | AGPL；不能直接闭源商用；平台接入风险需另审 |
| [cs-lazy-tools/ChatGPT-On-CS](https://github.com/cs-lazy-tools/ChatGPT-On-CS) | 电商客服 SaaS 形态、多平台统一管理、知识库、预设回复、多媒体、数据分析 | AGPL；不能直接搬代码；客户可见能力需逐项核验 |
| [tmwgsicp/dify-on-qianniu](https://github.com/tmwgsicp/dify-on-qianniu) | 最小 AI+RPA 闭环：Clicknium 操作千牛、Dify 生成回复、界面元素录制、复杂问题转人工 | 自动发送只能作为研究；正式方案不能承诺平台认可 |
| [mf-yang/pdd-customer-service-sdk](https://github.com/mf-yang/pdd-customer-service-sdk) | Playwright + FastAPI + 多工作台 + 回调机制 + API 包装 | 作者明确仅供学习研究；不进入正式商用主线 |
| [JC0v0/Customer-Agent](https://github.com/JC0v0/Customer-Agent) | 商品知识库 + 客服知识库、Agent 工具、异步队列、重连、转人工 | WebSocket 路线高风险，只能研究架构 |
| [XianyuAutoAgent](https://github.com/shaxiu/XianyuAutoAgent) | 多专家路由、议价专家、上下文管理、轻量客服 Agent | Cookie 路线不能进入正式方案 |
| [xianyu-auto-reply](https://github.com/zhinianboke/xianyu-auto-reply) | 前后端、WebSocket 服务、调度器、Docker、MySQL/Redis 结构 | AGPL；私有通道路线只适合阅读系统结构 |

## 3. 方案边界

### 3.1 本方案允许

- 研究 AI+RPA 的工程架构。
- 使用合成消息跑完整闭环。
- 生成 AI 草稿、转人工判断、知识缺口、dry-run RPA 动作计划。
- 输出审计 JSON，用于未来和客服中台对齐。
- 设计后续可替换的 `RpaAdapter` 接口。

### 3.2 本方案禁止

- 不读取、复用、存储 Cookie、Token、浏览器登录态。
- 不实现私有 WebSocket、私有协议、接口逆向发送。

## 4. 总体闭环

```text
平台界面/研究消息源
        |
        v
RPA 观察层
  - 读取新消息
  - 捕捉页面状态
  - 生成消息快照
        |
        v
消息标准化层
  - channel
  - conversation_id
  - customer_id
  - text
  - attachments
  - raw_observation_ref
        |
        v
AI 决策层
  - 意图识别
  - 知识库检索
  - 商品/订单工具查询
  - 草稿生成
  - 置信度评估
        |
        v
安全门禁层
  - 低置信
  - 投诉/赔付/退款纠纷
  - 医疗/法律/金融等高风险
  - 缺少引用
  - 重复发送/超频
        |
        v
动作编排层
  - 填入回复框
  - 标记转人工
  - 记录知识缺口
  - 截图/证据保存
  - 待发送队列
        |
        v
人工确认 / dry-run 输出 / 后续官方发送器
```

## 5. 模块设计

### 5.1 研究消息源

当前骨架用 `sample_inbound_messages.json` 模拟不同平台消息：

- `qianniu_research`
- `pdd_research`
- `douyin_research`
- `jd_research`

后续如果做真实 RPA 研究，应先接入“人工导入/复制消息”或“只读屏幕观察”，不要直接写真实平台。

### 5.2 RPA 观察层

职责：

- 识别新消息。
- 抽取客户昵称、消息文本、附件、时间、平台。
- 生成观察证据引用。
- 将平台差异消化在 adapter 内部。

当前 dry-run 骨架中对应：

```text
DryRunRpaAdapter.plan_actions()
```

后续可扩展 adapter：

| Adapter | 适用 | 风险 |
|---|---|---|
| ManualImportAdapter | 人工粘贴/导入聊天记录 | 低 |
| ScreenObserverAdapter | OCR/截图只读观察 | 中 |
| DesktopRpaAdapter | 桌面客户端 RPA，填框但不发送 | 中 |
| BrowserRpaAdapter | 浏览器工作台填框 | 中高 |
| PlaywrightResearchAdapter | 实验室浏览器自动化 | 中高 |

### 5.3 消息标准化层

统一消息结构：

```json
{
  "message_id": "demo-001",
  "channel": "qianniu_research",
  "customer_name": "测试客户A",
  "text": "你好，这个订单一般多久发货？",
  "received_at": "2026-07-02T10:00:00+08:00",
  "attachments": [],
  "metadata": {
    "store": "demo-store"
  }
}
```

正式嵌入中台时，需要映射到已有会话模型：

- `tenant_id`
- `channel_id`
- `contact_id`
- `conversation_id`
- `message_id`
- `source_event_id`
- `idempotency_key`
- `raw_observation_ref`

### 5.4 知识库与模型层

当前骨架使用确定性知识卡片，不调用真实模型：

- `shipping_policy`
- `refund_policy`
- `invoice_policy`

后续正式方案应对接现有标准运营版知识体系：

1. 先走高置信 FAQ / 结构化知识卡片。
2. 再走文档 chunk 检索。
3. 再走模型生成。
4. 必须保留引用来源。
5. 缺少引用或置信度低时转人工。

模型策略：

| 场景 | 建议 |
|---|---|
| 高频标准问题 | 规则/FAQ 直接生成，不调大模型 |
| 普通业务咨询 | 百炼/千问默认模型 |
| 复杂售前咨询 | 高阶模型或多轮工具调用 |
| 投诉/退款纠纷 | 只生成草稿，强制人工 |
| 缺知识 | 记录缺口，不自动答 |

### 5.5 安全门禁层

当前骨架 `ResearchGuardrail` 默认把以下情况转人工：

- 低置信。
- 知识缺失。
- 投诉、差评、赔偿、起诉、假货、退款纠纷等风险词。
- 知识卡片标记 `human_required`。

后续可扩展：

- 客户等级。
- 订单金额。
- 售后阶段。
- 同一客户连续追问次数。
- 模型事实性评分。
- 情绪强度。
- 平台回复时限。

### 5.6 动作编排层

当前只允许这些动作：

```text
observe_message
capture_evidence
fill_reply_box
mark_needs_human
record_knowledge_gap
```

所有动作固定：

```json
{
  "external_write": false
}
```

正式嵌入前必须继续禁止：

- `click_send`
- `private_websocket_send`
- `cookie_replay`
- `silent_background_send`

### 5.7 审计层

每次处理都会生成：

```json
{
  "mode": "research_dry_run",
  "external_write_performed": false,
  "private_protocol_used": false,
  "cookie_or_token_reuse_used": false,
  "auto_send_enabled": false
}
```

这层必须保留到未来中台，因为 AI+RPA 最大的工程风险不是“能不能生成回复”，而是“到底有没有真实写出去、谁确认的、依据是什么、出错后能不能复盘”。

## 6. 当前骨架文件

```text
standard_ops/research/ai_rpa_closed_loop/
├── README.md
├── ai_rpa_closed_loop.py
├── run_research_loop.py
└── sample_inbound_messages.json
```

配套验证：

```text
standard_ops/backend/tests/test_ai_rpa_closed_loop_research.py
standard_ops/scripts/check_ai_rpa_closed_loop_research.py
```

输出：

```text
standard_ops/output/ai_rpa_closed_loop_research/latest_run.json
```

## 7. 当前 dry-run 行为

当前 dry-run 已从 4 条样例扩展到 12 条样例，覆盖发货、退款投诉、发票、知识缺口、保修、最低价议价、平台介入、现货、带图售后、安装教程和人身安全疑问。

每条消息除 `draft`、`guardrail` 和 `actions` 外，还会输出 `reply_strategy`：

| 字段 | 说明 |
|---|---|
| `intent` | 问题意图，例如物流、发票、售后风险、知识缺口 |
| `answer_mode` | 回答模式，例如知识草稿、人工接管草稿、知识缺口接管 |
| `delivery_mode` | 动作模式，例如 `fill_draft_only`、`human_takeover`、`record_gap` |
| `customer_visible_policy` | 客户可见回复口径 |
| `next_best_action` | 下一步动作，例如人工审核发送、收集证据、补知识 |
| `quality_signals` | 知识命中、置信度、附件、风控原因等质量信号 |

### 7.1 普通发货问题

输入：

```text
你好，这个订单一般多久发货？
```

行为：

- 命中发货时效知识卡。
- 生成回复草稿。
- 生成 `fill_reply_box` 动作。
- `reply_strategy.delivery_mode=fill_draft_only`。
- `reply_strategy.next_best_action=operator_review_and_send`。

### 7.2 退款投诉问题

输入：

```text
收到后发现质量问题，我要退款，不处理我就投诉。
```

行为：

- 命中退款售后知识卡。
- 识别投诉/退款风险。
- 强制 `needs_human`。
- 生成 `mark_needs_human` 动作。
- 不填入可直接发送动作。
- `reply_strategy.delivery_mode=human_takeover`。
- `reply_strategy.next_best_action=collect_evidence_and_handoff`。

### 7.3 知识缺口问题

输入：

```text
这个产品能不能放在户外长期暴晒？
```

行为：

- 未命中知识。
- 生成谨慎草稿。
- 记录知识缺口。
- 转人工。
- `reply_strategy.delivery_mode=record_gap`。
- `reply_strategy.next_best_action=record_knowledge_gap_and_handoff`。

### 7.4 最低价和承诺类问题

输入：

```text
能不能再便宜一点，给我最低价我马上拍。
```

行为：

- 命中价格优惠知识卡。
- 价格卡标记 `human_required`。
- 不承诺最低价。
- 进入人工接管。

### 7.5 带图售后问题

输入：

```text
我拍了照片，收到的外包装破损，里面也有划痕，怎么售后？
```

行为：

- 识别附件存在。
- 命中售后知识卡。
- 进入人工接管。
- 仅记录 `has_attachment` 质量信号，不自动判断图片责任。

## 8. 后续三阶段路线

### 阶段 A：研究闭环完善

目标：让 dry-run 骨架覆盖真实客服决策逻辑。

任务：

- 增加 50 条合成平台消息。
- 增加更多知识卡片。
- 增加意图分类。
- 增加低置信、投诉、售后、价格、发票、物流、库存等场景。
- 增加动作时间线。
- 增加 replay 评测。

验收：

- 所有动作 `external_write=false`。
- 风险问题必须转人工。
- 知识缺口必须进入缺口队列。
- 普通问题只允许生成草稿或填框计划。
- 每条消息必须输出 `reply_strategy`。
- 回复策略要覆盖标准问题、售后风险、知识缺口、价格承诺、图片附件和安全疑问。

### 阶段 B：半自动副驾驶

目标：接入坐席副驾驶，不接真实平台发送。

任务：

- 接入人工粘贴/导入消息。
- 输出回复草稿。
- 输出引用证据。
- 输出转人工原因。
- 支持一键复制。
- 支持知识缺口回流。

验收：

- 坐席能使用草稿。
- 所有发送仍由人完成。
- 不需要平台账号自动化。

### 阶段 C：实验室 RPA Adapter

目标：在测试账号和测试环境里研究 RPA 填框。

## 9. 最新客服平台回复策略融入

本研究线已经转向“回复策略验证”，不是单纯 RPA 动作验证。

参考主流平台当前策略：

- Intercom Fin：集中维护知识源，并配置转人工规则。
- Zendesk AI Agent：转人工前应收集订单号、姓名、邮箱、标签和字段，方便人工接手。
- Freshdesk AI Agent：指令不能替代事实，至少要配置知识源；工作流负责收集信息、检查条件、调用动作和必要时转人工。
- Salesforce Agentforce：智能体需要明确升级能力，缺少升级能力时不能假装已经交接。
- Playwright / RPA 工具：自动化要依赖可等待、可验证的 UI 定位和动作检查，不应靠固定坐标或固定等待。

因此，本项目后续把回复策略统一为：

| 场景 | 策略 |
|---|---|
| 标准知识可答 | 引用知识卡生成草稿，RPA 只填框，人工点击发送 |
| 售后/投诉/退款/平台介入 | 生成安抚和资料收集草稿，强制人工接管 |
| 缺知识/缺订单上下文 | 不编造，记录知识缺口或数据缺口 |
| 价格/最低价/承诺类 | 不做绝对承诺，人工确认 |
| 图片/视频/语音 | 只记录附件存在，不自动定责，后续可接视觉模型 |

详细工程计划见：

```text
standard_ops/docs/P3-06U-12_AI_RPA_REPLY_STRATEGY_INTEGRATION_PLAN.md
```

## 10. 推荐决策

建议把 AI+RPA 定义为：

```text
内部研究线、坐席副驾驶和自动填框能力
```

不定义为：

```text
平台官方能力
```

这条路线值得持续学习，因为它能帮助我们理解电商客服真实工作台、坐席操作路径、知识缺口和自动化边界。

当前结论：

```text
可以继续走，但必须先按 dry-run / 人工导入 / 只读观察 / 有人值守填框四级推进。
```

不要一步跳到真实自动点击发送。
