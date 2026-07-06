# P3-06U-26H2M 月度质量复盘收束第一片

## 定位

本片补齐总控计划中“质量闭环还没真正收束”的第一层工程能力：系统不再只靠前端临时拼接质量看板，而是由后端生成可回溯的月度质量复盘包，再在质量复盘页展示。

本片仍不等于完整客服准确率验收。完整准确率必须继续依赖真实脱敏题库、人工事实性标签、知识修复、同题集回归和月度复盘结论。

## 已完成

- 新增只读接口：`GET /api/tenants/{tenant_id}/monthly-quality-review`
- 权限：需要 `quality.read`
- 后端聚合：
  - 本月题库规模
  - 最近评测运行
  - 同题集上一轮对比
  - 知识缺口新增、开放、解决、高风险数量
  - 人审新增、开放、高风险、低置信数量
  - 回复决策中的自动回复准备、转人工、知识缺口、策略阻断数量
- 前端质量页新增“本月复盘包”：
  - 核心指标
  - 主要问题
  - 下一步动作
  - 质量边界说明
- 新增浏览器 smoke：
  - `scripts/check_p3_06u_26h2m_monthly_quality_review_ui.mjs`
  - 证据目录：`output/p3_06u_26h2m_monthly_quality_review_ui/`

## 明确边界

- 不修改知识库。
- 不修改评测集。
- 不修改会话和人审任务。
- 不调用模型。
- 不写外部平台。
- 不打开真实外发。
- 不纳入渠道官方接入验收。
- 不导出客户原文、聊天原文、草稿全文、联系方式或密钥。

## 复盘包口径

当前接口返回：

- `schema_version=p3-06u-26h2m.monthly_quality_review.v1`
- `raw_text_included=false`
- `model_call_performed=false`
- `external_call_performed=false`
- `external_platform_write_performed=false`

核心判断：

- 题库少于 50 条：不能作为完整准确率依据。
- 没有人工事实性标签：不报告完整客服准确率。
- 检索命中率：只代表知识检索命中，不等同最终答案正确率。
- 引用覆盖率：只代表是否有可回溯依据，不等同话术可直接发送。
- 自动回复准备率：只代表策略判断可自动回复，不代表已经真实外发。

## 验证

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py -q
./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py

cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/frontend
npm run typecheck
npm run build

cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
node scripts/check_p3_06u_26h2m_monthly_quality_review_ui.mjs
```

## 仍未完成

- 真实客户 50-100 条脱敏题库仍需导入。
- 人工事实性标签仍未形成完整标注工作台。
- 知识修复后的同题集发布前后对比仍需继续加强。
- 生产级 RAG、向量检索、重排和引用充分性仍未完成生产验收。
- 高并发队列、真实告警和客户真实环境部署仍在后续阶段。

## 下一步

排除渠道正式接入验收后，建议继续推进：

1. 真实客户题库落地和人工事实性标签入口。
2. 知识修复后的发布前后自动对比。
3. 生产级 RAG/检索路线第一片。
4. 本地部署运维继续做真实恢复工具第二片或云端诊断接收台。
