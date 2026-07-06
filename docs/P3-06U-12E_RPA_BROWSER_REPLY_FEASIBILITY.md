# P3-06U-12E RPA 浏览器回复可行性实验

日期：2026-07-02

## 1. 本片目标

本片只研究 RPA 技术可行性，不研究官方 API 接入。

目标是验证：

```text
浏览器页面 -> 识别会话 -> 读取客户消息 -> 调用客服策略 -> 填入回复框 -> 可控发送
```

这条链路是否能跑通。

## 2. 当前结论

结论：在可控的类平台客服工作台页面里，RPA 技术链路已经跑通。

已证明：

- RPA 可以通过浏览器远程调试端口打开客服工作台页面。
- RPA 可以定位未读会话。
- RPA 可以读取当前客户、渠道和最新客户消息。
- RPA 可以调用现有后端 `POST /api/rpa-copilot/strategy-dry-run`。
- RPA 可以把策略草稿填入页面回复框。
- 在本地 mock 页面显式打开 `RPA_ALLOW_SEND=1` 时，RPA 可以点击发送按钮。
- 后端策略仍保持 `research_dry_run`，审计里 `external_write_performed=false`。

尚未证明：

- 真实拼多多、抖店、淘宝、京东、小红书、企业微信后台页面的选择器稳定性。
- 真实平台是否检测或限制浏览器自动化。
- 真实平台登录态、验证码、二次验证、风控弹窗对 RPA 的影响。
- iframe、虚拟列表、Shadow DOM、Canvas 消息区等复杂页面结构下的稳定性。
- 长时间运行、多会话排队、异常恢复、误发防护。
- 真实平台发送动作是否安全可接受。

因此当前只能说：

```text
RPA 动作链条在可控页面可行；真实平台仍需要逐个平台做人工登录、测试账号、测试会话的受控验证。
```

## 3. 新增文件

### 3.1 Mock 客服工作台

```text
research/rpa_browser_reply_feasibility/mock_platform_workbench.html
```

用途：

- 模拟电商客服后台常见结构。
- 左侧会话列表。
- 右侧当前对话。
- 回复框。
- 发送按钮。
- 本地发送后追加一条已发送消息。

该页面不连接任何真实平台。

### 3.2 RPA Driver

```text
scripts/run_p3_06u_12e_rpa_browser_reply_feasibility.mjs
```

能力：

- 默认打开本地 mock 页面。
- 支持读取 selector profile。
- 支持附着到已打开的 Chrome 标签页。
- 支持调用本地后端策略服务。
- 默认只填草稿，不点击发送。
- 只有本地页面或显式安全确认时才允许点击发送。

### 3.3 Selector 模板

```text
research/rpa_browser_reply_feasibility/selector_profile.example.json
```

后续真实平台实验时复制一份，再根据平台页面调整：

- 会话列表选择器。
- 当前客户选择器。
- 最新消息选择器。
- 回复框选择器。
- 发送按钮选择器。
- 发送状态选择器。

## 4. 验证命令

### 4.1 只填草稿，不发送

```bash
P3_06U_12E_OUTPUT=output/p3_06u_12e_rpa_browser_reply_feasibility/draft_only \
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 \
STANDARD_OPS_BACKEND_URL=http://127.0.0.1:8081 \
node scripts/run_p3_06u_12e_rpa_browser_reply_feasibility.mjs
```

结果：

- 通过。
- 输出目录：

```text
output/p3_06u_12e_rpa_browser_reply_feasibility/draft_only/
```

### 4.2 本地 mock 显式点击发送

```bash
P3_06U_12E_OUTPUT=output/p3_06u_12e_rpa_browser_reply_feasibility/mock_send \
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 \
STANDARD_OPS_BACKEND_URL=http://127.0.0.1:8081 \
RPA_ALLOW_SEND=1 \
node scripts/run_p3_06u_12e_rpa_browser_reply_feasibility.mjs
```

结果：

- 通过。
- 本地 mock 页面出现 `RPA 实验发送` 消息。
- 输出目录：

```text
output/p3_06u_12e_rpa_browser_reply_feasibility/mock_send/
```

## 5. 当前样例结果

样例客户消息：

```text
我下单后多久发货？节假日会延迟吗？
```

策略结果：

| 字段 | 结果 |
|---|---|
| `mode` | `research_dry_run` |
| `delivery_mode` | `fill_draft_only` |
| `intent` | `shipping_status_or_policy` |
| `next_best_action` | `operator_review_and_send` |
| `confidence` | `0.87` |
| `citation_count` | `1` |
| `external_write_performed` | `false` |
| `action_external_write_count` | `0` |

页面最终状态：

- 回复框已填入草稿。
- 本地 mock 发送模式下，已追加 1 条发送消息。
- 无横向溢出。
- 无失败项。

## 6. 真实平台实验方法

真实平台实验不能一上来点发送，建议分三步：

### 6.1 观察模式

用户手动登录平台测试账号，打开客服后台测试会话。

运行时使用：

```bash
RPA_ATTACH_URL_CONTAINS="平台页面 URL 里的稳定片段" \
RPA_SELECTOR_PROFILE=research/rpa_browser_reply_feasibility/selector_profile.平台名.json \
node scripts/run_p3_06u_12e_rpa_browser_reply_feasibility.mjs
```

目标：

- 能附着到已登录页面。
- 能识别会话。
- 能读取客户消息。
- 不填框或只填测试草稿。
- 不发送。

### 6.2 填框模式

在测试会话里验证：

- RPA 能把草稿填入真实平台回复框。
- 平台没有阻断普通输入。
- 页面没有自动提交。
- 坐席能看到草稿并人工编辑。

仍不点击发送。

### 6.3 人工确认发送模式

仅限：

- 用户明确说这是测试账号。
- 测试客户也是自己控制的账号。
- 允许发出测试消息。
- 已确认不会影响真实客户。

真实外部页面如果要让脚本点击发送，必须同时设置：

```bash
RPA_ALLOW_SEND=1
RPA_REAL_PLATFORM_SEND_ACK=I_UNDERSTAND_THIS_CAN_SEND
```

没有这个确认，脚本会拒绝非本地页面发送。

## 7. 下一步建议

下一步不做质量复盘，也不扩官方 API。

建议进入：

```text
P3-06U-12F 单平台真实页面 RPA Draft-Only 试验
```

优先选择一个平台：

- 拼多多客服后台。
- 抖店/飞鸽客服后台。
- 淘宝/千牛客服后台。
- 小红书企业号私信后台。
- 企业微信/微信客服后台。

第一轮只做：

1. 人工登录。
2. 打开测试会话。
3. 读取消息。
4. 填入草稿。
5. 截图和摘要。
6. 不点击发送。

如果第一轮稳定，再做人工确认发送。
