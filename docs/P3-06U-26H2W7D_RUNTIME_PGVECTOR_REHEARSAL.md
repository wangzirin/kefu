# H2W-7D-runtime PostgreSQL + pgvector 运行环境 rehearsal

## 结论

- 阶段状态：`ready_for_runtime_rehearsal`
- Docker daemon 可用：`true`
- Compose 声明 pgvector：`true`
- DATABASE_URL 指向 PostgreSQL：`false`
- KNOWLEDGE_VECTOR_STORE 为 pgvector：`false`
- 客户模板使用 pgvector：`true`
- pgvector ANN runtime smoke：`true`
- 7D 静态证据 ready：`true`
- 内部 100 题 ready：`true`
- 可进入 pgvector runtime rehearsal：`true`

## 停止门禁

- 没有 Docker daemon 或外部 PostgreSQL + pgvector 运行环境时，不写生产级检索完成。
- 非 PostgreSQL 环境必须 fail-closed，不能回退到 SQLite/JSON 还写成 pgvector。
- 内部 100 题可用于工程 rehearsal，但不能写成真实客户题库。
- 本阶段不调用付费 embedding，不切换真实生产查询路径。

## 阻断项

- 无

## 输出

- `output/p3_06u_26h2w7d_runtime_pgvector_rehearsal/summary.json`
- `output/p3_06u_26h2w7d_runtime_pgvector_rehearsal/pgvector_ann_smoke.json`

## 边界

- `production_retrieval_path_switched=false`
- `paid_embedding_call_performed=false`
- `external_platform_write_performed=false`
- `formal_accuracy_signoff_performed=false`
