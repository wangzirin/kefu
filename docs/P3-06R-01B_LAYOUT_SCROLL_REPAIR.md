# P3-06R-01B 中台壳层滚动二次修复

日期：2026-07-01

## Engineering Control Card

- Stage: P3-06R-01B
- 当前主线阶段: P3-06R 工程性优化、升级、修复计划
- 上一阶段真正完成: P3-06R-01 已完成壳层和运营总览 BI 第一版；P3-06R-02 已完成后端权限契约与前端按权限刷新资源。
- 上一阶段明确没有完成: 用户实测仍指出首页滚动时左侧黑色导航栏会跟随整页滑动；移动端滚动边界也需要重新验证。
- 本轮要交付的客户可见价值: 中台壳层像成熟后台产品一样工作，桌面端左侧导航固定，右侧工作区独立滚动；移动端保持自然纵向滚动且无横向溢出。
- 本轮是否只是评测: 否，本轮包含前端壳层代码修复和浏览器验证。
- 本轮不做什么: 不重做 BI 首页，不引入图表库，不改后端，不打开真实外发，不接真实渠道。
- 外部风险: 无真实平台、无真实客户数据、无模型付费调用、无生产部署。
- 需要用户授权的动作: 无。
- 验证方式: `npm run typecheck`、`npm run build`、Playwright 桌面/移动端滚动验证和截图。
- 写回文件: 本阶段卡、产品化总控手册、Superpowers 工程计划、Project_012 执行记录/文件索引/复盘。
- 下一阶段: P3-06R-03 坐席工作台一屏闭环，或 P3-06R-04 渠道连接器中心第一片。

## 问题复核

P3-06R-01 已把 `.app-shell`、`.sidebar`、`.workspace` 调整成中台壳层，但用户实测反馈说明旧验收仍不够严格。进一步检查发现两个风险点：

1. `App.tsx` 的 hash 路由切换仍调用 `window.scrollTo()`，桌面端语义上仍在操作整页滚动。
2. 移动端虽然把 `.workspace` 设为 `overflow: visible`，但 `html/body/#root` 仍保持 `height: 100%`，导致移动端文档滚动高度可能被锁到视口高度。

## 本轮改动

### 1. 桌面端滚动目标改为右侧工作区

文件：

- `frontend/src/App.tsx`

改动：

- 新增 `workspaceRef`。
- hash 路由切换时，桌面端优先调用 `workspaceRef.current.scrollTo({ top: 0 })`。
- 只有移动端才继续使用 `window.scrollTo()`。
- `.workspace` 根节点绑定 `ref={workspaceRef}`。

### 2. 壳层 CSS 边界收紧

文件：

- `frontend/src/styles.css`

改动：

- `.app-shell` 增加 `max-width: 100vw` 和 `overscroll-behavior: none`。
- `.sidebar` 增加 `position: sticky; top: 0; max-height: 100dvh; overflow-x: hidden; overscroll-behavior: contain`。
- `.workspace` 增加 `min-height: 0; overscroll-behavior: contain; scroll-behavior: auto`。
- 移动端 `html/body/#root` 改为 `height: auto; min-height: 100%`，恢复自然页面滚动。

## 验证结果

命令验证：

```bash
cd frontend && npm run typecheck
# passed

cd frontend && npm run build
# passed
```

浏览器验证地址：

```text
http://127.0.0.1:5175/#overview
```

桌面端 1440x1000 验证：

- 滚动前 `bodyScrollY=0`
- 滚动前 `documentScrollTop=0`
- 滚动前 `sidebarTop=0`
- 滚动前 `workspaceScrollTop=0`
- 滚动后 `bodyScrollY=0`
- 滚动后 `documentScrollTop=0`
- 滚动后 `sidebarTop=0`
- 滚动后 `workspaceScrollTop=1795`
- `workspaceScrollHeight=2795`
- `workspaceClientHeight=1000`
- `overflowX=false`

结论：桌面端滚动已由右侧 `.workspace` 承担，左侧黑色导航栏不再跟随整页滑动。

移动端 390x844 验证：

- 滚动前 `scrollingElementScrollHeight=6363`
- 滚动前 `scrollWidth=390`
- 滚动前 `innerWidth=390`
- 滚动前 `overflowX=false`
- 滚动后 `bodyScrollY=1200`
- 滚动后 `scrollingElementScrollTop=1200`
- 滚动后 `overflowX=false`
- `.workspace` 为 `overflow: visible`

结论：移动端恢复自然页面滚动，没有横向溢出。

Console：

- `consoleErrorCount=0`

截图证据：

- `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/output/p3_06r_layout_scroll/p3_06r_layout_scroll_desktop.png`
- `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/output/p3_06r_layout_scroll/p3_06r_layout_scroll_mobile.png`

## 当前边界

- 本轮只修复壳层滚动，不代表首页 BI 已达到最终视觉标准。
- 本轮没有新增后端聚合指标接口。
- 本轮没有接入 ECharts、Recharts 或其他图表库。
- 本轮没有打开真实外发，也没有改变任何渠道连接器状态。

## 下一步

建议进入 `P3-06R-03 坐席工作台一屏闭环`，重点把会话列表、聊天线程、AI 草稿编辑、知识引用确认、内部备注和进入待发送集中到同一主工作区。

如果先解决客户实施可理解性，则进入 `P3-06R-04 渠道连接器中心第一片`，把官网、企业微信、公众号和电商渠道的配置状态、回调 URL、密钥引用、最近事件和最近错误做成连接器中心。
