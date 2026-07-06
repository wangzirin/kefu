# P3-06U-26H2L 本地恢复工具 Dry-run 第一片

## 阶段定位

- Stage: P3-06U-26H2L
- Date: 2026-07-03
- Scope: 本地 SQLite 备份的恢复演练计划。
- Boundary: 只生成恢复演练计划，不覆盖数据库、不停服务、不替换文件、不执行迁移、不调用模型、不写外部平台。

## 为什么做这一片

本地部署客户真正出问题时，需要知道“是否可以从某个本地备份恢复、恢复前要做什么、哪些步骤必须停服务、失败后怎么回退”。在完整恢复工具完成前，系统先提供 dry-run 演练能力：

1. 负责人或管理员选择一个本地备份点。
2. 系统校验备份 sha256 和 SQLite `integrity_check`。
3. 系统生成恢复演练计划。
4. 页面展示恢复前必须完成的步骤、健康检查和阻断项。
5. 全程不执行真实恢复。

## 已完成

- 后端新增 `POST /api/local-backups/{local_backup_id}/restore-dry-run`。
- 新增 `LocalBackupRestoreDryRunCreate` 和 `LocalBackupRestoreDryRunRead`。
- `create_local_database_restore_dry_run()` 会复用本地备份记录，生成恢复演练计划，并把最近一次 dry-run 写入备份 manifest。
- 写入审计事件 `local_backup.restore_dry_run_created`。
- 前端“管理运维 -> 账号与安全 -> 本地备份点”新增“恢复演练”按钮。
- 前端展示演练结果：计划状态、阻断项、检查项和关键步骤。
- 新增浏览器 smoke：`scripts/check_p3_06u_26h2l_local_restore_dry_run_ui.mjs`。

## 恢复演练返回口径

关键字段：

```json
{
  "schema_version": "p3-06u-26h2l.restore_dry_run.v1",
  "dry_run": true,
  "can_restore_now": false,
  "rehearsal_ready": true,
  "restore_mode": "offline_operator_required",
  "safety": {
    "live_restore_performed": false,
    "database_file_replaced": false,
    "service_stopped": false,
    "database_migration_performed": false,
    "requires_fresh_pre_restore_backup": true,
    "requires_operator_confirmation": true,
    "requires_service_stop_window": true
  }
}
```

## 当前明确不做

- 不做在线覆盖恢复。
- 不提供“一键恢复”按钮。
- 不替换 SQLite 文件。
- 不停止或重启服务。
- 不执行数据库迁移。
- 不创建二次备份。
- 不接云端远程控制。
- 不上传诊断包。
- 不调用模型。
- 不写企业微信、抖音、淘宝、京东、拼多多等外部平台。

## 验证

已执行：

```bash
cd backend
./.venv/bin/python -m pytest tests/test_local_backups_api.py -q

cd frontend
npm run typecheck
npm run build

cd ..
node scripts/check_p3_06u_26h2l_local_restore_dry_run_ui.mjs
```

结果：

- `tests/test_local_backups_api.py`: 4 passed，1 个既有 Starlette/httpx warning。
- `npm run typecheck`: 通过。
- `npm run build`: 通过，仍有既有 Vite chunk 体积提醒。
- 浏览器 smoke: 通过。

证据：

```text
output/p3_06u_26h2l_local_restore_dry_run_ui/summary.json
output/p3_06u_26h2l_local_restore_dry_run_ui/local-restore-dry-run.png
```

## 下一步

优先进入月度质量复盘收束，或继续做以下 H2 后续片：

- 本机恢复工具第二片：独立命令行/桌面恢复工具，只在停服务窗口执行。
- 远程维护授权界面：客户明确授权我方查看诊断包、回传修复包或协助恢复。
- 知识包发布前后对比自动化：导入前后题库差异、风险题和回退建议。
- 我方诊断接收台：仅在客户授权后接收本地上传包。
