# H2W-10A 企业微信 / 微信客服官方沙箱闭环 readiness

## 结论

- 阶段状态：`waiting_for_official_sandbox_conditions`
- 官方 provider contract：`true`
- 验签测试：`true`
- 幂等入站测试：`true`
- 回执记录：`true`
- AI 草稿链路：`true`
- 外发默认关闭：`true`
- 真实官方沙箱可运行：`false`

## 还缺什么

- 尚未提供真实企业微信沙箱 CorpID/Token/EncodingAESKey 环境配置
- 尚未提供公网 HTTPS 回调 URL
- 尚未确认企业微信后台可信 IP 配置

## 企业微信后台需要准备

1. 已保存微信客服账号，并绑定接待人员。
2. 已有可访问公网 HTTPS 回调地址。
3. 在企业微信后台准备 URL、Token、EncodingAESKey。
4. 自建应用或客服 API 已配置可信 IP。
5. 只做白名单沙箱消息，不面向真实客户开放。

## 控制台配置手册

- 企业微信后台选择“微信客服”。
- 进入可调用接口的应用，选择企业内部开发或授权应用。
- 填入后端给出的 HTTPS 回调 URL。
- Token 与 EncodingAESKey 存入客户环境变量或密钥管理，不写入仓库。
- 平台 URL 验证通过后，用个人微信打开客服链接发送测试消息。
- 系统只生成 AI 草稿和回执记录；真实外发仍关闭。

## 输出

- `C:\Users\123\AppData\Local\Temp\pytest-of-123\pytest-3\test_h2w10a_waits_for_real_wec0\summary.json`

## 边界

- 本阶段不启用真实外发。
- 本阶段不保存 Token、EncodingAESKey 或客户 secret。
- 本阶段不把“配置模板准备好”写成“已接通”。
- RPA 不进入正式默认交付链。
