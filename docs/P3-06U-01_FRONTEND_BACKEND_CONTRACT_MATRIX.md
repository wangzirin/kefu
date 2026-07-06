# P3-06U-01 前后端契约与页面路径盘点

日期：2026-07-01  
适用系统：万法常世 AI 全智能客服系统标准运营版  
工程目录：`/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops`  
上游依据：`P3-06U_FRONTEND_BACKEND_ALIGNMENT_AND_PRACTICAL_UX_OPTIMIZATION_PLAN.md`  
阶段定位：先把当前页面、后端接口、权限、状态机和真实边界盘清，再继续做大面积视觉和交互重构。

## 1. 工程控制卡

| 项目 | 内容 |
| --- | --- |
| 阶段编号 | P3-06U-01 |
| 阶段名称 | 前后端契约与页面路径盘点 |
| 本轮目标 | 建立核心工作区的页面/API/权限/状态矩阵，清理第一批客户可见的工程阶段口吻 |
| 本轮改动边界 | 不打开真实外发；不接入非官方渠道；不新增无后端契约的功能；不修改后端业务状态机 |
| 本轮产品修复 | 左侧导航和设置页去掉 `P3-06UI`、`P3-06F`、`RAG`、`规划态`、`施工入口` 等内部工程表达 |
| 验收方式 | 静态契约脚本、前端 typecheck、前端 build、项目记录写回 |
| 后续阶段 | P3-06U-02 角色化任务路径重排；P3-06U-03 接待工作台实用性重构 |

## 2. 当前真实阶段

系统现在已经具备一条受控客服中台主链：

```mermaid
flowchart LR
  A["可信入站消息"] --> B["回复编排"]
  B --> C["人工审核"]
  C --> D["待发送草稿"]
  D --> E["发送计划 / 队列"]
  E --> F["失败复盘"]
  F --> G["知识缺口"]
  G --> H["知识修复与回归"]
```

但这条链路仍处在受控试点和标准运营版建设阶段，不等于全渠道真实自动回复已经上线。

| 模块 | 当前真实能力 | 仍不能承诺的能力 |
| --- | --- | --- |
| 前端中台 | 已有固定壳层、运营总览、接待工作台、会话收件箱、人工审核、待发送、联系人、线索、知识、质量、渠道、运维 | 还没有完成所有角色的真实登录端到端 smoke；部分页面仍需要按岗位任务重排 |
| 后端主链 | 有认证、租户、RBAC、会话、workflow、人审、outbox、dry-run、delivery job、失败复盘、知识文档、知识评测 | 还没有打开真实外部发送；没有生产级全渠道连接器实测闭环 |
| 知识库 | 有知识卡片、文档导入、分块、检索、发布门禁、回归题和回滚入口 | 还不是完整生产级向量库、重排器、批量文件解析和人工标注平台 |
| 模型路由 | 有模型网关边界、确定性 provider、百炼/DeepSeek 可插拔入口和人审兜底 | 不能把模型能力描述为“全自动无人值守”；真实模型质量仍需客户题库评测 |
| 渠道接入 | 有官网/企业微信/公众号等官方通道 readiness 和 webhook/connector 契约 | 企业微信、公众号、电商平台真实自动回复仍需要官方授权、公网 HTTPS、验签、回调和白名单 smoke |
| 高并发 | 有 worker、lease、heartbeat、dry-run 队列、只读指标和告警目录 | 还没有做压测、水平扩容、生产缓存、独立队列集群和 SLA 演练 |

## 3. 角色与权限基线

后端 `ROLE_PERMISSIONS` 是前端显示和动作门禁的源头。前端按钮禁用只能改善体验，不能替代后端权限。

| 角色 | 应看到的主入口 | 核心权限 | 前端设计原则 |
| --- | --- | --- | --- |
| owner | 运营总览、接待工作台、质量复盘、知识运营、渠道接入、管理运维 | 全量经营、会话、知识、渠道、outbox、运维、账号管理 | 可以看到配置、风险和管理动作，但真实外发仍受全局开关限制 |
| admin | 运营总览、接待工作台、质量复盘、知识运营、渠道接入、管理运维 | 除账号创建外的大部分运营管理权限 | 和 owner 接近，但不默认承担账号体系初始化 |
| agent | 接待工作台、会话、人工审核、待发送、联系人、线索、轻量工单、知识读取 | conversation/customer/lead/ticket/outbox/knowledge.read | 少看管理信息，重点完成接待、审核、备注、确认待发送 |
| viewer | 运营总览、质量复盘、渠道状态 | dashboard.read、quality.read、channel.read、failure_review.read | 只看经营信号和风险，不展示写动作按钮墙 |

## 4. 页面契约矩阵

### 4.1 运营总览

| 字段 | 内容 |
| --- | --- |
| 页面名称 | 运营总览 |
| 路由 | `#overview` |
| 主要用户 | owner、admin、viewer |
| 业务目的 | 让管理者快速判断今天客服系统是否健康，并进入下一步处理路径 |
| 后端 API | `GET /api/tenants/{tenant_id}/ops/dashboard` |
| 权限 | `dashboard.read` |
| 数据状态 | 优先服务端聚合；无 token 或开发演示时可能出现本地样本/汇总 |
| 关键动作 | 刷新数据、切换时间范围、进入高风险会话、待发送、渠道异常、知识缺口等处理入口 |
| 后端状态机 | 本页不直接改状态，只读取聚合结果 |
| 审计 | 读取本身不写业务审计；后续跳转动作由目标页面写审计 |
| 空态/错态 | 应明确区分“暂无数据”“无权限”“服务端聚合失败”“演示样本” |
| 当前缺口 | 优先动作已出现，但还需要把跳转过滤条件和目标页面状态完全绑定 |

### 4.2 接待工作台

| 字段 | 内容 |
| --- | --- |
| 页面名称 | 多渠道对话台 |
| 路由 | `#live` |
| 主要用户 | owner、admin、agent |
| 业务目的 | 坐席在一屏内完成看客户、看消息、看 AI 草稿、改写、备注、审核、确认进入待发送 |
| 后端 API | `GET /api/tenants/{tenant_id}/conversation-inbox`、`GET /api/tenants/{tenant_id}/human-review-inbox`、`GET /api/tenants/{tenant_id}/outbox-drafts`、`PATCH /api/human-review-tasks/{task_id}`、`POST /api/human-review-tasks/{task_id}/outbox-draft`、`POST /api/outbox-drafts/{draft_id}/confirmation`、`PATCH /api/conversations/{conversation_id}/assignment`、`POST /api/conversations/{conversation_id}/workflow-actions` |
| 权限 | `conversation.read`、`conversation.manage`、`outbox.draft.read`、`outbox.draft.manage` |
| 数据状态 | 真实服务端数据；开发模式可使用演示身份 |
| 关键动作 | 分配会话、标记风险、改写草稿、批准审核、创建待发送、确认待发送、写备注、创建工单/线索 |
| 后端状态机 | conversation assignment/status、human_review_task resolved、outbox_draft pending/confirmed |
| 审计 | 会话动作、人审动作、outbox 动作应保留审计链 |
| 空态/错态 | 无待办时应告诉坐席下一步；403 不应显示一堆不可点按钮 |
| 当前缺口 | 页面已具备主链，但还需更像真实 IM 工作区：左侧会话列表、中间消息流、右侧客户上下文和底部动作区应继续收紧 |

### 4.3 会话收件箱

| 字段 | 内容 |
| --- | --- |
| 页面名称 | 会话收件箱 |
| 路由 | `#conversations` |
| 主要用户 | owner、admin、agent |
| 业务目的 | 按等待时间、风险、渠道、接管状态和负责人处理入站会话 |
| 后端 API | `GET /api/tenants/{tenant_id}/conversation-inbox`、`PATCH /api/conversations/{conversation_id}/assignment`、`POST /api/conversations/{conversation_id}/workflow-actions` |
| 权限 | 读 `conversation.read`；写 `conversation.manage` |
| 数据状态 | 服务端分页/过滤结果；当前前端仍需确认所有筛选是否由后端支持 |
| 关键动作 | 分配、接管、标记风险、标记知识缺口、进入对话台 |
| 后端状态机 | 会话分配、状态标签、workflow action |
| 审计 | 会话动作应写审计或 workflow step |
| 当前缺口 | 筛选和分页体验要继续从“列表展示”变成“坐席队列处理” |

### 4.4 人工审核

| 字段 | 内容 |
| --- | --- |
| 页面名称 | 人工审核 |
| 路由 | `#reviews` |
| 主要用户 | owner、admin、agent |
| 业务目的 | 对低置信、高风险、无知识命中和模型异常的草稿进行人工放行或驳回 |
| 后端 API | `GET /api/tenants/{tenant_id}/human-review-inbox`、`PATCH /api/human-review-tasks/{task_id}`、`POST /api/human-review-tasks/{task_id}/outbox-draft` |
| 权限 | 读 `conversation.read`；写 `conversation.manage`、`outbox.draft.manage` |
| 数据状态 | 真实审核任务 |
| 关键动作 | 修改最终回复、记录审核意见、批准、拒绝、创建 outbox 草稿 |
| 后端状态机 | human_review_task pending/resolved/rejected；workflow state 写入最终回复 |
| 审计 | 审核结论和最终回复必须可追溯 |
| 当前缺口 | 需要更明确地区分“审核通过”和“已经发送给客户” |

### 4.5 待发送草稿

| 字段 | 内容 |
| --- | --- |
| 页面名称 | 待发送草稿 |
| 路由 | `#outbox` |
| 主要用户 | owner、admin、agent |
| 业务目的 | 在真实外发前集中确认草稿、生成发送计划、跑 dry-run 和查看失败复盘 |
| 后端 API | `GET /api/tenants/{tenant_id}/outbox-drafts`、`POST /api/outbox-drafts/{draft_id}/confirmation`、`POST /api/outbox-drafts/{draft_id}/send-attempts/dry-run`、`POST /api/outbox-drafts/{draft_id}/connector-send-plan`、`POST /api/outbox-drafts/{draft_id}/delivery-jobs`、`GET /api/tenants/{tenant_id}/outbox-delivery-jobs` |
| 权限 | `outbox.draft.read/manage`、`outbox.send_attempt.read/manage`、`outbox.send_plan.manage`、`outbox.delivery_job.read/manage` |
| 数据状态 | 服务端 outbox、send attempts、delivery jobs |
| 关键动作 | 确认待发送、取消、dry-run、生成连接器发送计划、创建 delivery job、运行队列检查 |
| 后端状态机 | draft pending/confirmed/cancelled；attempt created；job queued/running/failed/dead_letter |
| 审计 | outbox 动作和 send attempt 必须可追溯 |
| 当前缺口 | 页面要持续强化“真实外发关闭”和“只是进入发送计划/队列”的边界 |

### 4.6 联系人与线索

| 字段 | 内容 |
| --- | --- |
| 页面名称 | 联系人中心、线索跟进 |
| 路由 | `#contacts`、`#leads` |
| 主要用户 | owner、admin、agent |
| 业务目的 | 让坐席和销售看到客户画像、历史会话、工单、线索阶段和下一步跟进 |
| 后端 API | `GET /api/tenants/{tenant_id}/contact-profiles`、`GET /api/contact-profiles/{contact_id}`、`GET /api/tenants/{tenant_id}/leads`、`POST /api/conversations/{conversation_id}/leads`、`PATCH /api/leads/{lead_id}` |
| 权限 | `customer.read/manage`、`lead.read/manage` |
| 数据状态 | 服务端客户画像和线索 |
| 关键动作 | 查看画像、创建线索、更新阶段、分配负责人、记录下一步 |
| 后端状态机 | lead stage/owner/next_action |
| 审计 | 线索创建和更新应可追溯 |
| 当前缺口 | 不能做成重 CRM 幻觉；应该服务客服转化和售后跟进 |

### 4.7 工单/SLA

| 字段 | 内容 |
| --- | --- |
| 页面名称 | 工单/SLA |
| 路由 | `#tickets` |
| 主要用户 | owner、admin、agent |
| 业务目的 | 把需要持续处理的会话沉淀为轻量工单，跟踪负责人、状态、SLA 到期和解决结果 |
| 后端 API | `GET /api/tenants/{tenant_id}/support-tickets`、`POST /api/conversations/{conversation_id}/support-tickets`、`PATCH /api/support-tickets/{ticket_id}` |
| 权限 | `ticket.read`、`ticket.manage` |
| 数据状态 | 服务端轻量工单 |
| 关键动作 | 创建工单、更新状态、更新负责人、处理 SLA 风险 |
| 后端状态机 | open/in_progress/resolved/closed 和 SLA due |
| 当前缺口 | 当前应保持轻量，不扩展成完整 ITSM 或重型工单系统 |

### 4.8 知识运营

| 字段 | 内容 |
| --- | --- |
| 页面名称 | 知识库运营、知识缺口、知识评测 |
| 路由 | `#knowledge`、`#gaps`、`#evals` |
| 主要用户 | owner、admin；agent 可读知识 |
| 业务目的 | 维护客服知识，处理低置信和错误回答背后的知识缺口，发布前回归，必要时回滚 |
| 后端 API | `GET /api/tenants/{tenant_id}/knowledge-documents`、`POST /api/tenants/{tenant_id}/knowledge-documents`、`GET /api/knowledge-documents/{document_id}/chunks`、`POST /api/knowledge-documents/{document_id}/publish-checks`、`POST /api/knowledge-documents/{document_id}/publication`、`GET /api/knowledge-documents/{document_id}/publications`、`POST /api/knowledge-publications/{publication_id}/rollback`、`POST /api/tenants/{tenant_id}/knowledge-document-search`、`GET /api/tenants/{tenant_id}/knowledge-gaps`、`POST /api/tenants/{tenant_id}/knowledge-gaps/sync`、`PATCH /api/knowledge-gaps/{gap_id}`、`POST /api/knowledge-gaps/{gap_id}/document-draft`、`POST /api/knowledge-gaps/{gap_id}/regression-case`、`GET /api/tenants/{tenant_id}/knowledge-evaluation-sets`、`POST /api/tenants/{tenant_id}/knowledge-evaluation-sets`、`POST /api/knowledge-evaluation-sets/{set_id}/runs` |
| 权限 | 读 `knowledge.read`；管理 `knowledge.manage` |
| 数据状态 | 服务端知识文档、chunk、缺口、评测集、发布记录 |
| 关键动作 | 导入文档、搜索片段、同步缺口、生成草稿、生成回归题、发布预检、发布、回滚、运行评测 |
| 后端状态机 | document draft/active/archived；gap open/in_progress/resolved；evaluation run completed/failed |
| 审计 | 发布、回滚、缺口处理和评测结果都应可追溯 |
| 当前缺口 | 页面要更像“准确率维护工作台”，少一点工程表格感 |

### 4.9 质量复盘

| 字段 | 内容 |
| --- | --- |
| 页面名称 | 质量诊断 |
| 路由 | `#quality` |
| 主要用户 | owner、admin、viewer；知识负责人可作为 admin 使用 |
| 业务目的 | 找到回答质量下降的原因，并推动知识修复、审核策略、渠道排障或模型调整 |
| 后端 API | 当前主要来自前端聚合：human review、outbox、failure review、knowledge gaps、evaluation runs；后续应补 dedicated `quality.read` 聚合接口 |
| 权限 | `quality.read`；相关下钻受 `knowledge.manage`、`conversation.read`、`outbox.failure_review.read` 约束 |
| 数据状态 | 部分服务端真实数据，部分前端聚合 |
| 关键动作 | 查看错因、进入知识缺口、进入失败复盘、进入评测结果、进入审核队列 |
| 后端状态机 | 本页读多写少，修复动作由目标页面完成 |
| 当前缺口 | 还需要更强的错因 BI 和“发现问题 -> 修复知识 -> 回归验证”的闭环 |

### 4.10 渠道接入

| 字段 | 内容 |
| --- | --- |
| 页面名称 | 渠道接入 |
| 路由 | `#channels` |
| 主要用户 | owner、admin、viewer；agent 可读部分渠道状态 |
| 业务目的 | 展示官方通道接入状态、回调验证、连接器配置、最近回执和失败复盘 |
| 后端 API | `GET /api/channel-providers`、`GET /api/channels/{channel_id}/connector-config`、`POST /api/channels/{channel_id}/connector-config`、`GET /api/channels/{channel_id}/delivery-receipts`、`GET/POST /api/webhooks/wecom/channels/{channel_id}`、`POST /api/webhooks/{provider}/channels/{channel_id}`、`GET /api/tenants/{tenant_id}/delivery-failure-reviews` |
| 权限 | 读 `channel.read`、`channel.delivery_receipt.read`、`outbox.failure_review.read`；管理 `channel.connector.manage`、`channel.delivery_receipt.manage` |
| 数据状态 | 连接器配置和回执为服务端数据；真实平台联调需官方后台配置和公网 HTTPS |
| 关键动作 | 查看接入步骤、配置连接器、查看回执、查看失败复盘、运行可信入站 worker |
| 后端状态机 | connector configured/blocked；receipt signature_validated/untrusted；failure review open/resolved |
| 当前缺口 | 需要升级为真正的连接器中心：每个渠道显示“已完成/缺什么/下一步在哪里操作/风险边界” |

### 4.11 管理运维

| 字段 | 内容 |
| --- | --- |
| 页面名称 | 运维与告警、模型路由、系统设置 |
| 路由 | `#ops`、`#model`、`#settings` |
| 主要用户 | owner、admin |
| 业务目的 | 让内部交付和管理员知道 worker、告警、指标、模型路由和安全开关的状态 |
| 后端 API | `GET /api/tenants/{tenant_id}/ops/worker-health`、`GET /api/tenants/{tenant_id}/ops/alert-rules`、`GET /api/tenants/{tenant_id}/ops/metrics`、`GET /api/tenants/{tenant_id}/audit-events`、账号和团队相关接口 |
| 权限 | `ops.worker_health.read`、`ops.alert_rules.read`、`ops.metrics.read`、`audit.events.read`、`accounts.manage` |
| 数据状态 | 运维只读服务端数据；设置页当前偏说明和入口，不直接写生产开关 |
| 关键动作 | 刷新健康、查看告警规则、查看指标出口、理解模型路由边界 |
| 当前缺口 | 设置页还没有完整账号配置 UI；后续必须避免客户误以为所有安全开关都已可自助配置 |

## 5. 第一批错位点

| 编号 | 错位点 | 风险 | 本轮状态 |
| --- | --- | --- | --- |
| U01-01 | 左侧导航显示 `P3-06UI`、`P3-06F` 等内部阶段编号 | 客户会觉得这是未完成工程面板 | 已修复为“今日”“健康”等产品语言 |
| U01-02 | 左侧导航把知识入口标成 `RAG` | 客户不一定理解，且容易误以为完整生产级 RAG 已完成 | 已改为“知识” |
| U01-03 | 系统设置显示“规划/规划态/施工入口” | 对外显得不成熟，也像内部汇报 | 已改为授权和验收边界说明 |
| U01-04 | 渠道接入口仍偏“渠道健康” | 不能表达接入进度、回调验证和连接器配置 | 已先改名为“连接器状态”，后续做连接器中心 |
| U01-05 | 运营总览优先动作未完全绑定过滤后的目标页 | BI 发现问题后处理路径不够顺 | 待 P3-06U-04 |
| U01-06 | 质量诊断依赖多源前端聚合 | 错因口径后续可能和后端真实统计不一致 | 待 dedicated 质量聚合接口或统一聚合口径 |
| U01-07 | 接待工作台仍不像真实客服 IM 的完整操作台 | 坐席效率和产品观感不足 | 待 P3-06U-03 |
| U01-08 | 知识运营仍有工程表格感 | 客户不容易独立修准确率 | 待 P3-06U-06/P3-06U-07 |
| U01-09 | 渠道接入还没有按官方平台步骤做成配置向导 | 交付和售后排障成本高 | 待 P3-06U-08 |
| U01-10 | 老的验收脚本曾要求导航保留阶段编号 | 会把错误产品口吻固化成“通过条件” | 本轮同步改为禁止内部阶段编号 |

## 6. 本轮已修复

| 文件 | 修复内容 |
| --- | --- |
| `frontend/src/data/navigation.ts` | 导航去掉阶段编号和工程缩写；知识、质量、渠道、运维入口改成客户可理解的产品语言 |
| `frontend/src/App.tsx` | 渠道和设置页面说明去掉“规划态/施工入口”口吻，保留“未完成授权和验收前不触发真实外部动作”的安全边界 |
| `scripts/check_p3_06u_01_contract_alignment.py` | 新增静态契约检查，防止导航重新出现工程阶段标签 |
| `scripts/check_p3_06ui_information_architecture.py` | 更新历史验收脚本，不再把 `P3-06UI` 阶段标识当成必须保留的 UI 文案 |

## 7. 下一步施工建议

1. 先做 P3-06U-02 角色化任务路径重排：owner/admin/agent/viewer 登录后各自只看到最重要的任务路径。
2. 再做 P3-06U-03 接待工作台实用性重构：按照真实客服 IM 工作区调整会话列表、消息区、右侧画像和动作区。
3. 随后做 P3-06U-04 运营总览到处理路径打通：每个优先动作都能跳到带过滤条件的处理页。
4. 渠道接入中心和质量错因 BI 分别进入 P3-06U-08、P3-06U-06，不再用单页说明文字硬撑。

## 8. 结论

当前系统不是“前端太丑”的单点问题，而是产品化前端需要和后端契约、权限、状态机、真实运维边界重新对齐。

P3-06U-01 的价值是把后续优化从“继续凭观感改页面”改成“按真实业务路径和后端契约推进”。这一轮只做低风险清理和矩阵建设，后续每一轮都应该回到这份矩阵检查：页面是否服务真实岗位、动作是否有后端契约、权限是否一致、失败后用户是否知道下一步。
