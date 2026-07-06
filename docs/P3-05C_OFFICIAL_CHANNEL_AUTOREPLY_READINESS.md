# P3-05C 官方渠道自动回复可行性与当前系统差距

## Engineering Control Card

- Stage: P3-05C
- 当前主线阶段: Lite 试点封版前的官方渠道自动回复核验
- 上一阶段真正完成: P3-05B readiness smoke 已通过，托管云 runbook、私有化部署包、远程维护授权 SOP 和封版自检已完成
- 上一阶段明确没有完成: 真实官方渠道接入、真实外发、生产级 sender、真实客户 50-100 题、人工事实性标签、官方测试号端到端验收
- 本轮要交付的客户可见价值: 把“微信、企微、抖音、小红书、淘宝等到底能不能自动回复”拆成官方可行性、当前系统实现状态、必须准备的授权材料和下一步施工顺序
- 本轮是否只是评测: 否。本轮是渠道准入核验和交付边界固化
- 如果是评测，本轮问题是什么: 不适用
- 如果是评测，停止条件是什么: 不适用
- 本轮不做什么: 不登录真实平台、不配置真实密钥、不调用真实发送 API、不使用个人号外挂、Hook、群控、模拟点击、商家后台自动化或逆向 IM
- 外部风险: 平台权限、账号资质、回调域名、平台风控、误发、违规营销、售后赔付承诺、客户隐私和模型误答
- 需要用户授权的动作: 任何真实平台账号登录、真实 AppSecret/Token/EncodingAESKey 使用、真实外发、真实客户数据导入、真实模型批量调用
- 验证方式: 官方文档链接核验、当前代码合同检查、readiness JSON 矩阵和只读 smoke 脚本
- 写回文件: 本文档、`docs/channel_autoreply_readiness_matrix.json`、Superpowers 计划、Project_012 执行记录/关键决策/文件索引/复盘
- 下一阶段: P3-05C 第二片可选，先做企业微信/微信客服官方 sandbox connector；或回到 Lite 知识包模板、题库模板和工作台最终浏览器 QA

## 结论先行

**现在不能对外说“微信、企微、抖音、小红书、淘宝都已经可以自动回复”。**

更准确的结论是：

| 渠道 | 平台层面是否可能自动回复 | 我们当前系统是否已接通 | 可以对外怎么说 |
| --- | --- | --- | --- |
| 官网客服 | 可以，因为是自有入口 | 已有官网 sandbox Copilot 链路，但真实生产自动发送仍关闭 | 可做 Lite 首个试点入口 |
| 企业微信/微信客服 | 可以，需企业微信官方授权和客服能力配置 | 只有 provider 合同、fixture 验签和可信入站骨架 | 可列为优先官方 connector，未做真实 sandbox 前不能承诺已接通 |
| 微信公众号/服务号 | 可以，受账号类型、用户互动窗口、被动回复/客服消息规则约束 | 只有 provider 合同和 fixture 验签 | 可做官方账号 connector，不能说无限主动群发或个人微信自动回复 |
| 抖音开放平台私信 | 部分场景可以，需应用权限和私信/企业号相关 scope | 当前没有代码实现 | 可作为标准运营版后续官方 connector |
| 抖店/飞鸽 | 平台有客服和机器人体系，但公开通用会话发送 API 需权限确认 | 当前没有代码实现 | 先按 Copilot/人工确认卖，不承诺自动真实发送 |
| 小红书 | 有开放平台/商业平台和私信三方工具线索，但通用自动回复能力需后台权限确认 | 当前没有代码实现 | 只能作为授权后专项 connector，不进 Lite 默认承诺 |
| 淘宝/天猫/千牛 | 有开放平台、店小蜜、客服面板插件路线，但通用聊天发送能力强权限/服务市场约束 | 当前没有代码实现 | 先做客服面板 Copilot/知识建议，不能模拟千牛 |
| 京东/咚咚 | JOS 有客服机器人相关包，但需店铺和权限包 | 当前没有代码实现 | 后续标准/企业版 connector |
| 拼多多/多多客服 | 未公开核验到通用客服聊天发送 API | 当前没有代码实现 | 不承诺自动回复，等官方权限和文档 |

本轮最重要的边界是：**平台可行不等于我们已实现；我们有 connector 骨架不等于真实平台已接通；测试 webhook 不等于能自动发消息。**

## 当前系统真实状态

当前代码中，渠道层只有三个 provider 合同：

- `website`
- `wecom`
- `wechat_official_account`

其中：

- `website` 已在 P3-04 跑通过开发 fixture：HMAC 验签、可信入站、AI 草稿、人审、outbox 和发送计划门禁。
- `wecom` 已有企业微信客服 provider 合同和 SHA1 fixture 验签逻辑，但生产 AES 解密、真实 access token、真实客服消息发送 API、真实回执还没有做。
- `wechat_official_account` 已有公众号/服务号 provider 合同和 fixture 验签逻辑，但生产安全模式解密、被动回复时限、客服消息窗口、真实发送 API 还没有做。
- 抖音、小红书、淘宝、京东、拼多多没有 provider 合同、没有签名验签器、没有 webhook event parser、没有 token 管理、没有 send adapter。
- `OUTBOX_EXTERNAL_WRITE_ENABLED=false` 仍是正确默认值。
- 当前 outbox worker 和 connector send plan 都固定 `external_write=false`，不会真的向任何平台发送。

因此，当前 Lite 试点版最真实的可交付表达是：

> 支持官网/自有入口的智能客服 Copilot 试点；企业微信和公众号可进入官方 sandbox 接入施工；抖音、小红书、淘宝、京东、拼多多需要平台授权和专项 connector 后才能进入真实自动回复。

## 官方渠道逐项判断

### 1. 企业微信客服 / 微信客服

官方层面：可行。

依据：

- 企业微信开发者中心存在微信客服“发送消息”文档。
- 企业微信开发者中心存在客服接待人员管理和获取客服账号链接等文档。
- 这条路线需要企业微信/微信客服能力、客服账号、接待人员、回调 Token、EncodingAESKey、服务端回调 URL 和 access token。

当前系统差距：

- 已有 `wecom` provider contract。
- 已有 fixture 级 SHA1 验签。
- 未做生产 AES 解密。
- 未做官方 access token 刷新。
- 未做客服消息 send adapter。
- 未做会话状态、客户身份和平台错误码完整映射。

施工顺序：

1. 用企业微信测试企业或客户测试企业开通微信客服。
2. 配置回调 URL、Token、EncodingAESKey。
3. 在我们系统中接入真实 secret store，不把密钥写入源码。
4. 实现 AES 解密和明文消息 schema mapping。
5. 实现 `wecom_kf` 真实 send adapter，但默认仍走人工确认。
6. 做官方 sandbox 端到端：用户发消息 -> 平台回调 -> 我们验签/解密 -> 创建入站 -> AI 草稿 -> 人工审核 -> outbox -> 调官方 send -> 回执。

结论：这是最适合作为第一条真实官方渠道的外部平台。

### 2. 微信公众号 / 服务号

官方层面：可行，但受限制。

限制包括：

- 账号类型和认证状态会影响能力。
- 普通消息可做被动回复，但平台对响应时限有要求。
- 客服消息通常依赖用户互动窗口，不是无限主动触达。
- 安全模式需要消息解密。

当前系统差距：

- 已有 `wechat_official_account` provider contract。
- 已有明文/加密 fixture 验签框架。
- 未做生产解密和回复时限策略。
- 未做客服消息窗口策略。
- 未做 OpenID、会话和外发回执完整映射。

结论：适合第二条微信系 connector。不能把它说成个人微信自动回复，也不能承诺无限主动私聊。

### 3. 抖音开放平台私信 / 企业号私信

官方层面：部分场景可行。

公开文档能看到抖音开放平台私信发送、Webhook 事件、抖音小程序客服消息推送等能力。真实可用性取决于应用类型、账号类型、授权 scope、审核状态和平台规则。

当前系统差距：

- 没有 `douyin_open` provider。
- 没有 OAuth token 刷新。
- 没有 Webhook 签名验证。
- 没有私信事件 parser。
- 没有 send adapter。
- 没有 Msg-Id 去重和错误码映射。

结论：可以进入标准运营版路线，但不应进入 Lite 默认承诺。必须拿到官方测试应用和 scope 后才能验证自动回复。

### 4. 抖店 / 飞鸽客服

官方层面：需要保守。

抖店/飞鸽和抖音开放平台私信不是同一条能力线。公开资料能看到飞鸽客服相关 API、平台 AI 服务和机器人体系，但也能看到部分会话消息接口并非公开开放的提示。商家客服自动回复要以抖店开放平台、服务市场、飞鸽官方能力或客户店铺后台授权为准。

当前系统差距：

- 没有抖店 provider。
- 没有店铺授权、订单上下文、售后上下文。
- 没有飞鸽消息 send adapter。
- 没有服务市场应用形态。

结论：先做售前/售后 Copilot 与人工确认，不承诺无条件自动回复。拿到商家测试店和权限包后再验证。

### 5. 小红书

官方层面：部分线索存在，但通用自动回复未公开充分验证。

小红书有开放平台、商业开放平台和私信三方工具相关资料，但这不等同于所有专业号都开放通用私信自动发送。真实能力通常取决于账号类型、商业平台权限、工具接入资质和后台开通情况。

当前系统差距：

- 没有 `xiaohongshu` provider。
- 没有私信 webhook parser。
- 没有发送 API 合同。
- 没有内容风控和营销合规策略。

结论：只能作为授权专项 connector。对外不要说已经支持小红书自动回复。

### 6. 淘宝 / 天猫 / 千牛 / 店小蜜

官方层面：强权限、强生态约束。

阿里体系更适合走服务市场、店小蜜、千牛客服面板插件、订单/售后数据授权和客服辅助。公开资料能看到客服面板插件路线，也能看到部分内部调试接口明确不建议集成。不能把淘宝开放平台的消息服务误读为通用旺旺聊天自动发送。

当前系统差距：

- 没有 `taobao_tmall` provider。
- 没有服务市场应用。
- 没有千牛客服面板插件。
- 没有买家/订单/售后授权映射。
- 没有官方聊天 send API 验证。

结论：第一阶段只能卖 Copilot/知识建议/人工确认。严禁用千牛网页自动化、模拟点击或外挂。

### 7. 京东 / 咚咚

官方层面：可能可行，但需要 JOS 权限包。

JOS 能看到客服机器人相关 API 包。真实能否发送咚咚消息，要看应用、店铺授权、API 包和平台审核。

当前系统差距：

- 没有 `jd` provider。
- 没有 JOS token、签名、店铺授权。
- 没有咚咚消息 send adapter。

结论：后续标准/企业版 connector，不进入 Lite 默认交付。

### 8. 拼多多 / 多多客服

官方层面：公开通用客服聊天发送 API 未核验充分。

在公开网页检索范围内，未能可靠确认一个可直接用于通用多多客服自动发送的官方 API。拼多多如果要做，必须由客户或我方服务商账号在开放平台后台确认权限和文档。

当前系统差距：

- 没有 `pinduoduo` provider。
- 没有商家授权和消息 API 合同。

结论：暂不承诺自动回复。只能在拿到官方文档和权限后做专项验证。

## 我们下一步最合理的施工顺序

不要同时开微信、企微、抖音、小红书、淘宝、京东、拼多多。这样会把工程变成权限泥潭，也最容易出现封号和误承诺。

推荐顺序：

| 顺序 | 渠道 | 原因 | 本阶段验收 |
| --- | --- | --- | --- |
| 1 | 官网客服 | 自有入口，风险最低 | 低风险 FAQ 自动草稿、人审、outbox、审计、可关闭 |
| 2 | 企业微信客服 / 微信客服 | 官方 API 明确，B2B 私域价值最高 | 官方 sandbox 入站到人工确认，再到真实 send adapter |
| 3 | 微信公众号/服务号 | 微信生态常见入口 | 被动回复/客服消息窗口策略验证 |
| 4 | 抖音开放平台私信 | 部分官方私信 API 明确，但权限依赖强 | Scope 审批后做 webhook + send adapter |
| 5 | 电商平台专项 | 淘宝/抖店/京东/拼多多都强依赖商家授权和服务市场 | 先 Copilot，再逐平台服务商 connector |
| 6 | 小红书专项 | 权限和商业平台差异大 | 拿到私信三方工具或官方文档后再做 |

## 真实自动回复放行门槛

某个平台要被标记为“可自动回复”，必须同时满足：

1. 有官方文档或服务商后台权限证明。
2. 有客户授权账号或官方 sandbox。
3. 有可访问的 HTTPS 回调域名。
4. 回调验签通过。
5. 加密消息能解密。
6. 入站消息能映射为内部 message。
7. 重复回调不会重复创建消息。
8. AI 草稿有知识引用和风险标签。
9. 高风险、售后赔付、法务、退款、投诉、舆情必须转人工。
10. 低风险自动回复策略被客户书面确认。
11. outbox 真实 sender 已实现平台适配。
12. 平台回执、失败码、限流、重试、死信和人工复盘已实现。
13. `OUTBOX_EXTERNAL_WRITE_ENABLED` 能随时关闭。
14. 真实测试至少覆盖 50 条脱敏问题和 20 条平台回调样本。

少任何一项，都只能叫“接入施工中”或“Copilot 辅助回复”，不能叫“全自动回复已上线”。

## 来源链接

- 企业微信开发者中心，微信客服发送消息: https://developer.work.weixin.qq.com/document/path/94677
- 企业微信开发者中心，接待人员管理: https://developer.work.weixin.qq.com/document/path/94693
- 企业微信开发者中心，获取客服账号链接: https://developer.work.weixin.qq.com/document/path/94692
- 微信服务号/公众号文本客服消息: https://developers.weixin.qq.com/doc/service/api/message/message/api_send_text_msg.html
- 微信公众号客服接口说明: https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Service_Center_messages.html
- 抖音开放平台，发送私信消息: https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/interaction-management/private-message/send-msg
- 抖音开放平台，Webhook 事件列表: https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/webhooks/event-list
- 抖音小程序，客服消息推送: https://developer.open-douyin.com/docs/resource/zh-CN/mini-app/develop/server/customer-service/receive-msg/push-msg
- 抖店开放平台，飞鸽客服相关接口: https://op.jinritemai.com/docs/api-docs/188
- 抖店开放平台，会话消息接口开放边界问答: https://op.jinritemai.com/docs/question-docs/96/6260
- 飞鸽 AI 服务协议: https://fxg.jinritemai.com/ffa/maomao/agreement/AiService
- 小红书开放平台开发者协议: https://open.xiaohongshu.com/document/developer/file/4
- 小红书商业开放平台私信三方工具资料: https://ad-market.xiaohongshu.com/docs-center?articleId=4437&bizType=943
- 淘宝开放平台: https://open.taobao.com/
- 阿里开放平台客服面板插件文档: https://developer.alibaba.com/docs/doc.htm?articleId=119210&docType=1&treeId=780
- 阿里接口说明中“不建议直接集成”的内部调试 API 示例: https://jaq-doc.alibaba.com/docs/api.htm?apiId=22542
- 京东宙斯开放平台: https://jos.jd.com/
- 京东 JOS 客服机器人基础包: https://jos.jd.com/apilist?apiGroupId=952&apiGroupName=%E5%AE%A2%E6%9C%8D%E6%9C%BA%E5%99%A8%E4%BA%BA-%E5%9F%BA%E7%A1%80%E5%8C%85
- 拼多多开放平台: https://open.pinduoduo.com/
