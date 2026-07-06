# H2W-INSTALL1 非技术客户本地启动器 rehearsal

## 结论

- 阶段状态：`ready_for_nontechnical_customer_startup_rehearsal`
- 非技术客户启动器 rehearsal 就绪：`true`
- 完整桌面安装器就绪：`false`
- 原生安装包就绪：`false`
- 正式客户签收就绪：`false`
- 真实平台外发就绪：`false`

## 本阶段实际完成

- 新增 macOS 双击启动包装器 `deploy/start-local-pilot.command`。
- 新增客户可读启动说明 `docs/customer/万法常世AI客服本地试点启动说明.md`。
- 新增 INSTALL1 门禁脚本，检查 PACK5、KB1、安全启动脚本、客户环境模板、启动器和客户说明。
- 启动器只调用现有 `deploy/start-local-pilot.sh`，不自动创建客户环境文件、不填写密码、不启用 worker、不打开真实外发。

## 客户启动路径

1. 安装并启动 Docker Desktop。
2. 复制 `deploy/customer.env.example` 为 `deploy/customer.env`。
3. 替换本地随机数据库密码。
4. 双击 `deploy/start-local-pilot.command`。
5. 打开 `http://127.0.0.1:5173` 创建首任负责人。
6. 先生成诊断包和备份，再导入知识资料。

## 停止门禁

- PACK5 或 KB1 上游证据缺失时，不进入本地试点交付。
- 启动器绕过安全启动脚本、自动写入客户 env、启用 worker profile、展示真实外发已开启时，立即阻断。
- 客户说明出现正式签收、真实平台已接通、完整安装器已完成等越界承诺时，立即阻断。
- `deploy/customer.env` 不应进入仓库；客户只能从模板复制并在本地填写。

## 阻断项

- 无

## 不可对外承诺

- 完整 macOS dmg / Windows exe 安装器
- 正式客户准确率签收
- 真实平台自动外发
- 企业微信/微信客服/抖音/淘宝/京东/拼多多真实渠道上线
- 客户专属知识库正式验收
- 生产环境长期监控、告警和 SLA

## 固定边界

- `real_platform_send_performed=false`
- `enterprise_channel_scope_included=false`
- `rpa_formal_delivery_included=false`
- `formal_customer_signoff_performed=false`
- `desktop_installer_ready=false`
- `native_installer_ready=false`
- `customer_env_created_or_modified=false`
