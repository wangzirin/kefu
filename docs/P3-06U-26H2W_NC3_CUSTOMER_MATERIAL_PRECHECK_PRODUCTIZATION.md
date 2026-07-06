# H2W-NC3 客户资料接收与预检产品化

## 结论

- 阶段状态：`customer_material_precheck_productization_ready`
- 范围：把客户资料预检从一次性表单升级为可追踪的资料批次流程。
- 当前不保存客户原文，不打开真实外发，不标记客户签收，不生成正式安装包。

## 已纳入门禁

- schema_exposes_batch_list：`True`
- service_exposes_hash_only_batch_list：`True`
- service_keeps_boundaries_closed：`True`
- router_requires_knowledge_permission：`True`
- tests_cover_empty_passed_blocked_and_no_raw_leak：`True`
- frontend_client_has_batch_contract：`True`
- frontend_ui_has_real_actions：`True`
- frontend_rejects_binary_sources_for_precheck：`True`
- frontend_styles_present：`True`
- no_customer_visible_overclaim_in_added_flow：`True`

## 阻断项

- 无

## 产品化结果

- 后端新增资料批次只读接口，返回最近预检批次、阻断数量、脱敏风险数量和 ready 边界。
- 前端试点准备页支持从本地 CSV/JSON 填入资料草稿、刷新资料批次，并展示最近批次状态。
- 批次列表只返回 hash、统计和状态，不返回客户问题原文、标准答案全文、密钥或平台 payload。
- 预检通过只代表可以进入固定文件接收目录，不代表真实客户资料 ready。

## 边界

- 真实平台外发仍关闭。
- 真实渠道闭环仍未完成。
- 正式客户签收仍未完成。
- 签名 dmg/exe 安装器仍未完成。
- 内部样板或预检批次不能冒充真实客户资料。
