# 远程维护授权 SOP

更新时间：2026-06-29  
适用范围：Lite 试点版、标准运营版、托管云端单客户实例、私有化部署环境  
使用对象：我方交付、工程、运维、客户成功和销售负责人  
文档属性：内部操作标准，不直接对外发送；客户版应抽取为授权单、排障说明和复盘报告。

## 1. 核心原则

远程维护不是长期后门，也不是默认登录客户生产环境。所有远程排障都按以下顺序推进：

1. 诊断包优先：先让客户运行只读诊断包，优先离线分析。
2. 只读优先：诊断包不足时，再申请限时只读远程。
3. 最小权限：只申请本次故障必需的账号、目录、服务和时间窗口。
4. 变更二次授权：任何重启、迁移、改配置、恢复数据、清理数据、打开外发都必须二次确认。
5. 变更前备份：涉及数据库、知识库、配置或持久化 volume 的动作，先确认备份和回滚点。
6. 全程留痕：故障单、授权单、命令记录、验证结果和客户确认必须能追溯。
7. 结束权限回收：排障结束后关闭隧道、回收临时账号、撤销临时密钥，必要时轮换凭据。
8. 不记录密钥：文档、聊天、工单和复盘里不得出现 API key、token、密码、私钥、webhook secret 或客户原始敏感数据。

## 2. 故障分级

以下分级用于内部响应和调度，不自动等同于合同 SLA。若合同另有 SLA，以合同为准。

| 等级 | 典型情况 | 内部响应目标 | 第一动作 | 是否需要复盘 |
| --- | --- | --- | --- | --- |
| P0 | 系统整体不可用；存在误外发、数据丢失、密钥泄露或安全入侵风险；所有坐席无法登录；错误配置可能继续扩大影响 | 15 分钟内完成初判和止血动作 | 立即关闭外发或相关入口，保留现场，建立故障指挥线 | 必须 |
| P1 | 关键功能大面积异常；模型/provider 大面积失败；队列积压导致回复停滞；渠道官方回调失败；数据库迁移或升级失败但未造成数据丢失 | 1 小时内完成原因定位或降级方案 | 切 fallback、暂停自动化、限制风险功能，启动只读诊断 | 必须 |
| P2 | 部分功能异常；单渠道、单客户、部分账号或部分知识库版本受影响；准确率明显下降；外发失败增多但有人工兜底 | 1 个工作日内给出修复计划 | 收集样本、诊断包和最近变更，安排修复窗口 | 建议 |
| P3 | 文案、培训、配置、轻微体验、个别题库或知识口径问题；未影响核心接待和安全边界 | 按排期处理 | 客户成功或交付团队先处理，必要时进入知识更新流程 | 按需 |

### 2.1 P0 立即止血清单

P0 不等待完整根因分析，先阻断继续扩大影响：

- 确认 `OUTBOX_EXTERNAL_WRITE_ENABLED=false` 或临时关闭真实外发开关。
- 暂停相关 channel connector、worker 或 webhook 入口。
- 禁止继续修改数据库和配置，先保留现场。
- 导出只读诊断包和最近审计事件摘要。
- 通知客户授权联系人和我方项目负责人。
- 若涉及密钥泄露，指导客户轮换密钥，并确认旧密钥失效。

## 3. 远程维护标准流程

| 步骤 | 动作 | 产物 | 说明 |
| --- | --- | --- | --- |
| 1 | 建立故障单 | 故障单编号 | 记录客户、环境、影响范围、发现时间、联系人 |
| 2 | 确认分级 | P0/P1/P2/P3 | 分级可在排障中调整，但要记录调整原因 |
| 3 | 客户运行诊断包 | 脱敏诊断包 | 优先使用 `scripts/create_p3_05_diagnostic_bundle.py` 或客户环境等价脚本 |
| 4 | 只读离线分析 | 初步判断 | 不需要远程登录时，直接给客户修复建议或下一步信息 |
| 5 | 申请只读远程 | 临时授权单 | 写明操作人、时间窗口、访问方式、目录、命令范围和数据边界 |
| 6 | 执行只读检查 | 命令记录 | 只运行白名单命令，不读取 `.env` 明文和客户原始数据 |
| 7 | 如需变更，提交二次授权 | 变更单 | 写明变更原因、命令、备份、回滚、影响和验证方式 |
| 8 | 变更前备份 | 备份文件或客户备份确认 | 数据库、知识库、配置和 volume 变更必须有回滚点 |
| 9 | 执行变更 | 命令记录和结果 | 尽量在客户维护窗口执行，必要时全程录屏或堡垒机审计 |
| 10 | Smoke 验证 | 验证记录 | 健康检查、登录、知识检索、AI 草稿、人审、outbox 门禁 |
| 11 | 权限回收 | 回收记录 | 关闭隧道、删除临时账号、撤销临时 key，必要时轮换凭据 |
| 12 | 故障复盘 | 复盘报告 | P0/P1 必须复盘；P2 建议复盘；P3 按需记录 |

## 4. 授权方式

### 4.1 推荐方式

| 方式 | 适用场景 | 要求 |
| --- | --- | --- |
| 诊断包离线分析 | 大多数 P2/P3、可复现问题、质量下降 | 不含密钥、不含客户原始聊天、不含未脱敏数据 |
| VPN / 零信任访问 | 私有化部署、客户有统一安全网关 | 限时、MFA、IP 白名单、账号到期自动失效 |
| 堡垒机 | 中大型客户、强审计客户 | 命令留痕、会话录屏、账号实名、权限最小化 |
| 临时出站隧道 | 客户网络限制但可主动建立通道 | 有到期时间，仅开放必要端口，不开放数据库公网端口 |
| 屏幕共享指导客户操作 | 客户不允许我方登录服务器 | 由客户操作，我方指导；关键命令仍按授权单执行 |

### 4.2 禁止方式

- 长期开公网 SSH、RDP、数据库端口、Redis 端口。
- 我方长期保存客户 root 密码、数据库管理员密码或生产模型 key。
- 通过个人聊天软件发送 `.env`、数据库 dump、密钥、未脱敏聊天记录。
- 使用个人微信外挂、Hook、群控、模拟点击方式处理客户渠道故障。
- 在未授权情况下执行真实外发、真实模型批量调用或生产数据库变更。

## 5. 临时授权单模板

| 字段 | 填写要求 |
| --- | --- |
| 故障单编号 | 必填 |
| 客户名称 | 必填 |
| 环境 | 托管云 / 私有化 / 测试 / 演示 |
| 故障等级 | P0/P1/P2/P3 |
| 授权人 | 客户侧有权审批人 |
| 我方操作人 | 必填，不能写团队代称 |
| 授权窗口 | 起止时间，必须有到期时间 |
| 访问方式 | 诊断包 / VPN / 零信任 / 堡垒机 / 临时隧道 / 屏幕共享 |
| 权限范围 | 只读 / 指定服务重启 / 指定配置变更 / 指定迁移 |
| 可访问系统 | 服务器、容器、数据库、对象存储、日志系统等 |
| 数据边界 | 是否可看日志、是否可看脱敏样本、是否禁止原文 |
| 允许命令 | 具体到命令类别或命令清单 |
| 禁止命令 | 至少包含本 SOP 第 8 节命令 |
| 备份位置 | 变更类必须填写 |
| 回滚方式 | 变更类必须填写 |
| 验证方式 | 健康检查、登录、知识检索、AI 草稿、人审、outbox 门禁等 |
| 权限回收方式 | 删除账号 / 关闭隧道 / 撤销密钥 / 防火墙回滚 |

## 6. 只读命令白名单

以下命令可作为私有化或托管实例的默认只读排障白名单。执行前必须先确认客户实际安装目录和 Compose 文件路径；如果客户环境不是 Compose，以客户运维标准命令为准。

```bash
cd /opt/wanfa/standard_ops
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.pilot.yml ps
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.pilot.yml logs --tail=200 backend
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.pilot.yml logs --tail=200 frontend
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.pilot.yml logs --tail=200 postgres
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.pilot.yml logs --tail=200 redis
curl -fsS http://127.0.0.1:18080/health
df -h
free -m
docker system df
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.pilot.yml config --services
```

允许查看的数据库信息只限结构、连接状态、迁移版本和聚合数量，不得在未授权情况下导出表数据或查看客户原文。

## 7. 需要二次授权的命令

以下命令不是绝对禁止，但必须有变更单、客户二次确认、备份或回滚方式：

```bash
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.pilot.yml restart backend
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.pilot.yml restart frontend
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.pilot.yml up -d --build
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.pilot.yml pull
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.pilot.yml exec backend alembic upgrade head
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.pilot.yml exec postgres pg_dump --schema-only
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.pilot.yml exec postgres pg_dump
```

以下操作必须额外确认业务影响：

- 修改 `.env` 或 Secret 管理系统里的模型 key、渠道 secret、数据库连接、CORS、外发开关。
- 打开 `OUTBOX_EXTERNAL_WRITE_ENABLED=true`。
- 调整模型路由、检索 top-k、reranker、风险阈值、人审门禁。
- 发布新知识库版本、回滚知识库版本、批量导入题库。
- 执行数据库迁移、数据恢复、容器镜像升级或 volume 迁移。

## 8. 禁止命令和禁止动作

以下命令默认禁止。即使客户要求，也必须先升级为专项变更评审，确认业务影响、备份、回滚和数据合规；其中读取密钥明文类动作不得执行。

```bash
cat .env
cat */.env
printenv
env
docker compose down -v
docker volume rm
docker system prune -a --volumes
rm -rf /
rm -rf ./*
rm -rf /opt/wanfa
alembic downgrade
psql -c "delete from ..."
psql -c "update ..."
psql -c "drop table ..."
scp .env ...
scp *.dump ...
```

禁止动作：

- 未经授权读取、复制或保存客户 `.env`、key、token、secret。
- 未经授权导出客户数据库 dump、聊天原文、知识库原文或用户资料。
- 未经授权打开真实外发、批量发送、真实平台回调或真实模型批量评测。
- 直接在生产库执行没有事务、没有备份、没有 where 条件的数据修改。
- 把客户生产环境作为临时开发环境试错。

## 9. Smoke 验证清单

每次远程排障结束前，至少完成以下检查，并记录结果：

| 检查项 | 通过标准 |
| --- | --- |
| 健康检查 | 后端健康接口返回正常，前端可打开 |
| 登录 | 管理员或坐席测试账号可登录 |
| 知识检索 | 能返回知识引用或明确进入知识缺口 |
| AI 草稿 | 能生成草稿或按规则进入人工审核 |
| 人工审核 | 坐席能批准、改写或拒绝 |
| Outbox 门禁 | 默认真实外发仍关闭，发送计划不会误触达真实平台 |
| 审计记录 | 关键动作有审计事件或操作记录 |
| 诊断包 | 可重新生成脱敏诊断摘要 |
| 权限回收 | 临时账号、隧道、密钥或访问规则已关闭 |

## 10. 故障复盘模板

P0/P1 必须在故障处理后形成复盘。P2 建议复盘，P3 可在周报或月报中归档。

```markdown
# 故障复盘报告

## 基本信息

- 故障单编号：
- 客户名称：
- 环境：
- 故障等级：
- 发现时间：
- 恢复时间：
- 我方负责人：
- 客户确认人：

## 影响范围

- 影响的入口：
- 影响的坐席：
- 影响的会话或请求范围：
- 是否涉及真实外发：
- 是否涉及数据安全或密钥风险：

## 时间线

| 时间 | 事件 | 操作人 | 证据 |
| --- | --- | --- | --- |
|  |  |  |  |

## 原因分析

- 直接原因：
- 根本原因：
- 触发条件：
- 为什么监控或流程没有提前发现：

## 修复动作

- 已执行动作：
- 是否有备份：
- 是否执行回滚：
- 是否涉及配置、数据库、知识库、模型或渠道变更：

## 验证结果

- 健康检查：
- 登录：
- 知识检索：
- AI 草稿：
- 人工审核：
- Outbox 门禁：
- 诊断包：

## 预防措施

- 需要补的测试：
- 需要补的监控：
- 需要补的文档：
- 需要补的知识库流程：
- 需要补的客户培训：

## 客户确认

- 客户确认结果：
- 剩余问题：
- 下次跟进时间：
```

## 11. 准确率下降专项处理

准确率下降通常不是 P0，除非它导致大面积误外发、错误承诺或严重投诉。默认按 P2/P3 处理：

1. 收集最近低置信、转人工、坐席改写和客户纠错样本。
2. 对比最近知识库、prompt、检索参数、模型路由、provider 的变更。
3. 跑固定题库或客户脱敏题库回归。
4. 分桶为知识缺口、知识过期、检索错误、模型表达、风险门禁、渠道场景变化。
5. 先修知识和门禁，再考虑换模型或调路由。
6. 输出质量复盘，必要时安排知识更新发布和二次回归。

严禁把准确率下降直接归因于“模型不行”，也严禁只换更贵模型而不看引用证据、知识版本和人审反馈。

## 12. 记录保存要求

| 材料 | 保存位置 | 保留要求 |
| --- | --- | --- |
| 故障单 | 内部工单或项目记录 | 必须 |
| 授权单 | 内部工单附件或客户确认邮件 | 必须 |
| 诊断包 | 脱敏输出目录或工单附件 | 必须脱敏 |
| 命令记录 | 堡垒机、终端日志或手工摘要 | 不含密钥 |
| 变更单 | 内部工单 | 变更类必须 |
| 备份记录 | 客户备份系统或我方托管备份记录 | 变更类必须 |
| Smoke 结果 | 工单或复盘报告 | 必须 |
| 复盘报告 | 内部项目记录，客户版按需输出 | P0/P1 必须 |

## Stage Completion

- Stage: P3-05B 远程维护授权 SOP。
- What changed: 新增内部远程维护授权 SOP，覆盖 P0/P1/P2/P3 故障分级、诊断包优先、只读优先、变更二次授权、权限回收、只读命令白名单、禁止命令和故障复盘模板。
- What was verified: 已检查本文档命中 `P0`、`P1`、`P2`、`P3`、`诊断包优先`、`只读优先`、`变更二次授权`、`权限回收`、`只读命令白名单`、`禁止命令`、`故障复盘模板` 和 `客户确认`；`python3 scripts/check_p3_05_deployment_readiness.py` 通过；`docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.pilot.yml config --quiet` 通过。
- What remains not done: P3-05B readiness smoke、Lite 知识包模板、Lite 题库模板、工作台最终浏览器 QA、真实客户环境部署、真实官方渠道、真实外发和生产级 worker。
- Whether this was customer-visible: 间接是。它不会直接作为客户手册发出，但会支撑客户授权单、排障说明和故障复盘。
- Whether this was only evaluation: 否。本轮是运维交付能力建设。
- Next stage: P3-05B readiness smoke 脚本。
