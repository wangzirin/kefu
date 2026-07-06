# P3-06L RBAC 第五片：知识库业务动作权限

日期：2026-07-01  
范围：知识卡片、知识文档、文档分块、检索、发布检查、发布、回滚、知识缺口、评测、向量索引和 embedding provider smoke  
状态：第五片完成

## Engineering Control Card

- Stage: P3-06L RBAC 第五片
- 当前主线阶段: 后端资源级 RBAC 收口
- 上一阶段真正完成: P3-06K 已把会话读写动作迁到 `conversation.read` / `conversation.manage`
- 上一阶段明确没有完成: 知识、渠道、工单、客户、线索权限迁移；前端按钮级权限；字段脱敏
- 本轮要交付的客户可见价值: 坐席可以继续检索知识，但不能直接改知识库、发布文档、回滚、补缺口或触发 provider smoke；viewer 不能读取知识原文
- 本轮是否只是评测: 否
- 本轮不做什么: 不改数据库结构、不改前端页面、不接真实外部 provider、不改变知识发布门禁业务逻辑、不迁移工单/客户/渠道权限
- 外部风险: 无真实外发；embedding provider smoke 仍由原有 allow_external_call 门禁控制
- 需要用户授权的动作: 无
- 验证方式: 知识 RBAC 后端测试、知识相关业务回归、静态 readiness 检查、后端全量测试、前端构建
- 写回文件: 产品化总控手册、Superpowers P3 计划、Workspace Project_012 记录
- 下一阶段: RBAC 第六片，优先迁移工单、联系人、线索和渠道配置权限，或先做前端按钮级权限

## 1. 权限矩阵

| 权限 | owner | admin | agent | viewer |
| --- | --- | --- | --- | --- |
| `knowledge.read` | 允许 | 允许 | 允许 | 禁止 |
| `knowledge.manage` | 允许 | 允许 | 禁止 | 禁止 |

口径：

- `knowledge.read` 用于知识检索、知识卡片列表、知识文档列表、文档分块读取、文档检索。
- `knowledge.manage` 用于写入、发布、回滚、知识缺口处理、评测、索引和 provider smoke。
- viewer 当前不能读取知识原文，因为还没有完成租户级知识公开范围、字段脱敏和导出限制。

## 2. 已迁移接口

| 接口类别 | 权限 |
| --- | --- |
| `GET /api/tenants/{tenant_id}/knowledge-cards` | `knowledge.read` |
| `POST /api/tenants/{tenant_id}/knowledge-searches` | `knowledge.read` |
| `GET /api/tenants/{tenant_id}/knowledge-documents` | `knowledge.read` |
| `GET /api/knowledge-documents/{document_id}/chunks` | `knowledge.read` |
| `POST /api/tenants/{tenant_id}/knowledge-document-searches` | `knowledge.read` |
| 知识卡片创建/更新 | `knowledge.manage` |
| 知识文档创建 | `knowledge.manage` |
| 发布检查、发布、发布历史、回滚 | `knowledge.manage` |
| 向量索引 rebuild/plan | `knowledge.manage` |
| embedding provider smoke | `knowledge.manage` |
| 评测集、评测运行、报告导出 | `knowledge.manage` |
| 知识缺口列表、同步、更新、草稿生成、回归题生成 | `knowledge.manage` |

## 3. 业务边界

本轮只把 API 入口迁到命名权限，不改变原有服务层的租户隔离、发布门禁、回归题检查和 provider smoke 门禁。

保留的关键边界：

- 跨租户知识资源继续返回 404。
- 坐席只能检索知识，不能新增、更新、发布、回滚或跑评测。
- 知识缺口暂定为知识管理员能力，不给普通坐席直接操作。
- 外部 embedding provider smoke 仍必须显式允许外部调用，不因权限迁移自动触发真实 provider。

## 4. 验收结果

- `backend/tests/test_p3_06l_knowledge_rbac.py` 覆盖权限矩阵、owner/admin manage、agent read-only、viewer blocked 和跨租户 404。
- 知识卡片、知识文档、知识缺口、评测、向量索引、provider smoke 相关回归测试已通过。
- `scripts/check_p3_06l_knowledge_rbac.py` 用于静态检查 RBAC、API、测试和文档是否保持一致。

## 5. 后续建议

1. RBAC 第六片：迁移工单、联系人、线索权限。
2. RBAC 第七片：迁移渠道配置、连接器配置、回执读取和 send plan 权限。
3. 前端权限片：用 `user.permissions` 控制知识发布、回滚、缺口同步、评测运行、provider smoke 等按钮。
4. 字段脱敏片：为 viewer/agent/admin 分层处理客户资料、知识导出、评测报告和原始问答文本。
