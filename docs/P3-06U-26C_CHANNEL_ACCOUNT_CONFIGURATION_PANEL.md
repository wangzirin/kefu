# P3-06U-26C 渠道账号/店铺配置面板

日期：2026-07-02  
性质：内部工程记录  
范围：渠道接入页、`channel_accounts` 前端配置入口、对话台渠道身份刷新链路

## 1. 目标

本阶段把渠道账号从“前端演示身份”继续推进为“服务端可配置对象”。渠道接入页新增“渠道账号 / 店铺管理”面板，读取租户渠道和服务端 `channel_accounts`，并允许有权限的管理员保存低敏账号身份。

这不是平台真实外发，也不是已经接通微信、抖音、淘宝、京东、拼多多。它解决的是中台最基础的问题：每条消息和每个会话要能稳定指向“哪个渠道、哪个平台账号、哪个店铺或入口、当前回复模式是什么”。

## 2. 已完成内容

- 前端 API 新增 `listTenantChannels`，读取 `GET /api/tenants/{tenant_id}/channels`。
- 前端 API 新增 `configureChannelAccount`，写入 `POST /api/channels/{channel_id}/channel-accounts`。
- App 新增原始 `channelAccountState`，同时保留 `channelIdentityById` 派生数据供多渠道对话台使用。
- 登录、登出、无权限、演示预览状态都清理或隔离渠道账号状态，避免把预览样例误当作真实服务端账号。
- 渠道接入页新增 `data-channel-account-manager="p3-06u-26c"` 面板。
- 面板包含服务端账号清单、配置缺失空状态、刷新按钮和新增/更新表单。
- 表单只保存平台、账号、店铺、入口、授权状态、接入状态、回复模式、健康状态和公开备注。
- 表单不保存 Secret、Token、Cookie、个人号凭据或店铺授权密钥。
- 保存成功后回刷 `channel_accounts`，多渠道对话台继续读取同一份服务端渠道身份。

## 3. 当前边界

- 真实外发继续关闭。
- 不接真实平台账号。
- 不保存真实平台密钥。
- 不调用微信、抖音、淘宝、京东、拼多多真实发送接口。
- RPA 仍是研究线和 draft-only，不进入正式默认交付链。
- 面板只是账号/店铺身份管理，不代表对应平台已经授权。

## 4. 页面逻辑

渠道接入页现在分三层：

1. 渠道连接器状态中心：说明企业微信 / 微信客服和其他平台当前官方接入路线、阻塞点和真实外发门禁。
2. 渠道账号 / 店铺管理：读取和配置 `channel_accounts`，让中台知道平台账号、店铺、入口和回复模式。
3. 渠道健康、失败复盘和沙盒链路：继续展示入站、队列、回执和异常处理状态。

## 5. 后端契约

读取：

```text
GET /api/tenants/{tenant_id}/channels
GET /api/tenants/{tenant_id}/channel-accounts
```

写入：

```text
POST /api/channels/{channel_id}/channel-accounts
```

写入字段：

| 字段 | 用途 |
| --- | --- |
| `provider` | 渠道提供方，如 `wecom`、`douyin`、`taobao` |
| `platform` | 前端可读平台名，如微信客服、抖音、淘宝 |
| `account_name` | 平台账号或客服账号名称 |
| `external_account_id` | 低敏外部账号标识，不能填 token |
| `store_name` | 店铺、组织或客服账号显示名 |
| `entrypoint_name` | 官网浮窗、客服链接、二维码、店铺入口等 |
| `authorization_status` | 官方授权状态 |
| `access_status` | 当前接入状态 |
| `reply_mode` | 回复模式 |
| `health_status` | 健康状态 |
| `public_profile` | 低敏公开信息，只允许可见范围、备注等 |

## 6. 验收

```bash
backend/.venv/bin/pytest backend/tests/test_channel_connectors_api.py -q
python3 scripts/check_p3_06u_26c_channel_account_configuration.py
cd frontend && npm run typecheck && npm run build
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 FRONTEND_URL='http://127.0.0.1:5182/?demo=1#channels' node ../scripts/check_p3_06u_26c_channel_account_configuration.mjs
```

通过标准：

- 渠道接入页能看到“渠道账号 / 店铺管理”。
- 无真实登录时显示配置来源边界，不把预览样例伪装成服务端账号。
- 正式登录后可以读取租户渠道和 `channel_accounts`。
- 有 `channel.connector.manage` 权限时可以保存低敏账号身份。
- 保存后回刷账号列表和多渠道对话台渠道身份。
- 页面明确写出真实外发继续关闭。
- 敏感凭据不进入前端表单。

## 7. 下一步

进入 P3-06U-26D：知识三页组件拆分和真实服务端数据深化。重点是让知识库运营、知识缺口、知识评测三页不仅路由分开，而且数据、动作、指标和空状态都真正分开。
