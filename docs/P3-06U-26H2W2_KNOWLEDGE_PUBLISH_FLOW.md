# P3-06U-26H2W-2 客户知识发布流程第二片

本片继续 H2W-2 客户知识建设中心，目标是把“流程政策类知识”从导入后的草稿，推进到客户能理解、能操作、能追溯的发布流程。

## 本片完成内容

1. 知识库运营页新增 `客户知识发布流程`。
2. 发布流程拆成四步：选择草稿、发布前样题试跑、发布版本记录、安全边界。
3. 文档列表每份知识文档新增真实动作：
   - `发布前样题试跑`：调用 `POST /api/knowledge-documents/{document_id}/publish-checks`。
   - `确认发布版本`：调用 `POST /api/knowledge-documents/{document_id}/publication`。
   - `回滚为草稿`：继续使用已有回滚动作。
4. 发布前检查和正式发布都会刷新知识文档、发布历史和评测状态。
5. 页面明确展示：知识发布只影响本地 active 检索范围，不打开真实外发。

## 真实后端能力

- 发布前样题试跑会写入 `publish_check / passed|blocked` 记录。
- 正式发布会写入 `publish / published|blocked` 记录。
- 发布通过后，文档状态进入 `active`，文档分块进入 `active`。
- 发布失败时，阻断原因写入发布记录。
- 发布记录包含 checked case、case result、evaluation run、阻断项、文档快照和安全字段。
- 发布记录固定写入 `external_write_performed=false`、`model_call_performed=false`。

## 当前边界

- 本片不打开真实外发。
- 本片不调用模型。
- 本片不接真实微信、抖音、淘宝、京东或拼多多。
- 本片不是完整客服准确率验收。
- 本片的发布前样题试跑是知识文档检索、引用和必含词门禁，不等于真实客户全链路回复质量。
- 回滚当前只把文档退出 active 检索范围，不恢复旧正文；完整版本 diff 和内容级恢复仍属于后续阶段。

## 验收

- `python3 scripts/check_p3_06u_26h2w2_knowledge_publish_flow.py`
- `backend/.venv/bin/python -m py_compile scripts/check_p3_06u_26h2w2_knowledge_publish_flow.py scripts/smoke_p3_06u_26h2w2_knowledge_publish_flow_api.py`
- `python3 scripts/smoke_p3_06u_26h2w2_knowledge_publish_flow_api.py`
- `cd frontend && npm run build`

## 下一步

H2W-2 还可以继续补两块：

1. 把真实客户 50-100 条题库导入后，挂到客户知识发布流程里作为发布前样题池。
2. 把发布后命中率、转人工率、知识缺口变化接入 H2W-3 线上回执与准确率闭环。
