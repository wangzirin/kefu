# P3-06U-12K AIJiaKeFu EXE 静态代码线索分析

日期：2026-07-02

## 1. 结论

AIJiaKeFu release 包里的 `爱嘉客服.exe` 能看到比较清楚的平台模块结构，但不能把它当成可直接复刻的开源源码。

本轮没有运行 exe，没有接入真实平台，没有读取 Cookie、Token 或浏览器登录态，也没有反编译还原源码。分析只限于：

- PE 文件类型识别。
- PyInstaller 包目录表读取。
- PYZ 模块目录读取。
- 平台模块字符串常量和函数名/类名只读抽取。
- 配置文件静态读取。

## 2. 可确认事实

### 2.1 文件形态

| 文件 | 结论 |
| --- | --- |
| `爱嘉客服.exe` | Windows x64 GUI 程序，PyInstaller 打包，Python 3.12。 |
| `WebDriver.exe` | Windows x64 GUI 程序，疑似独立浏览器控制服务。 |
| `WindowsDriver.exe` | Windows x64 GUI 程序，疑似窗口/UI 自动化服务。 |
| `CopyImage.exe` | PyInstaller 打包，包含 PIL、win32clipboard 等图像/剪贴板能力。 |

### 2.2 主程序内可见业务模块

`爱嘉客服.exe` 的 PYZ 包内能看到这些业务模块：

| 模块 | 可能作用 |
| --- | --- |
| `Tool.DriverStartJD` | 启动京东相关 WebDriver/Chrome 远程调试端口。 |
| `Tool.DriverStartdoudian` | 启动抖店相关 WebDriver/Chrome 远程调试端口。 |
| `Tool.DriverStartdouyin` | 启动抖音相关 WebDriver/Chrome 远程调试端口。 |
| `Tool.JDmultidialog` | 京东多开控制面板。 |
| `Tool.JDmultiwebdriver` | 京东多开 WebDriver 线程/启动器。 |
| `Tool.PDDmultidialog` | 拼多多多开控制面板。 |
| `Tool.doudianmultidialog` | 抖店多开控制面板。 |
| `Tool.doudianmultiwebdriver` | 抖店多开 WebDriver 线程/启动器。 |
| `Tool.douyinmultidialog` | 抖音多开控制面板。 |
| `Tool.browser_utils` | Chrome 安装检测、远程调试端口检测。 |
| `Tool.config_manager` | 配置读写。 |
| `Tool.wechat_api` | 微信公众号 token、二维码接口。 |

### 2.3 配置口径

`Tool/config.json` 暴露的是平台多开配置框架：

- 抖店多开 1-8。
- 京东 / 京东多开 1-8。
- 拼多多 / 拼多多多开 1-8。
- 千牛 / 千牛 1-4。
- 每组包含 `shop_name`、`api_base`、`key`、`customer_service_name`。

`Tool/config.yaml` 暴露的是全局和单平台模型/接口配置：

- `global.api_base`
- `global.key`
- `individual.企业微信`
- `individual.抖音`
- `individual.抖店`

`Tool/serverConfiguration.yaml` 暴露的是远程服务配置：

- OCR 服务地址。
- WindowsDriver 服务地址和端口。
- WebDriver 服务地址和端口。

## 3. 关于“发送信息逻辑”的判断

从当前只读抽取结果看，能确认它有以下工程思路：

1. 每个平台先启动独立浏览器窗口或独立 WebDriver 实例。
2. 通过 `--remote-debugging-port=` 暴露 Chrome 调试端口。
3. 使用独立 `WebDriver.exe` 与主程序通信。
4. 对京东、抖店、抖音、拼多多使用多开控制面板。
5. 对部分桌面/图像场景可能通过 `WindowsDriver.exe`、OCR、剪贴板和图像识别辅助。
6. 通过 `api_base`、`key`、`customer_service_name` 接入大模型或客服身份配置。

但当前没有在不反编译源码的前提下看到：

- 抖音、京东、拼多多、淘宝/千牛的稳定 DOM selector。
- 明确的“发送按钮”定位代码。
- 平台消息读取、去重、回执、失败重试的完整业务实现。
- 官方平台授权验证逻辑。
- 高并发队列或生产级监控逻辑。

因此，这个 exe 对我们的价值是“产品形态和模块拆分参考”，不是“直接拿成熟代码复刻”。

## 4. 对我们工程的可借鉴点

### 4.1 可以借鉴

- 按平台拆 adapter，不把所有平台写成一个大脚本。
- 每个平台独立维护启动参数、调试端口、窗口/浏览器控制方式。
- 多开账号以实例为单位管理。
- API Base、Key、客服名等配置不写死在平台逻辑里。
- WebDriver、WindowsDriver、OCR、剪贴板能力分成不同执行服务。

### 4.2 不应照搬

- 不运行未知闭源 exe 作为我们的商业底座。
- 不复制或反编译代码放入我们的商业系统。
- 不用私有协议、Cookie 复用、风控规避或自动点击真实发送作为正式交付能力。
- 不把 RPA 多开能力写成官方平台接入能力。

## 5. 下一步建议

我们的实现路线保持：

1. 官方 API / 服务商授权：正式商用主线。
2. RPA draft-only：内部研究和坐席副驾驶线。
3. 单平台真实测试账号校准：先做可见页面读消息、填草稿、清空草稿。
4. 每个平台独立建立 locator profile、失败状态、发送禁点和操作证据。

如果继续研究 AIJiaKeFu，只建议继续做模块名、配置结构和产品流程参考，不建议进入源码还原或二进制运行。
