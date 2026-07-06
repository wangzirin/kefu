# H2W-7D 生产级检索与引用证据

## 结论

- 阶段状态：`blocked_waiting_for_real_bank_or_postgres`
- pgvector 代码路径：`true`
- ANN 索引策略：`true`
- 非 PostgreSQL fail-closed：`true`
- 真实题库可用于评测：`false`
- PostgreSQL 运行环境：`false`
- 可切生产检索路径：`false`

## 策略规则

- 小于 10,000 chunks：优先 exact scan，保证召回可解释。
- 10,000 到 500,000 chunks：优先 HNSW，召回/延迟折中较稳。
- 大于 500,000 chunks 或内存敏感：可选 IVFFlat，但必须与 exact scan 做召回对照。
- 所有 ANN 索引必须有构建窗口、回滚 SQL 和失败降级。
- 引用必须保留 chunk、version/hash/source_uri，不能只有文档名。

## 阻断项

- H2W-11O 真实 50-100 条脱敏题库尚未 ready，不能做生产检索评测
- 当前未检测到 PostgreSQL + pgvector 生产候选运行环境

## 输出

- `/private/var/folders/cv/nv4r5wsj1sl83z83j23cggb40000gn/T/pytest-of-ericlee/pytest-505/test_h2w7d_requires_real_bank_0/summary.json`

## 边界

- 本阶段不把 SQLite/JSON 检索包装成生产向量库。
- 没有真实题库评测，不切换生产检索路径。
- 外部 embedding 或 reranker 未记录价格、版本和降级时，不进入生产候选。
- 本阶段不调用付费模型，除非后续单独授权。
