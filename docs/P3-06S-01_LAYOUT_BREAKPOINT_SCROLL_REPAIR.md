# P3-06S-01 中台壳层窄桌面滚动修复

日期：2026-07-01

后续返修说明：P3-06T-01 已把本文件的 761px 窄桌面下限进一步下探到 721px，并新增 760、721、720 断点验收。后续以 `docs/P3-06T-01_LAYOUT_SCROLL_RETURN_REPAIR.md` 和 `scripts/check_p3_06t_layout_scroll.mjs` 作为壳层滚动最新验收基准。

## Engineering Control Card

- Stage: P3-06S-01
- 当前主线阶段: P3-06S UI、BI 与前后端口径工程优化
- 本轮要交付的客户可见价值: 在小窗口、窄桌面或浏览器缩放后，客服中台仍保持左侧导航固定、右侧工作区独立滚动，不再过早退化成整页滚动。
- 本轮是否只是评测: 否。本轮包含前端 CSS 修复、浏览器协议验收、截图证据、类型检查和生产构建。
- 本轮不做什么: 不重做运营总览 BI，不改后端聚合接口，不新增功能页，不打开真实外发。
- 需要用户授权的动作: 无。

## 问题复现

P3-06R-01B 已经修过桌面 1440/1280/1024 的壳层滚动，但本轮重新跑当前代码发现，宽度为 900px 时会触发 `@media (max-width: 960px)` 的移动布局：

- `.app-shell` 变成单列。
- `.sidebar` 变成 `position: static`。
- `.workspace` 变成 `overflow: visible`。
- body 恢复整页滚动。

这会造成用户在小窗口或浏览器缩放后看到黑色导航块跟着页面一起滑动。这个体验不符合中台类产品预期。

基线复现目录：

`/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/output/p3_06s_layout_baseline_demo/`

基线关键数据：

| 视口 | 滚动后 bodyScrollY | 滚动后 sidebarTop | 滚动后 workspaceScrollTop | 判断 |
| --- | ---: | ---: | ---: | --- |
| 1440x900 | 0 | 0 | 900 | 合格 |
| 1280x800 | 0 | 0 | 900 | 合格 |
| 1024x768 | 0 | 0 | 900 | 合格 |
| 900x768 | 900 | -900 | 0 | 不合格，过早进入整页滚动 |
| 390x844 | 900 | -900 | 0 | 合格，手机端允许自然滚动 |

## 本轮改动

文件：

- `frontend/src/styles.css`

改动：

- 新增 `@media (min-width: 761px) and (max-width: 960px)` 的窄桌面壳层覆盖规则。
- 在 761px 到 960px 区间恢复中台壳层：
  - `html/body/#root` 固定高度并隐藏整页滚动。
  - `.app-shell` 使用 `240px + 1fr` 双列。
  - `.sidebar` 固定 `100dvh`，只滚动自身导航。
  - `.workspace` 恢复为右侧独立滚动容器。
  - `.nav-list` 恢复纵向导航。
  - `.topbar` 保持右侧工作区内 sticky。
- 390px 手机端仍沿用移动布局和自然页面滚动。

## 验证结果

命令验证：

```bash
cd frontend && npm run typecheck
# passed

cd frontend && npm run build
# passed
```

构建说明：

- 构建通过。
- Vite 仍提示部分 chunk 超过 500 kB，主要来自现有图表依赖和应用体积，不是本次 CSS 修复导致的失败。

浏览器验证：

使用独立 headless Chrome + DevTools Protocol 访问：

`http://127.0.0.1:5176/#overview`

进入开发演示后，按 1440、1280、1024、900、760、390 六个视口采集滚动数据和截图。

验收截图目录：

`/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/output/p3_06s_layout_after/`

修复后关键数据：

| 视口 | 滚动后 bodyScrollY | 滚动后 sidebarTop | 滚动后 workspaceScrollTop | 判断 |
| --- | ---: | ---: | ---: | --- |
| 1440x900 | 0 | 0 | 900 | 合格 |
| 1280x800 | 0 | 0 | 900 | 合格 |
| 1024x768 | 0 | 0 | 900 | 合格 |
| 900x768 | 0 | 0 | 900 | 合格，已从整页滚动切回工作区滚动 |
| 760x844 | 900 | -900 | 0 | 合格，进入移动/窄屏自然滚动 |
| 390x844 | 900 | -900 | 0 | 合格，手机端自然滚动且无横向溢出 |

额外检查：

- 900x768：`appShellGrid=240px 660px`，`bodyOverflow=hidden`，`workspaceOverflowY=auto`，`overflowX=false`。
- 390x844：`scrollWidth=390`，`innerWidth=390`，`overflowX=false`。

## 当前边界

- 本轮只修复壳层断点和滚动，不代表运营总览 BI 已达到最终视觉目标。
- 当前 761px 到 960px 区间保留中台左侧栏，但右侧空间较窄，后续重做 BI 时应继续减少首屏卡片体积。
- 390px 手机端仍然是可用版移动布局，不是最终移动端精修版。

## 下一步

建议进入 `P3-06S-03 总览数据契约收口`，先让首页指标的数据来源、演示/真实聚合状态、时间范围和渠道筛选口径更硬。随后进入 `P3-06S-02 运营总览 BI 重做`，避免在口径不清的数据上继续做视觉升级。
