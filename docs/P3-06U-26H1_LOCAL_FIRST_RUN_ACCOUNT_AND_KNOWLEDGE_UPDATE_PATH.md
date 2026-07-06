# P3-06U-26H1 本地首次启动账号与知识更新路径

## Engineering Control Card

- Stage: P3-06U-26H1
- 当前主线阶段: 小微企业本地化使用收束
- 上一阶段真正完成: RPA 实验入口从中台下线；知识缺口筛选改为服务端；知识三页保留但减重
- 上一阶段明确没有完成: 完整本地首次启动账号、诊断包上传、签名更新包、真实平台外发
- 本轮要交付的客户可见价值: 第一次本地运行时可创建管理员账号；知识运营页能清楚说明并执行新增业务对象、绑定问答卡、导入知识文档
- 本轮是否只是评测: 否
- 如果是评测，本轮问题是什么: 不适用
- 如果是评测，停止条件是什么: 不适用
- 本轮不做什么: 不开启真实外发；不做诊断包上传；不做复杂多角色管理；不把本地初始化数据写成真实平台接通
- 外部风险: 无真实平台写入；本轮只操作本地数据库和本地前端
- 需要用户授权的动作: 无
- 验证方式: 后端 pytest、前端 typecheck/build、专项静态检查、必要时浏览器 smoke
- 写回文件: 本文档、执行记录、文件索引、复盘与采坑
- 下一阶段: P3-06U-26H2 诊断包生成或继续知识运营真实导入体验打磨

## 本轮判断

“新增业务对象”之前看起来不能点，不是后端没有接口，而是当前页面常用的是无 token 的本地查看态。业务对象、对象问答卡、知识文档导入三个后端接口已经存在，但前端在没有登录令牌或没有 `knowledge.manage` 权限时会禁用写入按钮。

二次验收时还发现一个更实际的问题：历史本地 SQLite 库曾由旧阶段脚本生成，`business_objects`、`object_knowledge_cards` 等后续表没有落到当前库里。前端按钮即使启用，也会因为后端缺表而无法完成写入。本轮新增本地库结构修复脚本，只用于本地开发/试点库，不作为生产迁移方式。

本轮把入口改为正式本地产品逻辑：

1. 本地库没有任何账号时，登录页可以创建第一个管理员。
2. 创建后系统生成本地租户、基础角色和负责人账号。
3. 创建成功后返回真实登录令牌，进入中台。
4. 进入知识库运营页后，新增业务对象、绑定对象问答卡、导入知识文档自然可用。

## 本地首次启动账号

新增后端接口：

| 接口 | 用途 | 约束 |
| --- | --- | --- |
| `GET /api/auth/local-setup/status` | 检查本地库是否已经初始化 | 不暴露密码和密钥，只返回租户数、用户数和第一个租户标识 |
| `POST /api/auth/local-setup/owner` | 创建第一个本地管理员并登录 | 只有全库没有任何用户时允许创建，之后再次调用返回 `409` |

首次创建会生成：

- 一个本地租户。
- `owner/admin/agent/viewer` 四个基础角色。
- 一个负责人账号。
- 一条登录 session。

密码由使用者第一次设置，系统不预置默认密码。

已初始化过的本地库不会再次开放“创建第一个管理员”。本轮验收库额外保留一个本地验收账号，方便重复跑端到端 smoke；正式交付时应由客户首次启动自行创建管理员账号。

如果本地库已经初始化但忘记管理员密码，不在网页端提供无身份重置入口。处理方式是在本机执行重置脚本，由本机操作者设置新密码：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
PYTHONPATH=backend backend/.venv/bin/python scripts/reset_local_admin_password.py \
  --tenant-slug wanfa-local-dev \
  --email real-test@wanfa.local \
  --name 本地管理员
```

不传 `--password` 时，脚本会在终端里隐藏输入新密码，避免把密码写入命令历史、文档或聊天记录。

## 知识更新路径

知识库不是只导入一段文本。小微企业的可维护路径应分成四步：

| 步骤 | 页面动作 | 写入后端 | 作用 |
| --- | --- | --- | --- |
| 1 | 新增业务对象 | `POST /api/tenants/{tenant_id}/business-objects` | 建商品、服务、套餐、课程、门店等对象 |
| 2 | 绑定标准问答 | `POST /api/business-objects/{id}/knowledge-cards` | 把客户会怎么问、标准答案、触发关键词挂到对象上 |
| 3 | 导入知识文档 | `POST /api/tenants/{tenant_id}/knowledge-documents` | 把价格、售后、合同、禁用承诺等长文本进入文档检索 |
| 4 | 检索与回归 | `POST /api/tenants/{tenant_id}/knowledge-document-searches` 和评测接口 | 检查引用、事实性和是否应该转人工 |

这条路径已经在知识库运营页顶部以四步形式展示，并给三个写入口加入可验收标识：

- `data-knowledge-action="create-business-object"`
- `data-knowledge-action="create-object-card"`
- `data-knowledge-action="import-document"`

## 前后端对齐结论

| 功能 | 前端状态 | 后端状态 | 本轮结论 |
| --- | --- | --- | --- |
| 本地首次启动账号 | 已新增创建管理员入口 | 已新增 setup status/owner 接口 | 对齐 |
| 登录后读取知识库 | 已有 token 后刷新知识资源 | 已有知识文档、业务对象、问答卡接口 | 对齐 |
| 新增业务对象 | 登录且有 `knowledge.manage` 才可点 | 已有创建接口 | 对齐 |
| 绑定对象问答卡 | 需要先有业务对象 | 已有对象问答卡接口 | 对齐 |
| 导入知识文档 | 需要标题和正文 | 已有导入、分块、索引状态 | 对齐 |
| 未登录写入 | 显示登录原因，不写数据 | 后端需要 token 和权限 | 对齐 |

## 本地库结构修复

当本地库来自旧脚本、旧种子数据或历史阶段快照时，可能出现“页面有入口，接口代码存在，但 SQLite 缺新表”的情况。处理方式：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
backend/.venv/bin/python scripts/repair_local_sqlite_schema.py
```

脚本行为：

- 读取当前模型定义，只创建缺失表，不删除业务数据。
- 校验 `business_objects`、`business_object_aliases`、`object_knowledge_cards`、`knowledge_import_batches`、`reply_decisions`、`channel_accounts`。
- 本地库修复完成后把 `alembic_version` 标记到当前单一 head，避免同一份本地库继续显示迁移状态混乱。

正式部署仍然使用 Alembic 迁移；这个脚本只用于本机开发库和试点演示库。

## 知识写入冒烟

新增接口级 smoke：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
STANDARD_OPS_SMOKE_PASSWORD='本机临时密码' python3 scripts/smoke_p3_06u_26h1_knowledge_write_path.py
```

该脚本会：

1. 使用本地验收账号登录。
2. 调用 `POST /api/tenants/{tenant_id}/business-objects` 新增业务对象。
3. 调用 `POST /api/business-objects/{id}/knowledge-cards` 绑定对象问答卡。
4. 调用 `POST /api/tenants/{tenant_id}/knowledge-documents` 导入知识文档。
5. 重新查询列表确认三类数据都能回显。

脚本不打印 access token，只打印对象 ID、文档 ID 和状态。

## 仍未完成

- 没有做诊断包生成和上传。
- 没有做签名更新包导入。
- 没有开启真实平台外发。
- 没有接入真实客户知识包。
- 没有把知识评测升级成完整客服最终答案准确率。

## 验收命令

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
backend/.venv/bin/python scripts/repair_local_sqlite_schema.py
python3 scripts/check_p3_06u_26h1_local_setup_and_knowledge_entry.py
STANDARD_OPS_SMOKE_PASSWORD='本机临时密码' python3 scripts/smoke_p3_06u_26h1_knowledge_write_path.py
cd backend && .venv/bin/python -m pytest tests/test_local_setup_api.py tests/test_knowledge_gaps_api.py
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

浏览器验收补充：本轮使用 Chrome 打开 `http://127.0.0.1:5182/` 能看到正式登录页；自动化点击阶段被当前 Chrome 扩展浮层阻断，因此本轮以接口级 smoke、前端构建和静态标识检查作为可重复验收依据。
