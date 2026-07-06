# P3-06U-26H2E 签名更新包预检第一片

## Engineering Control Card

- Stage: P3-06U-26H2E
- 当前主线阶段: 本地应用售后更新链路第一片
- 上一阶段真正完成: H2B 本地账号治理、H2C 本地诊断包生成、H2D 知识更新包导入
- 本片目标: 让客户本地系统可以对我方回传的 `.wanfa-update` 签名更新包做预检，确认签名、摘要、版本兼容、备份计划和健康检查计划
- 本片不做什么: 不执行更新、不替换程序文件、不创建真实备份、不迁移数据库、不写外部平台、不调用模型、不上传客户数据
- 产品口径: 这是更新器安全门的第一片，不是完整自动升级系统

## 为什么先做预检

客户本地版售后更新不能让客户直接解压覆盖文件，也不能让我们远程手动改库。正式链路必须先证明更新包来自我们、内容没有被篡改、版本适配当前应用，并且更新前需要备份哪些本地资源。

因此 H2E 先做一个保守的签名更新包预检入口：

1. 客户管理员拿到我方回传的更新包。
2. 在本地后台粘贴或导入更新包内容。
3. 系统只做 dry-run 预检。
4. 预检展示签名、摘要、版本、备份和健康检查结果。
5. 本片永远不直接应用更新。

## 更新包契约

当前 schema：

- 外层: `wanfa.signed_update_package.v1`
- manifest: `wanfa.signed_update_manifest.v1`
- 产品标识: `wanfa-standard-ops`
- 当前应用版本: `0.1.0`
- 签名算法: `rsa_pkcs1v15_sha256`
- 包类型: `knowledge`、`strategy`、`program`

最小结构：

```json
{
  "schema_version": "wanfa.signed_update_package.v1",
  "manifest": {
    "schema_version": "wanfa.signed_update_manifest.v1",
    "package_id": "wanfa-update-20260703-001",
    "package_name": "本地知识与策略修复包",
    "package_type": "knowledge",
    "package_version": "2026.07.03.1",
    "product": "wanfa-standard-ops",
    "released_at": "2026-07-03T10:00:00+08:00",
    "compatible_app_versions": ["0.1.0"],
    "requires_maintenance_window": false,
    "payload_digest_sha256": "...",
    "payload_size_bytes": 0,
    "operations": []
  },
  "payload": {},
  "release_notes": "更新说明",
  "checksums": {
    "payload_sha256": "..."
  },
  "signature": {
    "algorithm": "rsa_pkcs1v15_sha256",
    "key_id": "release-key-id",
    "value": "base64-signature"
  }
}
```

## 后端实现

新增接口：

```text
POST /api/tenants/{tenant_id}/signed-update-package/preflights
```

权限：

```text
updates.manage
```

当前只有 `owner` 和 `admin` 角色拥有该权限，普通客服坐席不能校验或暂存更新包。

可信发布公钥配置：

```text
WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON
```

该环境变量是 `key_id -> PEM public key` 的 JSON 映射。客户本地系统只有配置了我方可信发布公钥，才允许签名更新包进入下一步预检通过状态。

涉及文件：

- `backend/app/core/config.py`
- `backend/app/core/rbac.py`
- `backend/app/schemas/signed_updates.py`
- `backend/app/services/signed_updates.py`
- `backend/app/api/signed_updates.py`
- `backend/app/main.py`
- `backend/tests/test_signed_update_packages_api.py`

## 预检检查项

### 签名检查

系统使用可信公钥校验 manifest 的 RSA 签名。

阻断条件：

- 未配置可信发布公钥。
- `key_id` 找不到对应公钥。
- 签名格式错误。
- manifest 被篡改。
- 算法不是当前允许的 `rsa_pkcs1v15_sha256`。

### 摘要检查

系统对 `payload` 做 canonical JSON SHA256。

阻断条件：

- 实际 payload 摘要与 manifest 声明不一致。
- `checksums.payload_sha256` 与 manifest 声明不一致。

### 版本兼容检查

系统检查：

- `product` 必须等于 `wanfa-standard-ops`。
- 当前应用版本 `0.1.0` 必须在兼容版本列表中。

支持兼容写法：

- 精确版本，例如 `0.1.0`
- 通配版本，例如 `0.1.x`
- 全量通配 `*`

### 备份计划

本片只生成备份计划，不创建备份。

默认备份资源：

- `database_snapshot`
- `knowledge_documents`
- `business_objects`
- `object_knowledge_cards`
- `evaluation_sets`
- `knowledge_import_batches`
- `channel_accounts`
- `channel_connectors`

如果包类型是 `program`，额外要求：

- `program_version`
- `configuration_files`

### 健康检查计划

本片只列出健康检查计划，不执行更新后的检查。

默认检查：

- `api_health`
- `database_connectivity`
- `knowledge_search_smoke`
- `account_login_smoke`

程序包额外要求：

- `frontend_asset_health`
- `worker_health`
- `migration_version_check`

## 前端实现

入口位置：

```text
管理运维 -> 账号与安全 / 系统设置区域中的签名更新包预检卡片
```

前端能力：

- 粘贴 JSON 更新包。
- 恢复示例更新包。
- 发起预检。
- 展示是否可暂存。
- 展示签名、摘要、版本和执行状态。
- 展示备份资源。
- 展示错误和警告。

用户界面必须明确显示：

- 当前只是预检。
- 执行已关闭。
- 没有创建备份。
- 没有替换程序。
- 没有外部写入。

涉及文件：

- `frontend/src/api/client.ts`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`

## 安全边界

本片返回的安全标志必须保持保守：

```json
{
  "dry_run_only": true,
  "external_write_performed": false,
  "provider_call_performed": false,
  "program_execution_performed": false,
  "database_migration_performed": false,
  "backup_created": false,
  "raw_customer_text_logged": false
}
```

明确没有完成：

- 没有真实暂存更新包。
- 没有创建备份快照。
- 没有执行知识更新包。
- 没有执行策略更新包。
- 没有执行程序更新包。
- 没有重启服务。
- 没有迁移数据库。
- 没有恢复或回滚。
- 没有上传诊断包。
- 没有真实平台外发。

## 已验证内容

后端针对性测试：

```bash
cd backend && ./.venv/bin/python -m pytest tests/test_signed_update_packages_api.py -q
```

覆盖：

- 负责人可预检合法签名更新包。
- 篡改 payload 后被摘要检查阻断。
- 不兼容应用版本被阻断。
- 普通客服坐席调用预检接口返回 403。

后端相关回归：

```bash
cd backend && ./.venv/bin/python -m pytest tests/test_signed_update_packages_api.py tests/test_knowledge_update_packages_api.py tests/test_diagnostics_api.py tests/test_accounts_api.py -q
```

覆盖 H2B、H2C、H2D 和 H2E 的账号治理、诊断包、知识更新包和签名更新包预检。

前端验证：

```bash
npm run typecheck
npm run build
```

浏览器 smoke：

- 使用独立临时后端端口和临时 SQLite 数据库。
- 使用独立临时前端端口。
- 真实登录本地负责人账号。
- 打开系统设置。
- 找到“签名更新包预检”卡片。
- 点击“校验更新包”。
- 示例包因未配置可信发布公钥和摘要不匹配被阻断。
- 页面展示“执行 已关闭”。

截图证据：

```text
/Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/output/p3_06u_26h2e_signed_update_preflight_smoke.png
```

## 对客户本地运维模型的意义

H2E 把“我们回传更新包”从口头方案推进到可验证安全门：

1. 客户本地系统开始识别我方签名更新包。
2. 客户管理员能在界面看到更新包是否可信。
3. 系统能在执行前暴露备份和健康检查要求。
4. 普通坐席不能触碰更新入口。
5. 更新链路默认 dry-run，不会误把实验包应用到客户数据。

这解决的是“能不能安全接收更新包”的第一步，不是“已经能自动升级”。

## 下一步

建议进入 P3-06U-26H2F：

1. 新增更新包暂存表，合法签名包可以保存为待处理状态。
2. 导入前创建真实本地备份快照。
3. 为知识包接入 H2D 的知识更新包导入能力。
4. 导入后自动跑健康检查和知识回归题。
5. 失败时允许从备份快照回滚。

程序更新器建议再后置到 H2G，因为程序更新涉及进程停止、文件替换、数据库迁移、版本探针和重启确认，风险高于知识与策略更新。
