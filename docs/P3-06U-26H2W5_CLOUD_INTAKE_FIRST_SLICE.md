# P3-06U-26H2W5 云接收台第一片

## 定位

本片完成“售后接收台”的第一条闭环：客户本地生成脱敏授权上传包后，由售后在系统内登记接收、校验、下载和更新处理状态。

这不是正式云平台上线，也不是远程控制客户电脑。本片仍运行在当前系统内，作为后续托管云端接收台的本地模拟实现。

## 已完成

- 新增 `diagnostic_intake_records` 表，记录接收编号、状态、校验状态、包名、诊断包摘要、包摘要、包大小、拒收原因、处理备注、安全声明和原始授权包 payload。
- 新增后端接口：
  - `POST /api/tenants/{tenant_id}/diagnostic-intake-records`
  - `GET /api/tenants/{tenant_id}/diagnostic-intake-records`
  - `PATCH /api/tenants/{tenant_id}/diagnostic-intake-records/{record_id}`
  - `GET /api/tenants/{tenant_id}/diagnostic-intake-records/{record_id}/download`
- 接收时校验：
  - 上传包版本必须是 `p3-06u-26h2k.v1`。
  - 必须包含客户主动授权记录。
  - 必须包含上传清单、诊断包和安全声明。
  - 诊断包 sha256 必须和上传清单一致。
  - 安全声明不得标记包含原始聊天文本、直接客户标识、完整渠道 payload 或疑似凭据值。
- 校验失败时不丢包，登记为 `rejected` 并保留拒收原因。
- 前端“管理运维 -> 账号安全”新增“售后接收台”：
  - 粘贴授权上传包 JSON。
  - 登记接收。
  - 查看接收记录。
  - 下载包。
  - 负责人/管理员可更新为“处理中”或“已处理”。
- 新增静态门禁：`scripts/check_p3_06u_26h2w5_cloud_intake_static.py`。

## 边界

- 真实外发继续关闭。
- 不自动上传诊断包。
- 不定时联网采集客户环境。
- 不远程控制客户电脑。
- 不读取客户本机文件系统。
- 不替客户执行更新、恢复或回滚。
- 不把本地模拟接收台写成正式云服务已经上线。

## 验收门禁

- `backend/.venv/bin/python -m pytest backend/tests/test_diagnostics_api.py -q`
- `python3 scripts/check_p3_06u_26h2w5_cloud_intake_static.py`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `node scripts/check_p3_06u_26h2w5_cloud_intake.mjs`

## 停止门禁

- 接收包中出现 secrets、token、cookie、password、private key 或原始聊天文本，停止。
- 未记录客户主动授权仍能进入 `received`，停止。
- 摘要不一致仍能进入 `received`，停止。
- 前端写成远程控制、自动上传、自动修复客户环境，停止。
- 登记成功但列表看不到接收记录，停止。
- 拒收没有原因，停止。

## 下一步

- 将本地模拟接收台拆到独立售后云服务。
- 为接收记录增加处理人队列、附件下载权限、处理结果回传包和更新包生成请求。
- 补客户侧主动上传到正式云接收台的授权、网络失败重试和审计。
