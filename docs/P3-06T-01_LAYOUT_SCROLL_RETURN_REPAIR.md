# P3-06T-01 壳层滚动返修验收

日期：2026-07-01

## Engineering Control Card

- Stage: P3-06T-01 壳层滚动返修验收。
- 来源计划: `docs/P3-06T_NEXT_FOUR_ISSUES_ENGINEERING_PLAN.md` 的问题一。
- 本片客户可见价值: 在小窗口、窄桌面或浏览器侧边栏压缩视口时，左侧黑色导航不再跟随整页滚动，右侧白色工作区承担主滚动。
- 本片不是: 运营总览 BI 重做、数据口径重做、真实外发、真实渠道接入、生产部署。
- 外部动作: 无真实外发、无模型调用、无生产数据库动作。
- 本片停止条件: 721px 及以上桌面/窄桌面视口必须满足 `bodyScrollY=0`、`.workspace.scrollTop` 变化、`.sidebarTop=0`；720px 及以下按手机/窄屏自然页面滚动处理且无横向溢出。
- 写回位置: 本文件、`README.md`、`docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md`、Superpowers P3 计划、Project_012 执行记录/关键决策/文件索引/复盘。

## 真实问题

此前 P3-06S-01 已把 900px 小窗口从移动整页滚动修回窄桌面壳层，但用户真实预览仍反馈“首页往下滑时，左侧黑色导航也跟着滑”。本轮重新测量后确认：

- 1440、1280、1024、900 都已经是右侧 `.workspace` 独立滚动。
- 760px 仍进入了移动整页滚动。
- 760px 是典型“小窗口/窄桌面”尺寸，用户在 Chrome 侧栏、浏览器缩放或窄窗口预览时很容易落到这个区间。

## 无效基线

第一次 CDP 测量没有点击“开发演示进入”，实际测到的是登录页，`.workspace` 和 `.sidebar` 均为 `null`。该结果只用于排除错误测量方法，不作为产品验收证据。

无效输出目录:

```text
output/p3_06t_layout_baseline/
```

## 有效基线

有效基线在进入开发演示工作台后采集，输出目录:

```text
output/p3_06t_layout_baseline_workspace/
```

关键失败点:

| 视口 | 滚动后 bodyScrollY | 滚动后 workspaceScrollTop | 滚动后 sidebarTop | 结论 |
| --- | ---: | ---: | ---: | --- |
| 1440x900 | 0 | 900 | 0 | 合格 |
| 1280x800 | 0 | 900 | 0 | 合格 |
| 1024x768 | 0 | 900 | 0 | 合格 |
| 900x768 | 0 | 900 | 0 | 合格 |
| 760x768 | 900 | 0 | -900 | 不合格，进入整页滚动 |
| 390x844 | 900 | 0 | -900 | 手机自然滚动，符合移动端预期 |

## 修复内容

### 1. 窄桌面断点下探

文件:

```text
frontend/src/styles.css
```

修改:

- 将窄桌面覆盖规则从 `@media (min-width: 761px) and (max-width: 960px)` 下探到 `@media (min-width: 721px) and (max-width: 960px)`。
- 将该区间侧边栏从 `240px` 调整为 `224px`，减少对右侧工作区的挤压。
- 将该区间侧边栏内边距从 `20px 14px` 收紧为 `18px 12px`。

结果:

- 721px 到 960px 都保持中台双列壳层。
- 720px 及以下仍进入手机/窄屏自然滚动。

### 2. React 滚动目标同步

文件:

```text
frontend/src/App.tsx
```

修改:

- hash 切换后重置滚动位置时，从 `matchMedia("(min-width: 961px)")` 改为 `matchMedia("(min-width: 721px)")`。

结果:

- 721px 及以上的窄桌面视口，hash 切换后重置 `.workspace`，而不是误调 `window.scrollTo()`。

### 3. 可重复验收脚本

文件:

```text
scripts/check_p3_06t_layout_scroll.mjs
```

能力:

- 连接隔离 Chrome DevTools 端口。
- 打开本地前端。
- 点击“开发演示进入”。
- 采集 1440、1280、1024、900、760、721、720、390 八个视口。
- 读取 `bodyScrollY`、`.workspace.scrollTop`、`.sidebarTop`、横向溢出和滚动容器样式。
- 保存截图、`scroll-metrics.json` 和 `scroll-summary.json`。
- 发现断点失败时退出码为非 0。

运行前提:

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5176 --strictPort
```

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless=new \
  --remote-debugging-port=9224 \
  --user-data-dir=/tmp/wanfa-standard-ops-chrome-qa \
  --disable-gpu \
  --no-first-run \
  --no-default-browser-check \
  about:blank
```

```bash
node scripts/check_p3_06t_layout_scroll.mjs
```

## 修复后验收

正式输出目录:

```text
output/p3_06t_layout_after/
```

正式脚本结果:

```json
{
  "status": "passed",
  "checked": [
    "desktop-1440",
    "desktop-1280",
    "desktop-1024",
    "narrow-900",
    "narrow-760",
    "boundary-721",
    "boundary-720",
    "mobile-390"
  ]
}
```

关键数值:

| 视口 | 滚动后 bodyScrollY | 滚动后 workspaceScrollTop | 滚动后 sidebarTop | 横向溢出 | 结论 |
| --- | ---: | ---: | ---: | --- | --- |
| 1440x900 | 0 | 900 | 0 | 否 | 合格 |
| 1280x800 | 0 | 900 | 0 | 否 | 合格 |
| 1024x768 | 0 | 900 | 0 | 否 | 合格 |
| 900x768 | 0 | 900 | 0 | 否 | 合格 |
| 760x768 | 0 | 900 | 0 | 否 | 合格 |
| 721x768 | 0 | 900 | 0 | 否 | 合格 |
| 720x768 | 900 | 0 | -900 | 否 | 手机/窄屏自然滚动 |
| 390x844 | 900 | 0 | -900 | 否 | 手机自然滚动 |

截图抽检:

- `output/p3_06t_layout_after/narrow-760-after.png`: 左侧导航固定，右侧工作区滚动。
- `output/p3_06t_layout_after/mobile-390-after.png`: 手机端自然滚动，无横向溢出。

## 代码验证

```bash
cd frontend
npm run typecheck
```

结果: 通过。

```bash
cd frontend
npm run build
```

结果: 通过。Vite 仍提示部分 chunk 大于 500kB，这是既有包体提示，不是本片错误。

## Stage Completion

- Stage: P3-06T-01 壳层滚动返修验收。
- What changed: 窄桌面断点从 761px 下探到 721px；React hash 滚动重置同步改为 721px 以上滚动 `.workspace`；新增可重复 CDP 滚动验收脚本。
- What was verified: 1440、1280、1024、900、760、721、720、390 八个视口；`npm run typecheck`；`npm run build`。
- What remains not done: 未重做运营总览 BI，未做首页数据口径下一片，未改渠道、模型或真实外发。
- Whether this was customer-visible: 是，小窗口预览和窄桌面体验直接改善。
- Whether this was only evaluation: 否，包含前端壳层修复和可重复验收脚本。
- Next stage: P3-06T-02 首页数据口径收紧，随后 P3-06T-03 运营总览 BI 重做。

