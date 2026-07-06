# P3-06U-26H2W3D 线上回执与准确率闭环第一片

日期：2026-07-03

## 1. 阶段目标

本阶段只完成“线上回执闭环”的第一层可观测能力。

目标不是宣布完整客服准确率已经成立，而是先把以下问题变成可读、可验、可继续接真实渠道的内部能力：

- 平台回执有没有进入系统。
- 回执是否能匹配到本系统发出的发送尝试。
- 回执是否经过官方签名或 AES 验证。
- 送达、已读、失败、限流、授权异常、内容拒绝等状态是否被归一。
- 失败回执是否进入失败复盘。
- 质量复盘页是否明确区分“回执链路覆盖”和“完整客服答案准确率”。

## 2. 本次完成

### 2.1 后端

新增服务端汇总能力：

```text
GET /api/tenants/{tenant_id}/online-receipt-quality-summary
```

返回结构版本：

```text
p3-06u-26h2w3d.online_receipt_quality.v1
```

汇总范围：

- `channel_delivery_receipts`
- `delivery_failure_reviews`
- 回执匹配字段 `matched_attempt_id`
- 回执签名验证字段 `signature_validated` / `verification_status`
- 归一状态字段 `normalized_status`

该接口不返回 `raw_payload`，只返回统计和门禁状态。

### 2.2 前端

质量诊断页新增“线上回执闭环证据”区域：

- 回执总数
- 送达率
- 匹配率
- 签名验证率
- 打开的失败复盘数量
- 平台回执分布
- 回执验收门禁
- 完整准确率未成立说明

页面标记：

```text
data-h2w3d-online-receipt-quality="p3-06u-26h2w3d"
```

## 3. 明确边界

本片不做这些事：

- 不打开真实外发。
- 不接真实企微、公众号、抖音、淘宝、京东、拼多多等平台的正式发送。
- 不调用大模型。
- 不读取或展示回执原始 payload。
- 不展示客户聊天原文。
- 不把检索命中率、回执送达率、样本评测结果包装成完整客服准确率。
- 不生成客户可签收的线上准确率结论。
- 真实外发继续关闭。

当前完整客服准确率仍必须依赖：

- 真实客户题库。
- 最终客服回复样本。
- 人工事实性标签。
- 官方授权渠道。
- 真实平台回执。
- 失败重试和审计闭环。

## 4. 验收门禁

### 4.1 必须通过

```bash
python3 scripts/check_p3_06u_26h2w3d_online_receipt_quality.py
cd backend && .venv/bin/python -m pytest tests/test_channel_connectors_api.py::test_online_receipt_quality_summary_is_bounded_and_does_not_claim_full_accuracy -q
cd frontend && npm run typecheck
cd frontend && npm run build
```

### 4.2 停止门禁

任何一个条件出现，本阶段不能宣称完成：

- 接口返回 `raw_payload_included=true`。
- 接口返回 `customer_accuracy_completed=true`。
- 接口返回 `external_platform_write_performed=true` 或 `real_external_write_performed=true`。
- 前端文案把“回执送达率”写成“客服准确率”。
- 质量页没有展示“完整准确率未成立”的边界。
- 失败回执没有进入失败复盘。
- 回执汇总不能按租户隔离。

## 5. 后续接真实渠道时的接法

后续企微、公众号或其它官方渠道接入后，不需要另造质量口径。

真实渠道只需要把官方回调映射到现有回执表：

```text
官方回调 -> ChannelDeliveryReceipt -> normalized_status -> DeliveryFailureReview -> online receipt summary -> 质量诊断页
```

真实验收时再补：

- 官方签名/AES 验证必须为真。
- 外部消息 ID 必须能匹配 `OutboxSendAttempt.external_message_id`。
- 失败、限流、权限、内容拒绝必须进入失败复盘。
- 白名单测试消息必须形成发送尝试、回执、审计和复盘记录。

## 6. 下一步建议

下一片建议进入 H2W3E：

- 把质量复盘页里的“线上回执闭环”与客户题库最终答案标签再做一次归因合并。
- 继续不打开真实外发。
- 先完成可导出的内部质量证据包，再进入 XLSX/PDF/DOCX 正式签收文件接收。
