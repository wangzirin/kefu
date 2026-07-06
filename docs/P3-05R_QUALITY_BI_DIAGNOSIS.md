# P3-05R 质量诊断 BI 第一片

日期：2026-07-01  
阶段：P3-05R  
范围：前端质量工作区重构  
结论：质量页已经从“指标口径说明”升级为可扫读的错因 BI 工作区，但仍不代表已经完成真实客户准确率认证。

## Engineering Control Card

- Stage: P3-05R 质量诊断 BI 第一片。
- 当前主线阶段: 标准运营版客服中台产品化。
- 上一阶段真正完成: P3-05Q 已把对话台升级为坐席主工作区，包含队列、事件时间线、AI 草稿、知识证据和右侧检查器。
- 上一阶段明确没有完成: 真实外发、高并发、完整聊天历史 API、server-side queue counts、质量 BI。
- 本轮要交付的客户可见价值: 运营负责人可以在质量页看到主要错因、漏斗、渠道异常、知识缺口、人审矩阵和样本下钻，知道下一步该修知识、修渠道、补人审还是跑回归题。
- 本轮是否只是评测: 否。本轮是质量运营工作区建设。
- 如果是评测，本轮问题是什么: 不适用。
- 如果是评测，停止条件是什么: 不适用。
- 本轮不做什么: 不新增后端聚合接口；不新增真实投诉事件源；不做人工事实性标签；不宣称完整准确率；不打开真实平台外发。
- 外部风险: 无真实外部写入；无模型付费调用；无真实客户数据导出。
- 需要用户授权的动作: 无。
- 验证方式: `npm run build`、本地前后端健康检查、Playwright 桌面/移动端页面结构和横向溢出检查、截图目视检查。
- 写回文件: 本文档、Project_012 执行记录、关键决策、文件索引、复盘与采坑。
- 下一阶段: P3-05S 知识审核发布与回归门禁，或 P3-06A 生产并发底座。

## 本轮改了什么

### 1. 顶部诊断摘要

新增 4 个质量诊断摘要：

| 摘要 | 作用 |
|---|---|
| 主要错因 | 当前最需要优先处理的问题类型 |
| 题库趋势 | 最近题库命中率和历史对比状态 |
| 修复队列 | 需要生成草稿或加入回归的知识缺口 |
| 准确率口径 | 明确当前缺人工事实性标签，不能报完整准确率 |

### 2. 错因排行

把质量问题聚合为 6 类：

- 知识没有覆盖。
- 回答置信不足。
- 高风险需人工。
- 渠道或外发异常。
- 草稿卡在待发。
- 分配和时效风险。

每个错因都带数量、说明、修复动作和下钻入口。

### 3. 质量漏斗

新增从入站到失败复盘的漏斗：

```text
入站会话 -> 进入人审 -> 可用草稿 -> 待发送确认 -> 队列检查 -> 失败复盘
```

这能帮助判断问题卡在 AI、人工审核、待发送还是渠道执行层。

### 4. 题库趋势

用最近评测运行摘要展示命中趋势。当前如果没有同题集上一轮对比，会明确显示“待建立”，不把单次命中率包装成准确率。

### 5. 渠道异常分布

按渠道展示会话、人审、异常和超时信号。当前仍使用演示渠道和内部回执数据，不代表真实平台已经接通。

### 6. 知识缺口热力图

按来源和状态展示知识缺口：

- 人审缺口。
- 评测缺口。
- 手动缺口。

状态包括待处理、已分诊、处理中、已解决。这个视图用于观察补知识是否真的被推进。

### 7. 人审矩阵

按风险等级和证据质量交叉统计：

- 无知识。
- 弱证据。
- 可核对。

这比只看“转人工率”更有价值，因为它能判断转人工到底是知识缺口、风险问题还是证据弱。

### 8. 样本下钻和修复动作

质量页新增样本卡片，来源包括：

- 人审任务。
- 知识缺口。
- 渠道失败复盘。
- 评测失败样本。

样本卡直接指向审核、缺口、渠道和评测页面，底部也提供修复动作入口。

## 文件改动

- `frontend/src/App.tsx`
  - 新增 `QualityIssueBreakdown`、`QualityFunnelStep`、`QualityDrillSample`。
  - 重构 `QualityReviewPanel`，新增错因排行、质量漏斗、题库趋势、渠道异常、知识缺口热力、人审矩阵、样本下钻和修复动作。
  - 顶部工作区标题从“质量复盘”改为“质量诊断”。
- `frontend/src/styles.css`
  - 新增质量 BI 卡片、Pareto、漏斗、趋势、渠道堆叠、热力图、矩阵、样本卡和修复动作样式。
  - 补充移动端单列布局，避免 390px 横向溢出。
- `frontend/src/data/navigation.ts`
  - 阶段标识更新为 `P3-05R`。
  - 质量入口标记为 `BI`。

## 验证结果

### 构建

已运行：

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/frontend
npm run build
```

结果：

- `tsc` 通过。
- `vite build` 通过。

### 服务健康

已检查：

```bash
curl -I http://127.0.0.1:5175
curl http://127.0.0.1:8081/health
```

结果：

- 前端返回 200。
- 后端返回 `{"status":"ok","service":"standard_ops_backend","environment":"development"}`。

### 浏览器检查

Playwright 来自 Codex bundled runtime：

```text
/Users/ericlee/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules
```

桌面 1440x1000：

- `qualityExists=true`
- `navStageVisible=true`
- `topTitle=质量诊断`
- `commandCards=4`
- `paretoRows=6`
- `funnelSteps=6`
- `channelRows=6`
- `heatmapRows=3`
- `matrixRows=4`
- `sampleCards=8`
- `repairLinks=5`
- `overflowX=false`
- `consoleIssueCount=0`

移动端 390x1200：

- `qualityExists=true`
- `navStageVisible=true`
- `commandCards=4`
- `paretoRows=6`
- `funnelSteps=6`
- `sampleCards=8`
- `overflowX=false`
- `consoleIssueCount=0`

截图：

```text
/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/output/p3_05r_quality_bi/p3_05r_quality_bi_desktop.png
/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/output/p3_05r_quality_bi/p3_05r_quality_bi_mobile.png
```

## 当前仍不能承诺

- 不能承诺完整 AI 准确率已经可报。
- 不能承诺已有人工事实性标签。
- 不能承诺真实客户 50-100 条题库已经验收。
- 不能承诺真实投诉率、满意度或差评事件已经接入。
- 不能承诺图表是后端生产级历史聚合；当前第一片复用已加载的工作台数据和演示数据。
- 不能承诺真实渠道外发、高并发或生产 worker 已完成。

## 下一步

推荐进入 P3-05S：知识审核发布与回归门禁。

P3-05S 应至少包含：

1. 草稿知识详情页。
2. 草稿审核、发布、驳回、失效。
3. 发布前强制关联回归题。
4. 发布后回归运行结果关联到缺口。
5. 知识版本回滚边界。
6. 普通坐席脱敏查看缺口，owner/admin 执行发布。

