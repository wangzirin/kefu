# P3-06N RBAC 第七片：渠道连接器、回执与发送计划权限

日期：2026-07-01  
范围：渠道 provider 注册表、连接器配置、连接器读取、手工回执、回执列表、connector 发送计划  
状态：第七片完成

## Engineering Control Card

- Stage: P3-06N RBAC 第七片
- 当前主线阶段: 后端资源级 RBAC 收口
- 上一阶段真正完成: P3-06M 已把工单、客户画像和线索动作迁到 `ticket.*`、`customer.read`、`lead.*`
- 上一阶段明确没有完成: 渠道连接器、secret 引用、回执读取、发送计划权限迁移；前端按钮级权限；字段 allowlist
- 本轮要交付的客户可见价值: 渠道接入相关的高风险动作不再只靠“登录即可操作”，查看角色不能读取回执原文或生成发送计划，坐席可以生成受控发送计划但不能配置平台密钥
- 本轮是否只是评测: 否
- 本轮不做什么: 不打开真实外发、不新增真实平台发送器、不改企微/公众号/电商官方接入协议、不改数据库结构、不改前端页面
- 外部风险: 无真实外发；官方 webhook 回调入口仍保持平台可达；不读写第三方平台
- 需要用户授权的动作: 无
- 验证方式: P3-06N 后端测试、渠道连接器和 webhook 回归、静态 readiness 检查、RBAC 前序回归、后端全量测试、前端构建
- 写回文件: 产品化总控手册、Superpowers P3 计划、Workspace Project_012 记录
- 下一阶段: 前端按钮级权限，或继续迁移 outbox draft/dry-run send-attempt/delivery failure review 等剩余资源权限

## 1. 权限矩阵

| 权限 | owner | admin | agent | viewer |
| --- | --- | --- | --- | --- |
| `channel.read` | 允许 | 允许 | 允许 | 允许 |
| `channel.connector.manage` | 允许 | 允许 | 禁止 | 禁止 |
| `channel.delivery_receipt.read` | 允许 | 允许 | 允许 | 禁止 |
| `channel.delivery_receipt.manage` | 允许 | 允许 | 禁止 | 禁止 |
| `outbox.send_plan.manage` | 允许 | 允许 | 允许 | 禁止 |

口径：

- `channel.read` 控制渠道 provider 注册表和连接器配置摘要读取。当前连接器只暴露脱敏后的 public config 和 secret 状态，不返回 secret 明文。
- `channel.connector.manage` 控制连接器配置写入，包括 provider、模式、状态、webhook path、签名模式和 `credential_ref` 一类 secret 引用。
- `channel.delivery_receipt.read` 控制回执列表和回执原文读取。回执里可能包含平台事件字段、错误码、签名校验结果和排障上下文，viewer 暂不开放。
- `channel.delivery_receipt.manage` 控制手工记录占位回执，用于 sandbox、故障复盘和测试场景。普通坐席不能伪造平台回执。
- `outbox.send_plan.manage` 控制从已确认草稿生成连接器发送计划。当前计划仍是 `connector_noop`，外部写入保持关闭。

## 2. 已迁移接口

| 接口 | 权限 |
| --- | --- |
| `GET /api/channel-providers` | `channel.read` |
| `GET /api/channels/{channel_id}/connector-config` | `channel.read` |
| `POST /api/channels/{channel_id}/connector-config` | `channel.connector.manage` |
| `GET /api/channels/{channel_id}/delivery-receipts` | `channel.delivery_receipt.read` |
| `POST /api/channels/{channel_id}/delivery-receipts` | `channel.delivery_receipt.manage` |
| `POST /api/outbox-drafts/{draft_id}/connector-send-plans` | `outbox.send_plan.manage` |

## 3. 保留的服务层规则

本轮只迁移 API 入口权限，不改变已有渠道业务规则。

继续保留：

- 跨租户渠道、连接器、草稿和回执返回 404。
- 连接器配置会对 public config 里的敏感 key 做脱敏，不保存 secret 明文。
- 连接器 `external_write_enabled` 继续强制为 `False`。
- 发送计划只能基于 `ready_to_send` 草稿生成。
- 发送计划仍是 `connector_noop`，不会触达外部平台。
- 官方 webhook 入站继续走 provider、connector、签名、密钥引用、幂等和可信入站边界。

## 4. 官方 webhook 为什么不加普通 RBAC

企微、公众号或其他平台回调不是后台坐席发起的请求，平台无法携带我们的坐席 bearer token。

因此以下入口继续保持无坐席登录依赖：

- `GET /api/webhooks/wecom/channels/{channel_id}`
- `POST /api/webhooks/wecom/channels/{channel_id}`
- `POST /api/webhooks/{provider}/channels/{channel_id}`

它们的安全边界不是 `require_permission()`，而是：

1. 找到同租户的渠道连接器。
2. 校验 provider 与连接器配置一致。
3. 按签名模式验证 query/body。
4. 通过 secret 引用解析 Token/AESKey/HMAC secret。
5. 验签失败或 secret 缺失时记录不可信占位回执，不创建可信消息。
6. 验签通过后才进入可信入站、幂等和会话消息创建流程。

这个边界和后台 RBAC 是两套不同防线，不能互相替代。

## 5. Secret 引用边界

当前系统没有把平台密钥明文放进 API 响应，也没有在连接器表里保存明文 secret。

本轮采用的阶段性口径：

- `public_config` 可以保存 `credential_ref`、占位 corp id、webhook path 等非明文配置。
- `connector_secret_status()` 只返回 secret 状态，例如 `not_configured`、`fixture_configured`。
- `channel.connector.manage` 允许 owner/admin 修改 secret 引用。
- agent/viewer 不能修改连接器配置或 secret 引用。
- 后续如果增加单独的密钥轮换、测试密钥、密钥解析诊断接口，应再拆 `channel.secret.manage`。

## 6. 验收结果

- 新增 `backend/tests/test_p3_06n_channel_delivery_rbac.py`，覆盖权限矩阵、无 token 401、viewer registry 读取、agent 配置连接器 403、owner 配置连接器、agent/viewer 连接器摘要读取、viewer 回执读取 403、agent 手工写回执 403、owner 手工写回执、agent 回执读取、agent 发送计划、viewer 发送计划 403。
- 渠道连接器原有测试通过，确认连接器仍不真实外发。
- 官方 webhook 原有测试通过，确认平台回调入口没有被普通 RBAC 误锁。
- 新增 `scripts/check_p3_06n_channel_delivery_rbac.py`，用于静态检查 RBAC、API、测试和文档是否保持一致。

## 7. 后续建议

1. 前端按钮级权限：根据 `user.permissions` 隐藏或禁用连接器配置、手工回执、发送计划、工单、线索、知识发布等按钮。
2. 字段 allowlist：把连接器 config、回执 raw payload、联系人资料、线索备注按 owner/admin/agent/viewer 做响应字段收口。
3. Outbox 剩余权限：把 outbox draft 创建、确认、dry-run send-attempt、delivery failure review 继续迁到命名权限。
4. Secret 专项：当出现单独密钥轮换或生产 secret 诊断接口时，拆 `channel.secret.manage`，并确保永不返回明文。
5. 官方渠道 smoke：公网 HTTPS、Token、EncodingAESKey 和测试客服账号具备后，再做企微官方 URL 验证和白名单入站测试。
