# P3-06U-26H2K 客户授权诊断上传包第一片

日期：2026-07-03

## 阶段控制卡

- Stage: P3-06U-26H2K
- 当前主线阶段: 小微企业本地化交付后的诊断包、更新包、备份和售后运维闭环
- 上一阶段真正完成: H2J 签名程序更新包 dry-run 演练计划
- 本阶段真正完成: 客户管理员可在本地生成“授权上传包”，包内包含授权回执、脱敏诊断包、摘要和安全标记
- 本阶段没有完成: 自动联网上传、我方云端接收台、定期上传、真实客户云端工单流转、远程控制
- 安全边界: 不调用模型、不写外部平台、不自动联网、不保存 token/私钥/密码/真实客户聊天原文

## 本片为什么这样做

本地部署客户通常不希望系统默认把运行数据传出去。H2K 第一片采用“客户授权上传包”的方式：

1. 客户管理员主动点击生成。
2. 系统本地生成脱敏诊断包。
3. 系统把授权说明、诊断包摘要和安全标记包在同一个 JSON 文件里。
4. 文件下载到客户本机。
5. 客户再通过约定的售后工单、企业微信、邮箱或安全通道交给我方。

这一步不是自动上传。它解决的是“客户愿意给我们排障材料时，材料要有授权记录、可追溯摘要和安全边界”。

## 后端变化

新增接口：

```text
POST /api/tenants/{tenant_id}/diagnostic-upload-package
```

权限：

- 需要 `ops.metrics.read`。
- owner/admin 可用。
- agent/viewer 不可用。
- 只能访问自己租户。

新增 schema：

- `DiagnosticUploadPackageCreate`
- `DiagnosticUploadPackageRead`

新增服务：

- `build_diagnostic_upload_package()`

服务行为：

- 复用 `build_diagnostic_bundle()` 生成只读脱敏诊断包。
- 计算诊断包稳定 JSON sha256。
- 生成 `authorization` 授权块。
- 生成 `upload_manifest`。
- 生成 `safety` 安全块。
- 写入审计事件 `diagnostic_bundle.upload_package_created`。
- 路由提交事务，确保审计事件落库。

## 授权上传包结构

```json
{
  "schema_version": "p3-06u-26h2k.v1",
  "filename": "wanfa-diagnostic-upload-tenant-20260703-023316.json",
  "authorization": {
    "authorized_by_user_id": 1,
    "authorization_note": "客户管理员确认授权上传本次脱敏诊断包。",
    "contact_name": "",
    "support_ticket": "",
    "expires_after_hours": 24
  },
  "upload_manifest": {
    "transfer_mode": "manual_transfer_package",
    "upload_status": "ready_for_manual_transfer",
    "diagnostic_bundle_sha256": "...",
    "actual_external_upload_performed": false,
    "network_request_performed": false
  },
  "diagnostic_bundle": {},
  "safety": {
    "external_upload_performed": false,
    "network_request_performed": false,
    "manual_transfer_required": true,
    "customer_authorization_recorded": true
  }
}
```

## 前端变化

位置：

- 管理运维
- 系统设置
- 本地诊断包

新增动作：

- 原动作：`生成并下载`
- 新动作：`授权上传包`

点击 `授权上传包` 后：

- 调用 `createDiagnosticUploadPackage()`。
- 下载 `wanfa-diagnostic-upload-*.json`。
- 卡片状态显示“授权上传包已生成并下载”。
- 不触发真实外部请求。

## 明确不做

- 不自动上传到我方服务器。
- 不接第三方对象存储。
- 不做定期上传。
- 不打开后台联网任务。
- 不读取 `.env` 明文。
- 不包含密钥、密码、token、cookie、私钥。
- 不包含客户完整聊天原文。
- 不替代正式远程维护授权单。

## 验证

### 后端

```bash
cd backend
./.venv/bin/python -m pytest tests/test_diagnostics_api.py -q
```

结果：

```text
4 passed
```

### 前端

```bash
cd frontend
npm run typecheck
npm run build
```

结果：

- typecheck 通过。
- build 通过。
- 仅保留既有 Vite chunk 体积提醒。

### 浏览器 smoke

```bash
node scripts/check_p3_06u_26h2k_diagnostic_upload_package_ui.mjs
```

结果：

```text
PASS p3-06u-26h2k diagnostic upload package UI smoke
```

证据：

```text
output/p3_06u_26h2k_diagnostic_upload_package_ui/summary.json
output/p3_06u_26h2k_diagnostic_upload_package_ui/diagnostic-upload-package.png
output/p3_06u_26h2k_diagnostic_upload_package_ui/wanfa-diagnostic-upload-*.json
```

浏览器 smoke 断言：

- `schema_version=p3-06u-26h2k.v1`
- `transfer_mode=manual_transfer_package`
- `external_upload_performed=false`
- `network_request_performed=false`
- `customer_authorization_recorded=true`
- `manual_transfer_required=true`
- 下载包包含脱敏诊断包。
- 下载包包含诊断包 sha256。
- 下载包未发现 private key、access_token、Bearer、cookie、password、手机号和微信号标记。

## 下一步

1. P3-06U-26H2L：本地恢复工具 dry-run。
2. 后续客户授权上传第二片：我方售后接收台或客户指定安全通道。
3. 后续定期上传：只允许客户明确开启，且必须可随时关闭。
