# P3-06R-01 中台壳层与运营总览升级记录

日期：2026-07-01

## 本片目标

根据 `P3-06R_ENGINEERING_OPTIMIZATION_PLAN.md` 的第一施工片，先修复用户已感知到的两个前端核心问题：

1. 左侧黑色导航栏不应跟随整页滚动，桌面端应固定在视口左侧，右侧白色工作区独立滚动。
2. 运营总览不应只是普通模块堆叠，需要升级为更像 BI 数据中台的运营指挥舱。

本片不处理真实外发、不处理备案/部署、不处理重型字段脱敏、不接入真实外部渠道。

## 已完成改动

### 1. 中台壳层滚动修复

改动文件：

- `frontend/src/styles.css`

关键变化：

- `.app-shell` 改为固定 `100dvh` 高度并隐藏整体溢出。
- `.sidebar` 保持 `100dvh`，只滚动自身导航内容。
- `.workspace` 成为右侧独立滚动容器，承担主内容滚动。
- `.topbar` 在桌面端变成右侧工作区内的 sticky 顶栏。
- 移动端取消固定视口壳层，恢复自然页面滚动。
- 移动端导航从整段纵向菜单改成横向紧凑导航，避免首屏被菜单完全占用。

### 2. 运营总览升级为 BI 指挥舱第一版

改动文件：

- `frontend/src/App.tsx`
- `frontend/src/styles.css`

关键变化：

- 将原先 5 个普通运营卡片升级为 `ops-bi-shell`。
- 新增 4 个核心指标卡：
  - 试点进线样本
  - AI 草稿覆盖
  - 人工审核压力
  - 异常与缺口
- 新增处理漏斗：
  - 入站样本
  - AI 已草拟
  - 人工审核
  - 待确认发送
- 新增渠道矩阵：
  - 官网客服沙盒
  - 企业微信客服
  - 公众号/微信
  - 电商渠道
- 新增质量诊断：
  - 知识命中
  - 引用覆盖
  - 期望词覆盖
  - 人工复盘占比
- 新增下一步动作：
  - 优先处理高风险审核
  - 确认待发送草稿
  - 修复知识缺口

说明：当前 BI 数据仍基于试点口径，来自审核池、待发送、失败复盘和评测结果；没有把未完成的真实外发或全渠道能力包装成已上线能力。

## 验证结果

命令验证：

```bash
cd frontend && npm run typecheck
# passed

cd frontend && npm run build
# passed
```

构建输出：

- CSS：约 65.62 kB，gzip 后约 11.29 kB。
- JS：约 426.91 kB，gzip 后约 117.55 kB。

浏览器验证：

- 后端健康检查：`http://127.0.0.1:8081/api/health` 返回 `status=ok`。
- 前端本地预览：`http://127.0.0.1:5173/#overview`。
- 使用系统 Chrome + Playwright 自动化验证。

桌面端 1440x1000：

- `bodyScrollHeight=1000`
- `bodyClientHeight=1000`
- `bodyOverflow=hidden`
- `workspaceScrollHeight=2795`
- `workspaceClientHeight=1000`
- `workspaceOverflow=auto`
- 滚动后 `bodyScrollY=0`
- 滚动后 `sidebarTop=0`
- 滚动后 `workspaceScrollTop=900`
- BI 卡片数量：4
- BI 图表卡数量：4

移动端 390x844：

- `innerWidth=390`
- `scrollWidth=390`
- `bodyOverflow=auto`
- `navListHeight=96`
- `workspaceTop≈264`
- BI 卡片数量：4
- BI 图表卡数量：4

截图证据目录：

`/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/docs/p3_06r_01_layout_bi_qa/`

包含：

- `desktop-overview-top.png`
- `desktop-overview-scrolled.png`
- `mobile-overview.png`

## 当前剩余问题

- 移动端已解决横向溢出和超长侧栏问题，但整体移动端仍只是可用，不是最终移动优雅版。
- 导航里仍存在 `P3-06UI` 这类工程标签，后续客户演示收口时应去掉。
- 总览 BI 目前使用轻量 CSS 图表，没有引入 ECharts；后续如果需要更强交互，再单独做图表引擎引入。
- 运营总览仍复用当前已加载数据，没有新增后端聚合 API；后续可在 P3-06R-02 或 P3-06R-03 引入服务端聚合指标。

## 2026-07-01 二次修复追加记录

用户复查后指出首页滚动体验仍不够可靠。本轮追加 `P3-06R-01B_LAYOUT_SCROLL_REPAIR.md`，对壳层滚动做二次修复和更严格浏览器验证：

- `App.tsx` 新增 `workspaceRef`，桌面端 hash 切换时滚动右侧 `.workspace`，不再把 `window.scrollTo()` 当作桌面主路径。
- `styles.css` 进一步收紧 `.app-shell`、`.sidebar`、`.workspace` 的桌面滚动边界。
- 移动端把 `html/body/#root` 改为自然高度，修复内容高度被锁到视口的问题。
- 桌面端验证：滚动后 `bodyScrollY=0`、`documentScrollTop=0`、`sidebarTop=0`、`workspaceScrollTop=1795`、`overflowX=false`。
- 移动端验证：滚动后 `bodyScrollY=1200`、`scrollingElementScrollTop=1200`、`scrollWidth=390`、`innerWidth=390`、`overflowX=false`。
- 截图证据目录：`/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/output/p3_06r_layout_scroll/`。

## 下一步建议

P3-06R-02 已在后续完成。当前下一步建议：

1. 进入 `P3-06R-03 坐席工作台一屏闭环`：把会话列表、对话线程、AI 草稿编辑、知识引用确认、内部备注和进入待发送集中到同一工作区。
2. 或进入 `P3-06R-04 渠道连接器中心第一片`：把官网、企业微信、公众号和电商渠道的配置状态、回调 URL、密钥引用、最近事件和最近错误做成连接器中心。
3. 继续保留壳层和 BI 首页作为后续页面质量基线。
