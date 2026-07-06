# P3-05D 渠道测试账号准备与操作指南

日期：2026-06-29

用途：把“到底去哪里操作、拿什么给工程侧、怎么验证某个渠道能不能自动回复”拆成可执行清单。

## 0. 先说结论

现阶段不要同时开微信、企业微信、公众号、抖音、小红书、淘宝、京东、拼多多。最稳的真实测试顺序是：

1. 企业微信/微信客服：第一优先级，官方路径清楚，适合 B2B 私域试点。
2. 微信公众号测试号或服务号：第二优先级，适合微信生态入口验证。
3. 抖音开放平台私信：第三优先级，取决于应用权限和 scope 审批。
4. 抖店/飞鸽、小红书、淘宝/天猫、京东、拼多多：先做权限确认，不要先写代码承诺自动回复。

你需要做的是：在对应平台后台创建测试应用、开通消息/客服能力、把我们给你的公网 HTTPS 回调 URL 填进去，然后把非敏感配置和权限截图给我；敏感密钥不要发聊天，后续填到 `.env` 或临时安全配置文件。

## 1. 所有渠道共用的准备

### 1.1 必须先有一个公网 HTTPS 回调地址

第三方平台不能回调你的本机 `127.0.0.1`。我们需要二选一：

| 方式 | 适合阶段 | 说明 |
| --- | --- | --- |
| 临时隧道 | 第一次 sandbox | 用 Cloudflare Tunnel、ngrok 等把本机后端临时暴露成 HTTPS URL。优点是快，缺点是 URL 会变。 |
| 试点云域名 | 稳定试点 | 用云服务器 + 域名 + HTTPS，形如 `https://cs-test.example.com`。优点是稳定，适合给平台长期配置。 |

当前后端已有统一 webhook 入口：

```text
https://<你的测试域名>/api/webhooks/{provider}/channels/{channel_id}
```

当前已存在 provider 合同：

```text
企业微信/微信客服: /api/webhooks/wecom/channels/{channel_id}
微信公众号: /api/webhooks/wechat-official-account/channels/{channel_id}
官网自有入口: /api/webhooks/website/channels/{channel_id}
```

抖音、小红书、淘宝、京东、拼多多现在还没有 provider 实现，所以即使你先准备好后台权限，我们也要先补 provider，再给你正式回调 URL。

### 1.2 你给我的材料分三类

可以直接发给我：

- 平台名称。
- 账号类型：测试号、企业号、服务号、商家店铺、服务商应用等。
- AppID、Client Key、CorpID、店铺 ID、客服账号 ID 这类非密钥标识。
- 已开通权限的截图。
- 回调配置页面截图，截图前遮住 Secret、Token、EncodingAESKey。
- 测试账号说明：哪个微信号/抖音号/店铺测试号会发消息。

不要直接发聊天，后续填 `.env`：

- AppSecret、Client Secret、CorpSecret。
- Token。
- EncodingAESKey。
- access token、refresh token、session key。
- 店铺授权 token。
- webhook secret、signing secret。

我这边需要验证的不是你的账号密码，而是这些能力是否存在：

- 平台能不能把用户消息推到我们的回调 URL。
- 我们能不能验签/解密/去重。
- 我们能不能把消息变成内部会话。
- AI 能不能生成草稿。
- 坐席能不能审核。
- outbox 能不能生成待发送任务。
- 最后一步真实发送必须单独授权，默认不打开。

## 2. 企业微信 / 微信客服

推荐优先级：最高。

如果当前页面 URL 类似：

```text
https://work.weixin.qq.com/wework_admin/frame#/app/servicer/account_mod/<一串数字>
```

这说明你在“微信客服账号编辑/客服账号配置”页。这个页面是对的，但它只负责客服账号本身，例如客服名称、头像、接待人员、接待设置和客服链接。它不是 API 回调配置页。完成本页以后，还需要回到微信客服的“开发配置”或“API 接收消息”页面配置 URL、Token、EncodingAESKey。

你去哪里操作：

1. 打开企业微信管理后台：https://work.weixin.qq.com/
2. 进入“应用管理”或“客户联系/微信客服”相关入口。
3. 开通“微信客服”能力。
4. 新建一个客服账号，例如“测试客服”。
5. 绑定接待人员，建议先绑定你自己的企业微信账号。
6. 找到“开发配置”“API”“接收消息”或“回调配置”页面。
7. 填写我们提供的回调 URL：

```text
https://<测试域名>/api/webhooks/wecom/channels/{channel_id}
```

8. 在该页面生成或填写 `Token` 和 `EncodingAESKey`。
9. 获取客服账号链接，用个人微信打开这个链接并发送测试消息。

你要准备给我的信息：

| 信息 | 是否敏感 | 给法 |
| --- | --- | --- |
| 企业 ID / CorpID | 低敏 | 可以发 |
| 微信客服账号 ID / open_kfid | 低敏 | 可以发 |
| 接待人员 user id | 低敏 | 可以发 |
| 回调 URL 页面截图 | 中敏 | 遮住密钥后发 |
| Token | 敏感 | 不发聊天，填 `.env` |
| EncodingAESKey | 敏感 | 不发聊天，填 `.env` |
| Secret / CorpSecret | 敏感 | 不发聊天，填 `.env` |
| 客服账号测试链接 | 中敏 | 可以临时发，测试后可失效或重建 |

我们验收什么：

- 平台校验回调 URL 能通过。
- 你用个人微信给客服链接发消息后，我们后端收到回调。
- 我们验签和解密成功。
- 系统生成内部会话和 AI 草稿。
- 草稿进入人工审核。
- 审核通过后生成 outbox。
- 默认仍不真实外发；真实 send adapter 要单独开关。

官方参考：

- 企业微信微信客服发送消息：https://developer.work.weixin.qq.com/document/path/94677
- 企业微信微信客服接待人员管理：https://developer.work.weixin.qq.com/document/path/94693
- 企业微信获取客服账号链接：https://developer.work.weixin.qq.com/document/path/94692

## 3. 微信公众号 / 服务号 / 测试号

推荐优先级：高。

第一次建议用公众号测试号，不要直接动正式服务号。

你去哪里操作：

1. 公众号正式账号：打开微信公众平台：https://mp.weixin.qq.com/
2. 测试号：打开公众平台测试号入口：https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login
3. 进入“设置与开发”。
4. 进入“基本配置”或测试号配置页。
5. 找到服务器配置。
6. 填写 URL：

```text
https://<测试域名>/api/webhooks/wechat-official-account/channels/{channel_id}
```

7. 填写 Token。
8. 如启用安全模式，填写 EncodingAESKey。
9. 保存并启用服务器配置。
10. 用个人微信关注测试号或服务号，发送测试消息。

你要准备给我的信息：

| 信息 | 是否敏感 | 给法 |
| --- | --- | --- |
| AppID | 低敏 | 可以发 |
| 原始 ID，形如 `gh_xxx` | 低敏 | 可以发 |
| 测试号二维码或关注方式 | 低敏 | 可以发 |
| 已启用服务器配置截图 | 中敏 | 遮住密钥后发 |
| AppSecret | 敏感 | 不发聊天，填 `.env` |
| Token | 敏感 | 不发聊天，填 `.env` |
| EncodingAESKey | 敏感 | 不发聊天，填 `.env` |

我们验收什么：

- 微信服务器校验 URL 成功。
- 用户发消息后，系统收到公众号消息回调。
- 明文模式先跑通；安全模式再补解密。
- 系统生成内部会话和 AI 草稿。
- 被动回复和客服消息窗口策略后续单独处理。

注意：

- 公众号不是个人微信自动回复。
- 客服消息受用户互动窗口、账号类型和平台规则约束。
- 不承诺无限主动私聊。

官方参考：

- 公众号接入概述：https://developers.weixin.qq.com/doc/offiaccount/Basic_Information/Access_Overview.html
- 公众号客服消息：https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Service_Center_messages.html
- 微信服务号发送文本客服消息：https://developers.weixin.qq.com/doc/service/api/message/message/api_send_text_msg.html

## 4. 抖音开放平台私信

推荐优先级：中。先准备权限，不要先承诺上线。

你去哪里操作：

1. 打开抖音开放平台：https://developer.open-douyin.com/
2. 进入控制台。
3. 创建应用，按你的业务选择网站应用、小程序、企业号相关应用或其他合适类型。
4. 在能力或权限里查找“私信”“互动管理”“消息管理”“Webhook 事件”等能力。
5. 申请私信发送、私信接收或相关 webhook 事件权限。
6. 配置回调域名和事件订阅。
7. 配置授权回调地址。
8. 绑定或授权一个测试抖音账号。

当前我们系统还没有 `douyin_open` provider，所以回调 URL 要等我们实现后给你，预期类似：

```text
https://<测试域名>/api/webhooks/douyin-open/channels/{channel_id}
```

你要准备给我的信息：

| 信息 | 是否敏感 | 给法 |
| --- | --- | --- |
| 应用类型 | 低敏 | 可以发 |
| Client Key / App ID | 低敏 | 可以发 |
| 已申请 scope 列表 | 低敏 | 可以发 |
| Webhook 事件订阅截图 | 中敏 | 遮住密钥后发 |
| 授权测试账号说明 | 低敏 | 可以发 |
| Client Secret | 敏感 | 不发聊天，填 `.env` |
| access token / refresh token | 敏感 | 不发聊天，填 `.env` |

我们验收什么：

- 官方应用已获得私信/消息相关权限。
- 平台 webhook 能打到我们的回调。
- 私信事件能被解析成统一消息。
- 人审后再尝试官方 send API。

官方参考：

- 抖音开放平台发送私信消息：https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/interaction-management/private-message/send-msg
- 抖音开放平台 Webhook 事件列表：https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/webhooks/event-list
- 抖音小程序客服消息推送：https://developer.open-douyin.com/docs/resource/zh-CN/mini-app/develop/server/customer-service/receive-msg/push-msg

## 5. 抖店 / 飞鸽客服

推荐优先级：中低。先做权限确认。

你去哪里操作：

1. 打开抖店开放平台：https://op.jinritemai.com/
2. 登录商家或服务商账号。
3. 进入开发者控制台。
4. 创建应用，优先选择服务商应用或商家自研应用，具体取决于你是否是店铺主体。
5. 查找“飞鸽”“客服”“会话”“IM”“机器人”相关 API 权限。
6. 如果后台没有对应权限，截图给我；这说明当前账号不能直接做自动客服发送。
7. 如有权限，配置回调、授权店铺，并记录店铺 ID。

当前我们没有抖店 provider。预期后续 URL 类似：

```text
https://<测试域名>/api/webhooks/doudian-feige/channels/{channel_id}
```

你要准备给我的信息：

| 信息 | 是否敏感 | 给法 |
| --- | --- | --- |
| 店铺主体和应用类型 | 低敏 | 可以发 |
| App Key | 低敏 | 可以发 |
| 店铺 ID | 低敏 | 可以发 |
| 已开通 API 权限截图 | 中敏 | 遮住密钥后发 |
| App Secret | 敏感 | 不发聊天，填 `.env` |
| 店铺 access token | 敏感 | 不发聊天，填 `.env` |

我们验收什么：

- 先确认平台是否真的给了客服会话消息权限。
- 如果只有订单/售后 API，没有会话发送 API，就只能做 Copilot 和人工建议，不做自动发送承诺。

官方参考：

- 抖店开放平台飞鸽 API：https://op.jinritemai.com/docs/api-docs/188
- 抖店飞鸽会话开放问答：https://op.jinritemai.com/docs/question-docs/96/6260
- 飞鸽 AI 服务说明：https://fxg.jinritemai.com/ffa/maomao/agreement/AiService

## 6. 小红书

推荐优先级：低。先做资质和权限确认。

你去哪里操作：

1. 打开小红书开放平台：https://open.xiaohongshu.com/
2. 如果是广告/商业私信工具，进入小红书商业平台或聚光相关后台。
3. 登录企业主体账号。
4. 查找“私信”“线索”“客服”“三方工具”“消息”相关能力。
5. 如果后台可以创建应用或工具授权，记录应用类型和权限范围。
6. 如果看不到私信相关接口，截图给我；这说明不能直接承诺自动回复。

当前我们没有小红书 provider。预期后续 URL 类似：

```text
https://<测试域名>/api/webhooks/xiaohongshu/channels/{channel_id}
```

你要准备给我的信息：

| 信息 | 是否敏感 | 给法 |
| --- | --- | --- |
| 账号类型：专业号、企业号、广告账号等 | 低敏 | 可以发 |
| 应用或工具名称 | 低敏 | 可以发 |
| 已开通能力截图 | 中敏 | 遮住密钥后发 |
| App ID / Client ID | 低敏 | 可以发 |
| App Secret / Token | 敏感 | 不发聊天，填 `.env` |

我们验收什么：

- 先确认是否有官方私信接收和发送能力。
- 没有明确私信 API 时，只做线索/评论/内容运营辅助，不做私信自动回复。

官方参考：

- 小红书开放平台开发者协议：https://open.xiaohongshu.com/document/developer/file/4
- 小红书商业文档中心私信三方工具资料：https://ad-market.xiaohongshu.com/docs-center?articleId=4437&bizType=943

## 7. 淘宝 / 天猫 / 千牛

推荐优先级：低。先确认是“客服辅助”还是“聊天自动发送”。

你去哪里操作：

1. 打开淘宝开放平台：https://open.taobao.com/
2. 登录商家主体或服务商主体。
3. 进入控制台创建应用。
4. 判断应用类型：商家自研、服务市场应用、千牛插件、客服面板插件。
5. 查找客服、千牛、店铺授权、消息服务、客服面板插件相关权限。
6. 如果目标是进入客服工作台，优先查“客户面板插件”路线。
7. 如果目标是自动回复旺旺/千牛聊天，必须找到明确官方发送 API 或服务市场能力；没有就不能承诺。

当前我们没有淘宝/天猫 provider。预期后续可能不是简单 webhook，而是千牛插件或服务市场应用。

你要准备给我的信息：

| 信息 | 是否敏感 | 给法 |
| --- | --- | --- |
| 店铺类型：淘宝、天猫、1688 等 | 低敏 | 可以发 |
| 应用类型 | 低敏 | 可以发 |
| App Key | 低敏 | 可以发 |
| 已申请权限截图 | 中敏 | 遮住密钥后发 |
| 是否能看到客服/消息发送权限 | 低敏 | 可以发 |
| App Secret / session token | 敏感 | 不发聊天，填 `.env` |

我们验收什么：

- 如果只能做插件，就先做客服面板 Copilot。
- 如果有官方消息发送权限，再做真实 send adapter。
- 不允许用千牛网页模拟点击或外挂。

官方参考：

- 淘宝开放平台：https://open.taobao.com/
- 阿里客户面板插件文档：https://developer.alibaba.com/docs/doc.htm?articleId=119210&docType=1&treeId=780
- 阿里内部调试 API 风险示例：https://jaq-doc.alibaba.com/docs/api.htm?apiId=22542

## 8. 京东 / 咚咚

推荐优先级：低到中。取决于 JOS 权限包。

你去哪里操作：

1. 打开京东 JOS：https://jos.jd.com/
2. 登录商家或服务商开发者账号。
3. 创建应用。
4. 在 API 列表中查找“客服机器人”“咚咚”“客服消息”相关权限包。
5. 申请客服机器人基础包或相关能力。
6. 授权测试店铺。
7. 如果没有客服消息发送权限，截图给我。

当前我们没有京东 provider。预期后续 URL 类似：

```text
https://<测试域名>/api/webhooks/jd/channels/{channel_id}
```

你要准备给我的信息：

| 信息 | 是否敏感 | 给法 |
| --- | --- | --- |
| App Key | 低敏 | 可以发 |
| 店铺 ID | 低敏 | 可以发 |
| 已开通 API 包截图 | 中敏 | 遮住密钥后发 |
| App Secret / access token | 敏感 | 不发聊天，填 `.env` |

我们验收什么：

- 先验证 JOS 权限包是否包含客服消息能力。
- 再实现 token、签名、消息 parser、send adapter。

官方参考：

- 京东 JOS：https://jos.jd.com/
- 京东客服机器人基础包：https://jos.jd.com/apilist?apiGroupId=952&apiGroupName=%E5%AE%A2%E6%9C%8D%E6%9C%BA%E5%99%A8%E4%BA%BA-%E5%9F%BA%E7%A1%80%E5%8C%85

## 9. 拼多多 / 多多客服

推荐优先级：最低，除非客户明确有官方权限。

你去哪里操作：

1. 打开拼多多开放平台：https://open.pinduoduo.com/
2. 登录商家或服务商开发者账号。
3. 创建应用。
4. 在 API 权限里搜索“客服”“消息”“聊天”“机器人”“多多客服”。
5. 如果能看到官方客服消息发送 API，截图给我。
6. 如果没有，就记录为“当前账号无公开自动客服发送权限”。

当前我们没有拼多多 provider。不要在没有官方权限和文档的情况下承诺自动回复。

你要准备给我的信息：

| 信息 | 是否敏感 | 给法 |
| --- | --- | --- |
| Client ID / App ID | 低敏 | 可以发 |
| 店铺 ID | 低敏 | 可以发 |
| API 权限列表截图 | 中敏 | 遮住密钥后发 |
| Client Secret / access token | 敏感 | 不发聊天，填 `.env` |

我们验收什么：

- 第一阶段只确认有没有官方客服消息 API。
- 没有明确官方文档，不做自动回复。

官方参考：

- 拼多多开放平台：https://open.pinduoduo.com/

## 10. 我建议你现在立刻做哪一个

第一步只做一个：企业微信/微信客服。

你现在可以这样做：

1. 登录企业微信管理后台。
2. 开通微信客服。
3. 新建一个测试客服账号。
4. 绑定你自己的接待人员。
5. 找到开发配置。
6. 等我给你一个公网 HTTPS 回调 URL。
7. 把 URL、Token、EncodingAESKey 填进去。
8. 获取客服链接。
9. 用个人微信打开链接，发送一句：

```text
你好，我想了解智能客服系统价格和接入方式
```

10. 我们看系统是否收到回调、是否生成草稿、是否进入人工审核。

这一步通过以后，才进入真实发送测试。真实发送测试也只允许白名单测试账号、固定测试话术、人工确认后发送。

## 11. 发给我的最小信息模板

你可以按这个格式给我：

```text
准备测试渠道：企业微信/微信客服
账号类型：测试企业 / 正式企业
是否已开通微信客服：是 / 否
是否已创建客服账号：是 / 否
是否已绑定接待人员：是 / 否
是否能看到开发配置：是 / 否
CorpID：可以填
open_kfid：可以填
回调 URL 页面截图：已准备 / 未准备
Token：已填到 .env / 未填
EncodingAESKey：已填到 .env / 未填
Secret：已填到 .env / 未填
测试消息发送人：我自己的微信 / 其他测试号
```

如果是公众号：

```text
准备测试渠道：微信公众号测试号
是否已登录测试号：是 / 否
AppID：可以填
原始 ID：可以填
服务器配置是否已启用：是 / 否
Token：已填到 .env / 未填
EncodingAESKey：已填到 .env / 未填
AppSecret：已填到 .env / 未填
测试关注人：我自己的微信
```

如果是抖音/电商平台：

```text
准备测试渠道：抖音 / 抖店 / 小红书 / 淘宝 / 京东 / 拼多多
账号类型：商家 / 服务商 / 测试应用 / 正式应用
是否已创建应用：是 / 否
AppID 或 App Key：可以填
是否能看到客服/私信/消息相关权限：是 / 否
权限截图：已准备 / 未准备
是否已完成店铺或账号授权：是 / 否
Secret/token：已填到 .env / 未填
```

## 12. 放行红线

以下情况不要继续自动回复测试：

- 平台后台找不到客服消息、私信、会话或机器人相关权限。
- 平台只给了订单/商品/售后 API，没有会话消息发送 API。
- 需要个人号外挂、Hook、群控、模拟点击或浏览器自动化登录后台。
- 没有公网 HTTPS 回调 URL。
- 不能提供测试账号或白名单测试用户。
- 客户要求直接对真实用户自动发消息，但没有完成小范围 sandbox。

## 13. 下一步工程动作

当你完成企业微信/微信客服的后台准备后，我这边要做：

1. 生成或确认 `channel_id`。
2. 给你正式回调 URL。
3. 补生产 AES 解密和真实消息 parser。
4. 把 Token、EncodingAESKey、Secret 接入 secret store 或 `.env`。
5. 跑平台 URL 校验。
6. 跑真实入站消息。
7. 跑 AI 草稿和人工审核。
8. 最后再决定是否打开白名单真实发送。

在第 8 步之前，系统仍然只做“收到消息 -> 生成草稿 -> 人工审核”，不会自动给真实用户发出去。
