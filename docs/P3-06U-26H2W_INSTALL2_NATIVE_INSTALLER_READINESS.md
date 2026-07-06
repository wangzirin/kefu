# H2W-INSTALL2 原生安装器专项门禁

## 结论

- 阶段状态：`native_wrapper_candidate_ready`
- 安装器计划就绪：`true`
- 原生启动包装候选就绪：`true`
- 已签名 dmg/exe 就绪：`false`

## 本阶段实际完成

- 新增 `installers/macos/` 候选包装目录。
- 新增 `installers/windows/` 候选包装目录。
- 包装层只做预检和启动，不自动创建客户 env、不写密码、不开启真实外发、不启用 worker。
- 本阶段不进行 Apple/Windows 代码签名，不写成正式安装包完成。

## 阻断项

- 无

## 固定边界

- `desktop_installer_ready=false`
- `native_installer_ready=false`
- `signed_dmg_exe_ready=false`
- `real_platform_send_performed=false`
- `worker_enabled_by_default=false`
- `default_admin_password_created=false`
- `secret_written_by_installer=false`
