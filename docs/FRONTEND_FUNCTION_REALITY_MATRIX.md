# 前端功能真实性矩阵

日期：2026-07-05  
阶段：P3-06U-26H2W-FE6  
用途：作为客户可见功能进入下一阶段前的真实性门禁。任何客户可见控件必须能被归类为真实可用、只读可用、禁用合理或已隐藏；不允许保留无动作按钮、假流程或超过后端能力的文案。

## 0.7 H2W-FE6 最新前端真实工作流复测记录

本轮在 FE5 发现“试点准备”页尚未进入浏览器逐页点击清单后，补做最新前端全量复测：

| 项目 | 当前结论 | 验收方式 |
|---|---|---|
| 最新浏览器 QA | `status=passed_latest_frontend_browser_qa` | `scripts/check_p3_06u_26h2w_fe6_latest_frontend_browser_qa.mjs` |
| 试点准备页 | `#pilot` 已进入真实登录点击清单，并点击 6 步入口 | 截图 `output/p3_06u_26h2w_fe6_latest_frontend_browser_qa/fe6-11-pilot.png` |
| 覆盖页面 | 总览、接待工作台、多渠道对话台、知识运营、知识缺口、知识评测、质量复盘、渠道接入、账号与本地维护、自动回复策略、试点准备 | FE6 `summary.json` |
| 客户可见工程词 | H2W、P3、dry-run、provider、outbox、sandbox 等在客户可见页保持清理 | FE6 浏览器脚本逐页文本扫描 |
| 多渠道对话台 | 继续保持紧凑会话列表 + 大面积聊天流；转人工只是会话状态 | FE6 截图和 DOM 检查 |
| 边界 | 真实外发、真实渠道、正式客户签收、签名安装包仍不在 FE6 完成口径内 | FE6 summary 固定边界字段 |

## 0.6 H2W-FE4 客户可见 UI 封版候选记录

本轮在 FE2 静态矩阵、FE3 浏览器工作流和 PACK4 本地试点启动 rehearsal 基础上，补了一层客户可见 UI 封版候选门禁：

| 项目 | 当前结论 | 验收方式 |
|---|---|---|
| 客户可见 UI 候选 | 静态门禁状态为 `ready_for_customer_visible_ui_candidate` | `scripts/check_p3_06u_26h2w_fe4_customer_ui_sealed_candidate.py` |
| 真实登录点击 QA | 浏览器点击状态为 `passed_customer_visible_click_qa` | `scripts/check_p3_06u_26h2w_fe4_customer_visible_click_qa.mjs` |
| 多渠道对话台 | 保持紧凑会话列表 + 大面积消息流；转人工只作为会话状态 | 截图 `output/p3_06u_26h2w_fe4_customer_visible_click_qa/fe4-live-workbench.png` |
| 隐藏后台入口 | 会话收件箱、人工审核、待发送草稿、工单/SLA 仍作为后台能力保留，但不出现在主侧边栏 | 浏览器脚本检查侧边栏文本 |
| 客户可见文案 | `Provider：`、`H2W`、`P3`、`connector_noop`、越界完成态和真实外发误导均不允许出现在客户可见页；模型页使用“生产检索准备度”这类业务口径 | 静态门禁 + 浏览器逐页检查 |
| 边界 | 真实外发、正式客户签收、企业渠道和移动端仍不纳入本阶段 | `summary.json` 固定边界字段 |

## 0. P3-06U-26H2W3A 收口记录

本轮已根据 3 个子智能体交叉审查和浏览器门禁完成客户可见信息架构收口：

| 项目 | 当前结论 | 后续要求 |
|---|---|---|
| 多渠道对话台 | 客户可见主屏已收束为三队列：全部、我的、转人工；右侧只保留会话流和接管输入区 | 高风险、无知识、失败、超时等只能作为转人工来源或质量复盘原因，不再变成主屏二级队列 |
| 工程词 | 浏览器深审已达到 `Issues: 0`，客户可见页不再出现 API、sandbox、outbox、connector_noop、P3-06、H2W | 后续新增页面必须继续跑 `audit_p3_06u_26h2w3_frontend_clicks_and_ux.mjs` |
| 隐藏后台路由 | 总览、质量复盘、知识缺口不再直达 `#reviews`、`#outbox`、`#conversations`、`#tickets` | 后续只能从客户页进入 `#live`、`#gaps`、`#evals`、`#channels` 等正式工作页 |
| 知识运营 | 核心新增/导入/缺口/评测链路多数有真实 API 和后端落库 | H2W3B 已把客户可见入口收束为知识运营四步维护流程，并将“编辑知识草稿”改为“导入知识文档” |
| 知识评测 | 当前是发布前检查、检索回归和人工事实性标签，不是完整线上客服准确率 | 禁止把评测命中率包装为完整准确率；线上准确率必须等真实回执和抽检闭环完成 |

## 0.1 P3-06U-26H2W3B 知识运营收束记录

本轮只收束客户可见知识运营入口，不改后端知识模型、不打开真实外发、不重写生产级 RAG：

| 项目 | 当前结论 | 验收方式 |
|---|---|---|
| 知识运营四步维护流程 | 客户可见首屏只保留业务对象、标准问答、流程政策、禁用承诺与转人工规则四步 | `data-h2w3b-customer-knowledge-flow="true"` |
| 重复流程卡 | 旧 `knowledge-update-path` 已移除，避免四层知识中心和更新路径重复解释 | H2W3B 静态门禁禁止 `.knowledge-update-path` |
| 文档导入入口 | “编辑知识草稿”改为“导入知识文档”；文档启用仍通过“发布前样题试跑 / 确认发布版本”完成 | 前端文案和按钮仍复用真实 `createKnowledgeDocument`、`publish-checks`、`publication` |
| 自动回复策略语言 | “自动回复状态机 / AI 回复预案”改为“自动回复处理方式 / 回复草稿 / 转人工” | H2W3B 静态门禁禁止旧文案 |
| 真实性边界 | 知识发布只影响本地检索和版本记录，不承诺真实渠道发送或完整线上客服准确率 | 文档、矩阵和页面继续保留真实外发关闭边界 |

本轮验收：

```bash
npm run typecheck
npm run build
node scripts/check_p3_06u_26h2v_console_ia_alignment.mjs
node scripts/check_p3_06u_10b_conversation_workbench_simplification.mjs
node scripts/audit_p3_06u_26h2w3_frontend_clicks_and_ux.mjs
```

结果：类型检查通过、构建通过、H2V 通过、10B 通过、逐页点击深审 `Issues: 0`。

## 0.2 P3-06U-26H2W3C 客户资料整理记录

本轮只补客户资料进入知识资料包检查的第一片，不新增真实外发、不调用模型、不自动解析 PDF/DOCX/XLSX：

| 项目 | 当前结论 | 验收方式 |
|---|---|---|
| 客户资料整理 | 知识库运营页新增表格模板、CSV 下载和“生成资料包”动作 | `data-h2w3c-customer-intake="true"` |
| CSV 模板转换 | CSV 模板转换成 `wanfa.knowledge_update_package.v1`，写入现有知识资料包内容区 | `buildCustomerKnowledgeUpdatePackageFromCsv` |
| 真实检查链路 | 转换后仍需点击“检查资料包”，复用现有资料包预检 API | `previewKnowledgeUpdatePackage` |
| 文件格式边界 | PDF/DOCX/XLSX 暂不自动解析，只作为来源留档或人工整理后导入 | 页面和文档明确写出“不自动解析入库” |
| 启用边界 | 导入不等于启用，仍需发布前样题试跑和确认发布版本 | 发布流程仍由 `publish-checks` / `publication` 承接 |

## 0.3 P3-06U-26H2W3D 线上回执闭环记录

本轮只补质量复盘里的“线上回执链路覆盖”第一片，不打开真实外发，不接真实平台发送，不把回执送达率包装成完整客服答案准确率：

| 项目 | 当前结论 | 验收方式 |
|---|---|---|
| 线上回执汇总接口 | 新增 `GET /api/tenants/{tenant_id}/online-receipt-quality-summary`，按租户统计回执入库、匹配、签名验证、送达、失败复盘和平台分布 | 后端单测 `test_online_receipt_quality_summary_is_bounded_and_does_not_claim_full_accuracy` |
| 质量页证据区 | 质量复盘页新增“线上回执闭环证据”，展示回执链路覆盖和验收门禁 | `data-h2w3d-online-receipt-quality="p3-06u-26h2w3d"` |
| 准确率边界 | 页面明确当前是回执链路覆盖，不是完整客服答案准确率 | 页面与文档必须出现“不展示完整线上准确率” |
| 安全边界 | 接口不返回 raw payload，不调用模型，不产生外部平台写入 | `raw_payload_included=false`、`customer_accuracy_completed=false`、`external_platform_write_performed=false` |
| 后续接法 | 真实企微/公众号等官方回执后续只需要映射到同一回执表和归一层 | 当前不做真实渠道验收 |

## 0.4 P3-06U-26H2W4 报告导出与归档记录

本轮只补客户质量报告的 HTML/XLSX/DOCX 导出和本地审计归档，不做 PDF，不做正式电子签章，不打开真实外发：

| 项目 | 当前结论 | 验收方式 |
|---|---|---|
| HTML 留档 | 质量复盘页可下载 HTML 客户报告，导出后写入本地审计归档 | `data-h2w4-report-export="p3-06u-26h2w4"` |
| XLSX 明细 | 质量复盘页可下载 XLSX 明细表，后端生成有效 OpenXML zip 文件 | 后端单测用 `zipfile.ZipFile` 验证 |
| DOCX 报告 | 质量复盘页可下载 DOCX 客户报告，后端生成有效 OpenXML zip 文件 | 后端单测用 `zipfile.ZipFile` 验证 |
| 报告归档 | 质量复盘页可查看历史导出归档，显示格式、文件名、周期、hash、大小和审计号 | `data-h2w4-report-archives="p3-06u-26h2w4"` |
| 历史下载 | 历史归档下载走 `downloadCustomerQualityReportArchive`，不是前端假按钮 | `GET /api/tenants/{tenant_id}/customer-quality-report/archives/{archive_event_id}/download` |
| 签章边界 | 页面和文档明确“不是正式电子签章” | H2W4 静态门禁 |

## 0.5 P3-06U-26H2W5 云接收台第一片记录

本轮只补本地模拟售后接收台，不上线正式云服务，不做自动上传，不远程控制客户电脑：

| 项目 | 当前结论 | 验收方式 |
|---|---|---|
| 售后接收台 | 账号安全页新增“售后接收台”，用于粘贴客户主动提供的授权上传包 JSON | `data-h2w5-cloud-intake="p3-06u-26h2w5"` |
| 登记接收 | 前端调用 `createDiagnosticIntakeRecord`，后端写入 `diagnostic_intake_records` | `POST /api/tenants/{tenant_id}/diagnostic-intake-records` |
| 校验拒收 | 后端校验授权记录、上传包版本、安全声明和诊断包 sha256；失败写入 `rejected` 和拒收原因 | `test_diagnostic_intake_rejects_tampered_or_unsafe_package` |
| 接收记录 | 前端调用 `listDiagnosticIntakeRecords` 展示包名、摘要、大小、状态和拒收原因 | `GET /api/tenants/{tenant_id}/diagnostic-intake-records` |
| 下载包 | 历史包下载走后端 `downloadDiagnosticIntakeRecord`，不是前端假按钮 | `GET /api/tenants/{tenant_id}/diagnostic-intake-records/{record_id}/download` |
| 状态处理 | 负责人/管理员可标记处理中或已处理，写入审计 | `PATCH /api/tenants/{tenant_id}/diagnostic-intake-records/{record_id}` |
| 运维边界 | 页面明确客户主动授权、脱敏包校验、不远控客户电脑、不自动联网采集 | H2W5 静态门禁 |

## 1. 判定标准

| 状态 | 是否允许进入客户版 | 判定标准 |
|---|---|---|
| 真实可用 | 允许 | 有前端动作、API client、后端接口、权限、数据变化或审计、成功/失败反馈和 smoke 证据 |
| 只读可用 | 允许 | 只读取真实服务端数据或明确的本地兜底数据，不暗示可写 |
| 禁用合理 | 允许 | 控件存在但不可操作，有清楚禁用原因，不会让人误解为功能已完成 |
| 应隐藏 | 允许但必须已隐藏 | 后端能力缺失或流程未设计完整，不进入客户可见主界面 |
| 仅前端 | 不允许 | 只有 UI，没有真实动作；必须接动作、禁用或隐藏 |
| 仅后端 | 不对客户宣传 | 后端已存在但前端未接入，不能作为客户可见承诺 |

## 2. 功能真实性明细

| 页面 | 区域 | 控件名称 | 控件类型 | 当前可见角色 | 前端文件 | 前端动作 | API client | 后端接口 | 数据变化 | 权限要求 | 成功反馈 | 失败反馈 | 当前状态 | 处理结论 | 验收证据 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 多渠道对话台 | 顶部工具栏 | 刷新队列 | 按钮 | 负责人、管理员、坐席 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | `onRefresh` | `listConversationInbox` | `GET /api/tenants/{tenant_id}/conversation-inbox` | 读取会话列表 | `conversation.read` | 队列重新加载 | 无 token 或接口失败显示状态 | 真实可用 | 保留 | H2W/H2W0 静态和浏览器 smoke |
| 多渠道对话台 | 会话列表 | 搜索客户/聊天记录 | 输入框 | 负责人、管理员、坐席 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | 本地过滤当前页会话 | 无 | 无 | 仅前端筛选当前页 | 登录后可见 | 列表即时过滤 | 空结果显示暂无会话 | 只读可用 | 保留，矩阵注明当前页过滤 | H2W0 浏览器 smoke |
| 多渠道对话台 | 队列筛选 | 全部 | 按钮 | 负责人、管理员、坐席 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | `setActiveQueue("all")` | 无 | 无 | 仅切换本地队列视图 | 登录后可见 | 列表切换 | 无匹配显示空状态 | 只读可用 | 保留 | H2W0 浏览器 smoke |
| 多渠道对话台 | 队列筛选 | 我的 | 按钮 | 负责人、管理员、坐席 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | `setActiveQueue("mine")` | 无 | 无 | 仅切换本地队列视图 | 登录后可见 | 列表切换 | 无匹配显示空状态 | 只读可用 | 保留 | H2W0 浏览器 smoke |
| 多渠道对话台 | 队列筛选 | 转人工 | 按钮 | 负责人、管理员、坐席 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | `setActiveQueue("needs_review")` | 无 | 无 | 仅切换本地队列视图 | 登录后可见 | 列表切换到人工接管信号 | 无匹配显示空状态 | 只读可用 | 保留 | H2W0 浏览器 smoke |
| 多渠道对话台 | 会话列表 | 选择会话 | 按钮 | 负责人、管理员、坐席 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | `onSelectConversation` | 会话列表来自 `listConversationInbox` | `GET /api/tenants/{tenant_id}/conversation-inbox` | 更新当前选中会话 | `conversation.read` | 右侧消息流切换 | 空数据显示暂无会话 | 真实可用 | 保留 | H2W0 浏览器 smoke |
| 多渠道对话台 | 头部状态 | 真实外发关闭 | 状态文本 | 负责人、管理员、坐席 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | 无交互 | 无 | 无 | 无写入 | 无 | 明确当前边界 | 不适用 | 只读可用 | 保留 | 静态脚本检查 `data-function-reality` |
| 多渠道对话台 | 顶部操作 | 历史记录 | 按钮 | 不可见 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | 已移除 | 无 | 后端详情接口存在但前端未接抽屉 | 无 | 无 | 不展示 | 不展示 | 应隐藏 | 已隐藏，后续单独做历史抽屉 | H2W0 静态脚本禁止 `chat-head-action` |
| 多渠道对话台 | 顶部操作 | 设为星标 | 按钮 | 不可见 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | 已移除 | 无 | 无星标字段 | 无 | 无 | 不展示 | 不展示 | 应隐藏 | 已隐藏 | H2W0 静态脚本禁止 `设为星标` |
| 多渠道对话台 | 顶部操作 | 转接 | 按钮 | 不可见 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | 已移除 | `applyConversationWorkflowAction` 可支持 | `POST /api/conversations/{id}/workflow-actions` | 后续需目标人员/团队 | `conversation.manage` | 不展示 | 不展示 | 应隐藏 | 已隐藏，待目标选择器后再开放 | H2W0 静态脚本禁止裸露 `转接` 按钮 |
| 多渠道对话台 | 顶部操作 | 结束 | 按钮 | 不可见 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | 已移除 | `applyConversationWorkflowAction` 可支持 | `POST /api/conversations/{id}/workflow-actions` | 后续可写会话状态与审计 | `conversation.manage` | 不展示 | 不展示 | 应隐藏 | 已隐藏，待确认弹窗和状态刷新后再开放 | H2W0 静态脚本禁止 `chat-head-action` |
| 多渠道对话台 | 底部工具 | 表情 | 按钮 | 不可见 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | 已移除 | 无 | 无 | 无 | 无 | 不展示 | 不展示 | 应隐藏 | 已隐藏 | H2W0 静态脚本禁止 `composer-tool-button` |
| 多渠道对话台 | 底部工具 | 发送图片 | 按钮 | 不可见 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | 已移除 | 无 | 无附件上传模型 | 无 | 无 | 不展示 | 不展示 | 应隐藏 | 已隐藏 | H2W0 静态脚本禁止 `发送图片` |
| 多渠道对话台 | 底部工具 | 添加附件 | 按钮 | 不可见 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | 已移除 | 无 | 无附件上传模型 | 无 | 无 | 不展示 | 不展示 | 应隐藏 | 已隐藏 | H2W0 静态脚本禁止 `添加附件` |
| 多渠道对话台 | 底部输入区 | 回复内容 | 输入框 | 负责人、管理员、坐席 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | `setEditableDraft` | 无 | 无 | 仅本地编辑待保存文本 | 登录后可见；非转人工禁用 | 转人工时可输入 | 无人工接管时禁用并展示占位 | 禁用合理 | 保留 | H2W0 浏览器 smoke |
| 多渠道对话台 | 底部输入区 | 保存接管回复 | 按钮 | 负责人、管理员、坐席 | `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | `onApproveReviewDraft` | 人审批准接口由父组件接入 | 人审任务批准接口 | 写入人审处理结果，不代表外部发送 | `human_review.approve` 或管理权限 | 按钮可用时提交本地接管回复 | 无 token、无权限、非转人工、空内容时禁用 | 真实可用 | 保留，文案不再写发送 | H2W0 静态和浏览器 smoke |
| 知识库运营 | 业务对象 | 新增业务对象 | 表单按钮 | 负责人、管理员 | `frontend/src/App.tsx` | 业务对象表单提交 | `createBusinessObject` | `POST /api/tenants/{tenant_id}/business-objects` | 新增业务对象 | `knowledge.manage` | 列表刷新 | 字段错误或权限错误显示状态 | 真实可用 | 保留 | H2W0 知识操作真实浏览器门禁 + 服务端持久化验证 |
| 知识库运营 | 业务对象 | 编辑业务对象 | 表单按钮 | 负责人、管理员 | `frontend/src/App.tsx` | 选中对象后载入表单并提交更新 | `updateBusinessObject` | `PATCH /api/business-objects/{business_object_id}` | 更新业务对象、别名和审计 | `knowledge.manage` | 列表刷新并显示更新后的对象名称 | 字段错误或权限错误显示状态 | 真实可用 | 保留 | H2W0 知识操作真实浏览器门禁 + 服务端持久化验证 |
| 知识库运营 | 标准问答 | 新增问答卡 | 表单按钮 | 负责人、管理员 | `frontend/src/App.tsx` | 问答卡表单提交 | `createObjectKnowledgeCard` | `POST /api/business-objects/{business_object_id}/knowledge-cards` | 新增对象问答卡 | `knowledge.manage` | 列表刷新 | 字段错误或权限错误显示状态 | 真实可用 | 保留 | H2W0 知识操作真实浏览器门禁 + 服务端持久化验证 |
| 知识库运营 | 知识文档 | 新增知识文档 | 表单按钮 | 负责人、管理员 | `frontend/src/App.tsx` | 文档表单提交 | `createKnowledgeDocument` | `POST /api/tenants/{tenant_id}/knowledge-documents` | 新增文档和分块 | `knowledge.manage` | 文档列表刷新 | 字段错误或权限错误显示状态 | 真实可用 | 保留 | H2W0 知识操作真实浏览器门禁 + 服务端持久化验证 |
| 知识库运营 | 客户资料整理 | CSV 模板转换 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | CSV 转为知识资料包内容 | 无，转换后复用检查接口 | 无直接写入 | 仅生成本地资料包草稿 | 登录后推荐使用，未登录也可下载模板 | 下方资料包内容区更新，提示继续检查 | 空模板提示补充内容 | 只读可用 | 保留，不能包装成直接导入 | H2W3C 静态门禁 |
| 知识库运营 | 客户资料整理 | 下载 CSV 模板 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | 下载当前模板文本 | 无 | 无 | 无写入 | 无 | 下载本地 CSV 文件 | 浏览器下载失败由系统提示 | 只读可用 | 保留 | H2W3C 静态门禁 |
| 知识库运营 | 客户资料整理 | PDF/DOCX/XLSX 资料 | 状态说明 | 负责人、管理员 | `frontend/src/App.tsx` | 无自动解析动作 | 无 | 无 | 无写入 | 无 | 明确只做来源留档或人工整理 | 不适用 | 禁用合理 | 不做自动解析承诺 | H2W3C 静态门禁 |
| 知识库运营 | 知识资料包 | 检查资料包 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | 读取资料包内容并检查 | `previewKnowledgeUpdatePackage` | `POST /api/tenants/{tenant_id}/knowledge-update-package/previews` | 只读检查，不落库 | `knowledge.manage` | 展示新增、跳过、错误 | 内容格式错误或接口失败显示状态 | 真实可用 | 保留 | H2W0 知识操作真实浏览器门禁 + 检查结果截图 |
| 知识库运营 | 知识资料包 | 导入资料包 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | 提交资料包内容 | `importKnowledgeUpdatePackage` | `POST /api/tenants/{tenant_id}/knowledge-update-package-imports` | 写入知识对象、问答卡、文档、题集和审计 | `knowledge.manage` | 展示导入结果和批次 | 检查错误或权限错误阻断 | 真实可用 | 保留 | H2W0 知识操作真实浏览器门禁 + 服务端持久化验证 |
| 知识缺口 | 服务端筛选 | 关键词/状态/严重度/来源 | 表单控件 | 负责人、管理员 | `frontend/src/App.tsx` | 更新筛选参数并请求列表 | `listKnowledgeGaps` | `GET /api/tenants/{tenant_id}/knowledge-gaps` | 读取服务端筛选结果 | `knowledge.manage` | 列表和分页刷新 | 接口失败显示状态 | 真实可用 | 保留 | H2G5 验收 + H2W3A 浏览器 smoke |
| 知识缺口 | 修复动作 | 生成知识草稿 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | `onCreateKnowledgeGapDraft` | `createKnowledgeGapDocumentDraft` | `POST /api/knowledge-gaps/{id}/document-drafts` | 创建知识文档草稿 | `knowledge.manage` | 关联草稿和状态刷新 | 权限或数据错误显示状态 | 真实可用 | 保留 | H2W3A 静态矩阵 |
| 知识缺口 | 回归动作 | 加入回归题 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | `onCreateKnowledgeGapRegressionCase` | `createKnowledgeGapRegressionCase` | `POST /api/knowledge-gaps/{id}/regression-cases` | 创建评测用例 | `knowledge.manage` | 关联题目和状态刷新 | 权限或数据错误显示状态 | 真实可用 | 保留 | H2W3A 静态矩阵 |
| 知识评测 | 评测集 | 新建评测集 | 表单按钮 | 负责人、管理员 | `frontend/src/App.tsx` | 表单提交 | `createKnowledgeEvaluationSet` | `POST /api/tenants/{tenant_id}/knowledge-evaluation-sets` | 新增评测集与用例 | `knowledge.manage` | 评测集列表刷新 | 字段错误或权限错误显示状态 | 真实可用 | 保留 | H2W0 静态矩阵 |
| 知识评测 | 运行评测 | 运行回归评测 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | 触发评测运行 | `runKnowledgeEvaluationSet` | `POST /api/knowledge-evaluation-sets/{id}/runs` | 生成评测运行结果 | `knowledge.manage` | 展示命中、引用、缺口 | 接口失败显示状态 | 真实可用 | 保留，文案限定为评测不是完整准确率 | H2W0 静态和浏览器 smoke |
| 知识评测 | 人工标签 | 标注事实性 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | 提交人工事实性标签 | `labelKnowledgeEvaluationRunCaseFactuality` | `POST /api/knowledge-evaluation-runs/{run_id}/cases/{case_id}/factuality-label` | 写入标签摘要 | `knowledge.manage` | 月度质量复盘可聚合 | 权限或字段错误显示状态 | 真实可用 | 保留 | H2N 验收 |
| 运营总览 | 时间范围 | 今日/近七天/近三十天 | 按钮 | 负责人、管理员、只读账号 | `frontend/src/App.tsx` | 更新 overview filter | `getOpsMetricsDashboard` 或本地兜底 | `GET /api/tenants/{tenant_id}/ops/metrics` | 读取聚合指标 | `dashboard.read` | 图表和口径证明更新 | 失败展示本地兜底说明 | 只读可用 | 保留，必须展示口径证明 | H2V/H2W0 浏览器 smoke |
| 运营总览 | 渠道筛选 | 全部渠道/单渠道 | 按钮 | 负责人、管理员、只读账号 | `frontend/src/App.tsx` | 更新渠道过滤 | `getOpsMetricsDashboard` 或本地兜底 | `GET /api/tenants/{tenant_id}/ops/metrics` | 读取聚合指标 | `dashboard.read` | 图表和口径证明更新 | 失败展示本地兜底说明 | 只读可用 | 保留 | H2V/H2W0 浏览器 smoke |
| 质量复盘 | 月度报告 | 生成/刷新质量报告 | 按钮 | 负责人、管理员 | `frontend/src/components/quality/QualityReviewPanel.tsx` | 请求报告数据 | 质量报告相关 client | 质量复盘 API | 读取聚合报告 | `quality.read` | 报告更新 | 接口失败显示状态 | 真实可用 | 保留 | H2Q/H2W0 矩阵 |
| 质量复盘 | 线上回执闭环证据 | 查看回执链路覆盖 | 只读卡片 | 负责人、管理员、只读账号 | `frontend/src/components/quality/QualityReviewPanel.tsx` | 读取线上回执汇总 | `getOnlineReceiptQualitySummary` | `GET /api/tenants/{tenant_id}/online-receipt-quality-summary` | 读取回执入库、匹配、签名验证、失败复盘和平台分布 | `quality.read` | 展示回执链路覆盖、平台分布和门禁 | 接口失败显示状态，不展示完整准确率 | 只读可用 | 保留，必须注明不是完整客服答案准确率 | P3-06U-26H2W3D 静态门禁和后端单测 |
| 质量复盘 | 报告导出 | HTML 留档 | 按钮 | 负责人、管理员 | `frontend/src/components/quality/QualityReviewPanel.tsx` | 下载 HTML 报告 | `exportCustomerQualityReport(format=html)` | `GET /api/tenants/{tenant_id}/customer-quality-report/export?format=html` | 导出 HTML 文件并写审计归档 | `quality.read` | 下载留档件并刷新报告归档 | 导出失败显示状态 | 真实可用 | 保留，不是正式电子签章 | H2W4 静态门禁 + 后端测试 |
| 质量复盘 | 报告导出 | XLSX 明细 | 按钮 | 负责人、管理员 | `frontend/src/components/quality/QualityReviewPanel.tsx` | 下载 XLSX 明细 | `exportCustomerQualityReport(format=xlsx)` | `GET /api/tenants/{tenant_id}/customer-quality-report/export?format=xlsx` | 导出 XLSX OpenXML 文件并写审计归档 | `quality.read` | 下载明细表并刷新报告归档 | 导出失败显示状态 | 真实可用 | 保留，文件不包含原始问题或完整回复 | H2W4 静态门禁 + 后端 zip 校验 |
| 质量复盘 | 报告导出 | DOCX 报告 | 按钮 | 负责人、管理员 | `frontend/src/components/quality/QualityReviewPanel.tsx` | 下载 DOCX 报告 | `exportCustomerQualityReport(format=docx)` | `GET /api/tenants/{tenant_id}/customer-quality-report/export?format=docx` | 导出 DOCX OpenXML 文件并写审计归档 | `quality.read` | 下载客户报告并刷新报告归档 | 导出失败显示状态 | 真实可用 | 保留，不是正式电子签章 | H2W4 静态门禁 + 后端 zip 校验 |
| 质量复盘 | 报告归档 | 查看报告归档 | 只读列表 | 负责人、管理员、只读账号 | `frontend/src/components/quality/QualityReviewPanel.tsx` | 读取导出审计归档 | `listCustomerQualityReportArchives` | `GET /api/tenants/{tenant_id}/customer-quality-report/archives` | 读取历史导出记录 | `quality.read` | 展示格式、文件名、周期、hash、大小和审计号 | 接口失败显示状态 | 真实可用 | 保留，归档不是签章 | H2W4 静态门禁 |
| 质量复盘 | 报告归档 | 下载历史归档 | 按钮 | 负责人、管理员、只读账号 | `frontend/src/components/quality/QualityReviewPanel.tsx` | 下载历史报告文件 | `downloadCustomerQualityReportArchive` | `GET /api/tenants/{tenant_id}/customer-quality-report/archives/{archive_event_id}/download` | 读取审计归档中的文件体 | `quality.read` | 下载历史文件 | 文件不存在或接口失败显示状态 | 真实可用 | 保留，不能用于正式电子签章 | H2W4 静态门禁 |
| 质量复盘 | 客户确认 | 记录客户确认 | 按钮 | 负责人 | `frontend/src/components/quality/QualityReviewPanel.tsx` | 提交确认记录 | 客户确认记录 client | 客户确认记录 API | 写审计事件 | `accounts.manage` | 最近确认记录刷新 | 无权限或字段错误显示状态 | 真实可用 | 保留，文案不是电子签章 | H2T/H2U 验收 |
| 渠道接入 | 分层切换 | 账号与入口/企业微信步骤/其它官方平台/接入边界 | 按钮 | 负责人、管理员 | `frontend/src/components/channels/ChannelConnectorCenterPanel.tsx` | 本地切换分层 | 无 | 无 | 只切换页面层 | 登录后可见 | 分层内容显示 | 无 | 只读可用 | 保留 | H2V/H2W0 浏览器 smoke |
| 渠道接入 | 渠道账号 | 新增/编辑渠道账号 | 表单按钮 | 负责人、管理员 | `frontend/src/components/channels/ChannelConnectorCenterPanel.tsx` | 表单提交 | `createChannelAccount`/`updateChannelAccount` | `POST/PATCH /api/tenants/{tenant_id}/channel-accounts` | 写入渠道账号配置 | `channels.manage` | 列表刷新 | 权限或字段错误显示状态 | 真实可用 | 保留 | H2C 验收 |
| 渠道接入 | 官方平台状态 | 官方授权说明 | 状态卡 | 负责人、管理员、只读账号 | `frontend/src/components/channels/ChannelConnectorCenterPanel.tsx` | 无交互 | 无 | 无 | 无写入 | 无 | 显示未接入、待授权、真实外发关闭 | 不适用 | 只读可用 | 保留，不能写成已接通 | H2W0 静态脚本 |
| 运维与告警 | 只读健康 | 刷新运维状态 | 按钮 | 负责人、管理员、只读账号 | `frontend/src/App.tsx` | 刷新 worker/告警/指标 | 运维相关 client | 运维只读 API | 读取健康状态 | `ops.metrics.read` | 状态刷新 | 接口失败显示状态 | 只读可用 | 保留 | H2V/H2W0 浏览器 smoke |
| 自动回复策略 | 策略展示 | 查看策略和成本边界 | 状态/按钮 | 负责人、管理员 | `frontend/src/App.tsx` | 切换策略视图或刷新 | `listReplyDecisions` 等 | 回复决策/策略相关 API | 读取策略和决策 | `reply.read` 或管理权限 | 策略状态展示 | 接口失败显示状态 | 只读可用 | 保留，客户语言为自动回复策略 | H2W0 浏览器 smoke |
| 模型路由 | 检索与成本治理 | 刷新治理状态 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | `refreshRagCostGovernance` | `getRagCostGovernanceSummary` | `GET /api/tenants/{tenant_id}/rag-cost-governance-summary` | 读取知识规模、向量配置、最近评测、provider smoke、自动回复策略和成本门禁 | `ops.metrics.read` | 治理状态、门禁和下一步刷新 | 无权限或接口失败显示状态 | 只读可用 | 保留；不是完整模型成本报表，不触发模型调用和真实外发 | P3-06U-26H2W7 后端测试 + 静态门禁 |
| 模型路由 | 生产检索准备度 | 查看生产级检索缺口 | 只读卡片 | 负责人、管理员 | `frontend/src/App.tsx` | 展示后端返回门禁 | `getRagCostGovernanceSummary` | `GET /api/tenants/{tenant_id}/rag-cost-governance-summary` | 无写入 | `ops.metrics.read` | 展示通过、待加强、阻断 | 无数据时提示未读取 | 只读可用 | 保留；当前模型调用成本记录缺口必须可见 | P3-06U-26H2W7/NC5 后端测试 + 静态门禁 |
| 账号安全 | 账号列表 | 刷新账号 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | 请求账号列表 | 账号治理 client | 账号列表 API | 读取账号列表 | `accounts.manage` | 列表刷新 | 权限或接口错误显示状态 | 真实可用 | 保留 | H2B 验收 |
| 账号安全 | 账号治理 | 新增人员/启停/重置密码 | 表单/按钮 | 负责人 | `frontend/src/App.tsx` | 调用账号治理 handler | 账号治理 client | 账号治理 API | 写账号、撤销会话、写审计 | `accounts.manage` | 列表刷新和状态反馈 | 最后负责人保护、权限错误显示 | 真实可用 | 保留 | H2B 验收 |
| 账号安全 | 售后接收台 | 生成处理单 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | `handleCreateDiagnosticRemediationRequest` | `createDiagnosticRemediationRequest` | `POST /api/tenants/{tenant_id}/diagnostic-intake-records/{record_id}/remediation-requests` | 从已通过校验的接收记录生成售后处理单 | `updates.manage` | 处理单列表新增记录 | 拒收记录不可生成；权限错误显示状态 | 真实可用 | 保留；不是自动更新器 | P3-06U-26H2W6 静态门禁 + 后端测试 |
| 账号安全 | 售后接收台 | 下载回传包 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | `handleDownloadDiagnosticRemediationRequest` | `downloadDiagnosticRemediationRequest` | `GET /api/tenants/{tenant_id}/diagnostic-remediation-requests/{request_id}/download` | 下载处理建议 JSON 回传包 | `updates.manage` | 下载本地 JSON 文件 | 权限或记录不存在显示状态 | 真实可用 | 保留；不能写成已应用更新 | P3-06U-26H2W6 静态门禁 + 后端测试 |
| 账号安全 | 售后接收台 | 待客户确认 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | `handleUpdateDiagnosticRemediationRequest` | `updateDiagnosticRemediationRequest` | `PATCH /api/tenants/{tenant_id}/diagnostic-remediation-requests/{request_id}` | 更新处理单状态 | `updates.manage` | 状态刷新为待客户确认 | 权限或状态错误显示状态 | 真实可用 | 保留；不代表客户环境已写入 | P3-06U-26H2W6 静态门禁 + 后端测试 |
| 账号安全 | 售后接收台 | 生成受控更新计划 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | `handleCreateDiagnosticRemediationUpdatePlan` | `createDiagnosticRemediationUpdatePlan` | `POST /api/tenants/{tenant_id}/diagnostic-remediation-requests/{request_id}/signed-update-plan` | 处理单绑定同租户签名更新包，写入 `signed_update_control_plan` 和审计事件 | `updates.manage` | 处理单状态刷新为已生成更新计划 | 无暂存更新包、无权限或记录不存在显示状态 | 真实可用 | 保留；只生成计划，不自动应用 | P3-06U-26H2W6B 静态门禁 + 后端测试 |
| 账号安全 | 售后接收台 | 刷新受控更新计划 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | `handleCreateDiagnosticRemediationUpdatePlan` | `createDiagnosticRemediationUpdatePlan` | `POST /api/tenants/{tenant_id}/diagnostic-remediation-requests/{request_id}/signed-update-plan` | 读取签名更新包最新状态，刷新应用、回滚和备份摘要 | `updates.manage` | 计划步骤刷新为暂存、已应用或已回滚 | 无权限或更新包不存在显示状态 | 真实可用 | 保留；应用和回滚仍在签名更新中心手动执行 | P3-06U-26H2W6B 静态门禁 + 后端测试 |
| 知识库运营 | 知识维护总流程 | 生成资料包 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | `applyCustomerKnowledgeIntakePackage` | 无，转换后进入资料包内容区 | 无直接写入 | 仅把客户 CSV 模板转换为本地资料包草稿 | 登录后推荐使用 | 下方资料包内容区和状态提示更新 | 空模板提示补充内容 | 只读可用 | 保留；不是直接导入 | H2W-11D/H2W-11F 静态门禁 |
| 知识库运营 | 知识维护总流程 | 检查资料包 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | `onPreviewUpdatePackage` | `previewKnowledgeUpdatePackage` | `POST /api/tenants/{tenant_id}/knowledge-update-package/previews` | 只读检查，不落库 | `knowledge.manage` | 展示新增、跳过、错误和可应用状态 | 格式错误、权限或接口失败显示状态 | 真实可用 | 保留 | H2W-11D/H2W-11F 静态门禁 + H2W0 owner-login 知识操作 smoke |
| 知识库运营 | 知识维护总流程 | 导入知识库 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | `onImportUpdatePackage` | `importKnowledgeUpdatePackage` | `POST /api/tenants/{tenant_id}/knowledge-update-package-imports` | 写入业务对象、问答卡、文档、题集和导入批次 | `knowledge.manage` | 展示导入批次和操作结果 | 检查错误、权限或接口失败显示状态 | 真实可用 | 保留；导入不等于启用 | H2W-11D/H2W-11F 静态门禁 + H2W0 owner-login 知识操作 smoke |
| 知识库运营 | 知识维护总流程 | 启用前复测 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | `onCheckPublishDocument(firstReadyDocument)` | 发布门禁 client | `POST /api/knowledge-documents/{document_id}/publish-checks` | 写入发布前检查记录 | `knowledge.manage` | 展示发布门禁记录 | 无可发布文档时禁用 | 真实可用 | 保留；不是完整线上准确率 | H2W-11D/H2W-11F 静态门禁 |
| 知识库运营 | 知识维护总流程 | 启用知识 | 按钮 | 负责人、管理员 | `frontend/src/App.tsx` | `onPublishDocument(firstReadyDocument)` | 发布 client | `POST /api/knowledge-documents/{document_id}/publication` | 文档进入 active 检索范围并写发布记录 | `knowledge.manage` | 文档启用、版本记录刷新 | 未索引、非草稿、门禁失败或权限错误阻断 | 真实可用 | 保留；真实外发继续关闭 | H2W-11D/H2W-11F 静态门禁 |
| 知识库运营 | 知识维护总流程 | 查看复测题库 | 链接 | 负责人、管理员 | `frontend/src/App.tsx` | `href="#evals"` | 无 | 无 | 切换到知识评测页 | 登录后可见 | 跳转到评测页 | 不适用 | 只读可用 | 保留；评测不是完整线上准确率 | H2W-11D/H2W-11F 静态门禁 |
| 知识库运营 | 知识维护总流程 | 查看质量报告 | 链接 | 负责人、管理员 | `frontend/src/App.tsx` | `href="#quality"` | 质量报告 client 由质量页读取 | 质量报告 API | 切换到质量复盘页 | `quality.read` | 跳转到质量报告与客户确认入口 | 不适用 | 只读可用 | 保留；本地确认不是正式验收 | H2W-11D/H2W-11F 静态门禁 |
| 跨页验收 | 负责人逐页试用 | 负责人真实登录逐页试用 | 浏览器门禁 | 负责人 | `scripts/check_p3_06u_26h2w11e_owner_customer_knowledge_trial.mjs` | 真实登录表单、H2W-11D 动作点击、跨页导航 | 后端 API 读回同租户数据 | 业务对象、知识文档、评测集列表 API | 点击生成资料包、检查资料包、导入知识库后检查服务端落库 | 负责人临时账号 | `summary.json`、7 张截图、服务端计数 | 任一动作不可见、空按钮、未落库或越界文案即失败 | 真实可用 | 保留；不是正式客户验收，不打开真实外发 | H2W-11E owner-login 浏览器验收 |

## 3. 当前阻断项处理结果

| 阻断项 | 处理 |
|---|---|
| 多渠道对话台顶部“历史记录/设为星标/转接/结束”无动作 | 已从客户可见主界面隐藏；后续需要真实抽屉、星标字段、转接目标选择和结束确认后再开放 |
| 多渠道对话台底部“表情/图片/附件”无动作 | 已隐藏；等表情选择器、文件上传、存储和审计模型完成后再开放 |
| “发送”容易暗示真实外发 | 已改为“保存接管回复”，只在转人工场景保存本地接管结果 |
| 知识评测容易被误解为完整准确率 | 矩阵明确当前是评测/回归/人工事实性标签，不等于完整线上准确率 |
| 渠道接入容易被误解为已接通平台 | 矩阵明确当前是官方授权状态展示和配置入口，真实外发继续关闭 |
| 客户可见页面工程词残留 | H2W3A 已通过逐页浏览器深审，`API/sandbox/outbox/connector_noop/P3-06/H2W` 不再出现在客户可见页 |
| 文档导入入口命名已收束 | 已在 H2W3B 改为“导入知识文档”；启用仍通过发布前样题试跑和确认发布版本完成，避免把导入包装成已启用 |

## 4. 后续必须补的功能片

| 后续片 | 前置条件 |
|---|---|
| 会话历史抽屉 | 前端接 `GET /api/conversations/{id}`，展示真实 messages，不读本地假消息 |
| 设为星标 | 后端新增星标字段、接口、审计和列表筛选 |
| 转接会话 | 前端目标人员/团队选择器，后端 `transfer` 写审计并刷新分配状态 |
| 结束会话 | 前端确认弹窗，后端 `resolve` 写状态和审计，列表刷新 |
| 图片/附件 | 上传 API、文件存储、病毒/类型检查、审计和消息附件 schema |
| 真正外发 | 官方授权、白名单、回执、失败重试、审计和 kill switch 全部完成 |
