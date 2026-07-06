# P3-06U-12J AIJiaKeFu 参考仓库与四平台 RPA 实验包

日期：2026-07-02

## Engineering Control Card

- Stage：P3-06U-12J
- 本片目标：拉取 AIJiaKeFu / AI-Customer-Service，确认它是否有可复用源码，并把抖音、淘宝千牛、京东京麦、拼多多四个平台先纳入我们自己的 RPA draft-only 实验矩阵。
- 本片不是：真实接通抖音、淘宝、京东、拼多多；运行第三方闭源程序；绕过平台风控；自动发送真实消息。
- 本片客户可见价值：内部团队可以清楚知道 AIJiaKeFu 能参考什么、不能参考什么，并拥有下一步逐平台真实页面 draft-only 的工程入口。
- 真实外发：关闭。
- 真实平台账号：未使用。
- 真实客户消息：未读取、未保存。

## 1. 对 AIJiaKeFu 仓库的真实结论

已经拉取：

```text
/Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/assets/open_source_references/AI-Customer-Service
```

源码层结论：

- 主分支只有 `README.md`。
- 没有 Python、JavaScript、Java、Go 或其他可读源码。
- 没有可以直接复刻的抖音、千牛、京麦、拼多多 adapter 源码。

Release 静态检查：

```text
/Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究/assets/open_source_references/AI-Customer-Service-release/default.rar
```

- 文件类型：RAR v5。
- SHA256：`785d2a2cefc914a9362b89a632a02db95eed5646a4590a1045329acd01395896`。
- 包内有 Windows GUI 程序、`WebDriver.exe`、`WindowsDriver.exe`、`CopyImage.exe`、平台图标、千牛图像素材和配置文件。
- 未运行任何闭源二进制。

## 2. 它能证明什么

AIJiaKeFu 可以证明：

- 市面上确实存在把 AI 客服做成多平台 RPA 产品的实践。
- 它的产品口径明确覆盖企业微信、微信、抖店、千牛、拼多多、京麦、抖音私信、小红书私信等。
- Release 包形态支持“Windows 客户端 + WebDriver / WindowsDriver + 图像/控件识别 + 多平台配置”这个判断。

AIJiaKeFu 不能证明：

- 这些平台都有官方通用客服发送 API。
- 它的实现方式被抖音、淘宝、京东、拼多多官方认可。
- 它能支撑高并发、长期无人值守、低封控风险。
- 我们可以把它的闭源二进制或 AGPL 项目直接放进商用系统。

## 3. 四个平台怎么进入我们自己的实验

新增机器可读矩阵：

```text
research/rpa_browser_reply_feasibility/aijiakefu_platform_research_matrix.json
```

覆盖：

| 平台 | 上游声明 | 我们的实验路线 | 正式路线 |
|---|---|---|---|
| 抖音 / 抖店 | README 写抖音私信、抖店；包内有 `douyin.png`、`doudian.png` 和抖店多开配置 | 已登录测试页面 draft-only 填草稿 | 抖音开放平台私信、企业号 IM、抖店/飞鸽服务商权限 |
| 淘宝 / 千牛 | README 写千牛；包内有 `qianniu.png`、千牛图像素材和千牛客服名称配置 | 千牛可见工作台 draft-only 填草稿 | 淘宝客服面板插件、服务市场或店小蜜/官方能力 |
| 京东 / 京麦 | README 写京麦；包内有 `jingmai.png` 和京东多开配置 | 京麦/咚咚可见工作台 draft-only 填草稿 | JOS 客服机器人/客服插件接口包 |
| 拼多多 | README 写拼多多；包内有 `pdd.png` 和拼多多多开配置 | 多多客服可见工作台 draft-only 填草稿 | 拼多多开放平台或服务商权限专项确认 |

## 4. 本地四平台 mock 矩阵

已增强：

```text
research/rpa_browser_reply_feasibility/mock_platform_workbench.html
```

现在支持：

```text
?platform=douyin
?platform=qianniu
?platform=jingmai
?platform=pdd
```

新增矩阵 runner：

```text
scripts/run_p3_06u_12j_aijiakefu_platform_mock_matrix.mjs
```

它会逐个平台打开本地 mock 工作台，复用 P3-06U-12E 的 RPA 流程：

```text
打开平台样式页面 -> 读取消息 -> 调用策略服务 -> 填入草稿 -> 不发送 -> 输出证据
```

本片矩阵仍然是本地实验，不是真实平台接入。

## 5. 下一步真实页面实验顺序

建议顺序：

1. 拼多多或抖店：优先选一个有明确测试店铺和低风险测试会话的平台。
2. 用户人工登录测试账号。
3. 打开真实客服后台的一个测试会话。
4. 只运行 draft-only。
5. RPA 填入测试草稿。
6. 人工目视确认草稿出现。
7. 立即清空草稿。
8. 记录 `send_attempted=false`。

通过标准：

- 能定位输入框。
- 能写入草稿。
- 能清空草稿。
- 不点击发送。
- 不保存客户原文。
- 不读取 Cookie、Token、LocalStorage。

不通过也有价值：

- 如果页面是 iframe、虚拟列表、Canvas 或强风控，就记录失败原因。
- 失败不代表 RPA 总路线失败，只说明该平台需要专门 adapter 或转回官方 API/插件路线。

## 6. 当前边界

- 当前没有真实接通抖音、淘宝、京东、拼多多。
- 当前没有运行 AIJiaKeFu 的闭源 Windows 程序。
- 当前没有复制 AIJiaKeFu 代码，因为仓库没有源码可读。
- 当前只是把它作为市场和产品形态证据，并把我们自己的 RPA draft-only 实验链路扩展到四个平台。
