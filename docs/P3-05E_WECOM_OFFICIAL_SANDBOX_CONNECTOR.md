# P3-05E 企业微信官方 Sandbox Connector

## Engineering Control Card

- Stage: P3-05E
- 当前主线阶段: Lite 试点版单平台官方 sandbox
- 上一阶段真正完成: P3-05D 渠道测试账号准备指南，P3-05C 官方渠道自动回复 readiness
- 上一阶段明确没有完成: 企业微信真实 URL 验证、AES 解密、XML 消息解析、真实外发、可信 IP、access token 获取
- 本轮要交付的客户可见价值: 企业微信后台可以验证我们的 HTTPS 回调 URL；个人微信打开客服链接发测试消息后，消息可以进入系统，生成后续 AI 草稿与人工审核链路
- 本轮是否只是评测: 否，是真实官方回调入站 sandbox 能力
- 本轮不做什么: 不调用企微发送消息 API，不打开外部写入，不使用个人微信外挂、Hook、群控或模拟点击
- 外部风险: 需要公网 HTTPS 回调 URL；真实发送 API 后续需要可信 IP、access token、发送窗口和白名单
- 需要用户授权的动作: 在企业微信后台填写 URL / Token / EncodingAESKey；后续真实发送前还要再次授权
- 验证方式: 单测覆盖 URL 验证、坏签名拒绝、XML AES 解密入站；回归测试覆盖原有 webhook/worker/官网 sandbox
- 写回文件: Project_012 执行记录、关键决策、文件索引、复盘与采坑
- 下一阶段: 公网 HTTPS 回调 smoke，随后用个人微信客服链接发测试消息并运行可信入站 worker

## 这个 Connector 到底是什么

企业微信官方 sandbox connector 不是把我们的系统安装成企微原生机器人，也不是绕过微信规则的外挂。

它是一个官方回调入口：

1. 企业微信向我们的公网 HTTPS URL 发起 URL 验证。
2. 我们用后台填写的 Token 校验 `msg_signature`。
3. 我们用 `EncodingAESKey` 解密 `echostr`，把明文返回给企业微信。
4. 验证通过后，用户通过微信客服链接发送消息。
5. 企业微信把加密 XML 消息 POST 到同一个 URL。
6. 我们验签、AES 解密、解析 XML。
7. 解析后的文本消息进入系统内部 `messages`。
8. 后续由可信入站 worker 生成 AI 草稿，先进人工审核。
9. 本阶段不自动发回微信。

当前已实现的是 1 到 7。第 8 步用既有 worker 能力完成。第 9 步仍保持关闭。

## 当前后端能力

新增后端能力：

- `GET /api/webhooks/wecom/channels/{channel_id}`
  - 用于企业微信后台 URL 验证。
  - 查询参数：`msg_signature`、`timestamp`、`nonce`、`echostr`。
  - 成功返回解密后的纯文本 `echostr`。

- `POST /api/webhooks/wecom/channels/{channel_id}`
  - 支持企业微信官方 XML 安全模式消息。
  - 读取外层 XML 的 `Encrypt`。
  - 验证 `msg_signature`。
  - 使用 `EncodingAESKey` 做 AES-CBC 解密。
  - 解析内层 XML 的 `FromUserName`、`Content`、`MsgId` 等字段。
  - 创建可信入站消息。

- `credential_ref=env:WECOM_KF`
  - 数据库只保存这个引用。
  - 真实 Token 和 AESKey 只从环境变量读取。

## 环境变量

在服务端 `.env` 或部署环境中配置：

```bash
WECOM_CORP_ID=
WECOM_KF_CALLBACK_TOKEN=
WECOM_KF_ENCODING_AES_KEY=
WECOM_KF_RECEIVER_ID=
OUTBOX_EXTERNAL_WRITE_ENABLED=false
```

说明：

- `WECOM_KF_CALLBACK_TOKEN`: 你准备填到企微后台的 Token。
- `WECOM_KF_ENCODING_AES_KEY`: 你准备填到企微后台的 EncodingAESKey。
- `WECOM_KF_RECEIVER_ID`: 可选；如果明确知道接收方 ID，填这里；不确定时 sandbox 可先留空，避免 receiver id 不一致导致 URL 验证失败。
- `WECOM_CORP_ID`: 企业 ID；也可作为 WeCom receiver id 的兜底来源。
- `OUTBOX_EXTERNAL_WRITE_ENABLED=false`: 必须保持关闭，本阶段不真实外发。

不要把 Token、EncodingAESKey、Secret 写进客户文档、截图或聊天记录。

## 我们系统内如何配置 Channel Connector

后端已有连接器配置 API。对某个企业微信客服 channel 配置：

```json
{
  "provider": "wecom",
  "mode": "noop",
  "status": "ready",
  "display_name": "企业微信客服官方接口",
  "capabilities": ["receive_message", "delivery_receipt"],
  "public_config": {
    "credential_ref": "env:WECOM_KF",
    "corp_id_placeholder": "stored_in_env_only"
  },
  "webhook_path": "/api/webhooks/wecom/channels/{channel_id}",
  "signature_mode": "wecom_token_aeskey"
}
```

注意：

- `mode` 仍为 `noop`，因为不真实发送。
- `external_write_enabled` 会被后端强制保持 `false`。
- `credential_ref` 只指向环境变量前缀，不保存真实密钥。

## 企业微信后台怎么填

你现在在“应用管理 -> 微信客服”的页面，这是微信客服应用详情页。

下一步按这个顺序走：

1. 先保存客服账号。
2. 绑定接待人员。
3. 复制客服链接或二维码，先留着。
4. 回到“微信客服”应用详情页。
5. 找到“可调用接口的应用”。
6. 点“设置”。
7. 选择一个自建应用，或创建一个只用于测试的自建应用。
8. 到这个自建应用的详情页，找“接收消息 / API 接收 / 设置接收消息”。
9. 填入：
   - URL: `https://你的公网域名/api/webhooks/wecom/channels/<channel_id>`
   - Token: 与 `WECOM_KF_CALLBACK_TOKEN` 一致
   - EncodingAESKey: 与 `WECOM_KF_ENCODING_AES_KEY` 一致
10. 先提交 URL 验证。
11. URL 验证通过后，用个人微信打开客服链接，发一条白名单测试消息。
12. 系统收到消息后，先看内部会话和人工审核，不做自动外发。

如果后台页面没有直接显示 URL / Token / EncodingAESKey，通常说明你还停留在“微信客服应用详情页”，需要进入“可调用接口的应用”绑定的自建应用里配置“接收消息”。

## 没有固定公网 IP 时怎么办

分两种情况：

### 只做入站 sandbox

可以用公网 HTTPS 隧道或临时云服务：

- Cloudflare Tunnel
- ngrok
- frp
- 一台临时云服务器反代到本地

这可以完成：

- URL 验证
- 接收消息
- 解密解析
- 入库
- AI 草稿和人工审核

### 要真实发回微信

需要更严格：

- 自建应用需要可信 IP。
- 获取 access_token 和调用发送 API 时，出站 IP 要稳定。
- 建议使用云服务器固定公网 IP，或用固定 IP 出口代理。
- 不建议用家庭宽带临时公网 IP 做正式外发测试。

本阶段先不做真实发送，所以可信 IP 可以先作为后续事项处理；如果企业微信后台创建应用时强制要求可信 IP，临时方案是用云服务器固定 IP。

## 为什么先不真实发送

原因很现实：

- 企业微信客服发送消息有窗口和会话状态限制，不能无限主动营销。
- 自动发送如果出现错答、过度承诺、退款赔付、合同条款错误，商业风险很高。
- 真实发送需要 access token、可信 IP、限流、失败回执、重试、白名单和人工确认。
- 当前 Lite 试点版目标是先证明官方入站链路和 AI 草稿审核链路，而不是直接全自动回复。

## 当前完成边界

已经完成：

- URL 验证接口。
- Token + `msg_signature` 校验。
- `EncodingAESKey` AES-CBC 解密。
- XML 解析。
- 可信入站消息创建。
- 敏感值不落库。
- 外部写入保持关闭。

没有完成：

- 真实企微 access token 获取。
- 真实发送消息 API。
- 可信 IP 出站链路。
- 平台错误码完整映射。
- 真实客服链接端到端公网 smoke。
- 自动回复白名单测试。

## 参考来源

- 企业微信开发者文档：`https://developer.work.weixin.qq.com/document/path/94677`
- 企业微信 API 调试/镜像文档：`https://qiyeweixin.apifox.cn/api-10061328`
- 企业微信开发者文档入口：`https://developer.work.weixin.qq.com/`
