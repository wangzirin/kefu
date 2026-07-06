# P3-06U-26H2W6 本地更新恢复处理单第一片

## 定位

本片承接 `H2W-5 云接收台第一片`，把客户主动提供并通过校验的脱敏诊断包，转换为可审计的售后处理单和处理回传包。

它不是完整自动更新器，不替客户执行程序更新，不远程控制客户电脑，不静默更新客户环境，也不打开真实外发。

真实外发继续关闭；任何微信、企业微信、公众号、抖音、小红书、淘宝、京东或拼多多消息发送仍需官方授权、测试白名单、回执、失败重试和审计闭环后单独验收。

## 当前是否偏离总控步骤

没有偏离。

真实 IM 消息流已经按当前决策暂缓，本轮继续走 H2W 非渠道主线：

1. H2W-3D：线上回执与准确率闭环第一片。
2. H2W-4：质量报告导出与归档第一片。
3. H2W-5：云接收台第一片。
4. H2W-6A：本片，诊断接收记录到售后处理单。

下一步仍应继续 H2W-6 的签名更新包、备份、应用和回滚闭环，而不是回到企业微信 Token、URL 或 EncodingAESKey 配置。

## 本片完成内容

### 后端

- 新增 `diagnostic_remediation_requests` 表。
- 新增 Alembic 迁移 `0030_diagnostic_remediation_requests.py`。
- 新增处理单 schema：
  - `DiagnosticRemediationRequestCreate`
  - `DiagnosticRemediationRequestStatusUpdate`
  - `DiagnosticRemediationRequestRead`
  - `DiagnosticRemediationRequestListRead`
  - `DiagnosticRemediationRequestDownloadRead`
- 新增服务能力：
  - 从已通过校验的 `diagnostic_intake_records` 生成处理单。
  - 拒收记录不能生成处理单。
  - 处理单可列出、更新状态、下载回传包。
  - 回传包写明后续需要人工复核、本地备份、客户管理员确认和预检。
- 新增接口：
  - `POST /api/tenants/{tenant_id}/diagnostic-intake-records/{record_id}/remediation-requests`
  - `GET /api/tenants/{tenant_id}/diagnostic-remediation-requests`
  - `PATCH /api/tenants/{tenant_id}/diagnostic-remediation-requests/{request_id}`
  - `GET /api/tenants/{tenant_id}/diagnostic-remediation-requests/{request_id}/download`

### 前端

- “管理运维 -> 账号安全 -> 售后接收台”新增处理回传包区域。
- 已通过校验的接收记录可生成处理单。
- 处理单可标记为“待客户确认”。
- 处理单可下载为 JSON 回传包。
- 界面明确展示：
  - 需要人工复核。
  - 更新前必须备份。
  - 客户管理员确认。
  - 不静默更新。

## 安全边界

处理单中的安全标记固定保守：

- `remote_control_performed=false`
- `customer_environment_write_performed=false`
- `automatic_update_performed=false`
- `silent_update_performed=false`
- `network_push_performed=false`
- `can_apply_now=false`
- `requires_customer_admin_confirmation=true`

这意味着本片只能把诊断资料转成处理建议，不能作为客户环境更新完成证据。

## 验收门禁

- 合格授权上传包可以生成售后接收记录。
- 合格接收记录可以生成处理单。
- 拒收接收记录不能生成处理单。
- 处理单列表可查。
- 处理单状态可更新。
- 处理回传包可下载。
- 下载包不得声称可以直接应用更新。
- 前端出现“生成处理单”和“下载回传包”真实动作。
- 前端不得出现“已远程更新”“自动更新完成”“静默更新”等越界表达。

## 停止门禁

遇到以下情况必须停止，不进入下一片：

1. 拒收诊断包也能生成处理单。
2. 处理单下载包写成可直接更新客户环境。
3. 没有备份要求却允许进入应用更新。
4. 前端把处理单写成“自动更新器”或“远程修复完成”。
5. 真实外发被打开。
6. 未经客户管理员确认就执行客户环境写入。

## 验证命令

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
python3 scripts/check_p3_06u_26h2w6_remediation_static.py
backend/.venv/bin/python -m pytest backend/tests/test_diagnostics_api.py -q
cd frontend && npm run typecheck && npm run build
```

## 下一步

继续 H2W-6B：把处理单和现有签名更新包能力连接起来，形成“处理单 -> 建议包 -> 签名更新包预检 -> 暂存 -> 备份 -> 应用/回滚”的完整本地运维路径。

H2W-6B 仍不能做静默更新；必须继续保留客户管理员确认、预检、备份、应用结果、回滚结果和审计记录。
