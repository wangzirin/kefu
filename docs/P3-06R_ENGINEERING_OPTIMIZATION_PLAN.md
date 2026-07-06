# P3-06R 工程性优化、升级、修复计划

日期：2026-07-01

本计划只规划下一步，不实施代码修改。范围限定为：修复前后端契约、修复中台壳层滚动、升级运营总览 BI、补齐坐席闭环、补齐渠道连接器中心。不继续深挖字段脱敏，不推进备案/部署，不打开真实外发。

执行状态补充：P3-06R-01 已完成中台壳层与运营总览 BI 第一版；P3-06R-01B 已完成壳层滚动二次修复，桌面端改为右侧 `.workspace` 独立滚动，移动端恢复自然页面滚动；P3-06R-02 已完成后端权限契约与前端按权限刷新资源；P3-06R-03A 已完成坐席工作台一屏闭环第一片，把编辑 AI 草稿、内部备注、引用确认、批准进入待发送、确认待发送和右侧处理动作集中到 `#live`。下一步默认进入 P3-06R-03B 真实登录端到端动作 smoke，或 P3-06R-04 渠道连接器中心第一片。

## 当前判断

当前标准运营版不是空壳，也不是普通 FAQ 页面。它已有会话、人工审核、待发送草稿、失败复盘、知识库、质量诊断、工单、联系人、线索、渠道健康、运维指标和 RBAC 骨架。

但它还不是可直接对外发布的成熟商用智能客服中台。下一步不能再继续盲目加页面，而要把已存在的核心链路收紧，让系统从“看起来有模块”进入“真实中台可用”的状态。

## 必须解决的 6 个问题

### 问题 1：后端权限契约没有完全闭合

表现：

- 租户、渠道、联系人 foundation 接口仍有无鉴权入口。
- 无 token `/api/auth/me` 仍会返回开发演示 owner。
- workflow、inbound worker、reply orchestration 仍有只要求登录、不要求命名权限的旧接口。

风险：

- 试点环境或客户环境中，前端按钮权限不等于后端真实安全边界。
- 后续接真实平台 webhook、真实联系人和客户资料时会变成高风险入口。

### 问题 2：前端权限请求没有按角色分流

表现：

- 登录后前端会批量刷新会话、工单、联系人、线索、知识、运维、评测等模块。
- 低权限角色会天然触发多个 403，形成错误噪音。

风险：

- 客户看到“权限错误”会误判系统不稳定。
- 角色越细，前端体验越不可控。

### 问题 3：坐席工作台没有完成一屏闭环

表现：

- AI 草稿更像只读预览。
- 坐席不能自然完成编辑草稿、确认引用、写审核意见、转人工原因、发送前确认。
- 对话区、审核区、待发送区之间仍然有割裂感。

风险：

- 客服真正工作时要来回跳页面。
- 这个系统会像“运营看板”，不像“坐席每天用的主工作台”。

### 问题 4：渠道页还不是正式连接器中心

表现：

- 当前更像渠道状态说明和健康表。
- 缺少每个渠道的配置状态、官方授权状态、Webhook URL、Token/AESKey/Secret 引用状态、最近事件、最近错误、测试入口。

风险：

- 无法支撑客户理解“怎么接企业微信、公众号、抖音、小红书、淘宝”。
- 也无法支撑我们内部排障。

### 问题 5：应用壳层滚动逻辑不合格

表现：

- 用户向下滚动首页时，左侧黑色导航栏也跟着页面整体滑动。
- 中台类产品正常应该是左侧导航固定，右侧白色工作区独立滚动。

原因判断：

- 当前结构是 `.app-shell` + `.sidebar` + `.workspace`。
- `.sidebar` 虽然用了 `position: sticky; top: 0; height: 100vh; overflow-y: auto;`，但整个页面仍由 body 参与滚动，右侧工作区没有成为独立滚动容器。
- MDN 对 `position: sticky` 的说明是：sticky 会相对最近滚动祖先生效；一旦滚动容器和页面整体滚动关系没设计好，sticky 表现就会偏离中台预期。

目标：

- 桌面端：左侧栏固定，只有右侧内容滚动。
- 移动端：侧栏改为顶部/抽屉式或紧凑导航，不强行固定 280px 左栏。

### 问题 6：运营总览不够像高级 BI 中台首页

表现：

- 现在是几个大模块堆叠，信息密度和视觉冲击力都不足。
- 卡片占位大，但对运营决策的帮助有限。
- 缺少时间范围、渠道筛选、趋势图、漏斗、异常定位、点击下钻。

目标：

- 首页要从“模块集合”升级为“运营指挥舱”。
- 一眼看到：今天进线量、AI 自动解决率、转人工率、平均响应、风险会话、渠道异常、知识缺口、待处理队列。
- 支持点击进入对应工作台，而不是只展示数字。

## 外部参考源

### 客服中台参考

| 来源 | 许可证/边界 | 可参考点 | 不直接照搬原因 |
| --- | --- | --- | --- |
| [Chatwoot](https://github.com/chatwoot/chatwoot) | MIT | 全渠道收件箱、标签、快捷回复、自动分配、团队报表、客户资料、内部备注 | 技术栈不同，但产品结构很适合参考 |
| [Zammad](https://github.com/zammad/zammad) | AGPL-3.0 | 工单、客服协作、邮件/聊天/电话/社媒统一处理 | AGPL，不能直接复制进闭源商用系统 |
| [OpenAI Customer Service Agents Demo](https://github.com/openai/openai-cs-agents-demo) | MIT | 多 agent 路由和客服界面的编排展示 | 是 demo，不是完整客服中台 |

### 后台与 BI 参考

| 来源 | 许可证/边界 | 可参考点 | 是否建议直接引入 |
| --- | --- | --- | --- |
| [shadcn-admin](https://github.com/satnaing/shadcn-admin) | MIT | Vite + React 后台壳层、内置 Sidebar、响应式、可访问性、全局搜索 | 参考布局和交互，不整体迁移 |
| [Tremor](https://github.com/tremorlabs/tremor) | Apache-2.0 | 数据看板组件、仪表盘默认审美、图表排布 | 当前项目没 Tailwind/Radix，暂不整体引入 |
| [Tremor Dashboard Template](https://github.com/tremorlabs/template-dashboard-oss) | Apache-2.0 | SaaS 数据首页、指标卡、图表组合 | 参考视觉，不直接搬模板 |
| [Ant Design Pro](https://github.com/ant-design/ant-design-pro) | MIT | 企业级后台的信息架构、Dashboard/Workplace/Monitor 三类首页 | 当前不建议切到 AntD/Umi 大栈 |
| [Grafana](https://github.com/grafana/grafana) | AGPL-3.0 | 变量筛选、动态 Dashboard、告警、钻取、图表布局 | AGPL，不复制代码，只参考产品逻辑 |

### 图表与表格技术参考

| 来源 | 可参考点 | 初步建议 |
| --- | --- | --- |
| [Apache ECharts](https://echarts.apache.org/) | 图表类型多，Canvas/SVG，可做互动 BI、漏斗、热力、趋势、堆叠图 | 推荐作为运营总览 BI v1 的图表引擎候选 |
| [Recharts](https://recharts.org/) | React 组件式图表，写法直观 | 适合轻量 React 图表，但视觉冲击力和复杂交互不如 ECharts |
| [TanStack Table](https://tanstack.com/table/latest) | 分页、筛选、排序、列显隐、受控状态 | 后续替换手写表格时可用；P3-06R 不强制引入 |

## 推荐技术取舍

当前 `frontend/package.json` 只有 React、React DOM、lucide-react，没有 UI 框架和图表库。下一步不建议一次性引入 AntD、MUI 或完整 shadcn 体系，因为这会把项目变成重构工程。

推荐路线：

1. 壳层、布局、卡片、按钮继续用现有 CSS 体系修。
2. 运营总览图表优先引入 `echarts`，用极少数自封装组件承接。
3. 表格先保留现有实现，只补分页、筛选、空态和视觉；等数据量变大再评估 `@tanstack/react-table`。
4. shadcn-admin、Tremor、Ant Design Pro、Grafana 只作为布局和信息架构参考。

## 工程阶段计划

### 阶段 1：中台壳层修复

目标：解决左侧栏随页面整体滚动的问题，建立标准中台布局底座。

预计耗时：0.5 - 1 天。

任务：

- 调整 `.app-shell` 为固定视口高度。
- 让 body 不承担主滚动，改由 `.workspace` 或 `.workspace-page` 承担右侧滚动。
- 左侧 `.sidebar` 保持 100dvh，独立滚动自己的导航内容。
- 顶部 `.topbar` 视情况设为 sticky，保证右侧滚动时页面标题和操作区可见。
- 移动端单独处理，不能让 280px 左栏挤压内容。

可能涉及文件：

- `frontend/src/styles.css`
- `frontend/src/App.tsx`

验收标准：

- 桌面 1440x1000：滚动右侧内容时左侧黑色导航不移动。
- 桌面 1280x800：左侧导航可独立滚动，不遮挡右侧。
- 移动 390x844：页面不横向溢出，导航不压扁内容。
- 浏览器截图保存到证据目录。

验证命令：

```bash
cd frontend && npm run typecheck
cd frontend && npm run build
```

人工验证：

- 打开 `#overview`。
- 鼠标滚轮滚动。
- 观察左侧栏是否固定、右侧是否独立滚动。

### 阶段 2：运营总览 BI 首页升级

目标：把首页从普通卡片堆叠升级为“运营指挥舱”。

预计耗时：1.5 - 2.5 天。

任务：

- 重新定义首页首屏结构：
  - 顶部：今日核心指标带趋势。
  - 中部：会话漏斗、渠道分布、质量趋势、知识缺口。
  - 右侧或下方：待处理队列、异常 TOP、下一步建议。
- 增加时间范围切换：今日、近 7 天、近 30 天。
- 增加渠道筛选：全部、官网、企业微信、公众号、电商渠道。
- 增加图表：
  - 会话处理漏斗。
  - 渠道进线/转人工堆叠柱图。
  - AI 命中率/转人工率趋势线。
  - 知识缺口或错因 Pareto。
  - 待处理队列热力或优先级矩阵。
- 卡片减少大面积空白，把“数字 + 趋势 + 动作”放在同一个组件里。
- 首页每个指标都能跳转到对应工作区。

可能涉及文件：

- `frontend/package.json`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- 可能新增 `frontend/src/components/charts/`
- 可能新增 `backend/app/api/ops_dashboard.py` 或复用现有运维/质量接口聚合

建议图表引擎：

- 第一候选：`echarts`
- 理由：图表类型丰富、适合做更有视觉冲击力的 BI、支持 Canvas/SVG、后续可扩展到热力图和复杂趋势。
- 风险：需要封装 React 组件，避免在 `App.tsx` 中堆 option。

验收标准：

- 首屏不再是纯卡片堆叠，而是有明确运营指挥舱层级。
- 每个图表都有标题、口径、时间范围、空态。
- 图表在无真实数据时显示合理 demo/fixture 状态，不显示乱码或空白。
- 点击核心指标能进入对应页面。
- 桌面和移动截图通过。

### 阶段 3：后端权限契约收口

目标：让后端真实权限边界和前端按钮权限一致。

预计耗时：1 - 1.5 天。

任务：

- 为 tenant/channel/contact foundation 接口增加登录和命名权限。
- 把无 token bootstrap owner 改为仅开发模式允许。
- workflow、reply orchestration、trusted inbound worker 迁到对应权限：
  - `conversation.read`
  - `conversation.manage`
  - `outbox.read`
  - `outbox.manage`
  - `channel.read`
  - `channel.manage`
- 为 owner/admin/agent/viewer 建 contract smoke 测试。

可能涉及文件：

- `backend/app/api/tenants.py`
- `backend/app/api/auth.py`
- `backend/app/api/workflows.py`
- `backend/app/api/inbound_worker.py`
- `backend/app/api/reply_orchestrator.py`
- `backend/app/core/rbac.py`
- `backend/tests/`

验收标准：

- 未登录访问 foundation 接口返回 401。
- viewer 不能写租户、渠道、联系人、outbox。
- agent 只能访问坐席工作需要的读写范围。
- owner/admin 保持管理能力。
- 相关测试通过。

验证命令：

```bash
.venv/bin/python -m pytest backend/tests -q
```

### 阶段 4：前端按权限请求数据

目标：前端不再无脑请求所有模块，降低 403 噪音。

预计耗时：0.5 - 1 天。

任务：

- 抽出 `canReadConversation`、`canManageConversation`、`canReadOps`、`canReadKnowledge` 等权限判断。
- 登录成功后只刷新当前角色可读的数据。
- 顶部“检查连接”按钮也按权限刷新，而不是全量刷新。
- 对无权限模块显示“无权限/联系管理员”，不显示错误堆栈或红色失败态。

可能涉及文件：

- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/data/navigation.ts`

验收标准：

- owner/admin/agent/viewer 四类身份都能正常进入自己可见页面。
- viewer 不产生一串 403。
- 无权限模块不会出现在导航里，或显示明确无权限说明。

### 阶段 5：坐席工作台一屏闭环

目标：让坐席在一个主界面里完成真实客服工作，而不是在多个页面之间跳。

预计耗时：2 - 3 天。

任务：

- 左栏：会话列表，展示渠道、等待时间、风险、最后消息、是否 AI 已草拟。
- 中栏：对话线程，展示客户消息、AI 草稿、历史回复。
- 右栏：客户资料、知识引用、风险提示、处理动作。
- AI 草稿支持编辑。
- 支持写内部备注。
- 支持确认引用。
- 支持“批准进入待发送”。
- 支持“转人工/标记知识缺口/标记高风险”。
- 支持发送前确认入口，但不打开真实外发。

可能涉及文件：

- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/src/api/client.ts`
- 可能拆分 `frontend/src/components/conversation/`
- 后端可能补充少量组合接口或复用 review/outbox API

验收标准：

- 一个待审核会话可以在同一屏完成：查看消息、编辑 AI 草稿、确认引用、批准、进入待发送。
- 操作后 outbox 状态正确变化。
- 有内部备注/风险原因记录。
- 不触达真实外部平台。

### 阶段 6：渠道连接器中心第一片

目标：让渠道页从“状态说明”变成“可配置、可测试、可排障”的连接器中心。

预计耗时：1.5 - 2 天。

任务：

- 建立渠道连接器表格：
  - 渠道名称
  - 当前状态
  - 官方授权状态
  - Webhook URL 状态
  - Secret 引用状态
  - 最近事件
  - 最近错误
  - 测试入口
- 先覆盖官网客服沙盒和企业微信/微信客服。
- 显示“未接入原因”和“下一步需要客户提供什么”。
- 所有真实平台仍保持官方 API/服务商授权边界。

可能涉及文件：

- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `backend/app/api/channel_connectors.py` 或现有渠道 API
- `backend/tests/`

验收标准：

- 客户和我们内部都能一眼看懂：哪个渠道已接、哪个待配置、哪里报错。
- 有回调 URL、验证状态、最近事件和测试说明。
- 不出现“Hook、外挂、模拟点击、个人号群控”等正式交付禁用路径。

### 阶段 7：轻量模块化

目标：降低 `App.tsx` 和 `styles.css` 继续膨胀的风险。

预计耗时：1 - 2 天。

任务：

- 先拆新增模块，不大规模重构旧代码。
- 新增图表组件、布局组件、会话组件时放入独立目录。
- 保持每次拆分后都能 build。

建议目录：

```text
frontend/src/components/layout/
frontend/src/components/dashboard/
frontend/src/components/conversation/
frontend/src/components/channels/
frontend/src/components/charts/
```

验收标准：

- 新增功能不继续把 `App.tsx` 推到更不可维护。
- 不做大规模无业务价值重构。

## 建议执行顺序

1. 阶段 1：中台壳层修复。
2. 阶段 2：运营总览 BI 首页升级。
3. 阶段 3：后端权限契约收口。
4. 阶段 4：前端按权限请求数据。
5. 阶段 5：坐席工作台一屏闭环。P3-06R-03A 已完成前端第一片，仍需 P3-06R-03B 做真实登录端到端动作 smoke。
6. 阶段 6：运营总览服务端聚合。P3-06R-04C 已完成第一片：新增只读聚合接口、`dashboard.read` 权限和前端总览接入。
7. 阶段 7：渠道连接器中心第一片。
8. 阶段 8：轻量模块化随阶段 2/5/7 同步执行，不单独开大重构。

原因：

- 壳层滚动是用户立刻能感知的问题，优先修。
- 首页是客户第一印象，应该尽快升级到更像智能客服运营中台。
- 权限契约是安全基础，必须在真实试点前收口。
- 坐席闭环是系统从“看板”变成“客服工具”的关键。
- 渠道连接器中心决定客户能否理解系统如何接企微、公众号、电商平台。

## 预计总工期

| 阶段 | 工期 |
| --- | ---: |
| 壳层修复 | 0.5 - 1 天 |
| 运营总览 BI | 1.5 - 2.5 天 |
| 后端权限契约 | 1 - 1.5 天 |
| 前端权限请求 | 0.5 - 1 天 |
| 坐席闭环 | 2 - 3 天 |
| 渠道连接器中心 | 1.5 - 2 天 |
| 模块化整理 | 1 - 2 天，穿插进行 |

合计：约 7 - 11 个工作日。

如果压缩执行，建议先做阶段 1、2、3、4，形成一个明显更像商用中台的版本，预计 3.5 - 6 天。

## 本轮不做

- 不做真实外发。
- 不做全渠道一次性接入。
- 不做 Kubernetes、HPA、服务网格。
- 不做重型字段脱敏和字段 allowlist 深挖。
- 不做完整 UI 框架迁移。
- 不把 AGPL 项目代码复制进商业系统。

## 已完成补充：P3-06R-04C

2026-07-01 已完成 `P3-06R-04C 运营总览服务端聚合接口`：

- 后端新增 `GET /api/tenants/{tenant_id}/ops/dashboard`。
- `dashboard.read` 从 viewer-only 修正为 owner/admin/viewer 可读，agent 不可读。
- 聚合入站、审核、待发送、失败复盘、队列、知识缺口、工单、线索和评测质量信号。
- 接口不返回客户原文和待发送正文，跨租户仍为 404。
- 前端首页正式登录后优先读取服务端聚合，演示模式和接口不可用时回退到本地样本。
- 验证文档：`docs/P3-06R-04C_OPS_DASHBOARD_AGGREGATION.md`。

验证：

- `backend/tests/test_p3_06r_ops_dashboard_api.py` 通过。
- 相关后端 RBAC/运维回归 16 条通过。
- `frontend` typecheck 和 build 通过。
- Chrome 本地预览可打开，首页图表可渲染。

## 下一施工片建议

下一轮建议优先进入 `P3-06R-03B`：

目标：验证坐席工作台一屏闭环在真实登录和后端状态下可以完成编辑草稿、填写备注、批准审核、生成 outbox 草稿和确认待发送。

交付：

- 一个 open human review task 的端到端点击 smoke。
- 断言人审任务已批准，outbox draft 已生成，确认待发送后仍无外部平台写入。
- 保留 P3-06R-03A 的桌面和移动端布局截图证据。

停止条件：

- 如果缺少可用测试账号或 open review fixture，则先补后端 fixture/smoke，不伪造真实端到端成功。
- 如果审批或 outbox 状态变更失败，停止扩展渠道中心，先修复坐席主路径。
- 如果真实登录端到端 smoke 已经通过，再进入 `P3-06R-05 渠道连接器中心第一片`，或继续做 `P3-06R-04D 运营总览统计缓存/物化层`。
