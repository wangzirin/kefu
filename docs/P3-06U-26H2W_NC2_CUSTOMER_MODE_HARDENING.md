# H2W-NC2 客户模式安全硬化

## 结论

- 阶段状态：`customer_mode_security_hardening_ready`
- 范围：客户本地试跑安全门禁，不打开真实外发，不做真实渠道，不生成签名安装包。

## 已纳入门禁

- login_failure_limit_present：`True`
- login_failure_audit_present：`True`
- local_owner_safety_blockers_present：`True`
- customer_mode_me_requires_development_for_bootstrap：`True`
- diagnostic_package_size_gate_present：`True`
- diagnostic_package_depth_gate_present：`True`
- diagnostic_schema_allowlist_present：`True`
- diagnostic_rejected_payload_summary_only：`True`
- diagnostic_storage_redaction_present：`True`
- pack_common_forbids_browser_sensitive_files：`True`
- check_p3_06u_26h2w_pilot3_handoff_archive.py_forbids_browser_sensitive_files：`True`
- check_p3_06u_26h2w_pilot6_handoff_archive_refresh.py_forbids_browser_sensitive_files：`True`
- check_p3_06u_26h2w_pack7_trial_handoff_archive_v2.py_forbids_browser_sensitive_files：`True`
- h2w_pack8_common.py_forbids_browser_sensitive_files：`True`

## 阻断项

- 无

## 边界

- 真实平台外发仍关闭。
- 真实渠道闭环仍未完成。
- 诊断包只允许客户主动手动传输，坏包只保存拒收摘要。
- 交付档案禁止包含浏览器 profile、Cookies、History、Login Data、`.git`、`node_modules`。
