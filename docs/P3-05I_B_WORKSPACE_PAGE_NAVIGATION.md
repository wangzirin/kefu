# P3-05I-B 中控台页面化导航修复

## Engineering Control Card

- 阶段：P3-05I-B
- 目标：把商户中控台从“左侧菜单跳到长页锚点”修正为“左侧菜单切换独立工作区页面”。
- 范围：仅修复前端导航、页面渲染结构和工作区视觉边界，不新增真实渠道发送能力。
- 输入：用户指出总览、审核、待发送等模块仍然像一整页连续内容，没有真正分割。
- 完成标准：每个菜单只渲染一个 `.workspace-page`，顶部标题随菜单变化，左侧只有一个 active 状态，URL hash 不再触发 DOM 锚点滚动。

## 修复前问题

旧页面虽然有左侧菜单和 hash，但页面主体仍然容易呈现为一整页连续模块：

- 总览、审核、待发送、渠道、知识库、评测等模块被用户感知为没有切开。
- hash 与组件内部 `id` 同名，浏览器会把页面直接锚到中段内容，顶栏可能被顶出首屏。
- 左侧菜单更像长页目录，不像真实客服中台的工作区切换。

这个问题会影响客户第一印象。商户中台应该让使用者明确知道自己当前处于“总览、会话、审核、待发送、知识库、渠道、模型、评测、设置”哪一个工作区，而不是在一张长页面里找模块。

## 本轮改动

### 1. 左侧导航改为工作区入口

`frontend/src/data/navigation.ts` 已统一使用独立工作区 hash：

- `#overview`：运营总览
- `#conversations`：会话收件箱
- `#reviews`：人工审核
- `#outbox`：待发送草稿
- `#contacts`：联系人中心
- `#leads`：线索跟进
- `#knowledge`：知识库运营
- `#channels`：渠道接入
- `#model`：模型路由
- `#evals`：质量评测
- `#settings`：系统设置

### 2. 主体改为单 active section 渲染

`frontend/src/App.tsx` 新增 `WorkspaceSection` 状态和 `workspaceContent` switch。

现在页面主体只会根据当前工作区渲染一个内容块：

- 总览页只显示运营队列、会话预览、当前证据和渠道健康摘要。
- 会话页只显示会话收件箱。
- 审核页只显示人工审核收件箱和证据详情。
- 待发送页只显示待发送草稿。
- 知识库页只显示知识文档运营。
- 渠道页只显示官网沙盒、渠道健康和失败复盘。
- 模型页只显示模型路由说明。
- 评测页只显示知识评测与质量。
- 联系人、线索、设置当前保持规划态，不伪装成已完成能力。

### 3. 顶部标题跟随当前工作区

顶部标题、短标签和说明文字由 `getWorkspacePageMeta` 统一生成。

这样用户切换菜单时，首屏会明确显示：

- 当前页面名称
- 当前页面职责
- 当前是否是已完成能力或规划态
- 当前页面不会混入其他模块的主内容

### 4. 移除 hash 与 DOM id 同名锚点

组件内部 `id` 已改为 `workspace-*` 命名，例如：

- `workspace-overview`
- `workspace-conversations`
- `workspace-reviews`
- `workspace-outbox`
- `workspace-knowledge`
- `workspace-channels`
- `workspace-model`
- `workspace-evals`

这样 URL 中的 `#overview` 只作为路由状态，不再触发浏览器原生锚点滚动。

### 5. 增加工作区布局样式

`frontend/src/styles.css` 新增：

- `.workspace-page`
- `.workspace-page-grid`
- `.workspace-page-grid.two-column`
- `.workspace-page-grid.stacked`
- `.planning-panel`
- `.model-routing-panel`

这些样式用于让不同工作区有明确页面边界，而不是视觉上连成一整页。

## 已验证

### 构建验证

命令：

```bash
npm run build
```

结果：

- TypeScript 编译通过。
- Vite 构建通过。

### 浏览器路由验证

使用系统 Chrome 进行本地预览验证：

- 地址：`http://127.0.0.1:5173/#overview`
- 验证菜单：
  - `#overview`
  - `#conversations`
  - `#reviews`
  - `#outbox`
  - `#contacts`
  - `#leads`
  - `#knowledge`
  - `#channels`
  - `#model`
  - `#evals`
  - `#settings`

验证结果：

- 每个 hash 只有 1 个 `.workspace-page`。
- 每个页面都有正确的顶部标题。
- 每次只有 1 个左侧菜单 active。
- 当前 hash 不再存在同名 DOM id。
- 打开页面后 `scrollY=0`，顶栏不会被锚点顶掉。

### 移动端宽度验证

使用 390px 移动视口逐页验证：

- 11 个工作区均为 `innerWidth=390`、`scrollWidth=390`。
- 11 个工作区均只有 1 个 `.workspace-page`。
- 页面打开后均保持 `scrollY=0`。
- 未发现页面化改动引入横向溢出。

## 当前边界

本轮只修复中控台页面结构和视觉逻辑，不代表以下事项完成：

- 真实企业微信自动回复。
- 公众号、抖音、小红书、淘宝、京东、拼多多真实接入。
- 真实外发 API。
- 完整联系人画像。
- 完整线索 CRM。
- 完整 RBAC。
- 完整工单和 SLA。
- 生产级多租户运维后台。

## 后续建议

页面化结构已经修正，下一步不应再继续堆页面，而应进入真实业务能力：

1. P3-05J：联系人和线索画像。
2. P3-05K：知识缺口闭环。
3. P3-05M：坐席权限、工单和 SLA。
4. 条件具备时并行推进企业微信公网 HTTPS 回调 smoke。
