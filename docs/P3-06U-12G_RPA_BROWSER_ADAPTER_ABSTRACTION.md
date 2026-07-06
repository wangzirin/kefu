# P3-06U-12G RPA Browser Adapter 抽象第一片

日期：2026-07-02

## Engineering Control Card

- Stage: P3-06U-12G
- 当前主线阶段: AI+RPA 回复策略研究线，目标是验证非官方页面的坐席副驾驶 Draft-Only 能力。
- 上一阶段真正完成: P3-06U-12F 在抖音网页个人私信弹窗完成真实页 draft-only 探测，确认可定位输入框、写入测试草稿、清空草稿，没有发送消息，没有保存私聊原文。
- 上一阶段明确没有完成: 没有证明抖店飞鸽、企业号客服、官方 API、商家客服订单售后、多坐席队列或无人值守自动发送可用。
- 本轮要交付的客户可见价值: 把 RPA 执行层从单脚本变成可解释的 adapter 边界，后续能清楚区分“可控 CDP 测试页”和“已登录真实页面的辅助功能研究页”。
- 本轮是否只是评测: 否。本轮是工程结构和安全门禁收口。
- 本轮不做什么: 不操作真实抖音页面，不读取 Cookie/Token/LocalStorage，不保存页面截图，不点击发送，不接抖店/淘宝/拼多多真实后台。
- 外部风险: 如果未来把 Accessibility 直接做成自动发送能力，会进入平台风控、隐私和误发风险。本轮保持 contract-only fail-closed。
- 需要用户授权的动作: 任何真实页面发送、真实平台后台登录态读取、真实客户数据保存都需要另行明确授权。
- 验证方式: `node --check`、adapter capability 输出、Accessibility fail-closed 检查、本地 mock draft-only 链路回归。
- 写回文件: Project_012 执行记录、关键决策、文件索引、复盘与采坑。
- 下一阶段: P3-06U-12H 单平台真实页面 selector/locator profile 草稿，或继续保持人工 Computer Use 做单次 draft-only 探测。

## 1. 本片目标

P3-06U-12E 的脚本原本把 CDP 连接、页面选择器、消息读取、草稿写入、发送门禁全部写在一个文件里。P3-06U-12F 又证明：真实已登录页面不一定在 CDP 端口里。

所以本片先做一个小而必要的结构拆分：

```text
RPA Driver
  -> cdp_browser_adapter
  -> accessibility_browser_adapter
```

其中：

- `cdp_browser_adapter` 是当前可执行路径，服务本地 mock、localhost、专门以 remote debugging 打开的测试 Profile。
- `accessibility_browser_adapter` 先只作为 contract-only 边界存在，默认 fail-closed，不在 Node runner 里擅自操作当前桌面。

## 2. 新增和修改文件

### 2.1 Adapter 模块

```text
scripts/lib/rpa_browser_adapters.mjs
```

新增能力：

- `defaultSelectors`
- `loadSelectorProfile`
- `isLocalTarget`
- `describeRpaBrowserAdapters`
- `CdpBrowserAdapter`
- `AccessibilityBrowserAdapter`
- `createRpaBrowserAdapter`

### 2.2 原 RPA 脚本改造

```text
scripts/run_p3_06u_12e_rpa_browser_reply_feasibility.mjs
```

变化：

- 新增 `RPA_BROWSER_ADAPTER`，默认 `cdp_browser_adapter`。
- 新增 `RPA_PRINT_ADAPTER_CAPABILITIES=1`，只输出 adapter 能力，不连接浏览器、不访问后端。
- 原本的 mock draft-only 流程仍通过 CDP adapter 运行。
- 策略 dry-run metadata 写入 `browser_adapter`，便于后续审计区分执行层。

### 2.3 新增检查脚本

```text
scripts/check_p3_06u_12g_rpa_adapter_abstraction.py
```

检查项：

- 必要文件存在。
- 两个 `.mjs` 文件语法通过。
- `cdp_browser_adapter` 状态为 `implemented`。
- `accessibility_browser_adapter` 状态为 `contract_only_fail_closed`。
- 所有 adapter `sendAllowedByDefault=false`。
- 所有 adapter `persistsRawPrivateMessages=false`。
- Accessibility adapter 在 standalone Node runner 中调用 `open()` 会失败关闭。

## 3. 安全边界

本片保持以下边界：

- 默认不发送。
- 默认不保存原始私聊数据。
- 默认不保存截图。
- 默认不读取 Cookie、Token、LocalStorage。
- 不做验证码、风控、反检测、私有协议或 WebSocket 逆向。
- 不把个人私信页面能力写成商家客服后台能力。

`accessibility_browser_adapter` 现在不是自动化实现，而是工程边界声明。真实页面仍必须由操作者可见、可撤销地进行 draft-only 测试。

## 4. 验证结果

已通过：

```bash
node --check scripts/lib/rpa_browser_adapters.mjs
node --check scripts/run_p3_06u_12e_rpa_browser_reply_feasibility.mjs
```

已通过：

```bash
P3_06U_12E_OUTPUT=output/p3_06u_12g_rpa_adapter_abstraction/capabilities \
RPA_PRINT_ADAPTER_CAPABILITIES=1 \
node scripts/run_p3_06u_12e_rpa_browser_reply_feasibility.mjs
```

已通过本地 mock draft-only 回归：

```bash
P3_06U_12E_OUTPUT=output/p3_06u_12g_rpa_adapter_abstraction/draft_only \
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 \
STANDARD_OPS_BACKEND_URL=http://127.0.0.1:8081 \
RPA_BROWSER_ADAPTER=cdp_browser_adapter \
node scripts/run_p3_06u_12e_rpa_browser_reply_feasibility.mjs
```

输出目录：

```text
output/p3_06u_12g_rpa_adapter_abstraction/
```

## 5. 当前结论

P3-06U-12G 完成后，RPA 研究线的口径更清楚：

| Adapter | 当前状态 | 用途 | 是否默认发送 |
|---|---|---|---|
| `cdp_browser_adapter` | 已实现 | mock 页面、localhost、专门调试 Profile | 否 |
| `accessibility_browser_adapter` | contract-only / fail-closed | 已登录真实页面的受控研究边界 | 否 |

这一步仍不能证明任何电商平台自动回复可商用，只能证明我们已经把 RPA 页面执行层从“临时脚本”推进到“可治理的 adapter 边界”。

## 6. 下一步

建议下一步做 `P3-06U-12H`：

```text
单平台真实页面 selector/locator profile 草稿
```

但仍只做：

1. 人工选择一个测试页面。
2. 记录脱敏 locator。
3. 不保存页面原文。
4. 只填草稿。
5. 默认清空草稿。
6. 不点击发送。

