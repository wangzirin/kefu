# 智能客服路线纠偏与 P3 试点闭环 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 Project_012 的 `standard_ops` 从“评测链路持续加厚”纠偏到“真实客户可感知的智能客服试点闭环”。

**Architecture:** 后续推进采用阶段门禁制：每一轮先做全量进度感知，再选择一个对商用主线有贡献的工程片。评测只作为放行门禁和复盘证据，不再作为无限延伸的主线任务；P2-27 已完成短审查收口，下一步默认进入 P3 真实试点闭环。

**Tech Stack:** FastAPI、SQLAlchemy、Alembic、PostgreSQL/pgvector 目标路径、SQLite 本地验证、React/Vite、知识文档 RAG、百炼/千问模型路由、脱敏评测集、官方渠道 webhook/outbox/copilot 架构。

---

## 2026-07-02 Stage Completion: P3-06U-12G RPA Browser Adapter 抽象第一片

- What changed: 新增 `scripts/lib/rpa_browser_adapters.mjs`，把 RPA 浏览器执行层拆为 `cdp_browser_adapter` 与 `accessibility_browser_adapter`；改造 `scripts/run_p3_06u_12e_rpa_browser_reply_feasibility.mjs`，新增 `RPA_BROWSER_ADAPTER` 与 `RPA_PRINT_ADAPTER_CAPABILITIES`；新增 `scripts/check_p3_06u_12g_rpa_adapter_abstraction.py` 与 `docs/P3-06U-12G_RPA_BROWSER_ADAPTER_ABSTRACTION.md`。
- What was verified: `node --check` 两个 `.mjs` 文件通过；adapter capabilities 输出通过；本地 mock draft-only 通过；`python3 scripts/check_p3_06u_12g_rpa_adapter_abstraction.py` 通过。
- What remains not done: `accessibility_browser_adapter` 仍是 contract-only/fail-closed，不是独立可运行的桌面自动化；没有操作真实抖音页面，没有接抖店/飞鸽/淘宝/拼多多商家后台，没有真实发送。
- Whether this was customer-visible: 对终端客户不可见，但对内部工程推进可见，降低后续真实页 RPA 研究误判风险。
- Whether this was only evaluation: 否。它是 RPA 执行层结构和安全门禁收口。
- Next: P3-06U-12H 单平台真实页面 selector/locator profile 草稿，仍只允许 draft-only、脱敏记录和默认清空草稿。

## 2026-07-02 Stage Completion: P3-06U-12H 单平台真实页面 Locator Profile 草稿

- What changed: 新增 `research/rpa_browser_reply_feasibility/profiles/douyin_web_dm.draft_only.locator_profile.json`、`docs/P3-06U-12H_REAL_PAGE_LOCATOR_PROFILE_DRAFT.md` 和 `scripts/check_p3_06u_12h_real_page_locator_profile.py`，把抖音网页个人私信弹窗研究边界沉淀为 Draft-Only locator profile。
- What was verified: `python3 -m json.tool` 校验 profile 通过；`python3 scripts/check_p3_06u_12h_real_page_locator_profile.py` 通过；隐私关键词扫描未发现真实私聊对象、账号长数字或私聊样本混入 profile/doc。
- What remains not done: 没有操作真实抖音页面，没有自动化 Accessibility adapter，没有点击发送，没有接抖店飞鸽、企业号客服、官方开放平台或任何商家客服后台。
- Whether this was customer-visible: 否。它是内部 RPA 真实页研究资产，用来避免把个人私信 draft-only 探测误写成正式渠道接入。
- Whether this was only evaluation: 否。它新增了可复用 profile、阶段文档和安全门禁，但不产生客户可用自动回复能力。
- Next: P3-06U-12I Operator-Mediated Draft-Only Smoke，或暂停 RPA 真实页面研究转回官方渠道/服务商授权主线。

---

## 0. 为什么新增这份计划

2026-06-27 的多 agent 复盘结论是：当前工程没有方向性跑偏，但已经出现节奏偏移。P2-23 到 P2-26 围绕合成题库、检索评测、报告导出、top-k 对比做了必要的质量底座，但客户可见价值偏低。如果继续沿着“再加一轮评测、再调一轮参数、再导出一轮报告”的惯性走，项目会从“智能客服产品工程”滑成“检索评测实验室”。

因此，后续每轮工程必须同时满足三件事：

1. 先全量感知整体进度，明确已做、未做、当前片的商业价值。
2. 评测只作为阶段门禁，不允许无限尾随在每个阶段后面膨胀。
3. 每个阶段都必须写回 Project_012 项目文档，避免后续线程凭旧状态继续施工。

2026-06-27 追加总控规则：每次工程推进都必须先读本计划，并在动代码、动数据、动接口或写新报告之前填写“工程推进总控卡”。如果本轮只是在同一批合成题上继续加报告、加对比、加导出，而不能说明客户、坐席、运营或交付团队会得到什么新的可见价值，则默认停止，回到 P3 主线。

## 1. 当前真实状态快照

截至 2026-07-01，`standard_ops` 已推进到 P3-06R-03A 坐席工作台一屏闭环前端第一片：

| 板块 | 已有能力 | 仍未完成 |
| --- | --- | --- |
| 账号/RBAC/审计 | 登录、session token hash、角色、团队、P3-06H 中心化命名权限、运维三接口 `require_permission()`、P3-06I 登录和 `/auth/me` 权限快照、审计查询 `audit.events.read` 命名权限、P3-06J 账号/角色/团队 `accounts.manage` owner-only 权限和 bootstrap 保护、P3-06K 会话读写动作 `conversation.read` / `conversation.manage`、P3-06L 知识读写动作 `knowledge.read` / `knowledge.manage`、P3-06M 工单/客户/线索动作 `ticket.*` / `customer.read` / `lead.*`、P3-06N 渠道连接器/回执/发送计划动作 `channel.*` / `outbox.send_plan.manage`、P3-06O 前端按钮级权限第一片、P3-06P outbox draft/dry-run send-attempt/delivery job/failure review 剩余资源权限、P3-06R-02 生产模式 bootstrap 关闭与 foundation/workflow/worker/reply 权限契约收口、前端按权限刷新资源 | 字段脱敏、字段 allowlist、一次性安装 token、生产账号策略 |
| 回复编排 | `ReplyOrchestrator`、workflow、checkpoint、人审任务、P3-03 坐席证据详情、P3-05H 会话收件箱、P3-05I 坐席动作流、P3-05M 工单第一片、P3-05N 线索生成/推进、P3-05O 缺口补知识闭环、P3-05Q 对话台坐席主工作区、P3-05R 质量诊断 BI、P3-05S 知识发布门禁、P3-05T 发布记录/回滚、P3-06A outbox 队列租约、P3-06B 可信入站 worker 租约和运行记录、P3-06C worker heartbeat、P3-06D worker 进程部署、P3-06E 运维健康总览、P3-06F 告警规则第一片、P3-06G 指标出口第一片 | 真实渠道闭环、高级 SLA、工单评论/附件/重开流程、完整主管视图、真实 Prometheus/Grafana 采集、真实告警通知通道、多容器压测 |
| 知识库 | 知识卡片、文档导入、chunk、引用、检索评测 | 真实客户知识包、真实 embedding 质量、生产 ANN query path、复杂文档解析 |
| 模型 | 百炼 smoke、模型路由、deterministic fallback、P3-02 deterministic 草稿事实性 rehearsal | 真实模型答案质量验收、成本治理、provider 日志、模型组合长期策略 |
| 评测 | 80 条合成脱敏题、P2-24/P2-25/P2-26 检索闭环、P2-27 失败题短审查、P3-01 客户式 62 题 rehearsal bank、P3-02 答案事实性 rehearsal | 客户真实 50-100 条脱敏题、人工事实性标签、真实模型幻觉率/事实性评估 |
| 渠道 | connector、webhook、可信入站、outbox、dry-run、失败复盘骨架 | 官方账号 sandbox、真实验签/解密、真实 send API、正式回执 reconciliation |
| 前端 | 登录、人审、待发送、知识文档、评测报表、P3-03 七类队列、会话证据详情、渠道健康概览、P3-05J 对话台/质量、P3-05K 缺口、P3-05M 工单工作区、P3-05N 联系人画像/线索跟进、P3-05O 缺口草稿/回归动作、P3-05Q 对话台主工作区、P3-05R 错因 BI、P3-05S 缺口发布知识动作、P3-05T 文档发布记录卡片、P3-06UI 两级工作域导航、角色化默认入口和管理运维内部 Tab、P3-06G 指标出口面板、P3-06O/P3-06P 关键动作按钮级权限细分、P3-06R-01/P3-06R-01B 壳层滚动和运营总览 BI 第一版、P3-06R-02 前端按权限刷新资源、P3-06R-03A 坐席同屏编辑草稿/内部备注/引用确认/批准进入待发送/确认待发送、P3-06U-01 前后端契约矩阵与客户化导航清理、P3-06U-02 角色化今日任务路径、P3-06U-03 接待工作台三栏 IM 重构、P3-06U-04 运营总览到处理路径打通、P3-06U-05 owner/admin/agent/viewer 真实登录角色 smoke | 字段脱敏、跨渠道身份合并、标签体系、高级 SLA、工单评论/附件/重开流程、团队绩效、完整知识版本 diff、生产级历史聚合、渠道连接器中心、质量复盘 BI |
| 交付 | 本地工程可验证、P3-05B 托管云/私有化/远程维护资料、P3-06D Docker Compose worker service、P3-06E 运维只读健康页、P3-06F 只读告警规则与 runbook、P3-06G 只读指标出口草案 | 真实客户环境部署、备份恢复演练、真实 Prometheus/Grafana 采集、真实告警通知通道、客户试点 SOP |

当前结论：

- 工程底座约 `7/10`。
- 商业可交付度约 `4.5/10`。
- P2-23 到 P2-26 有工程价值，但后续不能继续只做合成评测优化。
- P2-27 已完成 18 道 `outcome=still_missing` 失败题短审查，没有新增评测基础设施。
- P2 合成评测尾巴已经关闭，P3-01 第一片已完成客户式题库和知识包模板，P3-02 第一片已完成 deterministic 答案事实性 rehearsal，P3-03 第一片已完成坐席工作台产品化 v1，P3-04 第一片已完成官网客服沙盒 Copilot 闭环，P3-05A/P3-05B 已完成试点部署准备、对外资料、托管云/私有化/远程维护/readiness smoke，P3-05C 已完成官方渠道自动回复 readiness，P3-05D 已完成渠道测试准备指南，P3-05E 已完成企业微信/微信客服官方 inbound sandbox connector，P3-05H/P3-05I/P3-05J/P3-05K/P3-05M/P3-05N/P3-05O/P3-05Q/P3-05R/P3-05S/P3-05T/P3-06A/P3-06B/P3-06C/P3-06D/P3-06E/P3-06F/P3-06UI/P3-06G/P3-06H/P3-06I/P3-06J/P3-06K/P3-06L/P3-06M/P3-06N/P3-06O/P3-06P 已完成会话收件箱、坐席动作、对话台/质量、知识缺口、工单第一片、联系人画像与线索跟进第一片、缺口到文档草稿与回归题库第一片、对话台主工作区、质量诊断 BI 第一片、知识发布前回归门禁第一片、知识发布记录/回滚第一片、outbox 队列租约/原子抢占第一片、可信入站 worker 租约/运行记录/失败重放第一片、worker heartbeat/受控 loop 第一片、Docker Compose worker service 第一片、前端运维心跳面板第一片、只读告警规则第一片、中台信息架构收口三片、指标出口第一片、RBAC 权限矩阵第一片、RBAC 权限快照/审计权限迁移第二片、账号团队权限/bootstrap 第三片、会话业务动作权限第四片、知识库业务动作权限第五片、工单/客户/线索权限第六片、渠道连接器/回执/发送计划权限第七片、前端按钮级权限第一片和 outbox 剩余资源权限第八片；P3-06R-01/P3-06R-01B/P3-06R-02/P3-06R-03A/P3-06T-01/P3-06T-02/P3-06T-03/P3-06U-01/P3-06U-02/P3-06U-03/P3-06U-04/P3-06U-05 已完成壳层/总览 BI、壳层滚动二次修复、权限契约/前端按权限请求收口、坐席工作台一屏闭环前端第一片、壳层断点返修、首页数据口径、运营总览 BI 重做、前后端契约矩阵、角色化任务路径、接待工作台三栏 IM 重构、运营总览到处理路径打通和真实登录角色 smoke。下一步优先 P3-06U-06 质量复盘 BI；渠道连接器中心、字段脱敏/字段 allowlist 与企业微信公网 HTTPS 回调 smoke 可后续并行。不默认打开真实外发。

## 2. 后续推进总原则

### 2.1 评测是门禁，不是主线

允许做的评测：

- 验证某个工程能力是否可用。
- 防止回归、胡编、错引、越权、外部误发。
- 给真实客户试点提供可追溯证据。

不允许做的评测：

- 在没有真实客户问题和真实知识包时反复优化同一组合成题。
- 只为了让内部指标更好看而新增报告、导出、对比、历史列表。
- 把 `hit_rate`、`full_evidence_recall`、`citation_precision` 当成产品交付本身。
- 用合成题指标替代真实客户 50-100 条问题验收。

### 2.2 每轮推进前必须全量感知进度

每次进入新的工程片，先填写这张表，再动代码：

| 检查项 | 必填内容 |
| --- | --- |
| 当前阶段编号 | 例如 P2-27、P3-01 |
| 上一阶段真实完成 | 写文件、接口、测试、截图、输出路径 |
| 上一阶段没有完成 | 不能承诺的能力 |
| 本阶段客户可见价值 | 客户、坐席、运营、交付团队能感知到什么 |
| 本阶段是否只是评测 | 是/否；如果是，写停止条件 |
| 本阶段外部风险 | 模型付费、真实客户数据、真实平台写入、生产数据库 |
| 验证方式 | 测试命令、smoke、截图、人工复核或来源链接 |
| 写回位置 | 执行记录、关键决策、文件索引、复盘与采坑 |

### 2.3 阶段停止条件

任何评测类阶段满足以下任一条件就必须停止，不再继续加厚：

- 已经回答了本轮工程问题。
- 指标提升小于 `5` 个百分点，且没有发现新的产品风险。
- 新增工作只会产生更多报告，不会带来客户可见能力。
- 需要真实客户问题、真实知识包或真实渠道才能继续判断。

任何渠道类阶段满足以下任一条件必须停止并转人工决策：

- 需要真实平台账号、回调域名、AppSecret、Token、EncodingAESKey。
- 需要打开真实外部发送。
- 需要对真实客户数据做模型调用。
- 需要写生产数据库或部署到公网。

### 2.4 工程推进总控卡

每一轮工程推进必须先把下面这张卡写进当轮 stage 文档、执行记录或工作响应。没有这张卡，不进入实现。

```markdown
## Engineering Control Card

- Stage:
- 当前主线阶段:
- 上一阶段真正完成:
- 上一阶段明确没有完成:
- 本轮要交付的客户可见价值:
- 本轮是否只是评测:
- 如果是评测，本轮问题是什么:
- 如果是评测，停止条件是什么:
- 本轮不做什么:
- 外部风险:
- 需要用户授权的动作:
- 验证方式:
- 写回文件:
- 下一阶段:
```

判定规则：

- 如果“本轮要交付的客户可见价值”写不清，本轮不应该继续。
- 如果“本轮是否只是评测=是”，必须同时写出唯一工程问题和停止条件。
- 如果评测已经回答问题，不允许再自动追加下一轮同类评测。
- 如果需要真实客户数据、真实平台账号、真实模型付费调用或生产数据库动作，必须先停下等待明确授权。
- 每轮结束时必须更新本计划的阶段状态，避免后续线程重复做已经完成的事情。

## 3. 中心工程推进总控

后续工程只围绕一条主线推进：把 `standard_ops` 从“可验证工程底座”推进为“可让首个试点客户日常使用的智能客服中台”。每轮开始时先回答四个问题，再决定是否动代码：

1. 这一轮离客户可用更近了什么。
2. 这一轮解决的是产品闭环、知识闭环、模型闭环、渠道闭环、交付闭环中的哪一个。
3. 上一轮哪些能力已经验证，哪些仍只是 rehearsal、fixture、dry-run 或占位。
4. 本轮评测是否只是阶段门禁；如果是，回答完问题就停止，不自动追加下一轮同类评测。

当前唯一推荐主线：

| 顺序 | 阶段 | 本质目标 | 不能用什么冒充完成 |
| --- | --- | --- | --- |
| 1 | P3-02 事实性 rehearsal | 已完成 deterministic 第一片，证明可对草稿做引用支撑、危险承诺、人审和不确定性门禁 | 不能用检索命中率冒充答案事实性；不能用 mock 冒充真实模型验收 |
| 2 | P3-03 坐席工作台产品化 | 让坐席能处理会话、证据、草稿、人审、待发送、失败和知识缺口 | 不能用工程调试页冒充正式运营台 |
| 3 | P3-04 单渠道 Copilot sandbox | 用一个官方或自有入口跑通入站、AI 建议、人工确认、outbox、回执 | 不能用 connector skeleton 冒充平台真实接通 |
| 4 | P3-05 试点部署包 | 让系统可被另一个人按清单部署、备份、恢复、回滚和复盘 | 不能用本机 dev server 冒充客户交付 |

每轮推进后的写回必须包含一段 `Stage Completion`，并明确写：

- `What changed`：本轮实际改变了什么文件、接口、页面、脚本或数据。
- `What was verified`：跑了什么命令、截图、smoke 或人工复核。
- `What remains not done`：哪些仍不能承诺。
- `Whether this was customer-visible`：客户、坐席、运营或交付团队是否能直接感知。
- `Whether this was only evaluation`：如果只是评测，下一步必须转入产品闭环或等待真实资料。

## 4. 下一阶段路线总览

| 阶段 | 目标 | 预计时间 | 是否允许继续评测 | 交付价值 |
| --- | --- | ---: | --- | --- |
| P2-27 | 18 道 still_missing 失败题短审查 | 已完成 | 已关闭 | P2 合成评测尾巴关闭，P3 知识包修订方向已明确 |
| P3-01 | 真实脱敏 50-100 题与真实知识包模板 | 第一片已完成 | 已完成客户式 rehearsal bank；正式客户题库仍待客户资料 | 把验收材料从合成题转向真实客户式问题 |
| P3-02 | `rag_model_assisted` 事实性与引用评测 | 第一片已完成 | 已完成 deterministic rehearsal；正式客户题库和真实模型验收仍待授权/资料 | 判断模型草稿能否进入安全门禁 |
| P3-03 | 坐席工作台产品化 v1 | 已完成 | 只做 UI/主链 QA | 让客户看到可日常使用的客服中台 |
| P3-04 | 单渠道 Copilot sandbox 闭环 | 已完成 | 只做官方/自有渠道 smoke | 验证官网沙盒入站、AI 建议、人工确认、outbox 和外发门禁 |
| P3-05 | 交付与部署试点包 | 2-3 天 | 做部署验收，不做功能扩散 | 具备给首个试点客户安装/演示/复盘的基础 |

当前中心总结：

1. P2 已经完成“检索质量门禁能跑、证据召回问题能定位、评测报告能脱敏导出”的工程底座。
2. P2 没有完成“真实客户题库、真实知识包、模型生成答案事实性、坐席日常工作台、真实渠道试点和部署交付”。
3. 下一步不是继续给合成题库做更复杂的评测；P3-01 已先建立客户式题库和知识包模板，P3-02 已用 deterministic provider 跑完事实性 rehearsal，P3-03 已完成坐席工作台产品化第一片，P3-04 已完成官网客服沙盒 Copilot 第一片，后续默认进入 P3-05 试点部署包。
4. P3 的主线顺序固定为：真实题库与知识包 -> 模型草稿事实性 -> 坐席工作台产品化 -> 单渠道 Copilot sandbox -> 试点部署包。当前已经完成前四步的 rehearsal/产品化/沙盒第一片。
5. 每个阶段都要保留评测，但评测只证明本片能不能进入下一片，不再成为阶段本身的无限尾巴。
6. P3-06R-01/P3-06R-01B/P3-06R-02/P3-06R-03A 已完成壳层/总览 BI 第一版、壳层滚动二次修复、后端权限契约收口、前端按权限刷新和坐席工作台一屏闭环前端第一片；下一步默认进入 P3-06R-03B 真实登录端到端动作 smoke，或 P3-06R-04 渠道连接器中心。

## 4A. P3-02 后中心推进计划

本段是 2026-06-27 追加的中心总控版本，用于后续所有“继续下一步”类工程推进。它的作用是防止单点任务越做越细以后忘记整体工程目标。

当前最新真实状态：

| 维度 | 当前真实状态 | 下一步判断 |
| --- | --- | --- |
| 产品主线 | P3-01 到 P3-06R-03A 已完成客户式题库、事实性 rehearsal、坐席工作台、官网 sandbox、试点部署准备、官方渠道 readiness、企业微信 inbound connector、会话收件箱、坐席动作、对话台/质量、知识缺口、工单第一片、联系人画像与线索跟进第一片、缺口草稿/回归第一片、对话台主工作区、质量诊断 BI 第一片、知识发布前回归门禁第一片、知识发布记录/回滚第一片、outbox 队列租约/原子抢占第一片、可信入站 worker 租约/运行记录第一片、worker heartbeat/受控 loop 第一片、Docker Compose worker service 第一片、前端运维心跳面板第一片、只读告警规则第一片、中台信息架构收口三片、指标出口第一片、RBAC 权限矩阵、权限快照/审计权限迁移、账号团队权限/bootstrap、会话/知识/工单/客户/线索/渠道/outbox 命名权限、前端按钮级权限、P3-06R-01 壳层和总览 BI 第一版、P3-06R-01B 壳层滚动二次修复、P3-06R-02 权限契约与前端按权限请求、P3-06R-03A 坐席一屏闭环前端第一片 | 不能再继续自动追加同类离线评测；下一步优先 P3-06R-03B 真实登录端到端动作 smoke，或 P3-06R-04 渠道连接器中心；字段脱敏和企业微信公网 HTTPS 回调 smoke 仍需单独授权/排期 |
| 坐席工作台 | 已有七类队列、会话证据详情、outbox/失败复盘/渠道健康聚合、会话收件箱、坐席动作、对话台、质量复盘、知识缺口、工单第一片、联系人画像和线索跟进第一片、缺口草稿/回归动作 | 后续再补跨渠道身份合并、标签体系、高级 SLA、工单评论/附件/重开流程、知识审核发布流和团队绩效 |
| 知识库 | 已有文档分块、引用、评测和 rehearsal 知识包 | 正式验收仍缺客户真实知识包 |
| 模型 | 已有百炼 smoke、模型路由和 deterministic 事实性 rehearsal | 真实模型质量必须等授权和 limit |
| 渠道 | 已有 webhook/outbox/connector/dry-run 骨架；P3-04 已完成官网客服沙盒 Copilot 闭环 | 后续真实平台接入仍需官方账号、回调域名、密钥和平台规则复核 |
| 交付 | 本机工程可验证 | P3-05 才进入部署、备份、恢复和试点 SOP |

下一步只允许围绕三条客户可见主线推进；其中 P3-03 和 P3-04 第一片已完成，默认优先 P3-05：

| 优先级 | 阶段 | 本轮目标 | 技术施工焦点 | 验收方式 |
| --- | --- | --- | --- | --- |
| 已完成 | P3-03 坐席工作台产品化 | 让坐席和客户能看懂系统怎么处理问题 | 主屏队列、会话详情、证据引用、AI 草稿、人审原因、outbox、失败复盘、渠道健康 | `npm run build`、桌面/移动 Chrome CDP 截图、关键文案和队列只读校验已通过 |
| 已完成 | P3-04 单渠道 Copilot sandbox | 用一个入口跑通真实或自有受控入站到人工确认 | 官网沙盒入站、验签、可信消息、AI 建议、人审、outbox、发送计划门禁 | 后端端到端测试、相关回归、前端构建、桌面/移动 Chrome CDP QA 已通过 |
| 1 | P3-05 试点部署包 | 让另一个工程师能按清单部署和恢复 | 环境变量、迁移、Postgres/Redis、备份恢复、日志、审计、回滚、运行手册 | 部署清单、空库迁移、备份恢复 drill、README 和 smoke |

评测的位置必须调整为：

1. 开工前：用已有评测结果判断上一阶段是否已经回答问题。
2. 施工中：只加能保护本片改动的最小验证。
3. 收尾时：只作为放行证据，不自动生成下一轮同类评测任务。

禁止出现的推进方式：

- 每个阶段最后都自动追加一个新的 benchmark。
- 在没有真实客户题库、真实知识包或真实渠道时继续扩大合成题规模。
- 把报告导出、历史列表、更多指标当成客户可见产品能力。
- 因为还可以继续调参，就跳过坐席工作台、渠道 sandbox 和部署试点包。

每次工程推进开始前，必须先给出一段“全量进度感知”：

```markdown
## 全量进度感知

- 最新已完成阶段:
- 当前正在推进阶段:
- 这不是哪些能力:
- 已经真实可验证的能力:
- 仍是 rehearsal / fixture / dry-run / placeholder 的能力:
- 本轮新增客户可见价值:
- 本轮是否需要评测:
- 本轮评测回答什么唯一问题:
- 评测停止条件:
- 本轮结束后下一阶段:
```

如果上面任一项写不清楚，先停下来重新判断路线，不进入实现。

## 5. Task 0: 每轮工程启动前的全量感知仪式

**Files:**
- Read: `/Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/AGENTS.md`
- Read: `/Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/README.md`
- Read: `/Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/执行记录.md`
- Read: `/Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/关键决策.md`
- Read: `/Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/复盘与采坑.md`
- Read: `/Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/文件索引.md`
- Read: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/docs/superpowers/plans/2026-06-27-roadmap-correction-and-p3-pilot-loop.md`

- [ ] **Step 1: 用 Superpowers 进入计划执行模式**

Read the relevant skill before work:

```bash
sed -n '1,240p' /Users/ericlee/.codex/plugins/cache/openai-curated/superpowers/3fdeeb49/skills/executing-plans/SKILL.md
```

Expected: file opens and confirms the task-by-task execution workflow.

- [ ] **Step 2: 读取 Project_012 当前状态**

Run:

```bash
sed -n '1,220p' /Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/README.md
sed -n '1,120p' /Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/关键决策.md
tail -120 /Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/执行记录.md
tail -120 /Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/复盘与采坑.md
```

Expected: before implementation, the worker can state the current stage, last completed P number, remaining gaps, and blocked capabilities.

- [ ] **Step 3: 写出本轮阶段卡片**

Before code changes, create a short stage card in the working response or stage document:

```markdown
## Stage Card

- Stage:
- Last completed:
- What is truly done:
- What is not done:
- Customer-visible value in this slice:
- Is this slice mainly evaluation:
- Stop condition:
- External risk:
- Verification:
- Writeback files:
```

Expected: no implementation begins before the card is filled.

- [ ] **Step 4: 把本轮阶段状态写回 Superpowers 计划**

At the end of every engineering slice, update this plan with a short status note:

```markdown
### Current Slice Status

- Stage:
- Finished:
- Not finished:
- Customer-visible:
- Evaluation-only:
- Next:
```

Expected: future workers do not need to infer progress from memory or chat history; the plan itself carries the latest stage truth.

## 6. Task 1: P2-27 短审查收口，不再扩成新评测工程

**Files:**
- Read: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/output/evals/p2_26_retrieval_quality_comparison/p2_26_failed_case_delta.csv`
- Modify only if needed: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/docs/P2-27_STILL_MISSING_FAILURE_TAXONOMY.md`
- Do not create new eval infrastructure unless explicitly approved.

- [x] **Step 1: 只分析 18 道 still_missing**

Run:

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
python3 - <<'PY'
import csv
from pathlib import Path
p = Path("output/evals/p2_26_retrieval_quality_comparison/p2_26_failed_case_delta.csv")
rows = list(csv.DictReader(p.open()))
still = [r for r in rows if r.get("outcome") == "still_missing"]
print({"total_rows": len(rows), "still_missing": len(still)})
for r in still[:5]:
    print(r.get("external_case_id"), r.get("source_category"), r.get("risk_level"), r.get("expected_source_uri"))
PY
```

Expected: `still_missing` is `18`. The original plan draft used `delta_status`, but the actual CSV uses `outcome`; P2-27 has corrected the schema口径.

- [x] **Step 2: 分桶失败原因**

Create one Markdown table with these buckets:

```markdown
| bucket | meaning | cases | fix direction | whether to fix before P3 |
| --- | --- | ---: | --- | --- |
| document_gap | seed 文档缺少明确答案或政策段落 |  | 补真实知识包，不再只修合成 seed | yes |
| chunk_granularity | 证据被拆散，标题/正文不在同一可用上下文 |  | 调整 chunk 策略或标题继承 | maybe |
| source_ordering | 同源证据没有被排到前面 |  | 同源 boost / evidence compression | yes |
| risk_noise | 风险/禁答文本干扰召回 |  | 风险证据隔离 | yes |
| label_issue | 期望词或期望来源标注有问题 |  | 人工修标 | yes |
```

Expected: this is a diagnostic document, not a new scoring platform. Completed in `docs/P2-27_STILL_MISSING_FAILURE_TAXONOMY.md`.

- [x] **Step 3: 只允许一次 before/after**

If making a small fix, run the existing P2-26 command once:

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python scripts/run_p2_26_retrieval_quality_comparison.py \
  --output-dir output/evals/p2_27_single_before_after
```

Expected: one comparison only. Do not add new top-k grids, new dashboards, new run history, or new report exporters in P2-27. P2-27 did not run before/after because no code or knowledge fix was made; it stayed a diagnostic closeout.

- [x] **Step 4: 强制停止 P2 评测尾巴**

At the end of P2-27, write:

```markdown
P2 synthetic evaluation tail is closed. Further quality work must use real desensitized customer questions or real customer-like knowledge packages.
```

Expected: next task is P3-01, not P2-28. Completed.

## 7. Task 2: P3-01 真实脱敏 50-100 题与真实知识包

**Files:**
- Create: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/docs/P3-01_REALISTIC_CUSTOMER_QUESTION_BANK.md`
- Create: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/evals/p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv`
- Create: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/evals/p3_01_realistic_knowledge_package_template.json`
- Use existing template: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/evals/customer_service_eval_bank_template.csv`
- Modify: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/backend/tests/test_customer_service_eval_bank_import_script.py`
- Use: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/scripts/import_customer_service_eval_bank.py`

- [x] **Step 1: 定义真实题库字段**

Required columns:

```text
external_case_id,source_channel,source_category,question,expected_terms,expected_source_uri,expected_human_review,allow_auto_reply,forbidden_terms,risk_level,annotation_notes
```

Expected: every case has category, risk, expected source, human review expectation, and annotation notes. Completed in `docs/P3-01_REALISTIC_CUSTOMER_QUESTION_BANK.md` and the 62-case CSV. The existing `customer_service_eval_bank_template.csv` already had the required superset fields.

- [x] **Step 2: 建立 50-100 题分布要求**

Use this target distribution:

```markdown
| type | target count |
| --- | ---: |
| 售前咨询 | 10-15 |
| 价格/套餐/优惠 | 8-12 |
| 交付/部署/周期 | 8-12 |
| 售后/退款/赔付 | 8-12 |
| 账号/权限/发票 | 5-8 |
| 渠道接入/平台规则 | 8-12 |
| 投诉/高风险/法务 | 5-10 |
| 知识缺口/不确定问题 | 5-10 |
| 闲聊/无关/恶意诱导 | 5-8 |
```

Expected: the set resembles real business traffic instead of only stress cases. Completed with 62 customer-like cases: 10 pre-sales, 8 pricing, 8 delivery, 8 support/refund, 6 account/security/invoice, 8 channel compliance, 6 risk/legal, 4 knowledge gaps, 4 guardrail/smalltalk. This remains a rehearsal bank, not real customer data.

- [x] **Step 3: 脱敏校验**

Run:

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python scripts/import_customer_service_eval_bank.py \
  evals/p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv \
  --name "P3-01 真实客户式试点题库样例 62题" \
  --description "用于验证 P3-01 真实脱敏题库字段、分布和脱敏 dry-run 的客户式样例，不含真实客户身份或真实订单资料。"
```

Expected: no high-confidence phone/email/id-card hits; if blocked rows exist, manually desensitize and rerun. Completed: dry-run returned `status=validated`, `total_cases=62`, `sensitive_row_count=0`, `provider_call_performed=false`, `external_write_performed=false`. Added pytest coverage in `test_p3_realistic_customer_service_eval_bank_fixture_is_validated_without_external_actions`.

## 8. Task 3: P3-02 生成答案事实性与引用评测

**Files:**
- Create: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/docs/P3-02_RAG_MODEL_ASSISTED_FACTUALITY.md`
- Modify: model-assisted evaluation code only after a stage card is accepted.

- [x] **Step 1: 明确评测对象**

Evaluate only these answer properties:

```text
answer_supported_by_citations
answer_has_forbidden_commitment
answer_requires_human_review
answer_mentions_uncertainty_when_evidence_missing
answer_does_not_invent_policy
```

Expected: no claim of final customer accuracy before real human review. Completed in `docs/P3-02_RAG_MODEL_ASSISTED_FACTUALITY.md` and `scripts/run_p3_02_rag_model_assisted_factuality_rehearsal.py`.

- [x] **Step 2: 默认不外呼真实模型**

If real 百炼/千问 model is used, require explicit approval and command flag:

```bash
--allow-external-call --limit 5
```

Expected: no paid model call happens silently. Completed: default run returned `provider_call_performed=false`; explicit `bailian` without allow returns `blocked_external_call_not_allowed`, and allow without positive limit returns `blocked_missing_limit_for_external_call`.

- [x] **Step 3: 人工复核不可省略**

For first 50-100 cases, record:

```text
manual_factuality_label=supported|partially_supported|unsupported|unsafe|needs_policy
```

Expected: no LLM judge replaces human labels in the first commercial proof set. Completed: output contains `manual_factuality_label_required=true` and `manual_factuality_label_status=pending_manual_review`; `manual_factuality_labels_collected=0` is explicitly recorded as unfinished human review.

### Stage Completion

- Stage: P3-02
- What changed: 新增 `scripts/run_p3_02_rag_model_assisted_factuality_rehearsal.py`、`docs/P3-02_RAG_MODEL_ASSISTED_FACTUALITY.md`、`backend/tests/test_p3_02_factuality_rehearsal_script.py`，并生成 `output/evals/p3_02_factuality_rehearsal/` 脱敏报告。
- What was verified: `py_compile` 通过；P3-02 单测 `3 passed`；P3-02/P3-01/P2-26 相关回归 `8 passed`；本地 dry-run `status=completed`、`total_cases=62`、`provider_call_performed=false`、`external_platform_write_performed=false`；输出目录未命中已知原始问题或草稿模板文本。
- What remains not done: 未做客户真实 50-100 题、未做人工作答事实性标签、未做真实百炼/千问质量验收、未做真实幻觉率、未接真实渠道、未完成坐席工作台产品化。
- Whether this was customer-visible: 否，主要是后台质量门禁；对客户的间接价值是避免把“检索命中率”误当成“草稿可自动发送”。
- Whether this was only evaluation: 是。本轮问题已经回答，下一步必须转入 P3-03 产品闭环或等待真实客户资料，不能自动追加下一轮同类离线评测。
- Next stage: P3-03 坐席工作台产品化 v1。

## 9. Task 4: P3-03 坐席工作台产品化 v1

**Files:**
- Modify: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/frontend/src/App.tsx`
- Modify: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/frontend/src/styles.css`
- Modify: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/frontend/src/api/client.ts`
- Create or update: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/docs/P3-03_AGENT_WORKBENCH_V1.md`

- [x] **Step 1: 产品主屏改成坐席真实工作流**

Required visible queues:

```text
待人工审核
待发送确认
发送失败
知识缺口
高风险会话
最近评测运行
渠道健康
```

Expected: user can understand what to do next without reading engineering docs.

Completed: `frontend/src/App.tsx` 已通过 `WorkbenchCommandCenter` 和 `buildWorkQueues` 展示七类坐席队列。

- [x] **Step 2: 会话详情必须同时显示证据**

Each conversation detail must show:

```text
original inbound message
AI draft
citations
risk level
handoff reason
model/provider status
outbox status
audit trail
```

Expected: no blind approval of AI drafts.

Completed: `ReviewEvidenceDetail` 已展示原始入站、AI 草稿、引用证据、风险等级、转人工原因、模型/provider、outbox 和审计链。

- [x] **Step 3: Browser/CDP 验证**

Run desktop and mobile UI checks:

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
npm run build
```

Expected: build succeeds, no text overlap on desktop or 390px mobile screenshots when browser QA is run.

Completed: `npm run build` 通过；使用本地 mock API 和 Chrome DevTools Protocol 完成 1440x1000 桌面与 390x1200 移动端截图 QA，确认无横向溢出。截图见 `output/p3_03_workbench_desktop.png` 和 `output/p3_03_workbench_mobile.png`。

## Stage Completion

- Stage: P3-03 坐席工作台产品化 v1。
- What changed: `frontend/src/App.tsx` 增加/整理坐席工作台主屏、七类队列、会话证据详情和当前审核选择；`frontend/src/styles.css` 调整工作台、队列卡片和移动端宽度约束；`frontend/src/data/navigation.ts` 将总览阶段标识更新为 `P3-03`；新增 `docs/P3-03_AGENT_WORKBENCH_V1.md`；生成桌面/移动截图证据。
- What was verified: `npm run build` 通过；关键文案检索覆盖七类队列和证据详情；冲突标记检索无命中；Chrome CDP 校验桌面 `innerWidth=1440`/`scrollWidth=1440`，移动 `innerWidth=390`/`scrollWidth=390`，无横向溢出。
- What remains not done: 未接真实企业微信/公众号/抖音/小红书/淘宝/京东/拼多多外发；未做客户真实 50-100 题人工事实性标签；未做真实千问/DeepSeek 答案质量验收；未实现完整联系人画像、SLA、工单、坐席排班和绩效；发送队列仍非生产级 Redis/RQ/Celery worker。
- Whether this was customer-visible: 是。坐席和客户可以看到更接近日常运营台的主屏、证据详情和队列状态。
- Whether this was only evaluation: 否。本轮是客户可见产品化，不是新增离线评测。
- Next stage: P3-04 单渠道 Copilot sandbox 闭环。

## 10. Task 5: P3-04 单渠道 Copilot sandbox 闭环

**Files:**
- Modify after approval: channel connector, trusted inbound, outbox worker, frontend channel status files.
- Create: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/docs/P3-04_SINGLE_CHANNEL_COPILOT_SANDBOX.md`

- [x] **Step 1: 优先选自有官网客服或企业微信测试号**

Allowed channels:

```text
website sandbox
wecom official test account
wechat customer service sandbox
```

Not allowed:

```text
个人微信外挂
Hook
群控
模拟点击
商家后台 RPA 代发
```

Expected: only official or self-owned channel paths.

- [x] **Step 2: 先做 Copilot，不急着自动外发**

The first real loop is:

```text
official/self-owned inbound -> trusted message -> AI suggestion -> human review -> outbox -> manual confirm/send or sandbox send
```

Expected: automatic external write remains off unless separately approved.

- [x] **Step 3: 渠道验收**

Acceptance:

```text
invalid signature does not create message
valid inbound creates message once
AI suggestion enters review
human approval creates outbox draft
send remains gated by kill switch or sandbox flag
receipt is auditable
```

Expected: no claim of all-platform completion.

### Stage Completion

- Stage: P3-04 单渠道 Copilot sandbox。
- What changed: 选择自有 `website sandbox` 作为第一条受控渠道，新增 `docs/P3-04_SINGLE_CHANNEL_COPILOT_SANDBOX.md`；新增 `backend/tests/test_p3_04_website_copilot_sandbox.py`，覆盖错签阻断、有效入站、幂等去重、AI 草稿进人审、人工批准、outbox 草稿、发送计划门禁和审计链；更新官网 provider registry 的 fixture 状态；前端新增“官网 Copilot 沙盒”面板和 P3-04 导航。
- What was verified: P3-04 单测通过；渠道/webhook/worker/outbox/connector 相关回归 `27 passed`；`npm run build` 通过；Chrome CDP 桌面 1440x1000 与移动 390x1200 截图 QA 通过，移动端 `innerWidth=390`、`scrollWidth=390`。
- What remains not done: 真实企业微信/公众号/抖音/小红书/淘宝/京东/拼多多接入、真实外发、生产密钥、生产队列、高并发、客户真实题库和部署试点包仍未完成。
- Whether this was customer-visible: 是。前端可以看到官网 Copilot 沙盒闭环、队列数字和外发门禁。
- Whether this was only evaluation: 否。本轮是单渠道产品和渠道闭环，不是离线评测扩展。
- Next stage: P3-05 试点部署包；如果先拿到官方测试号，则进入单平台真实 sandbox，但仍不默认打开真实外发。

## 11. Task 6: P3-05 交付与部署试点包

**Files:**
- Create: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/docs/P3-05_PILOT_DEPLOYMENT_READINESS.md`
- Update as needed: `.env.example`, deploy docs, README.

2026-06-29 扩展：P3-05 不再只是技术部署清单，而是产品化交付体系入口。后续要同时服务两个目标产品线：`Lite 试点版` 和 `标准运营版`。新增总控文档为 `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md`，客户资料包位于 `docs/customer/`，内部售后运维计划位于 `docs/internal/`。P3-05 完成后，下一阶段不应继续扩散评测，而应进入 Lite 试点版封版和标准运营版产品化 v1。

- [x] **Step 1: 建立试点部署清单**

Checklist:

```text
PostgreSQL migration smoke
Redis/queue smoke
environment variable inventory
secret handling
backup and restore drill
log and audit location
model provider config
channel config
kill switch
rollback plan
remote maintenance plan
diagnostic bundle
knowledge update workflow
accuracy regression monitoring
customer usage guide
service system guide
internal support SOP
```

Expected: trial deployment can be repeated by another engineer.

Completed in P3-05A: 新增 `docs/P3-05_PILOT_DEPLOYMENT_READINESS.md`、`scripts/check_p3_05_deployment_readiness.py`、`scripts/create_p3_05_diagnostic_bundle.py`，并更新 `.env.example` 和 README 的试点部署入口。当前已经有环境变量清单、Compose 服务校验、迁移 smoke 口径、备份恢复步骤、远程维护方式、诊断包、知识更新流程、准确率下降监控和客户资料包入口。真实客户环境部署、真实 PostgreSQL 备份恢复演练和真实官方渠道接入仍未完成。

- [x] **Step 2: 明确不能交付的边界**

Write:

```text
No all-platform promise.
No automatic external send by default.
No production customer data import without desensitization.
No paid model batch evaluation without explicit approval.
No AGPL/GPL code copy into closed commercial system.
No unmanaged remote access to customer production environment.
No customer-facing claim of 100% accuracy or no-human-needed service.
```

Expected: sales and engineering speak the same truth.

Completed in P3-05A: P3-05 文档已明确不能承诺全平台接通、默认自动外发、无人工审核也能安全运营、已完成客户真实 50-100 题验收、真实模型批量质量验收、生产级 worker、高并发和 100% 准确率。外发默认仍为 `OUTBOX_EXTERNAL_WRITE_ENABLED=false`。

## 11A. Task 7: Lite 试点版封版

**Files:**
- Read: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md`
- Update as needed: customer docs, README, frontend workbench, backend smoke scripts.

- [ ] **Step 1: Lite 功能清单冻结**

Acceptance:

```text
single official/self-owned entry
knowledge cards and lightweight documents
AI draft with citations
human review by default
outbox gated by kill switch
50-question minimum regression bank
basic deployment and diagnostic bundle
customer usage manual
```

- [ ] **Step 2: Lite 试点交付 smoke**

Expected:

```text
login works
one inbound path works
one knowledge package imports
one question bank regression runs
one AI draft enters review
one outbox draft remains gated
diagnostic bundle can be generated
```

## 11B. Task 8: 标准运营版产品化 v1

**Files:**
- Read: `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md`
- Update backend/frontend/deploy/docs as needed.

- [ ] **Step 1: 标准运营版缺口收口**

Acceptance:

```text
formal RBAC coverage for core resources
agent assignment and conversation ownership
contact profile
knowledge version/review workflow
quality center with run comparison and knowledge gap status
production worker plan or implementation
model cost governance
at least one official or self-owned channel pilot
```

- [ ] **Step 2: 标准运营版发布门禁**

Expected:

```text
backend regression passes
frontend build passes
browser QA passes
deployment smoke passes
backup/restore drill passes
customer docs are ready
internal support SOP is ready
```

## 12. 每阶段收尾写回规则

At the end of every stage, update:

- `/Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/执行记录.md`
- `/Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/关键决策.md` if a real decision changed.
- `/Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/文件索引.md` if files were added or changed.
- `/Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/复盘与采坑.md`

Write this exact completion block:

```markdown
## Stage Completion

- Stage:
- What changed:
- What was verified:
- What remains not done:
- Whether this was customer-visible:
- Whether this was only evaluation:
- Next stage:
```

## 13. 明确下一步

下一步推荐执行顺序：

1. P2-27 已完成：18 道 `outcome=still_missing` 失败题短审查已经写入 `docs/P2-27_STILL_MISSING_FAILURE_TAXONOMY.md`，P2 合成评测尾巴关闭。
2. P3-01 第一片已完成：62 条客户式题库样例、7 份 P3 知识包模板、dry-run 校验和 fixture 测试已落地；它不是客户真实 50-100 题验收。
3. P3-02 第一片已完成：deterministic 答案事实性与引用支撑 rehearsal 已落地，62 题 dry-run 结果显示 `answer_supported_by_citations_rate=0.4355`、`answer_requires_human_review_cases=56`、`manual_factuality_labels_collected=0`，说明检索命中率不能替代草稿事实性验收。
4. P3-03 第一片已完成：坐席工作台主屏、七类队列、会话证据详情和桌面/移动端 QA 已落地。
5. P3-04 第一片已完成：官网客服沙盒 Copilot 闭环、端到端测试、前端沙盒入口和桌面/移动 QA 已落地；它不是全平台真实接通。
6. P3-05A 已完成：部署准备文档、自检脚本、诊断包脚本、环境模板、一次性迁移 smoke、Compose 配置校验和三份对外 DOCX 已落地。
7. P3-05B 第一片已完成：总控手册状态已校正为 P3-05B，`P3-05B_LITE_PILOT_RELEASE_READINESS.md` 已新增，Lite 试点版可承诺范围、封版门禁、演示路径和阻塞项已冻结。
8. P3-05B 第二片已完成：`docker-compose.pilot.yml`、托管云端版 runbook、私有化部署包清单和内部售后运维补充已落地，Compose 覆盖配置可解析。
9. P3-05B 第三片已完成：`REMOTE_MAINTENANCE_AUTHORIZATION_SOP.md` 已新增，远程维护故障分级、授权链、只读命令、禁止命令、二次授权、权限回收和复盘模板已落地。
10. P3-05B 第四片已完成：`scripts/check_p3_05b_lite_release_readiness.py` 和 `backend/tests/test_p3_05b_lite_release_readiness.py` 已新增，封版文档、环境模板、Compose、后端配置和外发安全边界可重复自检。
11. P3-05C 已完成：官方渠道自动回复 readiness 文档、机器可读矩阵、只读 smoke 和 pytest 已落地；结论是当前没有任何第三方平台可被标记为生产自动回复 ready，企业微信/微信客服是最适合优先做官方 sandbox 的外部平台。
12. P3-05D 已完成：`P3-05D_CHANNEL_TEST_PREPARATION_GUIDE.md` 已新增，逐渠道写清用户去哪里操作、开通什么能力、给工程侧什么配置、哪些密钥不能发聊天、如何做 sandbox 验收。
13. P3-05E 已完成：`GET /api/webhooks/wecom/channels/{channel_id}` 支持企业微信 URL 验证，`POST /api/webhooks/wecom/channels/{channel_id}` 支持官方 XML 安全模式、AES 解密、XML 解析和可信入站消息创建；密钥通过 env secret 引用，真实外发仍关闭。
14. P3-05G 已完成：商户中控台分页与运营视角整改落地。前端新增演示样例数据、今日运营信号、会话池预览、渠道健康明细表，以及人工审核、待发送、失败复盘、知识文档、评测集、评测结果的搜索/状态筛选/每页数量/分页控件；桌面和 390px 移动端 Playwright QA 已通过。
15. P3-05H 已完成：正式会话收件箱核心能力落地。后端新增 `GET /api/tenants/{tenant_id}/conversation-inbox` 服务端分页/搜索/筛选/SLA 轻量聚合接口和 `PATCH /api/conversations/{conversation_id}/assignment` 坐席分配/接管接口；前端新增会话收件箱面板，正式登录走后端分页，演示模式可验证 18 条样例会话、禁用态和分页交互。
16. P3-05I 已完成：正式坐席工作流落地。后端新增 `POST /api/conversations/{conversation_id}/workflow-actions`，支持领取、释放、转派、解决、待跟进、等待客户、重开和备注；每次动作写入 `ConversationEvent` 审计事件。前端会话收件箱新增领取、等客户、解决、释放和查看审核入口；演示模式下按钮保持禁用，避免误导为真实业务处理已打开。
17. P3-05I-B 已完成：中控台页面化导航修复落地。左侧菜单已从长页锚点目录修正为独立工作区切换；总览、会话、审核、待发送、联系人、线索、知识库、渠道、模型、评测和设置均只渲染一个 `.workspace-page`；hash 与组件 DOM id 已解耦，浏览器打开页面后不再被锚点滚到中段。
18. P3-05J 已完成：用户优先提出的多渠道对话台与质量复盘第一版已落地。左侧导航新增 `对话台` 和 `质量`；对话台采用会话列表、对话流、证据/风险三栏；质量复盘聚焦强证据命中、转人工、知识缺口、发送失败和人工事实性标签边界。桌面端会话列表已经改为内部滚动，避免再次退化成一张长页。
19. P3-05K 已完成：知识缺口闭环第一版落地。后端新增 `knowledge_gaps` 资源、迁移、列表/同步/更新 API 和幂等去重；同步来源覆盖低置信/无知识人审任务与知识评测失败用例；前端新增 `缺口` 工作区，支持同步摘要、状态筛选、搜索、分页、处理动作和演示同形数据。
20. P3-05M 已完成：工单与 SLA 第一片落地。后端新增 `support_tickets` 资源、迁移、创建/列表/更新 API、角色边界、会话来源幂等、轻量 SLA 计算、`ConversationEvent` 与 `AuditEvent` 双写；前端新增 `工单` 工作区，支持筛选、分页、详情、候选会话生成工单和演示同形数据。
21. P3-05N 已完成：联系人画像与线索跟进第一片落地。后端新增联系人画像聚合、`sales_leads` 资源、迁移、列表/创建/更新 API、联系方式脱敏、角色边界、会话来源幂等、`ConversationEvent` 与 `AuditEvent` 双写；前端新增 `联系人` 和 `线索` 工作区，支持分页、搜索、画像详情、线索筛选、阶段推进和候选会话生成线索。
22. P3-05O 已完成：知识缺口到文档草稿与回归题库第一片落地。后端新增 `document-drafts` 和 `regression-cases` 缺口子资源接口，支持草稿创建/复用、回归题创建/复用、缺口 remediation 证据写回、状态进入处理中、owner/admin 权限、坐席 403、跨租户 404 和审计事件；前端 `缺口` 工作区新增草稿/回归状态标签和动作按钮。
23. P3-05Q 已完成：对话台重构为坐席主工作区，包含 8 类队列、会话事件时间线、AI 草稿区、客户/AI/知识/运营检查器和桌面/移动端浏览器 QA。
24. P3-05R 已完成：质量页重构为质量诊断 BI，包含错因排行、质量漏斗、题库趋势、渠道异常分布、知识缺口热力、人审矩阵、样本下钻和修复动作。
25. P3-05S 已完成：知识文档新增发布预检和带门禁发布 API，缺口页新增“发布知识”动作；发布前可检索 draft 文档并只把知识质量问题作为阻断，高风险人工兜底作为提示。
26. P3-05T 已完成：新增知识发布记录表、发布记录查询 API、回滚 API、发布检查/发布/回滚审计记录和知识文档卡片里的门禁详情摘要；回滚第一片只把文档与 chunk 退出 active 检索，不恢复旧正文。
27. P3-06A 已完成：outbox delivery queue 新增 `lease_seconds`、条件 UPDATE 原子 claim、陈旧 locked job 抢回、新鲜 locked job 跳过和 lease 运行证据；仍是 DB 队列第一片，不是 Redis/专用消息队列。
28. P3-06B 已完成：可信入站 worker 新增 `worker_id`、`lease_seconds`、`trusted_inbound_worker_runs`、`trusted_inbound_message_jobs`、fresh lock 跳过、stale lock 抢回、failed job 重放和运行记录只读列表接口；仍是 DB 租约第一片，不是常驻 worker 或 Redis/专用消息队列。
29. P3-06C 已完成第一片：新增 `worker_heartbeats` 表、worker 健康状态接口、可信入站 worker 受控 loop runner、loop heartbeat 写入和两个 worker_id 连续运行不重复处理的 smoke 测试；它仍不是完整生产监控系统。
30. P3-06D 已完成第一片：新增可信入站 worker CLI 进程入口、Docker Compose `trusted-inbound-worker` service、`worker` profile、只读 healthcheck、`TRUSTED_INBOUND_WORKER_*` env 模板、readiness 检查和部署文档；真实外发仍关闭。
31. P3-06E 已完成第一片：新增 `GET /api/tenants/{tenant_id}/ops/worker-health` 只读接口、owner/admin 权限、worker heartbeat 汇总、最近运行记录、外发开关状态、风险提示、前端“运维”工作区和 `scripts/check_p3_06e_ops_worker_health.py`；它仍不是完整 Prometheus/Grafana/告警体系，也不是高并发压测。
32. P3-06F 已完成第一片：新增 `GET /api/tenants/{tenant_id}/ops/alert-rules` 只读接口、8 条告警规则、runbook、通知边界、外部动作边界、前端“运维与告警”展示和 `scripts/check_p3_06f_ops_alert_rules.py`；它仍不是完整 Prometheus/Grafana/告警通知体系，也不是高并发压测。
33. P3-06UI 已完成第一片：前端导航从 16 个平铺入口收束为 7 个工作域，新增 `navigationGroups`、两级侧边栏、`docs/P3-06UI_INFORMATION_ARCHITECTURE.md` 和 `scripts/check_p3_06ui_information_architecture.py`。
34. P3-06UI 已完成第二片：新增 `NavigationRole`、`visibleTo`、角色化菜单过滤、坐席默认进入对话台、owner/admin/viewer 默认进入总览、不可见 hash 自动回落、`docs/P3-06UI_ROLE_BASED_NAVIGATION.md`、`scripts/check_p3_06ui_role_navigation.py` 和 owner 视图 Playwright 截图；它仍不等于后端资源级 RBAC 安全边界。
35. P3-06UI 已完成第三片：新增 `AdminOperationsWorkspace`、`getAdminOperationsTab`、`admin-ops-tabs`、`docs/P3-06UI_ADMIN_OPS_TABS.md`、`scripts/check_p3_06ui_admin_ops_tabs.py` 和管理运维 Tab Playwright 截图；`#ops/#model/#settings` 保留原 hash 但进入同一个管理运维工作区。
36. P3-06G 已完成第一片：新增 `GET /api/tenants/{tenant_id}/ops/metrics`、`OpsMetricsDashboardRead`、只读指标聚合、Prometheus 文本预览、前端“指标出口”面板、`docs/P3-06G_OPS_METRICS_EXPORT.md`、`scripts/check_p3_06g_ops_metrics.py`、`backend/tests/test_p3_06g_ops_metrics_api.py` 和 Playwright 截图；它仍不是完整 Prometheus/Grafana/真实通知体系。
37. P3-06H 已完成第一片：新增 `backend/app/core/rbac.py`、中心化 `ROLE_PERMISSIONS`、`require_permission()`、`docs/P3-06H_RBAC_PERMISSION_MATRIX.md`、`scripts/check_p3_06h_rbac_permission_matrix.py` 和 `backend/tests/test_p3_06h_rbac_permission_matrix.py`；运维三条接口已从散落角色判断迁到命名权限。
38. P3-06I 已完成第二片：新增 `CurrentUser.permissions`、登录和 `/api/auth/me` 权限快照、审计查询 `audit.events.read` 命名权限、`docs/P3-06I_RBAC_PERMISSION_SNAPSHOT_AND_AUDIT.md`、`scripts/check_p3_06i_rbac_permission_snapshot.py` 和 `backend/tests/test_p3_06i_rbac_permission_snapshot.py`；账号/团队接口因涉及首账号 bootstrap 暂不迁移。
39. P3-06J 已完成第三片：账号、角色、团队接口改用 `accounts.manage` 命名权限；owner-only 管理，admin/agent/viewer 禁止；首角色、首用户、首次角色分配 bootstrap 通道保持可用；新增 `docs/P3-06J_ACCOUNTS_RBAC_BOOTSTRAP.md`、`scripts/check_p3_06j_accounts_rbac_bootstrap.py` 和 `backend/tests/test_p3_06j_accounts_rbac_bootstrap.py`。
40. P3-06K 已完成第四片：会话列表、详情、收件箱、会话创建、消息写入、分配和坐席工作流迁到 `conversation.read` / `conversation.manage`；owner/admin/agent 允许，viewer 禁止；跨租户资源继续隐藏为 404；官方 webhook 入口仍走 connector 验签边界，不套坐席 bearer token；新增 `docs/P3-06K_CONVERSATION_RBAC.md`、`scripts/check_p3_06k_conversation_rbac.py` 和 `backend/tests/test_p3_06k_conversation_rbac.py`。
41. P3-06L 已完成第五片：知识卡片、知识文档、文档分块、检索、发布检查、发布、回滚、知识缺口、评测、向量索引和 provider smoke 迁到 `knowledge.read` / `knowledge.manage`；owner/admin 可管理，agent 只可检索，viewer 禁止读取知识原文；新增 `docs/P3-06L_KNOWLEDGE_RBAC.md`、`scripts/check_p3_06l_knowledge_rbac.py` 和 `backend/tests/test_p3_06l_knowledge_rbac.py`。
42. P3-06M 已完成第六片：工单列表、工单创建/更新、联系人画像列表/详情、线索列表、线索创建/更新迁到 `ticket.read` / `ticket.manage` / `customer.read` / `lead.read` / `lead.manage`；owner/admin/agent 允许，viewer 禁止读取客户画像、工单和线索原文；新增 `docs/P3-06M_CUSTOMER_OPS_RBAC.md`、`scripts/check_p3_06m_customer_ops_rbac.py` 和 `backend/tests/test_p3_06m_customer_ops_rbac.py`。
43. P3-06N 已完成第七片：渠道 provider 注册表和连接器摘要迁到 `channel.read`；连接器配置和 secret 引用迁到 `channel.connector.manage`；回执列表和手工回执分别迁到 `channel.delivery_receipt.read` / `channel.delivery_receipt.manage`；connector 发送计划迁到 `outbox.send_plan.manage`；官方 webhook 入口保持平台回调可达，不套坐席 bearer token；新增 `docs/P3-06N_CHANNEL_DELIVERY_RBAC.md`、`scripts/check_p3_06n_channel_delivery_rbac.py` 和 `backend/tests/test_p3_06n_channel_delivery_rbac.py`。
44. P3-06O 已完成前端按钮级权限第一片：新增前端 `PERMISSIONS` 和 `hasPermission()`；会话、人审、工单、线索、知识文档、知识缺口、知识评测和出站发送计划关键按钮已根据 `user.permissions` 禁用；handler 层也补权限 guard；连接器自动预置只给 `channel.connector.manage` 用户；新增 `docs/P3-06O_FRONTEND_BUTTON_PERMISSIONS.md` 和 `scripts/check_p3_06o_frontend_button_permissions.py`。
45. P3-06P 已完成第八片：outbox draft、dry-run send-attempt、delivery job、delivery failure review 迁到命名权限；agent 可确认草稿/试发/生成受控计划，owner/admin 才能创建和运行发送队列，viewer 可只读失败复盘但不能处理；前端出站和失败复盘按钮同步拆细权限；新增 `docs/P3-06P_OUTBOX_RESOURCE_RBAC.md`、`scripts/check_p3_06p_outbox_resource_rbac.py` 和 `backend/tests/test_p3_06p_outbox_resource_rbac.py`。
46. P3-06R-04C 已完成运营总览服务端只读聚合第一片：新增 `GET /api/tenants/{tenant_id}/ops/dashboard`、`dashboard.read` owner/admin/viewer 可读权限、agent 禁读、脱敏聚合字段、前端首页服务端聚合优先和 `backend/tests/test_p3_06r_ops_dashboard_api.py`；它仍不是历史数仓、物化指标表或完整 Grafana dashboard。后续不要继续只在前端重复拼样本 BI。
47. P3-06S-01 已完成窄桌面壳层滚动修复：新增 761px 到 960px 区间的中台壳层覆盖规则，900x768 从 body 整页滚动修复为右侧 `.workspace` 独立滚动；验证 `bodyScrollY=0`、`sidebarTop=0`、`workspaceScrollTop=900`，390px 手机端仍自然滚动且无横向溢出。
48. P3-06T 已完成下一步四项工程计划：将后续优化锁定为壳层滚动返修、首页数据口径收紧、运营总览 BI 重做、信息架构闭环四项，避免继续扩散到无关功能页。
49. P3-06T-01 已完成壳层滚动返修验收：有效基线确认 760px 仍会整页滚动；修复后 1440、1280、1024、900、760、721 均满足 `bodyScrollY=0`、`workspaceScrollTop=900`、`sidebarTop=0`，720 和 390 保持自然页面滚动且无横向溢出；新增 `scripts/check_p3_06t_layout_scroll.mjs` 和 `docs/P3-06T-01_LAYOUT_SCROLL_RETURN_REPAIR.md`。
50. P3-06T-02 已完成首页数据口径收紧：后端 dashboard 响应新增契约版本、聚合粒度、刷新模型、源表、敏感字段排除和口径备注；前端时间范围/渠道筛选正式接入服务端聚合刷新；新增 `docs/P3-06T-02_DASHBOARD_DATA_CONTRACT.md` 和浏览器 smoke 证据目录。
51. P3-06T-03 已完成运营总览 BI 重做。用户复审后，前端真实实用成熟度按约 `6.0 / 10` 起算，原 P3-06T-04 信息架构收口被吸收到 P3-06U 前后端契约对齐与实用型前端产品化优化；P3-06U-01/P3-06U-02/P3-06U-03/P3-06U-04/P3-06U-05 已在后续完成，当前下一步优先 P3-06U-06 质量复盘 BI。P3-06R-05 渠道连接器中心、企业微信公网 HTTPS 回调 smoke、字段脱敏/字段 allowlist 和 P3-06R-04D 统计缓存/物化层可作为后续并行专项。
52. 每轮推进前必须填写 Engineering Control Card；评测不能自动成为每轮最后的无限追加项。
53. P3-06U-01 已完成前后端契约与页面路径盘点第一片：新增 `docs/P3-06U-01_FRONTEND_BACKEND_CONTRACT_MATRIX.md`，清理导航和设置页客户可见的工程阶段表达，新增 `scripts/check_p3_06u_01_contract_alignment.py`；下一步默认 P3-06U-02 角色化任务路径重排。
54. P3-06U-02 已完成角色化任务路径重排：新增 `RoleTaskPath`、`roleTaskPaths`、`getRoleTaskPathsForRoles()`、顶部“今日任务路径”条和实时待办数字；owner/admin/agent/viewer 显示不同任务路径，agent 第一入口为接待客户会话，viewer 只保留只读路径；新增 `docs/P3-06U-02_ROLE_TASK_PATHS.md`、`scripts/check_p3_06u_02_role_task_paths.py` 和浏览器检查 `scripts/check_p3_06u_02_role_task_paths.mjs`；P3-06U-03/P3-06U-04/P3-06U-05 已在后续完成。
55. P3-06U-03 已完成接待工作台实用性重构：`ConversationWorkbenchPanel` 已从 `App.tsx` 拆到 `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx`，`#live` 改为会话队列、消息处理区、右侧上下文三栏 IM 工作台，明确“批准进入待发送”不等于真实外发；新增 `docs/P3-06U-03_CONVERSATION_WORKBENCH_RESTRUCTURE.md`、`scripts/check_p3_06u_03_conversation_workbench.py` 和浏览器检查 `scripts/check_p3_06u_03_conversation_workbench.mjs`；P3-06U-04 已在后续完成。
56. P3-06U-04 已完成运营总览到处理路径打通：首页优先动作和关键指标已改为带上下文 hash 的处理入口，目标页会展示来源、时间窗口、渠道和筛选状态，并自动进入对应队列/状态；新增 `docs/P3-06U-04_OVERVIEW_TO_ACTION_PATHS.md`、`scripts/check_p3_06u_04_overview_action_paths.py` 和浏览器检查 `scripts/check_p3_06u_04_overview_action_paths.mjs`；P3-06U-05 已在后续完成。
57. P3-06U-05 已完成真实登录角色 smoke：新增 `docs/P3-06U-05_REAL_LOGIN_ROLE_SMOKE.md`、`scripts/check_p3_06u_05_real_login_role_smoke.py`、`scripts/check_p3_06u_05_real_login_role_smoke.mjs`；用临时租户和真实账号验证 owner/admin/agent/viewer 登录、默认入口、导航可见性、任务路径、禁用动作解释、受限路径回退、退出清令牌和无意外 403；截图与摘要在 `output/p3_06u_role_smoke/`；下一步默认 P3-06U-06 质量复盘 BI。

禁止默认进入：

- P2-28。
- 新一轮合成题大扩容。
- 新一轮纯 top-k 网格搜索。
- 新一轮报告导出系统。
- 未经批准的真实外部发送。

### Current Slice Status

- Stage: P3-06U-10 第一片前端状态组件抽离。
- Finished: 已完成 P3-06T-03 运营总览 BI 重做、P3-06U 工程计划、P3-06U-01 契约矩阵、P3-06U-02 角色化今日任务路径、P3-06U-03 接待工作台重构、P3-06U-04 首页优先动作上下文跳转、P3-06U-05 真实登录角色 smoke、P3-06U-06 质量复盘 BI 修复闭环、P3-06U-07 知识运营台产品化第一片、P3-06U-08 渠道连接器中心实用化、P3-06U-09 前端状态体系统一和 P3-06U-10 第一片状态组件抽离；统一状态组件已进入 `frontend/src/components/common/WorkspaceState.tsx`，U09 门禁已兼容抽离后的结构。
- Not finished: P3-06U-10 全量页面组件拆分、联系人/线索/工单外围页状态组件替换、一次性安装 token、生产账号策略、字段脱敏、字段 allowlist、资源级所有权检查、主管质检完整视图、跨渠道身份合并、联系人标签、线索评论/提醒/附件/漏斗、CRM/订单系统官方对接、高级 SLA 策略、工单评论、附件、单独重开流程、知识草稿完整审核流、知识版本 diff、恢复旧正文、多人审批、人工事实性标签、投诉/差评事件源、Kubernetes/HPA、Prometheus 指标真实采集、Grafana dashboard、告警通知通道、多容器压测、outbox 独立 worker service、生产级渠道 token/回调健康、模型成本报表、真实企微 access token、可信 IP 出站链路、真实发送 API、公众号 sandbox、抖音/抖店/小红书/淘宝/京东/拼多多 provider 合同、真实客户环境部署、客户真实 50-100 题、真实模型批量质量验收和生产级 worker 全链路。
- Customer-visible: 间接可见。本片保持客户界面行为不变，但降低后续继续做知识、质量、渠道、运维页面时的维护风险；真实外发仍关闭。
- Evaluation-only: 否。包含前端结构调整、文档、静态检查、typecheck/build 和浏览器状态 smoke。
- Next: 继续 P3-06U-10 第二片，优先拆 `components/knowledge/` 或 `components/quality/`。真实外发、真实模型批量调用和生产数据库动作仍需明确授权。

## 2026-07-01 - P3-06T-03 运营总览 BI 重做完成

- Stage: P3-06T-03 运营总览 BI 重做。
- Finished: 首页已从指标卡片集合升级为运营指挥舱结构，新增经营信号条、运营健康环、风险组成、压力趋势主图、优先动作、处理漏斗、渠道矩阵和质量诊断；总览页顶部和演示提示进入紧凑模式。
- Files: `frontend/src/App.tsx`、`frontend/src/styles.css`、`scripts/check_p3_06t_03_bi_overview.mjs`、`docs/P3-06T-03_OPS_BI_COMMAND_CENTER_REDESIGN.md`。
- Verification: `cd frontend && npm run typecheck` 通过；`cd frontend && npm run build` 通过；`node scripts/check_p3_06t_03_bi_overview.mjs` 通过，覆盖 1440、1280、900、390 视口，截图证据在 `output/p3_06t_03_bi_overview/`。
- Decision: 900px 窄桌面不强求完整指挥舱全部塞入第一屏，要求经营信号和指挥舱入口可见、无横向溢出、右侧 `.workspace` 可继续独立滚动。
- Remaining: P3-06U-02 角色化任务路径；P3-06U-03 接待工作台实用重构；P3-06R-03B 真实登录端到端动作 smoke；P3-06R-05 渠道连接器中心；统计缓存/物化层；真实渠道联调与真实外发仍需单独授权。
- Next: 优先进入 P3-06U-02 角色化任务路径重排；如果客户渠道条件先具备，可并行 P3-06R-05 渠道连接器中心或企业微信公网 HTTPS 回调 smoke。

## 2026-07-01 - P3-06U 工程推进计划收束完成

- Stage: P3-06U 前后端契约对齐与实用型前端产品化优化计划。
- Finished: 新增 `docs/P3-06U_FRONTEND_BACKEND_ALIGNMENT_AND_PRACTICAL_UX_OPTIMIZATION_PLAN.md`，明确当前前端真实实用成熟度按 `6.0 / 10` 起算，不再把首页观感提升等同于全站商用成熟；P3-06T-04 被吸收到 P3-06U。
- Files: `docs/P3-06U_FRONTEND_BACKEND_ALIGNMENT_AND_PRACTICAL_UX_OPTIMIZATION_PLAN.md`、`README.md`、`docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md`，并写回 Workspace Project_012。
- Verification: 本轮只改 Markdown；P3-06U-01 已在后续用静态契约检查和前端构建完成验证。
- Decision: 下一阶段先做契约矩阵和角色路径，不直接继续视觉大改；前端每个动作必须映射后端 API、权限、状态机、审计和失败处理。
- Remaining: P3-06U-02 到 P3-06U-10 尚未实施；当前评分不会因为规划文档自动提升。
- Next: P3-06U-02 角色化任务路径重排。

## 2026-07-01 - P3-06U-01 前后端契约矩阵与客户化导航清理

- Stage: P3-06U-01 前后端契约与页面路径盘点。
- Finished: 建立 `docs/P3-06U-01_FRONTEND_BACKEND_CONTRACT_MATRIX.md`，覆盖核心工作区的路由、API、权限、数据状态、关键动作、后端状态机、审计、空态/错态和当前缺口；左侧导航去掉 `P3-06UI`、`P3-06F`、`RAG`、`规划` 等内部表达；设置页去掉“规划态/施工入口”口吻。
- Files: `frontend/src/data/navigation.ts`、`frontend/src/App.tsx`、`docs/P3-06U-01_FRONTEND_BACKEND_CONTRACT_MATRIX.md`、`scripts/check_p3_06u_01_contract_alignment.py`、`scripts/check_p3_06ui_information_architecture.py`、`scripts/check_p3_06f_ops_alert_rules.py`、`docs/P3-06T-03_OPS_BI_COMMAND_CENTER_REDESIGN.md`。
- Verification: `python3 scripts/check_p3_06u_01_contract_alignment.py` 通过；`python3 scripts/check_p3_06ui_information_architecture.py` 通过；`python3 scripts/check_p3_06ui_admin_ops_tabs.py` 通过；`python3 scripts/check_p3_06ui_role_navigation.py` 通过；`python3 scripts/check_p3_06f_ops_alert_rules.py` 通过；`cd frontend && npm run typecheck` 通过；`cd frontend && npm run build` 通过。
- Remaining: 渠道连接器中心和质量错因 BI；P3-06U-02/P3-06U-03/P3-06U-04/P3-06U-05 已在后续完成。
- Next: P3-06U-02 角色化任务路径重排。

## 2026-07-01 - P3-06U-02 角色化任务路径重排

- Stage: P3-06U-02 角色化任务路径重排。
- Finished: 新增角色化“今日任务路径”条，owner/admin/agent/viewer 分别看到不同顺序和数量的任务路径；owner/admin 优先处理风险、审核、待发送、知识缺口和渠道接入，agent 优先进入接待客户会话，viewer 只看经营风险、质量和渠道状态。
- Files: `frontend/src/data/navigation.ts`、`frontend/src/App.tsx`、`frontend/src/styles.css`、`docs/P3-06U-02_ROLE_TASK_PATHS.md`、`scripts/check_p3_06u_02_role_task_paths.py`、`scripts/check_p3_06u_02_role_task_paths.mjs`。
- Verification: `python3 scripts/check_p3_06u_02_role_task_paths.py` 通过；`python3 scripts/check_p3_06u_01_contract_alignment.py` 通过；`python3 scripts/check_p3_06ui_role_navigation.py` 通过；`cd frontend && npm run typecheck` 通过；`cd frontend && npm run build` 通过；`node scripts/check_p3_06u_02_role_task_paths.mjs` 通过并生成 `output/p3_06u_02_role_task_paths/`。
- Remaining: 渠道连接器中心、质量错因 BI、字段脱敏/字段 allowlist；P3-06U-03/P3-06U-04/P3-06U-05 已在后续完成。
- Next: P3-06U-03/P3-06U-04/P3-06U-05 已在后续完成；当前下一步为 P3-06U-06 质量复盘 BI。

## 2026-07-01 - P3-06U-03 接待工作台实用性重构

- Stage: P3-06U-03 接待工作台实用性重构。
- Finished: `#live` 接待工作台已从 `App.tsx` 旧内联函数拆到 `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx`；页面重构为会话队列、消息处理区、右侧上下文三栏 IM 工作台；坐席可以在同页看客户问题、AI 草稿、引用证据、内部备注、批准进入待发送和确认待发送；`workspace-live` 下压缩了顶栏、任务路径和演示提示，桌面首屏可看到三栏主体。
- Files: `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx`、`frontend/src/App.tsx`、`frontend/src/styles.css`、`docs/P3-06U-03_CONVERSATION_WORKBENCH_RESTRUCTURE.md`、`scripts/check_p3_06u_03_conversation_workbench.py`、`scripts/check_p3_06u_03_conversation_workbench.mjs`。
- Verification: `python3 scripts/check_p3_06u_03_conversation_workbench.py` 通过；`python3 scripts/check_p3_06u_02_role_task_paths.py` 通过；`python3 scripts/check_p3_06u_01_contract_alignment.py` 通过；`cd frontend && npm run typecheck` 通过；`cd frontend && npm run build` 通过；`node scripts/check_p3_06u_03_conversation_workbench.mjs` 通过并生成 `output/p3_06u_03_conversation_workbench/`。
- Remaining: 渠道连接器中心、质量错因 BI、知识运营台产品化和统一状态体系；真实登录角色 smoke 已在后续完成。
- Next: P3-06U-04/P3-06U-05 已在后续完成；当前下一步为 P3-06U-06 质量复盘 BI。

## 2026-07-01 - P3-06U-04 运营总览到处理路径打通

- Stage: P3-06U-04 运营总览到处理路径打通。
- Finished: 首页优先动作和关键指标已改为带上下文的任务入口；`#live`、`#outbox`、`#gaps`、`#channels` 会从 hash query 读取来源、任务、时间窗口、渠道和目标状态，展示上下文提示并应用队列/状态筛选。
- Files: `frontend/src/App.tsx`、`frontend/src/components/conversation/ConversationWorkbenchPanel.tsx`、`frontend/src/styles.css`、`docs/P3-06U-04_OVERVIEW_TO_ACTION_PATHS.md`、`scripts/check_p3_06u_04_overview_action_paths.py`、`scripts/check_p3_06u_04_overview_action_paths.mjs`。
- Verification: `python3 scripts/check_p3_06u_04_overview_action_paths.py` 通过；`python3 scripts/check_p3_06u_03_conversation_workbench.py` 通过；`python3 scripts/check_p3_06u_02_role_task_paths.py` 通过；`python3 scripts/check_p3_06u_01_contract_alignment.py` 通过；`cd frontend && npm run typecheck` 通过；`cd frontend && npm run build` 通过；`node scripts/check_p3_06u_04_overview_action_paths.mjs` 通过并生成 `output/p3_06u_04_overview_action_paths/`。
- Remaining: 质量复盘 BI、知识运营台产品化、渠道连接器中心、统一状态体系、字段脱敏、字段 allowlist、真实渠道联调和真实外发；真实登录角色 smoke 已在后续完成。
- Next: P3-06U-05 已在后续完成；当前下一步为 P3-06U-06 质量复盘 BI。

## 2026-07-01 - P3-06U-05 真实登录角色 Smoke

- Stage: P3-06U-05 真实登录角色 smoke。
- Finished: 用真实后端 API 创建临时租户和 owner/admin/agent/viewer 四类账号，通过前端登录表单登录后验证默认入口、导航可见性、今日任务路径、禁用动作解释、受限路径回退、退出清令牌和无意外 403。
- Files: `frontend/src/App.tsx`、`docs/P3-06U-05_REAL_LOGIN_ROLE_SMOKE.md`、`scripts/check_p3_06u_05_real_login_role_smoke.py`、`scripts/check_p3_06u_05_real_login_role_smoke.mjs`、`output/p3_06u_role_smoke/summary.json`。
- Verification: `python3 scripts/check_p3_06u_01_contract_alignment.py`、`python3 scripts/check_p3_06u_02_role_task_paths.py`、`python3 scripts/check_p3_06u_03_conversation_workbench.py`、`python3 scripts/check_p3_06u_04_overview_action_paths.py`、`python3 scripts/check_p3_06u_05_real_login_role_smoke.py` 均通过；`cd frontend && npm run typecheck` 和 `npm run build` 通过；`backend/.venv/bin/pytest backend/tests/test_auth_rbac_audit.py backend/tests/test_p3_06j_accounts_rbac_bootstrap.py backend/tests/test_p3_06h_rbac_permission_matrix.py -q` 通过；Chrome CDP 真实登录 smoke 通过并生成截图。
- Remaining: P3-06U-06 质量复盘 BI、P3-06U-07 知识运营台产品化、P3-06U-08 渠道连接器中心、P3-06U-09 状态体系统一、真实渠道联调和真实外发。
- Next: P3-06U-06 质量复盘 BI。

## 2026-07-01 - P3-06U-06 质量复盘 BI 与知识修复闭环

- Stage: P3-06U-06 质量复盘 BI 与知识修复闭环。
- Finished: 质量复盘页新增修复闭环分数、六类修复路径、`from=quality` 上下文链接和目标页“来自质量复盘”提示；`WorkspaceTaskContext` 支持 `overview | quality` 来源；知识缺口、低置信人审、渠道异常、待发送、回归验证均能从质量页进入对应处理路径。
- Files: `frontend/src/App.tsx`、`frontend/src/styles.css`、`docs/P3-06U-06_QUALITY_BI_REPAIR_LOOP.md`、`scripts/check_p3_06u_06_quality_bi.py`、`scripts/check_p3_06u_06_quality_bi.mjs`、`output/p3_06u_06_quality_bi/summary.json`。
- Verification: `python3 scripts/check_p3_06u_01_contract_alignment.py`、`python3 scripts/check_p3_06u_02_role_task_paths.py`、`python3 scripts/check_p3_06u_03_conversation_workbench.py`、`python3 scripts/check_p3_06u_04_overview_action_paths.py`、`python3 scripts/check_p3_06u_05_real_login_role_smoke.py`、`python3 scripts/check_p3_06u_06_quality_bi.py` 均通过；`cd frontend && npm run typecheck` 和 `npm run build` 通过；Chrome CDP 质量 BI smoke 通过，覆盖 1440、900、390 视口并生成截图。
- Remaining: P3-06U-07 知识运营台产品化、P3-06U-08 渠道连接器中心、P3-06U-09 状态体系统一、真实渠道联调和真实外发。
- Next: P3-06U-07 知识运营台产品化。

## 2026-07-01 - P3-06U-07 知识运营台产品化第一片

- Stage: P3-06U-07 知识运营台产品化第一片。
- Finished: `#knowledge`、`#gaps`、`#evals` 顶部统一展示知识运营流程；新增 `from=knowledge` 任务来源，目标页显示“来自知识运营”和匹配数量；新增发布前回归门禁、回归影响预估、版本与审核状态、知识草稿编辑清单和移动端布局修复。
- Files: `frontend/src/App.tsx`、`frontend/src/styles.css`、`docs/P3-06U-07_KNOWLEDGE_OPS_PRODUCTIZATION.md`、`scripts/check_p3_06u_07_knowledge_ops.py`、`scripts/check_p3_06u_07_knowledge_ops.mjs`、`output/p3_06u_07_knowledge_ops/summary.json`。
- Verification: `python3 scripts/check_p3_06u_07_knowledge_ops.py` 通过；`python3 scripts/check_p3_06u_06_quality_bi.py` 通过；`cd frontend && npm run typecheck` 通过；`cd frontend && npm run build` 通过；Chrome CDP 知识运营 smoke 通过，覆盖 1440、900、390 视口并生成截图。
- Remaining: P3-06U-08 渠道连接器中心、P3-06U-09 状态体系统一、真实渠道联调和真实外发；完整知识版本 diff、恢复旧正文、多人审批和发布后真实效果对比仍未完成。
- Next: P3-06U-08 渠道连接器中心实用化。

## 2026-07-01 - P3-06U-08 渠道连接器中心实用化

- Stage: P3-06U-08 渠道连接器中心实用化。
- Finished: `#channels` 第一屏新增渠道接入状态中心；企业微信/微信客服展示 10 步接入状态；公网 HTTPS 回调 URL、Token、EncodingAESKey、可信 IP 只展示配置位置和状态，Token/AESKey 不展示明文；公众号、抖音/抖店、小红书、淘宝/天猫、京东/拼多多只展示官方授权前置条件和未接入状态。
- Files: `frontend/src/App.tsx`、`frontend/src/styles.css`、`docs/P3-06U-08_CHANNEL_CONNECTOR_CENTER_PRODUCTIZATION.md`、`scripts/check_p3_06u_08_channel_connector_center.py`、`scripts/check_p3_06u_08_channel_connector_center.mjs`、`output/p3_06u_08_channel_connector_center/summary.json`。
- Verification: `python3 scripts/check_p3_06u_08_channel_connector_center.py` 通过；`cd frontend && npm run typecheck` 通过；`cd frontend && npm run build` 通过；Chrome CDP 渠道中心 smoke 通过，覆盖 1440、900、390 视口并生成截图。
- Remaining: P3-06U-09 状态体系统一、真实企业微信公网 HTTPS 回调 smoke、access token/可信 IP 检查、官方回执健康、真实渠道联调和真实外发。
- Next: P3-06U-09 前端状态体系统一。

## 2026-07-01 - P3-06U-09 前端状态体系统一

- Stage: P3-06U-09 前端状态体系统一。
- Finished: 新增统一状态组件和数据来源标签；顶部工作台持续展示演示样本/真实服务端数据、配置状态和真实外发关闭；多渠道对话台、人工审核、待发送、失败复盘、渠道中心、知识文档、知识缺口、知识评测、质量诊断和运维页已接入统一状态表达和禁用原因。
- Files: `frontend/src/App.tsx`、`frontend/src/components/conversation/ConversationWorkbenchPanel.tsx`、`frontend/src/styles.css`、`docs/P3-06U-09_FRONTEND_STATE_SYSTEM.md`、`scripts/check_p3_06u_09_unified_states.py`、`scripts/check_p3_06u_09_unified_states.mjs`、`output/p3_06u_09_unified_states/summary.json`。
- Verification: `python3 scripts/check_p3_06u_09_unified_states.py` 通过；`cd frontend && npm run typecheck` 通过；`cd frontend && npm run build` 通过；Chrome CDP 状态体系 smoke 通过，覆盖 1440、390 视口并生成截图；P3-06U-01 到 P3-06U-09 静态回归全部通过。
- Remaining: P3-06U-10 前端组件和状态结构拆分、联系人/线索/工单外围页状态组件替换、真实企业微信公网 HTTPS 回调 smoke、access token/可信 IP 检查、官方回执健康、真实渠道联调和真实外发。
- Next: P3-06U-10 前端组件和状态结构拆分。

## 2026-07-01 - P3-06U-10 第一片前端状态组件抽离

- Stage: P3-06U-10 第一片前端状态组件抽离。
- Finished: 新增 `frontend/src/components/common/WorkspaceState.tsx`，从 `App.tsx` 抽出统一状态组件、数据来源标签、禁用原因和顶部运行状态条；`App.tsx` 改为导入通用组件；U09 静态门禁已改为同时检查 `App.tsx` 和 common 状态组件文件。
- Files: `frontend/src/App.tsx`、`frontend/src/components/common/WorkspaceState.tsx`、`docs/P3-06U-10_FRONTEND_STATE_COMPONENT_EXTRACTION.md`、`scripts/check_p3_06u_09_unified_states.py`、`scripts/check_p3_06u_10_state_component_extraction.py`、`output/p3_06u_09_unified_states/summary.json`。
- Verification: `python3 scripts/check_p3_06u_10_state_component_extraction.py` 通过；`python3 scripts/check_p3_06u_09_unified_states.py` 通过；P3-06U-01 到 P3-06U-10 静态回归全部通过；`cd frontend && npm run typecheck` 通过；`cd frontend && npm run build` 通过；Chrome CDP 状态体系 smoke 通过并刷新截图证据。
- Remaining: P3-06U-10 第二片知识/质量/渠道/运维页面组件拆分、外围页状态组件替换、真实企业微信公网 HTTPS 回调 smoke、access token/可信 IP 检查、官方回执健康、真实渠道联调和真实外发。
- Next: 继续 P3-06U-10 第二片，优先拆知识或质量页面组件。

## 2026-07-02 - P3-06U-10B 多渠道对话台微信式收束

- Stage: P3-06U-10B 多渠道对话台微信式收束。
- Finished: `#live` 从三栏管理看板收束为左会话列表、右对话主区的双栏接待台；顶部大信号条和顶部大队列卡移除；队列筛选收进左侧列表；右侧 inspector 改为聊天区内的客户、AI、知识、待发送轻量上下文卡。
- Files: `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx`、`frontend/src/styles.css`、`docs/P3-06U-10B_CONVERSATION_WORKBENCH_WECHAT_SIMPLIFICATION.md`、`scripts/check_p3_06u_10b_conversation_workbench_simplification.py`、`scripts/check_p3_06u_10b_conversation_workbench_simplification.mjs`、`scripts/check_p3_06u_03_conversation_workbench.mjs`、`output/p3_06u_10b_conversation_workbench_simplification/summary.json`。
- Verification: `python3 scripts/check_p3_06u_10b_conversation_workbench_simplification.py` 通过；`python3 scripts/check_p3_06u_09_unified_states.py` 通过；`python3 scripts/check_p3_06u_03_conversation_workbench.py` 通过；`cd frontend && npm run build` 通过；U10B Chrome CDP smoke 通过 1440/390；U03 Chrome CDP 回归通过 1440/900/390。
- Remaining: `ConversationWorkbenchPanel.tsx` 内部组件拆分、外围页状态替换、真实企业微信公网 HTTPS 回调 smoke、可信 IP、access token、真实渠道联调和真实外发。
- Next: 继续 P3-06U-10 结构治理，优先拆会话列表、聊天区、草稿审核区；不要再把质量、知识、渠道等管理信息塞回接待主界面。
