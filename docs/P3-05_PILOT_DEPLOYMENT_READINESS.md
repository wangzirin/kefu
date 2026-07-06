# P3-05A 试点部署准备

更新时间：2026-06-29  
适用范围：Lite 试点版、标准运营版首个受控试点  
阶段定位：把当前标准运营版从“本机可验证”推进到“可由交付工程师按清单安装、检查、诊断和恢复”的状态。

## Engineering Control Card

| 项目 | 本轮口径 |
| --- | --- |
| Stage | P3-05A 试点部署准备 |
| 当前主线阶段 | P3-05 交付与部署试点包 |
| 上一阶段真正完成 | P3-04 官网客服沙盒 Copilot 闭环：HMAC 入站、可信消息、幂等、AI 建议、人审、outbox、发送门禁、前端沙盒面板、桌面和移动端截图 QA |
| 上一阶段明确没有完成 | 真实企业微信、公众号、抖音、小红书、淘宝、京东、拼多多接入；真实外发；生产队列；客户真实 50-100 题；人工事实性标签；真实模型批量质量验收 |
| 本轮要交付的客户可见价值 | 交付团队可以按清单部署试点环境，客户侧可获得清晰的安装边界、运维方式、故障处理和资料包 |
| 本轮是否只是评测 | 否。自检只作为部署准备门禁 |
| 本轮不做什么 | 不打开真实外发，不导入真实客户数据，不调用付费模型批量评测，不直接接入未授权平台，不承诺全平台上线 |
| 外部风险 | 生产密钥、真实平台账号、真实客户资料、付费模型调用、客户生产数据库、远程维护权限 |
| 需要用户授权的动作 | 真实模型调用、真实渠道回调域名和密钥配置、生产数据库迁移、对客户环境远程登录、真实外发 |
| 验证方式 | 文件自检、环境变量清单、Docker Compose 配置校验、一次性数据库迁移 smoke、诊断包生成、文档渲染检查 |
| 写回文件 | Project_012 执行记录、关键决策、文件索引、复盘与采坑、Superpowers 计划 |
| 下一阶段 | Lite 试点版封版或继续补 P3-05B 试点部署 smoke |

## 1. 当前部署对象

本阶段部署对象是 `standard_ops/` 标准运营版工程目录。它已经具备：

| 板块 | 已具备能力 | 试点部署时的边界 |
| --- | --- | --- |
| 后端 | FastAPI、SQLAlchemy、Alembic、账号、租户、会话、知识库、模型路由、审核、outbox、渠道沙盒 | 仍需按客户环境配置数据库、模型、域名和渠道授权 |
| 前端 | React/Vite 工作台、登录、人审、知识评测、官网 Copilot 沙盒、P3-03/P3-04 主屏 | 仍不是完整 CRM/SLA/工单系统 |
| 数据库 | PostgreSQL 目标路径，本地可用 SQLite 做部分 smoke，已有 Alembic 迁移 0001-0016 | 生产迁移必须先备份并在试点库执行 |
| 队列 | 已有发送队列和 worker 骨架 | 当前不是完整 Redis/RQ/Celery 独立生产消费者 |
| 知识库 | 知识卡片、文档、chunk、引用、评测、脱敏报告 | 仍需客户真实知识资料和人工审核 |
| 模型 | 百炼、DeepSeek 和 deterministic provider 边界；百炼 smoke 已跑通过小样本 | 批量调用必须显式授权和限量 |
| 渠道 | 官网 sandbox、connector、webhook、验签、outbox、回执、失败复盘骨架 | 真实官方平台接入需单独授权和平台配置 |

## 2. 环境变量清单

试点环境必须从 `.env.example` 复制为 `.env`，再按客户环境修改。禁止把真实密钥写回 `.env.example`、README、阶段文档或聊天记录。

| 类型 | 变量 | 试点要求 |
| --- | --- | --- |
| 应用 | `STANDARD_OPS_ENV` | 试点建议使用 `pilot` 或 `staging`，不要混用 `production` |
| 应用 | `STANDARD_OPS_ALLOWED_ORIGINS` | 只填客户正式访问域名和本地调试域名 |
| 数据库 | `DATABASE_URL` | 试点优先 PostgreSQL；迁移前必须备份 |
| Redis | `REDIS_URL` | 用于后续队列、缓存和限流；当前仍以 smoke 为主 |
| 管理员 | `ADMIN_BOOTSTRAP_EMAIL` | 改为客户管理员邮箱或交付临时账号 |
| 管理员 | `ADMIN_BOOTSTRAP_PASSWORD` | 必须替换默认值，首次交付后要求客户修改 |
| 百炼 | `BAILIAN_API_BASE` | 使用百炼兼容模式地址，客户有专属工作空间时按实际地址配置 |
| 百炼 | `BAILIAN_API_KEY` | 只放客户授权的真实 key；不写入任何长期文档 |
| 百炼 | `BAILIAN_MODEL` / `BAILIAN_*_MODEL` | 先按标准模型跑小样本，再决定是否开高阶模型 |
| DeepSeek | `DEEPSEEK_API_KEY` | 可作为备用 provider；未配置时不应被说成可用 |
| Embedding | `KNOWLEDGE_EMBEDDING_PROVIDER` | 默认 `deterministic_local`；真实 embedding 需要单独 smoke |
| 向量库 | `KNOWLEDGE_VECTOR_STORE` | SQLite 本地演示可用 JSON vector；正式路径优先 PostgreSQL + pgvector |
| 外发 | `OUTBOX_EXTERNAL_WRITE_ENABLED` | 试点默认必须是 `false` |
| 企业微信 | `WECOM_*` | 只有拿到官方授权测试号后填写；不使用个人微信外挂 |

## 3. 试点部署步骤

### 3.1 准备环境

1. 确认客户环境可以运行 Docker Desktop、Docker Engine 或等价容器环境。
2. 确认端口 `5173`、`18080`、`5432`、`6379` 没有被其他服务占用，或在 `deploy/docker-compose.yml` 中调整映射。
3. 从 `.env.example` 复制 `.env`，替换管理员密码、数据库密码、模型 key 和允许访问域名。
4. 保留 `OUTBOX_EXTERNAL_WRITE_ENABLED=false`，直到双方完成外发审批。

### 3.2 启动服务

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/deploy
docker compose up --build
```

启动后检查：

| 检查项 | 预期 |
| --- | --- |
| 前端 | `http://127.0.0.1:5173` 可以打开登录页 |
| 后端 | `http://127.0.0.1:18080/health` 返回 `status=ok` |
| PostgreSQL | 容器健康检查为 healthy |
| Redis | 容器健康检查为 healthy |
| 外发 | 日志和配置均显示真实外发关闭 |

### 3.3 数据库迁移

试点库迁移前必须先备份。空库迁移命令：

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/backend
DATABASE_URL=postgresql+psycopg://wanfa_ops:wanfa_ops_password@127.0.0.1:5432/wanfa_ops .venv/bin/alembic upgrade head
```

如果只做本地一次性 smoke，可以使用 disposable SQLite 路径；这只能证明迁移脚本没有基础语法问题，不能替代 PostgreSQL 验收。

## 4. 备份与恢复

### 4.1 备份对象

| 对象 | 内容 | 建议频率 |
| --- | --- | --- |
| 数据库 | 租户、账号、会话、消息、知识库、审核、outbox、审计、评测运行 | 试点每日一次；正式运营按客户要求加密留存 |
| 环境配置 | `.env` 中的变量名和客户侧安全保存的真实值 | 每次变更后保存 |
| 知识资料 | 原始知识文件、知识卡片版本、题库 CSV/JSON | 每次发布前后保存 |
| 输出报告 | 脱敏质量报告、诊断包、部署记录 | 每次交付节点保存 |

### 4.2 PostgreSQL 备份示例

```bash
docker compose exec postgres pg_dump -U wanfa_ops -d wanfa_ops -Fc -f /tmp/wanfa_ops_$(date +%Y%m%d_%H%M%S).dump
docker compose cp postgres:/tmp/wanfa_ops_YYYYMMDD_HHMMSS.dump ./backups/
```

### 4.3 PostgreSQL 恢复示例

恢复只能指向一次性演练库或经客户明确确认的目标库：

```bash
createdb wanfa_ops_restore_drill
pg_restore -U wanfa_ops -d wanfa_ops_restore_drill --clean --if-exists ./backups/wanfa_ops_YYYYMMDD_HHMMSS.dump
```

恢复演练必须记录：

- 演练时间。
- 备份文件名和校验值。
- 恢复目标库。
- 迁移版本。
- 抽查表和抽查结果。
- 是否删除一次性演练库。

## 5. 诊断包

诊断包用于远程维护前的只读排查，不应包含 `.env` 明文、API key、客户聊天原文、客户手机号、订单号或真实平台 token。

本阶段新增诊断脚本：

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python scripts/create_p3_05_diagnostic_bundle.py
```

诊断包应包含：

| 内容 | 说明 |
| --- | --- |
| 项目文件状态 | 关键文件是否存在、大小、hash |
| 环境模板摘要 | `.env.example` 的变量名和安全默认值检查，不读取 `.env` 明文 |
| Compose 摘要 | 服务名、端口、镜像或构建上下文 |
| 迁移摘要 | Alembic revision 列表 |
| 文档摘要 | P3-05、客户资料包、内部运维计划是否存在 |
| 安全检查 | 外发默认关闭、密钥字段为空、未发现常见 secret 片段 |

## 6. 远程维护方式

正式客户环境不默认开放公网 SSH/RDP。推荐顺序：

| 方式 | 适用场景 | 要求 |
| --- | --- | --- |
| 客户侧 VPN / 零信任访问 | 长期维护客户私有化部署 | 客户授权、账号实名、最小权限、操作审计 |
| 堡垒机 | 中大型客户 | 工单审批、录像、命令审计、过期账号回收 |
| 临时隧道 | 短时排障 | 明确时间窗口、只读优先、结束后关闭 |
| 诊断包 | 无法远程登录或客户安全要求高 | 只读、脱敏、不含密钥和聊天原文 |

不得采用：

- 长期保存客户生产服务器密码。
- 把公网 SSH/RDP 直接暴露给服务方。
- 通过个人微信、个人网盘传输密钥和数据库备份。
- 在未经客户确认的情况下修改生产配置或执行迁移。

## 7. 知识库更新流程

| 步骤 | 操作 | 验收 |
| --- | --- | --- |
| 资料确认 | 客户确认产品、价格、售后、合同、发票和禁用话术 | 有负责人和生效时间 |
| 内容整理 | 转成知识卡片或文档 | 有来源、版本和适用范围 |
| 导入系统 | 管理员导入，生成 chunk 和引用 | 可以检索到来源 |
| 题库回归 | 使用 50-100 条脱敏题或客户式题库跑回归 | 记录命中、引用、转人工和缺口 |
| 人工抽查 | 业务负责人抽查高风险和高频问题 | 通过后发布 |
| 发布记录 | 记录版本、变更点、时间和回滚方式 | 可追溯 |

知识库不要无记录覆盖旧版本。价格、售后、合同、赔付、合规类内容必须保留版本。

## 8. 准确率下降监控

准确率下降是长期运营中的正常风险，不应等客户投诉后才排查。

| 指标 | 预警含义 |
| --- | --- |
| 题库回归下降 | 新知识或检索策略让旧问题变差 |
| 引用支撑率下降 | 草稿引用不足或证据不匹配 |
| 转人工率异常升高 | 知识缺口、模型不可用或规则过严 |
| 坐席改写率升高 | 草稿口径、语气或事实支撑不足 |
| 知识缺口增加 | 新业务、新活动或新渠道问题涌入 |
| Provider 失败率升高 | 模型服务、网络或 key 配额异常 |
| 发送失败增加 | 渠道权限、外发开关或平台回执异常 |

处理顺序：

1. 查最近知识库版本。
2. 查最近模型/provider 配置。
3. 查最近渠道来源变化。
4. 抽查低分和高改写会话。
5. 补知识库或调整禁用话术。
6. 小样本跑题库回归。
7. 通过后发布，并记录复盘结论。

## 9. 外发与渠道边界

正式试点默认只做 Copilot，即“AI 生成草稿、人工审核、发送前确认”。真实自动外发必须另行审批。

不进入正式交付方案的路径：

- 个人微信外挂。
- Hook。
- 群控。
- 模拟点击。
- 商家后台 RPA 代发。
- 未经平台授权的抓取或代发。

可进入正式方案的路径：

- 官网自有入口。
- 企业微信官方 API 或测试号。
- 公众号官方接口。
- 电商和内容平台开放平台、服务商授权或官方客服接口。

## 10. P3-05A 完成标准

| 项目 | 状态 |
| --- | --- |
| P3-05 部署准备文档 | 本文档完成 |
| 环境变量清单 | 已整理，仍需客户真实值 |
| Compose 配置 | 已存在，需试点环境运行 smoke |
| 迁移路径 | 已有 Alembic，需试点 PostgreSQL 空库迁移 |
| 诊断包脚本 | 已新增，默认不读取 `.env` 明文 |
| 客户资料包 | 产品介绍、服务体系、使用手册进入正式 DOCX 制作 |
| 内部运维计划 | 已有 Markdown，后续可转内部 SOP 文档 |
| 外发安全边界 | 默认关闭，真实外发另行授权 |

## 11. 当前不能对外承诺

- 不能承诺已经接通所有平台。
- 不能承诺默认自动外发。
- 不能承诺没有人工审核也能安全运营。
- 不能承诺已经完成客户真实 50-100 题验收。
- 不能承诺真实模型批量质量已验收。
- 不能承诺当前队列已经是高并发生产消费者。
- 不能承诺未授权平台可以通过外挂方式接入。
- 不能承诺 100% 准确率或永不需要人工。

## Stage Completion

- Stage: P3-05A 试点部署准备。
- What changed: 新增 P3-05A 部署准备文档、诊断包入口、自检入口和客户资料 DOCX 制作任务。
- What was verified: `scripts/check_p3_05_deployment_readiness.py` 通过；诊断包生成且不读取 `.env` 明文；Docker Compose 配置校验通过；一次性 SQLite 迁移 smoke 跑到 Alembic head；三份正式对外 DOCX 成功渲染成 PNG 并完成视觉检查和词汇扫描。
- What remains not done: 真实客户环境部署、真实 PostgreSQL 备份恢复演练、真实官方渠道接入、真实外发、真实客户题库和人工事实性标签。
- Whether this was customer-visible: 是。部署准备和客户资料包会直接影响试点交付。
- Whether this was only evaluation: 否。
- Next stage: P3-05B 试点部署 smoke 或 Lite 试点版封版。
