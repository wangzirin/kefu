# P3-06U-12 AI+RPA 回复策略与中台融合计划

日期：2026-07-02

## 1. 当前判断

这条线可以继续研究，而且值得继续研究；但它不能被写成“正式平台接入能力”。

更准确的定位是：

```text
AI+RPA 研究线 = 非官方渠道场景下的坐席副驾驶、自动填框、动作证据采集和回复策略验证线。
```

不应定位为：

```text
全平台官方自动回复能力。
```

原因很直接：

- RPA 能模拟真人客服在平台后台看消息、填回复、打标签、记录信息。
- RPA 不等于平台授权，不等于账号安全，也不等于高并发稳定能力。
- 对中小企业内部研究和试点，RPA 能快速验证“客服回复策略是否跑得通”。
- 对正式交付，仍要把风险边界写清楚：正式外发优先官方 API、服务商授权或人工发送；非官方自动点击发送不能进入默认承诺。

## 2. 本轮已经落地的研究能力

当前研究骨架位置：

```text
standard_ops/research/ai_rpa_closed_loop/
```

已经从 4 条样例扩展到 12 条样例，覆盖：

- 发货时效。
- 退款投诉。
- 发票开具。
- 知识缺口。
- 保修/质保。
- 价格议价。
- 平台介入。
- 现货时效。
- 图片售后。
- 安装教程。
- 人身安全疑问。

代码层新增 `ReplyStrategyDecision`，每条消息会输出：

| 字段 | 含义 |
|---|---|
| `intent` | 当前问题意图，例如物流、发票、售后风险、知识缺口 |
| `answer_mode` | 回答模式，例如知识草稿、人工接管草稿、知识缺口接管 |
| `delivery_mode` | 动作模式，例如填草稿、人工接管、记录缺口 |
| `customer_visible_policy` | 面向客户回复时应该遵守的口径 |
| `next_best_action` | 下一步动作，例如人工审核发送、收集证据、补知识 |
| `quality_signals` | 命中知识、低置信、附件、风控原因等质量信号 |

当前仍保持：

```text
external_write=false
auto_send_enabled=false
private_protocol_used=false
cookie_or_token_reuse_used=false
```

这说明它是研究 dry-run，不是真实外发。

## 3. 最新客服平台回复策略参考

本轮参考的是主流客服平台最近的官方文档，不使用博客或二手摘要作为主依据。

| 平台/资料 | 对我们有用的策略 |
|---|---|
| [Intercom Fin AI Agent explained](https://www.intercom.com/help/en/articles/7120684-fin-ai-agent-explained) | AI 回答要绑定集中维护的知识源，知识源可包括帮助中心、内部支持内容、PDF 和网页。 |
| [Intercom Fin escalation rules](https://www.intercom.com/help/en/articles/12396892-manage-fin-ai-agent-s-escalation-guidance-and-rules) | 转人工不是按钮堆砌，而是对话内自然交接；没有人工目标时不能假装已转接。 |
| [Intercom Fin Procedures](https://www.intercom.com/help/en/articles/12495167-fin-procedures-explained) | 复杂问题要通过可重复流程、工具和指导处理，并控制敏感/关键问题何时转人工。 |
| [Zendesk escalation strategies](https://support.zendesk.com/hc/en-us/articles/8357756604186-Configuring-escalation-strategies-and-flows-for-AI-agents) | 转人工前应收集订单号、姓名、邮箱、标签和字段，让人工接手时有上下文。 |
| [Zendesk voice AI agents](https://support.zendesk.com/hc/en-us/articles/10169333291290-Creating-an-AI-agent-for-the-voice-channel-EAP) | AI 可以先接待，需要时升级人工；每次交互应形成 ticket 或可追踪记录。 |
| [Freshdesk AI agent instructions](https://support.freshdesk.com/en/support/solutions/articles/50000011714) | 指令只能约束表达，不能替代事实；至少要配置知识源，才能保证回答准确。 |
| [Freshdesk workflows for AI agents](https://support.freshdesk.com/support/solutions/articles/50000011733-workflows-for-ai-agents-in-freshdesk) | 知识负责回答，工作流负责收集信息、检查条件、调用动作和必要时转人工。 |
| [Freshdesk AI performance metrics](https://support.freshdesk.com/en/support/solutions/articles/50000011716) | 需要用表现面板、会话来源、主题、渠道、反馈、知识源等维度持续优化。 |
| [Salesforce Agentforce escalation](https://help.salesforce.com/s/articleView?id=ai.service_agent_escalation.htm&language=en_US&type=5) | 智能体需要明确升级能力，缺少升级子能力时不能完成真正转人工。 |
| [Playwright actionability](https://playwright.dev/docs/actionability) | 浏览器自动化要依赖动作可执行检查和等待机制，不能用脆弱的固定等待冒充稳定。 |
| [Playwright locators](https://playwright.dev/docs/locators) | RPA/浏览器自动化应优先使用可重试、可等待的 locator，而不是靠坐标或脆弱选择器。 |
| [Microsoft attended/unattended automation](https://learn.microsoft.com/en-us/power-automate/guidance/planning/attended-unattended) | 自动化要区分有人值守和无人值守；当前研究应按有人值守副驾驶设计。 |
| [UiPath attended vs unattended robots](https://docs.uipath.com/robot/standalone/2023.4/admin-guide/attended-vs-unattended) | 有人值守适合辅助个人完成重复动作；无人值守适合后台长流程，但治理和环境要求更高。 |

这些参考共同指向一个结论：

```text
成熟智能客服不是“能生成一句话”，而是“知识有来源、流程可控制、风险会转人工、动作能追踪、复盘能改知识”。
```

## 4. 适合我们的回复策略

先按中小企业内部研究口径，不做复杂角色区分，只保留一个统一中台。

### 4.1 标准问题

适用：

- 发货时效。
- 发票开具。
- 基础质保。
- 基础活动说明。
- 售前常规问答。

策略：

1. 优先命中结构化知识卡。
2. 有引用来源才生成草稿。
3. RPA 只填入回复框。
4. 人工确认后发送。
5. 记录命中知识、置信度和最后动作。

当前 dry-run 对应：

```text
delivery_mode=fill_draft_only
next_best_action=operator_review_and_send
external_write=false
```

### 4.2 售后、投诉、退款、平台介入

适用：

- 退款纠纷。
- 商品损坏。
- 投诉、差评、平台介入。
- 赔偿、起诉、监管、工商等敏感词。

策略：

1. AI 只生成安抚和资料收集草稿。
2. 必须人工接管。
3. 如果有附件，记录附件存在，但不直接做图片结论。
4. 对话台要显示“为什么转人工”。
5. 进入质量复盘和知识缺口池。

当前 dry-run 对应：

```text
delivery_mode=human_takeover
next_best_action=collect_evidence_and_handoff
```

### 4.3 缺知识、缺库存、缺订单上下文

适用：

- 知识库没有覆盖的问题。
- 需要查实时库存、物流轨迹、订单详情的问题。
- 需要人工判断产品适配的问题。

策略：

1. 不编造。
2. 生成“需要核对后回复”的谨慎草稿。
3. 记录知识缺口或数据缺口。
4. 后台生成补知识任务。
5. 后续通过知识评测验证是否修复。

当前 dry-run 对应：

```text
delivery_mode=record_gap
next_best_action=record_knowledge_gap_and_handoff
```

### 4.4 价格、最低价、承诺类问题

适用：

- “最低价”。
- “保证明天到”。
- “一定能修好”。
- “绝对正品/绝对无问题”。

策略：

1. 不做绝对承诺。
2. 可引用页面活动或公司政策。
3. 涉及额外优惠、大额订单、投诉威胁时转人工。
4. 记录为高价值线索或风险线索。

当前 dry-run 将最低价议价转人工，不自动填可发送动作。

### 4.5 图片、视频、语音

适用：

- 商品破损照片。
- 安装视频。
- 质量问题图片。

当前阶段策略：

1. 只记录附件存在。
2. 不做自动视觉判断。
3. 可生成“请补充订单号/更多角度照片”的草稿。
4. 人工处理或后续接入单独视觉模型。

原因：

多模态判断容易涉及售后责任和证据真实性，不能直接由入门研究线自动定责。

## 5. RPA 路线怎么进入我们的工程

### 阶段 1：研究 dry-run

当前已完成第一片。

目标：

- 证明回复策略能跑通。
- 证明不外发。
- 证明知识缺口和人工接管能被记录。

验收：

- 至少 12 条合成消息。
- 标准问题进入 `fill_draft_only`。
- 风险问题进入 `human_takeover`。
- 缺知识进入 `record_gap`。
- 输出审计 JSON。
- 禁止 `click_send`、私有协议、Cookie/Token 复用。

### 阶段 2：人工导入副驾驶

目标：

- 不接真实平台账号。
- 允许人工复制一段客户消息到中台。
- 中台返回草稿、引用、转人工原因、下一步动作。

中台需要新增：

- “RPA 研究台 / 副驾驶试验”入口。
- 粘贴客户消息表单。
- 策略结果卡：意图、回答模式、动作模式、转人工原因。
- 一键复制草稿。
- 一键记录知识缺口。

### 阶段 3：只读屏幕观察

目标：

- 研究 OCR/截图观察是否能稳定识别消息。
- 不写平台、不填框、不发送。

验收：

- 每次观察生成截图证据引用。
- 识别失败率可统计。
- 页面变化不会导致程序静默误判。

### 阶段 4：有人值守填框

目标：

- 在测试账号和测试环境里，研究 RPA 自动填入回复框。
- 发送按钮仍由人工点击。

验收：

- 只允许 `fill_reply_box`。
- 禁止 `click_send`。
- 页面定位失败必须停机。
- 每次填框有截图证据。

### 阶段 5：是否研究自动发送

默认不进入。

只有在测试账号、测试店铺、用户明确授权、账号风险可接受、平台规则已单独核验时，才可以做实验室验证。即使实验成功，也不能直接写进正式对外方案。

## 6. 对当前 P3 工程计划的调整

原 P3-06U-11 仍继续推进，但下一步不要急着做复杂管理员/坐席权限拆分。

新的施工顺序建议：

| 阶段 | 名称 | 目标 |
|---|---|---|
| P3-06U-12A | RPA 回复策略研究线固化 | 保持 dry-run，完善策略字段、样例、检查和文档 |
| P3-06U-12B | 副驾驶入口 | 在中台新增人工粘贴消息入口，输出策略结果和草稿 |
| P3-06U-12C | 对话台策略融合 | 在多渠道对话台展示 `intent / delivery_mode / next_best_action` |
| P3-06U-12D | 坐席判断区收束 | 合并策略、AI 草稿、人审原因、知识依据和下一步动作 |
| P3-06U-12E | RPA 浏览器回复可行性 | 在可控类平台页面验证读消息、填草稿、可控发送 |
| P3-06U-12F | 单平台真实页面 Draft-Only | 用户人工登录测试账号后，验证真实页面读取消息和填框 |
| P3-06U-12G | 质量复盘融合 | 把策略失败、知识缺口、转人工原因进入 BI |

## 7. 当前是否可以改变主线

可以调整研究重点，但不建议把原来的官方渠道主线完全删除。

更合理的架构是：

```text
官方 API / Webhook 线：正式交付候选
AI+RPA 线：内部研究、半自动副驾驶、平台后台操作理解、补充渠道验证
统一中台：同一套知识库、同一套回复策略、同一套质量复盘
```

这样做的好处：

- 现在可以快速研究非官方渠道的真实工作台形态。
- 不会把账号风险和平台协议风险写成正式能力。
- 回复策略可以统一，不管消息来自官方 webhook、人工粘贴还是 RPA 观察。
- 后续如果某个平台开放官方能力，可以把入口替换掉，回复策略不用重写。

## 8. 下一步

下一步建议做 P3-06U-12B：

```text
在中台里新增“RPA 副驾驶试验”入口。
```

第一版只做三件事：

1. 人工粘贴客户消息。
2. 后端调用当前 AI+RPA dry-run engine。
3. 前端展示草稿、引用、转人工原因、知识缺口和下一步动作。

这一步最符合当前目标：不碰真实平台、不冒账号风险，但能很快判断这套技术路线作为客服系统核心回复策略是否成立。

## 9. P3-06U-12B 进展

状态：已完成第一片。

本片采用隔离实验入口：

```text
#rpa-lab
```

没有直接改动现有多渠道对话台主流程。原因是当前能力仍是内部研究，直接塞进主工作台会让信息架构再次变重。

已新增：

- 后端 `POST /api/rpa-copilot/strategy-dry-run`。
- 前端“实验室 -> RPA副驾驶试验”入口。
- 人工粘贴消息表单。
- 策略结果卡。
- 回复草稿、风控原因、质量信号、引用来源和动作计划展示。
- 一键复制草稿。
- 后端/前端/浏览器门禁。

保留边界：

- 不读取平台账号。
- 不保存客户消息。
- 不点击发送。
- 不创建正式会话。
- 不进入 outbox。
- 不触发真实外发。

如果后续验证成为核心能力，应保留后端策略服务，隐藏或删除 `#rpa-lab` 实验页，再把策略服务接入：

- 多渠道对话台。
- 质量复盘。
- 知识缺口。
- 官方 webhook 入站编排。
- 未来 RPA 只读观察 adapter。

阶段文档：

```text
standard_ops/docs/P3-06U-12B_RPA_COPILOT_LAB_ENTRY.md
```

## 10. P3-06U-12C 进展

状态：已完成第一片。

本片解决两个落地问题：

1. 打开 `#rpa-lab` 时，如果没有登录，会先进入登录页；登录后必须保留原始目标页，不能强制回 `#overview`。
2. RPA 副驾驶不能只停留在实验页，需要开始进入正式坐席工作流，但仍保持 dry-run。

已新增/调整：

- `POST /api/auth/dev-local-login`：仅本地 development 使用的测试登录入口。
- 登录页默认租户和邮箱改为本地开发库：
  - `wanfa-local-dev`
  - `real-test@wanfa.local`
- 登录页新增“本地测试进入”按钮，本地研究阶段不需要手动输入密码。
- 登录成功和开发演示进入后会保留当前 hash；无权限时才回角色默认页。
- 多渠道对话台新增“回复策略”摘要。
- 对当前会话点击“试算当前会话”后展示：
  - 填入草稿 / 人工接管 / 补知识。
  - 意图。
  - 下一步。
  - 置信度。
  - 引用数量。

保留边界：

- 不接真实平台。
- 不读取平台账号。
- 不保存客户消息。
- 不创建 outbox 外发动作。
- 不触发真实发送。

阶段文档：

```text
standard_ops/docs/P3-06U-12C_LOGIN_ROUTE_AND_LIVE_STRATEGY_SUMMARY.md
```

浏览器证据：

```text
standard_ops/output/p3_06u_12c_login_route_and_live_strategy/
```

下一步建议进入 P3-06U-12D，把“策略摘要、AI 草稿、人审原因、知识引用、建议动作”合并得更顺，不要让坐席界面出现重复判断区。

## 11. P3-06U-12D 进展

状态：已完成第一片。

本片把多渠道对话台中的分散判断区收束为统一的“坐席判断区”。

已调整：

- 移除对话台内独立的会话上下文快照、回复策略摘要、无知识命中警告和建议动作条。
- 新增统一坐席判断区，集中展示：
  - 坐席判断。
  - 客户信息。
  - AI 草稿。
  - 人审原因。
  - 知识依据。
  - 下一步动作。
  - 安全门禁。
- “试算当前会话”仍调用后端 RPA dry-run 策略服务，但结果直接进入坐席判断区。
- 新增“带入回复框”，只把策略草稿写入前端编辑区，并添加内部备注；不保存、不进入待发送、不外发。
- RPA 策略枚举和门禁原因统一翻译成中文业务语言，未知枚举不再原样显示。

保留边界：

- 不接真实平台账号。
- 不读取平台后台。
- 不自动填真实平台表单。
- 不点击发送。
- 不创建 outbox 外发动作。
- 不触发 worker。

阶段文档：

```text
standard_ops/docs/P3-06U-12D_LIVE_DECISION_CENTER_CONSOLIDATION.md
```

浏览器证据：

```text
standard_ops/output/p3_06u_12d_live_decision_center/
```

下一步建议：

```text
把坐席判断区产生的知识缺口、转人工原因和策略失败信号接入质量复盘/知识缺口闭环。
```

如果继续 RPA 研究线，下一片只能做只读观察 PoC，仍不能进入真实自动发送。

## 12. P3-06U-12E 进展

状态：已完成第一片。

用户明确纠偏后，本片停止继续扩展官方 API 和质量复盘，回到 RPA 技术研究主线。

本片新增：

- 本地类平台客服工作台：

```text
research/rpa_browser_reply_feasibility/mock_platform_workbench.html
```

- 浏览器 RPA driver：

```text
scripts/run_p3_06u_12e_rpa_browser_reply_feasibility.mjs
```

- selector profile 模板：

```text
research/rpa_browser_reply_feasibility/selector_profile.example.json
```

已证明：

- RPA 可以通过浏览器页面定位会话。
- RPA 可以读取客户消息。
- RPA 可以调用现有客服策略服务。
- RPA 可以把草稿填入页面回复框。
- 本地 mock 页面显式开启 `RPA_ALLOW_SEND=1` 后，可以点击发送。

未证明：

- 真实平台 DOM 结构和 selector 稳定性。
- 真实平台风控、登录、验证码、iframe、虚拟列表和异常弹窗。
- 长时间多会话处理。
- 真实外部平台发送动作安全性。

阶段文档：

```text
standard_ops/docs/P3-06U-12E_RPA_BROWSER_REPLY_FEASIBILITY.md
```

浏览器证据：

```text
standard_ops/output/p3_06u_12e_rpa_browser_reply_feasibility/draft_only/
standard_ops/output/p3_06u_12e_rpa_browser_reply_feasibility/mock_send/
```

下一步建议：

```text
P3-06U-12F 单平台真实页面 RPA Draft-Only 试验。
```

这一片只做人工登录测试账号后的真实页面读取和填框，默认不点击发送。

## 13. P3-06U-12H 进展

状态：已完成第一片。

本片没有继续操作真实页面，而是把真实页面研究所需的脱敏定位器边界先固化为 profile。

新增文件：

```text
research/rpa_browser_reply_feasibility/profiles/douyin_web_dm.draft_only.locator_profile.json
docs/P3-06U-12H_REAL_PAGE_LOCATOR_PROFILE_DRAFT.md
scripts/check_p3_06u_12h_real_page_locator_profile.py
```

已固化边界：

- 页面类型是抖音网页个人私信弹窗，不等同抖店飞鸽、企业客服、官方开放平台或正式客服连接器。
- 只允许 Draft-Only：定位输入框、填入临时草稿、清空草稿。
- 禁止点击发送，禁止按 Enter 发送。
- 禁止保存私聊原文、联系人、群名、头像、视频卡片、未读数、账号号段、Cookie、Token、LocalStorage、截图和原始辅助功能树。
- 真实页面试验必须操作者可见，且需要单独确认。

验证：

```bash
python3 -m json.tool research/rpa_browser_reply_feasibility/profiles/douyin_web_dm.draft_only.locator_profile.json >/dev/null
python3 scripts/check_p3_06u_12h_real_page_locator_profile.py
```

下一步建议：

```text
P3-06U-12I Operator-Mediated Draft-Only Smoke。
```

如果继续，就只做一次操作者可见的“填入临时草稿 -> 立即清空 -> 确认未发送”。如果这一步失败，应暂停个人网页私信 RPA 路线，回到官方 API、服务商授权和商家后台正式能力研究。
